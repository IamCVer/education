/**
 * Socket.IO 客户端封装
 */
import { io } from "socket.io-client";

const WS_URL = process.env.VUE_APP_WS_URL || "http://localhost:8000";

class SocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  /**
   * 连接到 WebSocket 服务器
   * @param {string} token - 认证 Token
   */
  connect(token) {
    if (this.socket && this.socket.connected) {
      console.log("Socket already connected");
      return;
    }

    this.socket = io(WS_URL, {
      auth: {
        token: token || localStorage.getItem("access_token"),
      },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });

    this.socket.on("connect", () => {
      console.log("✅ WebSocket connected:", this.socket.id);
    });

    this.socket.on("disconnect", (reason) => {
      console.log("❌ WebSocket disconnected:", reason);
    });

    this.socket.on("connect_error", (error) => {
      console.error("WebSocket connection error:", error);
    });

    return this.socket;
  }

  /**
   * 订阅频道
   * @param {string} channel - 频道名称
   * @param {function} callback - 回调函数
   */
  subscribe(channel, callback) {
    if (!this.socket) {
      console.error("Socket not connected. Call connect() first.");
      return;
    }

    // 保存监听器引用
    this.listeners.set(channel, callback);
    this.socket.on(channel, callback);
    console.log(`📡 Subscribed to channel: ${channel}`);
  }

  /**
   * 取消订阅频道
   * @param {string} channel
   */
  unsubscribe(channel) {
    if (!this.socket) return;

    const callback = this.listeners.get(channel);
    if (callback) {
      this.socket.off(channel, callback);
      this.listeners.delete(channel);
      console.log(`🔕 Unsubscribed from channel: ${channel}`);
    }
  }

  /**
   * 发送消息到服务器
   * @param {string} event - 事件名称
   * @param {any} data - 数据
   */
  emit(event, data) {
    if (!this.socket) {
      console.error("Socket not connected");
      return;
    }
    this.socket.emit(event, data);
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.socket) {
      this.listeners.clear();
      this.socket.disconnect();
      this.socket = null;
      console.log("Socket disconnected");
    }
  }

  /**
   * 检查连接状态
   */
  isConnected() {
    return this.socket && this.socket.connected;
  }
}

// 导出单例
export default new SocketService();

