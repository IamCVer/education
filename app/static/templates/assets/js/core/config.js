// API配置文件
window.API_CONFIG = {
    BASE_URL: window.location.origin,
    WS_BASE_URL: window.location.protocol === 'https:' ? 'wss://' + window.location.host : 'ws://' + window.location.host,
    TIMEOUT: 10000,
    HEADERS: {
        'Content-Type': 'application/json'
    }
};


