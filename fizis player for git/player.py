import sys
import os
import json
import random
import sqlite3
import hashlib
import secrets
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QListWidgetItem,
    QHBoxLayout, QPushButton, QLineEdit, QWidget, QVBoxLayout, QListWidget,
    QLabel, QSplashScreen, QDialog, QStackedWidget,
    QSlider, QInputDialog, QMenu, QSplitter
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QPainterPath, QBrush, QAction

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ICON_FILENAME = "photo_2025-11-12_09-38-13.jpg"
APP_ICON_PATH = os.path.join(BASE_DIR, APP_ICON_FILENAME)


def get_app_icon():
    try:
        if os.path.exists(APP_ICON_PATH):
            return QIcon(APP_ICON_PATH)
    except Exception:
        pass
    return QIcon()


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


class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._scale = 1.0
        self.animation = QPropertyAnimation(self, b"scale")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._setup_base_styles()

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = pyqtProperty(float, get_scale, set_scale)

    def _setup_base_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #bb86fc;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9b66fc;
            }
            QPushButton:pressed {
                background-color: #7b46dc;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.animation.state() == QPropertyAnimation.State.Running:
                self.animation.stop()

            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.95)
            self.animation.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.animation.state() == QPropertyAnimation.State.Running:
                self.animation.stop()

            self.animation.setStartValue(0.95)
            self.animation.setEndValue(1.0)
            self.animation.start()

        super().mouseReleaseEvent(event)


class EmailManager:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = "fizisplayer@gmail.com"
        self.password = "twfk ztqh qkmm cswo"

    def send_verification_code(self, to_email, verification_code, is_login=False):
        try:
            msg = MIMEText(f'Ваш код подтверждения: {verification_code}')
            msg['Subject'] = 'Код подтверждения для fplay'
            msg['From'] = self.email
            msg['To'] = to_email

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Код подтверждения отправлен на {to_email}")
            return True

        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            QMessageBox.warning(None, "Ошибка отправки", f"Не удалось отправить код подтверждения:\n{str(e)}")
            return False


