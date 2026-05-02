import Vue from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia, PiniaVuePlugin } from 'pinia'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

// 使用 Pinia 插件
Vue.use(PiniaVuePlugin)
const pinia = createPinia()

// 使用 Element UI
Vue.use(ElementUI)

Vue.config.productionTip = false

new Vue({
  router,
  pinia,
  render: h => h(App),
}).$mount('#app')
