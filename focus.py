import datetime
import json

class FocusTreeException(Exception):
    pass


class TreeNode:
    TreeNode_Counter = 0
    def __init__(self, **kwargs):
        # This node's stuff
        type(self).TreeNode_Counter += 1
        self.text = kwargs.get('text', 'this node')
        self.done = kwargs.get('done', False)
        self.closing_notes = kwargs.get('closing_notes', None)
        self.id = kwargs.get('id', self.TreeNode_Counter)
        self.created_on = kwargs.get(
            'created_on',
            datetime.datetime.now().strftime("(%Y-%m-%d %H:%M:%S)"))
        self.finished_on = kwargs.get(
            'finished_on',
            None)

        # Relationships with other nodes
        self.children = []
        self.parent = None
        if kwargs.get("parent", None):
            kwargs["parent"].add_child(self)
        self.update_depth()

    # For serializing to JSON
    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "children": [ c.to_dict() for c in self.children],
            "info": {
                "done": self.done,
                "closing_notes": self.closing_notes,
                "created": str(self.created_on),
                "finished": str(self.finished_on) if self.done else None
            }
        }

    @staticmethod
    def from_dict(d):
        if not dict:
            return TreeNode()
        node_info = d["info"]
        node = TreeNode(text=d["text"], created_on=node_info["created"], finished_on=node_info["finished"], done=node_info['done'], id=d["id"], closing_notes=node_info["closing_notes"])
        for c in d["children"]:
            node.add_child(TreeNode.from_dict(c))
        return node

    def to_org(self, starting_depth=1):
        self.update_depth()
        org_todo_keyword = 'DONE' if self.done else 'TODO'
        output = '\n' + '*'*(self.depth + starting_depth) + ' ' + org_todo_keyword + ' ' + self.text + '\n'
        output += 'created_on : ' + self.created_on + '\n'
        output += ('closing_notes : ' + str(self.closing_notes) + '\n') if self.closing_notes else ''
        output += 'finished_on : ' + str( self.finished_on ) + '\n'
        output += '\n'.join([c.to_org(starting_depth) for c in self.children])
        return output


    def update_depth(self):
        self.depth = self.parent.depth + 1 if self.parent else 0

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        child.update_depth()

    def remove_child(self, child):
        self.children.remove(child)

    def is_done(self):
        for c in self.children:
            if not c.is_done():
                return False

        return self.done

    def find_subtask_by_id(self, id):
        if self.id == id:
            return self
        for c in self.children:
            c_with_id = c.find_subtask_by_id(id)
            if c_with_id != None:
                return c_with_id
        return None

    def __str__(self):
        first_part = self.text + " (id={},{})[created: {}".format(self.id, self.done, self.created_on)
        if self.done:
            finished = " finished: {}".format(self.finished_on)
        else:
            finished = ""
        return first_part + finished + ']'

    def printable_ancestors(self):
        curr = self
        chain = [self]
        while curr.parent:
            chain.append(curr.parent)
            curr = curr.parent

        output = str(chain.pop())
        prefix = "\n"
        for a in reversed(chain):
            output += prefix +  ' ^--' + str(a)
            prefix += "    "

        return output

    def printable_tree(self, depth=0, prefix="\n   "):
        self.update_depth()
        if depth == 0:
            lines = [str(self)]
        else:
            lines = ['^---' + str(self)]
        i = 0
        for c in self.children:
            i += 1
            if len(self.children) > 1 and i < len(self.children):
                new_prefix = prefix + "|   "
            else:
                new_prefix = prefix + "    "

            lines.append(c.printable_tree(depth+1, new_prefix))

        return prefix.join(lines)

    def ancestors(self):
        ancestors = []
        current = self
        while current:
            ancestors.append(str(current))
            current = current.parent
        return '\n'.join(reversed(ancestors))

def get_command():
    return input("enter command")

