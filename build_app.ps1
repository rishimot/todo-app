# スクリプトの開始
# 仮想環境をアクティブにする
& .\venv\Scripts\Activate.ps1

# pyinstallerを実行する
pyinstaller --onefile --noconsole --icon="icon/start_button.ico" todo_app.py
pyinstaller --onefile --noconsole --icon="icon/space_rocket.ico" lancher-app.py
pyinstaller --onefile --noconsole --icon="icon/reminder-aikon.ico" reminder_app.py