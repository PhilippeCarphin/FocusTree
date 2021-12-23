package focus

import (
	"encoding/json"
	"fmt"
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
	fmt.Println(string(b))

	var newNodeR TreeNode
	newNode := &newNodeR
	err = json.Unmarshal(b, newNode)
	if err != nil {
		t.Fatalf("Error marshaling to json: %v", err)
	}
	fmt.Println(newNode)
	fmt.Println(newNode.Children[0])
	return
}
