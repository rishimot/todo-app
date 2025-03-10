$date=Get-Date -Format "yyMMdd"
$remotePath="s145053@c1x28001l:~/.backup/todo_db/todo_$date.db"

scp C:\Users\S145053\develop\todo-app\dist\todo.db $remotePath
