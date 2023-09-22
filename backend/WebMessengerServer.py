from flask import Flask, request, send_from_directory, Response
from flask_socketio import SocketIO, join_room, leave_room, emit
from functools import wraps
import random
import jwt
import string
import bcrypt
import re
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import socket
import subprocess
import threading
from ORM import *


app = Flask(__name__, static_folder = "static")
socketio = SocketIO(app)
connected_users = []

def getRandomString(length = 10):
	return "".join(random.choices(string.ascii_letters, k = length))


@app.route("/", defaults = {"path": ""})
@app.route("/<path:path>")
def getFrontend(path):
	if (Path(app.static_folder) / Path(path)).is_file():
		return send_from_directory(app.static_folder, path)
	else:
		return send_from_directory(app.static_folder, "index.html")

################################### - Auth - ###################################
def createTokenResponse(user_id):
	session_key = getRandomString()
	
	refresh_token_data = {
		"type": "refresh",
		"key": session_key,
		"exp": datetime.utcnow() + timedelta(seconds = 10) #(hours = config["token_lifetime"]) #@@@@@@@@@@@@@@@@@@@@@@@@
	}
	access_token_data = {
		"type": "access",
		"key": session_key,
		"exp": datetime.utcnow() + timedelta(seconds = 5)
	}
	
	if config["single_session"]:
		current_session = Session.get_or_none(Session.user == user_id)
		if current_session:
			current_session.delete_instance()
	
	Session.create(
		user = user_id,
		key = session_key
	)
	
	refresh_token = jwt.encode(refresh_token_data, app.secret_key, algorithm = "HS512")
	if isinstance(refresh_token, bytes):
		refresh_token = refresh_token.decode()
	access_token = jwt.encode(access_token_data, app.secret_key, algorithm = "HS512")
	if isinstance(access_token, bytes):
		access_token = access_token.decode()
	
	response = Response()
	response.set_cookie(
		"refresh", refresh_token,
		httponly = True, # no access via js
		secure = config["https_only"], # use https only (or localhost)
		samesite = "Strict"
	)
	response.set_cookie(
		"access", access_token,
		httponly = True, # no access via js
		secure = config["https_only"], # use https only (or localhost)
		samesite = "Strict"
	)
	response.set_cookie(
		"auth",
		httponly = False,
		secure = config["https_only"], # use https only (or localhost)
		samesite = "Strict"
	)
	return response


def checkAccessToken(f):
	@wraps(f)
	def wrapped(*args, **kwargs):	
		if "access" not in request.cookies:
			emit("auth_error", {"summary": "Invalid access token", "detail": "The access token is missing"})
			return dict()
		
		try:
			payload = jwt.decode(
				request.cookies.get("access"),
				app.secret_key,
				algorithms = "HS512"
			)
		except jwt.exceptions.ExpiredSignatureError:
			emit("auth_error", {
				"summary": "Access token expired",
				"detail": "You need to update your tokens"
			})
			return dict()
		except jwt.InvalidTokenError:
			emit("auth_error", {"summary": "Invalid access token", "detail": "Access token decode failed"})
			return dict()
		
		if payload["type"] != "access":
			emit("auth_error", {"summary": "Invalid access token", "detail": "Invalid token type"})
			return dict()
		
		current_session = Session.get_or_none(Session.key == payload["key"])
		if not current_session:
			emit("auth_error", {
				"summary": "Invalid session key",
				"detail": "Your session may have been interrupted because someone else logged into your account. Multiple sessions are not allowed."
			})
			return dict()
		
		current_user = User.get_or_none(User.id == current_session.user)
		if not current_user or current_user.account_deleted:
			emit("auth_error", {"summary": "Invalid token", "detail": "Such user doesn't exist"})
			return dict()
		
		current_user.last_action_time = datetime.now()
		current_user.save()
		
		return f(*args, **kwargs, current_user = current_user)
	return wrapped


# ???
def refreshTokens():	
	if "refresh" not in request.cookies:
		emit("auth_error", {"summary": "Invalid refresh token", "detail": "The refresh token is missing"})
		return dict()
	
	try:
		payload = jwt.decode(
			request.cookies.get("refresh"),
			app.secret_key,
			algorithms = "HS512"
		)
	except jwt.exceptions.ExpiredSignatureError:
		emit("auth_error", {
			"summary": "Refresh token expired",
			"detail": "You need to login again"
		})
		return dict()
	except jwt.InvalidTokenError:
		emit("auth_error", {"summary": "Invalid refresh token", "detail": "Refresh token decode failed"})
		return dict()
	
	if payload["type"] != "refresh":
		emit("auth_error", {"summary": "Invalid refresh token", "detail": "Invalid token type"})
		return dict()
	
	current_session = Session.get_or_none(Session.key == payload["key"])
	if not current_session:
		emit("auth_error", {
			"summary": "Invalid session key",
			"detail": "Your session may have been interrupted because someone else logged into your account. Multiple sessions are not allowed."
		})
		return dict()
	user_id = current_session.user
	current_session.delete_instance()
	
	r = createTokenResponse(user_id)
	return r


