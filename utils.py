import sqlite3
import random
import requests
import datetime
import json
from create_db import create_db
import jpholiday

with open('./config.json', 'r') as config_file:
    config = json.load(config_file)
port = config.get('port', 8000)
database_path = config.get('database_path', "./todo.db")
SERVER_URL = f'http://localhost:{port}/'

create_db(database_path)

def generate_random_color():
    r = random.randint(70, 255)
    g = random.randint(70, 255)
    b = random.randint(70, 255)
    return f"#{r:02x}{g:02x}{b:02x}"

def get_mark_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_id, is_marked FROM mark WHERE task_id = ?", (task_id, ))
    mark_data = cursor.fetchone()
    if not mark_data:
        mark_id = add_mark_task_to_db((task_id, False))
        mark_data = (mark_id, task_id, False)
    conn.close()
    return mark_data


def add_mark_task_to_db(mark_data):
    task_id, is_marked = mark_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mark ( task_id, is_marked ) VALUES (?, ?)", (task_id, is_marked))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id


def update_mark_task_to_db(mark_data):
    mark_id, task_id, is_marked = mark_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mark 
        SET task_id = ?, is_marked = ?
        WHERE id = ?
    """, (task_id, is_marked, mark_id))
    last_mark_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_mark_id


def get_pin_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_id, is_pinned FROM pin WHERE task_id = ?", (task_id, ))
    pin_data = cursor.fetchone()
    if not pin_data:
        pin_id = add_pin_task_to_db((task_id, False))
        pin_data = (pin_id, task_id, False)
    conn.close()
    return pin_data

def add_pin_task_to_db(pin_data):
    task_id, is_pinned = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pin ( task_id, is_pinned ) VALUES (?, ?)", (task_id, is_pinned))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id

def update_pin_task_to_db(pin_data):
    pin_id, task_id, is_pinned = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pin 
        SET task_id = ?, is_pinned = ?
        WHERE id = ?
    """, (task_id, is_pinned, pin_id))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id

def delete_pin_task_in_db(pin_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM pin WHERE id = {pin_id}")
    conn.commit()
    conn.close()


def get_disable_tasks_from_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_id, disable FROM display WHERE disable = 1")
    display_data = cursor.fetchall()
    conn.close()
    return display_data

def get_display_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_id, disable FROM display WHERE task_id = ?", (task_id, ))
    display_data = cursor.fetchone()
    if not display_data:
        display_id = add_display_task_to_db((task_id, False))
        display_data = (display_id, task_id, False)
    conn.close()
    return display_data

def add_display_task_to_db(pin_data):
    task_id, disable = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO display ( task_id, disable ) VALUES (?, ?)", (task_id, disable))
    last_display_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_display_id

def update_display_task_to_db(pin_data):
    display_id, task_id, disable = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE display 
        SET task_id = ?, disable = ?
        WHERE id = ?
    """, (task_id, disable, display_id))
    last_display_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_display_id

def delete_display_task_in_db(pin_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM display WHERE id = {pin_id}")
    conn.commit()
    conn.close()


def get_time_from_db(time_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT start_time, end_time, duration, task_id FROM time WHERE id = ?", (time_id, ))
    time_data = cursor.fetchone()
    conn.close()
    return time_data

def get_task_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task.name, task.goal, task.detail, task.deadline, task.task_type, status.name, task.waiting_task, task.remind_date, task.remind_input
        FROM task 
        INNER JOIN status ON task.status_id = status.id
        WHERE task.id = ?
    """, (task_id, ))
    task = cursor.fetchone()
    conn.close()
    return task

