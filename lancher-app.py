import sys
import ctypes
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication
from utils import add_task_to_db_by_api, add_task2label_in_db
from todo_app import TaskDialog
from ctypes import wintypes
import win32con

HOTKEY_ID = 1  
MOD_CTRL_ALT = win32con.MOD_CONTROL | win32con.MOD_ALT
VK_SPACE = win32con.VK_SPACE
MOD_CTRL = win32con.MOD_CONTROL

class MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt", wintypes.POINT)]

class LancherTaskDialog(TaskDialog):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icon/space_rocket.ico"))  
        self.setWindowTitle("Task")

    def toggle_window(self):
        if self.isHidden():
            self.start_new_editing()
            self.show()
            self.activateWindow()
            self.raise_()
            self.task_name.setFocus()
        else:
            self.hide()

    def post_task(self): 
        task_name = self.task_name.text()
        task_goal = self.task_goal.text()
        task_detail = self.task_detail.toPlainText()
        task_deadline_date = self.task_deadline_date.text()
        task_deadline = None 
        if task_deadline_date != "":
            task_deadline_time = self.task_deadline_time.text()
            task_deadline = task_deadline_date + " " + task_deadline_time
        task_type = self.task_type.currentText()
        status_id = self.status_combo.itemData(self.status_combo.currentIndex())
        waiting_task = self.waiting_input.text()
        has_reminder = self.reminder.isChecked()
        remind_date = self.remind_timer.text() if has_reminder else None
        remind_input = self.remind_input.text() if has_reminder else None
        result = add_task_to_db_by_api((task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input))
        assert result, "データベースの追加に失敗しました。"
        task_id = result["taskId"]
        labels_id = self.newlabels_id
        for label_id in labels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)
    
    def handle_accept(self):
        self.add_label()
        self.post_task()
        self.clear_input()
        self.accept()

    def handle_reject(self):
        is_continue = self.is_continue_editing()
        if is_continue:
            return
        self.clear_input()
        self.reject()

    def closeEvent(self, event):
        is_continue = self.is_continue_editing()
        if is_continue:
            event.ignore() 
        self.clear_input()

    def clear_input(self):
        self.hide()
        self.task_name.clear()
        self.task_goal.clear()
        self.task_detail.clear()
        self.task_deadline_date.setText(None)
        self.task_type.setCurrentText("-")
        self.status_combo.setCurrentText("TODO") 
        self.waiting_input.clear()
        self.label_input.clear()
        self.newlabels_id = []
        while self.label_display_layout.count():
            item = self.label_display_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.reminder.setChecked(False)
        self.remind_timer.clear()
        self.remind_input.clear()

def main():
    app = QApplication(sys.argv)
    lancher_app = LancherTaskDialog()

    if not ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, MOD_CTRL_ALT, VK_SPACE):
        print("ホットキーの登録に失敗しました")
        sys.exit(-1)

    try:
        msg = MSG()
        while True:
            if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, win32con.PM_REMOVE):
                if msg.message == win32con.WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    lancher_app.toggle_window()
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
