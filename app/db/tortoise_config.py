# app/db/tortoise_config.py (aerich修正版)
"""
提供一个集中的Tortoise-ORM配置，以便在多个进程（backend, worker）中共享。
使用字典格式以确保所有连接参数被正确应用。
"""
from app.core.config import settings

TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": "db_mysql",
                "port": 3306,
                "user": "root",
                "password": "wcy666666", # 使用您在docker-compose.yml中为MySQL设置的密码
                "database": "my_database",
                "charset": "utf8mb4", # 明确指定字符集
            }
        }
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user_model",
                "app.models.qa_history_model",
                "app.models.notification_model",
                "app.models.video_model",  # 新增视频模型
                # "aerich.models" # 移除对尚未安装的aerich库的引用
            ],
            "default_connection": "default",
        },
    },
    # 设置时区
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}