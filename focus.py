import datetime
class TreeNode:
    def __init__(self, **kwargs):
        self.children = []
        self.text = kwargs.get('text', 'this node')
        self.parent = None
        if kwargs.get("parent", None):
            kwargs["parent"].add_child(self)
        self.done = False
        self.update_depth()
        self.created_on = datetime.datetime.now().strftime("(%Y-%m-%d %H:%M:%S)")
        self.finished_on = "DOES NOT APPLY"

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

    def __str__(self):
        indent = '    ' * self.depth
        return indent + self.text + f"[created: {self.created_on}, finished: {self.finished_on}]"

    def print_tree(self):
        print(self)
        for c in self.children:
            c.print_tree()

    def ancestors(self):
        ancestors = []
        current = self
        while current:
            ancestors.append(str(current))
            current = current.parent
        return '\n'.join(reversed(ancestors))

def get_command():
    return input("enter command")

def run():
    # while true
    #     get the command
    #     execute the command
    #     check if we are done (or find next task to do)
    #     print current info
    root_nodes = []
    current_task = None
    while True:

        command = get_command()

        # EXECUTE THE COMMAND
        if command in ["enqueue", "next-task"]:
            new_task_text = input("enter next task")
            new_task = TreeNode(text=new_task_text)
            root_nodes.append(new_task)
        elif command in [ "subtask", "call", "push"]:
            task_text = input("enter subtask")
            new_task = TreeNode(text=task_text)
            if current_task is not None:
                current_task.add_child(new_task)
            else:
                root_nodes.append(new_task)
            current_task = new_task
        elif command in ["return", "done", "pop"]:
            current_task.done = True
            if not current_task.is_done():
                print("Cannot mark done, task has unfinished children")
                current_task.done = False
                for c in current_task.children():
                    if not c.is_done():
                        current_task = c
                        break
                else:
                    raise Exception("Can't happen, is_done() would have returned True")

            else:
                current_task.finished_on = datetime.datetime.now().strftime("(%Y-%m-%d %H:%M:%S)")
                current_task = current_task.parent
        else:
            print("UNKNOWN COMMAND " + command)
            continue

        # CHECK IF WE ARE DONE (find next undone task if not)
        if current_task is None:
            # Might be done, check that no tasks are not done,
            # if we make it all the way through the loop, print and quit.
            for n in root_nodes:
                if not n.is_done():
                    current_task = n
                    break
            else:
                print("EVERYTHING IS DONE")
                for n in root_nodes:
                    n.print_tree()
                quit()


        # PRINT CURRENT INFO AFTER COMMAND
        print(current_task.ancestors())
        print("CURRENT TASK : " + current_task.text)
        # TODO Here we could also write the current task to a file and have
        # another prograp periodically notify me with the text of this file
        # like what I did with my nag fish functions

if __name__ == "__main__":
    a = TreeNode()
    b = TreeNode()
    c = TreeNode()
    a.add_child(b)
    print("INPUT : " + input("say something"))
    try:
        a.remove_child(c)
    except ValueError:
        pass

    run()

