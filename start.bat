@echo off
:: Переход в директорию проекта
cd /d C:\spanish_traditions

:: Активация виртуального окружения
call C:\venv\Scripts\activate.bat

:: Проверка версии Python и установленных модулей
python --version
where python
pip show django-ckeditor-5

:: Запуск сервера Django
python manage.py runserver

:: Оставить окно открытым после завершения
pause
