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

const MAX_TIMEOUT = 2 ** 31 - 1;
const reminder = {};
function set_reminder(task_id, name, time, message) {
    if (!time) return;
    const reminderTime = Date.parse(time);
    const now = Date.now();
    const timeout = reminderTime - now;
    if (timeout < 0 || MAX_TIMEOUT <= timeout) {
        return;
    }
    if (task_id in reminder) {
        clear_reminder(task_id);
    }
    const timerId = setTimeout(() => {
        sio.emit('notification', {name, message});
    }, timeout);
    reminder[task_id] = timerId;
}

function clear_reminder(task_id) {
    if (task_id in reminder) {
        clearTimeout(reminder[task_id]);
        delete reminder[task_id];
    }
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
        return res.status(401).json({ message: "The task doesn't exist"});
    }
});

app.post('/api/task', (req, res) => {
    const { name, goal, detail,  deadline, task_type, status_id, waiting_task, remind_date, remind_input } = req.body;
    db.serialize(() => {
        db.run('insert into task (name, goal, detail, deadline, task_type, status_id, waiting_task, remind_date, remind_input) values (?, ?, ?, ?, ?, ?, ?, ?, ?)',  [name, goal, detail, deadline, task_type, status_id, waiting_task, remind_date, remind_input], function(err) {
            if (err) {
                return res.status(401);
            }
            const taskId = this.lastID;
            if (remind_date) {
                set_reminder(taskId, name, remind_date, remind_input);
            }
            db.get('select name from status where id = ?', [status_id], (err, row) => {
                if (err) {
                    return res.status(401);
                }
                const status_name = row["name"];
                sio.emit('post_task', {taskId, name, goal, detail, deadline, task_type, status_name, waiting_task, remind_date, remind_input});
                return res.status(200).json({ taskId: taskId });
            });
        });
    });
});

app.patch('/api/task/:id', async (req, res) => {
    const taskId = parseInt(req.params.id);
    const { name, goal, detail, deadline, task_type, status_id, waiting_task, remind_date, remind_input } = req.body;
    if (!name) {
        return res.status(400).json({ message: 'タスクを正しく指定してください。' });
    }
    try {
        await dbGet('update task set name = ?, goal = ?, detail = ?, deadline = ?,  task_type = ?, status_id = ?, waiting_task = ?, remind_date = ?, remind_input = ? where id = ?',  name, goal, detail, deadline, task_type, status_id, waiting_task, remind_date, remind_input, taskId);
        const status = await dbGet(`select name from status where id = ?`, status_id);
        const status_name = status["name"]
        if (status_name == "DONE") {
            clear_reminder(taskId, remind_date);
        }
        else {
            set_reminder(taskId, name, remind_date, remind_input);
        }
        sio.emit('update_task', taskId, { name, goal, detail, deadline, task_type, status_name, waiting_task, remind_date, remind_input });
        return res.status(200).json({ taskId: taskId });
    } catch (error) {
        console.log(error);
        return res.status(401).json({ message: "An error occurred", error });
    }
});

app.delete('/api/task/:id', async (req, res) => {
    const taskId = parseInt(req.params.id);

    try {
        const task_data = await dbGet(
            `select task.id, task.name, task.goal, task.detail, task.deadline, task.task_type, task.status_id, task.waiting_task, task.remind_date, task.remind_input
             from task
             where task.id = ?`,
             taskId
        );
        if (!task_data) {
            return res.status(400).json({ message: "The task doesn't exist" });
        }
        if (taskId in reminder) {
            clear_reminder(taskId);
        }
        await dbRun('delete from task where id = ?', taskId);
        sio.emit('delete_task', taskId);
        return res.status(200).json({ deletedTask: taskId });
    } catch (error) {
        return res.status(401).json({ message: "An error occurred", error });
    }
});

app.post('/api/subtask', (req, res) => {
    const { parent_id, child_id, is_treed } = req.body;
    db.serialize(() => {
        db.run('insert into subtask (parent_id, child_id, is_treed) values (?, ?, ?)',  [parent_id, child_id, is_treed], function(err) {
            if (err) {
                return res.status(401).json({ message: "An error occurred", err });
            }
            const subtask_id = this.lastID;
            sio.emit('post_subtask', subtask_id, req.body);
            return res.status(200).json({ subtaskId: subtask_id });
        });
    });
});

app.patch('/api/subtask/:id', async (req, res) => {
    const subtask_id = parseInt(req.params.id);
    const { parent_id, child_id, is_treed } = req.body;
    try {
        await dbGet('update subtask set parent_id = ?, child_id = ?, is_treed = ? where id = ?',  parent_id, child_id, is_treed, subtask_id);
        sio.emit('update_subtask', subtask_id, req.body);
        return res.status(200).json({ subtaskId: subtask_id });
    } catch (error) {
        return res.status(401).json({ message: "An error occurred", error });
    }
});

app.delete('/api/subtask/:id', async (req, res) => {
    const subtask_id = parseInt(req.params.id);
    try {
        const subtask = await dbGet("select * from subtask where id = ?", subtask_id);
        await dbRun('delete from subtask where id = ?', subtask_id);
        sio.emit('delete_subtask', subtask_id, subtask);
        return res.status(200).json({ subtaskId: subtask_id });
    } catch (error) {
        return res.status(401).json({ message: "An error occurred", error });
    }
});

app.post('/api/time', (req, res) => {
    const { start_time, end_time, duration, task_id } = req.body;
    db.serialize(() => {
        db.run('insert into time (start_time, end_time, duration, task_id) values (?, ?, ?, ?)',  [start_time, end_time, duration, task_id], function(err) {
            if (err) {
                return res.status(401);
            }
            const timeId = this.lastID;
            sio.emit('post_time', timeId, req.body);
            return res.status(200).json({ timeId: timeId });
        });
    });
});

app.patch('/api/time/:id', async (req, res) => {
    const timeId = parseInt(req.params.id);
    const { start_time, end_time, duration, task_id } = req.body;
    try {
        await dbGet('update time set start_time = ?, end_time = ?, duration = ?,  task_id = ? where id = ?',  start_time, end_time, duration, task_id, timeId);
        sio.emit('update_time', task_id, req.body);
        return res.status(200).json({ timeId: timeId });
    } catch (error) {
        console.log(error);
        return res.status(401).json({ message: "An error occurred", error });
    }
});

app.delete('/api/time/:id', async (req, res) => {
    const timeId = parseInt(req.params.id);
    try {
        await dbRun('delete from time where id = ?', timeId);
        sio.emit('delete_time', timeId);
        return res.status(200).json({ deletedTask: timeId });
    } catch (error) {
        return res.status(401).json({ message: "An error occurred", error });
    }
});

sio.on('connection', (socket) => {
    socket.on('disconnect', () => {
        console.log('User disconnected:', socket.id);
    });
});

async function init_task_reminder() {
    try {
        const tasks = await dbAll(
            `select task.id, task.name, status.name as status_name, task.waiting_task, task.remind_date, task.remind_input
            from task
            INNER JOIN status ON task.status_id = status.id
            `
        );
        for (const task of tasks) {
            const taskId = task.id;
            const task_name = task.name;
            const status_name = task.status_name;
            const date = task.remind_date;
            const message = task.remind_input;
            if (date && status_name !== "DONE") {
                set_reminder(taskId, task_name, date, message);
            }
        }
    } catch (error) {
        console.log("An error occurred", error);
    }
}

server.listen(port, async() => {
    await init_task_reminder();
    console.log(`Server is running at http://localhost:${port}`);
});
