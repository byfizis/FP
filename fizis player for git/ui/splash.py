import os
from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath, QPixmap
from utils.helpers import get_app_icon


class CircularSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 400)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #1a1a1a;")
        icon = get_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.progress = 0
        self.rotation_angle = 0
        self.current_step = 0
        self.steps = ["Инициализация...", "Загрузка библиотек...", "Настройка аудио...", "Готово!"]

        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(50)

        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.update_rotation)
        self.rotation_timer.start(20)

        self.logo_pixmap = self.load_logo()

    def load_logo(self):
        try:
            from utils.helpers import APP_ICON_PATH
            if os.path.exists(APP_ICON_PATH):
                pixmap = QPixmap(APP_ICON_PATH)
                return pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
            else:
                pixmap = QPixmap(120, 120)
                pixmap.fill(QColor(26, 26, 26))
                painter = QPainter(pixmap)
                painter.setPen(QColor(187, 134, 252))
                painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "FP")
                painter.end()
                return pixmap
        except Exception:
            pixmap = QPixmap(120, 120)
            pixmap.fill(QColor(26, 26, 26))
            return pixmap

    def update_progress(self):
        self.progress += 1
        if self.progress >= 100:
            self.progress = 100
            self.progress_timer.stop()
            self.rotation_timer.stop()

        if self.steps and self.progress % 25 == 0:
            self.current_step = min(int(self.progress // 25), len(self.steps) - 1)
        self.repaint()

    def update_rotation(self):
        self.rotation_angle = (self.rotation_angle + 2) % 360
        self.repaint()

    def drawContents(self, painter):
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            center_x = self.width() // 2
            center_y = self.height() // 2
            outer_radius = 150
            inner_radius = 130

            painter.setPen(QPen(QColor(45, 45, 45), 8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center_x - outer_radius, center_y - outer_radius, outer_radius * 2, outer_radius * 2)

            progress_angle = int(360 * self.progress / 100)
            gradient = QColor(187, 134, 252)

            pen = QPen(gradient, 8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)

            span_angle = -progress_angle * 16
            painter.drawArc(center_x - outer_radius, center_y - outer_radius, outer_radius * 2, outer_radius * 2,
                            (90 - progress_angle) * 16, span_angle)

            indicator_radius = 8
            indicator_x = center_x + outer_radius * (3.14159 / 180) * (90 - self.rotation_angle)
            indicator_y = center_y - outer_radius * (3.14159 / 180) * (90 - self.rotation_angle)

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(indicator_x - indicator_radius), int(indicator_y - indicator_radius),
                                indicator_radius * 2, indicator_radius * 2)

            painter.setPen(QPen(QColor(45, 45, 45), 2))
            painter.setBrush(QBrush(QColor(35, 35, 35)))
            painter.drawEllipse(center_x - inner_radius, center_y - inner_radius, inner_radius * 2, inner_radius * 2)

            if not self.logo_pixmap.isNull():
                pixmap_x = center_x - self.logo_pixmap.width() // 2
                pixmap_y = center_y - self.logo_pixmap.height() // 2

                path = QPainterPath()
                path.addEllipse(pixmap_x, pixmap_y, self.logo_pixmap.width(), self.logo_pixmap.height())
                painter.setClipPath(path)
                painter.drawPixmap(pixmap_x, pixmap_y, self.logo_pixmap)
                painter.setClipping(False)

            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Normal))

            status_text = self.steps[self.current_step] if self.current_step < len(self.steps) else ""
            if status_text:
                text_width = painter.fontMetrics().horizontalAdvance(status_text)
                painter.drawText(center_x - text_width // 2, center_y + outer_radius + 30, status_text)

            percent_text = f"{self.progress}%"
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.setPen(QColor(187, 134, 252))
            percent_width = painter.fontMetrics().horizontalAdvance(percent_text)
            painter.drawText(center_x - percent_width // 2, center_y + outer_radius + 50, percent_text)

        except Exception as e:
            print(f"Ошибка отрисовки сплеш-скрина: {e}")

    def mousePressEvent(self, event):
        pass