@echo off
setlocal

cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente nao encontrado.
    echo Rode antes o arquivo scripts\instalar_primeira_vez.bat
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
start "" http://127.0.0.1:8000/
python manage.py runserver

