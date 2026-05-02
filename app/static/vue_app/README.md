# 智能问答系统 - Vue 3 前端

基于 `chat-demo-main` 样式的智能问答系统前端，采用 Vue 3 + Vite + Pinia + Element Plus 技术栈。

## 功能特性

- ✅ 聊天对话界面（沿用 chat-demo-main 的 UI 设计）
- ✅ WebSocket 实时通信
- ✅ TTS 语音生成（自动播放）
- ✅ Markdown 渲染与代码高亮
- ✅ 对话历史管理
- ✅ 暗黑/明亮主题切换
- ✅ 外链跳转到心灵助手（端口 3001）
- ✅ 外链跳转到知识图谱可视化（端口 3000）

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 新一代前端构建工具
- **Vue Router** - 官方路由管理器
- **Pinia** - 状态管理库
- **Element Plus** - Vue 3 组件库
- **Axios** - HTTP 客户端
- **Marked** - Markdown 解析器
- **Highlight.js** - 代码语法高亮

## 项目结构

```
vue_app/
├── public/               # 静态资源
├── src/
│   ├── api/             # API 接口封装
│   │   ├── request.js   # Axios 封装
│   │   └── qa.js        # 问答相关 API
│   ├── assets/          # 资源文件（从 chat-demo-main 复制）
│   ├── components/      # 公共组件
│   ├── router/          # 路由配置
│   │   └── index.js
│   ├── stores/          # Pinia 状态管理
│   │   ├── user.js      # 用户状态
│   │   └── chat.js      # 聊天状态
│   ├── views/           # 页面组件
│   │   └── ChatPage.vue # 聊天页面
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── .env.example         # 环境变量示例
├── index.html           # HTML 模板
├── package.json         # 依赖配置
├── vite.config.js       # Vite 配置
└── README.md            # 项目文档
```

## 环境配置

### 创建环境变量文件

复制并创建 `.env` 文件（开发环境）：

```bash
# 开发环境
VITE_API_BASE=http://localhost:8000/api
VITE_WS_BASE=ws://localhost:8000/ws/chat
VITE_TTS_ENDPOINT=http://localhost:9000/api/tts
VITE_MIND_ASSIST_URL=http://localhost:3001
VITE_GRAPH_URL=http://localhost:3000
```

创建 `.env.production` 文件（生产环境）：

```bash
# 生产环境
VITE_API_BASE=/api
VITE_WS_BASE=ws://your-domain.com/ws/chat
VITE_TTS_ENDPOINT=http://your-domain.com:9000/api/tts
VITE_MIND_ASSIST_URL=http://your-domain.com:3001
VITE_GRAPH_URL=http://your-domain.com:3000
```

## 安装依赖

```bash
npm install
```

## 开发运行

```bash
npm run dev
```

应用将运行在 `http://localhost:5173`

## 生产构建

```bash
npm run build
```

构建产物会生成在 `dist/` 目录。

## 部署说明

### 方式一：复制到 static 目录

```bash
# 构建
npm run build

# 复制到后端 static 目录
xcopy dist D:\code\education\app\static\vue_dist\ /E /I /Y
```

### 方式二：使用 Nginx 代理

在 `nginx.conf` 中添加：

```nginx
location /static/vue_app/ {
    alias D:/code/education/app/static/vue_app/dist/;
    try_files $uri $uri/ /index.html;
}

location /api/ {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 方式三：FastAPI 静态文件挂载

在 FastAPI 主文件中：

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static/vue_app", StaticFiles(directory="app/static/vue_app/dist"), name="vue_app")
```

## API 接口说明

### 后端接口要求

- **提交问题**: `POST /api/v1/questions`
- **WebSocket**: `ws://localhost:8000/api/v1/ws/qa?token={token}`
- **TTS 服务**: `GET http://localhost:9000/api/tts?text={text}`

### WebSocket 消息格式

**接收消息**：

```json
{
  "type": "answer",
  "data": {
    "answer": "AI 回复内容",
    "sources": []
  },
  "question_id": "xxx"
}

{
  "type": "audio_ready",
  "data": {
    "audio_url": "/path/to/audio.wav"
  },
  "question_id": "xxx"
}

{
  "type": "error",
  "message": "错误信息"
}
```

## 功能说明

### 1. 聊天对话

- 支持 Markdown 格式渲染
- 代码高亮显示（使用 Highlight.js）
- 流式输出效果
- 自动滚动到最新消息

### 2. TTS 语音

- AI 回复后自动生成语音
- 点击麦克风图标手动生成
- 音频播放器内嵌在消息中

### 3. 对话管理

- 新建对话
- 对话历史保存（localStorage）
- 清除所有对话
- 自动生成对话标题

### 4. 外部功能

- **心灵助手**: 点击侧边栏按钮跳转到 `http://localhost:3001`
- **知识图谱**: 点击侧边栏按钮跳转到 `http://localhost:3000`

### 5. 主题切换

- 明亮主题 / 暗黑主题
- 设置自动保存到 localStorage

## 注意事项

1. **认证**: 需要在 `localStorage` 中存储 `userToken` 或 `access_token`
2. **跨域**: 开发环境已配置 Vite 代理，生产环境需配置 Nginx 或后端 CORS
3. **WebSocket**: 确保后端 WebSocket 服务正常运行
4. **TTS 服务**: 确保 TTS 服务在 9000 端口运行
5. **心灵助手与知识图谱**: 确保对应的 Docker 容器在 3001 和 3000 端口运行

## 开发建议

### 添加新功能

1. 在 `src/api/` 中添加 API 接口
2. 在 `src/stores/` 中管理状态
3. 在 `src/views/` 或 `src/components/` 中创建组件
4. 在 `src/router/` 中添加路由

### 调试技巧

- 使用 Vue DevTools 查看组件状态
- 检查浏览器控制台的 WebSocket 连接日志
- 使用 Network 面板查看 API 请求

## 常见问题

### Q: WebSocket 连接失败？
A: 检查后端服务是否运行，确认 token 是否有效。

### Q: TTS 不工作？
A: 确认 TTS 服务在 9000 端口运行，检查 `.env` 配置。

### Q: 样式显示异常？
A: 确保 `src/assets/` 目录已从 `chat-demo-main` 完整复制。

### Q: 路由跳转到外部链接不生效？
A: 检查 `.env` 中的 `VITE_MIND_ASSIST_URL` 和 `VITE_GRAPH_URL` 配置。

## License

MIT

## 联系方式

如有问题，请联系项目维护者。

