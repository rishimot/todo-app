const express = require('express');
const notifier = require('node-notifier');
const sqlite3 = require('sqlite3');
const path = require('path');
const app = express();
let port = 8001;
let database_path = path.join(__dirname, "../todo.db");

const args = process.argv;
args.forEach(arg => {
    if (arg.startsWith('--dbPath=')) {
        database_path = arg.split('=')[1];
    }
    if (arg.startsWith('--port=')) {
        port = arg.split('=')[1];
    }
});
const db = new sqlite3.Database(database_path);

app.use(express.json());

const reminder = {};

function set_reminder(taskId, time, message) {
    const reminderTime = new Date(time).getTime();
    const now = Date.now();
    if (reminderTime < now) {
        return res.status(200).json({ error: 'The reminder time must be in the future.' });
    }
    const timeout = reminderTime - now;

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

app.post('/set-reminder', (req, res) => {
    const { taskId, time, message } = req.body;
    
    if (taskId in reminder) {
        clearTimeout(reminder[taskId]);
    }
    set_reminder(taskId, time, message);
    res.status(200).json({ message: 'OK' });
});

app.listen(port, () => {
    db.serialize(() => {
        db.all("select * from task", (err, rows) => {
            if (err) {
                console.log(err);
            }
            for (const task of rows) {
                const taskId = task.id
                const time = task.remind_date
                const message = task.remind_input
                db.get("select name from status where id = ?", task.status_id, (err, rows) => {
                    if (err) {
                        console.log(err);
                    }
                    const status = rows.name
                    if (time && status !== "DONE") {
                        set_reminder(taskId, time, message);
                    }
                });
            }
        });
    });
    console.log(`Server is running at http://localhost:${port}`);
});