#!/usr/bin/env python3

import os
import subprocess
import requests
import focus
import json
from termcolor import colored
import argparse
from pygments.lexers.shell import BashSessionLexer, BashLexer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completion, Completer, FuzzyCompleter, FuzzyWordCompleter, WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls, Style
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle

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
        command_line = read_command(prompt_sesh)
        if command_line == '': return
        resp = eval_command(command_line)
        if resp:
            print_output(resp)
    except KeyboardInterrupt:
        return

def read_config_file():
    file = fs_parent_search('.focustree.json')
    if file:
        with open(file) as f:
            config = json.loads(f.read())
            config['config_file'] = file
            return config
    else:
        return {}

def REPL():
    prompt = make_prompt_session()
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

def fs_parent_search(filename):
    directory = os.getcwd()
    while True:
        file = os.path.join(directory, filename)
        if os.path.exists(file):
            return file
        if directory == '/':
            return None
        directory = os.path.split(directory)[0]

    return None



def command_line_parser():
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--port", type=int, help="Port of the server")
    p.add_argument("--host", help="Address of the server")
    p.add_argument("-v", "--verbose", action="store_true", help="Address of the server")
    p.add_argument("ft_command", nargs='*', help="(optional) The command to send to focus tree, no command will launch an interactive client")
    return p.parse_args()

def get_options():
    cl_opts = command_line_parser()
    config = read_config_file()

    def get_value(key, default=None, t=str):
        env_var = 'FOCUS_TREE_' + key.upper()
        if key in config:
            if cl_opts.verbose:
                print(colored('Getting {} from from config file {}'
                              .format(key, config['config_file']), 'yellow'))
            return t(config[key])
        elif env_var in os.environ:
            if cl_opts.verbose:
                print(colored('Getting {} from from environment variable {}'
                              .format(key, env_var), 'yellow'))
            return t(os.environ[env_var])
        else:
            if cl_opts.verbose:
                print(colored('Getting {} from hardcoded value {}'
                              .format(key, default), 'yellow'))
            return default

    if not cl_opts.port:
        cl_opts.port = get_value('port', 5051, int)
    if not cl_opts.host:
        cl_opts.host = get_value('host', 'localhost')

    return cl_opts

if __name__ == "__main__":

    program_options = get_options()

    if program_options.verbose:
        print("FocusTree client using http://{}:{}"
              .format(program_options.host, program_options.port))

    print(program_options)
    try:
        get_tree()
    except:
        process = subprocess.Popen(['ftserver', '--port', str(program_options.port), '--host', program_options.host], stdout=os.devnull)
    if program_options.ft_command:
        resp = eval_command(' '.join(program_options.ft_command))
        print_output(resp)
    else:
        REPL()