@app.route("/sign_up", methods = ["CREATE"])
def signUp():
	if config["limited_registration"]:
		if request.remote_addr != "127.0.0.1":
			return "Registration is prohibited", 403

	credentials = request.json

	if User.get_or_none(User.login == credentials["login"]):
		return "This login already exists", 409
	if len(credentials["login"]) < 4:
		return "Login: min 4 chars", 400
		
	if User.get_or_none(User.username == credentials["username"]):
		return "This username already exists", 409
	if len(credentials["username"]) < 2:
		return "Username: min 2 chars", 400
	
	if len(credentials["password"]) < 8 or \
		not re.search("[a-z]", credentials["password"]) or \
		not re.search("[A-Z]", credentials["password"]) or \
		not re.search("[0-9]", credentials["password"]):
		return "Password: min 8 chars; at least one lowercase, uppercase and numeric", 400
		
	current_user = User.create(
		login = credentials["login"],
		password_hash = bcrypt.hashpw(credentials["password"].encode(), bcrypt.gensalt()),
		username = credentials["username"]
	)
	
	user_dir = Path("./users_data") / Path(str(current_user.id))
	user_dir.mkdir(parents = True, exist_ok = True)
	
	files_dir = user_dir / Path("files")
	files_dir.mkdir(parents = True, exist_ok = True)
	
	Log.create(ip = request.remote_addr, user = current_user.id, message = "Signed up")
	
	r = createTokenResponse(current_user.id)
	r.status = 201
	return r


@app.route("/sign_in", methods = ["POST"])
def signIn():
	credentials = request.json
	current_user = User.get_or_none(User.login == credentials["login"])
	if current_user:
		if bcrypt.checkpw(credentials["password"].encode(), current_user.password_hash.tobytes()):
			Log.create(ip = request.remote_addr, user = current_user.id, message = "Signed in")
			return createTokenResponse(current_user.id)
		else:
			Log.create(ip = request.remote_addr, user = current_user.id, message = "Authentication failed: invalid password")
	else:
		Log.create(ip = request.remote_addr, message = "Authentication failed: invalid login")
	return "Authentication failed", 401


@socketio.on("connect")
@checkAccessToken
def connect(current_user):
	connected_users.append(current_user.id)
	join_room(current_user.id)


@socketio.on("privilege_check")
@checkAccessToken
def privilegeCheck(payload, current_user):
	if bcrypt.checkpw(payload["password"].encode(), current_user.password_hash.tobytes()):
		return {"status": 200}
	else:
		return {"status": 401}


@socketio.on("disconnect")
@checkAccessToken
def disconnect(current_user):
	connected_users.remove(current_user.id)
	leave_room(current_user.id)


@app.route("/sign_out", methods = ["POST"])
@checkAccessToken
def signOut(current_user):
	current_user.last_action_time = None
	current_user.save()
	
	Log.create(ip = request.remote_addr, user = current_user.id, message = "Signed out")
	
	response = Response(status = 200)
	response.set_cookie("refresh", samesite = "Strict", expires = 0) #?
	response.set_cookie("access", samesite = "Strict", expires = 0)	 #?
	response.set_cookie("auth", samesite = "Strict", expires = 0)	 #?
	return response

################################ - Messenger - #################################
@socketio.on("/messenger/get_user_chats")
@checkAccessToken
def getUserChats(current_user):
	target_chats = UserToChat \
		.select(UserToChat.chat) \
		.where(UserToChat.user == current_user.id)
	chats = Chat.select() \
		.where(Chat.id.in_(target_chats))
	
	user_chats = dict()
	for chat in chats:
		user_chats[chat.id] = collectChatInfo(current_user.id, chat)
	return {"status": 200, "user_chats": user_chats}


