import { useState, useCallback, useEffect } from "react";
import { Link } from "./link";
import { login, getAuthToken } from "@/features/chat/fastApiChat";

type Props = {
  openAiKey: string;
  elevenLabsKey: string;
  onChangeAiKey: (openAiKey: string) => void;
  onChangeElevenLabsKey: (elevenLabsKey: string) => void;
};
export const Introduction = ({ openAiKey, elevenLabsKey, onChangeAiKey, onChangeElevenLabsKey }: Props) => {
  const [opened, setOpened] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false); // 避免SSR hydration错误
  const [isMounted, setIsMounted] = useState(false);
  
  // 首次挂载后检查登录状态
  useEffect(() => {
    setIsMounted(true);
    setIsLoggedIn(getAuthToken() !== null);
  }, []);

  const handleAiKeyChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      onChangeAiKey(event.target.value);
    },
    [onChangeAiKey]
  );

  const handleElevenLabsKeyChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      onChangeElevenLabsKey(event.target.value);
    },
    [onChangeElevenLabsKey]
  );

  const handleLogin = async () => {
    setLoginError("");
    const token = await login(username, password);
    if (token) {
      setLoginSuccess(true);
      setIsLoggedIn(true); // 更新登录状态
      setTimeout(() => {
        setOpened(false);
      }, 1000);
    } else {
      setLoginError("登录失败，请检查用户名和密码");
    }
  };

  return opened ? (
    <div className="absolute z-40 w-full h-full px-24 py-40  bg-black/30 font-M_PLUS_2">
      <div className="mx-auto my-auto max-w-3xl max-h-full p-24 overflow-auto bg-white rounded-16">
        <div className="my-24">
          <div className="my-8 font-bold typography-20 text-secondary ">
            关于 ChatVRM
          </div>
          <div>
            使用Web浏览器即可与3D角色对话，支持语音输入、文字输入和语音合成。您可以更换角色（VRM）、设置个性并调整声音。
          </div>
        </div>
        
        {/* FastAPI 登录状态（仅在客户端挂载后显示） */}
        {isMounted && isLoggedIn && (
          <div className="my-24 p-16 bg-green-100 border-2 border-green-500 rounded-8">
            <div className="font-bold text-green-700">
              ✅ 已连接到本地AI服务
            </div>
            <div className="text-sm text-green-600 mt-4">
              使用本地LLM和TTS引擎，无需第三方API密钥
            </div>
          </div>
        )}
        
        {isMounted && !isLoggedIn && !showLogin && (
          <div className="my-24 p-16 bg-blue-100 border-2 border-blue-500 rounded-8">
            <div className="font-bold text-blue-700 mb-8">
              🚀 推荐：使用本地AI服务
            </div>
            <div className="text-sm text-blue-600 mb-12">
              连接到本地FastAPI后端，使用免费的本地LLM和TTS引擎
            </div>
            <button
              onClick={() => setShowLogin(true)}
              className="font-bold bg-blue-600 hover:bg-blue-700 text-white px-16 py-6 rounded-4"
            >
              登录使用本地AI
            </button>
          </div>
        )}
        
        {/* 登录表单 */}
        {isMounted && !isLoggedIn && showLogin && (
          <div className="my-24 p-16 bg-white border-2 border-gray-300 rounded-8">
            <div className="font-bold text-secondary mb-12">
              登录本地AI服务
            </div>
            <div className="mb-8">
              <input
                id="username"
                name="username"
                type="text"
                placeholder="用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="px-16 py-8 w-full h-40 bg-surface3 hover:bg-surface3-hover rounded-4 mb-8"
              />
              <input
                id="password"
                name="password"
                type="password"
                placeholder="密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                className="px-16 py-8 w-full h-40 bg-surface3 hover:bg-surface3-hover rounded-4"
              />
            </div>
            {loginError && (
              <div className="text-red-600 text-sm mb-8">❌ {loginError}</div>
            )}
            {loginSuccess && (
              <div className="text-green-600 text-sm mb-8">✅ 登录成功！</div>
            )}
            <div className="flex gap-8">
              <button
                onClick={handleLogin}
                disabled={!username || !password}
                className="font-bold bg-secondary hover:bg-secondary-hover active:bg-secondary-press disabled:bg-secondary-disabled text-white px-16 py-6 rounded-4 flex-1"
              >
                登录
              </button>
              <button
                onClick={() => setShowLogin(false)}
                className="font-bold bg-gray-500 hover:bg-gray-600 text-white px-16 py-6 rounded-4"
              >
                取消
              </button>
            </div>
            <div className="text-sm text-gray-600 mt-8">
              没有账号？访问{" "}
              <a 
                href="http://localhost:8000/static/templates/pages/auth/register.html" 
                target="_blank"
                className="text-blue-600 hover:underline"
              >
                注册页面
              </a>
            </div>
          </div>
        )}
        <div className="my-24">
          <div className="my-8 font-bold typography-20 text-secondary">
            技术栈
          </div>
          <div>
            使用{" "}
            <Link
              url={"https://github.com/pixiv/three-vrm"}
              label={"@pixiv/three-vrm"}
            />{" "}
            渲染3D模型，本地FastAPI提供LLM对话，本地Piper引擎实现中文语音合成。
          </div>
        </div>

        {/* 可选：ElevenLabs API（演示模式） */}
        {isMounted && !isLoggedIn && (
          <div className="my-24">
            <div className="my-8 font-bold typography-20 text-secondary">
              或使用演示模式（需要ElevenLabs API）
            </div>
            <input
              id="elevenLabsKey"
              name="elevenLabsKey"
              type="text"
              placeholder="可选：ElevenLabs API密钥"
              value={elevenLabsKey}
              onChange={handleElevenLabsKeyChange}
              className="my-4 px-16 py-8 w-full h-40 bg-surface3 hover:bg-surface3-hover rounded-4 text-ellipsis"
            ></input>
            <div className="text-sm text-gray-600">
              如果不登录本地服务，可以输入ElevenLabs API密钥使用云端TTS（需要付费）
            </div>
          </div>
        )}
        <div className="my-24">
          <button
            onClick={() => {
              setOpened(false);
            }}
            className="font-bold bg-secondary hover:bg-secondary-hover active:bg-secondary-press disabled:bg-secondary-disabled text-white px-24 py-8 rounded-oval text-lg"
          >
            {isMounted && isLoggedIn ? "开始对话 →" : "跳过并开始（演示模式）"}
          </button>
          {isMounted && !isLoggedIn && (
            <div className="mt-8 text-sm text-gray-600">
              💡 提示：登录后可使用本地AI，无需第三方API
            </div>
          )}
        </div>
      </div>
    </div>
  ) : null;
};
