@echo off
setlocal
set "ANDROID_HOME=%USERPROFILE%\Android\Sdk"
set "ANDROID_AVD_HOME=%USERPROFILE%\.android\avd"
set "GS_ADB=%ANDROID_HOME%\platform-tools\adb.exe"
set "GS_APK=%~dp0Grove-and-Stone-Android-1.0.0.apk"
if not "%~1"=="" set "GS_APK=%~f1"
set "GS_SERIAL=emulator-5556"
if not exist "%GS_ADB%" goto missing
"%ANDROID_HOME%\emulator\emulator-check.exe" accel
if errorlevel 1 goto acceleration
"%GS_ADB%" start-server
"%GS_ADB%" devices | findstr /C:"%GS_SERIAL%" >nul
if errorlevel 1 start "Grove and Stone Android" "%ANDROID_HOME%\emulator\emulator.exe" -avd Grove_Stone_API_30 -port 5556 -memory 1536 -cores 2 -no-audio -no-boot-anim
echo Waiting for your Android phone to start...
set /a GS_ATTEMPTS=0
:wait
"%GS_ADB%" -s %GS_SERIAL% shell getprop sys.boot_completed 2>nul | findstr /X /C:"1" >nul
if not errorlevel 1 goto ready
set /a GS_ATTEMPTS+=1 >nul
if %GS_ATTEMPTS% GEQ 100 goto slow
ping -n 4 127.0.0.1 >nul
goto wait
:ready
"%GS_ADB%" -s %GS_SERIAL% shell pm path com.groveandstone.app | findstr /B /C:"package:" >nul
if not errorlevel 1 goto launch
if not exist "%GS_APK%" goto missing
echo Installing Grove and Stone...
"%GS_ADB%" -s %GS_SERIAL% install -r "%GS_APK%"
if errorlevel 1 goto error
:launch
"%GS_ADB%" -s %GS_SERIAL% shell am start -n com.groveandstone.app/.MainActivity
if errorlevel 1 goto error
echo Grove and Stone is open in the Android emulator.
exit /b 0
:missing
echo Android setup or the saved APK is missing. Place the APK in this folder or pass its full path to this launcher.
goto error
:acceleration
echo Enable Windows Hypervisor Platform in Windows Features and restart Windows.
goto error
:slow
echo Android took too long to start. Close unused apps to free memory, then try again.
:error
pause
exit /b 1
