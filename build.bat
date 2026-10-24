@echo off
rem Build hry Tisic (PyInstaller, onedir) -> dist\Tisic\Tisic.exe
rem Spustit dvojklikom alebo z terminalu PyCharmu: build.bat
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (set PY=.venv\Scripts\python.exe) else (set PY=python)
%PY% -m pip show pyinstaller >nul 2>&1 || %PY% -m pip install pyinstaller
%PY% -m PyInstaller Tisic.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo BUILD ZLYHAL
    pause
    exit /b 1
)
echo.
echo Hotovo: dist\Tisic\Tisic.exe
echo Na rozdanie zbal cely priecinok dist\Tisic do zipu.
pause
