import sqlite3

def create_db(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS label (
        "id"	INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL,
        "color"	TEXT NOT NULL,
        "point"	INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS status (
        "id"	INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL UNIQUE,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task (
        "id"	INTEGER NOT NULL UNIQUE,
        "name"	TEXT NOT NULL,
        "goal"	TEXT,
        "detail"	TEXT,
        "status_id"	INTEGER DEFAULT 1,
        "deadline"	TEXT,
        "waiting_task"	TEXT,
        "task_type"	TEXT NOT NULL DEFAULT '-',
        "remind_date"	TEXT,
        "remind_input"	TEXT,
        FOREIGN KEY("status_id") REFERENCES "status"("id") ON UPDATE CASCADE,
        PRIMARY KEY("id" AUTOINCREMENT))
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subtask (
        "id"	INTEGER NOT NULL UNIQUE,
        "parent_id"	INTEGER NOT NULL,
        "child_id"	INTEGER NOT NULL,
        "is_treed"	INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY("parent_id") REFERENCES "task"("id") ON DELETE CASCADE,
        FOREIGN KEY("child_id") REFERENCES "task"("id") ON DELETE CASCADE,
        PRIMARY KEY("id" AUTOINCREMENT))
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task2label (
        "id"	INTEGER NOT NULL UNIQUE,
        "task_id"	INTEGER NOT NULL,
        "label_id"	INTEGER NOT NULL,
        FOREIGN KEY("label_id") REFERENCES "label"("id") ON DELETE CASCADE,
        FOREIGN KEY("task_id") REFERENCES "task"("id") ON DELETE CASCADE,
        PRIMARY KEY("id" AUTOINCREMENT))
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS time (
        "id"	INTEGER NOT NULL UNIQUE,
        "start_time"	TEXT NOT NULL,
        "end_time"	TEXT NOT NULL,
        "duration"	INTEGER NOT NULL,
        "task_id"	INTEGER NOT NULL,
        FOREIGN KEY("task_id") REFERENCES "task"("id") ON DELETE CASCADE,
        PRIMARY KEY("id" AUTOINCREMENT))
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pin_task (
        "id"	INTEGER NOT NULL UNIQUE,
        "task_id"	INTEGER NOT NULL,
        "is_pinned"	INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY("task_id") REFERENCES "task"("id") ON DELETE CASCADE,
        PRIMARY KEY("id" AUTOINCREMENT))
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mark_task (
        "id"	INTEGER NOT NULL UNIQUE,
        "task_id"	INTEGER NOT NULL,
        "is_marked"	INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY("task_id") REFERENCES "task"("id") ON DELETE CASCADE,
        PRIMARY KEY("id" AUTOINCREMENT))
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()