package focus

import (
	"encoding/json"
	"fmt"
	"github.com/gorilla/mux"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
)

var TheTreeManager *TreeManager = nil

var TreeNodeIdCounter = 0

type TreeNode struct {
	Text     string       `json:"text"`
	Id       int          `json:"id"`
	Info     TreeNodeInfo `json:"info"`
	Children []*TreeNode  `json:"children"`
	Parent   *TreeNode    `json:"-"` // Must be ignored for JSON or cycles get created
	Depth    int          `json:"-"`
	Manager  *TreeManager `json:"-"`
}

type TreeNodeInfo struct {
	Done         bool   `json:"done"`
	CreatedOn    string `json:"created"`
	ClosingNotes string `json:"closing_notes"`
	FinishedOn   string `json:"finished"`
}

type TreeManager struct {
	RootNodes     []*TreeNode `json:"root_nodes"`
	CurrentTask   string      `json:"current_task"`
	Current       *TreeNode   `json:"-"`
	CurrentTaskId int         `json:"current_task_id"`
	moveStack     []*TreeNode `json:"-"`
}

func NewTreeManager() *TreeManager {
	return &TreeManager{
		RootNodes: make([]*TreeNode, 0),
		moveStack: make([]*TreeNode, 0),
	}
}

func FocusTreeServer() {
	var err error
	TheTreeManager, err = TreeManagerFromFile("FocusTree.service.save_file.json")
	if err != nil {
		panic(err)
	}

	m := mux.NewRouter()
	m.HandleFunc("/", TheTreeManager.handleRequest).Methods("GET")
	m.HandleFunc("/api/tree", TheTreeManager.handleRequest).Methods("GET")
	m.HandleFunc("/api/send-command", TheTreeManager.handleCommand).Methods("POST")

	l, err := net.Listen("tcp", "0.0.0.0:5052")
	if err != nil {
		panic(err)
	}
	// p := l.Addr().(*net.TCPAddr).Port

	http.Serve(l, m)
}

func (tm *TreeManager) handleRequest(w http.ResponseWriter, r *http.Request) {
	j, err := json.MarshalIndent(TheTreeManager, "    ", "    ")
	if err != nil {
		fmt.Printf("Error Could not marshal tree to JSON : %v", err)
	}
	w.Write(j)
}

type TerminalClientResponse struct {
	Error      string   `json:"error"`
	TermOutput string   `json:"term_output"`
	Command    string   `json:"command"`
	Status     int      `json:"status"`
}

func (tm *TreeManager) handleCommand(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		fmt.Printf("Error getting body of request : %v", err)
	}

	var tr = TerminalClientResponse{
		Status:     0,
		Command: string(body),
	}
	words := strings.Split(string(body), " ")
	command := words[0]
	switch command {
	case "current":
		tr.TermOutput = TheTreeManager.Current.PrintableAncestors()
	case "tree":
		tr.TermOutput = TheTreeManager.PrintableTree("")
	case "subtask":
	default:
		tr.TermOutput = ""
		tr.Error = fmt.Sprintf("Unknown command %s", string(body))
		tr.Status = 1
		fmt.Println(string(body))
	}

	j, err := json.Marshal(tr)
	if err != nil {
		fmt.Println(err)
	}
	w.Write(j)
}
func (tm *TreeManager) Move(n *TreeNode) {
	tm.moveStack = append(tm.moveStack, tm.Current)
	tm.Current = n
}

func (tm *TreeManager) ToFile(filename string) error {
	if tm.Current != nil {
		tm.CurrentTaskId = tm.Current.Id
	}
	b, err := json.Marshal(tm)
	if err != nil {
		return err
	}
	return os.WriteFile(filename, b, 0644)
}

func TreeManagerFromFile(filename string) (*TreeManager, error) {
	tm := TreeManager{}
	b, err := os.ReadFile(filename)
	if err != nil {
		return nil, fmt.Errorf("Error reading tree manager file : %v", err)
	}
	err = json.Unmarshal(b, &tm)
	if err != nil {
		return nil, fmt.Errorf("Error unmarshaling contents of file : %v", err)
	}

	for _, r := range tm.RootNodes {
		setParents(r)
	}


	tm.Current = tm.FindSubtaskById(tm.CurrentTaskId)

	// Reassigning IDs is how I'm making the global TreeNodeIdCounter
	// go up after having read the file.  Since json.Unmarshal does
	// not use the constructor which would increment the counter, the
	// counter would still be at 0 after having loaded the file.
	//
	// In Python, The constructor is run each time a node is created, but
	// in the from_dict method, the ID used is the one from the JSON.
	// But creating the node still increments the counter so at the end,
	// the counter is qual to the number of nodes but nothing prevents the
	// file from having IDs that would cause problems:
	//
	// Suppose we have tree nodes with Ids 2,3,4.  Then in Python, after
	// reading the file, the counter will be at 3, and the next time we
	// create add a node to the tree, it will be given the id 3.
	// If we want the nodes to keep the Ids from the file, we should find
	// the maximum of the Ids and set the counter one above that.

	tm.ReassignIds()
	tm.CurrentTaskId = tm.Current.Id

	return &tm, nil
}
func visit(n *TreeNode, f func(*TreeNode)) {
	f(n)
	for _,c := range n.Children {
		visit(c, f)
	}
}

