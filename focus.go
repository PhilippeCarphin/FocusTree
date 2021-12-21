package main

import (
	// "encoding/json"
	"fmt"
)



type TreeNode struct {
	Text string
	Done bool
	ClosingNotes string
	Id int
	CreatedOn string
	FinishedOn string
	Children []*TreeNode
	Parent *TreeNode
	Manager *TreeManager

}

type TreeManager struct {
	RootNodes []*TreeNode
	currentId int
}

func NewTreeManager() *TreeManager {
	return &TreeManager{
		RootNodes: make([]*TreeNode,0),
	}
}

func (tm *TreeManager) AddRootNode(n *TreeNode) error {
	n.Id = tm.currentId
	tm.currentId += 1

	n.Manager = tm
	tm.RootNodes = append(tm.RootNodes, n)

	return nil
}

func NewTreeNode() *TreeNode {

	return &TreeNode{
		CreatedOn: "Now",
		Children: make([]*TreeNode, 0),
	}
}

func (n *TreeNode) AddChild(c *TreeNode) error {
	c.Parent = n
	c.Manager = n.Manager
	n.Children = append(n.Children, c)
	return nil
}

func main(){
	n := NewTreeNode()
	fmt.Println(n)
	tm := NewTreeManager()
	tm.AddRootNode(n)
	return
}
//     """Basic noce of the focus tree.
//
//     The node has some info about itself and a 'children' attribute."""
//     TreeNode_Counter = 0
//     def __init__(self, **kwargs):
//         # This node's stuff
//         type(self).TreeNode_Counter += 1
//         self.text = kwargs.get('text', 'this node')
//         self.done = kwargs.get('done', False)
//         self.closing_notes = kwargs.get('closing_notes', None)
//         self.id = kwargs.get('id', self.TreeNode_Counter)
//         self.created_on = kwargs.get(
//             'created_on',
//             datetime.datetime.now().strftime("(%Y-%m-%d %H:%M:%S)"))
//         self.finished_on = kwargs.get(
//             'finished_on',
//             None)
//
//         # Relationships with other nodes
//         self.children = []
//         self.parent = None
//         if kwargs.get("parent", None):
//             kwargs["parent"].add_child(self)
//         self.update_depth()
