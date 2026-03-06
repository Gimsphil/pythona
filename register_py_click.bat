@echo off
setlocal
set APP_BAT=D:\PythonA\run_pythona.bat

if not exist "%APP_BAT%" (
  echo [ERROR] Launcher not found: %APP_BAT%
  pause
  exit /b 1
)

reg add "HKCU\Software\Classes\.py" /ve /d "PythonA.pyfile" /f
reg add "HKCU\Software\Classes\PythonA.pyfile" /ve /d "Python File (PythonA)" /f
reg add "HKCU\Software\Classes\PythonA.pyfile\shell\open\command" /ve /d "\"%APP_BAT%\" \"%%1\"" /f

echo [OK] .py double-click is now mapped to PythonA Runner (current user only).
echo Re-login or restart Explorer if needed.
pause
