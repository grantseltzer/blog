+++
title = "Parsing Go Binary Type Information"
Description = ""
Tags = []
Categories = []
Date = 2021-01-01T03:32:37+00:00
column = "left"
+++

In my very first blog post, [Dissecting Go Binaries](/blog/dissecting-go-binaries), I began to explore ELF files. That is the default format of executable binaries that Go produces on unix-like operating systems like Linux and MacOS. My most recent project, [weaver](https://github.com/grantseltzer/weaver), has me exploring a related object file format that Go leverages, [DWARF](http://dwarfstd.org/).

The DWARF specification is, of course, not Go specific. The DWARF object file specification describes the functions, variables, types, and more of a compiled program. Entries of a DWARF file are organized in a tree structure where each node can have children and siblings. For example, an entry node that describes a function would have children that describe the parameters. An entry node that describes a struct would have chidlren that describe the fields of it.

As the unofficial backronym for DWARF (Debugging With Attributed Record Formats) purports, the format is used by debugging tools to gather useful information such as data types or memory offsets. There's a ton of information that you can leverage for reverse engineering, debugging, or learning about systems programming. The Go standard library conveniently includes the [debug/dwarf](https://golang.org/pkg/debug/dwarf/) package for reading this information.

Let's build a program for parsing the DWARF out of any ELF binary and see what useful information we can find.

```
import (
	"debug/elf"
)

func main() {
	elfFile, err := elf.Open("/path/to/binary")
	if err != nil {
		return nil, err
	}

	dwarfData, err := elfFile.DWARF()
	if err != nil {
		return nil, err
	}

	entryReader := dwarfData.Reader()
	
	for {
		entry, err := entryReader.Next()

		// Inspect the entry
	}
}

```

First we use the `debug/elf` package to open up the file. Next we pull out the DWARF data, and create the package's notion of 'Reader'. The reader lets us parse the individual entries of the DWARF in sequence.

Now what can we do with each of these entries? Let's take a look at the definition of the `Entry` type and then go through it:

```
type Entry struct {
    Offset   Offset
    Tag      Tag
    Children bool
    Field    []Field
}
```

The `Offset` represents the offset of the DWARF entry, not to be confused with the offset of the symbol in the actual ELF binary. 

The `Tag` is a description of what this entry is. For example if the entry represents the definition of a struct the tag would be `TagStructType`. If the entry represented a function definition the tag would be `TagSubroutineType`.

`Children` is simply used to say whether subsequent entries represent child entries of the current one. For example, function parameters have separate entries from the function entry (they would have the tag `TagFormalParameter`).

Finally, the slice of `Field`'s describe various attributes about the entry. For example entries typically have a name, in which case there'd be a field that contains the entries name. There's some important info to dive into for parsing the fields so let's take a look at the type definition:

```
type Field struct {
    Attr  Attr
    Val   interface{}
    Class Class // Go 1.5
}
```
TODO:



<!-- How to parse using debug/dwarf -- > 
- How functions are stored 
  - Offset of the type definition

- How types (structs, interfaces, basic types) are stored 

<-- Higher level wrapper i'm writing


```
type SampleStruct struct {
	i int64
	j float32
	k uint8
}

func (a *SampleStruct) something() {}

func main() {

	sample := SampleStruct {
		i: 55,
		j: 12.5,
		k: 2,
	}
	
	sample.something()
}
```

We compile this with debug flags, just for the sake of disabling inling, like so:

`go build -gcflags="-N -l" -o main ./main.go`


 -->


