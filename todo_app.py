import sys
import datetime
from utils import (
    get_allstatus_form_db,
    get_status_by_name_from_db,
    get_task_from_db,
    update_task_in_db,
    delete_task_from_db,
    get_alltasks_from_db,
    add_task_in_db,
    get_label_by_name_from_db,
    get_task2label_from_db,
    generate_random_color,
    add_label_in_db,
    delete_task2label_from_db,
    add_task2label_in_db,
)
from PyQt6.QtCore import (
    Qt,
    QSize
)
from PyQt6.QtGui import QColor
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

class KanbanColumn(QListWidget):
    def __init__(self, title):
        super().__init__()
        self.id, self.name = get_status_by_name_from_db(title)
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
            event.accept()
            self.clearSelection()
            self.clearFocus()
        else:
            item = event.source().currentItem()
            event.source().takeItem(event.source().row(item))
            drop_item = self.itemAt(event.position().toPoint())
            drop_row = self.row(drop_item) if drop_item else self.count() 
            self.insertItem(drop_row, item)
            event.accept()

            task_id = item.data(Qt.ItemDataRole.UserRole) 
            _, task_name, task_goal, task_detail, task_deadline, _ = get_task_from_db(task_id)
            task = (task_id, task_name, task_goal, task_detail, task_deadline, self.id)
            update_task_in_db(task)
            event.source().clearSelection()
            event.source().clearFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.detele_selected_item()  
        if event.key() == Qt.Key.Key_Escape:
            if self.selectedItems():
                self.clearSelection()
                self.clearFocus()
        super().keyPressEvent(event)  

    def detele_selected_item(self):
        selected_items = self.selectedItems()  
        if selected_items:
            for item in selected_items:
                self.takeItem(self.row(item))  
                task_id = item.data(Qt.ItemDataRole.UserRole) 
                delete_task_from_db(task_id)
            self.clearFocus()

    def focusOutEvent(self, event):
        self.clearSelection()
        super().focusOutEvent(event)

class KanbanBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks_priority = {}

        self.setWindowTitle("TODO App")
        self.setGeometry(100, 100, 800, 600)

        self.todo_column = KanbanColumn("TODO")
        self.doing_column = KanbanColumn("DOING")
        self.waiting_column = KanbanColumn("WAITING")
        self.done_column = KanbanColumn("DONE")

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.create_column("TODO", self.todo_column))
        self.layout.addWidget(self.create_column("DOING", self.doing_column))
        self.layout.addWidget(self.create_column("WAITING", self.waiting_column))
        self.layout.addWidget(self.create_column("DONE", self.done_column))
        self.setLayout(self.layout)
        self.load_tasks()

    def create_column(self, title, column):
        column_widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel(title)
        layout.addWidget(label)
    
        add_button = QPushButton("+")
        add_button.clicked.connect(lambda: self.open_add_task_dialog(column))
        layout.addWidget(add_button)
        layout.addWidget(column)

        column.itemDoubleClicked.connect(self.open_edit_task_dialog)  

        column_widget.setLayout(layout)
        return column_widget

    def load_tasks(self):
        tasks = get_alltasks_from_db()
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

    def calc_priority(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole) 
        _, _, _, _, task_deadline, _ = get_task_from_db(task_id)
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
        importance = 1 
        labels = get_task2label_from_db(task_id)
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
        item.setText(f"#{task_id} {task_name}")
        item.setSizeHint(QSize(100, 50))
        item.setData(Qt.ItemDataRole.UserRole, task_id) 
        self.calc_priority(item)
        return item

    def update_item(self, item, task):
        task_id, task_name, _, _, task_deadline, _ = task
        item.setText(f"#{task_id} {task_name}")
        if task_deadline is not None:
            color = self.get_color(task_deadline)
            item.setForeground(color)
        self.calc_priority(item)
        column = item.listWidget()
        column.takeItem(column.row(item))
        self.add_item_in_column(item)
        return item

    def add_items_in_column_in_order_of_priority(self, items):
        sorted_priorities = sorted(self.tasks_priority.items(), reverse=True, key=lambda x: x[1])
        for (task_id, _) in sorted_priorities:
            item = items[task_id]
            self.add_item_in_column(item)

    def add_item_in_column(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole) 
        _, _, _, _, _, status_name = get_task_from_db(task_id)
        if status_name == "TODO":
            self.todo_column.addItem(item)
        if status_name == "DOING":
            self.doing_column.addItem(item)
        if status_name == "WAITING":
            self.waiting_column.addItem(item)
        if status_name == "DONE":
            self.done_column.addItem(item)

    def insert_item_in_column(self, item):
        target_task_id = item.data(Qt.ItemDataRole.UserRole) 
        column = item.listWidget()
        for i in range(column.count()): 
            source_item = column.item(i)
            source_task_id = source_item.data(Qt.ItemDataRole.UserRole) 
            source_priority = self.tasks_priority[source_task_id]
            target_priority = self.tasks_priority[target_task_id]
            if source_priority <= target_priority:
                column.takeItem(column.row(item))
                column.insertItem(column.row(source_item), item)
                return

    def open_add_task_dialog(self, column):
        dialog = TaskDialog(self)
        dialog.status_combo.setCurrentText(column.name) 
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_name = dialog.task_name.text()
            task_goal = dialog.task_goal.text()
            task_detail = dialog.task_detail.toPlainText()
            task_deadline = dialog.task_deadline.text()
            task_deadline = None if task_deadline == "" else task_deadline
            status_id = dialog.status_combo.itemData(dialog.status_combo.currentIndex())
            task_id = add_task_in_db((task_name, task_goal, task_detail, task_deadline, status_id))
            for label_id in dialog.newlabels_id:
                add_task2label_in_db(task_id=task_id, label_id=label_id)
            task = (task_id, task_name, task_goal, task_detail, task_deadline, status_id)
            item = self.create_item(task)
            self.add_item_in_column(item)
            self.insert_item_in_column(item)

    def open_edit_task_dialog(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole) 
        _, task_name, task_goal, task_detail, task_deadline, status_name = get_task_from_db(task_id)
        dialog = TaskDialog()
        dialog.task_name.setText(task_name)
        dialog.task_goal.setText(task_goal)
        dialog.task_detail.setPlainText(task_detail)
        dialog.task_deadline.setText(task_deadline)
        dialog.status_combo.setCurrentText(status_name) 
        dialog.display_labels(get_task2label_from_db(task_id))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_task_name = dialog.task_name.text()
            new_task_goal = dialog.task_goal.text()
            new_task_detail = dialog.task_detail.toPlainText()
            new_task_deadline = dialog.task_deadline.text() 
            new_task_deadline = None if new_task_deadline == "" else new_task_deadline
            new_status_id = dialog.status_combo.itemData(dialog.status_combo.currentIndex()) 
            task = (task_id, new_task_name, new_task_goal, new_task_detail, new_task_deadline, new_status_id)
            update_task_in_db(task)
            for label_id in dialog.newlabels_id:
                add_task2label_in_db(task_id=task_id, label_id=label_id)
            self.update_item(item, task)
            self.insert_item_in_column(item)
        item.listWidget().clearFocus()

