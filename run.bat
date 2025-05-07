@echo off
setlocal enabledelayedexpansion

REM Get input argument
set "ARG=%1"

REM Load .env file
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" .env`) do (
        set "%%A=%%B"
    )
)

REM Initialize Conda
call conda init >nul
call "%USERPROFILE%\anaconda3\Scripts\activate.bat"

IF "%ARG%"=="touch" (
    REM Start follow-touch in background
    echo Starting follow-touch application in foreground...
    conda run -n follow-touch-env python follow-touch/app.py
) ELSE IF "%ARG%"=="neural" (
    REM Start neural-model in foreground (blocking)
    echo Starting neural-model application in foreground...
    conda run -n neural-model-env streamlit run neural-model/app.py
) ELSE (
    echo ❌ Invalid argument. Use "touch" or "neural".
    exit /b 1
)
endlocal