def get_parenttask_from_db(child_task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task.id, task.name, task.goal, task.detail, task.deadline, task.task_type, status.name, task.waiting_task, task.remind_date, task.remind_input
        FROM task 
        INNER JOIN status ON task.status_id = status.id
        INNER JOIN subtask ON subtask.parent_id = task.id
        WHERE subtask.child_id = ?
    """, (child_task_id, ))
    task = cursor.fetchone()
    conn.close()
    return task

def get_allchildtask_from_db(parent_task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subtask.id, task.id, task.name, task.goal, task.detail, task.deadline, task.task_type, status.name, task.waiting_task, task.remind_date, task.remind_input
        FROM task 
        INNER JOIN status ON task.status_id = status.id
        INNER JOIN subtask ON subtask.child_id = task.id
        WHERE subtask.parent_id = ?
    """, (parent_task_id, ))
    all_tasks = cursor.fetchall()
    conn.close()
    return all_tasks

def get_label_from_db(label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT label.name, label.color, label.point
        FROM label 
        WHERE id = ?
    """, (label_id,))
    label = cursor.fetchone()
    conn.close()
    return label

def get_alltask_from_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task.id, task.name, task.goal, task.detail, task.deadline, task.task_type, status.name, task.waiting_task, task.remind_date, task.remind_input
        FROM task 
        INNER JOIN status ON task.status_id = status.id
    """)
    task = cursor.fetchall()
    conn.close()
    return task

def get_alllabel_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT label.id, label.name, label.color, label.point
        FROM label
        INNER JOIN task2label ON task2label.label_id = label.id
        WHERE task2label.task_id = ?
    """, (task_id, ))
    labels = cursor.fetchall()
    conn.close()
    return labels

def get_alltask_by_api():
    response = requests.get(f"{SERVER_URL}/api/task/")
    if response.status_code == 200:
        print("タスクが追加されました。")
    else:
        print("タスクの追加に失敗しました。")
    return response

def add_task_to_db(task_data):
    task_name, task_goal, task_detail, task_deadline_date, task_type, status_id, waiting_task, remind_date, remind_input = task_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO task (name, goal, detail, deadline, task_type, status_id, waiting_task, remind_date, remind_input) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (task_name, task_goal, task_detail, task_deadline_date, task_type, status_id, waiting_task, remind_date, remind_input))
    last_task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_task_id

def add_subtask_to_db(parent_id, child_id, is_treed=1):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subtask (parent_id, child_id, is_treed) VALUES (?, ?, ?)", (parent_id, child_id, is_treed))
    last_subtask_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_subtask_id

def add_time_to_db(time_data):
    start_time, end_time, duration, task_id = time_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO time (start_time, end_time, duration, task_id) VALUES (?, ?, ?, ?)", (start_time, end_time, duration, task_id))
    last_time_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_time_id

def delete_time_from_db(id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM time WHERE id = {id}")
    conn.commit()
    conn.close()

def update_task_in_db(task):
    task_id, task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input = task
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE task 
        SET name = ?, goal = ?, detail = ?, deadline = ?, task_type = ?, status_id = ?, waiting_task = ?, remind_date = ?, remind_input = ?
        WHERE id = ?
    """, (task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input, task_id))
    conn.commit()
    conn.close()
    return task_id

def update_time_in_db(time):
    time_id, start_time, end_time, duration, task_id = time
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE time 
        SET start_time = ?, end_time = ?, duration = ?, task_id = ?
        WHERE id = ?
    """, (start_time, end_time, duration, task_id, time_id))
    conn.commit()
    conn.close()
    return time_id

def update_subtask_in_db(subtask_id, parent_id, child_id, is_treed):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE subtask 
        SET parent_id = ?, child_id = ?, is_treed = ?
        WHERE id = ?
    """, (parent_id, child_id, is_treed, subtask_id))
    conn.commit()
    conn.close()
    return subtask_id

def delete_task_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM task WHERE id = {task_id}")
    conn.commit()
    conn.close()
    return task_id

