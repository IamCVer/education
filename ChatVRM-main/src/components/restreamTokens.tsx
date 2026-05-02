import React, { useState, useEffect } from 'react';
import { TextButton } from './textButton';
import Cookies from 'js-cookie';
import { websocketService } from '../services/websocketService';
import { refreshAccessToken } from '../utils/auth';
import { tokenRefreshService } from '../services/tokenRefreshService';
import { Link } from './link';

interface RestreamTokens {
    access_token: string;
    refresh_token: string;
}

// Add new interface for chat messages
interface ChatMessage {
    username: string;
    displayName: string;
    timestamp: number;
    text: string;
}

type Props = {
    onTokensUpdate: (tokens: any) => void;
    onChatMessage: (message: string) => void;
};

export const RestreamTokens: React.FC<Props> = ({ onTokensUpdate, onChatMessage }) => {
    const [jsonInput, setJsonInput] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [rawMessages, setRawMessages] = useState<any[]>([]);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isRefreshing, setIsRefreshing] = useState(false);

    // Load saved tokens on component mount
    useEffect(() => {
        const savedTokens = Cookies.get('restream_tokens');
        if (savedTokens) {
            try {
                const tokens = JSON.parse(savedTokens);
                setJsonInput(JSON.stringify(tokens, null, 2));
            } catch (err) {
                console.error('Error parsing saved tokens:', err);
            }
        }
    }, []);

    const handleJsonPaste = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = event.target.value;
        setJsonInput(newValue);
        setError(null);

        try {
            const tokens: RestreamTokens = JSON.parse(newValue);

            if (!tokens.access_token || !tokens.refresh_token) {
                setError('令牌格式无效');
                return;
            }

            const formattedJson = JSON.stringify(tokens, null, 2);
            Cookies.set('restream_tokens', formattedJson, { expires: 30 });
            onTokensUpdate(tokens);

            setError(null);
            setJsonInput(formattedJson);
        } catch (err) {
            setError('JSON 格式无效，请检查您的输入。');
        }
    };

    const handleClearTokens = () => {
        // Stop auto-refresh when tokens are cleared
        tokenRefreshService.stopAutoRefresh();

        Cookies.remove('restream_tokens');
        onTokensUpdate(null);
        setJsonInput('');
        setError(null);
    };

    useEffect(() => {
        // Add listeners for websocket events and token refresh events
        const handleConnectionChange = (isConnected: boolean) => {
            setIsConnected(isConnected);
            setError(null);
        };

        const handleRawMessage = (message: any) => {
            setRawMessages(prev => [...prev, message]);
        };

        const handleChatMessage = (message: ChatMessage) => {
            setMessages(prev => [...prev, message]);
        };

        // Add new handler for token refresh
        const handleTokenRefresh = (newTokens: RestreamTokens) => {
            const formattedJson = JSON.stringify(newTokens, null, 2);
            setJsonInput(formattedJson);
            setError(null);

            // Re-attach WebSocket event listeners after reconnection
            websocketService.off('rawMessage', handleRawMessage);
            websocketService.off('chatMessage', handleChatMessage);
            websocketService.on('rawMessage', handleRawMessage);
            websocketService.on('chatMessage', handleChatMessage);
        };

        websocketService.on('connectionChange', handleConnectionChange);
        websocketService.on('rawMessage', handleRawMessage);
        websocketService.on('chatMessage', handleChatMessage);
        tokenRefreshService.on('tokensRefreshed', handleTokenRefresh);

        // Check initial connection state
        setIsConnected(websocketService.isConnected());

        return () => {
            websocketService.off('connectionChange', handleConnectionChange);
            websocketService.off('rawMessage', handleRawMessage);
            websocketService.off('chatMessage', handleChatMessage);
            tokenRefreshService.off('tokensRefreshed', handleTokenRefresh);
        };
    }, []);

    const connectWebSocket = () => {
        try {
            const tokens: RestreamTokens = JSON.parse(jsonInput);

            if (!tokens.access_token) {
                setError('No access token available');
                return;
            }

            websocketService.connect(tokens.access_token);
            // Start auto-refresh when connecting
            tokenRefreshService.startAutoRefresh(tokens, onTokensUpdate);
        } catch (err) {
            setError('Invalid JSON format or connection error');
        }
    };

    const disconnectWebSocket = () => {
        websocketService.disconnect();
        // Stop auto-refresh when disconnecting
        tokenRefreshService.stopAutoRefresh();
    };

    // Modify sendTestMessage to match websocketService's handler format
    const sendTestMessage = () => {
        const testMessage = {
            payload: {
                eventPayload: {
                    author: {
                        username: 'tester1',
                        displayName: 'Test User'
                    },
                    timestamp: Math.floor(Date.now() / 1000),
                    text: 'Test message ' + Math.random().toString(36).substring(7)
                }
            }
        };

        websocketService.handleChatMessage(testMessage);
    };

    const handleRefreshTokens = async () => {
        try {
            const currentTokens: RestreamTokens = JSON.parse(jsonInput);
            setIsRefreshing(true);
            setError(null);

            const newTokens = await refreshAccessToken(currentTokens.refresh_token);

            // Format the JSON string with proper indentation
            const formattedJson = JSON.stringify(newTokens, null, 2);

            // Save to cookies with 30 days expiry
            Cookies.set('restream_tokens', formattedJson, { expires: 30 });
            onTokensUpdate(newTokens);
            setJsonInput(formattedJson);
        } catch (err) {
            setError('刷新令牌失败，请检查您的刷新令牌。');
        } finally {
            setIsRefreshing(false);
        }
    };

    return (
        <div className="my-40">
            <div className="my-16 typography-20 font-bold">Restream 集成</div>
            <div className="my-16">
                从 <Link
                    url="https://restream-token-fetcher.vercel.app/"
                    label="Restream Token Fetcher"
                /> 获取您的 Restream 身份验证令牌 JSON。它授权 ChatVRM 监听您来自 Restream 的聊天消息（目前支持 X 和 Twitch 来源）。
                粘贴您的令牌 JSON 并点击开始监听按钮后，ChatVRM 将监听您的聊天消息，并定期为您刷新令牌。
            </div>
            <div className="my-16">
                在此粘贴您的 Restream 身份验证令牌 JSON：
            </div>
            <textarea
                value={jsonInput}
                onChange={handleJsonPaste}
                placeholder='{"access_token": "...", "refresh_token": "..."}'
                className="px-16 py-8 bg-surface1 hover:bg-surface1-hover h-[120px] rounded-8 w-full font-mono text-sm"
            />
            {error && (
                <div className="text-red-500 my-8">{error}</div>
            )}
            <div className="flex gap-4 my-16">
                <div className="pr-8">
                    <TextButton
                        onClick={isConnected ? disconnectWebSocket : connectWebSocket}
                    >
                        {isConnected ? '停止监听' : '开始监听'}
                    </TextButton>
                </div>
                <div className="pr-8">
                    <TextButton onClick={handleClearTokens}>清除令牌</TextButton>
                </div>
                <div className="pr-8">
                    <TextButton
                        onClick={handleRefreshTokens}
                        disabled={isRefreshing || !jsonInput}
                    >
                        {isRefreshing ? '刷新中...' : '刷新令牌'}
                    </TextButton>
                </div>
                {isConnected && (
                    <div>
                        <TextButton onClick={sendTestMessage}>发送测试消息</TextButton>
                    </div>
                )}
            </div>

            {/* Connection Status */}
            <div className={`my-8 p-8 rounded-4 ${isConnected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                状态：{isConnected ? '已连接' : '未连接'}
            </div>

            {/* Filtered Chat Messages */}
            {messages.length > 0 && (
                <div className="my-16">
                    <div className="typography-16 font-bold mb-8">过滤的聊天消息：</div>
                    <div className="bg-surface1 p-16 rounded-8 max-h-[400px] overflow-y-auto">
                        {messages.map((msg, index) => (
                            <div key={index} className="font-mono text-sm mb-8">
                                [{new Date(msg.timestamp * 1000).toLocaleTimeString()}]
                                <strong>{msg.displayName}</strong> (@{msg.username}):
                                {msg.text}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Raw Messages */}
            {rawMessages.length > 0 && (
                <div className="my-16">
                    <div className="typography-16 font-bold mb-8">原始消息：</div>
                    <div className="bg-surface1 p-16 rounded-8 max-h-[400px] overflow-y-auto">
                        {rawMessages.map((msg, index) => (
                            <div key={index} className="font-mono text-sm mb-8">
                                {JSON.stringify(msg, null, 2)}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="text-sm text-gray-600">
                Your Restream tokens will be stored securely in browser cookies and restored when you return.
            </div>
        </div>
    );
}; 