import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.splash import CircularSplashScreen
from ui.main_window import MusicPlayer


def main():
    try:
        app = QApplication(sys.argv)

        from utils.helpers import get_app_icon
        icon = get_app_icon()
        if not icon.isNull():
            app.setWindowIcon(icon)

        splash = CircularSplashScreen()
        splash.show()

        player = MusicPlayer()

        def finish_startup():
            splash.close()
            player.show()
            player.raise_()
            player.activateWindow()

        QTimer.singleShot(2500, finish_startup)

        sys.exit(app.exec())
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()