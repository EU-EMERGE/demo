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
    REM Start follow-touch in foreground
    echo Starting follow-touch application in foreground...
    call conda activate follow-touch-env
    python -u follow-touch/app.py 2>&1 | tee follow-touch.log
) ELSE IF "%ARG%"=="neural" (
    REM Start neural-model in foreground
    echo Starting neural-model application in foreground...
    call conda activate neural-model-env
    python -u -m streamlit run neural-model/app.py | tee neural-model.log
) ELSE (
    echo ❌ Invalid argument. Use "touch" or "neural".
    exit /b 1
)
endlocal