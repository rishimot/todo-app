import os
import sys
import pickle
import datetime
import socketio
import webbrowser
import re
from utils import (
    get_allstatus_form_db,
    get_status_by_name_from_db,
    get_task_from_db,
    update_task_in_db,
    delete_task_from_db,
    get_alltask_from_db,
    get_label_by_name_from_db,
    get_task2label_from_db,
    get_label2task_from_db,
    generate_random_color,
    add_label_to_db,
    delete_label_in_db,
    delete_task2label_from_db,
    add_task2label_in_db,
    add_task_to_db,
    add_time_to_db,
    enable_focus_mode,
    disable_focus_mode,
    count_weekdays,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QUrl,
    QTimer,
    QEvent,
    QPoint,
    QMimeData,
)
from PyQt6.QtGui import(
    QColor,
    QIcon,
    QKeySequence,
    QShortcut,
    QMouseEvent,
    QDesktopServices,
    QPixmap,
    QCursor,
    QTextCursor,
) 
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QLabel,
    QDialog,
    QComboBox,
    QFormLayout,
    QTextEdit,
    QDialogButtonBox,
    QListWidgetItem,
    QCalendarWidget,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QMenu,
    QCheckBox,
)

sio = socketio.Client()

class DigitalTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_id = self.parent().item.data(Qt.ItemDataRole.UserRole)
        self.timer = QTimer()
        self.setting_time = 30
        self.duration_time = 0 
        self.time_elapsed = self.setting_time * 60
        self.button_size = (25, 25)
        self.start_time = None
        self.end_time = None
        self.time_format = "%Y/%m/%d/%H:%M:%S"

        self.load_assets()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel(f'{self.setting_time}:00', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedHeight(30)
        self.label.mousePressEvent = lambda event: self.start_timer()
        layout.addWidget(self.label)

        self.start_button = self.createButton(self.saisei_pixmap, lambda event: self.start_timer())
        layout.addWidget(self.start_button)
        self.setLayout(layout)

        self.timer.timeout.connect(self.update_timer)

        menu = QMenu()
        exit_action = menu.addAction("終了")
        exit_action.triggered.connect(self.close)
        self.tray_icon = QSystemTrayIcon(QIcon("icon/dokuro_switch.ico"), self)
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

    def start_timer(self):
        if self.start_time is None:
            enable_focus_mode()
            self.start_time = datetime.datetime.now().strftime(self.time_format)
        self.timer.start(1000) 
        self.start_button.setPixmap(self.teishi_pixmap)
        self.start_button.mousePressEvent = lambda event: self.stop_timer()
        self.label.mousePressEvent = lambda event: self.pause_timer()

    def pause_timer(self):
        disable_focus_mode()
        self.start_button.setPixmap(self.saisei_pixmap)
        self.start_button.mousePressEvent = lambda event: self.start_timer()
        self.label.mousePressEvent = lambda event: self.start_timer()
        self.timer.stop()

    def update_timer(self):
        self.duration_time += 1 
        self.time_elapsed -= 1
        minutes = (self.time_elapsed % 3600) // 60
        seconds = self.time_elapsed % 60
        self.label.setText(f'{minutes:02}:{seconds:02}')
        if self.time_elapsed <= 0:
            self.stop_timer()

    def stop_timer(self):
        disable_focus_mode()
        self.start_button.setPixmap(self.saisei_pixmap)
        self.start_button.mousePressEvent = lambda event: self.start_timer()
        self.timer.stop()
        if self.duration_time >= 1:
            end_time = datetime.datetime.now().strftime(self.time_format)
            add_time_to_db((self.start_time, end_time, self.duration_time, self.task_id))
            self.tray_icon.showMessage(
                "Notification",
                f"{self.duration_time // 60}分{self.duration_time % 60}秒が経ちました",
                QIcon("image/gabyou_pinned_plastic_red.png"),
                1000
            )
            self.duration_time = 0
            self.time_elapsed = self.setting_time * 60
            self.label.setText(f'{self.setting_time:02}:00')

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
    def __init__(self, text, item, kanban_board=None):
        super().__init__()
        self.setWindowIcon(QIcon("icon/dokuro_switch.ico"))
        self.setWindowTitle("Popup Task Window")
        self.kanban_board = kanban_board
        self.text = text[text.find("#") + 1:].strip().split(' ', 1)[1]
        self.start_pos = None
        self.item = item
        self.is_pinned = True
        self.pin_only = False
        self.pin_size = (15, 15)
        self.pinwidget_size = (37, 37)
        self.load_assets()
        self.init_ui()

    def load_assets(self):
        pin_red_pixmap = QPixmap("image/gabyou_pinned_plastic_red.png")
        pin_white_pixmap = QPixmap("image/gabyou_pinned_plastic_white.png")
        self.pin_red_pixmap = pin_red_pixmap.scaled(*self.pin_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.pin_white_pixmap = pin_white_pixmap.scaled(*self.pin_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def init_ui(self):
        self.setGeometry(0, 0, 200, 40)

        layout = QHBoxLayout()
        self.pin = QLabel(self)
        self.pin.setPixmap(self.pin_red_pixmap if self.is_pinned else self.pin_white_pixmap)
        self.pin.setFixedSize(*self.pin_size)
        self.pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin.mousePressEvent = self.pin_clicked
        layout.addWidget(self.pin)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.task_layout = QVBoxLayout()
        self.task_name = QLabel(self.text, self)
        self.task_layout.addWidget(self.task_name)

        self.target = TargetWidget(self) 
        self.task_layout.addWidget(self.target)
        main_layout.addLayout(self.task_layout)

        timer_layout = QVBoxLayout()
        self.task_timer = DigitalTimer(self)
        timer_layout.addWidget(self.task_timer)
        main_layout.addLayout(timer_layout)

        self.main_widget = QWidget()
        self.main_widget.setLayout(main_layout)
        layout.addWidget(self.main_widget)
        self.setLayout(layout)

        window_flags = self.windowFlags() | Qt.WindowType.FramelessWindowHint
        if self.is_pinned:
            window_flags |= Qt.WindowType.WindowStaysOnTopHint 
        self.setWindowFlags(window_flags)

        self.adjustSize()
        self.original_size = (self.width(), self.height())
        self.small_mode()

    def keyPressEvent(self, event: QMouseEvent):
        if event.key() == Qt.Key.Key_Escape:
            return
        if event.key() == Qt.Key.Key_M and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.close()
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            parent_rect = self.geometry()
            mouse_pos = QCursor.pos()
            if not parent_rect.contains(mouse_pos):
                self.small_mode()
        super().keyPressEvent(event)

    def pin_clicked(self, event):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.pin.setPixmap(self.pin_red_pixmap)
            self.unlock_pinonly_mode()
        else:
            self.pin.setPixmap(self.pin_white_pixmap)

        self.show()

    def mouseDoubleClickEvent(self, event):
        self.kanban_board.open_edit_task_dialog(self.item)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()  
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
        if self.is_pinned:
            self.enlarge_mode()
        else:
            self.pinonly_mode()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if (not self.target.hasFocus()) and (not self.pin_only):
            self.small_mode()
        super().leaveEvent(event)

    def enlarge_mode(self):
        self.main_widget.show() 
        self.task_name.setText(self.text)
        self.target.show()
        self.task_timer.show()
        self.setFixedHeight(self.original_size[1])
        self.adjustSize()

    def small_mode(self):
        if self.target.text() != "":
            self.task_name.setText(self.target.text())
        self.target.hide()
        self.task_timer.hide()
        self.setFixedHeight(35)
        self.adjustSize()

    def pinonly_mode(self):
        self.pin_only = True
        self.main_widget.hide() 
        self.setFixedSize(*self.pinwidget_size)
        self.adjustSize()
        QTimer.singleShot(3000, self.unlock_pinonly_mode) 

    def unlock_pinonly_mode(self):
        self.pin_only = False
        self.main_widget.show() 
        self.setFixedSize(*self.original_size)
        self.adjustSize()
        self.small_mode()

class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setPlaceholderText("Search...")

    def _filter_word(self, word, items):
        is_exclude = word.startswith('!')
        word = word[1:] if is_exclude else word
        for item in items:
            if item.isHidden():
                continue
            item.setHidden(not(is_exclude ^ (item.text().find(word) != -1)))

    def _filter_tag(self, tag, items):
        is_exclude = tag.startswith('!')
        search_label = tag[1:] if is_exclude else tag
        label2task = get_label2task_from_db(search_label)
        task_ids = [task_id for _, task_id, _ in label2task]
        for item in items:
            if item.isHidden():
                continue
            task_id = item.data(Qt.ItemDataRole.UserRole) 
            item.setHidden(not(is_exclude ^ (task_id in task_ids)))

    def filter_list(self, column):
        items = []
        for index in range(column.count()):
            item = column.item(index)
            item.setHidden(False)
            items.append(item)

        search_text = self.text()
        if search_text == "":
            return
        splitted_search_texts = search_text.split(' ')
        is_tag = False
        for splitted_search_text in splitted_search_texts:
            if splitted_search_text == "tag:":
                is_tag = True
                continue
            if is_tag is False and splitted_search_text.startswith('tag:'):
                self._filter_tag(splitted_search_text[4:], items)
                continue

            if is_tag:
                self._filter_tag(splitted_search_text, items)
                is_tag = False
            else:
                self._filter_word(splitted_search_text, items)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.hasFocus():
                self.clearFocus()
        super().keyPressEvent(event)
    
class KanbanItem(QListWidgetItem):
    def __init__(self, text, task_id):
        super().__init__(text)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_detail)
        self.detail_label = None
        self.task_id = task_id
        self.setData(Qt.ItemDataRole.UserRole, task_id) 
    
    def show_detail(self):
        if self.detail_label is None:
            task_name, _, _, deadline, _, status_name, waiting_task = get_task_from_db(self.task_id)
            content = f"{task_name}"
            if deadline:
                content += f"\n~{deadline}"
            if status_name == "WAITING":
                content += f"\nI'm waiting for... {waiting_task}"
            self.detail_label = QLabel(content)
            self.detail_label.setWindowFlag(Qt.WindowType.ToolTip)
            self.detail_label.move(QCursor.pos() + QPoint(10, 10))
            self.detail_label.show()
    
    def clear_detail(self):
        if self.detail_label is not None:
            self.detail_label.close()
            self.detail_label = None

class KanbanColumn(QListWidget):
    def __init__(self, title, parent=None):
        super().__init__()
        self.parent = parent
        self.id, self.name = get_status_by_name_from_db(title)
        self.current_item = None
        self.init_ui()
        self.setMouseTracking(True)

    def init_ui(self):
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.setStyleSheet("""
            QListWidget::item {
                border: 2px solid black;  /* 縁取りの色と太さ */
                border-radius: 5px;       /* 角を丸くする */
                padding: 10px;            /* 内側の余白 */
            }
            QListWidget::item:selected {
                background-color: lightblue;  /* 選択時の背景色 */
            }
        """)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.source() == self:
            drop_item = event.source().itemAt(event.position().toPoint())
            drop_row = self.row(drop_item) if drop_item else self.count() 
            item = self.currentItem()
            self.takeItem(self.row(item))
            self.insertItem(drop_row, item)

            self.parent.action_history.record({
                'type': 'move_task',
                'source_column': self,
                'target_column': self,
                'task_item': item,
                'original_row': self.row(item),
                'new_row': drop_row
            })

            event.accept()
            self.clearSelection()
            self.clearFocus()
        else:
            item = event.source().currentItem()
            event.source().takeItem(event.source().row(item))
            drop_item = self.itemAt(event.position().toPoint())
            drop_row = self.row(drop_item) if drop_item else self.count() 
            self.insertItem(drop_row, item)

            task_id = item.data(Qt.ItemDataRole.UserRole) 
            task_name, task_goal, task_detail, task_deadline, is_weekly_task, _, waiting_task = get_task_from_db(task_id)
            task = (task_id, task_name, task_goal, task_detail, task_deadline, is_weekly_task, self.id, waiting_task)
            update_task_in_db(task)
            if self.name == "DONE":
                complete_date = "Done:" + datetime.datetime.now().strftime("%Y/%m/%d")
                label = get_label_by_name_from_db(complete_date)
                if label:
                    label_id, _, _, _ = label
                else:
                    label_color = generate_random_color()
                    label_id = add_label_to_db(complete_date, label_color)
                add_task2label_in_db(task_id=task_id, label_id=label_id)
            elif event.source().name == "DONE":
                task2labels = get_task2label_from_db(task_id)
                for task2label_id, _, label_name, _, _ in task2labels:
                    if label_name.startswith("Done:"):
                        delete_task2label_from_db(task2label_id)

            self.parent.action_history.record({
                'type': 'move_task',
                'source_column': event.source(),
                'target_column': self,
                'task_item': item,
                'original_row': event.source().row(item),
                'new_row': drop_row
            })

            event.accept()
            event.source().clearSelection()
            event.source().clearFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.detele_selected_item()
            return
        if event.key() == Qt.Key.Key_Escape:
            if self.selectedItems():
                self.clearSelection()
                self.clearFocus()
                return
        if event.key() == Qt.Key.Key_M and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_popup_item()
            return
        super().keyPressEvent(event)

    def detele_selected_item(self):
        selected_items = self.selectedItems()
        if selected_items:
            for selected_item in selected_items:
                task_id = selected_item.data(Qt.ItemDataRole.UserRole) 
                column = selected_item.listWidget()
                deleted_task_name, deleted_task_goal, deleted_task_detail, deleted_task_deadline, deleted_is_weekly_task, _, deleted_waiting_task = get_task_from_db(task_id)
                column.takeItem(column.row(selected_item))  
                task2labels = get_task2label_from_db(task_id)
                deleted_labels_id = [ labels_id for _, labels_id, _, _, _ in task2labels]
                deleted_task2labels_id = get_task2label_from_db(task_id)
                delete_task_from_db(task_id)
                self.parent.action_history.record({
                    'type': 'delete_task',
                    'task_id': task_id,
                    'task_data': (deleted_task_name, deleted_task_goal, deleted_task_detail, deleted_task_deadline, deleted_is_weekly_task, column.id, deleted_waiting_task),
                    'task2labels_id': deleted_task2labels_id,
                    'labels_id': deleted_labels_id,
                    'source_column': column,
                    'original_row': column.row(selected_item),
                })
            self.clearFocus()

    def focusOutEvent(self, event):
        self.clearSelection()
        super().focusOutEvent(event)

    def show_popup_item(self):
        selected_items = self.selectedItems()
        if selected_items:
            item_text = selected_items[0].text()
            popup_window = PopupTaskWindow(item_text, selected_items[0], self.parent)
            popup_window.show()
            self.clearFocus()

    def mouseMoveEvent(self, event):
        if event.type() == QEvent.Type.MouseMove:
            item = self.itemAt(event.position().toPoint())
            if item:
                if self.current_item is None:
                    self.current_item = item
                    self.current_item.timer.start(100)
                    #self.current_item.timer.start(1000)
                elif item != self.current_item:
                    self.current_item.clear_detail()
                    self.current_item.timer.stop()
                    self.current_item = item
                    self.current_item.timer.start(100)
                    #self.current_item.timer.start(1000)
            else:
                if self.current_item:
                    self.current_item.clear_detail()
                    self.current_item.timer.stop()
                    self.current_item = None
        return super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        if self.current_item:
            self.current_item.clear_detail()
            self.current_item.timer.stop()
            self.current_item = None
        return super().leaveEvent(event)

class KanbanBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.action_history = ActionHistory(self)
        self.tasks_priority = {}
        self.dialogs = {}
        self.init_ui()
        self.load_tasks()
        self.setup_shortcuts()

    def init_ui(self):
        self.setWindowIcon(QIcon("icon/dokuro_switch.ico"))
        self.setWindowTitle("TODO App")
        self.setGeometry(100, 100, 800, 600)

        self.todo_column = KanbanColumn("TODO", self)
        self.doing_column = KanbanColumn("DOING", self)
        self.waiting_column = KanbanColumn("WAITING", self)
        self.done_column = KanbanColumn("DONE", self)
        self.columns = {
            "TODO": self.todo_column,
            "DOING": self.doing_column,
            "WAITING": self.waiting_column,
            "DONE": self.done_column,
        }

        self.todo_search_box = SearchBox(self)
        self.doing_search_box = SearchBox(self)
        self.waiting_search_box = SearchBox(self)
        self.done_search_box = SearchBox(self)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.create_column("TODO", self.todo_column, self.todo_search_box))
        self.layout.addWidget(self.create_column("DOING", self.doing_column, self.doing_search_box))
        self.layout.addWidget(self.create_column("WAITING", self.waiting_column, self.waiting_search_box))
        self.layout.addWidget(self.create_column("DONE", self.done_column, self.done_search_box))
        self.setLayout(self.layout)

    def create_column(self, title, column, search_box):
        column_widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel(title)
        layout.addWidget(label)

        add_button = QPushButton("+")
        add_button.clicked.connect(lambda: self.open_add_task_dialog(column))
        layout.addWidget(add_button)

        search_box.returnPressed.connect(lambda: search_box.filter_list(column))
        layout.addWidget(search_box)

        layout.addWidget(column)
        column.itemDoubleClicked.connect(self.open_edit_task_dialog)  
        column_widget.setLayout(layout)
        return column_widget

    def load_tasks(self):
        tasks = get_alltask_from_db()
        items = {}
        for task in tasks:
            task_id, task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_name, waiting_task = task
            if status_name == "DONE" and is_weekly_task:
                new_deadline = (datetime.datetime.strptime(task_deadline, "%Y/%m/%d") + datetime.timedelta(weeks=1)).strftime("%Y/%m/%d") if task_deadline else None
                new_status_id = self.columns["TODO"].id
                task = (task_id, task_name, task_goal, task_detail, new_deadline, is_weekly_task, new_status_id, waiting_task)
                update_task_in_db(task)
                task2labels = get_task2label_from_db(task_id)
                for task2label_id, _, label_name, _, _ in task2labels:
                    if label_name.startswith("Done:"):
                        delete_task2label_from_db(task2label_id)
            item = self.create_item(task)
            items[task_id] = item
        self.add_items_in_column_in_order_of_priority(items)

    def get_color(self, task_deadline):
        if task_deadline:
            deadline_date = datetime.datetime.strptime(task_deadline, "%Y/%m/%d") + datetime.timedelta(hours=17, minutes=45)
            now = datetime.datetime.now() 
            weekdays_diff = count_weekdays(now, deadline_date)
            if weekdays_diff <= 0:
                color = QColor(0, 0, 0)
            elif weekdays_diff <= 1:
                color = QColor(255, 0, 0)
            elif weekdays_diff <= 3:
                color = QColor(255, 150, 0)
            else:
                color = QColor(0, 0, 255)
        else:
            color = QColor(0, 0, 255)
        return color

    def calc_priority(self, task_id):
        priority = 0
        _, _, _, task_deadline, _, _, _ = get_task_from_db(task_id)
        if task_deadline:
            deadline_date = datetime.datetime.strptime(task_deadline, "%Y/%m/%d") + datetime.timedelta(hours=17, minutes=45)
            now = datetime.datetime.now() 
            weekdays_diff = count_weekdays(now, deadline_date)
            if weekdays_diff <= 0:
                priority += float('inf')
            elif weekdays_diff <= 1:
                priority += 100
            elif weekdays_diff <= 3:
                priority += 10
        labels = get_task2label_from_db(task_id)
        if labels:
            for _, _, _, _, label_point in labels:
                priority += label_point
        self.tasks_priority[task_id] = priority
        return priority

    def create_item(self, task):
        task_id, task_name, _, _, task_deadline, _, _, _ = task
        item = KanbanItem(f"#{task_id} {task_name}", task_id)
        color = self.get_color(task_deadline)
        item.setForeground(color)
        item.setSizeHint(QSize(100, 50))
        self.calc_priority(task_id)
        return item

    def update_item(self, item, task):
        task_id, task_name, _, _, task_deadline, _, _, _ = task
        item.setText(f"#{task_id} {task_name}")
        color = self.get_color(task_deadline)
        item.setForeground(color)
        self.calc_priority(task_id)
        column = item.listWidget()
        column.takeItem(column.row(item))
        self.add_item_in_column(item)
        self.insert_item_in_column(item)
        return item

    def add_items_in_column_in_order_of_priority(self, items):
        sorted_priorities = sorted(self.tasks_priority.items(), reverse=True, key=lambda x: x[1])
        for (task_id, _) in sorted_priorities:
            item = items[task_id]
            self.add_item_in_column(item)

    def add_item_in_column(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole) 
        _, _, _, _, _, status_name, _ = get_task_from_db(task_id)
        column = self.columns[status_name]
        column.addItem(item)
        return column

    def insert_item_in_column(self, item):
        target_task_id = item.data(Qt.ItemDataRole.UserRole) 
        column = item.listWidget()
        for i in range(column.count()): 
            source_item = column.item(i)
            source_task_id = source_item.data(Qt.ItemDataRole.UserRole) 
            source_priority = self.tasks_priority[source_task_id]
            target_priority = self.tasks_priority[target_task_id]
            if source_priority < target_priority:
                column.takeItem(column.row(item))
                column.insertItem(column.row(source_item), item)
                break
            elif source_priority == target_priority:
                if source_task_id > target_task_id:
                    column.takeItem(column.row(item))
                    column.insertItem(column.row(source_item), item)
                    break
        return column

    def open_add_task_dialog(self, column):
        dialog = TaskDialog(self)
        dialog.status_combo.setCurrentText(column.name) 
        dialog.show()
        self.dialogs[id(dialog)] = dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_name = dialog.task_name.text()
            task_goal = dialog.task_goal.text()
            task_detail = dialog.task_detail.toPlainText()
            task_deadline = dialog.task_deadline.text()
            task_deadline = None if task_deadline == "" else task_deadline
            is_weekly_task = dialog.is_weekly_task.isChecked()
            status_id = dialog.status_combo.itemData(dialog.status_combo.currentIndex())
            waiting_task = dialog.waiting_input.text()
            task_id = add_task_to_db((task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_id, waiting_task))
            labels_id = dialog.newlabels_id
            if status_id == self.columns["DONE"].id:
                complete_date = "Done:" + datetime.datetime.now().strftime("%Y/%m/%d")
                label = get_label_by_name_from_db(complete_date)
                if label:
                    label_id, _, _, _ = label
                else:
                    label_color = generate_random_color()
                    label_id = add_label_to_db(complete_date, label_color)
                labels_id.append(label_id)
            for label_id in labels_id:
                add_task2label_in_db(task_id=task_id, label_id=label_id)
            task2labels_id = get_task2label_from_db(task_id)
            task_data = (task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_id, waiting_task)
            item = self.create_item((task_id, *task_data))
            added_column = self.add_item_in_column(item)
            self.insert_item_in_column(item)
            self.action_history.record({
                'type': 'add_task',
                'task_id': task_id,
                'task_data': task_data,
                'task2labels_id': task2labels_id,
                'source_column': added_column,
                'original_row': added_column.row(item),
            }) 

    def open_edit_task_dialog(self, item):
        column = item.listWidget()
        task_id = item.data(Qt.ItemDataRole.UserRole) 
        old_task_name, old_task_goal, old_task_detail, old_task_deadline, old_is_weekly_task, old_status_name, old_waiting_task = get_task_from_db(task_id)
        old_status_id = column.id
        old_task_data = (old_task_name, old_task_goal, old_task_detail, old_task_deadline, old_is_weekly_task, old_status_id, old_waiting_task)
        old_task2labels_id = get_task2label_from_db(task_id)
        old_task_labels_id = [label_id for _, label_id, _, _, _ in old_task2labels_id]
        dialog = TaskDialog(self, task_id=task_id)
        dialog.task_name.setText(old_task_name)
        dialog.task_goal.setText(old_task_goal)
        dialog.task_detail.setPlainText(old_task_detail)
        dialog.task_deadline.setText(old_task_deadline)
        dialog.is_weekly_task.setChecked(bool(old_is_weekly_task))
        dialog.status_combo.setCurrentText(old_status_name) 
        dialog.waiting_input.setText(old_waiting_task)
        dialog.display_labels(old_task2labels_id)
        dialog.show()
        self.dialogs[id(dialog)] = dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_task_name = dialog.task_name.text()
            new_task_goal = dialog.task_goal.text()
            new_task_detail = dialog.task_detail.toPlainText()
            new_task_deadline = dialog.task_deadline.text() 
            new_is_weekly_task = 1 if dialog.is_weekly_task.isChecked() else 0
            new_task_deadline = None if new_task_deadline == "" else new_task_deadline
            new_status_id = dialog.status_combo.itemData(dialog.status_combo.currentIndex()) 
            new_waiting_task = dialog.waiting_input.text()
            new_task_data = (new_task_name, new_task_goal, new_task_detail, new_task_deadline, new_is_weekly_task, new_status_id, new_waiting_task)
            new_labels_id = dialog.newlabels_id
            update_task_in_db((task_id, *new_task_data))
            if old_status_name != "DONE" and new_status_id == self.columns["DONE"].id:
                complete_date = "Done:" + datetime.datetime.now().strftime("%Y/%m/%d")
                label = get_label_by_name_from_db(complete_date)
                if label:
                    label_id, _, _, _ = label
                else:
                    label_color = generate_random_color()
                    label_id = add_label_to_db(complete_date, label_color)
                new_labels_id.append(label_id)
            elif old_status_name == "DONE" and new_status_id != self.columns["DONE"].id:
                task2labels = get_task2label_from_db(task_id)
                for task2label_id, _, label_name, _, _ in task2labels:
                    if label_name.startswith("Done:"):
                        delete_task2label_from_db(task2label_id)
            self.update_item(item, (task_id, *new_task_data))
            new_task2labels_id = []
            for label_id in new_labels_id:
                new_task2label_id = add_task2label_in_db(task_id=task_id, label_id=label_id)
                new_task2labels_id.append(new_task2label_id)
            self.action_history.record({
                'type': 'edit_task',
                'task_id': task_id,
                'old_task_labels_id': old_task_labels_id,
                'old_task_data': old_task_data,
                'new_task_labels_id': new_labels_id,
                'new_task_data': new_task_data,
                'new_task2labels_id': new_task2labels_id,
                'item': item
            }) 
        column.clearFocus()

    def setup_shortcuts(self):
        undo_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Z), self)
        undo_shortcut.activated.connect(self.action_history.undo)
        redo_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Y), self)
        redo_shortcut.activated.connect(self.action_history.redo)
    
    def focus_next_dialog(self, dialog_id):
        del self.dialogs[dialog_id]
        if len(self.dialogs) > 0:
            next_dialog = list(self.dialogs.values())[-1]
            next_dialog.activateWindow()
            next_dialog.raise_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        #self.action_history.save()
        #sio.disconnect()
        event.accept()

