import subprocess
import requests
import focus
import time

def nag_current_task_ancestors():
    r = requests.get('http://localhost:5051/api/tree')
    server_tm = focus.TreeManager.from_dict(r.json())

    print(server_tm.print_tree())

    title = 'FocusTree'
    message = server_tm.current_task.print_ancestors()
    subprocess.run([
        'osascript',
        '-e',
        'display alert "' + title + '" message "' + message + '"'
    ])

if __name__ == "__main__":
    while True:
        time.sleep(30)
        nag_current_task_ancestors()
