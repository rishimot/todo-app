import sqlite3
import random
import requests
import winreg
import datetime
import jpholiday

def generate_random_color():
    r = random.randint(70, 255)
    g = random.randint(70, 255)
    b = random.randint(70, 255)
    return f"#{r:02x}{g:02x}{b:02x}"

def get_task_from_db(task_id):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task.name, task.goal, task.detail, task.deadline, task.is_weekly_task, status.name, task.waiting_task
        FROM task 
        INNER JOIN status ON task.status_id = status.id
        WHERE task.id = ?
    """, (task_id, ))
    task = cursor.fetchone()
    conn.close()
    return task


def get_alltask_from_db():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task.id, task.name, task.goal, task.detail, task.deadline, is_weekly_task, status.name, waiting_task
        FROM task 
        INNER JOIN status ON task.status_id = status.id
    """)
    task = cursor.fetchall()
    conn.close()
    return task

def get_alltask_to_api():
    response = requests.get("http://localhost:3000/api/task/")
    if response.status_code == 200:
        print("タスクが追加されました。")
    else:
        print("タスクの追加に失敗しました。")
    return response

def add_task_to_db(task):
    task_name, task_goal, task_detail, task_deadline_date, is_weekly_task, status_id, waiting_task = task
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO task (name, goal, detail, deadline, is_weekly_task, status_id, waiting_task) VALUES (?, ?, ?, ?, ?, ?, ?)", (task_name, task_goal, task_detail, task_deadline_date, is_weekly_task, status_id, waiting_task))
    last_task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_task_id

def add_time_to_db(time_data):
    start_time, end_time, duration, task_id = time_data
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO time (start_time, end_time, task_id) VALUES (?, ?, ?)", (start_time, end_time, task_id))
    last_time_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_time_id

def update_task_in_db(task):
    task_id, task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_id, waiting_task = task
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE task 
        SET name = ?, goal = ?, detail = ?, deadline = ?, is_weekly_task = ?, status_id = ?, waiting_task = ?
        WHERE id = ?
    """, (task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_id, waiting_task, task_id))
    conn.commit()
    conn.close()


def delete_task_from_db(task_id):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM task WHERE id = {task_id}")
    conn.commit()
    conn.close()

def delete_label_from_db(label_id):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM label WHERE id = {label_id}")
    conn.commit()
    conn.close()

def get_status_by_id_from_db(id):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM status WHERE id = {id}")
    status = cursor.fetchone()
    conn.close()
    return status

def get_status_by_name_from_db(name):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM status WHERE name = ?", (name, ))
    status = cursor.fetchone()
    conn.close()
    return status

def get_allstatus_form_db():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM status")
    all_status = cursor.fetchall()
    conn.close()
    return all_status

def get_label_by_name_from_db(name):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM label WHERE name = ?", (name, ))
    label = cursor.fetchone()
    conn.close()
    return label

def get_task2label_from_db(task_id):
    conn = sqlite3.connect('todo.db')
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

def get_alltask2label_from_db():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task2label")
    all_task2label = cursor.fetchall()
    conn.close()
    return all_task2label

def get_alllabel_from_db():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM label")
    all_label = cursor.fetchall()
    conn.close()
    return all_label

def get_label2task_from_db(label_name):
    conn = sqlite3.connect('todo.db')
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
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO label (name, color, point) VALUES (?, ?, ?)", (name, color, point))
    last_task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_task_id

def delete_label_in_db(id):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM label WHERE id = {id}")
    conn.commit()
    conn.close()

def delete_task2label_from_db(id):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM task2label WHERE id = {id}")
    conn.commit()
    conn.close()


def add_task2label_in_db(task_id, label_id):
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO task2label (task_id, label_id) VALUES (?, ?)", (task_id, label_id))
    last_task2label_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_task2label_id


SERVER_URL = 'http://localhost:3000/'
def get_task_from_db_by_api(task_id):
    response = requests.get(f"{SERVER_URL}/api/task/{task_id}")
    if response.status_code == 200:
        task_data = response.json()
        return {
            task_data.name,
            task_data.goal,
            task_data.is_weekly_task,
            task_data.detail,
            task_data.deadline,
            task_data.status_id,
            task_data.waiting_task,
        }

def add_task_to_db_by_api(task_data):
    task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_id, waiting_task = task_data
    payload = {
        "name": task_name,
        "goal": task_goal,
        "detail": task_detail,
        "is_weekly_task": is_weekly_task,
        "deadline": task_deadline,
        "status_id": status_id,
        "waiting_task": waiting_task
    }
    response = requests.post(f"{SERVER_URL}/api/task", json=payload)
    if response.status_code == 200:
        response_data = response.json()
        return response_data["taskId"]
    return None
   

def update_task_in_db_by_api(task_data, new_label_id=[]):
    task_id, task_name, task_goal, task_detail, task_deadline, is_weekly_task, status_id, waiting_task = task_data
    payload = {
        "name": task_name,
        "goal": task_goal,
        "detail": task_detail,
        "is_weekly_task": is_weekly_task,
        "deadline": task_deadline,
        "status_id": status_id,
        "waiting_task": waiting_task,
        "newlabel_id": new_label_id,
    }
    response = requests.patch(f"{SERVER_URL}/api/task/{task_id}", json=payload)
    if response.status_code == 200:
        response_data = response.json()
        return response_data["taskId"]
    return None

def delete_task_from_db_by_api(task_id):
    response = requests.delete(f"{SERVER_URL}/api/task/{task_id}")
    if response.status_code == 200:
        return task_id
    return None

def count_weekdays(start_date, end_date):
    weekdays = []
    while start_date < end_date:
        start_date += datetime.timedelta(days=1)
        if (start_date.weekday() <= 5) and (not jpholiday.is_holiday(start_date)):
            weekdays.append(start_date)
    return len(weekdays)
