@echo off
setlocal

:: Set the directory to the location of the bat file
cd /d "%~dp0"

echo =========================================
echo       ⚡ Starting M! TuneCLI ⚡
echo =========================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

:: 2. Ensure .env exists
if not exist ".env" (
    echo [INFO] Creating default .env file from .env.example...
    if exist ".env.example" (
        copy .env.example .env >nul
    ) else (
        echo # TuneCLI Environment Config > .env
    )
)

:: 3. Create Virtual Environment if it doesn't exist
if exist "venv\" goto skip_venv
echo [INFO] First time setup detected.
echo [INFO] Creating isolated Virtual Environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
:skip_venv

:: Activate the virtual environment
call venv\Scripts\activate

:: 4. Check if core requirements are installed by testing for 'textual'
python -c "import textual" >nul 2>&1
if not errorlevel 1 goto skip_install
echo [INFO] Installing required dependencies... This may take a minute.
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
:skip_install

:: 5. Launch the application
echo [INFO] Launching Application...
python main.py

:: 6. Keep window open if the app crashes
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] TuneCLI crashed. See the error message above.
    pause
)

endlocal
