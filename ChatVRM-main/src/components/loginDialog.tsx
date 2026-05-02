import { useState } from 'react';
import { login, isAuthenticated, logout } from '@/features/chat/fastApiChat';

type Props = {
  onLoginSuccess: () => void;
};

export const LoginDialog = ({ onLoginSuccess }: Props) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(isAuthenticated());
  
  const handleLogin = async () => {
    if (!username || !password) {
      setError('请输入用户名和密码');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const token = await login(username, password);
      if (token) {
        setLoggedIn(true);
        setPassword('');
        onLoginSuccess();
      } else {
        setError('登录失败，请检查用户名和密码');
      }
    } catch (err) {
      setError('登录失败：' + (err instanceof Error ? err.message : '未知错误'));
    } finally {
      setLoading(false);
    }
  };
  
  const handleLogout = () => {
    logout();
    setLoggedIn(false);
    setUsername('');
    setPassword('');
    setError('');
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleLogin();
    }
  };
  
  if (loggedIn) {
    return (
      <div className="bg-surface1 rounded-16 p-16">
        <div className="mb-8 text-text-primary typography-16 font-bold">
          ✅ 已登录到 FastAPI 后端
        </div>
        <div className="mb-16 text-text-secondary typography-14">
          用户: {username || '已认证用户'}
        </div>
        <button
          onClick={handleLogout}
          className="bg-secondary hover:bg-secondary-hover active:bg-secondary-press rounded-oval px-24 py-8 text-white typography-14 font-bold"
        >
          退出登录
        </button>
      </div>
    );
  }
  
  return (
    <div className="bg-surface1 rounded-16 p-16">
      <div className="mb-16 text-text-primary typography-16 font-bold">
        登录 FastAPI 后端
      </div>
      
      <div className="mb-8">
        <label className="block text-text-secondary typography-12 mb-4">
          用户名
        </label>
        <input 
          type="text" 
          placeholder="输入用户名" 
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          className="w-full bg-surface2 hover:bg-surface2-hover focus:bg-surface2 rounded-8 px-12 py-8 text-text-primary typography-14 disabled:opacity-50"
        />
      </div>
      
      <div className="mb-16">
        <label className="block text-text-secondary typography-12 mb-4">
          密码
        </label>
        <input 
          type="password" 
          placeholder="输入密码"
          value={password} 
          onChange={(e) => setPassword(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          className="w-full bg-surface2 hover:bg-surface2-hover focus:bg-surface2 rounded-8 px-12 py-8 text-text-primary typography-14 disabled:opacity-50"
        />
      </div>
      
      {error && (
        <div className="mb-16 text-red-500 typography-12 bg-red-50 rounded-8 p-8">
          ⚠️ {error}
        </div>
      )}
      
      <button 
        onClick={handleLogin}
        disabled={loading}
        className="w-full bg-secondary hover:bg-secondary-hover active:bg-secondary-press disabled:bg-secondary-disabled rounded-oval px-24 py-8 text-white typography-14 font-bold"
      >
        {loading ? '登录中...' : '登录'}
      </button>
      
      <div className="mt-12 text-text-secondary typography-12">
        提示：使用 FastAPI 后端的账号登录
      </div>
    </div>
  );
};