class TaskDetail(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def mousePressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            cursor = self.cursorForPosition(event.pos())
            selected_text = self.document().findBlockByNumber(cursor.blockNumber()).text()
            if re.match(r'https?://[^\s]+', selected_text):
                webbrowser.open(selected_text)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        selected_text = self.document().findBlockByNumber(cursor.blockNumber()).text()
        if re.match(r'https?://[^\s]+', selected_text):
            webbrowser.open(selected_text)
        super().mouseDoubleClickEvent(event)

class TaskDialog(QDialog):
    def __init__(self, parent=None, task_id=None):
        super().__init__()
        self.parent = parent
        self.task_id = task_id
        self.newlabels_id = []
        self.selected_label = None
        self.init_ui()
        self.setup_shortcuts()
    
    def init_ui(self):
        self.setWindowTitle("Task")
        self.setGeometry(200, 200, 500, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QFormLayout()

        self.task_name = QLineEdit(self)
        layout.addRow("Task:", self.task_name)

        self.task_goal = QLineEdit(self)
        layout.addRow("Goal:", self.task_goal)

        deadline_layout = QHBoxLayout()
        self.task_deadline = QPushButton("", self)
        self.task_deadline.setStyleSheet("text-align: left; padding-left: 10px;") 
        self.task_deadline.clicked.connect(self.open_calendar)
        self.task_deadline.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        deadline_layout.addWidget(self.task_deadline)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(QLabel("Repeat:", self)) 
        self.is_weekly_task = QCheckBox(self)
        self.is_weekly_task.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        checkbox_layout.addWidget(self.is_weekly_task)
        deadline_layout.addLayout(checkbox_layout)
        layout.addRow("Deadline:", deadline_layout)

        self.task_detail = TaskDetail(self)
        layout.addRow("Detail:", self.task_detail)

        self.status_combo = QComboBox(self)
        all_status = get_allstatus_form_db()
        for index, (status_id, status_name) in enumerate(all_status):
            self.status_combo.addItem(status_name) 
            self.status_combo.setItemData(index, status_id)
        self.status_combo.currentIndexChanged.connect(self.update_visibility)
        layout.addRow("Status:", self.status_combo)

        self.waiting_input_label = QLabel("Waiting for", self.status_combo)
        self.waiting_input_label.setVisible(False) 
        self.waiting_input = QLineEdit(self)
        self.waiting_input.setPlaceholderText("What are you waiting for?")
        self.waiting_input.setVisible(False) 
        layout.addRow(self.waiting_input_label, self.waiting_input)

        self.label_display_area = QScrollArea()
        self.label_display_area.setWidgetResizable(True)
        self.label_display_area.setMaximumHeight(30)
        self.label_display_area.setMinimumWidth(400)
        self.label_display_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.label_widget = QWidget()
        self.label_display_layout = QHBoxLayout(self.label_widget)
        self.label_display_area.setWidget(self.label_widget)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Enter keyword...")
        self.label_input.returnPressed.connect(self.add_label)

        label_layout = QVBoxLayout()
        label_layout.addWidget(self.label_input)
        label_layout.addWidget(self.label_display_area)
        layout.addRow("Keywords:", label_layout)

        self.dialog_button= QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.dialog_button.accepted.connect(self.handle_accept)
        self.dialog_button.rejected.connect(self.handle_reject)
        layout.addRow(self.dialog_button)


        self.setLayout(layout)

    def update_visibility(self):
        if self.status_combo.currentText() == "WAITING": 
            self.waiting_input.setVisible(True)
            self.waiting_input_label.setVisible(True) 
        else:
            self.waiting_input.setVisible(False)
            self.waiting_input_label.setVisible(False) 

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            return
        if event.key() == Qt.Key.Key_Delete:
            if self.selected_label:
                self.remove_label() 
                return
        if event.key() == Qt.Key.Key_Escape:
            if self.selected_label:
                label_color = self.selected_label.property("label_color") 
                self.selected_label.setStyleSheet(f"""
                    background-color: {label_color};
                    border-radius: 5px;
                """)
                return
            else:
                self.handle_reject()
        super().keyPressEvent(event)

    def open_calendar(self):
        dialog = CalendarDialog(self.update_date)
        dialog.exec()  

    def update_date(self, date):
        return self.task_deadline.setText(date)
    
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
        if self.selected_label:
            label_widget = self.selected_label
            self.label_display_layout.removeWidget(label_widget)
            label_id = label_widget.property("label_id")
            if label_id in self.newlabels_id:
                self.newlabels_id.remove(label_id)
                delete_label_in_db(label_id)
            else:
                task2label_id = label_widget.property("task2label_id")
                delete_task2label_from_db(task2label_id)
            label_widget.deleteLater() 
            self.selected_label = None

    def update_task(self): 
        task_id = self.task_id
        task_name = self.task_name.text()
        task_goal = self.task_goal.text()
        task_detail = self.task_detail.toPlainText()
        task_deadline = self.task_deadline.text()
        if task_deadline == "":
            task_deadline = None
        is_weekly_task = self.is_weekly_task.isChecked()
        status_id = self.status_combo.itemData(self.status_combo.currentIndex()) 
        waiting_task = self.waiting_input.text()
        new_task = (task_id, task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_id, waiting_task)
        update_task_in_db(new_task)
        newlabels_id = self.newlabels_id
        for label_id in newlabels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)

    def make_links_clickable(self):
        import re
        text = self.task_detail.toPlainText()
        url_pattern = r'(https?://[^\s]+)'
        if re.match(url_pattern, text):
            url = re.sub(url_pattern, text)
            QDesktopServices.openUrl(QUrl(url))  

    def setup_shortcuts(self):
        update_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_S), self)
        update_shortcut.activated.connect(self.update_task)
        ok_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        ok_shortcut.activated.connect(self.handle_accept)

    def handle_accept(self):
        self.add_label()
        if self.parent is not None:
            self.parent.focus_next_dialog(id(self))
        self.accept()

    def handle_reject(self):
        if self.parent is not None:
            self.parent.focus_next_dialog(id(self))
        self.reject() 

    def closeEvent(self, event):
        if self.parent is not None:
            self.parent.focus_next_dialog(id(self))
        event.accept()

