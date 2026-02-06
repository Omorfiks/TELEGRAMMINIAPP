"""
Скрипт для инициализации базы данных
Запустите этот файл один раз для создания таблиц
"""
from database import Base, engine
from models import Product, ProductView

if __name__ == "__main__":
    print("Создание таблиц в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно!")
