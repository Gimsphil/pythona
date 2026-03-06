@echo off
setlocal
set BASE_DIR=%~dp0
set PY=

where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py -3
) else (
  where python >nul 2>nul
  if %errorlevel%==0 set PY=python
)

if "%PY%"=="" (
  echo [ERROR] Python not found. Cannot build standalone EXE.
  pause
  exit /b 1
)

cd /d "%BASE_DIR%"
%PY% -m pip install pyinstaller
if errorlevel 1 (
  echo [ERROR] Failed to install pyinstaller.
  pause
  exit /b 1
)

%PY% -m PyInstaller --noconfirm --onefile --windowed --name PythonA_Runner --icon "assets\icons\????_??01.ico" pythona_runner.py
if errorlevel 1 (
  echo [ERROR] Build failed.
  pause
  exit /b 1
)

echo [OK] Build completed: %BASE_DIR%dist\PythonA_Runner.exe
pause
