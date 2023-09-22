import psycopg2
from peewee import PostgresqlDatabase, Model, AutoField, IntegerField, \
	TextField, BlobField, BooleanField, DateTimeField, ForeignKeyField
from datetime import datetime


# PostgreSQL credentials
HOST = "localhost"
PORT = 5432
USER = "postgres"
PASSWORD = "postgres"
DATABASE_NAME = "messenger".lower()


# create a new database if it doesn't exist
try:
	conn = None
	conn = psycopg2.connect(host = HOST, port = PORT, user = USER, password = PASSWORD)
	conn.autocommit = True
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DATABASE_NAME}'")
		if not cursor.fetchone():
			cursor.execute(f"CREATE DATABASE {DATABASE_NAME}")
except psycopg2.Error as e:
	exit("Error: PostgreSQL server is unavailable (ORM.py)")
finally:
	if conn:
		conn.close()

db = PostgresqlDatabase(DATABASE_NAME, host = HOST,  port = PORT, user = USER, password = PASSWORD)
db.connect()


class BaseModel(Model):
	class Meta:
		database = db


class User(BaseModel):
	id = AutoField()
	is_admin = BooleanField(default = False) # /admin/cli
	
	login = TextField(unique = True, null = True)
	password_hash = BlobField()
	last_action_time = DateTimeField(null = True)
	
	username = TextField(unique = True, null = True)
	photo_path = TextField(null = True)
	show_online_status = BooleanField(null = True, default = True)
	
	account_deleted = BooleanField(default = False)
	
	class Meta:
		table_name = "Users"


class Log(BaseModel):
	id = AutoField()
	date = DateTimeField(default = datetime.now)
	ip = TextField()
	user = ForeignKeyField(User, to_field = "id", null = True)
	message = TextField(default = "")
	
	class Meta:
		table_name = "Logs"


class Session(BaseModel):
	id = AutoField()
	user = ForeignKeyField(User, to_field = "id")
	key = TextField()

	class Meta:
		table_name = "Sessions"


class BlackList(BaseModel):
	id = AutoField()
	user = ForeignKeyField(User, to_field = "id", null = True)
	blocked_user = ForeignKeyField(User, to_field = "id", null = True)

	class Meta:
		table_name = "Black list"


class Chat(BaseModel):
	id = AutoField()
	type = TextField()
	owner = ForeignKeyField(User, to_field = "id", null = True)
	name = TextField(default = "")
	is_private = BooleanField(default = False)
	last_action_date = DateTimeField(default = datetime.now)
	
	class Meta:
		table_name = "Chats"


class Message(BaseModel):
	id = AutoField()
	chat = ForeignKeyField(Chat, to_field = "id", null = True)
	author = ForeignKeyField(User, to_field = "id", null = True)
	date = DateTimeField(default = datetime.now, null = True)
	type = IntegerField(null = True) # 1 = text message
	text = TextField()
	deleted = BooleanField(default = False)
	
	class Meta:
		table_name = "Messages"


class UserToChat(BaseModel):
	id = AutoField()
	user = ForeignKeyField(User, to_field = "id")
	chat = ForeignKeyField(Chat, to_field = "id")
	last_message_read = ForeignKeyField(Message, to_field = "id", null = True, default = None)
	
	class Meta:
		table_name = "User to chat"


class Calls(BaseModel):
	id = AutoField()
	calling_user = ForeignKeyField(User, to_field = "id")
	called_user =  ForeignKeyField(User, to_field = "id")
	date = DateTimeField(default = datetime.now)

	class Meta:
		table_name = "Calls"


# create tables if they don't exist
if not db.table_exists(User._meta.table_name):
	User.create_table()

if not db.table_exists(Log._meta.table_name):
	Log.create_table()

if not db.table_exists(Session._meta.table_name):
	Session.create_table()

if not db.table_exists(BlackList._meta.table_name):
	BlackList.create_table()

if not db.table_exists(Chat._meta.table_name):
	Chat.create_table()

if not db.table_exists(Message._meta.table_name):
	Message.create_table()

if not db.table_exists(UserToChat._meta.table_name):
	UserToChat.create_table()
	
if not db.table_exists(Calls._meta.table_name):
	Calls.create_table()

