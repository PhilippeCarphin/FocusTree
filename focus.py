import datetime
import json

class FocusTreeException(Exception):
    pass


class TreeNode:
    """Basic noce of the focus tree.

    The node has some info about itself and a 'children' attribute."""
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

    def to_dict(self):
        """Change the node to a dictionary, this is for serializing to JSON for
        transfer over HTTP or to a file"""
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
        """Create a TreeNode from a dictionary. This is for taking deserialized JSON
        from HTTP or a file"""
        if not dict:
            return TreeNode()
        node_info = d["info"]
        node = TreeNode(
            text=d["text"],
            created_on=node_info["created"],
            finished_on=node_info["finished"],
            done=node_info['done'],
            id=d["id"],
            closing_notes=node_info["closing_notes"]
        )
        for c in d["children"]:
            node.add_child(TreeNode.from_dict(c))
        return node

    def to_org(self, starting_depth=1):
        """Create an org-mode text representation of the tree of this Node
        This is for saving an org-mode report"""
        self.update_depth()
        org_todo_keyword = 'DONE' if self.done else 'TODO'
        stars = '\n' + '*'*(self.depth + starting_depth)
        output = stars + ' ' + org_todo_keyword + ' ' + self.text + '\n'
        output += 'created_on : ' + self.created_on + '\n'
        output += 'closing_notes : ' + str(self.closing_notes) + '\n'
        output += 'finished_on : ' + str( self.finished_on ) + '\n'
        output += '\n'.join([c.to_org(starting_depth) for c in self.children])
        return output

    def update_depth(self):
        """Set the depth of this node"""
        self.depth = self.parent.depth + 1 if self.parent else 0

    def add_child(self, child):
        """Append a child to this node's children, update the child's parent reference
        and depth."""
        self.children.append(child)
        child.parent = self
        child.update_depth()

    def remove_child(self, child):
        """Remove a child from this node's children, also cuts the parent reference"""
        self.children.remove(child)
        child.parent = None
        child.depth = 0

    def is_done(self):
        """Calculates the done-ness of the task"""
        for c in self.children:
            if not c.is_done():
                return False

        return self.done

    def find_subtask_by_id(self, id):
        """Return the task whose id matches the parameter. This is for turing id-based
        references from files and JSON into true references in the from_dict()
        methods"""
        if self.id == id:
            return self
        for c in self.children:
            c_with_id = c.find_subtask_by_id(id)
            if c_with_id != None:
                return c_with_id
        return None

    def ancestors(self):
        """Get a list of the ancestors of this node"""
        ancestors = []
        current = self
        while current:
            ancestors.append(str(current))
            current = current.parent
        return '\n'.join(reversed(ancestors))

    def __str__(self):
        """The string representation of nodes is meant to be shown in a terminal as a
        single line with some key info for the printable_tree and printable_ancestors
        methods."""
        first_part = self.text + " (id={},{})[created: {}".format(
            self.id, self.done, self.created_on
        )
        if self.done:
            finished = " finished: {}".format(self.finished_on)
        else:
            finished = ""
        return first_part + finished + ']'

    def printable_ancestors(self):
        """Get a string for making a nice display on the terminal of the ancestors of
        this node."""
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
        """Get a string for this tree for a nice display on the terminal"""
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


"""Dictionary of commands with command names as keys and info about these
commands as the value
{
    command_name: {'help': command.__doc__, 'handler': command},
    ...
}
"""
commands = {}

def register_command(func):
    """Decorator for registering methods of the TreeManager class as commands
    for the tree interface."""
    command = func.__name__.replace('_','-')
    commands[command] = {'help': func.__doc__, 'handler': func}
    return func


