import DashboardLayout from "@/pages/Layout/DashboardLayout.vue";

import Dashboard from "@/pages/Dashboard.vue";
import UserProfile from "@/pages/UserProfile.vue";
import TableList from "@/pages/TableList.vue";
import Typography from "@/pages/Typography.vue";
import Icons from "@/pages/Icons.vue";
import Maps from "@/pages/Maps.vue";
import Notifications from "@/pages/Notifications.vue";
import UpgradeToPRO from "@/pages/UpgradeToPRO.vue";

// 新增页面
import Users from "@/pages/Users.vue";
import Conversations from "@/pages/Conversations.vue";
import Logs from "@/pages/Logs.vue";
import Datasets from "@/pages/Datasets.vue";
import Login from "@/pages/Login.vue";

const routes = [
  {
    path: "/login",
    name: "登录",
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: "/",
    redirect: '/login'
  },
  {
    path: "/",
    component: DashboardLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "dashboard",
        name: "仪表盘",
        component: Dashboard,
      },
      {
        path: "users",
        name: "用户管理",
        component: Users,
      },
      {
        path: "conversations/:userId",
        name: "对话记录",
        component: Conversations,
        props: true,
      },
      {
        path: "logs",
        name: "日志监控",
        component: Logs,
      },
      {
        path: "datasets",
        name: "数据集仓库",
        component: Datasets,
      },
      {
        path: "table",
        name: "数据表格",
        component: TableList,
      },
      {
        path: "typography",
        name: "排版样式",
        component: Typography,
      },
      {
        path: "icons",
        name: "图标",
        component: Icons,
      },
      {
        path: "maps",
        name: "地图",
        meta: {
          hideFooter: true,
        },
        component: Maps,
      },
      {
        path: "notifications",
        name: "通知",
        component: Notifications,
      },
      {
        path: "user",
        name: "关于我们",
        component: UserProfile,
      },
      {
        path: "upgrade",
        name: "升级专业版",
        component: UpgradeToPRO,
      },
    ],
  },
];

export default routes;
