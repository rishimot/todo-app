const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3');
const path = require('path');
const { Server } = require('socket.io');
const { createServer } = require('node:http');
const util = require('util');

const db = new sqlite3.Database(path.join(__dirname, "todo.db"));
const app = express();
const server = createServer(app);
const sio = new Server(server);
const port = 3000;

const dbGet = util.promisify(db.get).bind(db);
const dbAll = util.promisify(db.all).bind(db);
const dbRun = util.promisify(db.run).bind(db);

app.use(cors());
app.use(express.json());

app.get('/api/task', (req, res) => {
    db.serialize(() => {
        db.all("select * from task", (err, rows) => {
            if (err) {
                return res.status(400);
            }
            return res.status(200).json(rows);
        });
    });
});

app.get('/api/task/:id', (req, res) => {
    const taskId = parseInt(req.params.id);
    db.serialize(() => {
        db.get("select * from task where id = ?", taskId, (err, rows) => {
            if (err) {
                return res.status(400).json({ message: "The task doesn't exist"});
            }
            return res.status(200).json(rows);
        });
    });
});

app.post('/api/task', (req, res) => {
    const { name, goal, detail, deadline, status_id } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    db.serialize(() => {
        db.run('insert into task (name, goal, detail, deadline, status_id) values (?, ?, ?, ?, ?)',  [name, goal, detail, deadline, status_id], function(err) {
            if (err) {
                return res.status(400);
            }
            const taskId = this.lastID;
            sio.emit('post', taskId);
            return res.status(200).json({ taskId: taskId });
        });
    });
});

app.patch('/api/task/:id', (req, res) => {
    const taskId = parseInt(req.params.id);
    const { name, goal, detail, deadline, status_id } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    db.serialize(() => {
        db.run('update task set name = ?, goal = ?, detail = ?, deadline = ?, status_id = ? where id = ?',  name, goal, detail, deadline, status_id, taskId, (err) => {
            if (err) {
                return res.status(404).json(err);
            }
            sio.emit('update', taskId);
            return res.status(200).json("OK");
        });
    });
});


app.delete('/api/task/:id', async (req, res) => {
    const taskId = parseInt(req.params.id);

    try {
        const task_data = await dbGet(
            `select task.id, task.name, task.goal, task.detail, task.deadline, status.name AS status_name
             from task 
             inner join status on task.status_id = status.id 
             where task.id = ?`, 
             taskId
        );
        if (!task_data) {
            return res.status(401).json({ message: "The task doesn't exist" });
        }

        const task2label_data = await dbAll(
            "select * from task2label where task_id = ?", 
            taskId
        );
        if (!task2label_data) {
            return res.status(402).json({ message: "The task2label doesn't exist" });
        }

        await dbRun('delete from task where id = ?', taskId);

        const labels_id = task2label_data.map(data => data.label_id);
        const response_data = { ...task_data, labels_id };
        sio.emit('delete', response_data);
        return res.status(200).json({ deletedTask: response_data });
    } catch (error) {
        console.log(error);
        return res.status(400).json({ message: "An error occurred", error });
    }
});

sio.on('connection', (socket) => {
    socket.on('disconnect', () => {
        console.log('User disconnected:', socket.id);
    });
});

server.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});