func (tm *TreeManager) ReassignIds() {
	var currentId int = 0
	giveId :=  func(n *TreeNode) {
		n.Id = currentId
		currentId++
	}
	for _, r := range tm.RootNodes {
		visit(r, giveId)
	}
	TreeNodeIdCounter = currentId
}

func (tm *TreeManager) maxId() int {
	var max = 0
	for _, r := range tm.RootNodes {
		m := r.maxId()
		if m > max {
			max = m
		}
	}
	return max

}

func (n *TreeNode) maxId() int {
	var max = 0
	for _, c := range n.Children {
		m := c.maxId()
		if m > max {
			max = m
		}
	}
	if n.Id > max {
		max = n.Id
	}
	return max
}

func setParents(tree *TreeNode) {
	for _, c := range tree.Children {
		c.Parent = tree
		setParents(c)
	}
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

func (tm *TreeManager) PrintableTree(prefix string) string {
	tree := strings.Builder{}
	for _, r := range tm.RootNodes {
		fmt.Fprint(&tree, r.PrintableTree(prefix))
	}
	return tree.String()
}

func NewTreeNode() *TreeNode {

	newNode := &TreeNode{
		Id: TreeNodeIdCounter,
		Info: TreeNodeInfo{
			CreatedOn: "Now",
		},
		Children: make([]*TreeNode, 0),
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
	return n.Info.Done
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
	b := strings.Builder{}
	p := strings.Builder{}
	for i := len(ans) - 1; 0 <= i; i-- {
		fmt.Fprintf(&b, "%s%s%s\n", p.String(), lastChild, ans[i].Text)
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

func (n *TreeNode) PrintableTree(prefix string) string {
	o := strings.Builder{}
	fmt.Fprintf(&o, "%s\n", n.Text)
	n.PrintableTreeInternal(&o, prefix)
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

func (tm *TreeManager) Subtask(t *TreeNode) error {
	tm.Current.AddChild(t)
	tm.Current = t
	return nil
}

func (tm *TreeManager) NewTask(t *TreeNode) error {
	tm.RootNodes = append(tm.RootNodes, t)
	return nil
}

func (tm *TreeManager) NextTask(t *TreeNode) error {
	parent := tm.Current.Parent
	if parent == nil {
		tm.RootNodes = append(tm.RootNodes, t)
	} else {
		parent.AddChild(t)
	}
	return nil
}

func (tm *TreeManager) Done(closingNotes string) error {
	// Change 'Done' attribute of current task
	// Look for descendants of current task that are not done
	// Look for descendant of parent that is not done
	// keep going until parent is nil
	// Look for descendant of next root nodes that are not done
	return nil
}

func (tm *TreeManager) FindSubtaskById(id int) *TreeNode {
	for _, r := range tm.RootNodes {
		n := r.FindSubtaskById(id)
		if n != nil {
			return n
		}
	}
	return nil
}

func (tm *TreeManager) SwitchTask(id int) error {
	n := tm.FindSubtaskById(id)
	if n == nil {
		return fmt.Errorf("No node with id '%d' was found", id)
	}

	tm.Current = n
	return nil
}

func newTestTree() *TreeNode {
	TreeNodeIdCounter = 0
	r := NewTreeNode()
	r.Text = "R Text"

	n := NewTreeNode()
	n.Text = "N Text"
	m := NewTreeNode()
	m.Text = "M Text"

	w := NewTreeNode()
	w.Text = "W Text"
	x := NewTreeNode()
	x.Text = "X Text"
	y := NewTreeNode()
	y.Text = "Y Text"
	z := NewTreeNode()
	z.Text = "Z Text"

	q := NewTreeNode()
	p := NewTreeNode()
	q.Text = "Q Text"
	p.Text = "P Text"

	r.AddChild(m)
	r.AddChild(n)

	n.AddChild(w)
	n.AddChild(x)
	x.AddChild(y)
	w.AddChild(z)

	m.AddChild(p)
	m.AddChild(q)

	return r
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
