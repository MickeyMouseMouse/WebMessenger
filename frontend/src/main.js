import { createApp } from "vue"
import App from "@/App.vue"
import router from "@/router"
import store from "@/store"

import "primevue/resources/themes/saga-blue/theme.css"
import "primevue/resources/primevue.min.css"
import "primeicons/primeicons.css"
import PrimeVue from "primevue/config"
import InputText from "primevue/inputtext"
import Password from "primevue/password"
import Button from "primevue/button"
import Toast from "primevue/toast"
import ToastService from "primevue/toastservice"
import Dialog from "primevue/dialog"
import TextArea from "primevue/textarea"
import Checkbox from "primevue/checkbox"
import InputSwitch from "primevue/inputswitch"
import Menu from "primevue/menu"
import Skeleton from "primevue/skeleton"
import TabView from "primevue/tabview"
import TabPanel from "primevue/tabpanel"
import Paginator from "primevue/paginator"

const app = createApp(App)

app.component(InputText.name, InputText)
app.component(Password.name, Password)
app.component(Button.name, Button)
app.component(Toast.name, Toast)
app.component("PopUp", Dialog)
app.component(TextArea.name, TextArea)
app.component(Checkbox.name, Checkbox)
app.component(InputSwitch.name, InputSwitch)
app.component(Menu.name, Menu)
app.component(Skeleton.name, Skeleton)
app.component(TabView.name, TabView)
app.component(TabPanel.name, TabPanel)
app.component(Paginator.name, Paginator)


app.use(store).use(router).use(PrimeVue).use(ToastService)
app.mount("#app")
