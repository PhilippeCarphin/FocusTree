
class TreeNode:
    def __init__(self, **kwargs):
        self.children = []
        self.text = kwargs.get('text', 'this node')
        self.parent = kwargs.get('parent', None)
        self.done = False
        self.update_depth()

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

def get_command():
    return input("enter command")

def run():
    root_node = TreeNode(parent=None, text="ROOT NODE OF TREE")
    root_node.done = True

    dummy_node = TreeNode(parent=root_node, text="dummy node")
    dummy_node.done = True

    current_task = dummy_node
    while True:

        command = get_command()

        if command == "next-task":
            next_task = input("enter next task")
            current_task.parent.add_child(TreeNode(text=next_task))

        elif command == "subtask":
            sub_task = input("enter subtask")
            child = TreeNode(text=sub_task)
            current_task.add_child(child)
            current_task = child

        elif command == "done":
            current_task.done = True
            if not current_task.is_done():
                print("Cannot mark done, task has unfinished children")
                for c in current_task.children():
                    if not c.is_done():
                        current_task = c
                        break
                else:
                    raise Exception("Can't happen, is_done() would have returned True")


                current_task = current_task.parent
                if current_task is root_node:
                    current_task = dummy_node
            else:
                current_task = current_task.parent
                if current_task is root_node:
                    current_task = dummy_node


        if current_task is dummy_node:
            for child in root_node.children:
                if child is not dummy_node and not child.is_done():
                    current_task = child
                    break
            else:
                print("EVERYTHING IS DONE. GOOD JOB.")
                quit()

        print("CURRENT TASK : " + current_task.text)
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

