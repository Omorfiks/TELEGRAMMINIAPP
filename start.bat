@echo off
echo Запуск проекта bro shop...
echo.

echo [1/3] Запуск PostgreSQL через Docker...
docker-compose up -d postgres
timeout /t 5 /nobreak >nul

echo [2/3] Инициализация базы данных...
cd backend
python init_db.py
cd ..

echo [3/3] Запуск сервисов...
echo.
echo Бэкенд будет запущен на http://localhost:8000
echo Веб-приложение будет запущено на http://localhost:5173
echo.
echo Откройте новые терминалы для запуска:
echo   1. cd backend ^&^& uvicorn main:app --reload
echo   2. cd webapp ^&^& npm run dev
echo   3. cd bot ^&^& python main.py
echo.
pause