class CalendarDialog(QDialog):
    def __init__(self, on_date_selected):
        super().__init__()
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
        self.undo_stack_file = 'undo_stack.pkl'
        self.redo_stack_file = 'redo_stack.pkl'
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
        if not self.undo_stack:
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
            self.move_task(last_action)
        self.redo_stack.append(last_action)

    def redo(self):
        if not self.redo_stack:
            return
        last_undo_action = self.redo_stack.pop()
        if last_undo_action['type'] == 'add_task':
            self.add_task(last_undo_action)
        elif last_undo_action['type'] == 'delete_task':
            self.delete_task(last_undo_action)
        elif last_undo_action['type'] == 'edit_task':
            self.update_task(last_undo_action)
        elif last_undo_action['type'] == 'restore_task':
            self.restore_task(last_undo_action)
        elif last_undo_action['type'] == 'move_task':
            self.move_task(last_undo_action)
        self.undo_stack.append(last_undo_action) 

    def add_task(self, last_action):
        task_data = last_action['task_data']
        task_id = add_task_to_db(task_data)
        labels_id = last_action['labels_id']
        for label_id in labels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)
        item = self.kanban_board.create_item((task_id, *task_data))
        self.kanban_board.add_item_in_column(item)
        self.kanban_board.insert_item_in_column(item)

    def delete_task(self, last_action):
        task_id = last_action["task_id"]
        delete_task_from_db(task_id)
        task2labels_id = last_action["task2labels_id"]
        for task2label_id in task2labels_id:
            delete_task2label_from_db(task2label_id)
        source_column = last_action["source_column"]
        source_column.takeItem(last_action['original_row'])

    def update_task(self, last_action):
        task_id = last_action['task_id']
        new_task_data = last_action['new_task_data']
        new_task_labels_id = last_action['new_task_labels_id']
        item = last_action['item']
        task = (task_id, *new_task_data)
        update_task_in_db(task)
        for label_id in new_task_labels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)
        self.kanban_board.update_item(item, task)

    def restore_task(self, last_action):
        task_id = last_action['task_id']
        old_task_data = last_action['old_task_data']
        old_task_labels_id = last_action['old_task_labels_id']
        new_task_labels_id = last_action['new_task_labels_id']
        new_task2labels_id = last_action['new_task2labels_id']
        item = last_action['item']
        task = (task_id, *old_task_data)
        update_task_in_db(task)
        for old_task_label_id in old_task_labels_id:
            if old_task_label_id not in new_task_labels_id:
                add_task2label_in_db(task_id=task_id, label_id=old_task_label_id)
        for task2label_id in new_task2labels_id:
            delete_task2label_from_db(task2label_id)
        self.kanban_board.update_item(item, task)


    def move_task(self, last_action):
        task_item = last_action['task_item']
        source_column = last_action['source_column']
        target_column = last_action['target_column']

        target_column.takeItem(target_column.row(task_item))
        source_column.insertItem(last_action['original_row'], task_item)

        task_id = task_item.data(Qt.ItemDataRole.UserRole)
        task_name, task_goal, task_detail, task_deadline, is_weekly_task, _, waiting_task = get_task_from_db(task_id)
        task = (task_id, task_name, task_goal, task_detail, task_deadline, is_weekly_task, source_column.id, waiting_task)
        update_task_in_db(task)

    def save_undo_stack(self):
        with open(self.undo_stack_file, 'wb') as f:
            pickle.dump(self.undo_stack, f)

    def save_redo_stack(self):
        with open(self.redo_stack_file, 'wb') as f:
            pickle.dump(self.redo_stack, f)

    def save(self):
        self.save_undo_stack()
        self.save_redo_stack()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kanban_board = KanbanBoard()
    kanban_board.show()
    sys.exit(app.exec())
