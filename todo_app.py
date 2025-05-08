import os
import urllib.parse
import subprocess
import sys
import pickle
import datetime
from dateutil.relativedelta import relativedelta
import webbrowser
import socketio
import re
from utils import (
    generate_random_color,
    count_weekdays,
    get_allstatus_form_db,
    get_status_by_name_from_db,
    get_task_from_db,
    get_pin_by_taskid_from_db,
    get_mark_by_taskid_from_db,
    get_display_by_taskid_from_db,
    get_disable_tasks_from_db,
    get_alltask_from_db,
    get_allsubtask_from_db,
    get_alllabel_by_taskid_from_db,
    get_allchildtask_from_db,
    get_parenttask_from_db,
    get_label_by_name_from_db,
    get_task2label_by_taskid_from_db,
    get_subtask_by_parentid_and_childid_from_db,
    get_subtask_by_childid_from_db,
    get_subtask_by_parentid_from_db,
    get_subtask_from_db,
    get_task2label_by_labelid_from_db,
    get_label2task_from_db,
    get_time_by_taskid_from_db,
    add_task2label_in_db,
    add_task_to_db_by_api,
    add_subtask_to_db_by_api,
    add_time_to_db_by_api,
    add_label_to_db,
    update_task_in_db_by_api,
    update_subtask_in_db_by_api,
    update_pin_task_to_db,
    update_mark_task_to_db,
    update_display_task_to_db,
    delete_label_in_db,
    delete_task2label_from_db,
    delete_task2label_by_labelname_from_db,
    delete_task_from_db_by_api,
    delete_subtask_from_db_by_api,
    delete_display_task_in_db,
    SERVER_URL,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QTimer,
    QEvent,
    QPoint,
    QTime,
    QDateTime,
)
from PyQt6.QtGui import(
    QColor,
    QIcon,
    QKeySequence,
    QShortcut,
    QMouseEvent,
    QPixmap,
    QCursor,
    QTextCursor,
    QTextCharFormat,
    QTransform,
    QFont
) 
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QLabel,
    QDialog,
    QComboBox,
    QFormLayout,
    QTextEdit,
    QDialogButtonBox,
    QTreeWidgetItem,
    QCalendarWidget,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QMenu,
    QCheckBox,
    QTimeEdit,
    QDateTimeEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
)

