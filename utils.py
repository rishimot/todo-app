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
    cursor.execute("SELECT id, task_id, is_marked FROM mark_task WHERE task_id = ?", (task_id, ))
    mark_data = cursor.fetchone()
    if not mark_data:
        mark_id = add_mark_task_to_db((task_id, False))
        mark_data = (mark_id, task_id, False)
    conn.close()
    return mark_data

def get_mark_by_actionid_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, action_id, is_marked FROM mark_action WHERE action_id = ?", (action_id, ))
    mark_data = cursor.fetchone()
    if not mark_data:
        mark_id = add_mark_action_to_db((action_id, False))
        mark_data = (mark_id, action_id, False)
    conn.close()
    return mark_data

def add_mark_task_to_db(mark_data):
    task_id, is_marked = mark_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mark_task ( task_id, is_marked ) VALUES (?, ?)", (task_id, is_marked))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id

def add_mark_action_to_db(mark_data):
    action_id, is_marked = mark_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mark_action ( action_id, is_marked ) VALUES (?, ?)", (action_id, is_marked))
    last_mark_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_mark_id

def update_mark_task_to_db(mark_data):
    mark_id, task_id, is_marked = mark_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mark_task 
        SET task_id = ?, is_marked = ?
        WHERE id = ?
    """, (task_id, is_marked, mark_id))
    last_mark_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_mark_id

def update_mark_action_to_db(mark_data):
    mark_id, action_id, is_marked = mark_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mark_action 
        SET action_id = ?, is_marked = ?
        WHERE id = ?
    """, (action_id, is_marked, mark_id))
    last_mark_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_mark_id

def get_pin_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_id, is_pinned FROM pin_task WHERE task_id = ?", (task_id, ))
    pin_data = cursor.fetchone()
    if not pin_data:
        pin_id = add_pin_task_to_db((task_id, False))
        pin_data = (pin_id, task_id, False)
    conn.close()
    return pin_data

def get_pin_by_actionid_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, action_id, is_pinned FROM pin_action WHERE action_id = ?", (action_id, ))
    pin_data = cursor.fetchone()
    if not pin_data:
        pin_id = add_pin_action_to_db((action_id, False))
        pin_data = (pin_id, action_id, False)
    conn.close()
    return pin_data

def add_pin_task_to_db(pin_data):
    task_id, is_pinned = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pin_task ( task_id, is_pinned ) VALUES (?, ?)", (task_id, is_pinned))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id

def add_pin_action_to_db(pin_data):
    action_id, is_pinned = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pin_action ( action_id, is_pinned ) VALUES (?, ?)", (action_id, is_pinned))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id

def update_pin_task_to_db(pin_data):
    pin_id, task_id, is_pinned = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pin_task 
        SET task_id = ?, is_pinned = ?
        WHERE id = ?
    """, (task_id, is_pinned, pin_id))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id

def update_pin_action_to_db(pin_data):
    pin_id, action_id, is_pinned = pin_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pin_action 
        SET action_id = ?, is_pinned = ?
        WHERE id = ?
    """, (action_id, is_pinned, pin_id))
    last_pin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_pin_id

def delete_pin_task_in_db(pin_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM pin_task WHERE id = {pin_id}")
    conn.commit()
    conn.close()

def delete_pin_action_in_db(pin_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM pin_action WHERE id = {pin_id}")
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

def get_action_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action.name, action.goal, action.detail, action.deadline, action.action_type, status.name, action.waiting_action, action.remind_date, action.remind_input, action.task_id
        FROM action 
        INNER JOIN status ON action.status_id = status.id
        WHERE action.id = ?
    """, (action_id, ))
    action = cursor.fetchone()
    conn.close()
    return action

def get_allaction_by_taskid_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action.id, action.name, action.goal, action.detail, action.deadline, action.action_type, status.name, action.waiting_action, action.remind_date, action.remind_input, action.task_id
        FROM action 
        INNER JOIN status ON action.status_id = status.id
        WHERE action.task_id = ?
    """, (task_id, ))
    action = cursor.fetchall()
    conn.close()
    return action

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

def get_alllabel_by_actionid_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT label.id, label.name, label.color, label.point
        FROM label
        INNER JOIN action2label ON action2label.label_id = label.id
        WHERE action2label.action_id = ?
    """, (action_id, ))
    labels = cursor.fetchall()
    conn.close()
    return labels

def get_allaction_from_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action.id, action.name, action.goal, action.detail, action.deadline, action.action_type, status.name, action.waiting_action, action.remind_date, action.remind_input, action.task_id
        FROM action
        INNER JOIN status ON action.status_id = status.id
    """)
    actions = cursor.fetchall()
    conn.close()
    return actions

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

def add_action_to_db(action_data):
    action_name, action_goal, action_detail, action_deadline_date, action_type, status_id, waiting_action, remind_date, remind_input, task_id = action_data
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO action (name, goal, detail, deadline, action_type, status_id, waiting_action, remind_date, remind_input, task_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (action_name, action_goal, action_detail, action_deadline_date, action_type, status_id, waiting_action, remind_date, remind_input, task_id))
    last_action_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_action_id

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

