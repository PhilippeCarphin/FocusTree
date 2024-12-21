#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import requests
import focus
import json
from termcolor import colored
from pygments.lexers.shell import BashSessionLexer, BashLexer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completion, Completer, FuzzyCompleter, FuzzyWordCompleter, WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls, Style
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
            "command" : command_line if command_line != '' else 'current',
            "token" : TOKEN,
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
            resp = {'status':0, 'term_output': ''}
        elif operation == 'save-file':
            the_tree = get_tree()
            the_tree.save_to_file(words[1])
            resp = {'status':0, 'term_output': ''}
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
            resp = {'status':0, 'term_output': ''}
    else:
        request_url = f'http://{args.host}:{args.port}/api/send-command'
        resp = requests.post(request_url, data=bytes(json.dumps(payload), 'utf-8')).json()
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
    r = eval_command('current')
    print(r['term_output'])
    while True:
        try:
            loop(prompt)
        except REPLDoneError:
            break

def make_prompt_session():
    commands = focus.commands
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
                to_completion = lambda n: Completion(
                        str(n.id),
                        display=f'{n.id} : {n.text}',
                        start_position=-len(word))
                yield from map(to_completion, tasks)
            else:
                if len(complete_words) >= 1:
                    return
                to_completion = lambda c : Completion(
                        c,
                        display=f"{c} : {focus.commands[c]['help']}",
                        start_position=-len(word))
                cmds = filter(lambda c: c.startswith(word), focus.commands.keys())
                yield from map(to_completion, cmds)

    ft_completer = FuzzyCompleter(CustomComplete())
    # This if I want the help to be displayed
    ft_completer = CustomComplete()
    ####################################################################################
    # commands = focus.commands
    # meta_dict = {c : commands[c]['help'] for c in commands}
    # #print(meta_dict)
    # ft_completer = WordCompleter(focus.commands, meta_dict=meta_dict)
    prompt_style = Style.from_dict({
        'prompt': '#00aa00'
    })
    prompt_string = [
        ('class:username', 'FocusTree> ')
    ]
    bindings = KeyBindings()
    @bindings.add('c-j')
    def _(event):
        event.current_buffer.complete_next()
    @bindings.add('c-k')
    def _(event):
        event.current_buffer.complete_previous()
    # @bindings.add('tab')
    # def _(event):
    #     # THIS IS THE GETTO-EST THING EVER, DON'T JUDGE ME!
    #     # I just want it to select the currently highlighted
    #     # completion.  It could continue completing after.
    #     current_buffer = event.app.current_buffer
    #     compl = current_buffer.text
    #     current_buffer.cancel_completion()
    #     current_buffer.text = ''
    #     current_buffer.insert_text(compl + ' ')

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
    with open(filename, 'w+') as f:
        f.write(tree.to_org())
    return {
        'command': 'save-org ' + filename,
        'status': 0,
        'error': None,
        'term_output': 'saved file {}'.format(os.getcwd() + '/' + filename),
        'term_error':''
    }


def execute(args):
    try:
        if args.ft_command:
            resp = eval_command(' '.join(args.ft_command))
            print_output(resp)
        else:
            REPL()
    except requests.exceptions.ConnectionError as e:
        print(f'Could not connect to ftserver : {e}')

class ServerProcess:
    def __init__(self, args):
        self.args = args
    def __enter__(self):
        self.process = subprocess.Popen(
            f'ftserver --port {args.port} --host {args.host}',
            shell=True,
            stderr=subprocess.DEVNULL,
        )
    def __exit__(self, type, value, traceback):
        self.process.terminate()

if __name__ == "__main__":

    args = get_args()

    print("FocusTree client using http://{}:{}"
              .format(args.host, args.port))

    home = os.environ['HOME']
    if 'http_proxy' in os.environ:
        print(f"{os.path.basename(sys.argv[0])}: \033[33mWARNING\033[0m: Unsetting environment variable 'http_proxy'")
        del os.environ['http_proxy']
    if 'HTTP_PROXY' in os.environ:
        print(f"{os.path.basename(sys.argv[0])}: \033[33mWARNING\033[0m: Unsetting environment variable 'HTTP_PROXY'")
        del os.environ['HTTP_PROXY']
    with open(os.path.expanduser('~/.ssh/ftserver_token')) as f:
        TOKEN = f.read().strip() # Just the actual key
    print(TOKEN)

    try:
        # There is already a server running
        get_tree()
    except BadServerError as e:
        print(f"{os.path.basename(sys.argv[0])}: \033[1;31mERROR\033[0m: ({type(e).__name__}) {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(f'No server running on {args.host}:{args.port}, starting manually on ...')
        with ServerProcess(args):
            # With sleep(0.1), the server isn't ready when we try to connect to it.
            time.sleep(1)
            execute(args)
    else:
        execute(args)
