import aiohttp
import os

async def upload_photo_to_backend(photo_file_id: str, bot_token: str, backend_url: str):
    """Загружает фото на бэкенд и возвращает URL"""
    from aiogram import Bot
    
    bot = Bot(token=bot_token)
    
    try:
        # Скачиваем фото из Telegram
        file = await bot.get_file(photo_file_id)
        file_data = await bot.download_file(file.file_path)
        
        # Отправляем на бэкенд
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', file_data, filename=os.path.basename(file.file_path))
            
            async with session.post(f"{backend_url}/api/admin/upload", data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("url")
        
        return None
    except Exception as e:
        print(f"Error uploading photo: {e}")
        return None
