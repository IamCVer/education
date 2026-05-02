// =========================================================
// * Vue Material Dashboard - v1.5.2
// =========================================================
//
// * Product Page: https://www.creative-tim.com/product/vue-material-dashboard
// * Copyright 2024 Creative Tim (https://www.creative-tim.com)
// * Licensed under MIT (https://github.com/creativetimofficial/vue-material-dashboard/blob/master/LICENSE.md)
//
// * Coded by Creative Tim
//
// =========================================================
//
// * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from "vue";
import VueRouter from "vue-router";
import App from "./App";

// router setup
import routes from "./routes/routes";

// Plugins
import GlobalComponents from "./globalComponents";
import GlobalDirectives from "./globalDirectives";
import Notifications from "./components/NotificationPlugin";

// MaterialDashboard plugin
import MaterialDashboard from "./material-dashboard";

import Chartist from "chartist";

// configure router
const router = new VueRouter({
  routes, // short for routes: routes
  linkExactActiveClass: "nav-item active",
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token');
  
  // 检查路由是否需要认证（默认需要，除非明确设置为 false）
  const requiresAuth = to.matched.some(record => {
    // 如果 meta.requiresAuth 明确设置为 false，则不需要认证
    return record.meta.requiresAuth !== false;
  });

  console.log('Route Guard:', {
    path: to.path,
    requiresAuth,
    hasToken: !!token
  });

  if (requiresAuth && !token) {
    // 需要认证但没有 token，跳转到登录页
    console.log('Redirecting to login - no token');
    next('/login');
  } else if (to.path === '/login' && token) {
    // 已登录用户访问登录页，跳转到仪表盘
    console.log('Redirecting to dashboard - already logged in');
    next('/dashboard');
  } else {
    next();
  }
});

Vue.prototype.$Chartist = Chartist;

Vue.use(VueRouter);
Vue.use(MaterialDashboard);
Vue.use(GlobalComponents);
Vue.use(GlobalDirectives);
Vue.use(Notifications);

// 将 router 暴露给全局，供 http 拦截器使用
window.vueRouter = router;

/* eslint-disable no-new */
new Vue({
  el: "#app",
  render: (h) => h(App),
  router,
  data: {
    Chartist: Chartist,
  },
});
