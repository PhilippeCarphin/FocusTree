package focus

import (
	"encoding/json"
	"fmt"
	"os"
	"io"
	"strings"
)

var TreeNodeIdCounter = 0

type TreeNode struct {
	Text         string       `json:text`
	Done         bool         `json:done`
	ClosingNotes string       `json:closing_notes`
	Id           int          `json:id`
	CreatedOn    string       `json:created`
	FinishedOn   string       `json:finished`
	Children     []*TreeNode  `json:children`
	Parent       *TreeNode    `json:"-"` // Must be ignored for JSON or cycles get created
	Depth        int          `json:"-"`
	Manager      *TreeManager `json:"-"`
}

type TreeManager struct {
	RootNodes []*TreeNode `json:root_nodes`
	Current   *TreeNode   `json:"-"`
	moveStack []*TreeNode `json:"-"`
}

func NewTreeManager() *TreeManager {
	return &TreeManager{
		RootNodes: make([]*TreeNode, 0),
		moveStack: make([]*TreeNode, 0),
	}
}

func (tm *TreeManager) Move(n *TreeNode) {
	tm.moveStack = append(tm.moveStack, tm.Current)
	tm.Current = n
}

func (tm *TreeManager) ToFile(filename string) error {
	b, err :=  json.Marshal(tm)
	if err != nil {
		return err
	}
	return os.WriteFile(filename, b, 0644)
}

func (tm *TreeManager) BacktrackMove() *TreeNode {
	last := len(tm.moveStack) - 1
	top := tm.moveStack[last]
	tm.moveStack = tm.moveStack[:last]
	return top
}

func (tm *TreeManager) AddRootNode(n *TreeNode) error {
	n.Manager = tm
	tm.RootNodes = append(tm.RootNodes, n)
	return nil
}

func NewTreeNode() *TreeNode {

	newNode := &TreeNode{
		Id:        TreeNodeIdCounter,
		CreatedOn: "Now",
		Children:  make([]*TreeNode, 0),
	}

	TreeNodeIdCounter++

	return newNode
}

func (n *TreeNode) AddChild(c *TreeNode) error {
	c.Parent = n
	c.Manager = n.Manager
	n.Children = append(n.Children, c)
	return nil
}

func (n *TreeNode) ToJSON() ([]byte, error) {
	b, err := json.MarshalIndent(n, "   ", "   ")
	if err != nil {
		return nil, fmt.Errorf("Error marshaling to json: %v", err)
	}
	return b, nil
}

func NodeFromJSON(b []byte) (*TreeNode, error) {
	var newNode TreeNode
	err := json.Unmarshal(b, &newNode)
	if err != nil {
		return nil, fmt.Errorf("Error marshaling to json: %v", err)
	}
	return &newNode, nil
}

func (n *TreeNode) IsDone() bool {
	for _, c := range n.Children {
		if !c.IsDone() {
			return false
		}
	}
	return n.Done
}

func (n *TreeNode) FindSubtaskById(id int) *TreeNode {

	if n.Id == id {
		return n
	}

	for _, c := range n.Children {

		cId := c.FindSubtaskById(id)

		if cId != nil {
			return cId
		}

	}

	return nil

}

func (n *TreeNode) Ancestors() []*TreeNode {
	ancestors := make([]*TreeNode, 0)
	for current := n; current != nil; current = current.Parent {
		ancestors = append(ancestors, current)
	}
	return ancestors
}

func (n *TreeNode) PrintableAncestors() string {
	ans := n.Ancestors()
	fmt.Printf("Ancestors = %v\n", ans)
	fmt.Printf("len Ancestors = %d\n", len(ans))
	b := strings.Builder{}
	p := strings.Builder{}
	fmt.Println("ASDF")
	for i := len(ans) - 1; 0 <= i; i-- {
		fmt.Printf("Inside the for\n")
		fmt.Fprintf(&b, "%s^---%s\n", p.String(), ans[i].Text)
		fmt.Fprint(&p, "    ")
	}

	return b.String()
}

func (n *TreeNode) UpdateDepth() {
	if n.Parent == nil {
		n.Depth = 0
	} else {
		n.Depth = n.Parent.Depth + 1
	}
}

const (
	connectExtend = " │   "
	interChild    = " ├───"
	lastChild     = " └───"
	lastTree      = "     "
)

func (n *TreeNode) PrintableTree() string {
	o := strings.Builder{}
	fmt.Fprintf(&o, "%s\n", n.Text)
	n.PrintableTreeInternal(&o, "")
	return o.String()
}

func (n *TreeNode) PrintableTreeInternal(o io.Writer, prefix string) {
	N := len(n.Children)
	for i, c := range n.Children {
		var thisPrefix string
		last := (i == N-1)
		if last {
			thisPrefix = prefix + lastChild
		} else {
			thisPrefix = prefix + interChild
		}

		fmt.Fprintf(o, "%s %s\n", thisPrefix, c.Text)

		var nextPrefix string
		if !last {
			nextPrefix = prefix + connectExtend
		} else {
			nextPrefix = prefix + lastTree
		}

		c.PrintableTreeInternal(o, nextPrefix)
	}
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