class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.newlabels_id = []
        self.selected_label = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Task")
        self.setGeometry(200, 200, 500, 400)

        layout = QFormLayout()

        self.task_name = QLineEdit(self)
        layout.addRow("Task:", self.task_name)

        self.task_goal = QLineEdit(self)
        layout.addRow("Goal:", self.task_goal)

        self.task_detail = QTextEdit(self)
        layout.addRow("Detail:", self.task_detail)

        self.task_deadline = QPushButton("", self)
        self.task_deadline.setStyleSheet("text-align: left; padding-left: 10px;") 
        self.task_deadline.clicked.connect(self.open_calendar)
        layout.addRow("Deadline:", self.task_deadline)

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
        self.label_input.setPlaceholderText("Enter label...")
        self.label_input.returnPressed.connect(self.add_label)

        label_layout = QVBoxLayout()
        label_layout.addWidget(self.label_input)
        label_layout.addWidget(self.label_display_area)
        layout.addRow("Label:", label_layout)

        self.dialog_button= QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.dialog_button.accepted.connect(self.push_ok)
        self.dialog_button.rejected.connect(self.reject)
        layout.addRow(self.dialog_button)

        self.setLayout(layout)

    def push_ok(self):
        self.add_label()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.push_ok()
        if event.key() == Qt.Key.Key_Return:
            return
        if event.key() == Qt.Key.Key_Delete:
            self.remove_label() 
        super().keyPressEvent(event)

    def open_calendar(self):
        dialog = CalendarDialog(self.update_date)
        dialog.exec()  

    def update_date(self, date):
        # 選択された日付をラベルに表示
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


class CalendarDialog(QDialog):
    def __init__(self, on_date_selected):
        super().__init__()
        self.on_date_selected = on_date_selected

        # カレンダーウィジェットの作成
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.select_date)

        # レイアウトの設定
        layout = QVBoxLayout()
        layout.addWidget(self.calendar)
        self.setLayout(layout)
        self.setWindowTitle("Calendar")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kanban_board = KanbanBoard()
    kanban_board.show()
    sys.exit(app.exec())
