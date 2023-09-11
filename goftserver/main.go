package main

import (
	"flag"
	"github.com/philippecarphin/FocusTree/focus"
)

func main() {
	var port int
	var file string
	var host string

	flag.IntVar(&port, "port", 5051, "Port on which to start the server")
	flag.StringVar(&file, "file", "", "File to use load and save tree")
	flag.StringVar(&host, "host", "0.0.0.0", "Host on which to run server")
	flag.Parse()

	focus.FocusTreeServer(port, host, file)
}