class AuthManager:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.email_manager = EmailManager()
        self.init_database()

    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT 0,
                    verification_code TEXT,
                    verification_code_expires TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    avatar_path TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    device_info TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    playlist_name TEXT NOT NULL,
                    playlist_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    volume INTEGER DEFAULT 50,
                    repeat_mode BOOLEAN DEFAULT 0,
                    shuffle_mode BOOLEAN DEFAULT 0,
                    current_playlist TEXT DEFAULT 'Основной',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            conn.commit()
            conn.close()
            print("✅ База данных успешно инициализирована")
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha512',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            310000,
            dklen=128
        ).hex()
        return password_hash, salt

    def verify_password(self, password, password_hash, salt):
        new_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(new_hash, password_hash)

    def generate_verification_code(self):
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    def register_user(self, email, username, password):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "Пользователь с таким email уже существует"

            password_hash, salt = self.hash_password(password)
            verification_code = self.generate_verification_code()
            verification_expires = datetime.now() + timedelta(minutes=10)

            cursor.execute('''
                INSERT INTO users (email, username, password_hash, salt, 
                verification_code, verification_code_expires, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (email, username, password_hash, salt,
                  verification_code, verification_expires, False))

            user_id = cursor.lastrowid

            cursor.execute('INSERT INTO user_settings (user_id) VALUES (?)', (user_id,))

            conn.commit()
            conn.close()

            if self.email_manager.send_verification_code(email, verification_code):
                return True, "Код подтверждения отправлен на вашу почту"
            else:
                return False, "Ошибка отправки кода подтверждения"

        except sqlite3.Error as e:
            return False, f"Ошибка базы данных: {str(e)}"

    def verify_email(self, email, verification_code):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, verification_code, verification_code_expires 
                FROM users WHERE email = ? AND is_verified = 0
            ''', (email,))

            user_data = cursor.fetchone()
            if not user_data:
                return False, "Пользователь не найден или уже подтвержден"

            user_id, stored_code, expires_at = user_data

            if datetime.now() > datetime.fromisoformat(expires_at):
                return False, "Срок действия кода истек"

            if not secrets.compare_digest(verification_code, stored_code):
                return False, "Неверный код подтверждения"

            cursor.execute('''
                UPDATE users 
                SET is_verified = 1, verification_code = NULL, 
                    verification_code_expires = NULL 
                WHERE id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()
            return True, "Email успешно подтвержден"

        except sqlite3.Error as e:
            return False, f"Ошибка базы данных: {str(e)}"

    def send_login_verification_code(self, email):
        """Отправляет код подтверждения для входа"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id, is_verified FROM users WHERE email = ?", (email,))
            user_data = cursor.fetchone()

            if not user_data:
                return False, "Пользователь не найден"

            user_id, is_verified = user_data

            if not is_verified:
                return False, "Email не подтвержден"

            verification_code = self.generate_verification_code()
            verification_expires = datetime.now() + timedelta(minutes=10)

            cursor.execute('''
                UPDATE users 
                SET verification_code = ?, verification_code_expires = ?
                WHERE id = ?
            ''', (verification_code, verification_expires, user_id))

            conn.commit()
            conn.close()

            if self.email_manager.send_verification_code(email, verification_code):
                return True, "Код подтверждения для входа отправлен на вашу почту"
            else:
                return False, "Ошибка отправки кода подтверждения"

        except sqlite3.Error as e:
            return False, f"Ошибка базы данных: {str(e)}"

    def verify_login_code(self, email, verification_code):
        """Проверяет код подтверждения для входа"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, verification_code, verification_code_expires 
                FROM users WHERE email = ?
            ''', (email,))

            user_data = cursor.fetchone()
            if not user_data:
                return False, "Пользователь не найден"

            user_id, stored_code, expires_at = user_data

            if not stored_code:
                return False, "Код подтверждения не запрашивался"

            if datetime.now() > datetime.fromisoformat(expires_at):
                return False, "Срок действия кода истек"

            if not secrets.compare_digest(verification_code, stored_code):
                return False, "Неверный код подтверждения"

            # Очищаем код после успешной проверки
            cursor.execute('''
                UPDATE users 
                SET verification_code = NULL, verification_code_expires = NULL,
                    login_attempts = 0, locked_until = NULL
                WHERE id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()
            return True, "Код подтвержден"

        except sqlite3.Error as e:
            return False, f"Ошибка базы данных: {str(e)}"

    def authenticate_user(self, email, password, device_info="", ip_address=""):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, email, username, password_hash, salt, is_verified,
                       login_attempts, locked_until, is_active, avatar_path
                FROM users WHERE email = ?
            ''', (email,))

            user_data = cursor.fetchone()
            if not user_data:
                return None, "Пользователь не найден"

            (user_id, email, username, password_hash, salt, is_verified,
             login_attempts, locked_until, is_active, avatar_path) = user_data

            if locked_until and datetime.now() < datetime.fromisoformat(locked_until):
                remaining_time = (datetime.fromisoformat(locked_until) - datetime.now()).seconds // 60
                return None, f"Аккаунт заблокирован. Попробуйте через {remaining_time} мин."

            if not is_active:
                return None, "Аккаунт деактивирован"

            if not is_verified:
                return None, "Email не подтвержден"

            if self.verify_password(password, password_hash, salt):
                # Отправляем код подтверждения для входа
                success, message = self.send_login_verification_code(email)
                if not success:
                    return None, message

                return {"needs_verification": True, "email": email}, "Код подтверждения отправлен на email"

            else:
                login_attempts += 1
                if login_attempts >= 5:
                    locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                    cursor.execute('''
                        UPDATE users 
                        SET login_attempts = ?, locked_until = ?
                        WHERE id = ?
                    ''', (login_attempts, locked_until, user_id))
                    message = "Слишком много неудачных попыток. Аккаунт заблокирован на 30 минут."
                else:
                    cursor.execute('''
                        UPDATE users 
                        SET login_attempts = ?
                        WHERE id = ?
                    ''', (login_attempts, user_id))
                    message = f"Неверный пароль. Осталось попыток: {5 - login_attempts}"

                conn.commit()
                conn.close()
                return None, message

        except sqlite3.Error as e:
            return None, f"Ошибка базы данных: {str(e)}"

    def complete_login(self, email, device_info="", ip_address=""):
        """Завершает вход после проверки кода"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, email, username, avatar_path
                FROM users WHERE email = ?
            ''', (email,))

            user_data = cursor.fetchone()
            if not user_data:
                return None, "Пользователь не найден"

            user_id, email, username, avatar_path = user_data

            # Создаем сессию
            session_token = secrets.token_urlsafe(64)
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()

            cursor.execute('''
                UPDATE users 
                SET last_login = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))

            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, device_info, 
                ip_address, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, device_info, ip_address, expires_at))

            conn.commit()
            conn.close()

            user = {
                'id': user_id,
                'email': email,
                'username': username,
                'avatar_path': avatar_path
            }

            self.save_session_token(session_token)
            return user, "Успешный вход"

        except sqlite3.Error as e:
            return None, f"Ошибка базы данных: {str(e)}"

    def save_session_token(self, token):
        try:
            with open('session.token', 'w') as f:
                f.write(token)
        except:
            pass

    def load_session_token(self):
        try:
            with open('session.token', 'r') as f:
                return f.read().strip()
        except:
            return None

    def validate_session(self, token):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT u.id, u.email, u.username, s.device_info, u.avatar_path
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.expires_at > ? AND u.is_active = 1
            ''', (token, datetime.now().isoformat()))

            user_data = cursor.fetchone()
            if user_data:
                cursor.execute('''
                    UPDATE sessions 
                    SET last_activity = ?
                    WHERE session_token = ?
                ''', (datetime.now().isoformat(), token))
                conn.commit()

                user = {
                    'id': user_data[0],
                    'email': user_data[1],
                    'username': user_data[2],
                    'device_info': user_data[3],
                    'avatar_path': user_data[4]
                }
                conn.close()
                return user
            conn.close()
            return None

        except sqlite3.Error:
            return None

    def logout(self, token=None):
        if not token:
            token = self.load_session_token()

        if token:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
                conn.commit()
                conn.close()
            except:
                pass

        try:
            os.remove('session.token')
        except:
            pass

    def save_user_settings(self, user_id, settings):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO user_settings 
                (user_id, volume, repeat_mode, shuffle_mode, current_playlist)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, settings.get('volume', 50),
                  settings.get('repeat_mode', False),
                  settings.get('shuffle_mode', False),
                  settings.get('current_playlist', 'Основной')))

            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False

    def load_user_settings(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT volume, repeat_mode, shuffle_mode, current_playlist
                FROM user_settings WHERE user_id = ?
            ''', (user_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'volume': result[0],
                    'repeat_mode': bool(result[1]),
                    'shuffle_mode': bool(result[2]),
                    'current_playlist': result[3]
                }
            return {}
        except sqlite3.Error:
            return {}

    def save_user_playlists(self, user_id, playlists):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM user_playlists WHERE user_id = ?", (user_id,))

            for name, tracks in playlists.items():
                playlist_data = json.dumps(tracks, ensure_ascii=False)
                cursor.execute('''
                    INSERT INTO user_playlists (user_id, playlist_name, playlist_data)
                    VALUES (?, ?, ?)
                ''', (user_id, name, playlist_data))

            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False

    def load_user_playlists(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT playlist_name, playlist_data 
                FROM user_playlists 
                WHERE user_id = ?
            ''', (user_id,))

            playlists = {}
            for name, data in cursor.fetchall():
                if data:
                    try:
                        playlists[name] = json.loads(data)
                    except:
                        playlists[name] = []
                else:
                    playlists[name] = []

            conn.close()
            return playlists
        except sqlite3.Error:
            return {}

    def delete_playlist(self, user_id, playlist_name):
        """Удаляет плейлист из базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM user_playlists 
                WHERE user_id = ? AND playlist_name = ?
            ''', (user_id, playlist_name))

            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False

    def update_username(self, user_id, new_username):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False

    def update_avatar(self, user_id, avatar_path):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET avatar_path = ? WHERE id = ?', (avatar_path, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False


class VerificationDialog(QDialog):
    def __init__(self, email, is_login=False, parent=None):
        super().__init__(parent)
        icon = get_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.email = email
        self.is_login = is_login
        self.setup_ui()

    def setup_ui(self):
        title = "Подтверждение входа" if self.is_login else "Подтверждение Email"
        self.setWindowTitle(title)
        self.setFixedSize(400, 300)
        self.setStyleSheet(
            "QDialog { background-color: #1a1a1a; color: white; }"
            "QLabel { color: white; font-size: 14px; }"
            "QLineEdit { background-color: #2d2d2d; color: white; border: 2px solid #bb86fc; border-radius: 8px; padding: 10px; font-size: 16px; letter-spacing: 2px; }"
            "QPushButton { background-color: #bb86fc; color: black; border: none; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { background-color: #9b66fc; }"
            "QPushButton:disabled { background-color: #666666; color: #999999; }"
        )

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #bb86fc; font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(20)

        info_label = QLabel(f"Код подтверждения отправлен на:\n{self.email}")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        layout.addSpacing(10)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Введите 6-значный код")
        self.code_input.setMaxLength(6)
        self.code_input.textChanged.connect(self.on_code_changed)
        layout.addWidget(self.code_input)

        self.timer_label = QLabel("Код действителен: 10:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)

        layout.addSpacing(20)

        self.verify_button = AnimatedButton("Подтвердить")
        self.verify_button.setEnabled(False)
        self.verify_button.clicked.connect(self.verify)
        layout.addWidget(self.verify_button)

        self.resend_button = AnimatedButton("Отправить код повторно")
        self.resend_button.clicked.connect(self.resend_code)
        layout.addWidget(self.resend_button)

        self.setLayout(layout)

        self.time_left = 600
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def on_code_changed(self, text):
        self.verify_button.setEnabled(len(text) == 6)

    def update_timer(self):
        self.time_left -= 1
        if self.time_left <= 0:
            self.timer.stop()
            self.timer_label.setText("Время истекло!")
            self.verify_button.setEnabled(False)
            return

        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.setText(f"Код действителен: {minutes:02d}:{seconds:02d}")

    def verify(self):
        code = self.code_input.text()
        if len(code) == 6:
            self.accept()

    def resend_code(self):
        self.time_left = 600
        self.timer.start()
        self.code_input.clear()
        QMessageBox.information(self, "Код отправлен", "Новый код подтверждения отправлен на вашу почту.")

    def get_verification_code(self):
        return self.code_input.text()


class PlaylistsDropdown(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget { 
                background-color: #2d2d2d; 
                border: 2px solid #bb86fc; 
                border-radius: 15px; 
                color: white; 
            }
            QListWidget { 
                background-color: #2d2d2d; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 12px; 
                outline: none; 
            }
            QListWidget::item { 
                padding: 12px 15px; 
                border-bottom: 1px solid #3d3d3d; 
                background-color: transparent; 
                color: white; 
                border-radius: 5px;
                margin: 2px;
            }
            QListWidget::item:selected { 
                background-color: #bb86fc !important; 
                color: #000000 !important; 
                font-weight: bold; 
                border: none; 
            }
            QListWidget::item:hover:!selected { 
                background-color: #3d3d3d; 
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Ваши плейлисты")
        title.setStyleSheet("""
            color: #bb86fc; 
            font-weight: bold; 
            font-size: 14px; 
            padding: 8px;
            background-color: #2d2d2d;
            border-radius: 8px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.playlists_list = QListWidget()
        self.playlists_list.itemClicked.connect(self.on_playlist_selected)
        self.playlists_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlists_list.customContextMenuRequested.connect(self.show_playlist_context_menu)
        layout.addWidget(self.playlists_list)

        self.add_button = AnimatedButton("Создать плейлист")
        self.add_button.setFixedHeight(35)
        self.add_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 15px; 
                padding: 8px 12px; 
                font-weight: bold; 
                font-size: 12px;
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.add_button.clicked.connect(self.create_new_playlist)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        self.setFixedSize(250, 350)

    def update_playlists(self, playlists, current_playlist):
        self.playlists_list.clear()
        for name in playlists.keys():
            item = QListWidgetItem(name)
            if name == current_playlist:
                item.setBackground(QColor(187, 134, 252))
                item.setForeground(QColor(0, 0, 0))
                item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.playlists_list.addItem(item)

    def on_playlist_selected(self, item):
        playlist_name = item.text()
        self.parent.switch_playlist(playlist_name)
        self.hide()

    def show_playlist_context_menu(self, position):
        item = self.playlists_list.itemAt(position)
        if not item:
            return

        playlist_name = item.text()

        # Не позволяем удалять основной плейлист
        if playlist_name == "Основной":
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #bb86fc;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 20px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #bb86fc;
                color: black;
            }
        """)

        delete_action = QAction("Удалить плейлист", self)
        delete_action.triggered.connect(lambda: self.delete_playlist(playlist_name))
        menu.addAction(delete_action)

        menu.exec(self.playlists_list.mapToGlobal(position))

    def delete_playlist(self, playlist_name):
        reply = QMessageBox.question(
            self,
            "Удаление плейлиста",
            f"Вы уверены, что хотите удалить плейлист '{playlist_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.parent.delete_playlist(playlist_name)
            self.hide()

    def create_new_playlist(self):
        self.parent.show_add_playlist_dialog()
        self.hide()

    def mousePressEvent(self, event):
        self.hide()


class AuthWidget(QWidget):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.parent_window = parent
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #1a1a1a; color: white; }
            QLabel { color: white; font-size: 14px; }
            QLabel#title { color: #bb86fc; font-size: 24px; font-weight: bold; }
            QLineEdit { background-color: #2d2d2d; color: white; border: 2px solid #bb86fc; border-radius: 8px; padding: 10px; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #9b66fc; }
            QPushButton { background-color: #bb86fc; color: black; border: none; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #9b66fc; }
            QPushButton:disabled { background-color: #666666; color: #999999; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("fplay")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(30)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.login_button = AnimatedButton("Войти")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        self.register_button = AnimatedButton("Регистрация")
        self.register_button.clicked.connect(self.show_register_dialog)
        layout.addWidget(self.register_button)

        layout.addStretch()
        self.setLayout(layout)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        # Администраторский вход (без подтверждения по email)
        if email == "fizisplayer@gmail.com" and password == "02fizis02":
            user = {
                'id': 0,
                'email': email,
                'username': 'Администратор',
                'avatar_path': None
            }
            if self.parent_window:
                self.parent_window.on_login_success(user)
            return

        result, message = self.auth_manager.authenticate_user(email, password)
        if result:
            if result.get("needs_verification"):
                # Показываем диалог подтверждения для входа
                verify_dialog = VerificationDialog(email, is_login=True, parent=self)
                if verify_dialog.exec() == QDialog.DialogCode.Accepted:
                    code = verify_dialog.get_verification_code()
                    verify_success, verify_message = self.auth_manager.verify_login_code(email, code)
                    if verify_success:
                        user, final_message = self.auth_manager.complete_login(email)
                        if user:
                            QMessageBox.information(self, "Успех", final_message)
                            if self.parent_window:
                                self.parent_window.on_login_success(user)
                        else:
                            QMessageBox.warning(self, "Ошибка", final_message)
                    else:
                        QMessageBox.warning(self, "Ошибка", verify_message)
            else:
                QMessageBox.information(self, "Успех", message)
                if self.parent_window:
                    self.parent_window.on_login_success(result)
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def show_register_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Регистрация")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: white; }
            QLabel { color: white; font-size: 14px; }
            QLineEdit { background-color: #2d2d2d; color: white; border: 2px solid #bb86fc; border-radius: 8px; padding: 10px; }
            QPushButton { background-color: #bb86fc; color: black; border: none; border-radius: 8px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #9b66fc; }
        """)

        layout = QVBoxLayout()

        email_input = QLineEdit()
        email_input.setPlaceholderText("Email")
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(email_input)

        username_input = QLineEdit()
        username_input.setPlaceholderText("Имя пользователя")
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(username_input)

        password_input = QLineEdit()
        password_input.setPlaceholderText("Пароль")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(password_input)

        register_btn = AnimatedButton("Зарегистрироваться")
        layout.addWidget(register_btn)

        def register():
            email = email_input.text().strip()
            username = username_input.text().strip()
            password = password_input.text()

            if not all([email, username, password]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
                return

            success, message = self.auth_manager.register_user(email, username, password)
            if success:
                QMessageBox.information(dialog, "Успех", message)
                verify_dialog = VerificationDialog(email, is_login=False, parent=dialog)
                if verify_dialog.exec() == QDialog.DialogCode.Accepted:
                    code = verify_dialog.get_verification_code()
                    verify_success, verify_message = self.auth_manager.verify_email(email, code)
                    if verify_success:
                        QMessageBox.information(dialog, "Успех", verify_message)
                        dialog.accept()
                    else:
                        QMessageBox.warning(dialog, "Ошибка", verify_message)
            else:
                QMessageBox.warning(dialog, "Ошибка", message)

        register_btn.clicked.connect(register)
        dialog.setLayout(layout)
        dialog.exec()


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_manager = AuthManager()
        self.current_user = None
        self.playlists = {}
        self.current_playlist = "Основной"
        self.current_track_index = 0
        self.is_shuffle = False
        self.is_repeat = False
        self.volume = 50
        self.current_playing_item = None
        self.is_playing = False
        self.playback_finished = False

        icon = get_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        self.setWindowTitle("fplay")
        self.setMinimumSize(900, 700)

        self.setup_ui()
        self.setup_player()
        self.check_session()

    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #1a1a1a; 
                color: white; 
            }
            QWidget { 
                background-color: #1a1a1a; 
                color: white; 
            }
            QLabel { 
                color: white; 
            }
            QListWidget { 
                background-color: #2d2d2d; 
                color: white; 
                border: 2px solid #bb86fc; 
                border-radius: 15px; 
                padding: 5px; 
            }
            QListWidget::item { 
                padding: 12px 15px; 
                border-bottom: 1px solid #3d3d3d; 
                border-radius: 8px;
                margin: 2px;
            }
            QListWidget::item:hover { 
                background-color: #3d3d3d; 
            }
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 8px; 
                padding: 10px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QSlider::groove:horizontal { 
                background: #2d2d2d; 
                height: 8px; 
                border-radius: 4px; 
            }
            QSlider::handle:horizontal { 
                background: #bb86fc; 
                width: 18px; 
                height: 18px; 
                border-radius: 9px; 
                margin: -5px 0; 
            }
            QSlider::handle:horizontal:hover { 
                background: #9b66fc; 
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.auth_widget = AuthWidget(self.auth_manager, self)
        self.stacked_widget.addWidget(self.auth_widget)

        self.player_widget = QWidget()
        player_layout = QVBoxLayout()
        player_layout.setSpacing(15)
        player_layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()

        self.user_container = QWidget()
        user_container_layout = QHBoxLayout()
        user_container_layout.setContentsMargins(0, 0, 0, 0)
        user_container_layout.setSpacing(8)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(32, 32)
        self.avatar_label.setStyleSheet("""
            border-radius: 16px; 
            background-color: #2d2d2d; 
            border: 2px solid #bb86fc;
        """)
        self.avatar_label.setScaledContents(True)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_container_layout.addWidget(self.avatar_label)

        self.user_label = QLabel("Не авторизован")
        self.user_label.setStyleSheet("""
            color: #bb86fc; 
            font-size: 14px; 
            font-weight: bold; 
            cursor: pointer; 
        """)
        self.user_label.mousePressEvent = self.on_user_label_clicked
        user_container_layout.addWidget(self.user_label)

        self.user_container.setLayout(user_container_layout)
        header_layout.addWidget(self.user_container)

        header_layout.addStretch()

        self.playlist_dropdown_btn = AnimatedButton("Плейлисты")
        self.playlist_dropdown_btn.setFixedSize(120, 40)
        self.playlist_dropdown_btn.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 20px; 
                font-size: 14px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
        """)
        self.playlist_dropdown_btn.clicked.connect(self.show_playlists_dropdown)
        header_layout.addWidget(self.playlist_dropdown_btn)

        self.add_track_btn = AnimatedButton("Добавить трек")
        self.add_track_btn.setFixedSize(120, 40)
        self.add_track_btn.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 20px; 
                font-size: 14px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
        """)
        self.add_track_btn.clicked.connect(self.show_add_track_dialog)
        header_layout.addWidget(self.add_track_btn)

        player_layout.addLayout(header_layout)

        self.playlist_label = QLabel("Плейлист: Основной")
        self.playlist_label.setStyleSheet("""
            color: #bb86fc; 
            font-size: 16px; 
            font-weight: bold;
            padding: 10px;
            background-color: #2d2d2d;
            border-radius: 10px;
            border: 1px solid #bb86fc;
        """)
        self.playlist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_layout.addWidget(self.playlist_label)

        self.tracks_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tracks_splitter.setChildrenCollapsible(False)
        self.tracks_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bb86fc;
                width: 3px;
                border-radius: 1px;
            }
            QSplitter::handle:hover {
                background-color: #9b66fc;
            }
        """)

        self.tracks_list = QListWidget()
        self.tracks_list.itemClicked.connect(self.on_track_clicked)
        self.tracks_list.itemDoubleClicked.connect(self.play_selected_track)
        self.tracks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tracks_list.customContextMenuRequested.connect(self.show_track_context_menu)
        self.tracks_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #bb86fc;
                border-radius: 15px;
                padding: 8px;
                outline: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid #3d3d3d;
                background-color: transparent;
                border-radius: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        self.tracks_splitter.addWidget(self.tracks_list)

        self.profile_stats_widget = QWidget()
        self.profile_stats_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 2px solid #bb86fc;
                border-radius: 15px;
                padding: 15px;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
        """)
        profile_stats_layout = QVBoxLayout()
        profile_stats_layout.setContentsMargins(10, 10, 10, 10)
        profile_stats_layout.setSpacing(15)

        stats_title = QLabel("Статистика профиля")
        stats_title.setStyleSheet("""
            color: #bb86fc;
            font-size: 18px;
            font-weight: bold;
            padding: 5px;
            border-bottom: 2px solid #bb86fc;
        """)
        stats_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_stats_layout.addWidget(stats_title)

        self.total_tracks_label = QLabel("Всего треков: 0")
        self.total_tracks_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        profile_stats_layout.addWidget(self.total_tracks_label)

        self.total_playlists_label = QLabel("Плейлистов: 0")
        self.total_playlists_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        profile_stats_layout.addWidget(self.total_playlists_label)

        self.total_duration_label = QLabel("Общее время: 0:00")
        self.total_duration_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        profile_stats_layout.addWidget(self.total_duration_label)

        profile_stats_layout.addStretch()

        self.profile_stats_widget.setLayout(profile_stats_layout)
        self.tracks_splitter.addWidget(self.profile_stats_widget)

        self.profile_stats_widget.hide()
        self.tracks_splitter.setSizes([1000, 0])

        player_layout.addWidget(self.tracks_splitter, 1)

        self.current_track_label = QLabel("Трек не выбран")
        self.current_track_label.setStyleSheet("""
            color: #bb86fc; 
            font-size: 12px; 
            padding: 8px; 
            background-color: #2d2d2d; 
            border-radius: 8px;
            border: 1px solid #bb86fc;
            font-weight: bold;
        """)
        self.current_track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_layout.addWidget(self.current_track_label)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(100)
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        player_layout.addWidget(self.position_slider)

        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: #bb86fc; font-size: 11px;")
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("color: #bb86fc; font-size: 11px;")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        player_layout.addLayout(time_layout)

        controls_layout = QHBoxLayout()
        controls_layout.addStretch()

        self.repeat_button = AnimatedButton("↻")
        self.repeat_button.setFixedSize(100, 50)
        self.repeat_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 24px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.repeat_button.clicked.connect(self.toggle_repeat)
        controls_layout.addWidget(self.repeat_button)

        self.prev_button = AnimatedButton("◀◀")
        self.prev_button.setFixedSize(100, 50)
        self.prev_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 18px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.prev_button.clicked.connect(self.play_previous)
        controls_layout.addWidget(self.prev_button)

        self.play_pause_button = AnimatedButton("▶")
        self.play_pause_button.setFixedSize(100, 60)
        self.play_pause_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 30px; 
                font-size: 28px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_pause_button)

        self.next_button = AnimatedButton("▶▶")
        self.next_button.setFixedSize(100, 50)
        self.next_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 18px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.next_button.clicked.connect(self.play_next)
        controls_layout.addWidget(self.next_button)

        self.shuffle_button = AnimatedButton("⇄")
        self.shuffle_button.setFixedSize(100, 50)
        self.shuffle_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 24px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
        """)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        controls_layout.addWidget(self.shuffle_button)

        controls_layout.addStretch()

        volume_layout = QHBoxLayout()
        volume_layout.addStretch()
        volume_layout.setSpacing(9)

        volume_icon = QLabel("♪")
        volume_icon.setStyleSheet("color: #bb86fc; font-size: 14px; font-weight: bold;")
        volume_icon.setFixedWidth(19)
        volume_layout.addWidget(volume_icon)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("50%")
        self.volume_label.setStyleSheet("color: #bb86fc; font-size: 11px; font-weight: bold;")
        self.volume_label.setFixedWidth(30)
        volume_layout.addWidget(self.volume_label)

        controls_layout.addLayout(volume_layout)

        player_layout.addLayout(controls_layout)

        self.player_widget.setLayout(player_layout)
        self.stacked_widget.addWidget(self.player_widget)

        self.playlists_dropdown = PlaylistsDropdown(self)

        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start(100)

        self.slider_pressed = False

    def setup_player(self):
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_finished = True
            self.handle_playback_finished()

    def handle_playback_finished(self):
        if self.playback_finished:
            self.playback_finished = False
            if self.is_repeat:
                self.play_current_track()
            else:
                if (self.current_playlist in self.playlists and
                        self.current_track_index < len(self.playlists[self.current_playlist]) - 1):
                    self.play_next()
                else:
                    self.current_track_index = 0
                    self.play_current_track()

    def on_track_clicked(self, item):
        track_data = item.data(Qt.ItemDataRole.UserRole)
        index = self.tracks_list.row(item)

        self.current_track_index = index
        self.highlight_current_track()

        if isinstance(track_data, dict):
            if track_data.get('local_file') and track_data.get('file_path'):
                if os.path.exists(track_data['file_path']):
                    self.play_track(track_data['file_path'])
                else:
                    self.play_streaming_track(track_data)
            else:
                self.play_streaming_track(track_data)
        else:
            track_path = track_data
            if not os.path.exists(track_path):
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track_path}")
                return
            self.play_track(track_path)

    def check_session(self):
        token = self.auth_manager.load_session_token()
        if token:
            user = self.auth_manager.validate_session(token)
            if user:
                self.on_login_success(user)
                return
        self.stacked_widget.setCurrentIndex(0)

    def on_login_success(self, user):
        self.current_user = user
        self.user_label.setText(f"{user['username']}")

        # Загружаем аватарку из базы данных
        if user.get('avatar_path'):
            self.load_user_avatar(user['avatar_path'], self.avatar_label)
        else:
            self.set_default_avatar(self.avatar_label)

        self.stacked_widget.setCurrentIndex(1)

        if user.get('id'):
            settings = self.auth_manager.load_user_settings(user['id'])
            self.volume = settings.get('volume', 50)
            self.volume_slider.setValue(self.volume)
            self.set_volume(self.volume)
            self.is_repeat = settings.get('repeat_mode', False)
            self.is_shuffle = settings.get('shuffle_mode', False)
            self.current_playlist = settings.get('current_playlist', 'Основной')

            self.playlists = self.auth_manager.load_user_playlists(user['id'])
            if not self.playlists:
                self.playlists = {'Основной': []}
            self.update_playlist_display()

            self.repeat_button.setText("↻●" if self.is_repeat else "↻")
            self.shuffle_button.setText("⇄●" if self.is_shuffle else "⇄")

        self.tracks_splitter.splitterMoved.connect(self.on_splitter_moved)

    def on_splitter_moved(self, pos, index):
        sizes = self.tracks_splitter.sizes()
        if sizes[1] > 50:
            if not self.profile_stats_widget.isVisible():
                self.profile_stats_widget.show()
        else:
            if self.profile_stats_widget.isVisible():
                self.profile_stats_widget.hide()

    def update_profile_stats(self):
        if not self.current_user:
            return

        total_tracks = 0
        total_playlists = len(self.playlists)
        total_duration_seconds = 0

        for playlist_name, tracks in self.playlists.items():
            total_tracks += len(tracks)
            for track in tracks:
                if isinstance(track, dict):
                    if 'duration' in track:
                        duration_str = track.get('duration', '0:00')
                        try:
                            parts = duration_str.split(':')
                            if len(parts) == 2:
                                minutes, seconds = map(int, parts)
                                total_duration_seconds += minutes * 60 + seconds
                        except:
                            pass
                elif isinstance(track, str) and os.path.exists(track):
                    pass

        self.total_tracks_label.setText(f"Всего треков: {total_tracks}")
        self.total_playlists_label.setText(f"Плейлистов: {total_playlists}")

        hours = total_duration_seconds // 3600
        minutes = (total_duration_seconds % 3600) // 60
        if hours > 0:
            self.total_duration_label.setText(f"Общее время: {hours}:{minutes:02d}:00")
        else:
            self.total_duration_label.setText(f"Общее время: {minutes}:00")

    def handle_logout(self):
        self.auth_manager.logout()
        self.current_user = None
        self.playlists = {}
        self.current_playlist = "Основной"
        self.tracks_list.clear()
        self.stacked_widget.setCurrentIndex(0)
        self.stop()

    def show_playlists_dropdown(self):
        if self.current_user:
            self.playlists_dropdown.update_playlists(self.playlists, self.current_playlist)
            button_pos = self.playlist_dropdown_btn.mapToGlobal(self.playlist_dropdown_btn.rect().bottomLeft())
            self.playlists_dropdown.move(button_pos)
            self.playlists_dropdown.show()

    def show_add_playlist_dialog(self):
        name, ok = QInputDialog.getText(self, "Новый плейлист", "Введите название плейлиста:")
        if ok and name.strip():
            if name.strip() not in self.playlists:
                self.playlists[name.strip()] = []
                self.current_playlist = name.strip()
                self.playlist_label.setText(f"Плейлист: {self.current_playlist}")
                self.save_playlists()
                self.update_playlist_display()
                QMessageBox.information(self, "Успех", f"Плейлист '{name.strip()}' создан")
            else:
                QMessageBox.warning(self, "Ошибка", "Плейлист с таким именем уже существует")

    def delete_playlist(self, playlist_name):
        """Удаляет плейлист"""
        if playlist_name not in self.playlists:
            return

        # Не позволяем удалить основной плейлист
        if playlist_name == "Основной":
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить основной плейлист")
            return

        # Если удаляем текущий плейлист, переключаемся на основной
        if self.current_playlist == playlist_name:
            self.current_playlist = "Основной"
            self.playlist_label.setText(f"Плейлист: {self.current_playlist}")

        # Удаляем плейлист из словаря
        del self.playlists[playlist_name]

        # Сохраняем изменения в базе данных
        if self.current_user and self.current_user.get('id'):
            self.auth_manager.delete_playlist(self.current_user['id'], playlist_name)
            self.save_playlists()

        # Обновляем отображение
        self.update_playlist_display()
        QMessageBox.information(self, "Успех", f"Плейлист '{playlist_name}' удален")

    def switch_playlist(self, playlist_name):
        if playlist_name in self.playlists:
            self.current_playlist = playlist_name
            self.playlist_label.setText(f"Плейлист: {self.current_playlist}")
            self.update_playlist_display()
            if self.current_user:
                settings = self.auth_manager.load_user_settings(self.current_user['id'])
                settings['current_playlist'] = playlist_name
                self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def update_playlist_display(self):
        self.tracks_list.clear()
        self.current_playing_item = None

        if self.current_playlist in self.playlists:
            for i, track in enumerate(self.playlists[self.current_playlist]):
                if isinstance(track, dict):
                    if track.get('type') == 'youtube':
                        title = track.get('title', 'Unknown YouTube track')
                        artist = track.get('artist', 'Unknown Artist')
                        source = track.get('source', 'YouTube')
                        downloaded = " ✅" if track.get('downloaded') else ""
                        item_text = f"🎵 {artist} - {title}{downloaded}"
                        item = QListWidgetItem(item_text)
                        item.setToolTip(f"YouTube: {title}\nИсполнитель: {artist}\nИсточник: {source}")
                        item.setData(Qt.ItemDataRole.UserRole, track)
                    elif track.get('type') == 'telegram':
                        title = track.get('title', 'Unknown Telegram track')
                        artist = track.get('artist', 'Unknown Artist')
                        item_text = f"{artist} - {title}"
                        item = QListWidgetItem(item_text)
                        item.setToolTip(f"AudioBot: {title}\nИсполнитель: {artist}")
                        item.setData(Qt.ItemDataRole.UserRole, track)
                else:
                    track_path = track
                    track_name = os.path.basename(track_path)
                    item_text = track_name
                    item = QListWidgetItem(item_text)
                    item.setToolTip(f"Локальный файл: {track_name}")
                    item.setData(Qt.ItemDataRole.UserRole, track_path)

                self.tracks_list.addItem(item)

        self.highlight_current_track()
        self.update_profile_stats()

    def highlight_current_track(self):
        for i in range(self.tracks_list.count()):
            item = self.tracks_list.item(i)
            if item:
                if i == self.current_track_index:
                    item.setBackground(QColor(45, 45, 45))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                    self.current_playing_item = item
                    self.tracks_list.scrollToItem(item, QListWidget.ScrollHint.EnsureVisible)
                else:
                    item.setBackground(QColor(0, 0, 0, 0))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Arial", 10, QFont.Weight.Normal))

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите аудио файлы", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a);;All Files (*)"
        )
        if files:
            self.add_tracks_to_playlist(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с музыкой")
        if folder:
            audio_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
                        audio_files.append(os.path.join(root, file))
            if audio_files:
                self.add_tracks_to_playlist(audio_files)
            else:
                QMessageBox.information(self, "Информация", "В выбранной папке не найдено аудио файлов")

    def add_tracks_to_playlist(self, files):
        if self.current_playlist not in self.playlists:
            self.playlists[self.current_playlist] = []
        for file_path in files:
            if file_path not in self.playlists[self.current_playlist]:
                self.playlists[self.current_playlist].append(file_path)
        self.update_playlist_display()
        self.save_playlists()

    def save_playlists(self):
        if self.current_user and self.current_user.get('id'):
            self.auth_manager.save_user_playlists(self.current_user['id'], self.playlists)

    def play_selected_track(self, item):
        self.on_track_clicked(item)

    def play_current_track(self):
        if (self.current_playlist in self.playlists and
                self.current_track_index < len(self.playlists[self.current_playlist])):

            track = self.playlists[self.current_playlist][self.current_track_index]

            if isinstance(track, dict):
                if track.get('local_file') and track.get('file_path'):
                    if os.path.exists(track['file_path']):
                        self.play_track(track['file_path'])
                    else:
                        self.play_streaming_track(track)
                else:
                    self.play_streaming_track(track)
            else:
                if os.path.exists(track):
                    self.play_track(track)
                else:
                    QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track}")

    def play_streaming_track(self, track_data):
        try:
            if track_data.get('type') == 'youtube':
                title = track_data.get('title', 'YouTube трек')
                artist = track_data.get('artist', 'Неизвестный исполнитель')
                self.current_track_label.setText(f"🎵 {artist} - {title}")

                if track_data.get('downloaded') and track_data.get('file_path'):
                    if os.path.exists(track_data['file_path']):
                        self.play_track(track_data['file_path'])
                        return

                QMessageBox.information(
                    self,
                    "YouTube Music",
                    f"Трек: {track_data.get('title', 'Неизвестный')}\n"
                    f"Исполнитель: {track_data.get('artist', 'Неизвестный')}\n\n"
                    "Скачайте трек для воспроизведения."
                )
            else:
                self.current_track_label.setText(f"♪ {track_data.get('title', 'Стриминговый трек')}")

        except Exception as e:
            print(f"Ошибка воспроизведения стримингового трека: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось воспроизвести трек: {str(e)}")

    def play_track(self, track_path):
        try:
            if isinstance(track_path, dict):
                self.play_streaming_track(track_path)
                return

            if not os.path.exists(track_path):
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track_path}")
                return

            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()

            QTimer.singleShot(100, lambda: self._actually_play_track(track_path))

        except Exception as e:
            print(f"Ошибка в play_track: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка воспроизведения: {str(e)}")

    def _actually_play_track(self, track_path):
        try:
            if not os.path.exists(track_path):
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track_path}")
                return

            file_url = QUrl.fromLocalFile(track_path)

            if not file_url.isValid():
                QMessageBox.warning(self, "Ошибка", f"Неверный URL файла: {track_path}")
                return

            self.media_player.setSource(file_url)

            if self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.InvalidMedia:
                QMessageBox.warning(self, "Ошибка", f"Неподдерживаемый формат файла: {track_path}")
                return

            self.media_player.play()
            self.is_playing = True
            track_name = os.path.basename(track_path)
            self.current_track_label.setText(f"▶ {track_name}")

            self.highlight_current_track()

        except Exception as e:
            print(f"Ошибка в _actually_play_track: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка воспроизведения: {str(e)}")

    def toggle_play_pause(self):
        try:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.play_pause_button.setText("▶")
                self.is_playing = False
            else:
                if self.media_player.source().isEmpty():
                    if (self.current_playlist in self.playlists and
                            self.playlists[self.current_playlist] and
                            self.current_track_index >= 0):
                        self.play_current_track()
                    else:
                        QMessageBox.information(self, "Информация", "Нет треков в плейлисте")
                else:
                    self.media_player.play()
                    self.play_pause_button.setText("❚❚")
                    self.is_playing = True

        except Exception as e:
            print(f"Ошибка в toggle_play_pause: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка управления воспроизведением: {str(e)}")

    def pause(self):
        self.media_player.pause()
        self.play_pause_button.setText("▶")
        self.is_playing = False

    def stop(self):
        self.media_player.stop()
        self.current_track_label.setText("Трек не выбран")
        self.position_slider.setValue(0)
        self.play_pause_button.setText("▶")
        self.is_playing = False

    def play_next(self):
        try:
            if self.current_playlist in self.playlists and self.playlists[self.current_playlist]:
                if self.is_shuffle:
                    self.current_track_index = random.randint(0, len(self.playlists[self.current_playlist]) - 1)
                else:
                    self.current_track_index = (self.current_track_index + 1) % len(
                        self.playlists[self.current_playlist])

                self.play_current_track()

        except Exception as e:
            print(f"Ошибка в play_next: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка переключения трека: {str(e)}")

    def play_previous(self):
        try:
            if self.current_playlist in self.playlists and self.playlists[self.current_playlist]:
                if self.is_shuffle:
                    self.current_track_index = random.randint(0, len(self.playlists[self.current_playlist]) - 1)
                else:
                    self.current_track_index = (self.current_track_index - 1) % len(
                        self.playlists[self.current_playlist])

                self.play_current_track()

        except Exception as e:
            print(f"Ошибка в play_previous: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка переключения трека: {str(e)}")

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        self.shuffle_button.setText("⇄●" if self.is_shuffle else "⇄")

        if self.current_user and self.current_user.get('id'):
            settings = self.auth_manager.load_user_settings(self.current_user['id'])
            settings['shuffle_mode'] = self.is_shuffle
            self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        self.repeat_button.setText("↻●" if self.is_repeat else "↻")

        if self.current_user and self.current_user.get('id'):
            settings = self.auth_manager.load_user_settings(self.current_user['id'])
            settings['repeat_mode'] = self.is_repeat
            self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def set_volume(self, value):
        self.volume = value
        self.audio_output.setVolume(value / 100.0)
        self.volume_label.setText(f"{value}%")
        if self.current_user and self.current_user.get('id'):
            settings = self.auth_manager.load_user_settings(self.current_user['id'])
            settings['volume'] = value
            self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def on_position_changed(self, position):
        if not self.slider_pressed:
            duration = self.media_player.duration()
            if duration > 0:
                self.position_slider.setValue(int((position / duration) * 100))
                self.current_time_label.setText(self.format_time(position))

    def on_duration_changed(self, duration):
        if duration > 0:
            self.position_slider.setMaximum(100)
            self.total_time_label.setText(self.format_time(duration))

    def on_playback_state_changed(self, state):
        try:
            if state == QMediaPlayer.PlaybackState.PlayingState:
                self.play_pause_button.setText("❚❚")
                self.is_playing = True
            elif state == QMediaPlayer.PlaybackState.PausedState:
                self.play_pause_button.setText("▶")
                self.is_playing = False
            elif state == QMediaPlayer.PlaybackState.StoppedState:
                self.play_pause_button.setText("▶")
                self.is_playing = False

        except Exception as e:
            print(f"Ошибка в on_playback_state_changed: {e}")

    def format_time(self, milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def update_position(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            pass

    def on_slider_pressed(self):
        self.slider_pressed = True

    def on_slider_released(self):
        self.slider_pressed = False
        if self.media_player.duration() > 0:
            position = int((self.position_slider.value() / 100.0) * self.media_player.duration())
            self.media_player.setPosition(position)

    def on_user_label_clicked(self, event):
        if self.current_user:
            self.show_account_menu(event)

    def show_account_menu(self, event):
        if not self.current_user:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #bb86fc;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 20px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #bb86fc;
                color: black;
            }
        """)

        change_avatar_action = QAction("Изменить аватарку", self)
        change_avatar_action.triggered.connect(self.change_avatar)
        menu.addAction(change_avatar_action)

        change_name_action = QAction("Изменить имя", self)
        change_name_action.triggered.connect(self.change_username)
        menu.addAction(change_name_action)

        menu.addSeparator()

        logout_action = QAction("Выйти из аккаунта", self)
        logout_action.triggered.connect(self.handle_logout)
        menu.addAction(logout_action)

        menu.exec(self.user_label.mapToGlobal(self.user_label.rect().bottomLeft()))

    def show_track_context_menu(self, position):
        item = self.tracks_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #bb86fc;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 20px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #bb86fc;
                color: black;
            }
        """)

        play_action = QAction("Воспроизвести", self)
        play_action.triggered.connect(lambda: self.play_selected_track(item))
        menu.addAction(play_action)

        menu.addSeparator()

        remove_action = QAction("Удалить из плейлиста", self)
        remove_action.triggered.connect(lambda: self.remove_track_from_playlist(item))
        menu.addAction(remove_action)

        menu.exec(self.tracks_list.mapToGlobal(position))

    def remove_track_from_playlist(self, item):
        index = self.tracks_list.row(item)
        if (self.current_playlist in self.playlists and
                index < len(self.playlists[self.current_playlist])):

            if index == self.current_track_index:
                self.stop()
                self.current_track_index = -1

            del self.playlists[self.current_playlist][index]

            self.update_playlist_display()
            self.save_playlists()

            QMessageBox.information(self, "Успех", "Трек удален из плейлиста")

    def load_user_avatar(self, avatar_path, avatar_label):
        try:
            if avatar_path and os.path.exists(avatar_path):
                pixmap = QPixmap(avatar_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation)
                    rounded_pixmap = QPixmap(32, 32)
                    rounded_pixmap.fill(Qt.GlobalColor.transparent)

                    painter = QPainter(rounded_pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setBrush(QBrush(scaled_pixmap))
                    painter.setPen(QPen(QColor(187, 134, 252), 2))
                    painter.drawEllipse(0, 0, 32, 32)
                    painter.end()

                    avatar_label.setPixmap(rounded_pixmap)
                    return
        except Exception as e:
            print(f"Ошибка загрузки аватарки: {e}")
        self.set_default_avatar(avatar_label)

    def set_default_avatar(self, avatar_label):
        try:
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(45, 45, 45))

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(187, 134, 252), 2))
            painter.setBrush(QBrush(QColor(187, 134, 252)))

            painter.drawEllipse(4, 4, 24, 24)

            painter.setPen(QColor(26, 26, 26))
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            if self.current_user and self.current_user.get('username'):
                initial = self.current_user['username'][0].upper()
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initial)
            painter.end()

            avatar_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Ошибка создания дефолтной аватарки: {e}")

    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите аватарку", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path and self.current_user and self.current_user.get('id'):
            avatars_dir = os.path.join(BASE_DIR, "avatars")
            os.makedirs(avatars_dir, exist_ok=True)

            file_ext = os.path.splitext(file_path)[1]
            new_filename = f"avatar_{self.current_user['id']}{file_ext}"
            new_path = os.path.join(avatars_dir, new_filename)

            try:
                shutil.copy2(file_path, new_path)
                self.auth_manager.update_avatar(self.current_user['id'], new_path)

                self.current_user['avatar_path'] = new_path
                self.load_user_avatar(new_path, self.avatar_label)

                QMessageBox.information(self, "Успех", "Аватарка изменена")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось изменить аватарку:\n{str(e)}")

    def change_username(self):
        if not self.current_user:
            return

        new_username, ok = QInputDialog.getText(
            self, "Изменить имя", "Введите новое имя:",
            text=self.current_user.get('username', '')
        )

        if ok and new_username.strip() and self.current_user.get('id'):
            if self.auth_manager.update_username(self.current_user['id'], new_username.strip()):
                self.current_user['username'] = new_username.strip()
                self.user_label.setText(f"{self.current_user['username']}")

                if not self.current_user.get('avatar_path'):
                    self.set_default_avatar(self.avatar_label)

                QMessageBox.information(self, "Успех", "Имя изменено")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось изменить имя")

    def show_add_track_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить трек")
        dialog.setFixedSize(400, 200)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: white; }
            QLabel { color: white; font-size: 14px; }
            QPushButton { background-color: #bb86fc; color: black; border: none; border-radius: 8px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #9b66fc; }
            QLineEdit { background-color: #2d2d2d; color: white; border: 2px solid #bb86fc; border-radius: 8px; padding: 10px; }
        """)

        layout = QVBoxLayout()

        title = QLabel("Добавить трек")
        title.setStyleSheet("color: #bb86fc; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        from_device_btn = AnimatedButton("С устройства")
        from_device_btn.clicked.connect(lambda: self.add_from_device(dialog))
        layout.addWidget(from_device_btn)

        add_folder_btn = AnimatedButton("Добавить папку")
        add_folder_btn.clicked.connect(lambda: self.add_folder_from_dialog(dialog))
        layout.addWidget(add_folder_btn)

        layout.addStretch()

        close_btn = AnimatedButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def add_from_device(self, dialog):
        dialog.accept()
        self.add_files()

    def add_folder_from_dialog(self, dialog):
        dialog.accept()
        self.add_folder()


def main():
    try:
        app = QApplication(sys.argv)
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