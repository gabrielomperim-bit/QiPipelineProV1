@echo off
setlocal

cd /d "%~dp0.."

set "PYTHON_CMD=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
)

echo.
echo Reiniciar projeto para outro usuario
echo.
echo 1. Limpar dados locais e manter a base CVM ^(Recomendado^)
echo 2. Limpar tudo, incluindo a base CVM
echo 3. Cancelar
echo.
set /p RESET_OPTION=Escolha uma opcao: 

if "%RESET_OPTION%"=="1" (
    "%PYTHON_CMD%" scripts\reset_project.py --mode keep-cvm
    goto :end
)

if "%RESET_OPTION%"=="2" (
    "%PYTHON_CMD%" scripts\reset_project.py --mode full
    goto :end
)

echo Operacao cancelada.

:end
echo.
pause