@socketio.on("/messenger/get_chat_info")
@checkAccessToken
def getChatInfo(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if chat:
		return {"status": 200, "chat_info": collectChatInfo(current_user.id, chat)}
	else:
		return {"status": 404}


def collectChatInfo(user_id, chat):
	user_to_chat = UserToChat.get_or_none(
		UserToChat.user == user_id,
		UserToChat.chat == chat.id
	)
	is_user_joined = user_to_chat is not None
	if not is_user_joined:
		if not (chat.type == "channel" and not chat.is_private):
			return {}

	info = dict()
	info["type"] = chat.type
	info["is_joined"] = is_user_joined
	info["last_action_timestamp"] = chat.last_action_date.timestamp()
	
	if is_user_joined:
		if not user_to_chat.last_message_read:
			last_message_read_id = 0
		else:
			last_message_read_id = user_to_chat.last_message_read.id	
		info["last_message_read_id"] = last_message_read_id
	
		unread_messages = Message \
			.select() \
			.where(
				Message.id > last_message_read_id,
				Message.chat == chat.id
			)
		info["unread_counter"] = len(unread_messages)

	if chat.type == "dialog":
		relation = UserToChat.get_or_none(
			UserToChat.user != user_id,
			UserToChat.chat == chat.id
		)
		interlocutor = User.get_or_none(User.id == relation.user.id)
		info["name"] = interlocutor.username
		info["online"] = interlocutor.show_online_status and \
			interlocutor.last_action_time and \
			datetime.now() - interlocutor.last_action_time < timedelta(minutes = 3)
	else: # GROUP or CHANNEL
		info["name"] = chat.name
		info["is_owner"] = chat.owner.id == user_id
		if chat.type == "channel":
			info["is_private"] = chat.is_private
	
	return info


@socketio.on("/messenger/get_chat_messages")
@checkAccessToken
def getChatMessages(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if not chat:
		return {"status": 404}

	user_to_chat = UserToChat.get_or_none(
		UserToChat.user == current_user.id,
		UserToChat.chat == payload["chat_id"]
	)
	if not user_to_chat:
		if not (chat.type == "channel" and not chat.is_private):
			return {"status": 403, "error": "This is not your chat"}

	chat_messages = Message.select() \
		.where(
			Message.chat == payload["chat_id"],
			Message.deleted == False
		)
	messages = dict()
	for msg in chat_messages:
		messages[msg.id] = {
			"chat_id": msg.chat.id,
			"author": User.get_or_none(User.id == msg.author).username,
			"is_my_message": msg.author.id == current_user.id,
			"timestamp": msg.date.timestamp(),
			"type": msg.type,
			"text": msg.text
		}
	
	return {"status": 200, "chat_messages": messages}


@socketio.on("/messenger/search")
@checkAccessToken
def search(payload, current_user):
	search_result = []
	if payload["query"]:
		if "user" in payload["types"]:
			users = User \
				.select() \
				.where(
					User.id != current_user.id,
					User.account_deleted == False,
					User.username.contains(payload["query"])
				)
			for user in users:
				search_result.append({
					"type": "user",
					"id": user.id,
					"name": user.username,
					"online": user.show_online_status and user.last_action_time and \
						datetime.now() - user.last_action_time < timedelta(minutes = 3) 
				})
		
		if "channel" in payload["types"]:
			channels = Chat \
				.select() \
				.where(
					Chat.type == "channel",
					Chat.is_private == False,
					Chat.name.contains(payload["query"])
				)
			for channel in channels:
				search_result.append({
					"type": "channel",
					"id": channel.id,
					"name": channel.name
				})
	return {"status": 200, "search_result": search_result}


@socketio.on("/messenger/create_dialog")
@checkAccessToken
def createDialog(payload, current_user):
	block = BlackList.get_or_none(
		BlackList.user == payload["interlocutor_id"],
		BlackList.blocked_user == current_user.id
	)
	if block:
		return {"status": 403, "error": "This user has blocked you"}

	existing_dialogs = UserToChat \
		.select(UserToChat.chat) \
		.join(Chat, on = (UserToChat.chat == Chat.id)) \
		.where(
			UserToChat.user == current_user.id,
			Chat.type == "dialog"
		)
	user_to_chat = UserToChat.get_or_none(
		UserToChat.user == payload["interlocutor_id"],
		UserToChat.chat.in_(existing_dialogs)
	)
	if user_to_chat: # dialog already exists
		return {"status": 200, "chat_id": user_to_chat.chat.id}
	
	chat = Chat.create(type = "dialog")
	chat.save()
	
	UserToChat.create(
		user = current_user.id,
		chat = chat.id
	).save()
	UserToChat.create(
		user = payload["interlocutor_id"],
		chat = chat.id
	).save()
	
	socketio.emit("chat_created", chat.id, to = current_user.id)
	
	return {"status": 200, "chat_id": chat.id}


@socketio.on("/messenger/create_group")
@checkAccessToken
def createGroup(payload, current_user):
	chat = Chat.create(
		type = "group",
		owner_id = current_user.id,
		name = payload["name"]
	)
	chat.save()
	
	UserToChat.create(
		user = current_user.id,
		chat = chat.id
	).save()
	
	socketio.emit("chat_created", chat.id, to = current_user.id)
	
	return {"status": 200, "chat_id": chat.id}


@socketio.on("/messenger/create_channel")
@checkAccessToken
def createChannel(payload, current_user):
	chat = Chat.get_or_none(
		Chat.type == "channel",
		Chat.name == payload["name"]
	)
	if chat:
		return {"status": 409}
	
	chat = Chat.create(
		type = "channel",
		owner = current_user.id,
		name = payload["name"],
		is_private = payload["is_private"]
	)
	chat.save()
	
	UserToChat.create(
		user = current_user.id,
		chat = chat.id
	).save()
	
	socketio.emit("chat_created", chat.id, to = current_user.id)
	
	return {"status": 200, "chat_id": chat.id}


@socketio.on("/messenger/call")
@checkAccessToken
def call(payload, current_user):
	user_to_chat = UserToChat.get_or_none(
		UserToChat.user != current_user.id,
		UserToChat.chat == payload["chat_id"]
	)
	if not user_to_chat:
		return {"status": 404, "error": "Invalid chat_id"}
		
	if payload["mode"] not in ["call", "accept_call", "decline_call"]:
		return {"status": 404, "error": "Invalid mode"}
	
	target_user_id = user_to_chat.user.id
	if target_user_id not in connected_users:
		return {"status": 404, "error": "User is offline"}
	
	socketio.emit(payload["mode"], {"chat_id": payload["chat_id"]}, to = target_user_id)
	return {"status": 200, "mode": payload["mode"]}


@socketio.on("/messenger/rename_chat")
@checkAccessToken
def renameChat(payload, current_user):
	chat = Chat.get_or_none(
		Chat.id == payload["chat_id"],
		Chat.owner == current_user.id
	)
	if not chat:
		return {"status": 404}
	
	chat.name = payload["name"]
	chat.last_action_date = datetime.now()
	chat.save()
	
	user_to_chat_list = UserToChat \
		.select() \
		.where(
			UserToChat.chat == payload["chat_id"]
		)
	for user_to_chat in user_to_chat_list:
		recipient_id = user_to_chat.user.id
		if recipient_id in connected_users:
			socketio.emit("chat_renamed", {
					"chat_id": chat.id,
					"name": chat.name,
					"last_action_timestamp": chat.last_action_date.timestamp()
				},
				to = recipient_id)
	
	return {"status": 200}


@socketio.on("/messenger/get_chat_members")
@checkAccessToken
def getChatMembers(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if not chat:
		return {"status": 404}
	
	user_to_chat_list = UserToChat \
		.select() \
		.where(
			UserToChat.chat == payload["chat_id"]
		)
	
	members = []
	for user_to_chat in user_to_chat_list:
		members.append({
			"id": user_to_chat.user.id,
			"name": user_to_chat.user.username,
			"is_owner": user_to_chat.user.id == chat.owner.id,
			"online": user_to_chat.user.show_online_status and user_to_chat.user.last_action_time and \
				datetime.now() - user_to_chat.user.last_action_time < timedelta(minutes = 3)
		})
	
	return {"status": 200, "chat_members": members}


@socketio.on("/messenger/search_new_chat_member")
@checkAccessToken
def searchNewChatMember(payload, current_user):
	search_result = []
	if payload["query"]:
		chat_members = UserToChat \
			.select(UserToChat.user) \
			.where(UserToChat.chat == payload["chat_id"])
		
		users = User \
			.select() \
			.where(
				User.id.not_in(chat_members),
				User.account_deleted == False,
				User.username.contains(payload["query"])
			)
		for user in users:
			search_result.append({
				"id": user.id,
				"name": user.username,
				"online": user.show_online_status and user.last_action_time and \
					datetime.now() - user.last_action_time < timedelta(minutes = 3) 
			})
	return {"status": 200, "search_result": search_result}


@socketio.on("/messenger/add_user_to_chat")
@checkAccessToken
def addUserToChat(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if not chat:
		return {"status": 404}
	
	if chat.owner.id != current_user.id:
		return {"status": 403, "error": "This is not your chat"}

	if chat.type == "dialog" or (chat.type == "channel" and not chat.is_private):
		return {"status": 403, "error": "You cannot add user to this chat"}

	block = BlackList.get_or_none(
		BlackList.user == payload["user_id"],
		BlackList.blocked_user == current_user.id
	)
	if block:
		return {"status": 403, "error": "This user has blocked you"}

	check = UserToChat.get_or_none(
		UserToChat.user == payload["user_id"],
		UserToChat.chat == payload["chat_id"]
	)
	if check: # already added
		return {"status": 200}

	UserToChat.create(
		user = payload["user_id"],
		chat = payload["chat_id"]
	).save()
	
	socketio.emit("chat_created", payload["chat_id"], to = payload["user_id"])
	
	return {"status": 200}


@socketio.on("/messenger/remove_user_from_chat")
@checkAccessToken
def removeUserFromChat(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if not chat:
		return {"status": 404}
		
	if chat.owner.id != current_user.id:
		return {"status": 403, "error": "This is not your chat"}
	
	if chat.type == "dialog" or (chat.type == "channel" and not chat.is_private):
		return {"status": 403, "error": "You can't remove a user from this chat"}
	
	user_to_chat = UserToChat.get_or_none(
		UserToChat.user == payload["user_id"],
		UserToChat.chat == payload["chat_id"]
	)
	if user_to_chat:
		user_to_chat.delete_instance()
		socketio.emit("chat_deleted", payload["chat_id"], to = payload["user_id"])
	
	return {"status": 200}


@socketio.on("/messenger/join_chat")
@checkAccessToken
def joinChat(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if not chat:
		return {"status": 404}
	
	if chat.type != "channel" or chat.is_private:
		return {"status": 403, "error": "You can't join this chat"}
	
	user_to_chat = UserToChat.get_or_none(
		UserToChat.user == current_user.id,
		UserToChat.chat == payload["chat_id"]
	)
	if not user_to_chat:
		UserToChat.create(
			user = current_user.id,
			chat = payload["chat_id"]
		).save()
		socketio.emit("chat_created", payload["chat_id"], to = current_user.id)
	
	return {"status": 200}


@socketio.on("/messenger/leave_chat")
@checkAccessToken
def leaveChat(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if not chat:
		return {"status": 404}
	
	if chat.type == "dialog" or chat.owner.id == current_user.id:
		return {"status": 403, "error": "You can't leave this chat"}
	
	relation = UserToChat.get_or_none(
		UserToChat.user == current_user.id,
		UserToChat.chat == payload["chat_id"]
	)
	if relation:
		relation.delete_instance()
		socketio.emit("chat_deleted", payload["chat_id"], to = current_user.id)
	
	return {"status": 200}


@socketio.on("/messenger/delete_chat")
@checkAccessToken
def deleteChat(payload, current_user):
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if not chat:
		return {"status": 404}
	
	if chat.type != "dialog":
		if chat.owner.id != current_user.id:
			return {"status": 403, "error": "You can't delete this chat"}
	
	user_to_chat_list = UserToChat.select().where(UserToChat.chat == payload["chat_id"])
	for user_to_chat in user_to_chat_list:
		socketio.emit("chat_deleted", user_to_chat.chat.id, to = user_to_chat.user.id)
		user_to_chat.delete_instance()
	
	messages = Message.select().where(Message.chat == payload["chat_id"])
	for message in messages:
		message.delete_instance()
	
	chat.delete_instance()
	return {"status": 200}


@socketio.on("/messenger/post_message")
@checkAccessToken
def postMessage(payload, current_user):
	user_to_chat = UserToChat \
		.select() \
		.where(
			UserToChat.user == current_user.id,
			UserToChat.chat == payload["chat_id"]
		)
	if not user_to_chat:
		return {"status": 404}
	
	chat = Chat.get_or_none(Chat.id == payload["chat_id"])
	if chat.type == "dialog":
		user_to_chat = UserToChat.get_or_none(
			UserToChat.user != current_user.id,
			UserToChat.chat == chat.id
		)
		block = BlackList.get_or_none(
			BlackList.user == user_to_chat.user,
			BlackList.blocked_user == current_user.id
		)
		if block:
			return {"status": 403, "error": "This user has blocked you"}
	if chat.type == "channel" and chat.owner.id != current_user.id:
		return {"status": 403, "error": "You can't post messages in this chat"}
	
	chat.last_action_date = datetime.now()
	chat.save()
	
	message = Message.create(
		chat = chat.id,
		author = current_user.id,
		type = payload["type"],
		text = payload["text"]
	)
	message.save()
	
	user_to_chat_list = UserToChat \
		.select() \
		.where(
			UserToChat.chat == chat.id
		)
	for user_to_chat in user_to_chat_list:
		recipient_id = user_to_chat.user.id
		if recipient_id in connected_users:
			socketio.emit("message_posted", {
					"id": message.id,
					"info": {
						"chat_id": chat.id,
						"author": current_user.username,
						"is_my_message": message.author.id == recipient_id,
						"timestamp": message.date.timestamp(),
						"type": message.type,
						"text": message.text
					},
				}, to = recipient_id)
	
	return {"status": 200}


@socketio.on("/messenger/set_last_message_read")
@checkAccessToken
def setLastMessageRead(payload, current_user):
	user_to_chat = UserToChat.get_or_none(
		UserToChat.user == current_user.id,
		UserToChat.chat == payload["chat_id"]
	)
	if user_to_chat:
		user_to_chat.last_message_read = payload["message_id"]
		user_to_chat.save()
		return {"status": 200}
	return {"status": 404}


@socketio.on("/messenger/edit_message")
@checkAccessToken
def editMessage(payload, current_user):
	message = Message.get_or_none(Message.id == payload["message_id"])
	if not message:
		return {"status": 404}
	if message.author.id != current_user.id:
		return {"status": 403, "error": "You can't edit this message"}

	user_to_chat_list = UserToChat.select() \
		.where(UserToChat.chat == message.chat)	
	
	for user_to_chat in user_to_chat_list:
		recipient_id = user_to_chat.user.id
		if recipient_id in connected_users:
			socketio.emit("message_edited", {
				"id": message.id,
				"new_text": payload["new_text"]
			},
			to = recipient_id)

	message.text = payload["new_text"]
	message.save()


@socketio.on("/messenger/delete_message")
@checkAccessToken
def deleteMessage(payload, current_user):
	message = Message.get_or_none(Message.id == payload["message_id"])
	if not message:
		return {"status": 404}
	if message.author.id != current_user.id:
		return {"status": 403, "error": "You can't delete this message"}
	
	user_to_chat_list = UserToChat.select() \
		.where(UserToChat.chat == message.chat)	
	
	for user_to_chat in user_to_chat_list:
		recipient_id = user_to_chat.user.id
		if recipient_id in connected_users:
			socketio.emit("message_deleted", message.id, to = recipient_id)

	message.chat = None
	message.author = None
	message.date = None
	message.type = None
	message.text = ""
	message.deleted = True
	message.save()

################################## - Files - ###################################
ITEMS_ON_PAGE = 10
@socketio.on("/files/get_directory_content")
@checkAccessToken
def getDirectoryContent(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"]
	if not target.is_dir():
		return  {"status": 404}
	
	dirs = []
	for item in target.glob("*"):
		if item.is_dir():
			dirs.append({"type": "dir", "name": item.name, "modified": item.stat().st_mtime})
	content = sorted(dirs, key = lambda item: item["modified"], reverse = True)
	
	files = []
	for item in target.glob("*"):
		if item.is_file():
			files.append({"type": "file", "name": item.name, "modified": item.stat().st_mtime, "size": item.stat().st_size})
	content += sorted(files, key = lambda item: item["modified"], reverse = True)
	
	return {
		"status": 200,
		"content": content[payload["paginator"]:payload["paginator"] + ITEMS_ON_PAGE],
		"items": ITEMS_ON_PAGE,
		"total": len(content)
	}


@socketio.on("/files/get_free_space")
@checkAccessToken
def getFreeSpace(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"]
	if not target.is_dir():
		return  {"status": 404}
	total, used, free = shutil.disk_usage(target)
	return {"status": 200, "free_space": "{:.2f}".format(free / 2**30)}


@socketio.on("/files/upload")
@checkAccessToken
def upload(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"] / payload["file_name"]
	if target.exists():
		return {"status": 409, "error": "Such file already exists"}
	
	with open(target, "wb") as f:
		f.write(payload["file_data"])
	return {"status": 200}


@socketio.on("/files/create_dir")
@checkAccessToken
def createDir(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"] / payload["name"]
	if target.exists():
		return {"status": 400, "error": "Such directory already exists"}
	target.mkdir(parents = True, exist_ok = True)
	return {"status": 200}


@socketio.on("/files/download")
@checkAccessToken
def download(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"] / payload["name"]
	if not target.is_file():
		return {"status": 404, "error": "File not found"}
	
	file_data = []
	with open(target, "rb") as f:
		file_data = f.read()
	return {"status": 200, "file_data": file_data}


@socketio.on("/files/rename")
@checkAccessToken
def rename(payload, current_user):	
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"] / payload["name"]
	if not target.exists():
		return {"status": 404, "error": "File not found"}
	new_target = user_remote_storage / payload["cwd"] / Path(payload["new_name"])
	if new_target.exists():
		return {"status": 400, "error": "Such file already exists"}
	target.rename(new_target)
	return {"status": 200}


@socketio.on("/files/move")
@checkAccessToken
def move(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"] / payload["name"]	
	if not target.exists():
		return {"status": 404, "error": "Source file doesn't exist"}
	dest = user_remote_storage / Path(payload["dest"])
	if not dest.exists():
		return {"status": 404, "error": "The destination doesn't exist"}
	new_target = dest / payload["name"]
	if new_target.exists():
		return {"status": 409, "error": "Such file already exists"}
	target.rename(new_target)
	return {"status": 200}


@socketio.on("/files/copy")
@checkAccessToken
def copy(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"] / payload["name"]	
	if not target.exists():
		return {"status": 404, "error": "Source file doesn't exist"}
	dest = user_remote_storage / Path(payload["dest"])
	if not dest.exists():
		return {"status": 404, "error": "The destination doesn't exist"}
	new_target = dest / payload["name"]
	while new_target.exists():
		new_target = Path(new_target.parents[0]) / Path(new_target.stem + "_copy" + new_target.suffix)
	if target.is_dir():
		shutil.copytree(target, new_target)
	else:
		shutil.copy(target, new_target)
	return {"status": 200}


@socketio.on("/files/delete")
@checkAccessToken
def delete(payload, current_user):
	user_remote_storage = Path("./users_data") / Path(str(current_user.id)) / Path("files")
	target = user_remote_storage / payload["cwd"] / payload["name"]
	if target.is_file():
		target.unlink()
	elif target.is_dir():
		shutil.rmtree(target)
	else:
		return {"status": 404, "error": "File not found"}
	return {"status": 200}

################################# - Settings - #################################
@socketio.on("/settings/get_user_info")
@checkAccessToken
def getUserInfo(current_user):
	info = dict()
	if current_user.photo_path:
		photo_path = Path(current_user.photo_path)
		if photo_path.exists():
			with open(photo_path, "rb") as f:
				info["photo_data"] = f.read()
		else:
			current_user.photo_path = ""
			current_user.save()

	info["username"] = current_user.username
	info["show_online_status"] = current_user.show_online_status	
	return {"status": 200, "user_info": info}


@socketio.on("/settings/update_user_photo")
@checkAccessToken
def updateUserPhoto(payload, current_user):	
	requirements = re.fullmatch("(.)+\.(png|PNG|jpg|JPG|jpeg|JPEG)$", payload["name"]) and len(payload["data"]) <= 512 * 1024
	if not requirements:
		return {"status": 400, "error": "Inappropriate photo"}
	
	if (current_user.photo_path): # delete old photo
		old_photo_path = Path(current_user.photo_path)
		if (old_photo_path.exists()):
			old_photo_path.unlink()
	
	new_photo_path = Path("./users_data") / Path(str(current_user.id)) / Path(payload["name"])
	with open(new_photo_path, "wb") as f:
		f.write(payload["data"])
	
	current_user.photo_path = new_photo_path
	current_user.save()
	return {"status": 201}


@socketio.on("/settings/delete_photo")
@checkAccessToken
def deletePhoto(current_user):
	if (current_user.photo_path):
		photo_path = Path(current_user.photo_path)
		if photo_path.exists():
			photo_path.unlink()
		current_user.photo_path = ""
		current_user.save()
	return {"status": 200}


@socketio.on("/settings/update_username")
@checkAccessToken
def updateUsername(payload, current_user):
	if len(payload["new_username"]) < 2:
		return {"status": 400, "error": "The username must consist at least of 2 characters"}
	if User.get_or_none(User.username == payload["new_username"]):
		return {"status": 409, "error": "This username already exists"}
	current_user.username = payload["new_username"]
	current_user.save()
	return {"status": 201}


@socketio.on("/settings/update_show_online_status")
@checkAccessToken
def updateShowOnlineStatus(payload, current_user):
	current_user.show_online_status = payload["new_status"]
	current_user.save()
	return {"status": 200}


@socketio.on("/settings/get_blocked_users")
@checkAccessToken
def getBlockedUsers(current_user):
	blocked_users_id = BlackList.select(BlackList.blocked_user).where(
		BlackList.user == current_user.id
	)
	blocked_users_list = User.select().where(
		User.id.in_(blocked_users_id)
	)
	blocked_users = []
	for user in blocked_users_list:
		blocked_users.append({
			"id": user.id,
			"name": user.username,
			"online": user.show_online_status and user.last_action_time and \
				datetime.now() - user.last_action_time < timedelta(minutes = 3)
		})
	
	return {"status": 200, "blocked_users": blocked_users}


@socketio.on("/settings/search_user_to_block")
@checkAccessToken
def searchUserToBlock(payload, current_user):
	search_result = []
	if payload["query"]:
		blocked_users_id = BlackList.select(BlackList.blocked_user).where(
			BlackList.user == current_user.id
		)
		users = User.select().where(
			User.id != current_user.id,
			User.id.not_in(blocked_users_id),
			User.account_deleted == False,
			User.username.contains(payload["query"])
		)
		for user in users:
			search_result.append({
				"id": user.id,
				"name": user.username,
				"online": user.show_online_status and user.last_action_time and \
					datetime.now() - user.last_action_time < timedelta(minutes = 3) 
			})
	return {"status": 200, "search_result": search_result}


@socketio.on("/settings/block_user")
@checkAccessToken
def blockUser(payload, current_user):
	if current_user.id == payload["user_id"]:
		return {"status": 404}
	blocked_user = BlackList.get_or_none(
		BlackList.user == current_user.id,
		BlackList.blocked_user == payload["user_id"]
	)
	if not blocked_user:
		BlackList.create(
			user = current_user.id,
			blocked_user = payload["user_id"]
		)
	return {"status": 200}


@socketio.on("/settings/unblock_user")
@checkAccessToken
def unblockUser(payload, current_user):
	blocked_user = BlackList.get_or_none(
		BlackList.user == current_user.id,
		BlackList.blocked_user == payload["user_id"]
	)
	if blocked_user:
		blocked_user.delete_instance()
	return {"status": 200}


@socketio.on("/settings/update_password")
@checkAccessToken
def updatePassword(payload, current_user):
	if not bcrypt.checkpw(payload["current_password"].encode(), current_user.password_hash.tobytes()):
		Log.create(ip = request.remote_addr, user = current_user.id, message = "Password update failed: invalid current password")
		return {"status": 401, "error": "Invalid current password"}
	
	if len(payload["new_password"]) < 8 or \
		not re.search("[a-z]", payload["new_password"]) or \
		not re.search("[A-Z]", payload["new_password"]) or \
		not re.search("[0-9]", payload["new_password"]):
		return {"status": 400, "error": "Password: min 8 chars; at least one lowercase, uppercase and numeric"}
	else:
		current_user.password_hash = bcrypt.hashpw(payload["new_password"].encode(), bcrypt.gensalt())
		current_user.save()
		Log.create(ip = request.remote_addr, user = current_user.id, message = "Password updated")
		return {"status": 201}


@app.route("/settings/delete_account", methods = ["DELETE"])
@checkAccessToken
def deleteAccount(current_user):
	credentials = request.json
	if not bcrypt.checkpw(credentials["password"].encode(), current_user.password_hash.tobytes()):
		Log.create(ip = request.remote_addr, user = current_user.id, message = "Account deletion failed: invalid password")
		return 401

	current_user.account_deleted = True
	current_user.is_admin = False
	current_user.login = None
	current_user.password_hash = ""
	current_user.last_action_time = None
	current_user.username = None
	current_user.photo_path = ""
	current_user.show_online_status = None
	current_user.save()
	
	user_dir = Path("./users_data") / Path(str(current_user.id))
	if (user_dir.exists()):
		shutil.rmtree(user_dir)
	
	Log.create(ip = request.remote_addr, user = current_user.id, message = "Account deleted")
	
	response = Response()
	response.set_cookie("token", samesite = "Strict", expires = 0)
	response.set_cookie("auth", samesite = "Strict", expires = 0)
	return response

################################### - CLI - ####################################
@socketio.on("/admin/cli")
@checkAccessToken
def cmd(payload, current_user):
	if not current_user.is_admin:
		Log.create(ip = request.remote_addr, user = current_user.id, message = "CLI access failed: permission denied")
		return {"status": 403, "error": "You aren't an administrator"}
	
	p = subprocess.Popen(
		payload["cmd"],
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.STDOUT
	)
	try:
		p.wait(timeout = 15)
	except subprocess.TimeoutExpired:
		return {"status": 200, "output": "<timeout>"}
	
	return {
		"status": 200,
		"output": "".join([line.decode() for line in p.stdout.readlines()])
	}

############################## - Server Config - ###############################
server_config = {
	"port": {
		"type": "int",
		"default": "8080",
		"comment": "server port"
	},
	"secret_key": {
		"type": "str",
		"default": "auto",
		"comment": "auto = generate a new secret key"
	},
	"limited_registration": {
		"type": "bool",
		"default": "off",
		"comment": "only the admin (localhost) can register new users"
	},
	"single_session": {
		"type": "bool",
		"default": "on",
		"comment": "only one session is allowed to the user at a time"
	},
	"token_lifetime": {
		"type": "int",
		"default": "8",
		"comment": "the lifetime of the authentication token in hours"
	},
	"https_only": {
		"type": "bool",
		"default": "on",
		"comment": "use https only (or localhost)"
	}
}


def createDefaultConfig(config_file_path):
	with open(config_file_path, "w") as f:
		for key in server_config:
			f.write(f"# {server_config[key]['comment']}\n")
			f.write(f"{key} {server_config[key]['default']}\n\n")


def getConfig(config_file_path): # config-file parser
	if not config_file_path.exists():
		createDefaultConfig(config_file_path)
	
	with open(config_file_path, "r") as f:		
		lines = f.readlines()
	config = {}
	for i in range(len(lines)):
		comment_index = lines[i].find("#")
		if comment_index >= 0:
			pair = lines[i][:comment_index].lower().split()
		else:
			pair = lines[i].lower().split()
		if len(pair) == 0: continue
		if len(pair) != 2: return None, f"Not a \"Key Value\" entity:\tLine {i + 1}: {lines[i]}"
		sample_key = server_config.get(pair[0])
		if not sample_key:
			return None, f"Unknown key \"{pair[0]}\":\tLine {i + 1}: {lines[i]}"
		match sample_key["type"]:
			case "int":
				config[pair[0]] = int(pair[1])
			case "bool":
				if pair[1] not in ["on", "off"]:
					return None, f"Invalid value \"{pair[1]}\":\tLine {i + 1}: {lines[i]}"
				config[pair[0]] = pair[1] == "on"
			case _: # str
				config[pair[0]] = pair[1]
		
	for key in server_config: # check completeness
		if key not in config:
			return None, f"\"{key}\" key is missing"
	
	return config, "Success"


def getLocalIP():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect(("192.255.255.255", 1))
		ip = s.getsockname()[0]
	except:
		ip = "127.0.0.1"
	finally:
		s.close()
	return ip


def cmdHandler():
	print(f"Server is running ({ip}:{config['port']})")
	print("Press Enter to stop")
	while True:
		if (len(input()) == 0):
			break
	socketio.stop()


config, err = getConfig(Path("./server.conf"))
if not config:
	exit(f"Invalid config file\n{err}")

if config["secret_key"] == "auto":
	app.secret_key = getRandomString(length = 30)
else:
	app.secret_key = config["secret_key"]


if __name__ == "__main__":	
	ip = getLocalIP()
	threading.Thread(target = cmdHandler).start()
	socketio.run(app, host = "0.0.0.0", port = config["port"])


# Status codes:
# 200: OK
# 201: Created
# 204: No Content (empty body but it's OK)
# 
# 400: Bad Request
# 401: Unauthorized
# 403: Forbidden
# 404: Not found
# 409: Conflict