class TreeManager:
    def __init__(self):
        self.root_nodes = []
        self.current_task = None
        self.commands = {
            'next-task': {'handler': self.next_task, 'help': 'Create a new sibling of current_task'},
            'new-task': {'handler': self.new_task, 'help': 'Create new root task'},
            'save-org': {'handler': self.save_org , 'help': 'Save as org mode file'},
            'subtask': {'handler': self.subtask, 'help': 'Create and enter new subtask of current task'},
            'done': {'handler': self.done , 'help': 'Mark current task as done and move to the next task in DFS order'},
            'reset': {'handler': lambda args : self.reset(), 'help': 'Clear the tree completely'},
            'switch-task': {'handler': self.switch_task, 'help': 'switch to the task (by id)'},
            'tree' : { 'handler': lambda args: None , 'help': 'Show the entire tree'},
            'subtask-by-id': {'handler': self.subtask_by_id, 'help': 'create subtask of task with id (subtask-by-id <an id> the text of the task)'},
            'reassign-ids': {'handler': lambda args: self.reassign_ids(), 'help': 'Reassing all ids in case something weird happened'},
            'current' : {'handler' : lambda args : None, 'help': 'Show the current context'},
            'help': {'handler': lambda args: None, 'help': 'Show this thing'},
        }

    @staticmethod
    def command_list():
        return list(TreeManager().commands.keys())

    @staticmethod
    def meta_dict():
        commands = TreeManager().commands
        return {key: commands[key]["help"] for key in commands} 

    def to_dict(self):
        return {
            "root_nodes": [r.to_dict() for r in self.root_nodes],
            "current_task_id": self.current_task.id if self.current_task else 0,
            "current_task": self.current_task.text if self.current_task is not None else "--NONE--"
        }

    def to_org(self, starting_depth=1):
        title = '#+TITLE: FocusTree exported on{}\n\n'.format(datetime.datetime.now())
        return title + ''.join([r.to_org(starting_depth) for r in self.root_nodes])

    def find_task_by_id(self, id):
        """Depth first searches for the first leaf task it can find and sets it
        as the current task"""
        if id == 0:
            return None
        for r in self.root_nodes:
            task_with_id = r.find_subtask_by_id(id)
            if task_with_id:
                return task_with_id
        return None

    def save_to_file(self, filename):
        with open(filename, 'w+') as f:
            f.write(json.dumps(self.to_dict(), indent=4, sort_keys=True))

    @staticmethod
    def load_from_file(filename):
        with open(filename, 'r') as f:
            return TreeManager.from_dict(json.loads(f.read()))

    @staticmethod
    def from_dict(d):
        tm = TreeManager()
        tm.root_nodes = [TreeNode.from_dict(rn) for rn in d["root_nodes"]]
        tm.current_task = tm.find_task_by_id(d["current_task_id"])
        return tm

    def execute_command(self, command):
        words = command.split();
        if not words:
            raise FocusTreeException("Missing Command: Must supply a command")

        operation = words[0].lower()
        args = ' '.join(words[1:])
        print("EXECUTE_COMMAND(): operation = {}, args = {}".format(operation,args))

        if operation not in self.commands:
            raise FocusTreeException("UNKNOWN OPERATION " + operation)

        self.commands[operation]['handler'](args)

        if operation in ['help']:
            term_output = json.dumps(TreeManager.meta_dict(), indent=4, sort_keys=True)
        elif operation in ['t', "tree", 'nt', "next-task", 'net', "new-task"] or self.current_task is None:
            term_output = self.printable_tree()
        else:
            term_output = self.current_task.printable_ancestors()

        return term_output

    def subtask_by_id(self, args):
        words = args.split()
        try:
            id = int(words[1])
        except ValueError:
            raise FocusTreeException("Second argument must be an id")
        except IndexError:
            raise FocusTreeException("This command requires an id and then some text")
        task = self.find_task_by_id(id)
        if not task:
            raise FocusTreeException("Task with id {} was not found.".format(id))
        task_text = ''.join(words[2:])
        if not task_text:
            raise FocusTreeException("This command requires text after the id")
        task.add_child(TreeNode(text=task_text))

    def save_org(self, args):
        with open(args, 'w+') as f:
            f.write(self.to_org())

    def switch_task(self, args):
        id = int(args)
        self.current_task = self.find_task_by_id(id)
        print('setting current task to :{} (id={})'.format(self.current_task.text, self.current_task.id))
        return self.current_task

    def reset(self):
        self.save_to_file('backup.json')
        self.root_nodes = []
        self.current_task = None

    def update(self):
        def find_not_done_dfs(n):
            if n is None:
                return None

            for c in n.children:
                res = find_not_done_dfs(c)
                if res:
                    return res
            else:
                if not n.done:
                    return n
                else:
                    return None

        cursor = self.current_task
        result = find_not_done_dfs(cursor)

        while not result and cursor and cursor.parent:
            cursor = cursor.parent
            result = find_not_done_dfs(cursor)
            if result:
                break
        else:
            for r in self.root_nodes:
                result = find_not_done_dfs(r)
                if result:
                    break

        self.current_task = result



    def reassign_ids(self):
        current_id = 0

        def visit(n, func):
            func(n)
            for c in n.children:
                visit(c, func)

        def give_id(n):
            nonlocal current_id
            current_id += 1
            n.id = current_id

        for r in self.root_nodes:
            visit(r, give_id)

        TreeNode.TreeNode_Counter = current_id + 1

    def printable_tree(self):
        lines = []
        for n in self.root_nodes:
            lines.append(n.printable_tree())
        return '->' + '\n->'.join(lines)

    def next_task(self, task):
        if not args:
            raise FocusTreeException("Missing Command : This command must have an argument")
        if not self.current_task:
            raise FocusTreeException("Next-task is only valid if there is a current task")
        if not self.current_task.parent:
            raise FocusTreeException("Next-task is only valid if current_task has a parent")

        self.current_task.parent.add_child(TreeNode(text=task))

    def new_task(self, task):
        if not task:
            raise FocusTreeException("Missing Command : This command must have an argument")
        self.root_nodes.append(TreeNode(text=task))

    def subtask(self, task):
        if not task:
            raise FocusTreeException("Missing Command : This command must have an argument")
        new_task = TreeNode(text=task)
        if self.current_task is not None:
            self.current_task.add_child(new_task)
        else:
            self.root_nodes.append(new_task)
        self.current_task = new_task

    def done(self, args):
        if self.current_task is None:
            raise FocusTreeException("No current task")
        self.current_task.done = True
        if not self.current_task.is_done():
            self.current_task.done = False
            raise FocusTreeException("Cannot mark done, task has unfinished children")
        else:
            self.current_task.closing_notes = args
            self.current_task.finished_on = datetime.datetime.now().strftime("(%Y-%m-%d %H:%M:%S)")
            self.update()

def make_test_tree():
    root = TreeNode(text="This is the root node of the tree")
    root.add_child(TreeNode(text="This is a sub-task of root"))
    root.children[0].add_child(TreeNode(text="This is a sub-sub-task of root"))
    root.add_child(TreeNode(text="This is another child of root"))
    return root

if __name__ == "__main__":
    pass
