import { createRouter, createWebHistory } from "vue-router"

const routes = [
  {
    path: "/",
    component: () => import("@/views/SignIn.vue"), // lazy loading
    meta: { requiresAuth: false }
  },
  {
    path: "/signup",
    component: () => import("@/views/SignUp.vue"),
    meta: { requiresAuth: false }
  },
  {
    path: "/account",
    component: () => import("@/views/WebMessenger.vue"),
    children: [
      {
        path: "",
        redirect: "/messenger"
      },
      {
        path: "messenger",
        name: "Messenger",
        component: () => import("@/components/Messenger/MessengerPage.vue"),
        meta: { requiresAuth: true }
      },
      {
        path: "files",
        name: "Files",
        component: () => import("@/components/Files/FilesPage.vue"),
        meta: { requiresAuth: true }
      },
      {
        path: "settings",
        name: "Settings",
        component: () => import("@/components/Settings/SettingsPage.vue"),
        meta: { requiresAuth: true }
      },
      {
        path: "calls",
        name: "Calls",
        component: () => import("@/components/Calls/CallsPage.vue"),
        meta: { requiresAuth: true }
      },
      {
        path: "admin",
        name: "AdminPanel",
        component: () => import("@/components/Admin/AdminPage.vue"),
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/account/messenger"
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

router.beforeEach((to, _, next) => {
  if (document.cookie.indexOf("auth_flag=") == -1) { // not authenticated
    if (to.meta.requiresAuth)
      next({path: "/"})
    else
      next()
  } else { // authenticated
    if (!to.meta.requiresAuth)
      next({path: "/account/messenger"})
    else
      next()
  }
})

export default router
