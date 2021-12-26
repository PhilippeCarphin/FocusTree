package focus

import (
	"encoding/json"
	"testing"
	"fmt"
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
func TestPrintableTree(t *testing.T) {
	TreeNodeIdCounter = 0
	n := NewTreeNode()
	m := NewTreeNode()
	w := NewTreeNode()
	q := NewTreeNode()
	p := NewTreeNode()
	q.Text = "Q Text"
	p.Text = "P Text"
	w.Text = "W Text"
	m.Text = "M Text"
	n.Text = "N Text"
	n.AddChild(m)
	n.AddChild(w)
	m.AddChild(p)
	m.AddChild(q)
	fmt.Println(m.PrintableTree())
	fmt.Println(n.PrintableTree())
}
