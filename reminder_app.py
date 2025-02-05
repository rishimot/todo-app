import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSharedMemory
import socketio
from utils import SERVER_URL

class SingleInstanceApp:
    def __init__(self):
        self.shared_memory = QSharedMemory("UniqueAppKey")
        if not self.shared_memory.create(1):
            print("Application is already running.")
            sys.exit(0)

class ReminderApp(SingleInstanceApp):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.tray_icon = QSystemTrayIcon(QIcon("image/reminder-aikon.png"), self.app)
        self.tray_icon.show()
        self.connect_server()

    def connect_server(self):
        self.sio = socketio.Client()
        try:
            self.sio.on('notification', self.on_notification)
            self.sio.connect(f'{SERVER_URL}')
            print(f"Connection Success")
        except Exception as e:
            print(f"Connection failed: {e}")

    def on_notification(self, data):
        taskName = data["taskName"]
        message = data["message"]
        self.tray_icon.showMessage(
            taskName,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    app = ReminderApp()
    app.run()