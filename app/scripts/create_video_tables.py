from tortoise import Tortoise
import asyncio

async def init():
    await Tortoise.init(
        db_url='mysql://root:wcy666666@db_mysql:3306/my_database',
        modules={'models': ['app.models.video_model']}
    )
    await Tortoise.generate_schemas()
    print('✅ Video tables created successfully!')
    await Tortoise.close_connections()

if __name__ == '__main__':
    asyncio.run(init())
