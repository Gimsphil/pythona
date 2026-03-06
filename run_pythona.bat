@echo off
setlocal
set BASE_DIR=%~dp0
set APP_PY=%BASE_DIR%pythona_runner.py
set APP_EXE=%BASE_DIR%PythonA_Runner.exe
set DIST_EXE=%BASE_DIR%dist\PythonA_Runner.exe

if exist "%APP_EXE%" (
  "%APP_EXE%" %*
  exit /b %errorlevel%
)

if exist "%DIST_EXE%" (
  "%DIST_EXE%" %*
  exit /b %errorlevel%
)

if not exist "%APP_PY%" (
  echo [ERROR] pythona_runner.py not found: %APP_PY%
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%APP_PY%" %*
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python "%APP_PY%" %*
  exit /b %errorlevel%
)

echo [ERROR] Python runtime not found.
echo [INFO] To run without Python installed, build/use PythonA_Runner.exe.
pause
exit /b 1