def delete_subtask_from_db(subtask_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM subtask WHERE id = {subtask_id}")
    conn.commit()
    conn.close()
    return subtask_id

def delete_label_from_db(label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM label WHERE id = {label_id}")
    conn.commit()
    conn.close()
    all_task2labels = get_alltask2label_from_db()
    for task2label_id, _, source_label_id in all_task2labels:
        if label_id == source_label_id:
            delete_task2label_from_db(task2label_id)

def get_status_from_db(id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM status WHERE id = {id}")
    status = cursor.fetchone()
    conn.close()
    return status

def get_status_by_name_from_db(name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM status WHERE name = ?", (name, ))
    status = cursor.fetchone()
    conn.close()
    return status

def get_allstatus_form_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM status")
    all_status = cursor.fetchall()
    conn.close()
    return all_status

def get_label_by_name_from_db(label_name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM label WHERE name = ?", (label_name, ))
    label = cursor.fetchone()
    conn.close()
    return label

def get_label_by_task2labelid_from_db(task2label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT label.id, label.name, label.color, label.point
        FROM task2label
        INNER JOIN label ON task2label.label_id = label.id
        WHERE task2label.id = ?
    """, (task2label_id, ))
    label = cursor.fetchone()
    conn.close()
    return label

def get_task2label_from_db(task2label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task2label.id, label.id, label.name, label.color, label.point
        FROM task2label
        INNER JOIN label ON task2label.label_id = label.id
        WHERE task2label.id = ?
    """, (task2label_id, ))
    task2label = cursor.fetchall()
    conn.close()
    return task2label

def get_task2label_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task2label.id, label.id, label.name, label.color, label.point
        FROM task2label
        INNER JOIN label ON task2label.label_id = label.id
        WHERE task2label.task_id = ?
    """, (task_id, ))
    task2label = cursor.fetchall()
    conn.close()
    return task2label

def get_task2label_by_labelid_from_db(label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task2label.id
        FROM task2label
        INNER JOIN label ON task2label.label_id = label.id
        WHERE task2label.label_id = ?
    """, (label_id, ))
    task2label = cursor.fetchall()
    conn.close()
    return task2label

def get_time_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, start_time, end_time, duration FROM time WHERE time.task_id = ?", (task_id, ))
    time_data = cursor.fetchall()
    conn.close()
    return time_data

def get_alltask2label_from_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task2label")
    all_task2label = cursor.fetchall()
    conn.close()
    return all_task2label

def get_alltime_from_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM time")
    all_time = cursor.fetchall()
    conn.close()
    return all_time

def get_alllabel_from_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM label")
    all_label = cursor.fetchall()
    conn.close()
    return all_label

def get_label2task_from_db(label_name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task2label.id, task2label.task_id, task2label.label_id
        FROM task2label
        INNER JOIN label ON task2label.label_id = label.id
        WHERE label.name = ?
    """, (label_name, ))
    status = cursor.fetchall()
    conn.close()
    return status

def add_label_to_db(name, color, point=0):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO label (name, color, point) VALUES (?, ?, ?)", (name, color, point))
    last_task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_task_id

def delete_label_in_db(id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM label WHERE id = {id}")
    conn.commit()
    conn.close()

def delete_task2label_from_db(task2label_id):
    label_id, _, _, _ = get_label_by_task2labelid_from_db(task2label_id)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM task2label WHERE id = {task2label_id}")
    conn.commit()
    conn.close()

    task2label_ids = get_task2label_by_labelid_from_db(label_id)
    if len(task2label_ids) == 0:
        delete_label_in_db(label_id)

def delete_task2label_by_labelname_from_db(label_name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM task2label
        WHERE label_id IN (
            SELECT id FROM label WHERE name = ?
        )
    """, (label_name,))
    conn.commit()
    conn.close()

def add_task2label_in_db(task_id, label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO task2label (task_id, label_id) VALUES (?, ?)", (task_id, label_id))
    last_task2label_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_task2label_id

def add_task_to_db_by_api(task_data):
    task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input = task_data
    payload = {
        "name": task_name,
        "goal": task_goal,
        "detail": task_detail,
        "deadline": task_deadline,
        "task_type": task_type,
        "status_id": status_id,
        "waiting_task": waiting_task,
        "remind_date": remind_date,
        "remind_input": remind_input
    }
    result = None
    try:
        response = requests.post(f"{SERVER_URL}/api/task", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            result = {"type": "server", "taskId": response_data["taskId"]}
    except:
        task_id = add_task_to_db(task_data)
        result = {"type": "local", "taskId": task_id}
    return result
   
def add_subtask_to_db_by_api(parent_id, child_id, is_treed=1):
    payload = {
        "parent_id": parent_id,
        "child_id": child_id,
        "is_treed": is_treed,
    }
    result = None
    try:
        response = requests.post(f"{SERVER_URL}/api/subtask", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            result = {"type": "server", "subtaskId": response_data["subtaskId"]}
        else:
            subtask_id = add_subtask_to_db(parent_id, child_id, is_treed)
            result = {"type": "local", "subtaskId": subtask_id}
    except:
        subtask_id = add_subtask_to_db(parent_id, child_id, is_treed)
        result = {"type": "local", "subtaskId": subtask_id}
    return result

def update_task_in_db_by_api(task_data):
    task_id, task_name, task_goal, task_detail, task_deadline, task_type, status_id, waiting_task, remind_date, remind_input = task_data
    payload = {
        "name": task_name,
        "goal": task_goal,
        "detail": task_detail,
        "deadline": task_deadline,
        "task_type": task_type,
        "status_id": status_id,
        "waiting_task": waiting_task,
        "remind_date": remind_date,
        "remind_input": remind_input,
    }
    result = None
    try:
        response = requests.patch(f"{SERVER_URL}/api/task/{task_id}", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            result = {"type": "server", "taskId": response_data["taskId"]}
    except:
        task_id = update_task_in_db(task_data)
        result = {"type": "local", "taskId": task_id}
    return result

def update_subtask_in_db_by_api(subtask_id, parent_id, child_id, is_treed):
    payload = {
        "parent_id": parent_id,
        "child_id": child_id,
        "is_treed": is_treed,
    }
    result = None
    try:
        response = requests.patch(f"{SERVER_URL}/api/subtask/{subtask_id}", json=payload)
        if response.status_code == 200:
            result = {"type": "server", "subtaskId": subtask_id}
        else:
            subtask_id = update_subtask_in_db(subtask_id, parent_id, child_id, is_treed)
            result = {"type": "local", "subtaskId": subtask_id}
    except:
        subtask_id = update_subtask_in_db(subtask_id, parent_id, child_id, is_treed)
        result = {"type": "local", "subtaskId": subtask_id}
    return result

def delete_task_from_db_by_api(task_id):
    result = None
    try:
        response = requests.delete(f"{SERVER_URL}/api/task/{task_id}")
        if response.status_code == 200:
            result = {"type": "server", "taskId": response["taskId"]}
    except:
        task_id = delete_task_from_db(task_id)
        result = {"type": "local", "taskId": task_id}

    subtask_data = get_subtask_by_parentid_from_db(task_id)
    for (subtask_id, _, _, _) in subtask_data:
        delete_subtask_from_db_by_api(subtask_id)
    subtask_data = get_subtask_by_childid_from_db(task_id)
    if subtask_data:
        (subtask_id, _, _, _) = subtask_data
        delete_subtask_from_db_by_api(subtask_id)
    all_task2labels = get_task2label_by_taskid_from_db(task_id)
    for task2label_id, _, _, _, _ in all_task2labels:
        delete_task2label_from_db(task2label_id)
    all_time = get_time_by_taskid_from_db(task_id)
    for time_id, _, _, _ in all_time:
        delete_time_from_db(time_id)
    pin_id, _, _ = get_pin_by_taskid_from_db(task_id)
    delete_pin_task_in_db(pin_id)
    return result

def get_allsubtask_from_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subtask")
    all_subtask = cursor.fetchall()
    conn.close()
    return all_subtask

def get_subtask_from_db(subtask_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM subtask 
        WHERE subtask.id = ?
    """, (subtask_id,))
    subtask = cursor.fetchone()
    conn.close()
    return subtask

def get_subtask_by_parentid_and_childid_from_db(parent_id, child_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM subtask 
        WHERE subtask.parent_id = ? AND subtask.child_id = ?
    """, (parent_id, child_id, ))
    subtask_id = cursor.fetchone()
    conn.close()
    return subtask_id

def get_subtask_by_parentid_from_db(parent_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM subtask 
        WHERE subtask.parent_id = ?
    """, (parent_id, ))
    subtask = cursor.fetchall()
    conn.close()
    return subtask

def get_subtask_by_childid_from_db(child_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM subtask 
        WHERE subtask.child_id = ?
    """, (child_id, ))
    subtask = cursor.fetchone()
    conn.close()
    return subtask

def delete_subtask_from_db_by_api(subtask_id):
    try:
        response = requests.delete(f"{SERVER_URL}/api/subtask/{subtask_id}")
        if response.status_code == 200:
            result = {"type": "server", "subtaskId": response["subtaskId"]}
        else:
            subtask_id = delete_subtask_from_db(subtask_id)
            result = {"type": "local", "subtaskId": subtask_id}
    except:
        subtask_id = delete_subtask_from_db(subtask_id)
        result = {"type": "local", "subtaskId": subtask_id}
    return result

def delete_subtask_by_parentid_and_childid_from_db_by_api(parent_id, child_id):
    subtask_id, _, _, _ = get_subtask_by_parentid_and_childid_from_db(parent_id, child_id)
    payload = {
        "parent_id": parent_id,
        "child_id": child_id,
    }
    if subtask_id:
        try:
            response = requests.delete(f"{SERVER_URL}/api/subtask/{subtask_id}", json=payload)
            if response.status_code == 200:
                result = {"type": "server", "subtaskId": response["subtaskId"]}
            else:
                subtask_id = delete_subtask_from_db(subtask_id)
                result = {"type": "local", "subtaskId": subtask_id}
        except:
            subtask_id = delete_subtask_from_db(subtask_id)
            result = {"type": "local", "subtaskId": subtask_id}
    return result

def delete_subtask_by_parentid_from_db_by_api(parent_id):
    subtask_id, _, child_id, _ = get_subtask_by_parentid_from_db(parent_id)
    payload = {
        "parent_id": parent_id,
        "child_id": child_id,
    }
    if subtask_id:
        try:
            response = requests.delete(f"{SERVER_URL}/api/subtask/{subtask_id}", json=payload)
            if response.status_code == 200:
                result = {"type": "server", "subtaskId": response["subtaskId"]}
            else:
                subtask_id = delete_subtask_from_db(subtask_id)
                result = {"type": "local", "subtaskId": subtask_id}
        except:
            subtask_id = delete_subtask_from_db(subtask_id)
            result = {"type": "local", "subtaskId": subtask_id}
    return result

def add_time_to_db_by_api(time_data):
    start_time, end_time, duration, task_id = time_data
    payload = {
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "task_id": task_id
    }
    result = None
    try:
        response = requests.post(f"{SERVER_URL}/api/time", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            result = {"type": "server", "timeId": response_data["timeId"]}
    except:
        time_id = add_time_to_db(time_data)
        result = {"type": "local", "timeId": time_id}
    return result
   
def update_time_in_db_by_api(time_data):
    time_id, start_time, end_time, duration, task_id = time_data
    payload = {
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "task_id": task_id,
    }
    result = None
    try:
        response = requests.patch(f"{SERVER_URL}/api/time/{time_id}", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            result = {"type": "server", "timeId": response_data["timeId"]}
    except:
        time_id = update_time_in_db(time_data)
        result = {"type": "local", "timeId": time_id}
    return result

def delete_time_from_db_by_api(time_id):
    result = None
    try:
        response = requests.delete(f"{SERVER_URL}/api/time/{time_id}")
        if response.status_code == 200:
            result = {"type": "server", "timeId": response["timeId"]}
    except:
        time_id = delete_task_from_db(time_id)
        result = {"type": "local", "timeId": time_id}
    return result

def count_weekdays(start_date, end_date):
    weekdays = []
    while start_date < end_date:
        if (start_date.weekday() <= 5) and (not jpholiday.is_holiday(start_date)):
            weekdays.append(start_date)
        start_date += datetime.timedelta(days=1)
    return len(weekdays)
