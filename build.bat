@echo off
setlocal enabledelayedexpansion

REM Get input argument
set "ARG=%1"

IF "%ARG%"=="touch" (
    set "ENV_NAME=follow-touch-env"
    set "PYTHON_VERSION=3.8"
    set "REQUIREMENTS_PATH=follow-touch/requirements.txt"
) ELSE IF "%ARG%"=="neural" (
    set "ENV_NAME=neural-model-env"
    set "PYTHON_VERSION=3.11"
    set "REQUIREMENTS_PATH=neural-model/requirements.txt"
) ELSE (
    echo ❌ Invalid argument. Use "touch" or "neural".
    exit /b 1
)

REM Initialize conda for this shell
call conda init >nul

REM Check if environment exists
conda info --envs | findstr /c:"%ENV_NAME%" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo Creating Conda environment: %ENV_NAME% with Python %PYTHON_VERSION%...
    conda create -y -n %ENV_NAME% python=%PYTHON_VERSION%
) ELSE (
    echo Conda environment '%ENV_NAME%' already exists. Skipping creation.
)

REM Activate environment
echo Activating Conda environment: %ENV_NAME%...
call conda activate %ENV_NAME%

REM Install requirements
echo Installing Python dependencies from %REQUIREMENTS_PATH%...
pip install -r %REQUIREMENTS_PATH%

echo ✅ Environment setup complete.
endlocal