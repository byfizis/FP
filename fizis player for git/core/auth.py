import sqlite3
import hashlib
import secrets
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from PyQt6.QtWidgets import QMessageBox
import json
import os


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