from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QWidget, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from ui.widgets import AnimatedButton
from utils.helpers import get_app_icon


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