class DigitalTimer(QWidget):
    def __init__(self, parent=None, task_id=None):
        super().__init__(parent)
        self.task_id = task_id
        self.action_id = ""
        self.setting_time = 30
        self.button_size = (25, 25)
        self.mode = "CountDown"
        self.start_time = None
        self.end_time = None
        self.break_time = False
        self.timer_running = False
        self.time_format = "%Y/%m/%d %H:%M"
        self.load_assets()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.label = QLabel(f'/ {self.setting_time:03}:00', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedHeight(30)
        self.label.mousePressEvent = lambda event: self.change_mode()
        layout.addWidget(self.label)
        self.start_button = self.createButton(self.saisei_pixmap, lambda event: self.start_timer())
        layout.addWidget(self.start_button)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown_timer if self.mode == "CountDown" else self.update_countup_timer)

        menu = QMenu()
        exit_action = menu.addAction("終了")
        exit_action.triggered.connect(self.close)
        self.tray_icon = QSystemTrayIcon(QIcon("icon/start_button.ico"), self)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def load_assets(self):
        saisei_pixmap = QPixmap("image/player_button_blue_saisei.png")
        teishi_pixmap = QPixmap("image/player_button_blue_teishi.png")
        ichijiteishi_pixmap = QPixmap("image/player_button_blue_ichijiteishi.png")
        self.saisei_pixmap = saisei_pixmap.scaled(*self.button_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.teishi_pixmap = teishi_pixmap.scaled(*self.button_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.ichijiteishi_pixmap = ichijiteishi_pixmap.scaled(*self.button_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def createButton(self, pixmap, callback=None):
        button = QLabel(self)
        button.setMaximumSize(*self.button_size)
        button.setPixmap(pixmap)
        button.mousePressEvent = callback
        return button

    def is_timer_running(self):
        return self.timer_running

    def change_mode(self):
        self.timer.timeout.disconnect()
        if self.mode == "CountDown":
            self.mode = "CountUp" 
            self.label.setText(f'/ 00:00')
            self.timer.timeout.connect(self.update_countup_timer)
        elif self.mode == "CountUp":
            self.mode = "CountDown"
            self.label.setText(f'/ {self.setting_time:03}:00')
            self.timer.timeout.connect(self.update_countdown_timer)

    def start_timer(self, time=None):
        time = self.setting_time if time is None else time
        if not self.is_timer_running():
            self.start_time = datetime.datetime.now().strftime(self.time_format)
        self.time_elapsed = time * 60 if self.mode == "CountDown" else 0
        self.duration_time = 0
        self.timer_running = True
        self.timer.start(1000) 
        self.label.mousePressEvent = lambda event: self.pause_timer()
        self.start_button.setPixmap(self.teishi_pixmap)
        self.start_button.mousePressEvent = lambda event: self.stop_timer()
    
    def pause_timer(self):
        self.start_button.setPixmap(self.saisei_pixmap)
        self.start_button.mousePressEvent = lambda event: self.resume_timer()
        self.label.mousePressEvent = lambda event: self.resume_timer()
        self.timer_running = False
        self.timer.stop()

    def resume_timer(self):
        self.timer_running = True
        self.timer.start(1000) 
        self.start_button.setPixmap(self.teishi_pixmap)
        self.start_button.mousePressEvent = lambda event: self.stop_timer()
        self.label.mousePressEvent = lambda event: self.pause_timer()

    def update_countdown_timer(self):
        self.duration_time += 1 
        self.time_elapsed -= 1
        if self.time_elapsed >= 0:
            minutes = (self.time_elapsed % 3600) // 60
            seconds = self.time_elapsed % 60
            self.label.setText(f'/ {minutes:03}:{seconds:02}')
            if self.break_time and self.time_elapsed == 0:
                self.stop_timer()
        else:
            minutes = (-self.time_elapsed % 3600) // 60
            seconds = -self.time_elapsed % 60
            self.label.setText(f'/ -{minutes:03}:{seconds:02}')

    def update_countup_timer(self):
        self.duration_time += 1
        self.time_elapsed += 1
        minutes = (self.time_elapsed % 3600) // 60
        seconds = self.time_elapsed % 60
        self.label.setText(f'/ {minutes:03}:{seconds:02}')

    def stop_timer(self):
        self.timer_running = False
        self.timer.stop()
        self.start_button.setPixmap(self.saisei_pixmap)
        self.start_button.mousePressEvent = lambda event: self.start_timer()
        self.label.mousePressEvent = lambda event: self.change_mode()
        if self.duration_time >= 60:
            end_time = datetime.datetime.now().strftime(self.time_format)
            if not self.break_time:
                add_time_to_db_by_api((self.start_time, end_time, self.duration_time, self.task_id))
            self.tray_icon.showMessage(
                "Notification",
                f"{self.duration_time // 60}分{self.duration_time % 60}秒が経ちました",
                QSystemTrayIcon.MessageIcon.Information,
                1000
            )
            self.break_time = not self.break_time
            self.start_time = None
        elif self.break_time:
            self.start_time = None
            self.break_time = not self.break_time
        if self.break_time and self.mode == "CountDown":
            self.label.setText(f'/ 5:00')
            self.start_timer(time=5)
        else:
            self.label.setText(f'/ {self.setting_time:02}:00' if self.mode == "CountDown" else "/ 00:00")

    def maximize(self):
        self.start_button.show()
        self.label.setFixedHeight(20)

    def minimize(self):
        self.start_button.hide()
        self.label.setFixedHeight(10)

class TargetWidget(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setPlaceholderText("Target is in this time...")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)   

    def keyPressEvent(self, event: QMouseEvent):
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.clearFocus()
        super().keyPressEvent(event)

class PopupTaskWindow(QDialog):
    def __init__(self, item):
        super().__init__()
        self.setWindowIcon(QIcon("icon/start_button.ico"))
        self.setWindowTitle("Popup Task Window")
        self.item = item
        self.task_id = item.data(0, Qt.ItemDataRole.UserRole) 
        self.text = item.name
        self.kanban_board = None
        self.start_pos = None
        self.close_button_size = (15, 15)
        self.pin_size = (15, 15)
        self.connect_server()
        self.load_assets()
        self.init_ui()
        self.setup_shortcuts()

    def connect_server(self):
        self.sio = socketio.Client()
        try:
            self.sio.on('update_task', self.on_update_task)

            self.sio.connect(f'{SERVER_URL}')
            print(f"Connection Success")
        except Exception as e:
            print(f"Connection failed: {e}")

    def on_update_task(self, updated_task_id, updated_task_data): 
        if updated_task_id != self.item.data(0, Qt.ItemDataRole.UserRole):
            return
        self.text = updated_task_data['name']
        self.task_name.setText(updated_task_data['name'])
        """
        if updated_task_data["status_name"] != "DOING":
            self.hide()
        """

    def init_ui(self):
        self.setGeometry(0, 0, 200, 40)

        layout = QHBoxLayout()

        button_layout = QVBoxLayout()
        self.pin = QLabel(self)
        self.pin.setPixmap(self.pin_red_pixmap)
        self.pin.setFixedSize(*self.pin_size)
        self.pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin.mousePressEvent = self.pin_clicked
        button_layout.addWidget(self.pin)

        self.close_button = QPushButton("x", self)
        self.close_button.setFixedSize(*self.close_button_size)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #A9A9A9;
                font-size: 10px;
                color: white;
                border: none;
                border-radius: 7;
            }
            QPushButton:hover {
                background-color: darkred; 
            }
        """)
        self.close_button.clicked.connect(self.close)
        self.close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button_layout.addWidget(self.close_button)

        self.button_widget = QWidget()
        self.button_widget.setLayout(button_layout)
        layout.addWidget(self.button_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.task_layout = QVBoxLayout()
        self.task_name = QLabel(self.text, self)
        self.task_layout.addWidget(self.task_name)

        self.target = TargetWidget(self) 
        self.task_layout.addWidget(self.target)
        main_layout.addLayout(self.task_layout)

        self.task_timer = DigitalTimer(self, self.task_id)
        main_layout.addWidget(self.task_timer)

        self.main_widget = QWidget()
        self.main_widget.setLayout(main_layout)
        self.main_widget.setStyleSheet("QWidget { color: yellow; }")
        layout.addWidget(self.main_widget)

        self.setLayout(layout)
        self.setStyleSheet("QDialog { background-color: black; }")
        self.setWindowFlags(self.windowType() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.adjustSize()
        self.original_size = (self.width(), self.height())
        self.small_mode()

    def load_assets(self):
        pin_red_pixmap = QPixmap("image/gabyou_pinned_plastic_red.png")
        pin_white_pixmap = QPixmap("image/gabyou_pinned_plastic_white.png")
        self.pin_red_pixmap = pin_red_pixmap.scaled(*self.pin_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.pin_white_pixmap = pin_white_pixmap.scaled(*self.pin_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def keyPressEvent(self, event: QMouseEvent):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Escape:
            return
        if event.key() == Qt.Key.Key_N and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if not self.kanban_board:
                self.kanban_board = TodoBoard()
                self.kanban_board.popup_window = self
            if self.kanban_board.isHidden():
                self.kanban_board.show()
            if self.kanban_board.isMinimized():
                self.kanban_board.showNormal()
            if not self.kanban_board.isActiveWindow():
                self.kanban_board.activateWindow()
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            parent_rect = self.geometry()
            mouse_pos = QCursor.pos()
            if not parent_rect.contains(mouse_pos):
                self.small_mode()
        super().keyPressEvent(event)

    def setup_shortcuts(self):
        close_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_M), self)
        close_shortcut.activated.connect(self.close)

    def pin_clicked(self, event):
        self.hide()
        QTimer.singleShot(5000, self.show) 

    def mouseDoubleClickEvent(self, event):
        if not self.kanban_board:
            self.kanban_board = TodoBoard()
            self.kanban_board.popup_window = self
        task_dialog = self.kanban_board.open_edit_task_dialog(self.item)
        task_dialog.finished.connect(self.check_doing_task) 
        super().mouseDoubleClickEvent(event)
    
    def check_doing_task(self):
        if self.item.get_status() != "DOING":
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()  
        if event.button() == Qt.MouseButton.RightButton:
            if not self.kanban_board:
                self.kanban_board = TodoBoard()
                self.kanban_board.popup_window = self
            if self.kanban_board.isHidden():
                self.kanban_board.show()
            if self.kanban_board.isMinimized():
                self.kanban_board.showNormal()
            if not self.kanban_board.isActiveWindow():
                self.kanban_board.activateWindow()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.start_pos is not None:
            new_position = self.pos() + (event.globalPosition().toPoint() - self.start_pos)

            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            new_x = max(screen_geometry.left(), min(new_position.x(), screen_geometry.right() - self.width()))
            new_y = max(screen_geometry.top(), min(new_position.y(), screen_geometry.bottom() - self.height()))

            self.move(new_x, new_y)  
            self.start_pos = event.globalPosition().toPoint() 
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = None
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.enlarge_mode()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.target.hasFocus():# and self.task_timer.is_timer_running():
            self.small_mode()
        super().leaveEvent(event)

    def enlarge_mode(self):
        self.button_widget.show()
        self.task_name.setText(self.text)
        self.target.show()
        self.task_timer.maximize()
        self.setFixedHeight(self.original_size[1])
        self.adjustSize()

    def small_mode(self):
        self.button_widget.hide()
        if self.target.text() != "":
            self.task_name.setText(self.target.text())
        self.target.hide()
        self.task_timer.minimize()
        self.setFixedHeight(35)
        self.adjustSize()

    def closeEvent(self, event):
        if self.task_timer.start_time:
            self.task_timer.stop_timer()

        if self.kanban_board:
            self.kanban_board.show()
            self.kanban_board.raise_()
            self.kanban_board.activateWindow()
        else:
            kanban_board = TodoBoard()
            kanban_board.show()
        return super().closeEvent(event)

class SearchBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        layout.addWidget(self.search_bar)
        self.search_label = QLabel("", self)
        layout.addWidget(self.search_label)
        self.setLayout(layout)

    def _filter_word(self, word, items):
        is_exclude = word.startswith('!')
        word = word[1:] if is_exclude else word
        for item in items:
            if item.isHidden():
                continue
            item.setHidden(not(is_exclude ^ (item.text(0).find(word) != -1)))

    def _filter_tag(self, tag, items):
        is_exclude = tag.startswith('!')
        tag_content = tag[1:] if is_exclude else tag
        for item in items:
            if item.isHidden():
                continue
            task_id = item.data(0, Qt.ItemDataRole.UserRole) 
            labels = get_alllabel_by_taskid_from_db(task_id=task_id)
            item.setHidden(not(is_exclude ^ any([label_name.find(tag_content) != -1 for _, label_name, _, _ in labels])))

    def _filter_act(self, act, items):
        if act.lower() == "count":
            self._count_items(items)
        if act.lower() == "off":
            for item in items:
                item.setHidden(True)
        if act.lower() == "next":
            first_item = None
            for item in items:
                if item.isHidden():
                    continue
                if not first_item:
                    first_item = item
                else:
                    item.setHidden(True)
        if act.lower() == "all":
            for item in items:
                item.setHidden(False)
        if act.lower() == "expand":
            for item in items:
                item.setExpanded(True)
        if act.lower() == "fold":
            for item in items:
                item.setExpanded(False)

    def count_items(self, column):
        items = []
        for index in range(column.topLevelItemCount()):
            item = column.topLevelItem(index)
            items.append(item)
        self._count_items(items)

    def _count_items(self, items):
        cnt = 0
        for item in items:
            if not item.isHidden():
                cnt += 1
        self.search_label.setText(f"/{cnt}")

    def filter(self, column):
        items = []
        for index in range(column.topLevelItemCount()):
            item = column.topLevelItem(index)
            item.setHidden(item.is_disable())
            items.append(item)
        search_text = self.search_bar.text().replace("　", " ")
        if search_text != "":
            splitted_search_texts = search_text.split(' ')
            is_tag = False
            is_pre_act = False
            is_act = False
            tags = []
            acts = []
            pre_acts = []
            words = []
            for splitted_search_text in splitted_search_texts:
                if splitted_search_text == "tag:":
                    is_tag = True
                    continue

                if splitted_search_text == "pre-act:":
                    is_pre_act = True
                    continue

                if splitted_search_text == "act:":
                    is_act = True
                    continue


                if is_tag is False and splitted_search_text.startswith('tag:'):
                    tags.append(splitted_search_text[4:])
                    continue

                if is_pre_act is False and splitted_search_text.startswith('pre-act:'):
                    pre_acts.append(splitted_search_text[8:])
                    continue

                if is_act is False and splitted_search_text.startswith('act:'):
                    acts.append(splitted_search_text[4:])
                    continue

                if is_tag:
                    tags.append(splitted_search_text)
                    is_tag = False
                elif is_act:
                    acts.append(splitted_search_text)
                    is_act = False
                elif is_pre_act:
                    pre_acts.append(splitted_search_text)
                    is_pre_act = False
                else:
                    words.append(splitted_search_text)

            for pre_act in pre_acts:
                self._filter_act(pre_act, items)
            for tag in tags:
                self._filter_tag(tag, items)
            for word in words:
                self._filter_word(word, items)
            for act in acts:
                self._filter_act(act, items)
        self._count_items(items)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.hasFocus():
                self.clearFocus()
        if event.key() == Qt.Key.Key_Delete and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.setText("")
        super().keyPressEvent(event)
    
class TodoItem(QTreeWidgetItem):
    def __init__(self, text, id):
        self.id = id
        is_marked = self.is_marked()
        is_pinned = self.is_pinned()
        set_text = f"#{id} {text}"
        set_text = f"★{set_text}" if is_marked else set_text
        set_text = f"📌{set_text}" if is_pinned else set_text
        super().__init__([set_text])
        self.name = text
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_detail)
        self.detail_label = None
        self.setData(0, Qt.ItemDataRole.UserRole, id) 

    def is_pinned(self):
        (_, _, is_pinned) = get_pin_by_taskid_from_db(self.id)
        return is_pinned

    def is_marked(self):
        (_, _, is_marked) = get_mark_by_taskid_from_db(self.id)
        return is_marked
        
    def is_disable(self):
        (_, _, is_disable) = get_display_by_taskid_from_db(self.id)
        return is_disable

    def get_status(self):
        (_, _, _, _, _, status_name, _, _, _) = get_task_from_db(self.id)
        return status_name

    def get_content(self):
        task_name, _, _, deadline, _, status_name, waiting_task, _, _ = get_task_from_db(self.id)
        content = f"{task_name}"
        if deadline:
            content += f"\n~{deadline}"
        if status_name == "WAITING":
            content += f"\nI'm waiting for... {waiting_task}"
        parent_task = get_parenttask_from_db(child_task_id=self.id)
        if parent_task:
            _, task_name, _, _, _, _, _, _, _, _ = parent_task
            content += f"\n⬆️{task_name}"
        if self.childCount() > 0:
            content += f"\nA number of children: {len(self.get_child_items())}"
        return content
    
    def show_detail(self):
        if self.detail_label is None:
            content = self.get_content()
            self.detail_label = QLabel(content)
            self.detail_label.setWindowFlag(Qt.WindowType.ToolTip)
            self.detail_label.move(QCursor.pos() + QPoint(10, 10))
            self.detail_label.show()
    
    def clear_detail(self):
        if self.detail_label is not None:
            self.detail_label.close()
            self.detail_label = None
    
    def setText(self, atext):
        self.title = atext
        is_pinned = self.is_pinned()
        is_marked = self.is_marked()
        title = f"#{self.id} {atext}"
        title = f"📌{title}" if is_pinned else title
        title = f"★{title}" if is_marked else title
        return super().setText(0, title)

    def editText(self, atext):
        return super().setText(0, atext)
    
    def has_parent_task(self):
        return get_parenttask_from_db(child_task_id=self.id) is not None

    def get_child_tasks(self):
        child_tasks = get_allchildtask_from_db(self.id)
        return child_tasks

    def get_child_items(self):
        child_items = []
        for i in range(self.childCount()):
            child_item = self.child(i)
            if not child_item.is_disable():
                child_items.append(child_item)
                child_items.extend(child_item.get_child_items())
        return child_items

class TodoColumn(QTreeWidget):
    def __init__(self, title, kanban_board):
        super().__init__()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.pinned_items = []
        self.kanban_board = kanban_board
        self.id, self.name = get_status_by_name_from_db(title)
        self.current_item = None
        self.editing_item = None 
        self.init_ui()
        self.setMouseTracking(True)

    def init_ui(self):
        self.setHeaderHidden(True)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.setStyleSheet("""
            QTreeWidget::item {
                border: 2px solid black;  /* 縁取りの色と太さ */
                border-radius: 5px;       /* 角を丸く */
                padding: 10px;            /* 内側の余白 */
            }
            QTreeWidget::item:selected {
                background-color: lightblue;  /* 選択時の背景色 */
            }
        """)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        self.clearSelection()
        self.clearFocus()
        drop_item = self.itemAt(event.position().toPoint())
        drag_item = event.source().currentItem()
        drag_item_task_id = drag_item.data(0, Qt.ItemDataRole.UserRole)
        if drop_item:
            if drag_item.parent():
                subtask_id, parent_task_id, child_task_id, _ = get_subtask_by_childid_from_db(child_id=drag_item_task_id)
                result = update_subtask_in_db_by_api(subtask_id, parent_task_id, child_task_id, is_treed=0)
                assert result, "データベースの更新でエラー"
                if result["type"] == "local":
                    self.kanban_board.on_update_subtask(subtask_id, {"parent_id": parent_task_id, "child_id": drag_item_task_id, "is_treed": 0}) 
            else:
                drop_item_task_id = drop_item.data(0, Qt.ItemDataRole.UserRole)
                if drop_item.childCount() > 0 and drop_item.isExpanded():
                    result = add_subtask_to_db_by_api(drop_item_task_id, drag_item_task_id, is_treed=1)
                    assert result, "データベースの追加でエラー"
                    subtask_id = result["subtaskId"]
                    if result["type"] == "local":
                        self.kanban_board.on_post_subtask(subtask_id, {"parent_id": drop_item_task_id, "child_id": drag_item_task_id, "is_treed": 1}) 
                elif drag_item.has_parent_task():
                    subtask_id, parent_drag_item_task_id, _, _ = get_subtask_by_childid_from_db(child_id=drag_item_task_id)
                    if drop_item_task_id == parent_drag_item_task_id:
                        result = update_subtask_in_db_by_api(subtask_id, drop_item_task_id, drag_item_task_id, is_treed=1)
                        assert result, "データベースの更新でエラー"
                        if result["type"] == "local":
                            self.kanban_board.on_update_subtask(subtask_id, {"parent_id": drop_item_task_id, "child_id": drag_item_task_id, "is_treed": 1}) 
                if self == event.source():
                    drag_item_index = self.indexOfTopLevelItem(drag_item)
                    drop_item_index = self.indexOfTopLevelItem(drop_item)
                    self.takeTopLevelItem(drag_item_index)
                    self.insertTopLevelItem(drop_item_index, drag_item)
                    self.setCurrentItem(drag_item)
        else:
            if drag_item.parent():
                subtask_data = get_subtask_by_childid_from_db(child_id=drag_item_task_id)
                if subtask_data:
                    subtask_id, parent_task_id, child_task_id, _ = subtask_data
                    result = update_subtask_in_db_by_api(subtask_id, parent_task_id, child_task_id, is_treed=0)
                    assert result, "データベースの更新でエラー"
                    if result["type"] == "local":
                        self.kanban_board.on_update_subtask(subtask_id, {"parent_id": parent_task_id, "child_id": child_task_id, "is_treed": 0}) 
            if self == event.source():
                drag_item_index = self.indexOfTopLevelItem(drag_item)
                self.takeTopLevelItem(drag_item_index)
                self.insertTopLevelItem(self.topLevelItemCount(), drag_item)
                self.setCurrentItem(drag_item)
        if self != event.source():
            event.source().takeTopLevelItem(event.source().indexOfTopLevelItem(drag_item))
            self.addTopLevelItem(drag_item)
            self.move_selected_item(drag_item, event.source())
        return 

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            selected_items = self.selectedItems()
            if selected_items:
                self.delete_selected_item(selected_items)
        if event.key() == Qt.Key.Key_Escape:
            selected_item = self.currentItem()
            if selected_item:
                if self.editing_item:
                    self.stop_editing(selected_item)
                    selected_item.setText(selected_item.name)
                self.clearSelection()
                self.clearFocus()
                return
        if event.key() == Qt.Key.Key_F2:
            selected_item = self.currentItem()
            if selected_item:
                self.start_editing(selected_item)
        if event.key() == Qt.Key.Key_Return:
            selected_item = self.currentItem()
            if selected_item:
                self.stop_editing(selected_item)
                self.update_selected_item(selected_item)
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                self.copy_item()
            if event.key() == Qt.Key.Key_V:
                self.paste_item()
            if event.key() == Qt.Key.Key_M:
                selected_item = self.currentItem()
                if selected_item:
                    self.show_popup_item(selected_item)
                    self.kanban_board.close()
            if event.key() == Qt.Key.Key_Up:
                selected_item = self.currentItem()
                if selected_item:
                    index = self.indexOfTopLevelItem(selected_item)
                    if index > 0 and index != -1:
                        self.takeTopLevelItem(index)
                        self.insertTopLevelItem(index - 1, selected_item)
                        self.clearSelection()
                        selected_item.setSelected(True)
                        self.setCurrentItem(selected_item)
                        return
            if event.key() == Qt.Key.Key_Down:
                selected_item = self.currentItem()
                if selected_item:
                    index = self.indexOfTopLevelItem(selected_item)
                    if index < self.topLevelItemCount() - 1 and index != -1:
                        self.takeTopLevelItem(index)
                        self.insertTopLevelItem(index + 1, selected_item)
        return super().keyPressEvent(event)

    def start_editing(self, item):
        self.openPersistentEditor(item)
        item.editText(item.name)
        self.editing_item = item

    def stop_editing(self, item):
        self.closePersistentEditor(item) 
        self.editing_item = None 

    def focusOutEvent(self, event):
        self.clearSelection()
        super().focusOutEvent(event)

    def show_popup_item(self, item):
        popup_task_window = PopupTaskWindow(item)
        if self.kanban_board.popup_window:
            if popup_task_window.task_id == self.kanban_board.popup_window.task_id:
                self.kanban_board.popup_window.raise_()
                return
            else:
                self.kanban_board.popup_window.close()
        popup_task_window.show()
        popup_task_window.task_timer.start_timer()
        self.kanban_board.poup_window = popup_task_window

    def mouseMoveEvent(self, event):
        if event.type() == QEvent.Type.MouseMove:
            item = self.itemAt(event.position().toPoint())
            if item:
                if self.current_item is None:
                    self.current_item = item
                    self.current_item.timer.start(100)
                elif item != self.current_item:
                    self.current_item.clear_detail()
                    self.current_item.timer.stop()
                    self.current_item = item
                    self.current_item.timer.start(100)
            else:
                if self.current_item:
                    self.current_item.clear_detail()
                    self.current_item.timer.stop()
                    self.current_item = None
        super().mouseMoveEvent(event)
    
    def clear_item_detail(self):
        if self.current_item:
            self.current_item.clear_detail()
            self.current_item.timer.stop()
            self.current_item = None

    def leaveEvent(self, event):
        self.clear_item_detail()
        super().leaveEvent(event)
    
    def show_context_menu(self, position):
        item = self.itemAt(position)
        if item is None:
            return 
        is_pinned = item.is_pinned()
        is_marked = item.is_marked()
        is_disable = item.is_disable()
        menu = QMenu(self)
        pin_action = menu.addAction("ピンを解除" if is_pinned else "ピン留め")
        mark_action = menu.addAction("マークを解除" if is_marked else "マーク")
        hidden_item_action = menu.addAction("表示" if is_disable else "非表示")

        priority_menu = QMenu("優先度", self)
        priority_middle_action = priority_menu.addAction("中")
        priority_low_action = priority_menu.addAction("低")
        menu.addMenu(priority_menu)

        move_menu = QMenu("移動", self)
        move2top_action = move_menu.addAction("トップへ")
        move2bottom_action = move_menu.addAction("ボトムへ")
        if item.has_parent_task():
            move2parent_action = move_menu.addAction("親タスクへ戻る")
            disable_parent_action = move_menu.addAction("親タスクを解除")
        else:
            move2parent_action = disable_parent_action = None
        menu.addMenu(move_menu)

        expand_childtask_action = menu.addAction("展開" if len(item.get_child_tasks()) > 0 else "折りたたむ")

        action = menu.exec(self.mapToGlobal(position))
        if action == pin_action:
            self.toggle_pin_item(item)
        elif action == mark_action:
            self.toggle_mark_item(item)
        elif action == hidden_item_action:
            self.toggle_display_item(item)
        elif action == move2top_action:
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            self.insertTopLevelItem(0, item)
        elif action == move2bottom_action:
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            self.insertTopLevelItem(self.topLevelItemCount(), item)
        elif action == move2parent_action:
            if item.has_parent_task():
                subtask_id, parent_id, child_id, _ = get_subtask_by_childid_from_db(item.id)
                result = update_subtask_in_db_by_api(subtask_id, parent_id, child_id, is_treed=1)
                assert result, "データベースの更新でエラー"
                if result["type"] == "local":
                    self.kanban_board.on_delete_subtask(subtask_id, {"parent_id": parent_id, "child_id": child_id, "is_treed": 1}) 
        elif action == disable_parent_action:
            if item.has_parent_task():
                subtask_id, parent_id, child_id, is_treed = get_subtask_by_childid_from_db(item.id)
                result = delete_subtask_from_db_by_api(subtask_id)
                assert result, "データベースの削除でエラー"
                if result["type"] == "local":
                    self.kanban_board.on_delete_subtask(subtask_id, {"parent_id": parent_id, "child_id": child_id, "is_treed": is_treed}) 
        elif action == priority_middle_action:
            self.set_marked_label(item, label_name="優先度中")
        elif action == priority_low_action:
            self.set_marked_label(item, label_name="優先度低")
        elif action == expand_childtask_action:
            pass
        self.clearFocus()

    def toggle_pin_item(self, item):
        (pin_id, id_, is_pinned) = self.get_pin_data(item)
        if is_pinned:
            self.update_pin_data((pin_id, id_, False))
            item.setText(item.name)
            column = item.treeWidget()
            current_row = column.indexOfTopLevelItem(column.currentItem())
            for row in range(current_row + 1, column.topLevelItemCount()):
                source_item = column.topLevelItem(row)
                source_item_text = source_item.text(0)
                if not source_item_text.startswith("📌"):
                    column.takeTopLevelItem(column.indexOfTopLevelItem(item))
                    column.insertTopLevelItem(column.indexOfTopLevelItem(source_item), item)
                    break
        else:
            self.update_pin_data((pin_id, id_, True))
            item.setText(item.name)
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            self.insertTopLevelItem(0, item)  

    def toggle_mark_item(self, item):
        (mark_id, id_, is_marked) = self.get_mark_data(item)
        self.update_mark_data(item, (mark_id, id_, not is_marked))
        item.setText(item.name)

    def toggle_display_item(self, item):
        (display_id, task_id, disable) = self.get_display_data(item)
        disable = not disable
        self.update_display_data(item, (display_id, task_id, disable))
        item.setHidden(disable)

        subtask = get_subtask_by_childid_from_db(item.id)
        if subtask:
            subtask_id, parent_id, child_id, _ = subtask
            result = update_subtask_in_db_by_api(subtask_id, parent_id, child_id, is_treed=0 if disable else 1)
            assert result, "データベースの更新でエラー"
            if result["type"] == "local":
                self.kanban_board.on_update_subtask(subtask_id, {"parent_id": parent_id, "child_id": task_id, "is_treed": 0 if disable else 1})

    def copy_item(self):
        selected_item = self.currentItem()
        if selected_item:
            self.copied_item = selected_item

    def paste_item(self):
        if hasattr(self, 'copied_item'):
            item = self.copied_item
            self.copy_selected_item(item) 

    def copy_selected_item(self, item):
        old_task_name, old_task_goal, old_task_detail, old_task_deadline, old_task_type, old_status_name, old_waiting_task, old_remind_date, old_remind_input = get_task_from_db(item.id)
        old_task2labels_id = get_task2label_by_taskid_from_db(item.id)
        dialog = TodoDialog(self.kanban_board)
        dialog.task_name.setText(old_task_name)
        dialog.task_goal.setText(old_task_goal)
        dialog.task_detail.setPlainText(old_task_detail)
        if old_task_deadline:
            old_task_deadline_date = old_task_deadline.split(" ")[0]
            old_task_deadline_time = old_task_deadline.split(" ")[1]
            old_task_deadline_hour = int(old_task_deadline_time.split(":")[0])
            old_task_deadline_minutes = int(old_task_deadline_time.split(":")[1])
            dialog.task_deadline_date.setText(old_task_deadline_date)
            dialog.task_deadline_time.setTime(QTime(old_task_deadline_hour, old_task_deadline_minutes))
        dialog.task_type.setCurrentText(old_task_type)
        dialog.status_combo.setCurrentText(old_status_name) 
        dialog.waiting_input.setText(old_waiting_task)
        if old_remind_date:
            old_remind_date = datetime.datetime.strptime(old_remind_date, "%Y/%m/%d %H:%M")
            dialog.reminder.setChecked(True)
            dialog.remind_timer.setDateTime(QDateTime(old_remind_date.date(), old_remind_date.time())) 
            dialog.remind_input.setText(old_remind_input)
        subtask_data = get_subtask_by_parentid_from_db(item.id)
        for (subtask_id, _, child_id, _) in subtask_data:
            child_task_data = get_task_from_db(child_id)
            dialog.add_subtask_table((child_id, *child_task_data), subtask_id)
        subtask = get_subtask_by_childid_from_db(child_id=item.id) 
        if subtask:
            subtask_id, parent_id, _, _ = subtask
            parent_task_item = self.kanban_board.id2item[parent_id]
            dialog.parent_task = QPushButton(parent_task_item.text(0))
            dialog.parent_task.setProperty("parent_task_id", parent_id)
            dialog.parent_task.setProperty("subtask_id", subtask_id)
        dialog.display_labels(old_task2labels_id)
        dialog.post_task()

    def update_selected_item(self, item):
        task_id = item.data(0, Qt.ItemDataRole.UserRole) 
        task_name = item.text()
        _, task_goal, task_detail, task_deadline, task_type, status_name, waiting_task, remind_date, remind_input = get_task_from_db(task_id)
        new_task = (task_id, task_name, task_goal, task_detail, task_deadline, task_type, self.id, waiting_task, remind_date, remind_input)
        result = update_task_in_db_by_api(new_task)
        assert result, "データベースの追加でエラー"
        task_id = result["taskId"]
        if result["type"] == "local":
            self.kanban_board.on_post_task({"taskId": task_id, "name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})

    def move_selected_item(self, item, source_column):
        task_id = item.data(0, Qt.ItemDataRole.UserRole) 
        task_name, task_goal, task_detail, task_deadline_date, task_type, _, waiting_task, remind_date, remind_input = get_task_from_db(task_id)
        new_task = (task_id, task_name, task_goal, task_detail, task_deadline_date, task_type, self.id, waiting_task, remind_date, remind_input)
        result = update_task_in_db_by_api(new_task)
        assert result, "データベースの更新でエラー"
        if result["type"] == "local":
            self.kanban_board.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline_date, "task_type": task_type, "status_name": self.name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})

        if self.name == "DONE":
            self.set_complete_label(task_id)
        elif source_column.name == "DONE":
            self.delete_complete_label(task_id)
        
    def delete_selected_item(self, selected_items):
        for selected_item in selected_items:
            task_id = selected_item.data(0, Qt.ItemDataRole.UserRole) 
            (task_name, task_goal, task_detail, task_deadline, task_type, _, waiting_task, remind_date, remind_input) = get_task_from_db(task_id)
            deleted_task2labels = get_task2label_by_taskid_from_db(task_id)
            deleted_task2labels_id = [ task2label_id for task2label_id, _, _, _, _ in deleted_task2labels]
            deleted_labels_id = [ labels_id for _, labels_id, _, _, _ in deleted_task2labels]
            result = delete_task_from_db_by_api(task_id)
            assert result, "データベースの削除でエラー"
            if result["type"] == "local":
                self.kanban_board.on_delete_task(task_id)
            self.kanban_board.action_history.record({
                'type': 'delete_task',
                'task_id': task_id,
                'task_data': (task_name, task_goal, task_detail, task_deadline, task_type, self.id, waiting_task, remind_date, remind_input),
                'labels_id': deleted_labels_id,
                'task2labels_id': deleted_task2labels_id
            })
        self.clearFocus()

    def set_complete_label(self, task_id):
        complete_date = "Done:" + datetime.datetime.now().strftime("%Y/%m/%d")
        label = get_label_by_name_from_db(complete_date)
        if label:
            label_id, _, _, _ = label
        else:
            label_color = generate_random_color()
            label_id = add_label_to_db(complete_date, label_color)
        add_task2label_in_db(task_id=task_id, label_id=label_id)

    def delete_complete_label(self, task_id):
        task2labels = get_task2label_by_taskid_from_db(task_id)
        for task2label_id, _, label_name, _, _ in task2labels:
            if label_name.startswith("Done:"):
                delete_task2label_from_db(task2label_id)

    def get_pin_data(self, item):
        id_ = item.data(0, Qt.ItemDataRole.UserRole) 
        pin_data = get_pin_by_taskid_from_db(id_)
        return pin_data

    def get_mark_data(self, item):
        id_ = item.data(0, Qt.ItemDataRole.UserRole) 
        mark_data = get_mark_by_taskid_from_db(id_)
        return mark_data

    def get_display_data(self, item):
        task_id = item.data(0, Qt.ItemDataRole.UserRole) 
        display_data = get_display_by_taskid_from_db(task_id)
        return display_data

    def update_pin_data(self, pin_data):
        update_pin_task_to_db(pin_data)

    def update_mark_data(self, item, mark_data):
        (_, _, is_marked) = mark_data
        if is_marked:
            self.set_marked_label(item, label_name="marked")
        else:
            delete_task2label_by_labelname_from_db("marked")
        update_mark_task_to_db(mark_data)

    def update_display_data(self, item, display_data):
        (_, _, is_disable) = display_data
        if is_disable:
            self.set_marked_label(item, label_name="DISABLE")
        else:
            delete_task2label_by_labelname_from_db("DISABLE")
        update_display_task_to_db(display_data)

    def set_marked_label(self, item, label_name):
        label = get_label_by_name_from_db(label_name)
        if label:
            label_id, _, _, _ = label
        else:
            label_color = generate_random_color()
            label_id = add_label_to_db(label_name, label_color)
        task_id = item.data(0, Qt.ItemDataRole.UserRole) 
        add_task2label_in_db(task_id=task_id, label_id=label_id)

    def delete_marked_label(self, item):
        marked_label = "marked"
        delete_task2label_by_labelname_from_db(marked_label)
    
    def count_all_items(self):
        return len(self.get_all_items())

    def get_all_items(self):
        items = []
        for parent_item_idx in range(self.topLevelItemCount()):
            parent_item = self.topLevelItem(parent_item_idx)
            if parent_item and not parent_item.is_disable():
                items.append(parent_item)
                child_items = parent_item.get_child_items()
                items.extend(child_items)
        return items

class TodoBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.items_priority = {}
        self.dialogs = {}
        self.id2dialogs = {}
        self.id2item = {}
        self.action_history = ActionHistory(self)
        self.popup_window = None
        self.window_title = "TODO App"
        self.columns_state_file = f"pkl_files/columns_state-TodoBoard.pkl"
        self.init_ui()
        self.load_columns_state_file()
        self.load_tasks()
        self.setup_shortcuts()
        self.connect_server()

    def init_ui(self):
        self.setWindowIcon(QIcon("icon/start_button.ico"))
        self.setWindowTitle(self.window_title)
        screen_rect = QApplication.primaryScreen().availableGeometry() 
        self.setGeometry(50, 50, screen_rect.width() - 80*2, screen_rect.height() - 80*2 + 50) #self.setGeometry(80, 80, 1350, 700)

        todo_column = TodoColumn("TODO", self)
        doing_column = TodoColumn("DOING", self)
        waiting_column = TodoColumn("WAITING", self)
        done_column = TodoColumn("DONE", self)
        self.columns = {
            "TODO": todo_column,
            "DOING": doing_column,
            "WAITING": waiting_column,
            "DONE": done_column,
        }

        todo_search_box = SearchBox(self)
        doing_search_box = SearchBox(self)
        waiting_search_box = SearchBox(self)
        done_search_box = SearchBox(self)
        self.search_boxes = {
            "TODO": todo_search_box,
            "DOING": doing_search_box,
            "WAITING": waiting_search_box,
            "DONE": done_search_box,
        }

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.create_column("TODO", todo_column, todo_search_box))
        self.layout.addWidget(self.create_column("DOING", doing_column, doing_search_box))
        self.layout.addWidget(self.create_column("WAITING", waiting_column, waiting_search_box))
        self.layout.addWidget(self.create_column("DONE", done_column, done_search_box))
        self.setLayout(self.layout)

    def create_column(self, title, column, search_box):
        column_widget = QWidget()
        layout = QVBoxLayout()

        labels_layout = QHBoxLayout()
        label = QLabel(title)
        labels_layout.addWidget(label)
        labels_layout.addStretch() 
        save_button = QPushButton("保存", self)
        save_button.clicked.connect(self.save_columns_state)
        save_button.setProperty("column", column)
        labels_layout.addWidget(save_button)
        layout.addLayout(labels_layout)

        add_button = QPushButton("+", self)
        add_button.clicked.connect(lambda: self.open_add_task_dialog(column.name))
        layout.addWidget(add_button)

        search_box.search_bar.textChanged.connect(lambda: search_box.filter(column))
        search_box.search_bar.returnPressed.connect(lambda: search_box.filter(column))
        layout.addWidget(search_box)

        layout.addWidget(column)
        column.itemDoubleClicked.connect(self.open_edit_task_dialog)  
        column_widget.setLayout(layout)
        return column_widget

    def load_tasks(self):
        self.load_items()
        for (column_name, search_box) in self.search_boxes.items():
            search_box.count_items(self.columns[column_name])
        self.sort_items_in_columns()
        self.sort_items_in_columns_by_deadline()
        self.sort_pin_items()
        self.set_search_bar()

    def remove_item_in_column(self, task_id):
        item = self.search_item(task_id)
        if item:
            column = item.treeWidget()
            if item.parent():
                item.parent().removeChild(item)
            else:
                column.takeTopLevelItem(column.indexOfTopLevelItem(item))
            self.search_boxes[column.name].count_items(column)
            return column
        return None

    def sort_pin_items(self):
        for column in self.columns.values():
            for idx in range(column.topLevelItemCount()):
                item = column.topLevelItem(idx)
                (_, _, is_pinned) = column.get_pin_data(item)
                if is_pinned:
                    column.takeTopLevelItem(idx)
                    column.insertTopLevelItem(0, item)  

    def insert_item_in_column(self, item):
        target_id = item.data(0, Qt.ItemDataRole.UserRole) 
        column = item.treeWidget()
        for i in range(column.topLevelItemCount()): 
            source_item = column.topLevelItem(i)
            source_id = source_item.data(0, Qt.ItemDataRole.UserRole) 
            source_priority = self.items_priority[source_id]
            target_priority = self.items_priority[target_id]
            if source_priority < target_priority:
                column.takeTopLevelItem(column.indexOfTopLevelItem(item))
                column.insertTopLevelItem(column.indexOfTopLevelItem(source_item), item)
                break
            elif source_priority == target_priority:
                if source_id < target_id:
                    column.takeTopLevelItem(column.indexOfTopLevelItem(item))
                    column.insertTopLevelItem(column.indexOfTopLevelItem(source_item), item)
                    break
        return column

    def load_columns_state_file(self):
        try:
            with open(self.columns_state_file, 'rb') as f:
                self.columns_state = pickle.load(f)
        except:
            self.columns_state = {}
            return

    def set_search_bar(self):
        if not self.columns_state:
            return
        for column_name, state in self.columns_state.items(): 
            column = self.columns[column_name]
            search_box_state = state["search_box"]
            search_word = search_box_state["search_word"]
            if search_word.find("act:next") != -1:
                top_task_id = state["search_box"]["top_task_id"] 
                item = self.search_item(top_task_id)
                if item:
                    column.takeTopLevelItem(column.indexOfTopLevelItem(item))
                    column.insertTopLevelItem(0, item)
            search_box = self.search_boxes[column_name]
            search_box.search_bar.setText(search_word)

    def sort_items_in_columns(self):
        if not self.columns_state:
            return
        for column_name, state in self.columns_state.items(): 
            item_orders = state["item_orders"]
            column = self.columns[column_name]
            for order in range(column.topLevelItemCount()):
                min_task_order = float('-inf')
                target_item = column.topLevelItem(order)
                for i in range(order, column.topLevelItemCount()):
                    source_item = column.topLevelItem(i)
                    source_task_id = source_item.data(0, Qt.ItemDataRole.UserRole) 
                    source_task_order = order - item_orders[source_task_id] if source_task_id in item_orders else float('-inf')
                    if min_task_order <= source_task_order:
                        min_task_order = source_task_order
                        target_item = source_item
                column.takeTopLevelItem(column.indexOfTopLevelItem(target_item))
                column.insertTopLevelItem(order, target_item)

    def sort_items_in_columns_by_deadline(self):
        for column_name in ["TODO", "DOING", "WAITING"]:
            deadlines = {}
            column = self.columns[column_name]
            for idx in range(column.topLevelItemCount()): 
                item = column.topLevelItem(idx)
                task_id = item.data(0, Qt.ItemDataRole.UserRole) 
                deadline = self.get_deadline(item)
                weekdays_diff = self.get_due_date(deadline)
                deadlines[task_id] = weekdays_diff
            for deadline_color in [0, 1, 3]:
                for source_idx in range(column.topLevelItemCount()):
                    source_item = column.topLevelItem(source_idx)
                    source_id = source_item.data(0, Qt.ItemDataRole.UserRole) 
                    for target_idx in range(source_idx, column.topLevelItemCount()):
                        target_item = column.topLevelItem(target_idx)
                        target_id = target_item.data(0, Qt.ItemDataRole.UserRole) 
                        if deadlines[target_id] != deadline_color:
                            continue
                        if deadlines[source_id] > deadlines[target_id]:
                            column.takeTopLevelItem(target_idx)
                            column.insertTopLevelItem(source_idx, target_item)

    def get_due_date(self, deadline_date):
        if deadline_date:
            deadline_date = datetime.datetime.strptime(deadline_date, "%Y/%m/%d %H:%M")
            now = datetime.datetime.now() 
            weekdays_diff = count_weekdays(now, deadline_date)
        else:
            weekdays_diff = float('inf')
        return weekdays_diff

    def get_color(self, deadline_date):
        if not deadline_date:
            return QColor(0, 0, 255)
        weekdays_diff = self.get_due_date(deadline_date)
        if weekdays_diff <= 0:
            color = QColor(0, 0, 0)
        elif weekdays_diff <= 1:
            color = QColor(255, 0, 0)
        elif weekdays_diff <= 3:
            color = QColor(255, 150, 0)
        else:
            color = QColor(0, 0, 255)
        return color

    def search_item(self, target_id):
        return self.id2item[target_id] if target_id in self.id2item else None

    def calc_priority(self, task_id, deadline_date):
        priority = 0
        if deadline_date:
            weekdays_diff = self.get_due_date(deadline_date)
            if weekdays_diff <= 0:
                priority += float('inf')
            elif weekdays_diff <= 1:
                priority += 100
            elif weekdays_diff <= 3:
                priority += 10
        self.items_priority[task_id] = priority

        labels = get_alllabel_by_taskid_from_db(task_id)
        for _, _, _, label_point in labels:
            priority += label_point
        self.items_priority[task_id] = priority
        return priority

    def setup_shortcuts(self):
        undo_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Z), self)
        undo_shortcut.activated.connect(self.action_history.undo)
        redo_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Y), self)
        redo_shortcut.activated.connect(self.action_history.redo)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_M and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            for column in self.columns.values():
                item = column.current_item
                if item:
                    column.show_popup_item(item)
                    self.close()
                    return
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def focus_next_dialog(self, dialog_id):
        del self.dialogs[dialog_id]
        if len(self.dialogs) > 0:
            next_dialog = list(self.dialogs.values())[-1]
            next_dialog.activateWindow()
            next_dialog.raise_()

    def save_columns_state(self):
        try:
            button = self.sender()
            column = button.property("column")
            with open(self.columns_state_file, 'wb') as f:
                item_order = {}
                for idx in range(column.topLevelItemCount()):
                    item = column.topLevelItem(idx)
                    task_id = item.data(0, Qt.ItemDataRole.UserRole)
                    item_order[task_id] = idx
                search_box = {}
                search_box["search_word"] = self.search_boxes[column.name].search_bar.text()
                search_box["top_task_id"] = column.topLevelItem(0).data(0, Qt.ItemDataRole.UserRole) if search_box["search_word"] == "act:next" else -1
                self.columns_state[column.name] = {"search_box": search_box, "item_orders": item_order}
                pickle.dump(self.columns_state, f)
        except Exception as e:
            print(e)
            return

    def connect_server(self):
        self.sio = socketio.Client()
        try:
            self.sio.on('post_task', self.on_post_task)
            self.sio.on('update_task', self.on_update_task)
            self.sio.on('delete_task', self.on_delete_task)
            self.sio.on('post_subtask', self.on_post_subtask)
            self.sio.on('update_subtask', self.on_update_subtask)
            self.sio.on('delete_subtask', self.on_delete_subtask)
            self.sio.connect(f'{SERVER_URL}')
            print(f"Connection Success")
        except Exception as e:
            print(f"Connection failed: {e}")

    def on_post_subtask(self, subtask_id, subtask_data):
        parent_id = subtask_data['parent_id']
        child_id = subtask_data['child_id']
        is_treed = subtask_data['is_treed']
        parent_item = self.id2item[parent_id]
        child_item = self.id2item[child_id]
        if is_treed:
            child_tree = child_item.treeWidget()
            child_tree.takeTopLevelItem(child_tree.indexOfTopLevelItem(child_item))
            child_item.setIcon(0, QIcon())
            parent_item.addChild(child_item)
        else:
            child_item.setIcon(0, QIcon("image/arrow_color11_up.png"))
            self.insert_item_in_column(child_item)

    def on_update_subtask(self, subtask_id, subtask_data): 
        parent_id = subtask_data['parent_id']
        child_id = subtask_data['child_id']
        is_treed = subtask_data['is_treed']
        parent_item = self.id2item[parent_id]
        child_item = self.id2item[child_id]

        if is_treed:
            preparent_tree = child_item.parent()
            if preparent_tree:
                preparent_tree.removeChild(child_item)
            else:
                child_tree = child_item.treeWidget()
                child_tree.takeTopLevelItem(child_tree.indexOfTopLevelItem(child_item))
            parent_item.addChild(child_item)
            child_item.setIcon(0, QIcon())
        else:
            preparent_tree = child_item.parent()
            if preparent_tree:
                preparent_tree.removeChild(child_item)
            self.columns[child_item.get_status()].addTopLevelItem(child_item)
            self.insert_item_in_column(child_item)
            child_item.setIcon(0, QIcon("image/arrow_color11_up.png"))

    def on_delete_subtask(self, subtask_id, subtask_data):
        parent_id = subtask_data['parent_id']
        child_id = subtask_data['child_id']
        child_item = self.id2item[child_id]
        child_item.setIcon(0, QIcon())

    def on_post_task(self, task_data):
        task = (task_data['taskId'], 
                task_data['name'], 
                task_data['goal'], 
                task_data['detail'], 
                task_data['deadline'], 
                task_data['task_type'], 
                task_data['status_name'],
                task_data['waiting_task'], 
                task_data['remind_date'], 
                task_data['remind_input'])
        self.create_item(task)
        column = self.columns[task_data["status_name"]]
        search_box = self.search_boxes[task_data["status_name"]]
        search_box.count_items(column)

    def on_update_task(self, task_id, new_task_data): 
        new_task = (task_id,
                    new_task_data['name'], 
                    new_task_data['goal'], 
                    new_task_data['detail'], 
                    new_task_data['deadline'], 
                    new_task_data['task_type'], 
                    new_task_data['status_name'],
                    new_task_data['waiting_task'],
                    new_task_data['remind_date'],
                    new_task_data['remind_input'])
        item = self.search_item(task_id)
        if item:
            self.update_item(item, new_task)
        column = self.columns[new_task_data["status_name"]]
        search_box = self.search_boxes[new_task_data["status_name"]]
        search_box.count_items(column)

    def on_delete_task(self, deleted_task_id):
        self.remove_item_in_column(deleted_task_id)

    def load_items(self):
        tasks = get_alltask_from_db() 
        for task in tasks:
            task = self.update_repeatly_task(task)
            self.create_item(task)

        all_subtask = get_allsubtask_from_db()
        for (_, parent_id, child_id, is_treed) in all_subtask:
            parent_item = self.id2item[parent_id]
            child_item = self.id2item[child_id]
            if child_item.get_status() == "DONE":
                continue
            if is_treed and not child_item.is_disable():
                child_tree = child_item.treeWidget()
                child_tree.takeTopLevelItem(child_tree.indexOfTopLevelItem(child_item))
                parent_item.addChild(child_item)
            else:
                child_item.setIcon(0, QIcon("image/arrow_color11_up.png"))
            
        disable_tasks = get_disable_tasks_from_db()
        for (_, task_id, _) in disable_tasks:
            item = self.search_item(task_id)
            if item:
                item.setHidden(True)

    def update_repeatly_task(self, task):
        task_id, task_name, task_goal, task_detail, task_deadline_date, task_type, status_name, waiting_task, remind_date, remind_input = task
        if ((task_type != "-" and status_name == "DONE") or (task_type == "daily")) and task_deadline_date and datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M")  <= datetime.datetime.now():
            new_deadline = task_deadline_date
            if task_type == "daily":
                new_deadline = (datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M") + datetime.timedelta(days=1)).strftime("%Y/%m/%d %H:%M") 
            elif task_type == "weekly":
                new_deadline = (datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M") + datetime.timedelta(weeks=1)).strftime("%Y/%m/%d %H:%M") 
            elif task_type == "monthly":
                new_deadline = (datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M") + relativedelta(months=1)).strftime("%Y/%m/%d %H:%M")
            result = update_task_in_db_by_api((task_id, task_name, task_goal, task_detail, new_deadline, task_type, self.columns["TODO"].id, waiting_task, remind_date, remind_input))
            assert result, "データベースの更新でエラー"
            if result["type"] == "local":
                self.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": new_deadline, "task_type": task_type, "status_name": "TODO", "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
            task2labels = get_task2label_by_taskid_from_db(task_id)
            for task2label_id, _, label_name, _, _ in task2labels:
                if label_name.startswith("Done:"):
                    delete_task2label_from_db(task2label_id)
            task = (task_id, task_name, task_goal, task_detail, new_deadline, task_type, "TODO", waiting_task, remind_date, remind_input)
        return task

    def create_item(self, task):
        task_id, task_name, _, _, task_deadline, _, status_name, _, _, _ = task
        item = TodoItem(task_name, task_id)
        self.id2item[task_id] = item
        color = self.get_color(task_deadline)
        item.setForeground(0, color)
        item.setHidden(item.is_disable())
        item.setSizeHint(0, QSize(100, 50))
        self.calc_priority(task_id, task_deadline)
        self.columns[status_name].addTopLevelItem(item)
        self.insert_item_in_column(item)
        return item

    def update_item(self, item, task):
        task_id, task_name, _, _, task_deadline_date, _, status_name, _, _, _ = task
        color = self.get_color(task_deadline_date)
        item.setText(task_name)
        item.setForeground(0, color)
        item.treeWidget().takeTopLevelItem(item.treeWidget().indexOfTopLevelItem(item))
        self.columns[status_name].addTopLevelItem(item)
        self.calc_priority(task_id, task_deadline_date)
        self.insert_item_in_column(item)

    def open_add_task_dialog(self, column_name):
        dialog = TodoDialog(self)
        dialog.status_combo.setCurrentText(column_name) 
        dialog.start_new_editing()
        dialog.show()
        self.dialogs[id(dialog)] = dialog
        return dialog

    def open_edit_task_dialog(self, item):
        item.treeWidget().clearFocus()
        task_id = item.data(0, Qt.ItemDataRole.UserRole) 
        if task_id in self.id2dialogs:
            dialog = self.id2dialogs[task_id]
            if dialog.isHidden():
                dialog.show()
            if dialog.isMinimized():
                dialog.showNormal()
            if not dialog.isActiveWindow():
                dialog.activateWindow()
            dialog.raise_()
            return dialog
        old_task_name, old_task_goal, old_task_detail, old_task_deadline, old_task_type, old_status_name, old_waiting_task, old_remind_date, old_remind_input = get_task_from_db(task_id)
        old_task2labels_id = get_task2label_by_taskid_from_db(task_id)
        dialog = TodoDialog(self, item)
        dialog.task_name.setText(old_task_name)
        dialog.task_goal.setText(old_task_goal)
        dialog.task_detail.setPlainText(old_task_detail)
        if old_task_deadline:
            old_task_deadline_date = old_task_deadline.split(" ")[0]
            old_task_deadline_time = old_task_deadline.split(" ")[1]
            old_task_deadline_hour = int(old_task_deadline_time.split(":")[0])
            old_task_deadline_minutes = int(old_task_deadline_time.split(":")[1])
            dialog.task_deadline_date.setText(old_task_deadline_date)
            dialog.task_deadline_time.setTime(QTime(old_task_deadline_hour, old_task_deadline_minutes))
        dialog.task_type.setCurrentText(old_task_type)
        dialog.status_combo.setCurrentText(old_status_name) 
        dialog.waiting_input.setText(old_waiting_task)
        if old_remind_date:
            old_remind_date = datetime.datetime.strptime(old_remind_date, "%Y/%m/%d %H:%M")
            dialog.reminder.setChecked(True)
            dialog.remind_timer.setDateTime(QDateTime(old_remind_date.date(), old_remind_date.time())) 
            dialog.remind_input.setText(old_remind_input)
        subtask_data = get_subtask_by_parentid_from_db(task_id)
        for (subtask_id, _, child_id, _) in subtask_data:
            child_task_data = get_task_from_db(child_id)
            dialog.add_subtask_table((child_id, *child_task_data), subtask_id)
        subtask = get_subtask_by_childid_from_db(child_id=task_id) 
        if subtask:
            subtask_id, parent_id, _, _ = subtask
            parent_task_item = self.id2item[parent_id]
            dialog.parent_task.setText(parent_task_item.text(0))
            dialog.parent_task.setProperty("parent_task_id", parent_id)
            dialog.parent_task.setProperty("subtask_id", subtask_id)
        dialog.display_labels(old_task2labels_id)
        dialog.start_new_editing()
        dialog.show()
        self.dialogs[id(dialog)] = dialog
        self.id2dialogs[task_id] = dialog
        return dialog

    def get_deadline(self, item):
        task_id = item.data(0, Qt.ItemDataRole.UserRole) 
        _, _, _, deadline, _, _, _, _, _  = get_task_from_db(task_id)
        return deadline

    def check_deadline_task(self):
        pass

    def closeEvent(self, event):
        for column in self.columns.values():
            column.clear_item_detail()
        
        if self.popup_window and self.popup_window.kanban_board:
            self.popup_window.kanban_board = None
        self.sio.disconnect()
        self.action_history.save()
        self.check_deadline_task()
        return super().closeEvent(event)
    
class PopUpTaskDetail(QDialog):
    def __init__(self, parent_detail=None):
        super().__init__()
        self.parent_detail = parent_detail
        self.init_ui()
        self.setup_shortcuts()
    
    def init_ui(self):
        self.setGeometry(150, 100, 500, 550)
        self.setWindowIcon(QIcon("icon/youhishi.ico"))
        self.setWindowTitle("Detail")
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint)
        self.task_detail = TaskDetail(self)
        self.task_detail.textChanged.connect(lambda : self.setWindowTitle("Detail*"))
        self.task_detail.popup_button.setPixmap(self.task_detail.popdown_pixmap)
        self.task_detail.popup_button.mousePressEvent = lambda event: self.accept()
        layout = QVBoxLayout(self)
        layout.addWidget(self.task_detail)
        self.setLayout(layout)

    def setup_shortcuts(self):
        ok_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        ok_shortcut.activated.connect(self.close)
        n_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_N), self)
        n_shortcut.activated.connect(self.close)
        save_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_S), self)
        save_shortcut.activated.connect(self.update)
        popup_item_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_M), self)
        popup_item_shortcut.activated.connect(self.parent_detail.parent().show_popup_item)

    def update(self):
        self.parent_detail.setPlainText(self.task_detail.toPlainText())
        self.parent_detail.parent().database_update()
        self.setWindowTitle("Detail")
    
    def show(self):
        self.setWindowTitle("Detail")
        super().show()

    def closeEvent(self, event):
        self.hide()

class TaskDetail(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_font_size = 10  
        self.button_size = (15, 15)
        self.load_assets()
        self.init_ui()

    def init_ui(self):
        self.setFontPointSize(self.default_font_size)
        self.popup_detail = None
        self.popup_button = self.createButton(self.popup_pixmap)
        self.popup_button.mousePressEvent = lambda event: self.open_edit_dialog()
        self.popup_button.move(self.width() - self.popup_button.width() - 15, 0) 
   
    def load_assets(self):
        popup_pixmap = QPixmap("image/popup.png")
        popdown_pixmap = popup_pixmap.transformed(QTransform().rotate(180))
        self.popup_pixmap = popup_pixmap.scaled(*self.button_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.popdown_pixmap = popdown_pixmap.scaled(*self.button_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def createButton(self, pixmap):
        button = QLabel(self)
        button.setMaximumSize(*self.button_size)
        button.setPixmap(pixmap)
        return button

    def open_edit_dialog(self):
        self.popup_detail = PopUpTaskDetail(self)
        self.popup_detail.task_detail.setPlainText(self.toPlainText())
        self.popup_detail.task_detail.setFontPointSize(self.fontPointSize())
        cursor = self.popup_detail.task_detail.textCursor()
        cursor.setPosition(self.textCursor().position()) 
        self.popup_detail.task_detail.setTextCursor(cursor)
        self.popup_detail.finished.connect(self.close_edit_dialog) 
        self.popup_detail.show()
        self.parent().hide()

    def close_edit_dialog(self):
        self.setPlainText(self.popup_detail.task_detail.toPlainText())
        if not self.parent().is_form_changed():
            self.parent().start_new_editing()
        self.popup_detail = None
        self.parent().show()

    def mousePressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            cursor = self.cursorForPosition(event.pos())
            selected_text = self.document().findBlockByNumber(cursor.blockNumber()).text()
            self.open_link(selected_text)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        selected_text = self.document().findBlockByNumber(cursor.blockNumber()).text()
        self.open_link(selected_text)
        super().mouseDoubleClickEvent(event)

    def open_link(self, selected_text):
        try:
            if re.match(r'^https?://[^\s]+', selected_text):
                webbrowser.open(selected_text, new=1, autoraise=False)
            if re.match(r'^(file://)?\\\\ssfs-2md01\.jp\.sharp\\046-0002-ＳＥＰセンター共有\\.*', selected_text):
                os.startfile(selected_text)
            if re.match(r'^file:///C:/Users/S145053/*', selected_text):
                webbrowser.open(urllib.parse.unquote(selected_text))
            if re.match(r'^C:\\Users\\S145053\\.*', selected_text):
                os.startfile(selected_text)
            if re.match(r'^(X|Y|Z):\\.*', selected_text):
                os.startfile(selected_text)
            if re.match(r'^code (c1x|b91) /(home|work00|work01)/s145053/.*', selected_text):
                selected_texts = selected_text.split(" ")
                app_server = selected_texts[1] 
                app_path = selected_texts[2]
                self.open_vscode(app_server, app_path)
            """
            if re.match(r'^cd /(home|work00|work01)/s145053/.*', selected_text):
                remote_directory = selected_text.split(" ")[1]
                self.open_remote_folder(remote_directory)
            """
            if re.match(r'^onenote:///C:\\Users\\S145053\\*', selected_text):
                os.startfile(selected_text)
        except Exception as error:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"{error}")
            msg_box.exec()

    def open_remote_folder(self, remote_directory):
        command = [
            "powershell",
            "-Command",
            "ssh s145053@c1x",
            f"cd {remote_directory}",
        ]
        subprocess.Popen(command)

    def open_vscode(self, app_server, app_path):
        command = [
            "C:\\Users\\S145053\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
            "--remote",
            f"ssh-remote+{app_server}",
            app_path,
        ]
        subprocess.Popen(command)

    def zoom_in(self):
        current_font_size = self.fontPointSize()
        new_font_size = current_font_size + 1
        self.setFontPointSize(new_font_size)
        self.set_all_text_font_size(new_font_size)

    def zoom_out(self):
        current_font_size = self.fontPointSize()
        new_font_size = max(current_font_size - 1, 1)
        self.setFontPointSize(new_font_size)
        self.set_all_text_font_size(new_font_size)

    def set_all_text_font_size(self, font_size):
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)
        text_format = QTextCharFormat()
        text_format.setFontPointSize(font_size)
        cursor.mergeCharFormat(text_format) 
        cursor.clearSelection() 
    
    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0: 
                self.zoom_in()
            else:
                self.zoom_out()
        super().wheelEvent(event)

    def resizeEvent(self, event):
        self.popup_button.move(self.width() - self.popup_button.width() - 5, 5)
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == 59:
            self.zoom_in()
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            clipboard_text = QApplication.clipboard().text()
            self.insertPlainText(clipboard_text)  
            return
        super().keyPressEvent(event)

class TodoDialog(QDialog):
    def __init__(self, kanban_board, item=None):
        super().__init__()
        self.kanban_board = kanban_board
        self.item = item
        self.task_id = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        self.subtask_id = None
        self.newlabels_id = []
        self.selected_label = None
        self.is_edited = False
        self.button_size = (15, 15)
        self.checkpoint_content = None
        self.title = "Task"
        self.load_assets()
        self.init_ui()
        self.setup_shortcuts()
        self.connect_server()

    def init_ui(self):
        self.setWindowIcon(QIcon("icon/youhishi.ico"))
        self.setWindowTitle(f"{self.title}")
        self.setGeometry(100, 50, 600, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowMinimizeButtonHint)

        self.layouts = QFormLayout()

        task_name_layout = QHBoxLayout()
        self.task_name = QLineEdit(self)
        self.task_name.textChanged.connect(self.on_edit)
        task_name_layout.addWidget(self.task_name)
        popup_item_button = QLabel(self)
        popup_item_button.setPixmap(self.popup_pixmap)
        popup_item_button.setMaximumSize(*self.button_size)
        popup_item_button.mousePressEvent = lambda event: self.show_popup_item()
        task_name_layout.addWidget(popup_item_button)
        self.layouts.addRow("Task:", task_name_layout)

        self.task_goal = QLineEdit(self)
        self.task_goal.textChanged.connect(self.on_edit)
        self.layouts.addRow("Goal:", self.task_goal)

        deadline_layout = QHBoxLayout()
        self.task_deadline_date = QPushButton("", self)
        self.task_deadline_date.setStyleSheet("text-align: left; padding-left: 10px;") 
        self.task_deadline_date.clicked.connect(self.open_calendar)
        self.task_deadline_date.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.task_deadline_time = QTimeEdit()
        self.task_deadline_time.timeChanged.connect(self.on_edit)
        self.task_deadline_time.setTime(QTime(17, 45))
        deadline_layout.addWidget(self.task_deadline_date)
        deadline_layout.addWidget(self.task_deadline_time)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(QLabel("Repeat:", self)) 
        self.task_type = QComboBox(self)
        for index, interval in enumerate(["-", "daily", "weekly", "monthly"]):
            self.task_type.addItem(interval) 
        self.task_type.currentIndexChanged.connect(self.on_edit)
        checkbox_layout.addWidget(self.task_type)
        deadline_layout.addLayout(checkbox_layout)
        self.layouts.addRow("Deadline:", deadline_layout)

        self.task_detail = TaskDetail(self)
        self.task_detail.textChanged.connect(self.on_edit)
        self.layouts.addRow("Detail:", self.task_detail)

        self.status_combo = QComboBox(self)
        all_status = get_allstatus_form_db()
        for index, (status_id, status_name) in enumerate(all_status):
            self.status_combo.addItem(status_name) 
            self.status_combo.setItemData(index, status_id)
        self.status_combo.currentIndexChanged.connect(self.update_visibility)
        self.layouts.addRow("Status:", self.status_combo)

        self.waiting_input_label = QLabel("Waiting for:", self.status_combo)
        self.waiting_input_label.setVisible(False) 
        self.waiting_input = QLineEdit(self)
        self.waiting_input.textChanged.connect(self.on_edit)
        self.waiting_input.setPlaceholderText("What are you waiting for?")
        self.waiting_input.setVisible(False) 
        self.layouts.addRow(self.waiting_input_label, self.waiting_input)


        label_layout = QVBoxLayout()
        label_layout.setSpacing(0)
        self.label_display_area = QScrollArea()
        self.label_display_area.setWidgetResizable(True)
        self.label_display_area.setMaximumHeight(40)
        self.label_display_area.setMinimumWidth(400)
        self.label_display_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.label_widget = QWidget()
        self.label_display_layout = QHBoxLayout(self.label_widget)
        self.label_display_area.setWidget(self.label_widget)
        label_layout.addWidget(self.label_display_area)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Enter keyword...")
        self.label_input.returnPressed.connect(self.add_label)
        label_layout.addWidget(self.label_input)
        self.layouts.addRow("Keywords:", label_layout)


        remind_layout = QHBoxLayout()
        self.reminder = QCheckBox(self)
        self.reminder.setChecked(False)
        self.reminder.stateChanged.connect(self.toggle_remind_timer)
        remind_layout.addWidget(self.reminder) 
        self.remind_timer = QDateTimeEdit(self)
        self.remind_timer.setDateTime(QDateTime(QDateTime.currentDateTime().date(), QTime(17, 45))) 
        self.remind_timer.dateTimeChanged.connect(self.on_edit)
        self.remind_timer.setVisible(False)
        remind_layout.addWidget(self.remind_timer) 
        self.remind_input = QLineEdit(self)
        self.remind_input.textChanged.connect(self.on_edit)
        self.remind_input.setVisible(False) 
        remind_layout.addWidget(self.remind_input) 
        self.layouts.addRow("Reminder:", remind_layout)

        todays_time_seconds = 0
        weekly_time_seconds = 0
        total_time_seconds = 0
        if self.task_id:
            time_data = get_time_by_taskid_from_db(self.task_id)
            today = datetime.datetime.now().date()
            week_start_date = today - datetime.timedelta(weeks=1)
            for _, _, end_date, duration in time_data:
                end_date_dt = datetime.datetime.strptime(end_date, "%Y/%m/%d %H:%M").date()
                if end_date_dt == today:
                    todays_time_seconds += duration 
                if week_start_date <= end_date_dt <= today:
                    weekly_time_seconds += duration
                total_time_seconds += duration
        total_time_label = QLabel(f"{todays_time_seconds//3600:02}:{todays_time_seconds%3600//60:02} / {weekly_time_seconds//3600:02}:{weekly_time_seconds%3600//60:02} / {total_time_seconds//3600:02}:{total_time_seconds%3600//60:02}")
        total_time_label.setStyleSheet("font-size: 13px;")
        self.layouts.addRow("D/W/ALL:", total_time_label)

        self.child_task_id = []
        child_tasks_layout = QVBoxLayout()
        self.subtask_table = QTableWidget()
        self.subtask_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) 
        self.subtask_table.horizontalHeader().setVisible(False) 
        self.subtask_table.verticalHeader().setVisible(False) 
        self.subtask_table.setColumnCount(4)
        self.subtask_table.setColumnWidth(0, 50)  
        self.subtask_table.setColumnWidth(1, 370)
        self.subtask_table.setColumnWidth(3, 0)
        self.subtask_table.doubleClicked.connect(self.open_edit_child_task_dialog)
        child_tasks_area = QScrollArea()
        child_tasks_area.setWidgetResizable(True)
        child_tasks_area.setMaximumHeight(100)
        child_tasks_area.setMinimumWidth(400)
        child_tasks_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        child_tasks_area.setWidget(self.subtask_table)
        child_tasks_layout.addWidget(child_tasks_area)

        child_task_button_layout = QHBoxLayout()
        search_child_task_button = QPushButton(f"検索") 
        search_child_task_button.clicked.connect(self.open_search_child_task_display)
        child_task_button_layout.addWidget(search_child_task_button)
        child_task_button_layout.addStretch() 
        add_child_task_button = QPushButton(f"+") 
        add_child_task_button.clicked.connect(self.open_new_child_task_dialog)
        child_task_button_layout.addWidget(add_child_task_button)
        child_tasks_layout.addLayout(child_task_button_layout)
        self.layouts.addRow("SubTasks:", child_tasks_layout)

        parent_task_layout = QHBoxLayout()
        self.parent_task = QPushButton("")
        self.parent_task.setProperty("parent_task_id", None)
        self.parent_task.setProperty("subtask_id", None)
        self.parent_task.clicked.connect(self.open_edit_parent_task_dialog)
        parent_task_layout.addWidget(self.parent_task)
        change_parent_task_button = QPushButton("変更") 
        change_parent_task_button.clicked.connect(self.open_search_parent_task_display)
        parent_task_layout.addWidget(change_parent_task_button)
        parent_task_layout.setStretch(0, 10) 
        parent_task_layout.setStretch(1, 1) 
        self.layouts.addRow("ParentTask:", parent_task_layout)

        self.dialog_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.dialog_button.accepted.connect(self.handle_accept)
        self.dialog_button.rejected.connect(self.handle_reject)
        self.layouts.addRow(self.dialog_button)

        self.setLayout(self.layouts)

    def connect_server(self):
        self.sio = socketio.Client()
        try:
            self.sio.on('post_subtask', self.on_post_subtask)
            self.sio.on('update_subtask', self.on_update_subtask)
            self.sio.on('delete_subtask', self.on_delete_subtask)
            self.sio.connect(f'{SERVER_URL}')
            print(f"Connection Success")
        except Exception as e:
            print(f"Connection failed: {e}")

    def on_post_subtask(self, subtask_id, subtask_data):
        parent_task_id = subtask_data['parent_id']
        child_task_id = subtask_data['child_id']
        if parent_task_id == self.task_id:
            row = self.search_item_from_subtask_table(child_task_id)
            if not row:
                child_task = get_task_from_db(child_task_id)
                self.add_subtask_table((child_task_id, *child_task), subtask_id)
        else:
            (task_name, _, _, _, _, _, _, _, _) = get_task_from_db(parent_task_id)
            self.parent_task.setText(task_name)
        
    def on_update_subtask(self, subtask_id, subtask_data): 
        if subtask_data['parent_id'] == self.task_id:
            target_subtask_id = subtask_data['child_id']
            row = self.search_item_from_subtask_table(target_subtask_id)
            if row:
                (task_name, _, _, task_deadline, _, _, _, _, _) = get_task_from_db(target_subtask_id)
                self.subtask_table.item(row, 1).setText(task_name)
                self.subtask_table.item(row, 2).setText(f"{task_deadline}" if task_deadline else "")
        else:
            parent_task_id = subtask_data['parent_id']
            (task_name, _, _, _, _, _, _, _, _) = get_task_from_db(parent_task_id)
            self.parent_task.setText(task_name)

    def on_delete_subtask(self, subtask_id, subtask_data):
        if subtask_data['parent_id'] != self.task_id:
            return
        target_id = subtask_data['child_id']
        row = self.search_item_from_subtask_table(target_id)
        if row:
            self.subtask_table.removeRow(row)

    def search_item_from_subtask_table(self, target_id):
        for row in range(self.subtask_table.rowCount()):
            source_id = self.subtask_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if target_id == source_id:
                return row
        return None

    def load_assets(self):
        popup_pixmap = QPixmap("image/popup.png")
        self.popup_pixmap = popup_pixmap.scaled(*self.button_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def toggle_remind_timer(self, state):
        if state == 2: 
            self.remind_timer.setVisible(True)
            self.remind_input.setVisible(True) 
        else:
            self.remind_timer.setVisible(False)
            self.remind_input.setVisible(False) 
        self.on_edit()

    def update_visibility(self):
        self.on_edit()
        if self.status_combo.currentText() == "WAITING": 
            self.waiting_input.setVisible(True)
            self.waiting_input_label.setVisible(True) 
        else:
            self.waiting_input.setVisible(False)
            self.waiting_input_label.setVisible(False) 

    def open_calendar(self):
        dialog = CalendarDialog(self.update_date)
        dialog.exec()  

    def update_date(self, date):
        return self.task_deadline_date.setText(date)
    
    def display_labels(self, task2labels):
        for task2label_id, label_id, label_name, label_color, _ in task2labels:
            label_widget = QLabel(label_name)  
            label_widget.setProperty("task2label_id", task2label_id) 
            label_widget.setProperty("label_id", label_id) 
            label_widget.setProperty("label_color", label_color) 
            label_widget.setStyleSheet(f"""
                background-color: {label_color};
                border-radius: 5px;
            """)
            label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_widget.setMaximumWidth(100)
            label_widget.adjustSize()
            label_widget.mousePressEvent = lambda event, label_widget=label_widget: self.select_label(label_widget)
            self.label_display_layout.addWidget(label_widget)

    def add_label(self):
        label_name = self.label_input.text().strip()
        if label_name == "":
            return
        label = get_label_by_name_from_db(label_name)
        if label:
            label_id, label_name, label_color, _ = label
        else:
            label_color = generate_random_color()
            label_id = add_label_to_db(label_name, label_color)

        label_widget = QLabel(label_name)
        label_widget.setProperty("label_id", label_id) 
        label_widget.setProperty("label_color", label_color) 
        label_widget.setStyleSheet(f"""
            background-color: {label_color};
            border-radius: 5px;
        """)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_widget.setMaximumWidth(100)
        label_widget.adjustSize()
        label_widget.mousePressEvent = lambda event: self.select_label(label_widget)

        self.label_display_layout.addWidget(label_widget)
        self.label_input.clear()
        self.newlabels_id.append(label_id)

        self.on_edit()

    def select_label(self, label_widget):
        if self.selected_label:
            label_color = self.selected_label.property("label_color") 
            self.selected_label.setStyleSheet(f"""
                background-color: {label_color};
                border-radius: 5px;
            """)
        self.selected_label = label_widget
        self.selected_label.setStyleSheet("border: 2px solid blue;")

    def remove_label(self):
        if not self.selected_label:
            return
        label_widget = self.selected_label
        self.label_display_layout.removeWidget(label_widget)
        label_id = label_widget.property("label_id")
        if label_id in self.newlabels_id:
            self.newlabels_id.remove(label_id)
            delete_label_in_db(label_id)
        else:
            task2label_id = label_widget.property("task2label_id")
            self.delete_existing_label(task2label_id)
        label_widget.deleteLater() 
        self.selected_label = None
        self.on_edit()

    def delete_existing_label(self, task2label_id):
        delete_task2label_from_db(task2label_id)

    def database_update(self):
        if self.task_id:
            self.update_task()
        else:
            self.post_task()

    def setup_shortcuts(self):
        self.to_database_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_S), self)
        self.to_database_shortcut.activated.connect(self.database_update)
        ok_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        ok_shortcut.activated.connect(self.handle_accept)
        cancel_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        cancel_shortcut.activated.connect(self.handle_reject)
        popup_taskdetail_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_N), self)
        popup_taskdetail_shortcut.activated.connect(self.task_detail.open_edit_dialog)
        popup_item_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_M), self)
        popup_item_shortcut.activated.connect(self.show_popup_item)

    def handle_accept(self):
        self.add_label()
        self.database_update()
        self.kanban_board.focus_next_dialog(id(self))
        if self.item:
            del self.kanban_board.id2dialogs[self.task_id]
        self.accept()

    def handle_reject(self):
        is_continue = self.is_continue_editing()
        if is_continue:
            return
        self.kanban_board.focus_next_dialog(id(self))
        if self.item:
            del self.kanban_board.id2dialogs[self.task_id]
        self.reject() 

    def on_edit(self):
        if self.is_edited and not self.is_form_changed():
            self.setWindowTitle(f"{self.title}")
            self.is_edited = False
        else:
            self.setWindowTitle(f"{self.title}*")
            self.is_edited = True

    def start_new_editing(self):
        self.checkpoint_content = self.get_form_content()
        self.setWindowTitle(f"{self.title}")
        self.is_edited = False

    def get_form_content(self):
        return {"name": self.task_name.text(),
                "goal": self.task_goal.text(),
                "deadline": self.task_deadline_date.text() + " " + self.task_deadline_time.text() if self.task_deadline_date.text() != "" else None,
                "task_type": self.task_type.currentText(),
                "detail": self.task_detail.toPlainText(),
                "status_id": self.status_combo.itemData(self.status_combo.currentIndex()),
                "waiting_task": self.waiting_input.text(),
                "remind_date": self.remind_timer.text() if self.reminder.isChecked() else None,
                "remind_input": self.remind_input.text() if self.reminder.isChecked() else None,
                "keywords": [label_id for _, label_id, _, _, _ in get_task2label_by_taskid_from_db(task_id=self.task_id)],
                "parent_task_id": self.parent_task.property("parent_task_id") }

    def is_form_changed(self):
        return self.checkpoint_content != self.get_form_content()

    def is_continue_editing(self):
        if self.is_edited:
            if not self.is_form_changed():
                return False
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmation")
            msg_box.setText("編集を破棄しますか？")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            return msg_box.exec() == QMessageBox.StandardButton.No
        return False

    def show_popup_item(self):
        if not self.item:
            return
        self.move_to_doing_column()
        popup_task_window = PopupTaskWindow(self.item)
        if self.kanban_board.popup_window:
            if popup_task_window.task_id == self.kanban_board.popup_window.task_id:
                self.kanban_board.popup_window.raise_()
                return
            else:
                self.kanban_board.popup_window.close()
        popup_task_window.show()
        popup_task_window.task_timer.start_timer()
        self.kanban_board.poup_window = popup_task_window
        self.kanban_board.close()
        self.close()
    
    def add_subtask_table(self, task_data,  subtask_id=None):
        (task_id, task_name, _, _, task_deadline, _, _, _, _, _) = task_data
        font = QFont()
        font.setPointSize(8)
        row_position = self.subtask_table.rowCount()
        self.subtask_table.insertRow(row_position)
        self.subtask_table.setRowHeight(row_position, 30) 

        task_id_item = QTableWidgetItem(f"#{task_id}")
        task_id_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        task_id_item.setFont(font)
        task_id_item.setData(Qt.ItemDataRole.UserRole, task_id)
        self.subtask_table.setItem(row_position, 0, task_id_item)  

        task_name_item = QTableWidgetItem(f"{task_name}")
        task_name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
        task_name_item.setFont(font)
        task_name_item.setData(Qt.ItemDataRole.UserRole, task_name)
        self.subtask_table.setItem(row_position, 1, task_name_item)

        task_deadline_item = QTableWidgetItem(f"{task_deadline}" if task_deadline else "")
        task_deadline_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
        task_deadline_item.setFont(font)
        task_deadline_item.setData(Qt.ItemDataRole.UserRole, task_deadline)
        self.subtask_table.setItem(row_position, 2, task_deadline_item)

        subtask_item = QTableWidgetItem()
        subtask_item.setData(Qt.ItemDataRole.UserRole, subtask_id)
        self.subtask_table.setItem(row_position, 3, subtask_item)

    def open_new_child_task_dialog(self):
        (task_name, _, _, _, _, _, _, _, _) = get_task_from_db(self.task_id)
        dialog = self.kanban_board.open_add_task_dialog(column_name="TODO")
        dialog.parent_task.setText(f"#{self.task_id} {task_name}")
        dialog.parent_task.setProperty("parent_task_id", self.task_id)

    def open_edit_child_task_dialog(self, index):
        row = index.row()
        task_id = self.subtask_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        item = self.kanban_board.id2item[task_id]
        self.kanban_board.open_edit_task_dialog(item)

    def open_search_child_task_display(self):
        all_task_display = AllTaskDisplay()
        if all_task_display.exec() == QDialog.DialogCode.Accepted:
            child_id = all_task_display.selected_task_id
            if self.task_id != child_id:
                self.child_task_id.append(child_id)
                task_data = get_task_from_db(child_id)
                self.add_subtask_table((child_id, *task_data))

    def open_edit_parent_task_dialog(self):
        parent_task_id = self.parent_task.property("parent_task_id")
        if parent_task_id:
            item = self.kanban_board.id2item[parent_task_id]
            self.kanban_board.open_edit_task_dialog(item)

    def open_search_parent_task_display(self):
        all_task_display = AllTaskDisplay()
        if all_task_display.exec() == QDialog.DialogCode.Accepted:
            parent_task_id = all_task_display.selected_task_id
            parent_task_name = all_task_display.selected_task_name
            if parent_task_id:
                if parent_task_id != self.task_id:
                    self.parent_task.setProperty("parent_task_id", parent_task_id)
                    self.parent_task.setText(f"#{parent_task_id} {parent_task_name}")
            else:
                prev_parent_task_id = self.parent_task.property("parent_task_id")
                if prev_parent_task_id:
                    subtask_id = self.parent_task.property("subtask_id")
                    delete_subtask_from_db_by_api(subtask_id)
                    self.parent_task.setProperty("subtask_id", None)
                    self.parent_task.setProperty("parent_task_id", None)

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
        status_name = self.status_combo.currentText()
        status_id = self.status_combo.itemData(self.status_combo.currentIndex())
        waiting_task = self.waiting_input.text()
        has_reminder = self.reminder.isChecked()
        remind_date = self.remind_timer.text() if has_reminder else None
        remind_input = self.remind_input.text() if has_reminder else None
        newlabels_id = self.newlabels_id
        task_data = (task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input)
        result = add_task_to_db_by_api(task_data)
        assert result, "データベースの追加でエラー"
        task_id = result["taskId"]
        if result["type"] == "local":
            self.kanban_board.on_post_task({"taskId": task_id, "name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
        self.task_id = task_id
        for label_id in newlabels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)

        for child_id in self.child_task_id:
            result = add_subtask_to_db_by_api(self.task_id, child_id, is_treed=1)
            assert result, "データベースの追加でエラー"
            subtask_id = result["subtaskId"]
            if result["type"] == "local":
                self.on_post_subtask(subtask_id, {"parent_id": self.task_id, "child_id": child_id, "is_treed": 1})

        parent_id = self.parent_task.property("parent_task_id")
        if parent_id:
            result = add_subtask_to_db_by_api(parent_id, self.task_id)
            assert result, "データベースの追加でエラー"
            subtask_id = result["subtaskId"]
            self.parent_task.setProperty("subtask_id", subtask_id)
            if result["type"] == "local":
                self.kanban_board.on_post_subtask(subtask_id, {"parent_id": parent_id, "child_id": task_id, "is_treed": 1})

        if status_name == "DONE":
            complete_date = "Done:" + datetime.datetime.now().strftime("%Y/%m/%d")
            label = get_label_by_name_from_db(complete_date)
            if label:
                label_id, _, _, _ = label
            else:
                label_color = generate_random_color()
                label_id = add_label_to_db(complete_date, label_color)
            add_task2label_in_db(task_id=task_id, label_id=label_id)
        task2labels = get_task2label_by_taskid_from_db(task_id)
        task2labels_id = [task2label_id for task2label_id, _, _, _, _ in task2labels]
        labels_id = [label_id for _, label_id, _, _, _ in task2labels]
        self.kanban_board.action_history.record({
            'type': 'add_task',
            'task_id': task_id,
            'task_data': task_data,
            'labels_id': labels_id,
            'task2labels_id': task2labels_id,
        })
        self.start_new_editing()

    def update_task(self): 
        old_task_data = (
            self.checkpoint_content["name"], 
            self.checkpoint_content["goal"],
            self.checkpoint_content["detail"],
            self.checkpoint_content["deadline"],
            self.checkpoint_content["task_type"],
            self.checkpoint_content["status_id"],
            self.checkpoint_content["waiting_task"],
            self.checkpoint_content["remind_date"],
            self.checkpoint_content["remind_input"],
            self.checkpoint_content["parent_task_id"],
        )
        old_task_labels_id = self.checkpoint_content["keywords"]

        task_id = self.task_id
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
        status_name = self.status_combo.currentText()
        waiting_task = self.waiting_input.text()
        remind_date = self.remind_timer.text() if self.reminder.isChecked() else None
        remind_input = self.remind_input.text() if self.reminder.isChecked() else None
        new_task_data = (task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input)
        result = update_task_in_db_by_api((task_id, *new_task_data))
        assert result, "データベースの更新でエラー"
        if result["type"] == "local":
            self.kanban_board.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
        for label_id in self.newlabels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)

        for child_id in self.child_task_id:
            result = add_subtask_to_db_by_api(self.task_id, child_id, is_treed=1)
            assert result, "データベースの追加でエラー"
            subtask_id = result["subtaskId"]
            if result["type"] == "local":
                self.on_post_subtask(subtask_id, {"parent_id": self.task_id, "child_id": child_id, "is_treed": 1})

        parent_id = self.parent_task.property("parent_task_id")
        if parent_id:
            subtask_id = self.parent_task.property("subtask_id")
            if subtask_id:
                _, _, _, is_treed = get_subtask_from_db(subtask_id)
                result = update_subtask_in_db_by_api(subtask_id, parent_id, task_id, is_treed=is_treed)
                assert result, "データベースの更新でエラー"
                if result["type"] == "local":
                    self.kanban_board.on_update_subtask(subtask_id, {"parent_id": parent_id, "child_id": task_id, "is_treed": is_treed})
            else:
                result = add_subtask_to_db_by_api(parent_id, self.task_id)
                assert result, "データベースの追加でエラー"
                subtask_id = result["subtaskId"]
                self.parent_task.setProperty("subtask_id", subtask_id)
                if result["type"] == "local":
                    self.kanban_board.on_post_subtask(subtask_id, {"parent_id": parent_id, "child_id": task_id, "is_treed": 1})

        new_task2labels = get_task2label_by_taskid_from_db(self.task_id)
        new_task2labels_id = [task2label_id for task2label_id, _, _, _, _ in new_task2labels]
        self.kanban_board.action_history.record({
            'type': 'edit_task',
            'task_id': task_id,
            'old_task_data': old_task_data, 
            'old_task_labels_id': old_task_labels_id,
            'new_task_data': new_task_data,
            'new_task_newlabels_id': self.newlabels_id,
            'new_task2labels_id': new_task2labels_id,
        }) 
        self.start_new_editing()

    def move_to_doing_column(self):
        if  self.status_combo.currentText() != "DOING":
            tmp_editing_status = (self.windowTitle(), self.is_edited)
            self.status_combo.setCurrentText("DOING")
            window_title, self.is_edited = tmp_editing_status
            self.setWindowTitle(window_title)
            task_data = (
                self.checkpoint_content["name"], 
                self.checkpoint_content["goal"],
                self.checkpoint_content["detail"],
                self.checkpoint_content["deadline"],
                self.checkpoint_content["task_type"],
                self.status_combo.itemData(self.status_combo.currentIndex()),
                self.checkpoint_content["waiting_task"],
                self.checkpoint_content["remind_date"],
                self.checkpoint_content["remind_input"],
            )
            result = update_task_in_db_by_api((self.task_id, *task_data))
            assert result, "データベースの更新でエラー"
            if result["type"] == "local":
                self.kanban_board.on_update_task(self.task_id, {"name": self.checkpoint_content["name"], "goal": self.checkpoint_content["goal"], "detail": self.checkpoint_content["detail"], "deadline": self.checkpoint_content["deadline"], "task_type": self.checkpoint_content["task_type"], "status_name": "TODO", "waiting_task": self.checkpoint_content["waiting_task"], "remind_date": self.checkpoint_content["remind_date"], "remind_input": self.checkpoint_content["remind_input"]})
            self.checkpoint_content["status_id"] = self.status_combo.itemData(self.status_combo.currentIndex())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            return
        elif event.key() == Qt.Key.Key_Delete:
            if self.selected_label:
                self.remove_label() 
            selected_items = self.subtask_table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                subtask_id = self.subtask_table.item(row, 3).data(Qt.ItemDataRole.UserRole)
                if subtask_id:
                    _, parent_id, child_id, is_treed = get_subtask_from_db(subtask_id)
                    result = delete_subtask_from_db_by_api(subtask_id)
                    assert result, "データベースの削除でエラー"
                    if result["type"] == "local":
                        self.on_delete_subtask(subtask_id, {"parent_id": parent_id, "child_id": child_id, "is_treed": is_treed}) 
                else:
                    self.subtask_table.removeRow(row)
        elif event.key() == Qt.Key.Key_Escape:
            if self.selected_label:
                label_color = self.selected_label.property("label_color") 
                self.selected_label.setStyleSheet(f"""
                    background-color: {label_color};
                    border-radius: 5px;
                """)
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        is_continue = self.is_continue_editing()
        if is_continue:
            return event.ignore() 
        self.kanban_board.focus_next_dialog(id(self))
        if self.item:
            del self.kanban_board.id2dialogs[self.task_id]
        return event.accept()

    def show(self):
        if self.task_detail.popup_detail:
            dialog = self.task_detail.popup_detail
            if dialog.isHidden():
                dialog.show()
            if dialog.isMinimized():
                dialog.showNormal()
            dialog.activateWindow()
            dialog.setFocus()
            dialog.raise_()
        else:
            super().show()

class CalendarDialog(QDialog):
    def __init__(self, on_date_selected):
        super().__init__()
        self.setWindowIcon(QIcon("image/calender.png"))
        self.on_date_selected = on_date_selected
        self.init_ui()
    
    def init_ui(self):
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.select_date)

        layout = QVBoxLayout()
        layout.addWidget(self.calendar)
        self.setLayout(layout)
        self.setWindowTitle("Calendar")

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    def select_date(self, date):
        self.on_date_selected(f"{date.toString('yyyy/MM/dd')}")
        self.close()

    def reset_deadline(self):
        self.on_date_selected("")
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.reset_deadline() 
        super().keyPressEvent(event)

class ActionHistory:
    def __init__(self, kanban_board):
        self.kanban_board = kanban_board
        self.undo_stack = []
        self.redo_stack = []
        if not os.path.exists("pkl_files"):
            os.makedirs("pkl_files")
        self.undo_stack_file = 'pkl_files/undo_stack.pkl'
        self.redo_stack_file = 'pkl_files/redo_stack.pkl'
        self.load_undo_stack()
        self.load_redo_stack()

    def load_undo_stack(self):
        if os.path.exists(self.undo_stack_file):
            with open(self.undo_stack_file, 'rb') as f:
                try:
                    self.undo_stack = pickle.load(f)
                except (pickle.UnpicklingError, EOFError):
                    self.undo_stack = []

    def load_redo_stack(self):
        if os.path.exists(self.redo_stack_file):
            with open(self.redo_stack_file, 'rb') as f:
                try:
                    self.redo_stack = pickle.load(f)
                except (pickle.UnpicklingError, EOFError):
                    self.redo_stack = []

    def record(self, action):
        self.undo_stack.append(action)
        self.redo_stack = []

    def undo(self):
        if len(self.undo_stack) == 0:
            return
        last_action = self.undo_stack.pop()
        if last_action['type'] == 'add_task':
            self.delete_task(last_action)
        elif last_action['type'] == 'delete_task':
            self.add_task(last_action)
        elif last_action['type'] == 'edit_task':
            self.restore_task(last_action)
        elif last_action['type'] == 'restore_task':
            self.update_task(last_action)
        elif last_action['type'] == 'move_task':
            self.move_back_task(last_action)
        self.redo_stack.append(last_action)

    def redo(self):
        if len(self.redo_stack) == 0:
            return
        last_action = self.redo_stack.pop()
        if last_action['type'] == 'add_task':
            self.add_task(last_action)
        elif last_action['type'] == 'delete_task':
            self.delete_task(last_action)
        elif last_action['type'] == 'edit_task':
            self.update_task(last_action)
        elif last_action['type'] == 'restore_task':
            self.restore_task(last_action)
        elif last_action['type'] == 'move_task':
            self.move_task(last_action)
        self.undo_stack.append(last_action) 

    def add_task(self, last_action):
        task_data = last_action['task_data']
        labels_id = last_action["labels_id"]
        result = add_task_to_db_by_api(task_data)
        assert result, "データベースの追加でエラー"
        task_id = result["taskId"]
        if result["type"] == "local":
            task_name, task_goal, task_detail, task_deadline, task_type, status_name, waiting_task ,remind_date, remind_input = task_data
            self.kanban_board.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
        task2labels_id = []
        for label_id in labels_id:
            task2label_id = add_task2label_in_db(task_id=task_id, label_id=label_id)
            task2labels_id.append(task2label_id)
        last_action["task_id"] = task_id 
        last_action["task2labels_id"] = task2labels_id

    def delete_task(self, last_action):
        task_id = last_action["task_id"]
        task2labels_id = last_action["task2labels_id"]
        result = delete_task_from_db_by_api(task_id)
        assert result, "データベースの削除でエラー"
        if result["type"] == "local":
            self.kanban_board.on_delete_task(task_id)
        for task2label_id in task2labels_id:
            delete_task2label_from_db(task2label_id)

    def update_task(self, last_action):
        task_id = last_action['task_id']
        new_task_data = last_action['new_task_data']
        new_task_newlabels_id = last_action['new_task_newlabels_id']
        result = update_task_in_db_by_api((task_id, *new_task_data))
        assert result, "データベースの更新でエラー"
        if result["type"] == "local":
            task_name, task_goal, task_detail, task_deadline, task_type, status_name, waiting_task ,remind_date, remind_input = new_task_data
            self.kanban_board.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
        task2labels_id = [] 
        for label_id in new_task_newlabels_id:
            task2label_id = add_task2label_in_db(task_id=task_id, label_id=label_id)
            task2labels_id.append(task2label_id)
        last_action['new_task2labels_id'] = task2labels_id

    def restore_task(self, last_action):
        task_id = last_action['task_id']
        old_task_data = last_action['old_task_data']
        old_task_labels_id = last_action['old_task_labels_id']
        new_task_newlabels_id = last_action['new_task_newlabels_id']
        new_task2labels_id = last_action['new_task2labels_id']
        for old_task_label_id in old_task_labels_id:
            if old_task_label_id not in new_task_newlabels_id:
                add_task2label_in_db(task_id=task_id, label_id=old_task_label_id)
        for task2label_id in new_task2labels_id:
            delete_task2label_from_db(task2label_id)
        result = update_task_in_db_by_api((task_id, *old_task_data))
        assert result, "データベースの更新でエラー"
        if result["type"] == "local":
            task_name, task_goal, task_detail, task_deadline, task_type, status_name, waiting_task ,remind_date, remind_input = old_task_data
            self.kanban_board.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})

    def move_back_task(self, last_action):
        task_id = last_action["task_id"]
        source_status_id = last_action['source_status_id']
        task_name, task_goal, task_detail, task_deadline, task_type, _, waiting_task, remind_date, remind_input = get_task_from_db(task_id)
        task_data = (task_name, task_goal, task_detail, task_deadline, task_type, source_status_id, waiting_task, remind_date, remind_input)
        result = update_task_in_db_by_api((task_id, *task_data))
        assert result, "データベースの更新でエラー"
        if result["type"] == "local":
            self.kanban_board.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})

    def move_task(self, last_action):
        task_id = last_action["task_id"]
        target_status_id = last_action['target_status_id']

        task_name, task_goal, task_detail, task_deadline, task_type, _, waiting_task, remind_date, remind_input = get_task_from_db(task_id)
        task_data = (task_name, task_goal, task_detail, task_deadline, task_type, target_status_id, waiting_task, remind_date, remind_input)
        result = update_task_in_db_by_api((task_id, *task_data))
        assert result, "データベースの更新でエラー"
        if result["type"] == "local":
            self.kanban_board.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})

    def save_undo_stack(self):
        with open(self.undo_stack_file, 'wb') as f:
            pickle.dump(self.undo_stack, f)

    def save_redo_stack(self):
        with open(self.redo_stack_file, 'wb') as f:
            pickle.dump(self.redo_stack, f)

    def save(self):
        self.save_undo_stack()
        self.save_redo_stack()

class TaskSearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setPlaceholderText("Search...")

    def _filter_word(self, word, table):
        is_exclude = word.startswith('!')
        word = word[1:] if is_exclude else word
        for row in range(table.rowCount()):
            is_hidden = table.isRowHidden(row)
            if is_hidden:
                continue
            table.setRowHidden(row, not(is_exclude ^ (table.item(row, 2).text().find(word) != -1)))

    def _filter_tag(self, tag, table):
        is_exclude = tag.startswith('!')
        search_label = tag[1:] if is_exclude else tag
        for row in range(table.rowCount()):
            is_hidden = table.isRowHidden(row)
            if is_hidden:
                continue
            task_id = table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            labels = get_alllabel_by_taskid_from_db(task_id=task_id)
            table.setRowHidden(row, not(is_exclude ^ any([label_name.find(search_label) != -1 for _, label_name, _, _ in labels])))

    def filter(self, table):
        for row in range(table.rowCount()):
            table.setRowHidden(row, False)

        search_text = self.text()
        if search_text == "":
            return
        splitted_search_texts = search_text.replace("　", " ").split(' ')
        is_tag = False
        tags = []
        words = []
        for splitted_search_text in splitted_search_texts:
            if splitted_search_text == "tag:":
                is_tag = True
                continue
            if is_tag is False and splitted_search_text.startswith('tag:'):
                tags.append(splitted_search_text[4:])
                continue
            if is_tag:
                tags.append(splitted_search_text)
                is_tag = False
            else:
                words.append(splitted_search_text)

        for tag in tags:
            self._filter_tag(tag, table)
        for word in words:
            self._filter_word(word, table)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.hasFocus():
                self.clearFocus()
                return
        return super().keyPressEvent(event)
    
class AllTaskDisplay(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_task_id = None
        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(QIcon("icon/youhishi.ico"))
        self.setWindowTitle(f"All Tasks")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.setGeometry(200, 100, 500, 550)

        layouts = QVBoxLayout()

        search_box = TaskSearchBox(self)
        search_box.textChanged.connect(lambda: search_box.filter(table=self.table))
        search_box.returnPressed.connect(lambda: search_box.filter(table=self.table))
        layouts.addWidget(search_box)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) 
        self.table.horizontalHeader().setVisible(False) 
        self.table.verticalHeader().setVisible(False) 
        self.table.setColumnCount(3)
        self.table.setColumnWidth(0, 30)  
        self.table.setColumnWidth(1, 30)  
        self.table.setColumnWidth(2, 370)
        all_task_data = get_alltask_from_db()
        for task in all_task_data:
            self.add_task_table(task)
        self.table.cellClicked.connect(self.on_row_clicked)
        layouts.addWidget(self.table)

        self.setLayout(layouts)

    def setup_shortcut(self):
        close_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        close_shortcut.activated.connect(self.close)

    def add_task_table(self, task):
        (task_id, task_name, _, _, _, _, _, _, _, _) = task
        font = QFont()
        font.setPointSize(9)
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)  
        self.table.setRowHeight(row_position, 30) 

        select_button = QPushButton("選択") 
        select_button.clicked.connect(lambda: self.select_task(task_id, task_name))
        self.table.setCellWidget(row_position, 0, select_button)  

        task_id_item = QTableWidgetItem(f"{task_id}")
        task_id_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        task_id_item.setFont(font)
        task_id_item.setData(Qt.ItemDataRole.UserRole, task_id)
        self.table.setItem(row_position, 1, task_id_item)  

        task_name_item = QTableWidgetItem(f"{task_name}")
        task_name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
        task_name_item.setFont(font)
        task_name_item.setData(Qt.ItemDataRole.UserRole, task_name)
        self.table.setItem(row_position, 2, task_name_item)

    def on_row_clicked(self, row, column):
        task_id = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        task_name = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole)
        self.select_task(task_id, task_name)

    def select_task(self, task_id, task_name=None):
        self.selected_task_id = task_id
        self.selected_task_name = task_name
        self.accept() 

    def keyPressEvent(self, event: QMouseEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.select_task(None)
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    todo_board = TodoBoard()
    todo_board.show()
    sys.exit(app.exec())
