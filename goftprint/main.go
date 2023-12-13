package main

import (
	"fmt"
	"os"
	"flag"
	"github.com/philippecarphin/FocusTree/focus"
)

func main() {
	var file string
	flag.StringVar(&file, "file", "", "File to use load and save tree")
	flag.Parse()

	t, err := focus.TreeManagerFromFile(file)
	if err != nil {
		fmt.Printf("Could not get Focus Tree from file '%s': %v\n", file, err)
		os.Exit(1)
	}

	fmt.Print(t.PrintableTree(""))

}
