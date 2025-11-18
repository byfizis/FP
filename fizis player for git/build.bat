@echo off
chcp 65001
echo =================================
echo    СБОРКА MUSIC PLAYER
echo =================================
echo.

echo Очистка старых файлов...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Начинаем сборку...
pyinstaller --onefile --windowed --name="MusicPlayer" --add-data="config;config" --add-data="core;core" --add-data="ui;ui" --add-data="utils;utils" --add-data="photo_2025-11-12_09-38-13.jpg;." --hidden-import=PyQt6.sip --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --hidden-import=PyQt6.QtMultimedia --hidden-import=email.mime.text --hidden-import=email.mime.multipart --hidden-import=smtplib main.py

echo.
if exist dist\MusicPlayer.exe (
    echo ✅ УСПЕХ! EXE-файл создан!
    echo 📊 Размер файла:
    dir dist\MusicPlayer.exe
    echo.
    echo 🎯 Файл: dist\MusicPlayer.exe
) else (
    echo ❌ ОШИБКА! EXE-файл не создан!
)

echo.
echo =================================
pause