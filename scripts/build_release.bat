@echo off
setlocal
cd /d %~dp0..
if exist release rmdir /s /q release
mkdir release
robocopy . release /E /XD backend\.venv frontend\node_modules frontend\dist models data\outputs data\reference .git /XF *.pyc *.pyo >nul
powershell -NoProfile -Command "Compress-Archive -Path 'release\*' -DestinationPath 'DepthWizard-v1.0.0-source.zip' -Force"
echo Created DepthWizard-v1.0.0-source.zip
