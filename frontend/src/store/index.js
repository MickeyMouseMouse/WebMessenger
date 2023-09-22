import { createStore } from "vuex"
import router from "@/router"
import io from "socket.io-client"

export default createStore({
  state: {
    desktop: navigator.userAgent.search(/iPhone|Android/) == -1,

    mobile_sidebar_visible: false,

    socket: null,
    socket_error: null,
    
    new_message_sound: new Audio(require("@/assets/new_message_sound.mp3")),
    call_sound: new Audio(require("@/assets/call_sound.mp3")),

    // messenger
    chats: {},
    selected_chat_id: null,
    messages: {},
    unread_indicator: false,

    // files
    current_working_dir: [], // [] = root
    paginator: 0,

    //calls
    emit_call_request: false,
    incoming_call_popup_visible: false,
    incoming_call_popup_visible_timer: false,
    incoming_call_chat_id: null
  },
  getters: {
    getSocket(state) {
      return state.socket
    },
    getSocketError(state) {
      let error = state.socket_error
      state.socket_error = null
      return error
    },
    isDesktop(state) {
      return state.desktop
    },
    isMobile(state) {
      return !state.desktop
    },
    getMobileSidebarVisible(state) {
      return state.mobile_sidebar_visible
    },


    getChatList(state) {
      let chat_list = []
      for (let chat_id in state.chats) {
        if (state.chats[chat_id].is_joined) {
          let chat_info = state.chats[chat_id]
          chat_info["id"] = chat_id
          chat_list.push(chat_info)
        }
      }
      chat_list.sort(function(a, b) {
        return b.last_action_timestamp - a.last_action_timestamp
      })
      return chat_list
    },
    getSelectedChatId(state) {
      return state.selected_chat_id
    },
    getChats(state) {
      return state.chats
    },
    getSelectedChatInfo(state) {
      return (state.chats[state.selected_chat_id]) ? state.chats[state.selected_chat_id] : []
    },
    getMessageList(state) {
      let sortable = []
      for (let message_id in state.messages) {
        sortable.push([message_id, state.messages[message_id].timestamp])
      }
      sortable.sort(function(a, b) {
        return a[1] - b[1]
      })
      let message_list = []
      sortable.forEach((item) => message_list.push(item[0]))
      return message_list
    },
    getMessages(state) {
      return state.messages
    },
    isChatOpen(state) {
      return state.chats[state.selected_chat_id] != null
    },
    getUnreadIndicator(state) {
      return state.unread_indicator
    },

    getCurrentWorkingDir(state) {
      return state.current_working_dir
    },
    getPaginator(state) {
      return state.paginator
    },

    getIncomingCallPopUpVisible(state) {
      return state.incoming_call_popup_visible
    }
  },
  mutations: {
    CONNECT_SOCKET_IO(state) {
      state.socket = io(window.location.protocol + "//" + location.host)
    },
    RESET_DATA(state) {
      state.socket.disconnect()

      state.chats = {}
      state.selected_chat_id = null
      state.messages = {}
      state.unread_indicator = false

      state.current_working_dir = []
      state.paginator = 0
    },
    SET_MOBILE_SIDEBAR_VISIBLE(state, visible) {
      state.mobile_sidebar_visible = visible
    },

    SET_USER_CHATS(state, chats) {
      state.chats = chats
    },
    SET_SELECTED_CHAT_ID(state, chat_id) {
      state.selected_chat_id = chat_id
    },
    SET_CHAT(state, chat) {
      state.chats[chat.id] = chat.info
    },
    RENAME_CHAT(state, chat) {
      state.chats[chat.chat_id].name = chat.name
      state.chats[chat.chat_id].last_action_timestamp = chat.last_action_timestamp
    },
    DELETE_CHAT(state, chat_id) {
      delete state.chats[chat_id]
    },
    SET_CHAT_MESSAGES(state, messages) {
      state.messages = messages
    },
    SET_MESSAGE(state, message) {
      state.messages[message.id] = message.info
      state.chats[message.info.chat_id].last_action_timestamp =  message.info.timestamp
    },
    UPDATE_MESSAGE(state, message) {
      state.messages[message.id].text = message.new_text
    },
    DELETE_MESSAGE(state, message_id) {
      delete state.messages[message_id]
    },

    SET_UNREAD_INDICATOR(state, status) {
      state.unread_indicator = status
      if (status) state.new_message_sound.play()
    },

    SET_CURRENT_WORKING_DIR(state, dir) {
      state.current_working_dir = dir
    },
    SET_PAGINATOR(state, paginator) {
      state.paginator = paginator
    },

    SET_EMIT_CALL_REQUEST(state, emit) {
      state.emit_call_request = emit
    },
    SET_INCOMING_CALL_POPUP_VISIBLE(state, visible) {
      state.incoming_call_popup_visible = visible
    },
    SET_INCOMING_CALL_POPUP_VISIBLE_TIMER(state, time) {
      state.incoming_call_popup_visible_timer = time
    },
    SET_INCOMING_CALL_CHAT_ID(state, id) {
      state.incoming_call_chat_id = id
    }
  },
  actions: {
    connectSocketIO({commit, state}) {
      commit("CONNECT_SOCKET_IO")

      state.socket.on("auth_error", (payload) => {
        document.cookie = "auth_flag=;expires=" + new Date(0).toUTCString() + ";SameSite=Strict"
        state.socket_error = payload
        commit("RESET_DATA")
        router.replace({"path": "/"})
      })

      state.socket.on("message_posted", (message) => {
        if (state.selected_chat_id == message.info.chat_id) {
          commit("SET_MESSAGE", message)
        } else {
          this.dispatch("fetchChatInfo", message.info.chat_id)
          if (state.app_state != "messenger") {
            state.unread_indicator = true
            state.new_message_sound.play()
          }
        }
      })
      state.socket.on("message_edited", (message) => {
        commit("UPDATE_MESSAGE", message)
      })
      state.socket.on("message_deleted", (message_id) => {
        commit("DELETE_MESSAGE", message_id)
      })


      state.socket.on("chat_created", (chat_id) => {
        this.dispatch("fetchChatInfo", chat_id)
      })
      state.socket.on("chat_renamed", (chat) => {
        commit("RENAME_CHAT", chat)
      })
      state.socket.on("chat_deleted", (chat_id) => {
        commit("DELETE_CHAT", chat_id)
        commit("SET_SELECTED_CHAT_ID", null)
      })

      state.socket.on("call", (data) => {
        commit("SET_INCOMING_CALL_POPUP_VISIBLE", true)
        state.incoming_call_chat_id = data.chat_id

        let timer_status = state.incoming_call_popup_visible_timer
        commit("SET_INCOMING_CALL_POPUP_VISIBLE_TIMER", 1500)
        if (timer_status == false) this.dispatch("startTimer")
      })
      state.socket.on("accept_call", (data) => {
        commit("SET_EMIT_CALL_REQUEST", false)
        console.log("accepted")
        console.log(data)
      })
      state.socket.on("decline_call", (data) => {
        commit("SET_EMIT_CALL_REQUEST", false)
        console.log("declined")
        console.log(data)
      })
    },
    resetData({commit}) {
      commit("RESET_DATA")
    },
    setMobileSidebarVisible({commit}, visible) {
      commit("SET_MOBILE_SIDEBAR_VISIBLE", visible)
    },

    fetchUserChats({commit, state}) {
      state.socket.emit("/messenger/get_user_chats", (r) => {
        commit("SET_USER_CHATS", r.user_chats)
      })
    },
    fetchChatInfo({commit, state}, chat_id) {
      state.socket.emit("/messenger/get_chat_info", {
          "chat_id": chat_id
        }, (r) => {
        if (r.status == 200) {
          commit("SET_CHAT", {"id": chat_id, "info": r.chat_info})
        }
      })
    },
    fetchChatMessages({commit, state}, chat_id) {
      state.socket.emit("/messenger/get_chat_messages", {
          "chat_id": chat_id
        }, (r) => {
        if (r.status == 200) {
          commit("SET_CHAT_MESSAGES", r.chat_messages)
          commit("SET_SELECTED_CHAT_ID", chat_id)
        }
      })
    },
    resetChat({commit}) {
      commit("SET_SELECTED_CHAT_ID", null)
      commit("SET_CHAT_MESSAGES", {})
    },
    setUnreadIndicator({commit}, status) {
      commit("SET_UNREAD_INDICATOR", status)
    },

    setCurrentWorkingDir({commit}, dir) {
      commit("SET_CURRENT_WORKING_DIR", dir)
    },
    setPaginator({commit}, paginator) {
      commit("SET_PAGINATOR", paginator)
    },

    async call({commit, state}, chat_id) {
      commit("SET_EMIT_CALL_REQUEST", true)
      while (state.emit_call_request) {
        state.socket.emit("/messenger/call", {
          "chat_id": chat_id, 
          "mode": "call"
        }, (r) => {
          if (r.status == 200) {
            console.log(r)
          } else {
            console.log(r)
            commit("SET_EMIT_CALL_REQUEST", false)
          }
        })
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    },
    async startTimer({commit, state}) {
      while (state.timer > 0) {
        await new Promise(resolve => setTimeout(resolve, 500))
        commit("SET_INCOMING_CALL_POPUP_VISIBLE_TIMER", state.timer - 500)
      }
      if (state.timer <= 0) {
        commit("SET_INCOMING_CALL_POPUP_VISIBLE", false)
        commit("SET_INCOMING_CALL_POPUP_VISIBLE_TIMER", false)
      }
    },
    acceptCall({commit, state}) {
      state.socket.emit("/messenger/call", {
        "chat_id": state.incoming_call_chat_id,
        "mode": "accept_call"
      }, (r) => {
        console.log(r)
      })
      commit("SET_INCOMING_CALL_POPUP_VISIBLE", false)
      commit("SET_INCOMING_CALL_POPUP_VISIBLE_TIMER", false)
    },
    declineCall({commit, state}) {
      state.socket.emit("/messenger/call", {
        "chat_id": state.incoming_call_chat_id,
        "mode": "decline_call"
      }, (r) => {
        console.log(r)
      })
      commit("SET_INCOMING_CALL_POPUP_VISIBLE", false)
      commit("SET_INCOMING_CALL_POPUP_VISIBLE_TIMER", false)
    }
  }
})
