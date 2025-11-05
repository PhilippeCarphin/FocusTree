package main

import (
	"flag"
	"fmt"
	"os"
	"github.com/philippecarphin/FocusTree/focus"
)


func main() {

	var port int
	var file string
	var host string
	var new bool
	var search bool

	flag.IntVar(&port, "port", 5051, "Port on which to start the server")
	flag.StringVar(&file, "file", "", "File to use load and save tree")
	flag.StringVar(&host, "host", "0.0.0.0", "Host on which to run server")
	flag.BoolVar(&new, "new", false, "Create empty tree with filename")
	flag.BoolVar(&search, "search", false, "Search for focustree file by going up the filesystem")
	flag.Parse()

	if new {
		tm := focus.NewTreeManager()
		tm.File = file
		err := tm.ToFile()
		if err != nil {
			fmt.Printf("\033[1;31mERROR\033[0m: %v\n", err)
			os.Exit(1)
		}
	}

	err := focus.FocusTreeServer(port, host, file, search)
	if err != nil {
		fmt.Printf("\033[1;31mERROR\033[0m: %v\n", err)
		os.Exit(1)
	}
}
