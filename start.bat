@echo off
:: Укажите полный путь к виртуальному окружению
call C:\venv\Scripts\activate

:: Запуск сервера Django
python manage.py runserver

:: Оставить окно открытым после завершения
pause
