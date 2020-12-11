#!/usr/bin/env python3

import os
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

from program_options import get_options

the_tree = None

class REPLDoneError(Exception):
    pass

def read_command(prompt):
    try:
        return prompt()
    except EOFError as e:
        raise REPLDoneError("EOF entered")

def eval_command(command_line):
    payload = command_line if command_line != '' else 'current'
    words = command_line.split()
    operation = words[0]
    client_commands = ['save-org', 'clear', 'save-file', 'send-file']
    print("operation = {}".format(operation))
    if operation in client_commands:
        if operation == 'save-org':
            the_tree = get_tree()
            resp = save_org_command(''.join(words[1:]), the_tree)
        elif operation == 'clear':
            os.system('clear')
            resp = {'status':'OK', 'term_output': ''}
        elif operation == 'save-file':
            the_tree = get_tree()
            the_tree.save_to_file(words[1])
            resp = {'status':'OK', 'term_output': ''}
        elif operation == 'send-file':
            request_url = 'http://{}:{}/api/send-tree'.format(
                program_options.host,
                program_options.port
                )
            tree = focus.TreeManager.load_from_file(words[1])
            payload = bytes(json.dumps(tree.to_dict()), 'utf-8')
            resp = requests.post(request_url, data=payload).json()
    else:
        request_url = 'http://{}:{}/api/send-command' .format(
            program_options.host,
            program_options.port
            )
        resp = requests.post(request_url, data=bytes(payload, 'utf-8')).json()
    return resp

def print_output(resp):
    if resp['status'] != 'OK':
        print(colored('ERROR : ' + resp['error'], 'red'))
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
            if words and words[0] in ['subtask-by-id', 'switch-task']:
                if len(complete_words) >= 2:
                    return
                for task in the_tree.root_nodes_iter():
                    yield Completion(
                            task.id,
                            display=f'{task.id} : {task.text}',
                            start_position=-len(word)
                    )
            else:
                if len(complete_words) >= 1:
                    return
                for command in list(commands):
                    if command.startswith(word):
                        yield Completion(
                            command,
                            display=command + ' : ' + commands[command]['help'],
                            start_position=-len(word))

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
    request_url = 'http://{}:{}/api/tree'.format(
        program_options.host,
        program_options.port
    )
    print(request_url)
    resp = requests.get(request_url)
    return focus.TreeManager.from_dict(resp.json())

def save_org_command(filename, tree):
    with open(filename, 'w+') as f:
        f.write(tree.to_org())
    return {
        'command': 'save-org ' + filename,
        'status': 'OK',
        'error': None,
        'term_output': 'saved file {}'.format(os.getcwd() + '/' + filename),
        'term_error':''
    }


if __name__ == "__main__":

    program_options = get_options()

    if program_options.verbose:
        print("FocusTree client using http://{}:{}"
              .format(program_options.host, program_options.port))

    print(program_options)

    server_process = None

    try:
        get_tree()
    except requests.exceptions.ConnectionError as e:
        # NOTE Maybe this should only be done if we are getting our port and host from a file
        print(f'Could not connect to server on host {program_options.port}, port {program_options.host}')
        print("Starting server")
        server_process = subprocess.Popen(['ftserver', '--port', str(program_options.port), '--host', program_options.host])
        time.sleep(1)
        try:
            get_tree()
        except requests.exceptions.ConnectionError as e:
            print('Could not start server')
            quit()

    if program_options.ft_command:
        resp = eval_command(' '.join(program_options.ft_command))
        print_output(resp)
    else:
        REPL()

    if server_process:
        server_process.kill()

