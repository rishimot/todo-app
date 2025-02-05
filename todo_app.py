import os
import subprocess
import sys
import pickle
import datetime
import webbrowser
import socketio
import re
from utils import (
    generate_random_color,
    count_weekdays,
    get_allstatus_form_db,
    get_status_by_name_from_db,
    get_task_from_db,
    get_alltask_from_db,
    get_label_by_name_from_db,
    get_task2label_from_db,
    get_task2label_by_label_id_from_db,
    get_label2task_from_db,
    get_alllabel_from_db,
    get_alltask2label_from_db,
    add_task2label_in_db,
    add_task_to_db_by_api,
    add_time_to_db,
    add_label_to_db,
    update_task_in_db_by_api,
    delete_label_in_db,
    delete_task2label_from_db,
    delete_task_from_db_by_api,
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
    QTimeEdit,
    QDateTimeEdit,
    QMessageBox,
)

class DigitalTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_id = self.parent().item.data(Qt.ItemDataRole.UserRole)
        self.setting_time = 30
        self.button_size = (25, 25)
        self.mode = "CountDown"
        self.start_time = None
        self.end_time = None
        self.time_format = "%Y/%m/%d %H:%M:%S"
        self.load_assets()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.label = QLabel(f'{self.setting_time}:00', self)
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

    def is_timer_running(self):
        return self.start_time is not None

    def change_mode(self):
        self.timer.timeout.disconnect()
        if self.mode == "CountDown":
            self.mode = "CountUp" 
            self.label.setText(f'00:00')
            self.timer.timeout.connect(self.update_countup_timer)
        elif self.mode == "CountUp":
            self.mode = "CountDown"
            self.setting_time = 30
            self.label.setText(f'{self.setting_time:02}:00')
            self.timer.timeout.connect(self.update_countdown_timer)

    def start_timer(self):
        if not self.is_timer_running():
            self.start_time = datetime.datetime.now().strftime(self.time_format)
        self.time_elapsed = self.setting_time * 60 if self.mode == "CountDown" else 0
        self.duration_time = 0
        self.timer.start(1000) 
        self.label.mousePressEvent = lambda event: self.pause_timer()
        self.start_button.setPixmap(self.teishi_pixmap)
        self.start_button.mousePressEvent = lambda event: self.stop_timer()
    
    def pause_timer(self):
        self.start_button.setPixmap(self.saisei_pixmap)
        self.start_button.mousePressEvent = lambda event: self.resume_timer()
        self.label.mousePressEvent = lambda event: self.resume_timer()
        self.timer.stop()

    def resume_timer(self):
        self.timer.start(1000) 
        self.start_button.mousePressEvent = lambda event: self.stop_timer()
        self.start_button.setPixmap(self.teishi_pixmap)
        self.label.mousePressEvent = lambda event: self.pause_timer()

    def update_countdown_timer(self):
        self.duration_time += 1 
        self.time_elapsed -= 1
        if self.time_elapsed >= 0:
            minutes = (self.time_elapsed % 3600) // 60
            seconds = self.time_elapsed % 60
            self.label.setText(f'{minutes:02}:{seconds:02}')
            if self.time_elapsed == 0:
                self.tray_icon.showMessage(
                    "Notification",
                    f"{self.duration_time // 60}分{self.duration_time % 60}秒が経ちました",
                    QSystemTrayIcon.MessageIcon.Information,
                    1000
                )
        else:
            minutes = (-self.time_elapsed % 3600) // 60
            seconds = -self.time_elapsed % 60
            self.label.setText(f'-{minutes:02}:{seconds:02}')

    def update_countup_timer(self):
        self.duration_time += 1
        self.time_elapsed += 1
        minutes = (self.time_elapsed % 3600) // 60
        seconds = self.time_elapsed % 60
        self.label.setText(f'{minutes:02}:{seconds:02}')

    def stop_timer(self):
        self.start_button.setPixmap(self.saisei_pixmap)
        self.start_button.mousePressEvent = lambda event: self.start_timer()
        self.timer.stop()
        if self.duration_time >= 1:
            end_time = datetime.datetime.now().strftime(self.time_format)
            add_time_to_db((self.start_time, end_time, self.duration_time, self.task_id))
            self.tray_icon.showMessage(
                "Notification",
                f"{self.duration_time // 60}分{self.duration_time % 60}秒が経ちました",
                QSystemTrayIcon.MessageIcon.Information,
                1000
            )
            self.label.mousePressEvent = lambda event: self.change_mode()
            self.label.setText(f'{self.setting_time:02}:00' if self.mode == "CountDown" else "00:00")
            self.start_time = None

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
    def __init__(self, text, item, kanban_board):
        super().__init__()
        self.setWindowIcon(QIcon("icon/dokuro_switch.ico"))
        self.setWindowTitle("Popup Task Window")
        self.text = text[text.find("#") + 1:].strip().split(' ', 1)[1]
        self.kanban_board = kanban_board
        self.start_pos = None
        self.item = item
        self.is_pinned = True
        self.pin_only = False
        self.pin_size = (15, 15)
        self.pinwidget_size = (37, 37)
        self.load_assets()
        self.init_ui()

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

        self.task_timer = DigitalTimer(self)
        main_layout.addWidget(self.task_timer)

        self.main_widget = QWidget()
        self.main_widget.setLayout(main_layout)
        layout.addWidget(self.main_widget)
        self.setLayout(layout)

        window_flags = self.windowType()
        window_flags |= Qt.WindowType.FramelessWindowHint
        window_flags |= Qt.WindowType.WindowStaysOnTopHint 
        self.setWindowFlags(window_flags)

        self.adjustSize()
        self.original_size = (self.width(), self.height())
        self.small_mode()

    def load_assets(self):
        pin_red_pixmap = QPixmap("image/gabyou_pinned_plastic_red.png")
        pin_white_pixmap = QPixmap("image/gabyou_pinned_plastic_white.png")
        self.pin_red_pixmap = pin_red_pixmap.scaled(*self.pin_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.pin_white_pixmap = pin_white_pixmap.scaled(*self.pin_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def keyPressEvent(self, event: QMouseEvent):
        if event.key() == Qt.Key.Key_Escape:
            return
        if event.key() == Qt.Key.Key_N and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if not self.kanban_board:
                self.kanban_board = KanbanBoard()
            if self.kanban_board.isHidden():
                self.kanban_board.show()
            if self.kanban_board.isMinimized():
                self.kanban_board.showNormal()
            if not self.kanban_board.isActiveWindow():
                self.kanban_board.activateWindow()
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
            self.enlarge_mode()
        else:
            self.pin.setPixmap(self.pin_white_pixmap)
        self.show()

    def mouseDoubleClickEvent(self, event):
        self.kanban_board.open_edit_task_dialog(self.item)
        task_id = self.item.data(Qt.ItemDataRole.UserRole) 
        _, _, _, _, _, new_status_name, _, _, _ = get_task_from_db(task_id)
        if new_status_name != "DOING":
            self.close()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()  
        if event.button() == Qt.MouseButton.RightButton:
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
        self.task_timer.maximize()
        self.setFixedHeight(self.original_size[1])
        self.adjustSize()

    def small_mode(self):
        if self.target.text() != "":
            self.task_name.setText(self.target.text())
        self.target.hide()
        self.task_timer.minimize()
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

    def closeEvent(self, event):
        if self.task_timer.is_timer_running():
            self.task_timer.stop_timer()
        event.accept()

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
            task_name, _, _, deadline, _, status_name, waiting_task, _, _ = get_task_from_db(self.task_id)
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
        self.popup_window = None
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
            task_id = item.data(Qt.ItemDataRole.UserRole) 
            self.takeItem(self.row(item))
            self.insertItem(drop_row, item)
        else:
            item = event.source().currentItem()
            event.source().takeItem(event.source().row(item))
            drop_item = self.itemAt(event.position().toPoint())
            drop_row = self.row(drop_item) if drop_item else self.count() 
            self.insertItem(drop_row, item)

            task_id = item.data(Qt.ItemDataRole.UserRole) 
            task_name, task_goal, task_detail, task_deadline_date, task_type, _, waiting_task, remind_date, remind_input = get_task_from_db(task_id)
            new_task = (task_id, task_name, task_goal, task_detail, task_deadline_date, task_type, self.id, waiting_task, remind_date, remind_input)
            result = update_task_in_db_by_api(new_task)
            assert result, "データベースの更新でエラー"
            if result["type"] == "local":
                self.parent.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline_date, "task_type": task_type, "status_name": self.name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
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
            'task_id': task_id,
            'source_status_id': event.source().id,
            'target_status_id': self.id,
        })

        event.accept()
        event.source().clearSelection()
        event.source().clearFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_item()
        if event.key() == Qt.Key.Key_Escape:
            if self.selectedItems():
                self.clearSelection()
                self.clearFocus()
                return
        if event.key() == Qt.Key.Key_M and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            selected_items = self.selectedItems()
            if len(selected_items) > 0:
                self.show_popup_item(selected_items[0])
        super().keyPressEvent(event)

    def delete_selected_item(self):
        selected_items = self.selectedItems()
        if selected_items:
            for selected_item in selected_items:
                task_id = selected_item.data(Qt.ItemDataRole.UserRole) 
                (task_name, task_goal, task_detail, task_deadline, task_type, _, waiting_task, remind_date, remind_input) = get_task_from_db(task_id)
                deleted_task2labels = get_task2label_from_db(task_id)
                deleted_task2labels_id = [ task2label_id for task2label_id, _, _, _, _ in deleted_task2labels]
                deleted_labels_id = [ labels_id for _, labels_id, _, _, _ in deleted_task2labels]
                result = delete_task_from_db_by_api(task_id)
                assert result, "データベースの削除でエラー"
                if result["type"] == "local":
                    self.parent.on_delete_task(task_id)
                self.parent.action_history.record({
                    'type': 'delete_task',
                    'task_id': task_id,
                    'task_data': (task_name, task_goal, task_detail, task_deadline, task_type, self.id, waiting_task, remind_date, remind_input),
                    'labels_id': deleted_labels_id,
                    'task2labels_id': deleted_task2labels_id
                })
            self.clearFocus()

    def focusOutEvent(self, event):
        self.clearSelection()
        super().focusOutEvent(event)

    def show_popup_item(self, item):
        item_text = item.text()
        if self.popup_window:
            self.popup_window.close()
        self.popup_window = PopupTaskWindow(item_text, item, self.parent)
        self.popup_window.show()
        self.popup_window.task_timer.start_timer()
        self.parent.hide()

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
    
class KanbanBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks_priority = {}
        self.dialogs = {}
        self.taskid2dialogs = {}
        self.action_history = ActionHistory(self)
        self.init_ui()
        self.load_tasks()
        self.setup_shortcuts()
        self.connect_server()

    def connect_server(self):
        self.sio = socketio.Client()
        try:
            self.sio.on('post', self.on_post_task)
            self.sio.on('update', self.on_update_task)
            self.sio.on('delete', self.on_delete_task)
            self.sio.connect(f'{SERVER_URL}')
            print(f"Connection Success")
        except Exception as e:
            print(f"Connection failed: {e}")

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

    def on_delete_task(self, deleted_task_id):
        for column in self.columns.values():
            for i in range(column.count()):
                item = column.item(i)
                task_id = item.data(Qt.ItemDataRole.UserRole) 
                if deleted_task_id == task_id:
                    column.takeItem(column.row(item))  
                    return

    def on_update_task(self, task_id, new_task_data): 
        new_task_data = (new_task_data['name'], new_task_data['goal'], new_task_data['detail'], new_task_data['deadline'],  new_task_data['task_type'], new_task_data['status_name'], new_task_data['waiting_task'], new_task_data['remind_date'], new_task_data['remind_input'])
        for column in self.columns.values():
            for i in range(column.count()):
                item = column.item(i)
                source_task_id = item.data(Qt.ItemDataRole.UserRole) 
                if task_id == source_task_id:
                    self.update_item(item, (task_id, *new_task_data))
                    return

    def init_ui(self):
        self.setWindowIcon(QIcon("icon/dokuro_switch.ico"))
        self.setWindowTitle("TODO App")
        self.setGeometry(100, 100, 800, 600)

        todo_column = KanbanColumn("TODO", self)
        doing_column = KanbanColumn("DOING", self)
        waiting_column = KanbanColumn("WAITING", self)
        done_column = KanbanColumn("DONE", self)
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

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.create_column("TODO", todo_column, todo_search_box))
        self.layout.addWidget(self.create_column("DOING", doing_column, doing_search_box))
        self.layout.addWidget(self.create_column("WAITING", waiting_column, waiting_search_box))
        self.layout.addWidget(self.create_column("DONE", done_column, done_search_box))
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
        for task in tasks:
            task_id, task_name, task_goal, task_detail, task_deadline_date, task_type, status_name, waiting_task, remind_date, remind_input = task
            if ((task_type == "daily") or (status_name == "DONE" and task_type != "-")) and task_deadline_date and datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M")  <= datetime.datetime.now():
                new_deadline = task_deadline_date
                if task_type == "daily":
                    new_deadline = datetime.datetime.now().strftime("%Y/%m/%d 17:45") 
                elif task_type == "weekly":
                    new_deadline = (datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M") + datetime.timedelta(weeks=1)).strftime("%Y/%m/%d %H:%M") 
                elif task_type == "monthly":
                    new_deadline = (datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M") + datetime.timedelta(months=1)).strftime("%Y/%m/%d %H:%M")
                result = update_task_in_db_by_api((task_id, task_name, task_goal, task_detail, new_deadline, task_type, self.columns["TODO"].id, waiting_task, remind_date, remind_input))
                assert result, "データベースの更新でエラー"
                if result["type"] == "local":
                    self.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": new_deadline, "task_type": task_type, "status_name": "TODO", "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
                task2labels = get_task2label_from_db(task_id)
                for task2label_id, _, label_name, _, _ in task2labels:
                    if label_name.startswith("Done:"):
                        delete_task2label_from_db(task2label_id)
                task = (task_id, task_name, task_goal, task_detail, new_deadline, task_type, "TODO", waiting_task, remind_date, remind_input)
            self.create_item(task)

    def get_color(self, task_deadline_date):
        if task_deadline_date:
            deadline_date = datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M")
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

    def calc_priority(self, task):
        priority = 0
        task_id, _, _, _, task_deadline_date, _, _, _, _, _ = task
        if task_deadline_date:
            deadline_date = datetime.datetime.strptime(task_deadline_date, "%Y/%m/%d %H:%M") + datetime.timedelta(hours=17, minutes=45)
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
        task_id, task_name, _, _, task_deadline, _, status_name, _, _, _ = task
        item = KanbanItem(f"#{task_id} {task_name}", task_id)
        color = self.get_color(task_deadline)
        item.setForeground(color)
        item.setSizeHint(QSize(100, 50))
        self.calc_priority(task)
        self.columns[status_name].addItem(item)
        self.sort_item_in_column(item)
        return item

    def update_item(self, item, task):
        task_id, task_name, _, _, task_deadline_date, _, status_name, _, _, _ = task
        color = self.get_color(task_deadline_date)
        item.setText(f"#{task_id} {task_name}")
        item.setForeground(color)
        self.calc_priority(task)
        self.remove_item_in_column(item)
        self.columns[status_name].addItem(item)
        self.sort_item_in_column(item)
        return item

    def remove_item_in_column(self, item):
        column = item.listWidget()
        column.takeItem(column.row(item))
        return column

    def sort_item_in_column(self, item):
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
                if source_task_id < target_task_id:
                    column.takeItem(column.row(item))
                    column.insertItem(column.row(source_item), item)
                    break
        return column

    def open_add_task_dialog(self, column):
        dialog = TaskDialog(self)
        dialog.status_combo.setCurrentText(column.name) 
        dialog.start_new_editing()
        dialog.show()
        self.dialogs[id(dialog)] = dialog

    def open_edit_task_dialog(self, item):
        item.listWidget().clearFocus()
        task_id = item.data(Qt.ItemDataRole.UserRole) 
        if task_id in self.taskid2dialogs:
            dialog = self.taskid2dialogs[task_id]
            if dialog.isHidden():
                dialog.show()
            if dialog.isMinimized():
                dialog.showNormal()
            if not dialog.isActiveWindow():
                dialog.activateWindow()
            #dialog.raise_()
            return
        old_task_name, old_task_goal, old_task_detail, old_task_deadline, old_task_type, old_status_name, old_waiting_task, old_remind_date, old_remind_input = get_task_from_db(task_id)
        old_task2labels_id = get_task2label_from_db(task_id)
        dialog = TaskDialog(self, task_id=task_id)
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
        dialog.display_labels(old_task2labels_id)
        dialog.start_new_editing()
        dialog.show()
        self.dialogs[id(dialog)] = dialog
        self.taskid2dialogs[task_id] = dialog

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
        elif event.key() == Qt.Key.Key_M and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            for column in self.columns.values():
                item = column.current_item
                if item:
                    column.show_popup_item(item)
        super().keyPressEvent(event)

    def delete_unused_label(self):
        all_task2labels = get_alltask2label_from_db()
        used_label_id = [label_id for _, _, label_id in all_task2labels]
        all_labels = get_alllabel_from_db()
        all_label_id = [label_id for label_id, _, _, _ in all_labels]
        unused_label_id = set(all_label_id) - set(used_label_id)
        for label_id in unused_label_id:
            delete_label_in_db(label_id)

    def delete_unused_task2label(self):
        all_tasks = get_alltask_from_db()
        used_task_id = [task_id for task_id, _, _, _, _, _, _, _ in all_tasks]
        all_labels = get_alllabel_from_db()
        used_label_id = [label_id for label_id, _, _, _ in all_labels]
        all_task2labels = get_alltask2label_from_db()
        for task2label_id, task_id, label_id in all_task2labels:
            if (task_id not in used_task_id) or (label_id not in used_label_id):
                delete_task2label_from_db(task2label_id)

    def closeEvent(self, event):
        for column in self.columns.values():
            column.clear_item_detail()
        self.sio.disconnect()
        self.action_history.save()
        event.accept()

class PopUpTaskDetail(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.setup_shortcuts()
    
    def init_ui(self):
        self.setGeometry(100, 100, 700, 500)
        self.setWindowIcon(QIcon("icon/youhishi.ico"))
        self.setWindowTitle("Detail")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)
        self.text_edit = QTextEdit(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def setup_shortcuts(self):
        ok_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        ok_shortcut.activated.connect(self.accept)
        cancel_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        cancel_shortcut.activated.connect(self.reject)

    def zoom_in(self):
        current_font_size = self.text_edit.fontPointSize()
        new_font_size = current_font_size + 1
        self.text_edit.setFontPointSize(new_font_size)
        self.set_all_text_font_size(new_font_size)

    def zoom_out(self):
        current_font_size = self.text_edit.fontPointSize()
        new_font_size = max(current_font_size - 1, 1)
        self.text_edit.setFontPointSize(new_font_size)
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
            event.accept()
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == 59:
            self.zoom_in()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        super().keyPressEvent(event)

    def accept(self):
        self.parent.setPlainText(self.text_edit.toPlainText())
        return super().accept()

class TaskDetail(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_font_size = 10  
        self.button_size = (15, 15)
        self.init_ui()

    def init_ui(self):
        self.load_assets()
        self.setFontPointSize(self.default_font_size)
        self.popup_detail = None
        self.popup_button = self.createButton(self.popup_pixmap)
        self.popup_button.mousePressEvent = lambda event: self.open_edit_dialog()
        self.popup_button.move(self.width() - self.popup_button.width() - 15, 0) 
   
    def load_assets(self):
        self.popup_pixmap = QPixmap("image/popup.png").scaled(*self.button_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def createButton(self, pixmap):
        button = QLabel(self)
        button.setMaximumSize(*self.button_size)
        button.setPixmap(pixmap)
        return button

    def open_edit_dialog(self):
        self.popup_detail = PopUpTaskDetail(self)
        self.popup_detail.text_edit.setPlainText(self.toPlainText())
        self.popup_detail.text_edit.setFontPointSize(self.fontPointSize())
        self.popup_detail.finished.connect(self.close_edit_dialog) 
        self.popup_detail.show()
        self.parent().hide()

    def close_edit_dialog(self):
        self.popup_detail = None
        self.parent().show()

    def mousePressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            cursor = self.cursorForPosition(event.pos())
            selected_text = self.document().findBlockByNumber(cursor.blockNumber()).text()
            if re.match(r'https?://[^\s]+', selected_text):
                webbrowser.open(selected_text, new=1, autoraise=False)
            if re.match(r'^\\\\ssfs-2md01\.jp\.sharp\\046-0002-ＳＥＰセンター共有\\20_GroupShare\\映像Gr\\.*', selected_text):
                os.startfile(selected_text)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        selected_text = self.document().findBlockByNumber(cursor.blockNumber()).text()
        if re.match(r'^https?://[^\s]+', selected_text):
            webbrowser.open(selected_text, new=1, autoraise=False)
        if re.match(r'^\\\\ssfs-2md01\.jp\.sharp\\046-0002-ＳＥＰセンター共有\\.*', selected_text):
            os.startfile(selected_text)
        if re.match(r'^C:\\Users\\S145053\\.*', selected_text):
            os.startfile(selected_text)
        if re.match(r'^(X|Y|Z):\\.*', selected_text):
            os.startfile(selected_text)
        if re.match(r'^/home/s145053/.*', selected_text):
            self.open_vscode(selected_text)
        super().mouseDoubleClickEvent(event)

    def open_vscode(self, app_path):
        try:
            command = [
                "C:\\Users\\S145053\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
                "--remote",
                "ssh-remote+c1x",
                app_path,
            ]
            subprocess.Popen(command)
        except Exception as e:
            print(f"Could not open {app_path}: {e}")

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
            event.accept()
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == 59:
            self.zoom_in()
            event.accept()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
            event.accept()
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        self.popup_button.move(self.width() - self.popup_button.width() - 5, 5)
        super().resizeEvent(event)

class TaskDialog(QDialog):
    def __init__(self, parent=None, task_id=None):
        super().__init__()
        self.parent = parent
        self.task_id = task_id
        self.newlabels_id = []
        self.selected_label = None
        self.is_edited = False
        self.init_ui()
        self.setup_shortcuts()
    
    def init_ui(self):
        self.setWindowIcon(QIcon("icon/youhishi.ico"))
        self.setWindowTitle("Task")
        self.setGeometry(150, 100, 500, 550)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowMinimizeButtonHint)

        layout = QFormLayout()
        self.checkpoint_content = {}

        self.task_name = QLineEdit(self)
        self.task_name.textChanged.connect(self.on_edit)
        layout.addRow("Task:", self.task_name)
        self.checkpoint_content["Task"] = self.task_name.text()

        self.task_goal = QLineEdit(self)
        self.task_goal.textChanged.connect(self.on_edit)
        layout.addRow("Goal:", self.task_goal)
        self.checkpoint_content["Goal"] = self.task_goal.text()

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
        layout.addRow("Deadline:", deadline_layout)
        self.checkpoint_content["TaskType"] = self.task_type.currentText()
        self.checkpoint_content["Deadline"] = self.task_deadline_date.text() + " " + self.task_deadline_time.text() if self.task_deadline_date.text() != "" else None

        self.task_detail = TaskDetail(self)
        self.task_detail.textChanged.connect(self.on_edit)
        layout.addRow("Detail:", self.task_detail)
        self.checkpoint_content["Detail"] = self.task_detail.toPlainText()

        self.status_combo = QComboBox(self)
        all_status = get_allstatus_form_db()
        for index, (status_id, status_name) in enumerate(all_status):
            self.status_combo.addItem(status_name) 
            self.status_combo.setItemData(index, status_id)
        self.status_combo.currentIndexChanged.connect(self.update_visibility)
        layout.addRow("Status:", self.status_combo)
        self.checkpoint_content["Status"] = self.status_combo.currentText()

        self.waiting_input_label = QLabel("Waiting for:", self.status_combo)
        self.waiting_input_label.setVisible(False) 
        self.waiting_input = QLineEdit(self)
        self.waiting_input.textChanged.connect(self.on_edit)
        self.waiting_input.setPlaceholderText("What are you waiting for?")
        self.waiting_input.setVisible(False) 
        layout.addRow(self.waiting_input_label, self.waiting_input)
        self.checkpoint_content["Waiting for"] = self.waiting_input.text()

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
        self.checkpoint_content["Keywords"] = []

        remind_layout = QHBoxLayout()
        self.reminder = QCheckBox(self)
        self.reminder.setChecked(False)
        self.reminder.stateChanged.connect(self.toggle_remind_timer)
        remind_layout.addWidget(self.reminder) 
        self.remind_timer = QDateTimeEdit(self)
        self.remind_timer.dateTimeChanged.connect(self.on_edit)
        self.remind_timer.setDateTime(QDateTime(QDateTime.currentDateTime().date(), QTime(17, 45))) 
        self.remind_timer.setVisible(False)
        self.checkpoint_content["Reminder date"] = self.remind_timer.text() if self.reminder.isChecked() else None
        remind_layout.addWidget(self.remind_timer) 
        self.remind_input = QLineEdit(self)
        self.remind_input.textChanged.connect(self.on_edit)
        self.remind_input.setVisible(False) 
        self.checkpoint_content["Reminder input"] = self.remind_input.text() if self.reminder.isChecked() else None
        remind_layout.addWidget(self.remind_input) 
        layout.addRow("Reminder:", remind_layout)

        self.dialog_button= QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.dialog_button.accepted.connect(self.handle_accept)
        self.dialog_button.rejected.connect(self.handle_reject)
        layout.addRow(self.dialog_button)

        self.setLayout(layout)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            return
        elif event.key() == Qt.Key.Key_Delete:
            if self.selected_label:
                self.remove_label() 
        elif event.key() == Qt.Key.Key_Escape:
            if self.selected_label:
                label_color = self.selected_label.property("label_color") 
                self.selected_label.setStyleSheet(f"""
                    background-color: {label_color};
                    border-radius: 5px;
                """)
            return
        super().keyPressEvent(event)

    def open_calendar(self):
        self.on_edit()
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
        self.checkpoint_content["Keywords"] += [label_id]

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
            delete_task2label_from_db(task2label_id)
            task2labels_id = get_task2label_by_label_id_from_db(label_id)
            if len(task2labels_id) == 0:
                delete_label_in_db(label_id)
        label_widget.deleteLater() 
        self.selected_label = None
        self.on_edit()
        self.checkpoint_content["Keywords"].remove(label_id)

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
            self.parent.on_post_task({"taskId": task_id, "name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
        self.task_id = task_id
        for label_id in newlabels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)
        if status_name == "DONE":
            complete_date = "Done:" + datetime.datetime.now().strftime("%Y/%m/%d")
            label = get_label_by_name_from_db(complete_date)
            if label:
                label_id, _, _, _ = label
            else:
                label_color = generate_random_color()
                label_id = add_label_to_db(complete_date, label_color)
            add_task2label_in_db(task_id=task_id, label_id=label_id)
        task2labels = get_task2label_from_db(task_id)
        task2labels_id = [task2label_id for task2label_id, _, _, _, _ in task2labels]
        labels_id = [label_id for _, label_id, _, _, _ in task2labels]
        self.parent.action_history.record({
            'type': 'add_task',
            'task_id': task_id,
            'task_data': task_data,
            'labels_id': labels_id,
            'task2labels_id': task2labels_id,
        })

    def update_task(self): 
        old_task_data = (
            self.checkpoint_content["Task"], 
            self.checkpoint_content["Goal"],
            self.checkpoint_content["Detail"],
            self.checkpoint_content["Deadline"],
            self.checkpoint_content["TaskType"],
            self.checkpoint_content["Status"],
            self.checkpoint_content["Waiting for"],
            self.checkpoint_content["Reminder timer"],
            self.checkpoint_content["Reminder input"],
            )
        old_task_labels_id = self.checkpoint_content["Keywords"]

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
        status_name = self.status_combo.currentText()
        status_id = self.status_combo.itemData(self.status_combo.currentIndex()) 
        waiting_task = self.waiting_input.text()
        remind_date = self.remind_timer.text() if self.reminder.isChecked() else None
        remind_input = self.remind_input.text() if self.reminder.isChecked() else None
        new_task_data = (task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input)
        result = update_task_in_db_by_api((task_id, *new_task_data))
        assert result, "データベースの更新でエラー"
        if result["type"] == "local":
            self.parent.on_update_task(task_id, {"name": task_name, "goal": task_goal, "detail": task_detail, "deadline": task_deadline, "task_type": task_type, "status_name": status_name, "waiting_task": waiting_task, "remind_date": remind_date, "remind_input": remind_input})
        for label_id in self.newlabels_id:
            add_task2label_in_db(task_id=task_id, label_id=label_id)
        new_task2labels = get_task2label_from_db(self.task_id)
        new_task2labels_id = [task2label_id for task2label_id, _, _, _, _ in new_task2labels]
        self.parent.action_history.record({
            'type': 'edit_task',
            'task_id': task_id,
            'old_task_data': old_task_data, 
            'old_task_labels_id': old_task_labels_id,
            'new_task_data': new_task_data,
            'new_task_newlabels_id': self.newlabels_id,
            'new_task2labels_id': new_task2labels_id,
        }) 
        self.start_new_editing()

    def database_update(self):
        if self.task_id:
            self.update_task()
        else:
            self.post_task()

    def setup_shortcuts(self):
        to_database_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_S), self)
        to_database_shortcut.activated.connect(self.database_update)
        ok_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        ok_shortcut.activated.connect(self.handle_accept)
        popup_taskdetail_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_N), self)
        popup_taskdetail_shortcut.activated.connect(self.task_detail.open_edit_dialog)
        cancel_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        cancel_shortcut.activated.connect(self.handle_reject)

    def handle_accept(self):
        self.add_label()
        self.database_update()
        if self.parent is not None:
            self.parent.focus_next_dialog(id(self))
            del self.parent.taskid2dialogs[self.task_id]
        self.accept()

    def handle_reject(self):
        is_continue = self.check_edit_status()
        if is_continue:
            return
        if self.parent is not None:
            self.parent.focus_next_dialog(id(self))
            del self.parent.taskid2dialogs[self.task_id]
        self.reject() 

    def on_edit(self):
        self.setWindowTitle("Task*")
        self.is_edited = True

    def start_new_editing(self):
        self.checkpoint_content["Task"] = self.task_name.text()
        self.checkpoint_content["Goal"] = self.task_goal.text()
        self.checkpoint_content["Deadline"] = self.task_deadline_date.text() + " " + self.task_deadline_time.text() if self.task_deadline_date.text() != "" else None
        self.checkpoint_content["TaskType"] = self.task_type.currentText()
        self.checkpoint_content["Detail"] = self.task_detail.toPlainText()
        self.checkpoint_content["Status"] = self.status_combo.itemData(self.status_combo.currentIndex()) 
        self.checkpoint_content["Waiting for"] = self.waiting_input.text()
        self.checkpoint_content["Reminder timer"] = self.remind_timer.text() if self.reminder.isChecked() else None
        self.checkpoint_content["Reminder input"] = self.remind_input.text() if self.reminder.isChecked() else None
        self.checkpoint_content["Keywords"] =  [label_id for _, label_id, _, _, _ in get_task2label_from_db(self.task_id)]
        self.setWindowTitle("Task")
        self.is_edited = False

    def check_edit_status(self):
        if self.is_edited:
            current_content = {}
            current_content["Task"] = self.task_name.text()
            current_content["Goal"] = self.task_goal.text()
            current_content["Deadline"] = self.task_deadline_date.text() + " " + self.task_deadline_time.text() if self.task_deadline_date.text() != "" else None
            current_content["TaskType"] = self.task_type.currentText()
            current_content["Detail"] = self.task_detail.toPlainText()
            current_content["Status"] = self.status_combo.itemData(self.status_combo.currentIndex()) 
            current_content["Waiting for"] = self.waiting_input.text()
            current_content["Reminder timer"] = self.remind_timer.text() if self.reminder.isChecked() else None
            current_content["Reminder input"] = self.remind_input.text() if self.reminder.isChecked() else None
            current_content["Keywords"] =  [label_id for _, label_id, _, _, _ in get_task2label_from_db(self.task_id)]
            if (
                self.checkpoint_content["Task"] == current_content["Task"] and
                self.checkpoint_content["Goal"] == current_content["Goal"] and
                self.checkpoint_content["Deadline"] == current_content["Deadline"] and
                self.checkpoint_content["TaskType"] == current_content["TaskType"] and
                self.checkpoint_content["Detail"] == current_content["Detail"] and
                self.checkpoint_content["Status"] == current_content["Status"] and
                self.checkpoint_content["Waiting for"] == current_content["Waiting for"] and
                self.checkpoint_content["Reminder timer"] == current_content["Reminder timer"] and
                self.checkpoint_content["Reminder input"] == current_content["Reminder input"] and
                self.checkpoint_content["Keywords"] == current_content["Keywords"] 
            ):
                return False

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmation")
            msg_box.setText("編集を破棄しますか？")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            result = msg_box.exec()
            if result == QMessageBox.StandardButton.Yes:
                return False
            elif result == QMessageBox.StandardButton.No:
                return True
        return False

    def closeEvent(self, event):
        is_continue = self.check_edit_status()
        if is_continue:
            event.ignore() 
        if self.parent is not None:
            self.parent.focus_next_dialog(id(self))
            del self.parent.taskid2dialogs[self.task_id]
        event.accept()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kanban_board = KanbanBoard()
    kanban_board.show()
    sys.exit(app.exec())
