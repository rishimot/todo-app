import os
import sys
import pickle
import datetime
import socketio
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
    add_label_in_db,
    delete_task2label_from_db,
    add_task2label_in_db,
    add_task_to_db,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QUrl,
)
from PyQt6.QtGui import(
    QColor,
    QIcon,
    QKeySequence,
    QShortcut,
    QMouseEvent,
    QDesktopServices,
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
)

sio = socketio.Client()

class PopupWindow(QDialog):
    def __init__(self, text, item, kanban_board=None):
        super().__init__()
        self.kanban_board = kanban_board
        self.text = text
        self.item = item
        self.init_ui()

    def init_ui(self):
        self.setGeometry(0, 0, 200, 50)

        layout = QVBoxLayout()
        label = QLabel(self.text, self)
        layout.addWidget(label)
        self.setLayout(layout)

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)

    def keyPressEvent(self, event: QMouseEvent):
        if event.key() == Qt.Key.Key_M and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.close()
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.kanban_board.open_edit_task_dialog(self.item)
        super().mouseDoubleClickEvent(event)


class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setPlaceholderText("Search...")

    def filter_list(self, column):
        search_text = self.text().lower()
        splitted_search_texts = search_text.split(' ')
        for splitted_search_text in splitted_search_texts:
            if splitted_search_text.startswith('tag:'):
                search_text = splitted_search_text[4:]
                is_exclude = search_text.startswith('!')
                search_label = search_text[1:] if is_exclude else search_text
                label2tasks = get_label2task_from_db(search_label)
                task_ids = [ task_id for _, task_id, _ in label2tasks] 
                for index in range(column.count()):
                    item = column.item(index)
                    task_id = item.data(Qt.ItemDataRole.UserRole) 
                    if is_exclude:
                        item.setHidden(task_id in task_ids)
                    else:
                        item.setHidden(task_id not in task_ids)
            else:
                for index in range(column.count()):
                    item = column.item(index)
                    item_text = item.text()
                    if item_text.startswith('!'):
                        item_text = item_text[1:]
                        item.setHidden(item_text.find(splitted_search_text) != -1)
                    else:
                        item.setHidden(item_text.find(splitted_search_text) == -1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if self.hasFocus():
                self.clear()
        if event.key() == Qt.Key.Key_Escape:
            if self.hasFocus():
                self.clearFocus()
        super().keyPressEvent(event)


class KanbanColumn(QListWidget):
    def __init__(self, title, parent=None):
        super().__init__()
        self.parent = parent
        self.id, self.name = get_status_by_name_from_db(title)
        self.popup_window = None
        self.init_ui()

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
            task_name, task_goal, task_detail, task_deadline, _ = get_task_from_db(task_id)
            task = (task_id, task_name, task_goal, task_detail, task_deadline, self.id)
            update_task_in_db(task)

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
                deleted_task_name, deleted_task_goal, deleted_task_detail, deleted_task_deadline, _ = get_task_from_db(task_id)
                column.takeItem(column.row(selected_item))  
                task2labels = get_task2label_from_db(task_id)
                deleted_labels_id = [ labels_id for _, labels_id, _, _ in task2labels]
                deleted_task2labels_id = get_task2label_from_db(task_id)
                delete_task_from_db(task_id)
                self.parent.action_history.record({
                    'type': 'delete_task',
                    'task_id': task_id,
                    'task_data': (deleted_task_name, deleted_task_goal, deleted_task_detail, deleted_task_deadline, column.id),
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
            if self.popup_window is None or not self.popup_window.isVisible():
                self.popup_window = PopupWindow(item_text, selected_items[0], self.parent)
                self.popup_window.show()
            else:
                self.popup_window.close()
                self.popup_window = None
            self.clearFocus()


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
            task_id, _, _, _, _, _ = task
            item = self.create_item(task)
            items[task_id] = item
        self.add_items_in_column_in_order_of_priority(items)

    def get_color(self, task_deadline):
        if task_deadline:
            deadline_date = datetime.datetime.strptime(task_deadline, "%Y/%m/%d") + datetime.timedelta(hours=17, minutes=45)
            now = datetime.datetime.now() 
            if deadline_date - now < datetime.timedelta(days=0):
                color = QColor(0, 0, 0)
            elif deadline_date - now < datetime.timedelta(days=1):
                color = QColor(255, 0, 0)
            elif deadline_date - now < datetime.timedelta(days=7):
                color = QColor(255, 150, 0)
            else:
                color = QColor(0, 0, 255)
        else:
            color = QColor(0, 0, 255)
        return color

    def calc_priority(self, task_id):
        _, _, _, task_deadline, _ = get_task_from_db(task_id)
        priority = 1
        if task_deadline:
            deadline_date = datetime.datetime.strptime(task_deadline, "%Y/%m/%d") + datetime.timedelta(hours=17, minutes=45)
            now = datetime.datetime.now() 
            if deadline_date - now < datetime.timedelta(days=0):
                priority = float('inf')
            elif deadline_date - now < datetime.timedelta(days=1):
                priority = 1000
            elif deadline_date - now < datetime.timedelta(days=7):
                priority = 100
            else:
                priority = 10
        labels = get_task2label_from_db(task_id)
        if labels:
            importance = 1 
            for _, _, label_name, _ in labels:
                if label_name == "priority_high":
                    importance *= 5
                elif label_name == "priority_low":
                    importance *= 1
                else:
                    importance *= 3

                if label_name == "emergency":
                    importance *= 5
                elif label_name == "tivial":
                    importance *= 1
                else:
                    importance *= 3
            priority += importance
        self.tasks_priority[task_id] = priority
        return priority

    def create_item(self, task):
        task_id, task_name, _, _, task_deadline, _ = task
        item = QListWidgetItem(f"#{task_id} {task_name}")
        color = self.get_color(task_deadline)
        item.setForeground(color)
        item.setSizeHint(QSize(100, 50))
        item.setData(Qt.ItemDataRole.UserRole, task_id) 
        self.calc_priority(task_id)
        return item

    def update_item(self, item, task):
        task_id, task_name, _, _, task_deadline, _ = task
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
        _, _, _, _, status_name = get_task_from_db(task_id)
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
            status_id = dialog.status_combo.itemData(dialog.status_combo.currentIndex())
            labels_id = dialog.newlabels_id
            task_id = add_task_to_db((task_name, task_goal, task_detail, task_deadline, status_id))
            for label_id in labels_id:
                add_task2label_in_db(task_id=task_id, label_id=label_id)
            task2labels_id = get_task2label_from_db(task_id)
            task_data = (task_name, task_goal, task_detail, task_deadline, status_id)
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
        status_id = column.id
        old_task_name, old_task_goal, old_task_detail, old_task_deadline, old_status_name = get_task_from_db(task_id)
        old_task2labels_id = get_task2label_from_db(task_id)
        old_task_labels_id = [label_id for _, label_id, _, _ in old_task2labels_id]
        dialog = TaskDialog(self)
        dialog.task_name.setText(old_task_name)
        dialog.task_goal.setText(old_task_goal)
        dialog.task_detail.setPlainText(old_task_detail)
        dialog.task_deadline.setText(old_task_deadline)
        dialog.status_combo.setCurrentText(old_status_name) 
        dialog.display_labels(old_task2labels_id)
        dialog.show()
        self.dialogs[id(dialog)] = dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_task_name = dialog.task_name.text()
            new_task_goal = dialog.task_goal.text()
            new_task_detail = dialog.task_detail.toPlainText()
            new_task_deadline = dialog.task_deadline.text() 
            new_task_deadline = None if new_task_deadline == "" else new_task_deadline
            new_status_id = dialog.status_combo.itemData(dialog.status_combo.currentIndex()) 
            new_task = (task_id, new_task_name, new_task_goal, new_task_detail, new_task_deadline, new_status_id)
            update_task_in_db(new_task)
            for label_id in dialog.newlabels_id:
                add_task2label_in_db(task_id=task_id, label_id=label_id)
            self.update_item(item, new_task)
            self.insert_item_in_column(item)
            new_task2labels = get_task2label_from_db(task_id)
            new_task2labels_id = [task2label_id for task2label_id, _, _, _ in new_task2labels]
            new_task_labels_id = [label_id  for _, label_id, _, _ in new_task2labels]
            self.action_history.record({
                'type': 'edit_task',
                'task_id': task_id,
                'old_task_labels_id': old_task_labels_id,
                'old_task_data': (old_task_name, old_task_goal, old_task_detail, old_task_deadline, status_id),
                'new_task_labels_id': new_task_labels_id,
                'new_task_data': (new_task_name, new_task_goal, new_task_detail, new_task_deadline, new_status_id),
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

    def closeEvent(self, event):
        #self.action_history.save()
        #sio.disconnect()
        event.accept()


class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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

        self.task_deadline = QPushButton("", self)
        self.task_deadline.setStyleSheet("text-align: left; padding-left: 10px;") 
        self.task_deadline.clicked.connect(self.open_calendar)
        layout.addRow("Deadline:", self.task_deadline)

        self.task_detail = QTextEdit(self)
        layout.addRow("Detail:", self.task_detail)

        self.status_combo = QComboBox(self)
        all_status = get_allstatus_form_db()
        for index, (status_id, status_name) in enumerate(all_status):
            self.status_combo.addItem(status_name) 
            self.status_combo.setItemData(index, status_id)
        layout.addRow("Status:", self.status_combo)

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
        for task2label_id, label_id, label_name, label_color in task2labels:
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
            label_id, label_name, label_color = label
        else:
            label_color = generate_random_color()
            label_id = add_label_in_db(label_name, label_color)

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
            else:
                task2label_id = label_widget.property("task2label_id")
                delete_task2label_from_db(task2label_id)
            label_widget.deleteLater() 
            self.selected_label = None

    def make_links_clickable(self):
        import re
        text = self.task_detail.toPlainText()
        url_pattern = r'(https?://[^\s]+)'
        if re.match(url_pattern, text):
            url = re.sub(url_pattern, text)
            QDesktopServices.openUrl(QUrl(url))  

    def setup_shortcuts(self):
        ok_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        ok_shortcut.activated.connect(self.handle_accept)

    def handle_accept(self):
        self.add_label()
        if self.parent() is not None:
            self.parent().focus_next_dialog(id(self))
        self.accept()

    def handle_reject(self):
        if self.parent() is not None:
            self.parent().focus_next_dialog(id(self))
        self.reject() 

    def closeEvent(self, event):
        if self.parent() is not None:
            self.parent().focus_next_dialog(id(self))
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
        # ファイルが存在する場合、undo_stackをロード
        if os.path.exists(self.undo_stack_file):
            with open(self.undo_stack_file, 'rb') as f:
                try:
                    self.undo_stack = pickle.load(f)
                except (pickle.UnpicklingError, EOFError):
                    self.undo_stack = []

    def load_redo_stack(self):
        # ファイルが存在する場合、undo_stackをロード
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
        task_name, task_goal, task_detail, task_deadline, _ = get_task_from_db(task_id)
        task = (task_id, task_name, task_goal, task_detail, task_deadline, source_column.id)
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
