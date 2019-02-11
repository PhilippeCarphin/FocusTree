import datetime
import json
import mailtool

class FocusTreeException(Exception):
    pass

HOTMAIL = mailtool.make_hotmail_connection()

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
            'DOES NOT APPLY')

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
                "finished": str(self.finished_on) if self.done else "task not finished"
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
        org_todo_keyword = 'DONE' if self.done else 'TODO'
        output = '\n' + '*'*(self.depth + starting_depth) + ' ' + org_todo_keyword + ' ' + self.text + '\n'
        output += 'created_on : ' + self.created_on + '\n'
        output += 'finished_on : ' + self.finished_on + '\n'
        output += ('closing_notes : ' + str(self.closing_notes) + '\n') if self.closing_notes else ''
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
        if self.done:
            return self.text + "[created: {}, finished: {}]".format(self.created_on, self.finished_on)
        else:
            return self.text + "[created: {}]".format(self.created_on)

    def print_ancestors(self):
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

    def print_tree(self, depth=0, prefix="\n   "):
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

            lines.append(c.print_tree(depth+1, new_prefix))

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
        self.operations = {
            "subtask": self.subtask,
            "done": self.done,
            "next-task": self.next_task
        }

    def to_dict(self):
        return {
            "root_nodes": [r.to_dict() for r in self.root_nodes],
            "current_task_id": self.current_task.id if self.current_task else 0,
            "current_task": self.current_task.text if self.current_task is not None else "--NONE--"
        }

    def to_org(self, starting_depth=1):
        return ''.join([r.to_org(starting_depth) for r in self.root_nodes])

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
            raise IndexError("Missing Command: Must supply a command")
        operation = words[0]
        args = ' '.join(words[1:])
        print("EXECUTE_COMMAND(): operation = {}, args = {}".format(operation,args))
        if operation in ["enqueue", "next-task"]:
            if not args:
                raise IndexError("Missing Command : This command must have an argument")
            self.next_task(args)
        elif operation in ['save-org']:
            with open(args, 'w+') as f:
                f.write(self.to_org())
        elif operation in ['send-org']:
            with open('focus-tree.org', 'w+') as f:
                f.write(self.to_org())
            mailtool.send_mail_connected(
                'phil103@hotmail.com',
                args,
                'FocusTree: Your tree',
                'Current contents of your tree',
                HOTMAIL,
                'focus-tree.org',
                )
        elif operation in [ "subtask", "call", "push"]:
            if not args:
                raise IndexError("Missing Command : This command must have an argument")
            self.subtask(args)
        elif operation in ["return", "done", "pop"]:
            self.done(args)
        elif operation in ["reset"]:
            self.reset()
        elif operation in ["tree", "current"]:
            pass
        else:
            raise Exception("UNKNOWN OPERATION " + operation)
        self.update()
        if operation in ["tree", "next-task"] or self.current_task is None:
            term_output = self.print_tree()
        else:
            term_output = self.current_task.print_ancestors()

        return term_output

    def reset(self):
        self.save_to_file('backup.json')
        self.root_nodes = []
        self.current_task = None

    def update(self):
        if self.current_task is None:
            for n in self.root_nodes:
                if not n.is_done():
                    self.current_task = n
                    break

    def print_tree(self):
        lines = []
        for n in self.root_nodes:
            lines.append(n.print_tree())
        return '->' + '\n->'.join(lines)

    def next_task(self, task):
        self.root_nodes.append(TreeNode(text=task))

    def subtask(self, task):
        new_task = TreeNode(text=task)
        if self.current_task is not None:
            self.current_task.add_child(new_task)
        else:
            self.root_nodes.append(new_task)
        self.current_task = new_task

    def done(self, args):
        self.current_task.done = True
        if not self.current_task.is_done():
            self.current_task.done = False
            print("Cannot mark done, task has unfinished children")
            update()
        else:
            self.current_task.closing_notes = args
            self.current_task.finished_on = datetime.datetime.now().strftime("(%Y-%m-%d %H:%M:%S)")
            self.current_task = self.current_task.parent

def make_test_tree():
    root = TreeNode(text="This is the root node of the tree")
    root.add_child(TreeNode(text="This is a sub-task of root"))
    root.children[0].add_child(TreeNode(text="This is a sub-sub-task of root"))
    root.add_child(TreeNode(text="This is another child of root"))
    return root

if __name__ == "__main__":
    a = TreeNode()
    b = TreeNode()
    c = TreeNode()
    a.add_child(b)
    try:
        a.remove_child(c)
    except ValueError:
        pass

    run()

