@echo off
setlocal

cd /d "%~dp0"
set "LOG_FILE=%~dp0update.log"

call :log ========================================
call :log JoyON update script
call :log Folder: %cd%
call :log Time: %date% %time%
call :log ========================================

> "%LOG_FILE%" echo ========================================
>> "%LOG_FILE%" echo JoyON update script
>> "%LOG_FILE%" echo Folder: %cd%
>> "%LOG_FILE%" echo Time: %date% %time%
>> "%LOG_FILE%" echo ========================================

if not exist ".git" (
  call :fail "Folder nay khong phai git repository. Hay chay file nay trong dung repo JoyON."
)

where git >nul 2>nul
if errorlevel 1 (
  call :fail "Khong tim thay git trong PATH."
)

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  call :fail "Repo git khong hop le."
)

for /f %%i in ('git status --porcelain') do (
  call :log [ERROR] Repo dang co file sua chua commit.
  call :log Hay commit, stash, hoac clone folder moi truoc khi update.
  git status --short
  >> "%LOG_FILE%" git status --short
  pause
  exit /b 1
)

call :step [1/5] Fetch code moi...
git fetch origin main >> "%LOG_FILE%" 2>&1
if errorlevel 1 call :fail "git fetch origin main that bai."
call :ok [1/5] Fetch xong

call :step [2/5] Pull code moi...
git pull --ff-only origin main >> "%LOG_FILE%" 2>&1
if errorlevel 1 call :fail "git pull --ff-only origin main that bai."
call :ok [2/5] Pull xong

if not exist ".env.production" (
  if not exist ".env.production.example" (
    call :fail "Thieu ca .env.production va .env.production.example"
  )

  call :step [3/5] Tao .env.production tu file example...
  copy /Y ".env.production.example" ".env.production" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 call :fail "Khong tao duoc .env.production"
  call :ok [3/5] Da tao .env.production
)

where docker >nul 2>nul
if errorlevel 1 (
  call :fail "Khong tim thay docker trong PATH."
)

call :step [4/5] Docker compose production...
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build >> "%LOG_FILE%" 2>&1
if errorlevel 1 call :fail "docker compose production that bai."
call :ok [4/5] Docker compose xong

call :step [5/5] Kiem tra container...
docker compose -f docker-compose.prod.yml --env-file .env.production ps >> "%LOG_FILE%" 2>&1
if errorlevel 1 call :fail "Khong doc duoc trang thai container."
call :ok [5/5] Container dang chay

call :log [DONE] Da cap nhat code moi va deploy xong.
call :log Log file: %LOG_FILE%
call :log App local: http://localhost:9979
call :log Review app: https://joyon.asia/review
pause
exit /b 0

:step
echo.
echo %~1
>> "%LOG_FILE%" echo.
>> "%LOG_FILE%" echo %~1
exit /b 0

:ok
echo [OK] %~1
>> "%LOG_FILE%" echo [OK] %~1
exit /b 0

:log
echo %*
>> "%LOG_FILE%" echo %*
exit /b 0

:fail
echo [ERROR] %~1
>> "%LOG_FILE%" echo [ERROR] %~1
echo Xem log tai: %LOG_FILE%
pause
exit /b 1
