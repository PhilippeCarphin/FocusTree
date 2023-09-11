# I attempted to make a TUI client with curses but I gave up on it because the
# it is too complicated compared to the benefit that I would be getting; the
# CLI works perfectly fine.  I could make the TUI look cool but I would have
# really hard time, I think, getting the same prompt_toolkit stuff to work.
#
# All in all, continuing this would be a waste of time.

import curses
import curses.textpad
import time
import requests
import os
import json
import culour
with open(os.path.expanduser("~/.ssh/ftserver_token")) as f:
    TOKEN = f.read().strip()
    print(TOKEN)

resp = requests.post("http://localhost:5051/api/send-command", data=json.dumps({"command": "tree", "args": "args", "token": TOKEN}))
tree = resp.json()['term_output']
print(tree)
def main(stdscr):
    stdscr.refresh()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_MAGENTA)
    # resp = requests.get("http://localhost:5051/api/send-command")
    resp = requests.post("http://localhost:5051/api/send-command", data=json.dumps({"command": "tree", "args": "args", "token": TOKEN}))
    tree = resp.json()['term_output']

    pad = curses.newpad(1000, 1000)
    # pad.addstr(tree)
    # culour.addstr(pad, "\x1b[93mHELLO\033[95m WORLD\033[0m")
    culour.addstr(pad, tree) # Only understands colors 91, 92, 93, 94, 95

    pad.refresh(0,0, 0,0, curses.LINES-4, curses.COLS-1)
    # tw = curses.newwin(curses.LINES-4,curses.COLS,0,0)
    # tw.bkgd(' ', curses.color_pair(1))
    # tw.addstr(resp.text[:200])
    # tw.refresh()

    editwin = curses.newwin(1,curses.COLS-3, curses.LINES-3, 2)
    box = curses.textpad.Textbox(editwin)
    curses.textpad.rectangle(stdscr,curses.LINES-4, 0, curses.LINES-2, curses.COLS-1)
    stdscr.refresh()


    while True:
        editwin.clear()
        box.edit()
        message = box.gather().strip()
        if message == "quit" or message == "q":
            return
        pad.clear()
        # pad.refresh()
        resp = requests.post("http://localhost:5051/api/send-command", data=json.dumps({"command": message, "args": "", "token": TOKEN}))
        text = resp.json()['term_output']
        culour.addstr(pad, text)
        pad.refresh(0,0, 0,0, curses.LINES-5, curses.COLS-1)




curses.wrapper(main)
