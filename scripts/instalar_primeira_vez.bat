@echo off
setlocal

cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt

echo.
echo Instalacao concluida.
echo Para abrir o sistema no dia a dia, execute o arquivo scripts\abrir_qi_pipeline.bat
pause

