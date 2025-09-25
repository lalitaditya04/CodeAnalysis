@echo off
echo Starting Code Quality Dashboard...
echo.

REM Check if conda environment exists
conda env list | findstr "codeanalysis" >nul
if errorlevel 1 (
    echo Creating conda environment...
    conda create -n codeanalysis python=3.10 -y
)

REM Activate conda environment
echo Activating conda environment...
call conda activate codeanalysis

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo Please edit .env file with your configuration before running the application.
    echo You can add a GitHub token for better API rate limits.
    echo.
    pause
)

REM Run database migration
echo.
echo Checking database schema...
python migrate_database.py
if errorlevel 1 (
    echo.
    echo Database migration failed. Please check the error messages above.
    pause
    exit /b 1
)

REM Start the application
echo.
echo Starting the Code Quality Dashboard...
echo Open your browser and go to: http://localhost:5000
echo.
python app.py
