package main

import (
	"flag"
	// "fmt"
	"github.com/philippecarphin/FocusTree/focus"
)

func main() {
	var port int
	var file string
	var host string
	var new bool

	flag.IntVar(&port, "port", 5051, "Port on which to start the server")
	flag.StringVar(&file, "file", "", "File to use load and save tree")
	flag.StringVar(&host, "host", "0.0.0.0", "Host on which to run server")
	flag.BoolVar(&new, "new", false, "Create empty tree with filename")
	flag.Parse()

	// if new {
	// 	tm := focus.NewTreeManager()
	// 	tm.File = file
	// 	tm.ToFile()
	// }

	focus.FocusTreeServer(port, host, file)
}
