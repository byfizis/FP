@echo off
chcp 65001
echo ===============================
echo    СБОРКА MUSIC PLAYER
echo ===============================
echo.

echo Очистка старых файлов...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Проверяем файлы...
echo Файлы в папке:
dir *.py *.jpg *.json *.db

echo.
echo Начинаем сборку EXE...
pyinstaller --onefile --windowed --name="MusicPlayer" --add-data="photo_2025-11-12_09-38-13.jpg;." --add-data="playlist.json;." --add-data="playlists.json;." --add-data="users.db;." --add-data="avatars;avatars" --add-data="downloads;downloads" --add-data="temp_music;temp_music" --add-data="music_library;music_library" player.py

echo.
if exist dist\MusicPlayer.exe (
    echo ✅ УСПЕХ! EXE-файл создан!
    echo 📊 Размер файла:
    dir dist\MusicPlayer.exe
    echo.
    echo 🎯 Файл находится в папке: dist\MusicPlayer.exe
) else (
    echo ❌ ОШИБКА! EXE-файл не создан!
)

echo.
echo ===============================
pause