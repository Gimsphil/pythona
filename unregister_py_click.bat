@echo off
setlocal
reg delete "HKCU\Software\Classes\.py" /f
reg delete "HKCU\Software\Classes\PythonA.pyfile" /f
echo [OK] User-level .py mapping removed.
pause
