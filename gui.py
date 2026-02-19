import sys
import os
from pathlib import Path
from dotenv import set_key, load_dotenv

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import QProcess, Qt

# Завантажуємо існуючий .env, якщо є
ENV_PATH = Path(".env")
load_dotenv(dotenv_path=ENV_PATH)

class BotControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EVS Bot Control Panel")
        self.setFixedSize(400, 250)

        # Процес для запуску бота
        self.bot_process = QProcess(self)
        self.bot_process.started.connect(self.on_bot_started)
        self.bot_process.finished.connect(self.on_bot_finished)
        self.bot_process.errorOccurred.connect(self.on_bot_error)
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. Поле для токена
        token_layout = QHBoxLayout()
        token_label = QLabel("Telegram Bot Token:")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Завантажуємо токен з .env
        saved_token = os.getenv("BOT_TOKEN", "")
        if saved_token:
            self.token_input.setText(saved_token)
            
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)

        # Кнопка збереження токена
        self.save_token_btn = QPushButton("Зберегти токен")
        self.save_token_btn.clicked.connect(self.save_token)
        layout.addWidget(self.save_token_btn)

        # 2. Індикатор статусу
        status_layout = QHBoxLayout()
        status_label = QLabel("Статус сервера:")
        self.status_indicator = QLabel("🔴 Зупинено")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_indicator)
        layout.addLayout(status_layout)

        # 3. Кнопки управління (Запуск/Зупинка)
        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Запустити бота")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_bot)
        
        self.stop_btn = QPushButton("⏹ Зупинити бота")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False) # Відключена при старті

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        layout.addLayout(controls_layout)
        
        # 4. Лог виводу (Опціонально, для відображення помилок з stderr)
        self.log_label = QLabel("")
        self.log_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.log_label)

    def save_token(self):
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Помилка", "Токен не може бути порожнім!")
            return
            
        if not ENV_PATH.exists():
            ENV_PATH.touch()
            
        set_key(dotenv_path=ENV_PATH, key_to_set="BOT_TOKEN", value_to_set=token)
        
        # Оновлюємо змінні оточення для поточного процесу
        os.environ["BOT_TOKEN"] = token
        QMessageBox.information(self, "Успіх", "Токен успішно збережено у файл .env!")

    def start_bot(self):
        # Перевірка наявності токена
        token = os.getenv("BOT_TOKEN", "")
        if not token:
            QMessageBox.warning(self, "Увага", "Спочатку збережіть токен Telegram-бота!")
            return

        self.log_label.setText("Запуск...")
        # Використовуємо системний python (або з віртуального оточення, якщо він запущений через нього)
        self.bot_process.start("python", ["main.py"])

    def stop_bot(self):
        if self.bot_process.state() == QProcess.ProcessState.Running:
            self.bot_process.terminate()
            self.bot_process.waitForFinished(3000)
            if self.bot_process.state() == QProcess.ProcessState.Running:
                self.bot_process.kill()

    def on_bot_started(self):
        self.status_indicator.setText("🟢 Працює")
        self.status_indicator.setStyleSheet("color: green; font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.token_input.setEnabled(False)
        self.save_token_btn.setEnabled(False)
        self.log_label.setText("Бот успішно запущений.")

    def on_bot_finished(self, exit_code, exit_status):
        self.status_indicator.setText("🔴 Зупинено")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.token_input.setEnabled(True)
        self.save_token_btn.setEnabled(True)
        
        # Читаємо помилки, якщо бот впав
        stderr = self.bot_process.readAllStandardError().data().decode('utf-8')
        if stderr:
            self.log_label.setText(f"Помилка: {stderr[:100]}...")
        else:
            self.log_label.setText("Бот зупинений.")

    def on_bot_error(self, error):
        self.log_label.setText(f"Помилка процесу: {error.name}")

    def closeEvent(self, event):
        """Зупиняємо бота при закритті вікна."""
        self.stop_bot()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BotControlPanel()
    window.show()
    sys.exit(app.exec())
