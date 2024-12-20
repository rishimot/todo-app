const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3');
const path = require('path');
const { Server } = require('socket.io');
const { createServer } = require('node:http');
const util = require('util');

const deploy = true;
let database_path = "todo.db";
if (deploy) {
    database_path = path.join("dist", "todo.db");
}
const db = new sqlite3.Database(path.join(__dirname, database_path));
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
    const { name, goal, detail, deadline, is_weekly_task, status_id, waiting_task } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    db.serialize(() => {
        db.run('insert into task (name, goal, detail, deadline, is_weekly_task, status_id, waiting_task) values (?, ?, ?, ?, ?, ?, ?)',  [name, goal, detail, deadline, is_weekly_task, status_id, waiting_task], function(err) {
            if (err) {
                return res.status(400);
            }
            const taskId = this.lastID;
            sio.emit('post', taskId);
            return res.status(200).json({ taskId: taskId });
        });
    });
});

app.patch('/api/task/:id', async (req, res) => {
    const taskId = parseInt(req.params.id);
    const { name, goal, detail, deadline, is_weekly_task, status_id, waiting_task, newlabel_id } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    try {
        const old_task_data = await dbGet(
            `select task.id, task.name, task.goal, task.detail, task.deadline, task.is_weekly_task, task.status_id, task.waiting_task
            from task 
            where task.id = ?`, 
            taskId
        );
        const old_task2label_id = await dbAll(
            "select * from task2label where task_id = ?", 
            taskId
        );
        const old_task_label_id = old_task2label_id.map(elem => elem["label_id"])
        if (!old_task_label_id) {
            return res.status(402).json({ message: "The task2label doesn't exist" });
        }
        await dbGet('update task set name = ?, goal = ?, detail = ?, deadline = ?, is_weekly_task = ?, status_id = ?, waiting_task = ? where id = ?',  name, goal, detail, deadline, is_weekly_task, status_id, waiting_task, taskId);
        sio.emit('update', taskId, old_task_data, old_task_label_id, req.body, newlabel_id);
        return res.status(200).json({ taskId: taskId });
    } catch (error) {
        console.log(error);
        return res.status(400).json({ message: "An error occurred", error });
    }
});


app.delete('/api/task/:id', async (req, res) => {
    const taskId = parseInt(req.params.id);

    try {
        const task_data = await dbGet(
            `select task.id, task.name, task.goal, task.detail, task.deadline, task.is_weekly_task, task.status_id, task.waiting_task
             from task 
             where task.id = ?`, 
             taskId
        );
        if (!task_data) {
            return res.status(401).json({ message: "The task doesn't exist" });
        }
        await dbRun('delete from task where id = ?', taskId);
        sio.emit('delete', task_data);
        return res.status(200).json({ deletedTask: taskId });
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
