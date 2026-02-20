import sys
import os
from pathlib import Path
from dotenv import set_key, load_dotenv

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QPlainTextEdit
)
from PySide6.QtCore import QProcess, Qt
import subprocess

# Завантажуємо існуючий .env, якщо є
ENV_PATH = Path(".env")
load_dotenv(dotenv_path=ENV_PATH)

class BotControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EVS Bot Control Panel")
        self.setMinimumSize(600, 450) # Адаптивний розмір замість фіксованого

        # Процес для запуску бота
        self.bot_process = QProcess(self)
        self.bot_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels) # Об'єднуємо stdout та stderr
        self.bot_process.readyReadStandardOutput.connect(self.handle_stdout)
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
        
        self.save_token_btn = QPushButton("Зберегти токен")
        self.save_token_btn.clicked.connect(self.save_token)
        token_layout.addWidget(self.save_token_btn)
        
        layout.addLayout(token_layout)

        # 2. Індикатор статусу
        status_layout = QHBoxLayout()
        status_label = QLabel("Статус сервера:")
        self.status_indicator = QLabel("🔴 Зупинено")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch() # Відсуваємо індикатор ліворуч
        layout.addLayout(status_layout)

        # 3. Кнопки управління (Запуск/Зупинка)
        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Запустити бота")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.start_btn.clicked.connect(self.start_bot)
        
        self.stop_btn = QPushButton("⏹ Зупинити бота")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False) # Відключена при старті

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        layout.addLayout(controls_layout)
        
        # 4. Лог виводу з можливістю копіювання
        log_label_layout = QHBoxLayout()
        log_label = QLabel("Логи сервера:")
        
        self.copy_log_btn = QPushButton("📋 Скопіювати логи")
        self.copy_log_btn.clicked.connect(self.copy_logs)
        
        log_label_layout.addWidget(log_label)
        log_label_layout.addStretch()
        log_label_layout.addWidget(self.copy_log_btn)
        
        layout.addLayout(log_label_layout)
        
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        # Стилізація під консоль: темний фон, моноширинний шрифт
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(self.log_area)

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

        self.log_area.clear()
        self.append_log("Система: Запуск бота...")
        
        # Використовуємо системний python
        self.bot_process.start("python", ["-u", "main.py"]) # -u для небуферизованого виводу

    def stop_bot(self):
        if self.bot_process.state() == QProcess.ProcessState.Running:
            self.append_log("Система: Надсилання сигналу м'якої зупинки (taskkill)...")
            
            # В Windows QProcess.terminate() часто працює як kill(). 
            # Використовуємо taskkill для відправки SIGTERM на дерево процесів.
            pid = self.bot_process.processId()
            if sys.platform == 'win32':
                # Намагаємось закрити м'яко без /F (force)
                subprocess.call(['taskkill', '/PID', str(pid), '/T'])
            else:
                self.bot_process.terminate()

            # Чекаємо 3 секунди
            if not self.bot_process.waitForFinished(3000):
                self.append_log("Система: Процес не відповідає. Примусове завершення...")
                if sys.platform == 'win32':
                    subprocess.call(['taskkill', '/F', '/PID', str(pid), '/T'])
                else:
                    self.bot_process.kill()

    def handle_stdout(self):
        data = self.bot_process.readAllStandardOutput()
        stdout = bytes(data).decode('utf-8', errors='replace')
        self.append_log(stdout.strip())

    def append_log(self, text):
        if text:
            self.log_area.appendPlainText(text)
            # Автоматичний скрол донизу
            scrollbar = self.log_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def copy_logs(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_area.toPlainText())
        QMessageBox.information(self, "Успіх", "Логи скопійовано в буфер обміну!")

    def on_bot_started(self):
        self.status_indicator.setText("🟢 Працює")
        self.status_indicator.setStyleSheet("color: green; font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.token_input.setEnabled(False)
        self.save_token_btn.setEnabled(False)
        self.append_log("Система: Процес бота успішно стартував.")

    def on_bot_finished(self, exit_code, exit_status):
        self.status_indicator.setText("🔴 Зупинено")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.token_input.setEnabled(True)
        self.save_token_btn.setEnabled(True)
        
        # Визначаємо, чи це був очікуваний вихід через taskkill, чи реальний краш
        if exit_status == QProcess.ExitStatus.CrashExit and exit_code != 1:
            self.append_log("Система: Бот завершив роботу (Зупинено користувачем або Crash).")
        else:
            self.append_log(f"Система: Бот зупинений. Код виходу: {exit_code}")

    def on_bot_error(self, error):
        self.append_log(f"Система: Помилка процесу ({error.name})")

    def closeEvent(self, event):
        """Зупиняємо бота при закритті вікна."""
        self.stop_bot()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BotControlPanel()
    window.show()
    sys.exit(app.exec())
