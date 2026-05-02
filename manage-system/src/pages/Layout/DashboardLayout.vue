<template>
  <div class="wrapper" :class="{ 'nav-open': $sidebar.showSidebar }">
    <notifications></notifications>

    <side-bar
      :sidebar-item-color="sidebarBackground"
      :sidebar-background-image="sidebarBackgroundImage"
    >
      <mobile-menu slot="content"></mobile-menu>
      <sidebar-link to="/dashboard">
        <md-icon>dashboard</md-icon>
        <p>仪表盘</p>
      </sidebar-link>
      <sidebar-link to="/users">
        <md-icon>people</md-icon>
        <p>用户管理</p>
      </sidebar-link>
      <sidebar-link to="/logs">
        <md-icon>article</md-icon>
        <p>日志监控</p>
      </sidebar-link>
      <sidebar-link to="/datasets">
        <md-icon>storage</md-icon>
        <p>数据集仓库</p>
      </sidebar-link>
      <!-- 数据表格已隐藏 -->
      <!-- <sidebar-link to="/table">
        <md-icon>content_paste</md-icon>
        <p>数据表格</p>
      </sidebar-link> -->
      <sidebar-link to="/notifications">
        <md-icon>notifications</md-icon>
        <p>通知</p>
      </sidebar-link>
      <sidebar-link to="/user">
        <md-icon>person</md-icon>
        <p>关于我们</p>
      </sidebar-link>
    </side-bar>

    <div class="main-panel">
      <top-navbar></top-navbar>

      <fixed-plugin
        :color.sync="sidebarBackground"
        :image.sync="sidebarBackgroundImage"
      >
      </fixed-plugin>

      <dashboard-content> </dashboard-content>

      <content-footer v-if="!$route.meta.hideFooter"></content-footer>
    </div>
  </div>
</template>

<script>
import TopNavbar from "./TopNavbar.vue";
import ContentFooter from "./ContentFooter.vue";
import DashboardContent from "./Content.vue";
import MobileMenu from "@/pages/Layout/MobileMenu.vue";
import FixedPlugin from "./Extra/FixedPlugin.vue";

export default {
  components: {
    TopNavbar,
    DashboardContent,
    ContentFooter,
    MobileMenu,
    FixedPlugin,
  },
  data() {
    return {
      sidebarBackground: "green",
      sidebarBackgroundImage: require("@/assets/img/sidebar-2.jpg"),
    };
  },
};
</script>
