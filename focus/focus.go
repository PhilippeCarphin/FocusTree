package focus

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/gorilla/mux"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strconv"
	"strings"
)

var TheTreeManager *TreeManager = nil

var TheToken string = "1234"

var TreeNodeIdCounter = 0

type TreeNode struct {
	Text                string       `json:"text"`
	Id                  int          `json:"id"`
	Info                TreeNodeInfo `json:"info"`
	Children            []*TreeNode  `json:"children"`
	Parent              *TreeNode    `json:"-"` // Must be ignored for JSON or cycles get created
	Depth               int          `json:"-"`
	Manager             *TreeManager `json:"-"`
	IsAncestorOfCurrent bool         `json:"-"`
}

type TreeNodeInfo struct {
	Done         bool   `json:"done"`
	CreatedOn    string `json:"created"`
	ClosingNotes string `json:"closing_notes"`
	FinishedOn   string `json:"finished"`
}

type TreeManager struct {
	File          string      `json:"-"`
	RootNodes     []*TreeNode `json:"root_nodes"`
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

func DefaultFileName(port int) string {
	return fmt.Sprintf(".focustree.save.%d.json", port)
}

func FindFocusTree(port int) (*TreeManager, error) {
	d, err := os.Getwd()
	base := DefaultFileName(port)
	if err != nil {
		return nil, fmt.Errorf("Could not get cwd: %v", err)
	}
	for ; ; d = path.Dir(d) {
		file := path.Join(d, base)
		t, err := TreeManagerFromFile(file)
		if err == nil {
			fmt.Printf("Using tree file '%s' found from directory search\n", file)
			return t, nil
		}

		if d == "" || d == "/" {
			// return nil, fmt.Errorf("Reached filesystem root without finding tree file")
			break
		}
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return nil, fmt.Errorf("Could not get user home: %v", err)
	}
	file := path.Join(home, base)
	fmt.Printf("Using file from '%s' from home directory\n", file)

	if _, err := os.Stat(file); errors.Is(err, os.ErrNotExist) {
		tm := NewTreeManager()
		tm.File = file
		tm.ToFile()
	}
	return TreeManagerFromFile(file)
}

func FocusTreeServer(port int, host string, file string) error {
	if file == "" {
		t, err := FindFocusTree(port)
		if err != nil {
			return fmt.Errorf("could not load focus tree file: %v", err)
		}
		TheTreeManager = t
	} else {
		t, err := TreeManagerFromFile(file)
		if err != nil {
			return fmt.Errorf("could not get Focus Tree from file '%s': %v", file, err)
		}
		TheTreeManager = t
	}

	if TheTreeManager == nil {
		return fmt.Errorf("Unexpected error: TheTreeManager is nil")
	}

	fmt.Printf("Using '%s' as Tree file\n", TheTreeManager.File)

	home, err := os.UserHomeDir()
	if err != nil {
		panic(err)
	}
	tokenFile := path.Join(home, ".ssh", "ftserver_token")
	content, err := os.ReadFile(tokenFile)
	if err != nil {
		return fmt.Errorf("Could not get auth token from file '%s': %v", tokenFile, err)
	}
	TheToken = strings.Trim(string(content), " \n")
	fmt.Printf("The token is '%s'\n", TheToken)

	m := mux.NewRouter()
	m.HandleFunc("/", TheTreeManager.sendTree).Methods("GET")
	m.HandleFunc("/favicon.ico", Favicon).Methods("GET")
	m.HandleFunc("/api/tree", TheTreeManager.sendTree).Methods("GET")
	m.HandleFunc("/api/send-command", TheTreeManager.handleCommand).Methods("POST")
	m.PathPrefix("/simple-client").HandlerFunc(ServeWebApp).Methods("GET")
	m.HandleFunc("/api/current", TheTreeManager.currentContext).Methods("GET")
	m.HandleFunc("/authenticate", Authenticate).Methods("POST")

	l, err := net.Listen("tcp", fmt.Sprintf("%s:%d", host, port))
	if err != nil {
		panic(err)
	}
	fmt.Printf("Starting server on host %s, port %d\n", host, port)
	fmt.Printf("Visit web client with 'http://%s:%d/simple-client?ftserver_token=%s\n", host, port, TheToken)

	http.Serve(l, m)
	return nil
}

func Authenticate(w http.ResponseWriter, r *http.Request) {

	body, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	fmt.Fprintf(os.Stderr, "Authenticate: body: '%s'", body)
	w.Header().Set("Set-Cookie", fmt.Sprintf("ftserver_token=%s;", body))
	w.WriteHeader(http.StatusOK)
}

func VerifyCookieRequest(r *http.Request) (bool, error) {
	cookiesStr := r.Header.Get("Cookie")
	if cookiesStr == "" {
		return false, nil
	}
	cookies, err := http.ParseCookie(cookiesStr)
	if err != nil {
		return false, err
	}
	for _, cookie := range cookies {
		fmt.Printf("Cookie: %#v\n", cookie)
		if cookie.Name == "ftserver_token" && cookie.Value == TheToken {
			fmt.Fprintf(os.Stderr, "Cookie authentication SUCCESSFUL\n")
			return true, nil
		}
	}

	return false, nil
}

func rootPath() (string, error) {
	// In installed situation, the execuable is in ${root}/bin and the root
	// is $(cd $(dirname $0)/.. && pwd), and in the build situation, assuming
	// a build directory inside the source dir, this same code will give the
	// source directory.  So we will reach the client as well.
	ex, err := os.Executable()
	if err != nil {
		return "", err
	}
	return path.Join(filepath.Dir(ex), ".."), nil
}

// Favicon tree from https://www.iconpacks.net/free-icon/bonsai-tree-5206.html
func Favicon(w http.ResponseWriter, r *http.Request) {
	root, err := rootPath()
	if err != nil {
		panic(err)
	}
	favicon := path.Join(root, "share", "FocusTree", "clients", "basic_js_client", "favicon.png")
	fmt.Printf("Serving favicon :'%s'\n", favicon)
	http.ServeFile(w, r, favicon)
}

func ServeWebApp(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("Serving web app")
	fmt.Printf("Request : r.URL.Path() -> %s\n", r.URL.Path)
	file := strings.TrimPrefix(r.URL.Path, "/simple-client")
	fmt.Printf("Rest of path: %s\n", file)

	if file == "/" {
		file = "/index.html"
	}

	root, err := rootPath()
	if err != nil {
		panic(err)
	}
	webAppPath := path.Join(root, "share", "FocusTree", "clients", "basic_js_client")
	filePath := path.Join(webAppPath, file)
	fmt.Printf("Serving file %s\n", filePath)

	if r.URL.Query().Get("ftserver_token") == TheToken {
		w.Header().Set("Set-Cookie", fmt.Sprintf("ftserver_token=%s; Path=/", TheToken))
	}

	http.ServeFile(w, r, filePath)
}

func (tm *TreeManager) sendTree(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("sendTree(): Sending tree in JSON form\n")
	j, err := json.MarshalIndent(TheTreeManager, "    ", "    ")
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		fmt.Printf("Error Could not marshal tree to JSON : %v", err)
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/json")
	w.Write(j)
}

// currentContext creates a subtree which is a path from a root node to the
// current task and sends this tree in JSON form as the response.
func (tm *TreeManager) currentContext(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("currentContext(): Sending current context in JSON form\n")
	/*
	 * Create the list of pointers to the relevant nodes
	 */
	path := make([]*TreeNode, 0)
	current := tm.Current
	for current != nil {
		path = append([]*TreeNode{current}, path...)
		current = current.Parent
	}
	p, err := json.Marshal(path)
	if err != nil {
		fmt.Printf("currentContext(): ERROR: Could not marshal node path\n")
	}
	w.Write(p)
}

type TerminalClientResponse struct {
	Error      string `json:"error"`
	TermOutput string `json:"term_output"`
	Command    string `json:"command"`
	Status     int    `json:"status"`
}

func (tm *TreeManager) FindIncompleteFromCurrent() (*TreeNode, error) {

	c := tm.Current

	for ; c != nil; c = c.Parent {
		fmt.Printf("FindIncompleteFromCurrent() Examining parent of current : %v\n", c)
		u, err := c.FindIncompleteChild()
		if err != nil {
			panic(err)
		}
		if u != nil {
			fmt.Printf("FindIncompleteFromCurrent() Setting current node to %v\n", u)
			tm.ChangeCurrent(u)
			return u, nil
		}
	}

	for _, r := range tm.RootNodes {
		fmt.Printf("FindIncompleteFromCurrent() Examining root node : %v\n", r)
		fmt.Println(r.Text)
		u, err := r.FindIncompleteChild()
		if err != nil {
			panic(err)
		}
		if u != nil {
			fmt.Printf("FindIncompleteFromCurrent() Setting current node to %v\n", u)
			tm.ChangeCurrent(u)
			return u, nil
		}
	}

	return nil, nil
}

func (tm *TreeManager) Reset() error {
	tm.RootNodes = make([]*TreeNode, 0)
	tm.Current = nil
	tm.CurrentTaskId = 0
	return nil
}

type FtclientPayload struct {
	Command string
	Token   string
	Html    bool
}

func (tm *TreeManager) handleCommand(w http.ResponseWriter, r *http.Request) {

	body, err := io.ReadAll(r.Body)
	if err != nil {
		fmt.Printf("Error getting body of request : %v", err)
	}

	var payload FtclientPayload
	json.Unmarshal(body, &payload)
	fmt.Printf("Received Token = '%s'\n", strings.Trim(payload.Token, " \n"))
	fmt.Printf("      TheToken = '%s'\n", TheToken)

	cookieOk, err := VerifyCookieRequest(r)
	if err != nil {
		fmt.Printf("Error checking cookie: %v\n", err)
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	if strings.Trim(payload.Token, " \n") != TheToken && !cookieOk {
		fmt.Println("Unauthorized access attempted")

		var tr = TerminalClientResponse{
			Status:  1,
			Command: string(body),
			Error:   "Access denied your token does not match server token",
		}

		j, err := json.Marshal(tr)
		if err != nil {
			fmt.Println(err)
		}
		w.WriteHeader(http.StatusUnauthorized)
		w.Write(j)

		return
	} else {
		fmt.Println("Token authorization successful, proceeding with request")
	}

	words := strings.Split(payload.Command, " ")
	command := words[0]
	args := words[1:]
	fmt.Printf("handleCommand(): Comand : %s, Args : %s (len(args): %d)\n", command, args, len(args))

	var tr = TerminalClientResponse{
		Status:  0,
		Command: string(body),
	}
	switch command {
	case "reset":
		tm.Reset()
		tr.TermOutput = "No current task\n" + tm.PrintableTree("")

	case "current":
		if tm.Current == nil {
			tr.TermOutput = "No current task\n" + tm.PrintableTree("")
		} else {
			tr.TermOutput = tm.Current.PrintableAncestors()
		}
	case "tree":
		tr.TermOutput = tm.PrintableTree("")
	case "subtask":
		t := NewTreeNode()
		t.Text = strings.Join(args, " ")
		if tm.Current == nil {
			tm.AddRootNode(t)
		} else {
			tm.Current.AddChild(t)
		}
		tm.ChangeCurrent(t)

		tr.TermOutput = tm.Current.PrintableAncestors()
	case "new-task", "new":
		t := NewTreeNode()
		t.Text = strings.Join(args, " ")

		tm.AddRootNode(t)

		tr.TermOutput = tm.PrintableTree("")
	case "next-task", "next":
		t := NewTreeNode()
		t.Text = strings.Join(args, " ")

		if tm.Current == nil || tm.Current.Parent == nil {
			tm.AddRootNode(t)
		} else {
			tm.Current.Parent.AddChild(t)
		}

		tr.TermOutput = tm.PrintableTree("")
	case "switch-task":
		if len(args) == 0 || args[0] == "" {
			tr.Status = 1
			tr.Error = "Command requires ID as argument"
			break
		}

		id64, err := strconv.ParseInt(args[0], 0, 0)
		if err != nil {
			tr.Status = 1
			tr.Error = fmt.Sprintf("Could not parse numeric ID from '%s': %v", args[0], err)
			break
		}
		id := int(id64)

		n := tm.FindSubtaskById(id)
		if n == nil {
			tr.Status = 1
			tr.Error = fmt.Sprintf("Could not find node with ID '%d'", id)
			break
		}
		tm.ChangeCurrent(n)
		fmt.Printf("Set current task by ID to %s\n", n)
	case "delete-task", "delete":
		if len(args) == 0 || args[0] == "" {
			tr.Status = 1
			tr.Error = "Command requires ID as argument"
			break
		}

		id64, err := strconv.ParseInt(args[0], 0, 0)
		if err != nil {
			tr.Status = 1
			tr.Error = fmt.Sprintf("Could not parse numeric ID from '%s': %v", args[0], err)
			break
		}
		id := int(id64)

		n := tm.FindSubtaskById(id)
		if n == nil {
			tr.Status = 1
			tr.Error = fmt.Sprintf("Could not find node with ID '%d'", id)
			break
		}
		err = tm.DeleteTaskById(id)
		if err != nil {
			tr.Error = fmt.Sprintf("%v", err)
			tr.Status = 1
		}
		tr.TermOutput = fmt.Sprintf("Deleted task with id %d: '%s'", id, n.Text)
	case "info":
		var id int
		if len(args) == 0 {
			id = tm.CurrentTaskId
		} else {
			id64, err := strconv.ParseInt(args[0], 0, 0)
			if err != nil {
				tr.Status = 1
				tr.Error = fmt.Sprintf("Could not parse numeric ID from '%s': %v", args[0], err)
				break
			}
			id = int(id64)
		}
		n := tm.FindSubtaskById(id)
		if n == nil {
			tr.Status = 1
			tr.Error = fmt.Sprintf("Could not find node with ID '%d'", id)
			break
		}
		tr.TermOutput = fmt.Sprintf("Info on task %d - \033[1;37m%s\033[0m: \n\tDone: %t,\n\tClosingNotes: %s\n", id, n.Text, n.Info.Done, n.Info.ClosingNotes)
	case "not-done":
		if tm.Current == nil {
			tr.Status = 1
			tr.Error = fmt.Sprintf("No current task")
			break
		}
		tm.Current.Info.Done = false
		tr.Status = 0
		tr.TermOutput = fmt.Sprintf("Marked current task as Not Done")
	case "subtask-by-id":
		var id int
		nbRead, err := fmt.Sscanf(args[0], "%d", &id)
		if err != nil {
			panic(err)
		}
		if nbRead == 0 {
			panic("No bytes read")
		}
		n := tm.FindSubtaskById(id)

		t := NewTreeNode()
		t.Text = strings.Join(args[1:], " ")
		n.AddChild(t)
		tr.TermOutput = tm.PrintableTree("")
	case "done":
		if tm.Current == nil {
			tr.TermOutput = "No current task"
			tr.Status = 1
			tr.Error = "No current task to mark done"
			break
		}

		tm.Current.Info.Done = true
		tm.Current.Info.ClosingNotes = strings.Join(args, " ")

		tm.Current, err = tm.FindIncompleteFromCurrent()
		if err != nil {
			panic(err)
		}
		if tm.Current == nil {
			tr.TermOutput = "No current task"
		} else {
			tr.TermOutput = tm.Current.PrintableAncestors()
		}
	case "reassign-ids":
		tm.ReassignIds()
	default:
		tr.TermOutput = ""
		tr.Error = fmt.Sprintf("(goftserver) Unknown command %s", string(body))
		tr.Status = 1
		fmt.Println(string(body))
	}

	if payload.Html {
		html, err := ansiToHtml(tr.TermOutput)
		if err == nil {
			tr.TermOutput = html
		} else {
			fmt.Fprintf(os.Stderr, "Could not convert TermOutput to html: %v", err)
			tr.Error = fmt.Sprintf("Failed to convert output to HTML: %v", err)
		}
	}

	j, err := json.Marshal(tr)
	if err != nil {
		fmt.Println(err)
	}
	tm.ToFile()
	w.Write(j)
}

func ansiToHtml(ansi string) (string, error) {
	c := exec.Command("aha", "-b", "--no-header")
	p, err := c.StdinPipe()
	if err != nil {
		return "", err
	}
	p.Write([]byte(ansi))
	p.Close()

	out, err := c.Output()
	if err != nil {
		return "", err
	}
	return string(out), nil
}

func (t *TreeNode) FindIncompleteChild() (*TreeNode, error) {

	for _, c := range t.Children {
		u, err := c.FindIncompleteChild()
		if err != nil {
			return nil, err
		}
		if u != nil {
			return u, nil
		}
	}

	if !t.Info.Done {
		return t, nil
	}

	return nil, nil
}

func (tm *TreeManager) Move(n *TreeNode) {
	tm.moveStack = append(tm.moveStack, tm.Current)
	tm.ChangeCurrent(n)
}

func (tm *TreeManager) ToFile() error {
	if tm.Current != nil {
		tm.CurrentTaskId = tm.Current.Id
	}
	b, err := json.MarshalIndent(tm, "\t", "	")
	if err != nil {
		return err
	}
	return os.WriteFile(tm.File, b, 0644)
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
		tm.setParents(r)
	}

	// tm.Current = tm.FindSubtaskById(tm.CurrentTaskId)
	if len(tm.RootNodes) > 0 && tm.CurrentTaskId != -1 {
		err := tm.ChangeCurrentById(tm.CurrentTaskId)
		if err != nil {
			return nil, err
		}
		if tm.Current == nil {
			fmt.Printf("Could not set current node according to current_task_id %d\n", tm.CurrentTaskId)
		} else {
			fmt.Printf("Current task is %v\n", tm.Current)
		}
	}

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
	if tm.Current != nil {
		tm.CurrentTaskId = tm.Current.Id
	} else {
		tm.CurrentTaskId = -77
	}

	tm.File = filename

	return &tm, nil
}
func visit(n *TreeNode, f func(*TreeNode)) {
	f(n)
	for _, c := range n.Children {
		visit(c, f)
	}
}

func (tm *TreeManager) ReassignIds() {
	var currentId int = 0
	giveId := func(n *TreeNode) {
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

func (tm *TreeManager) setParents(tree *TreeNode) {
	tree.Manager = tm
	for _, c := range tree.Children {
		c.Parent = tree
		tm.setParents(c)
	}
}

func (tm *TreeManager) BacktrackMove() *TreeNode {
	last := len(tm.moveStack) - 1
	top := tm.moveStack[last]
	tm.moveStack = tm.moveStack[:last]
	tm.ChangeCurrent(top)
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
		color := "\033[31m"
		if r.IsDone() {
			color = "\033[32m"
		}
		fmt.Fprintf(&tree, "%s\u2b95\033[0m %s", color, r.PrintableTree("   "+prefix))
	}
	return tree.String()
}

func (n *TreeNode) IsDone() bool {
	if n.Info.Done == false {
		return false
	}

	for _, c := range n.Children {
		if !c.IsDone() {
			return false
		}
	}

	return true
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

// func (n *TreeNode) IsDone() bool {
// 	for _, c := range n.Children {
// 		if !c.IsDone() {
// 			return false
// 		}
// 	}
// 	return n.Info.Done
// }

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

func (n *TreeNode) String() string {
	bulletColor := "\033[94m"
	textColor := "\033[0m"
	manager := n.Manager
	if n.Info.Done {
		bulletColor = "\033[32m"
	} else {
		bulletColor = "\033[34m"
	}

	if manager != nil {
		if n == n.Manager.Current {
			textColor = "\033[1;37m"
			bulletColor = "\033[35m"
		} else if n.IsAncestorOfCurrent {
			textColor = "\033[1m"
		}
	}

	return fmt.Sprintf("\033[90m[%d]\033[0m %s\u2b24 \033[0m %s%s\033[0m", n.Id, bulletColor, textColor, n.Text)
}

func (tm *TreeManager) ChangeCurrent(newCurrent *TreeNode) {
	if tm.Current != nil {
		for cursor := tm.Current; cursor != nil; cursor = cursor.Parent {
			cursor.IsAncestorOfCurrent = false
		}
	}
	tm.Current = newCurrent
	tm.CurrentTaskId = newCurrent.Id
	for cursor := tm.Current; cursor != nil; cursor = cursor.Parent {
		cursor.IsAncestorOfCurrent = true
	}
}

func (tm *TreeManager) ChangeCurrentById(id int) error {
	newCurrent := tm.FindSubtaskById(id)
	if newCurrent == nil {
		return fmt.Errorf("could not find task with ID %d", id)
	}
	tm.ChangeCurrent(newCurrent)
	return nil
}

func (n *TreeNode) PrintableAncestors() string {
	ans := n.Ancestors()
	b := strings.Builder{}
	prefix := strings.Builder{}
	for i := len(ans) - 1; 0 <= i; i-- {
		fmt.Fprintf(&b, "%s%s%s\n", prefix.String(), lastChild, ans[i])
		fmt.Fprint(&prefix, "    ")
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
	fmt.Fprintf(&o, "%s\n", n)
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

		fmt.Fprintf(o, "%s %s\n", thisPrefix, c)

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
	tm.ChangeCurrent(t)
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

func (tm *TreeManager) DeleteTaskById(id int) error {
	toDelete := tm.FindSubtaskById(id)
	if toDelete == nil {
		return fmt.Errorf("Could not find node with id %d", id)
	}

	parent := toDelete.Parent
	var indexToRemove int
	if parent == nil {
		for i, r := range tm.RootNodes {
			if r.Id == id {
				indexToRemove = i
				break
			}
		}
		tm.RootNodes = append(tm.RootNodes[:indexToRemove], tm.RootNodes[indexToRemove+1:]...)
	} else {
		for i, c := range parent.Children {
			if c.Id == id {
				indexToRemove = i
				break
			}
		}
		parent.Children = append(parent.Children[:indexToRemove], parent.Children[indexToRemove+1:]...)
	}
	return nil
}

func (tm *TreeManager) SwitchTask(id int) error {
	n := tm.FindSubtaskById(id)
	if n == nil {
		return fmt.Errorf("No node with id '%d' was found", id)
	}

	tm.ChangeCurrent(n)
	return nil
}

func NewTestTree() *TreeNode {
	return newTestTree()
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