class TreeManager:
    """Class defining a command based user interface"""
    def __init__(self):
        self.root_nodes = []
        self.current_task = None

    def execute_command(self, command):
        if not command:
            raise FocusTreeException("Missing Command: Must supply a command")

        words = command.split();
        operation = words[0].lower()
        args = ' '.join(words[1:])

        if operation not in commands:
            raise FocusTreeException("UNKNOWN OPERATION " + operation)

        print("EXECUTE_COMMAND(): operation = {}, args = {}".format(operation,args))
        return commands[operation]['handler'](self, args)

    def update(self):
        """Update the current_task of the tree (I shoudld change the name
        before it's too late), do a dfs from the current node for a not-done
        task, then do DFS searches from the ancestors, and finally, move on
        to the other root_nodes."""
        def find_not_done_dfs(n):
            """Does a DFS search for the deepest not-done node with n as a
            starting point"""
            if n is None:
                return None

            for c in n.children:
                res = find_not_done_dfs(c)
                if res: return res
            if not n.done:
                return n

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


    def to_dict(self):
        """Method for turning the whole tree into a dictionary for serializing
        to JSON.  Note the use of id to remember the current task."""
        return {
            "root_nodes": [r.to_dict() for r in self.root_nodes],
            "current_task_id": self.current_task.id if self.current_task else 0,
            "current_task": self.current_task.text
                                 if self.current_task is not None else "--NONE--"
        }

    @staticmethod
    def from_dict(d):
        """Create a TreeManager from a dictionary"""
        tm = TreeManager()
        tm.root_nodes = [TreeNode.from_dict(rn) for rn in d["root_nodes"]]
        tm.current_task = tm.find_task_by_id(d["current_task_id"])
        return tm

    def to_org(self, starting_depth=1):
        """Create an org-mode file with the tree."""
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
        """Save tree as json to local file"""
        with open(filename, 'w+') as f:
            f.write(json.dumps(self.to_dict(), indent=4, sort_keys=True))

    @staticmethod
    def load_from_file(filename):
        """Load tree from local json file"""
        with open(filename, 'r') as f:
            return TreeManager.from_dict(json.loads(f.read()))

    def printable_tree(self):
        """Get a printable tree for terminal output"""
        lines = []
        for n in self.root_nodes:
            lines.append(n.printable_tree())
        return '->' + '\n->'.join(lines)


    @register_command
    def tree(self, args):
        """Get a printable tree"""
        return self.printable_tree()

    @register_command
    def current(self, args):
        """Get a printable list of ancestors"""
        if self.current_task:
        	return self.current_task.printable_ancestors()
        else:
        	return "No current task"

    @register_command
    def help(self, args):
        """Show the list of commands and their descriptions"""
        return json.dumps({c: str(commands[c]['help']) for c in commands}, indent=4, sort_keys=True)

    @register_command
    def subtask_by_id(self, args):
        """Change to the subtask with the specified id"""
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
        return self.printable_tree()

    @register_command
    def save_org(self, args):
        """ Save an org-mode file locally"""
        with open(args, 'w+') as f:
            f.write(self.to_org())

        return 'Saved file {}'.format(args)

    @register_command
    def switch_task(self, args):
        """Switch to the task with the specified id"""
        id = int(args)
        self.current_task = self.find_task_by_id(id)
        print('setting current task to :{} (id={})'
              .format(self.current_task.text, self.current_task.id))
        return self.current_task.printable_ancestors()

    @register_command
    def reset(self, args):
        """Clear the whole tree"""
        self.save_to_file('backup.json')
        self.root_nodes = []
        self.current_task = None
        return 'Cleared tree'

    @register_command
    def reassign_ids(self, args):
        """Reassign all the ids in the case that they got messed up."""
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

        return 'Reassigned ids'


    @register_command
    def next_task(self, task):
        """Add a new sibling to the current task"""
        if not task:
            raise FocusTreeException("Missing Command : This command must have an argument")
        if not self.current_task:
            raise FocusTreeException("Next-task is only valid if there is a current task")
        if not self.current_task.parent:
            raise FocusTreeException("Next-task is only valid if current_task has a parent")

        self.current_task.parent.add_child(TreeNode(text=task))

        return self.printable_tree()

    @register_command
    def new_task(self, task):
        """Create a new root task"""
        if not task:
            raise FocusTreeException("Missing Command : This command must have an argument")
        self.root_nodes.append(TreeNode(text=task))

        return self.printable_tree()

    @register_command
    def subtask(self, task):
        """Create and enter a new subtask of the current task"""
        if not task:
            raise FocusTreeException("Missing Command : This command must have an argument")
        new_task = TreeNode(text=task)
        if self.current_task is not None:
            self.current_task.add_child(new_task)
        else:
            self.root_nodes.append(new_task)
        self.current_task = new_task

        return self.current_task.printable_ancestors()

    @register_command
    def done(self, args):
        """Mark the current task as done (with optional closing notes)"""
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

        return self.current_task.printable_ancestors()

def make_test_tree():
    root = TreeNode(text="This is the root node of the tree")
    root.add_child(TreeNode(text="This is a sub-task of root"))
    root.children[0].add_child(TreeNode(text="This is a sub-sub-task of root"))
    root.add_child(TreeNode(text="This is another child of root"))
    return root

if __name__ == "__main__":
    pass
