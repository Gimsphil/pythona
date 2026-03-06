@echo off
setlocal
set BASE_DIR=%~dp0
set APP=%BASE_DIR%pythona_runner.py

if not exist "%APP%" (
  echo [ERROR] pythona_runner.py not found: %APP%
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%APP%" %*
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python "%APP%" %*
  exit /b %errorlevel%
)

echo [ERROR] Python launcher(py) or python.exe not found.
pause
exit /b 1
