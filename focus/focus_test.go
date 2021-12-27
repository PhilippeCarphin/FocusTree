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
	m.Info.Done = false
	m.Info.ClosingNotes = "M Closing Notes"
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

	expected, err := os.ReadFile("../tree_manager_save_Expected.json")
	if err != nil {
		t.Fatal(err)
	}
	result, err := os.ReadFile("tree_manager_save.json")

	if string(result) != string(expected) {
		t.Fatalf("Expected '%s', got '%s'", expected, result)
	}

	// fmt.Printf("tm.PrintableTree() : '%s'\n", tm.PrintableTree())
	// fmt.Println(r.PrintableTree())

}
