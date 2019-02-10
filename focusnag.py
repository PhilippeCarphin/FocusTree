import subprocess
import requests
import focus
import time

if __name__ == "__main__":
    r = requests.get('http://localhost:5051/api/tree')
    server_tm = focus.TreeManager.from_dict(r.json())
    title = 'FocusTree'

    message = server_tm.current_task.print_ancestors()

    print(server_tm.print_tree())
    while True:
        time.sleep(30)
        subprocess.run(
        [
	        'osascript', '-e',
            'display alert "' + title + '" message "' + message + '"'
        ])
        r = requests.get('http://localhost:5051/api/tree')
        server_tm = focus.TreeManager.from_dict(r.json())
