#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import requests
import focus
import json
from termcolor import colored
from pygments.lexers.shell import BashLexer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completion, Completer, FuzzyCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle

from program_options import get_args

TOKEN = None

the_tree = None


class REPLDoneError(Exception):
    pass


class BadServerError(Exception):
    pass


def read_command(prompt):
    try:
        return prompt()
    except EOFError as e:
        raise REPLDoneError("EOF entered")


def eval_command(command_line='current'):
    payload = {
            "command": command_line if command_line != '' else 'current',
            "token": TOKEN,
    }
    words = command_line.split()
    operation = words[0]
    client_commands = ['save-org', 'clear', 'save-file', 'send-file']
    if operation in client_commands:
        if operation == 'save-org':
            the_tree = get_tree()
            resp = save_org_command(''.join(words[1:]), the_tree)
        elif operation == 'clear':
            os.system('clear')
            resp = {'status': 0, 'term_output': ''}
        elif operation == 'save-file':
            the_tree = get_tree()
            the_tree.save_to_file(words[1])
            resp = {'status': 0, 'term_output': ''}
        elif operation == 'send-file':
            request_url = f'http://{args.host}:{args.port}/api/send-tree'
            tree = focus.TreeManager.load_from_file(words[1])
            payload = bytes(json.dumps(tree.to_dict()), 'utf-8')
            resp = requests.post(request_url, data=payload).json()
        elif operation == 'help':
            print("<table>")
            for name, obj in focus.commands.items():
                print(f"<tr><td>{name}</td><td>{obj['help']}</td></tr>")
            print("</table>")
            resp = {'status': 0, 'term_output': ''}
    else:
        request_url = f'http://{args.host}:{args.port}/api/send-command'
        resp = requests.post(request_url, data=bytes(json.dumps(payload), 'utf-8'))
        if resp.status_code != 200:
            raise RuntimeError(f"send-command response code: {resp.status_code}")
        resp = resp.json()
    return resp


def print_output(resp):
    if resp['status'] != 0:
        print(colored('ERROR : ' + str(resp['error']), 'red'))
    print(resp['term_output'])


def loop(prompt_sesh):
    try:
        global the_tree
        the_tree = get_tree()
        command_line = read_command(prompt_sesh)
        if command_line == '': return
        resp = eval_command(command_line)
        if resp:
            print_output(resp)
    except KeyboardInterrupt:
        return


def REPL():
    prompt = make_prompt_session()
    resp = eval_command('current')
    print(resp['term_output'])
    while True:
        try:
            loop(prompt)
        except REPLDoneError:
            break


def make_prompt_session():
    class CustomComplete(Completer):
        def get_completions(self, document, complete_event):
            word = document.get_word_before_cursor()
            words = document.text.split()
            complete_words = (words if document.text.endswith(' ')
                                   else words[:-1])
            if words and words[0] in ['subtask-by-id', 'switch-task', 'delete-task', 'delete', 'info']:
                if len(complete_words) >= 2:
                    return
                tasks = the_tree.root_nodes_iter()
                if words[0] in ['subtask-by-id', 'switch-task']:
                    tasks = filter(lambda n: not n.done, tasks)
                # tasks = sorted(tasks, key=lambda n: n.id)
                tasks = filter(lambda n: str(n.id).startswith(word), tasks)

                yield from map(
                    lambda task: Completion(
                        str(task.id),
                        display=f'{task.id} : {task.text}',
                        start_position=-len(word)),
                    tasks
                )
            else:
                if len(complete_words) >= 1:
                    return
                cmds = filter(lambda c: c.startswith(word), focus.commands.keys())
                yield from map(
                    lambda c: Completion(
                        c,
                        display=f"{c} : {focus.commands[c]['help']}",
                        start_position=-len(word)),
                    cmds
                )

    ft_completer = FuzzyCompleter(CustomComplete())
    ft_completer = CustomComplete()
    prompt_style = Style.from_dict({
        'prompt': '#00aa00'
    })

    bindings = KeyBindings()

    @bindings.add('c-j')
    def _(event):
        event.current_buffer.complete_next()

    @bindings.add('c-k')
    def _(event):
        event.current_buffer.complete_previous()

    prompt_sesh = PromptSession(
        history=FileHistory(os.path.expanduser('~/.focus_tree_history')),
        auto_suggest=AutoSuggestFromHistory(),
        completer=ft_completer,
        reserve_space_for_menu=8,
        lexer=PygmentsLexer(BashLexer),
        key_bindings=bindings,
        style=prompt_style,
        complete_style=CompleteStyle.COLUMN
    )

    def prompt():
        return prompt_sesh.prompt([('class:username', 'FocusTree> ')])

    return prompt


def get_tree():
    request_url = f'http://{args.host}:{args.port}/api/tree'
    resp = requests.get(request_url)
    if resp.status_code != 200:
        e = BadServerError(f"Initial request '{request_url}' (no data) failed with code {resp.status_code}")
        e.response = resp
        raise e
    return focus.TreeManager.from_dict(resp.json())


def save_org_command(filename, tree):
    if not filename.endswith('.org'):
        filename += '.org'
    with open(filename, 'w+') as f:
        tree.to_org(1,f)
    return {
        'command': 'save-org ' + filename,
        'status': 0,
        'error': None,
        'term_output': 'saved file {}'.format(os.getcwd() + '/' + filename),
        'term_error':''
    }


def ensure_no_proxy():
    if 'http_proxy' in os.environ:
        print(f"{os.path.basename(sys.argv[0])}: \033[33mWARNING\033[0m: Unsetting environment variable 'http_proxy'")
        del os.environ['http_proxy']
    if 'HTTP_PROXY' in os.environ:
        print(f"{os.path.basename(sys.argv[0])}: \033[33mWARNING\033[0m: Unsetting environment variable 'HTTP_PROXY'")
        del os.environ['HTTP_PROXY']


def read_token():
    global TOKEN
    with open(os.path.expanduser('~/.ssh/ftserver_token')) as f:
        TOKEN = f.read().strip()  # Just the actual key
    print(f"Value of authentication token: {TOKEN}")


if __name__ == "__main__":
    args = get_args()
    print(f"FocusTree client using http://{args.host}:{args.port}")
    ensure_no_proxy()
    read_token()

    try:
        if args.ft_command:
            resp = eval_command(' '.join(args.ft_command))
            print_output(resp)
        else:
            REPL()
    except requests.exceptions.ConnectionError as e:
        print(f'Could not connect to ftserver : {e}')
