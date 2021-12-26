package focus

import (
	"encoding/json"
	// "fmt"
	"os"
	"testing"
)

func TestBuildTree(t *testing.T) {
	n := NewTreeNode()
	tm := NewTreeManager()
	tm.AddRootNode(n)
	if len(tm.RootNodes) != 1 {
		t.Fail()
	}
	return
}

func TestJson(t *testing.T) {
	n := NewTreeNode()
	m := NewTreeNode()
	m.Text = "M Text"
	m.Done = false
	m.ClosingNotes = "M Closing Notes"
	n.AddChild(m)
	b, err := json.MarshalIndent(n, "   ", "   ")
	if err != nil {
		t.Fatalf("Error marshaling to json: %v", err)
	}
	if len(b) < 100 {
		t.Fatalf("JSON string is too short")
	}

	var newNodeR TreeNode
	newNode := &newNodeR
	err = json.Unmarshal(b, newNode)
	if err != nil {
		t.Fatalf("Error marshaling to json: %v", err)
	}
	return
}

func TestFindById(t *testing.T) {
	TreeNodeIdCounter = 0
	n := NewTreeNode()
	m := NewTreeNode()
	m.Text = "M Text"
	n.Text = "N Text"
	n.AddChild(m)

	x := n.FindSubtaskById(1)
	if x == nil {
		t.Fatalf("Should have found node with Id 1 but didn't")
	}
}

func TestAncestors(t *testing.T) {
	TreeNodeIdCounter = 0
	n := NewTreeNode()
	m := NewTreeNode()
	m.Text = "M Text"
	n.Text = "N Text"
	n.AddChild(m)
	if len(m.Ancestors()) != 2 {
		t.Fatalf("M's ancestor list should be 2 long")
	}
	if len(n.Ancestors()) != 1 {
		t.Fatalf("N's ancestor list should be 1 long")
	}
}

func TestPrintableAncestors(t *testing.T) {
	TreeNodeIdCounter = 0
	n := NewTreeNode()
	m := NewTreeNode()
	m.Text = "M Text"
	n.Text = "N Text"
	n.AddChild(m)
	// fmt.Println(m.PrintableAncestors())
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

func TestPrintableTree(t *testing.T) {
	r := newTestTree()
	expected := `R Text
 ├─── M Text
 │    ├─── P Text
 │    └─── Q Text
 └─── N Text
      ├─── W Text
      │    └─── Z Text
      └─── X Text
           └─── Y Text
`
	result := r.PrintableTree()
	if result != expected {
		t.Fatalf("Expected '%s'\nGot '%s'", expected, result)
	}
}

func TestSaveTreeManager(t *testing.T) {
	r := newTestTree()
	tm := NewTreeManager()

	tm.RootNodes = append(tm.RootNodes, r)

	tm.ToFile("tree_manager_save.json")

	expected, err := os.ReadFile("tree_manager_save_Expected.json")
	if err != nil {
		t.Fatal(err)
	}
	result, err := os.ReadFile("tree_manager_save.json")

	if string(result) != string(expected) {
		t.Fatalf("Expected '%s', got '%s'", expected, result)
	}

}
