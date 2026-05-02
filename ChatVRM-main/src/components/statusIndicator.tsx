type Props = {
  status: 'connected' | 'disconnected' | 'error';
  isLoggedIn: boolean;
};

export const StatusIndicator = ({ status, isLoggedIn }: Props) => {
  const statusText = {
    connected: '✅ 已连接到 FastAPI',
    disconnected: '⚪ 未连接',
    error: '❌ 连接错误'
  };
  
  const statusColor = {
    connected: 'bg-green-500',
    disconnected: 'bg-gray-500',
    error: 'bg-red-500'
  };
  
  return (
    <div className="fixed top-16 right-16 z-50 flex items-center gap-8 bg-white/90 backdrop-blur-sm px-16 py-8 rounded-16 shadow-lg">
      <div className={`w-8 h-8 rounded-full ${statusColor[status]}`}></div>
      <span className="text-text-primary typography-12 font-bold">
        {statusText[status]}
      </span>
      {!isLoggedIn && (
        <span className="text-red-500 typography-12">(未登录)</span>
      )}
    </div>
  );
};

