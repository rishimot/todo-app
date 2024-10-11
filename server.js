const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3');
const path = require('path');

const db = new sqlite3.Database(path.join(__dirname + "todo.db"));
const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

// タスクを取得するエンドポイント
app.get('/api/tasks/:id', (req, res) => {
    const taskId = parseInt(req.params.id);
    db.serialize(() => {
        db.get("select * from tasks where id = ?", taskId, (err, rows) => {
            if (err) {
                return res.status(400).json({ message: "The task doesn't exist"});
            }
            return res.status(200).json(rows);
        });
    });
});

app.get('/api/tasks', (req, res) => {
    db.serialize(() => {
        db.all("select * from tasks", (err, rows) => {
            if (err) {
                return res.status(400);
            }
            return res.status(200).json(rows);
        });
    });
});

// タスクを追加するエンドポイント
app.post('/api/tasks', (req, res) => {
    const { name, detail } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    db.serialize(() => {
        db.run('insert into tasks (name, detail) values (?, ?)',  name, detail, (err) => {
            if (err) {
                return res.status(400);
            }
            return res.status(200).json("OK");
        });
    });
});

// タスクを削除するエンドポイント
app.delete('/api/tasks/:id', (req, res) => {
    const taskId = parseInt(req.params.id);
    db.serialize(() => {
        db.run('delete from tasks where id = ?',  taskId, (err) => {
            if (err) {
                return res.status(400);
            }
            return res.status(200).json("OK");
        });
    });
});

// タスクの状態を更新するエンドポイント
app.patch('/api/tasks/:id', (req, res) => {
    const taskId = parseInt(req.params.id);
    const { name, detail, label_id, status_id } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    db.serialize(() => {
        db.run('update tasks set name = ?, detail = ?, label_id = ?, status_id = ? where id = ?',  name, detail, label_id, status_id, taskId, (err) => {
            if (err) {
                return res.status(404).json(err);
            }
            return res.status(200).json("OK");
        });
    });

});

// サーバーの起動
app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});