def update_action_in_db(action):
    action_id, action_name, action_goal, action_detail, action_deadline, action_type, status_id, waiting_action, remind_date, remind_input = action
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE action 
        SET name = ?, goal = ?, detail = ?, deadline = ?, action_type = ?, status_id = ?, waiting_action = ?, remind_date = ?, remind_input = ?
        WHERE id = ?
    """, (action_name, action_goal, action_detail, action_deadline, action_type, status_id, waiting_action, remind_date, remind_input, action_id))
    conn.commit()
    conn.close()
    return action_id

def delete_task_from_db(task_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM task WHERE id = {task_id}")
    conn.commit()
    conn.close()
    return task_id

def delete_action_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM action WHERE id = {action_id}")
    conn.commit()
    conn.close()
    return action_id

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

def get_action2label_by_actionid_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action2label.id, label.id, label.name, label.color, label.point
        FROM action2label
        INNER JOIN label ON action2label.label_id = label.id
        WHERE action2label.action_id = ?
    """, (action_id))
    action2label = cursor.fetchall()
    conn.close()
    return action2label

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

def get_action2label_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action2label.id, action2label.action_id, actio2label.label_id
        FROM action2label
        WHERE action2label.action_id = ?
    """, (action_id, ))
    action2labels = cursor.fetchall()
    conn.close()
    return action2labels

def get_action2label_by_actionid_from_db(action_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action2label.id, label.id, label.name, label.color, label.point
        FROM action2label
        INNER JOIN label ON action2label.label_id = label.id
        WHERE action2label.action_id = ?
    """, (action_id, ))
    action2label = cursor.fetchall()
    conn.close()
    return action2label

def get_action2label_by_labelid_from_db(label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action2label.id
        FROM action2label
        INNER JOIN label ON action2label.label_id = label.id
        WHERE action2label.label_id = ?
    """, (label_id, ))
    action2label = cursor.fetchall()
    conn.close()
    return action2label

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

def delete_action2label_by_labelname_from_db(label_name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM action2label
        WHERE label_id IN (
            SELECT id FROM label WHERE name = ?
        )
    """, (label_name,))
    conn.commit()
    conn.close()

def delete_action2label_from_db(action2label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM action2label WHERE id = {action2label_id}")
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

def add_action2label_in_db(action_id, label_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO action2label (action_id, label_id) VALUES (?, ?)", (action_id, label_id))
    last_action2label_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_action2label_id

def get_task_from_db_by_api(task_id):
    response = requests.get(f"{SERVER_URL}/api/task/{task_id}")
    if response.status_code == 200:
        task_data = response.json()
        return {
            task_data.name,
            task_data.goal,
            task_data.task_type,
            task_data.detail,
            task_data.deadline,
            task_data.status_id,
            task_data.waiting_task,
            task_data.remind_date,
            task_data.remind_input,
        }

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
   
def add_action_to_db_by_api(action_data):
    action_name, action_goal, action_detail, action_deadline, action_type, status_id, waiting_action, remind_date, remind_input, task_id = action_data
    payload = {
        "name": action_name,
        "goal": action_goal,
        "detail": action_detail,
        "deadline": action_deadline,
        "action_type": action_type,
        "status_id": status_id,
        "waiting_action": waiting_action,
        "remind_date": remind_date,
        "remind_input": remind_input,
        "task_id": task_id
    }
    result = None
    try:
        response = requests.post(f"{SERVER_URL}/api/action", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            result = {"type": "server", "actionId": response_data["actionId"]}
    except:
        action_id = add_action_to_db(action_data)
        result = {"type": "local", "actionId": action_id}
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

def update_action_in_db_by_api(action_data):
    action_id, action_name, action_goal, action_detail, action_deadline, action_type, status_id, waiting_action, remind_date, remind_input, task_id = action_data
    payload = {
        "name": action_name,
        "goal": action_goal,
        "detail": action_detail,
        "deadline": action_deadline,
        "action_type": action_type,
        "status_id": status_id,
        "waiting_action": waiting_action,
        "remind_date": remind_date,
        "remind_input": remind_input,
        "task_id": task_id,
    }
    result = None
    try:
        response = requests.patch(f"{SERVER_URL}/api/action/{action_id}", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            result = {"type": "server", "actionId": response_data["actionId"]}
    except:
        action_id = update_action_in_db(action_data)
        result = {"type": "local", "actionId": action_id}
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

    all_task2labels = get_task2label_by_taskid_from_db(task_id)
    for task2label_id, _, _, _, _ in all_task2labels:
        delete_task2label_from_db(task2label_id)
    all_actions = get_allaction_by_taskid_from_db(task_id)
    for (action_id, _, _, _, _, _, _, _, _, _, _) in all_actions:
        delete_action_from_db_by_api(action_id)
    all_time = get_time_by_taskid_from_db(task_id)
    for time_id, _, _, _ in all_time:
        delete_time_from_db(time_id)
    pin_id, _, _ = get_pin_by_taskid_from_db(task_id)
    delete_pin_task_in_db(pin_id)
    return result

def delete_action_from_db_by_api(action_id):
    _, _, _, _, _, _, _, _, _, task_id = get_action_from_db(action_id)
    result = None
    try:
        response = requests.delete(f"{SERVER_URL}/api/action/{action_id}")
        if response.status_code == 200:
            result = {"type": "server", "actionId": response["actionId"]}
    except:
        action_id = delete_action_from_db(action_id)
        result = {"type": "local", "actionId": action_id}

    all_task2labels = get_action2label_by_actionid_from_db(action_id)
    for action2label_id, _, _, _, _ in all_task2labels:
        delete_action2label_from_db(action2label_id)
    all_time = get_time_by_taskid_from_db(task_id)
    for time_id, _, _, _ in all_time:
        delete_time_from_db(time_id)
    pin_id, _, _ = get_pin_by_taskid_from_db(task_id)
    delete_pin_action_in_db(pin_id)
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
