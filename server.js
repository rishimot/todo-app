const express = require('express');
const cors = require('cors');
const notifier = require('node-notifier');
const sqlite3 = require('sqlite3');
const path = require('path');
const { Server } = require('socket.io');
const { createServer } = require('node:http');
const util = require('util');
const fs = require('fs');

const args = process.argv;
let config_path = "./config.json";
args.forEach(arg => {
    if (arg.startsWith('--config_path=')) {
        config_path = arg.split('=')[1];
    }
});
const data = fs.readFileSync(config_path, 'utf8');
const config = JSON.parse(data);
const port = config.port || 8000; 
const database_path = config.database_path || "./todo.db";
const db = new sqlite3.Database(database_path);
const app = express();
const server = createServer(app);
const sio = new Server(server);

const dbGet = util.promisify(db.get).bind(db);
const dbAll = util.promisify(db.all).bind(db);
const dbRun = util.promisify(db.run).bind(db);

app.use(cors());
app.use(express.json());

const reminder = {};
function set_reminder(taskId, time, message) {
    if (!time) return;
    const reminderTime = Date.parse(time);
    const now = Date.now();
    const timeout = reminderTime - now;
    if (timeout < 0) {
        return;
    }
    if (taskId in reminder) {
        clearTimeout(reminder[taskId]);
    }
    const timerId = setTimeout(() => {
        notifier.notify({
            title: 'Reminder',
            message: message || 'It\'s time!',
            icon: null, 
            sound: true,
        });
    }, timeout);
    reminder[taskId] = timerId;
}

app.get('/api/task', async (req, res) => {
    try {
        const allTasks = dbAll("select * from task");
        return res.status(200).json(allTasks);
    }
    catch {
        return res.status(400);
    }
});

app.get('/api/task/:id', async(req, res) => {
    const taskId = parseInt(req.params.id);
    try {
        const task = await dbGet("select * from task where id = ?", taskId);
        return res.status(200).json(task);
    }
    catch {
        return res.status(400).json({ message: "The task doesn't exist"});
    }
});

app.post('/api/task', (req, res) => {
    const { name, goal, detail, deadline, is_weekly_task, status_id, waiting_task, remind_date, remind_input } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    db.serialize(() => {
        db.run('insert into task (name, goal, detail, deadline, is_weekly_task, status_id, waiting_task, remind_date, remind_input) values (?, ?, ?, ?, ?, ?, ?, ?, ?)',  [name, goal, detail, deadline, is_weekly_task, status_id, waiting_task, remind_date, remind_input], function(err) {
            if (err) {
                return res.status(400);
            }
            const taskId = this.lastID;
            if (remind_date) {
                set_reminder(taskId, remind_date, remind_input);
            }
            sio.emit('post', taskId);
            return res.status(200).json({ taskId: taskId });
        });
    });
});

app.patch('/api/task/:id', async (req, res) => {
    const taskId = parseInt(req.params.id);
    const { name, goal, detail, deadline, is_weekly_task, status_id, waiting_task, remind_date, remind_input, newlabel_id } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    try {
        const old_task_data = await dbGet(
            `select task.id, task.name, task.goal, task.detail, task.deadline, task.is_weekly_task, task.status_id, task.waiting_task, task.remind_date, task.remind_input
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
        set_reminder(taskId, remind_date, remind_input);
        await dbGet('update task set name = ?, goal = ?, detail = ?, deadline = ?, is_weekly_task = ?, status_id = ?, waiting_task = ?, remind_date = ?, remind_input = ? where id = ?',  name, goal, detail, deadline, is_weekly_task, status_id, waiting_task, remind_date, remind_input, taskId);
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
            `select task.id, task.name, task.goal, task.detail, task.deadline, task.is_weekly_task, task.status_id, task.waiting_task, task.remind_date, task.remind_input
             from task
             where task.id = ?`,
             taskId
        );
        if (!task_data) {
            return res.status(401).json({ message: "The task doesn't exist" });
        }
        if (taskId in reminder) {
            clearTimeout(reminder[taskId]);
            delete reminder[taskId];
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

server.listen(port, async() => {
    try {
        const tasks = await dbAll(
            `select task.id,  status.name, task.waiting_task, task.remind_date, task.remind_input
            from task
            INNER JOIN status ON task.status_id = status.id
            `
        );
        for (const task of tasks) {
            const taskId = task.id;
            const status_name = task.name;
            const date = task.remind_date;
            const message = task.remind_input;
            if (date && status_name !== "DONE") {
                set_reminder(taskId, date, message);
            }
        }
    } catch (error) {
        console.log("An error occurred", error);
    }
    console.log(`Server is running at http://localhost:${port}`);
});
