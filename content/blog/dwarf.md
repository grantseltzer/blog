+++
title = "Parsing Go Binary Type Information"
Description = ""
Tags = []
Categories = []
Date = 2020-12-30T03:32:37+00:00
column = "left"
+++

<!-- Intro -->

In my very first blog post, [Dissecting Go Binaries](/blog/dissecting-go-binaries), I began to explore ELF files. That is the default format of executable binaries that Go produces on unix-like operating systems like Linux and MacOS. My most recent project, [weaver](https://github.com/grantseltzer/weaver), has me exploring a related object file format that Go leverages, [DWARF](http://dwarfstd.org/).

<!-- What is DWARF? -->

The DWARF specification is, of course, not Go specific. The DWARF object file specification describes the functions, variables, types, and more of a compiled program. Entries of a DWARF file are organized in a tree structure where each node can have children and siblings. For example, an entry node that describes a function would have children that describe the parameters. An entry node that describes a struct would have chidlren that describe the fields of it.

As the unofficial backronym for DWARF (Debugging With Attributed Record Formats) purports, the format is used by debugging tools to gather useful information such as data types or memory offsets. There's a ton of information that you can leverage for reverse engineering, debugging, or learning about systems programming. The Go standard library conveniently includes the [debug/dwarf](https://golang.org/pkg/debug/dwarf/) package for reading this information.

Let's take a look at the following program:
`test`

```
type blahblah interface {
	something()
}

type BBBBBBBBBBBB struct {
	i int64
	j int32
	k int32
	l int32
	u int64
}

type shmick int

//go:noinline
func (a BBBBBBBBBBBB) something() {}

func shmoo(b blahblah) {
	b.something()
}

func main() {
	var SHHHHHMICK shmick = 5
	ab := BBBBBBBBBBBB{}
	shmoo(ab)
	fmt.Println(SHHHHHMICK)
}

```

<!-- How to parse using debug/dwarf -->

- How functions are stored 
  - Offset of the type definition

- How types (structs, interfaces, basic types) are stored 

<!-- Higher level wrapper i'm writing -->
