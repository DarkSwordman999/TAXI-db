@echo off
rem Run run_app.sh on Windows from PowerShell or cmd: .\run_app.cmd
rem On Linux and macOS run ./run_app.sh directly.
rem Uses bash from Git for Windows (bash.exe from WSL in System32 does not fit)
rem and switches the console to UTF-8 so Cyrillic output is readable.
setlocal
for /f "tokens=2 delims=:." %%C in ('chcp') do set "OLD_CP=%%C"
chcp 65001 >nul
set "PGCLIENTENCODING=UTF8"
set "PYTHONIOENCODING=utf-8"
set "RC=1"

set "BASH_EXE="
for /f "delims=" %%G in ('where git 2^>nul') do (
    if not defined BASH_EXE if exist "%%~dpG..\bin\bash.exe" set "BASH_EXE=%%~dpG..\bin\bash.exe"
    if not defined BASH_EXE if exist "%%~dpG..\..\bin\bash.exe" set "BASH_EXE=%%~dpG..\..\bin\bash.exe"
)
if not defined BASH_EXE if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH_EXE (
    echo ОШИБКА: не найден Git for Windows ^(bash.exe^), установите его: https://git-scm.com/download/win
    goto end
)

"%BASH_EXE%" "%~dp0run_app.sh" %*
set "RC=%ERRORLEVEL%"

:end
chcp %OLD_CP% >nul
exit /b %RC%
