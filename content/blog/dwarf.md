+++
title = "Parsing Go Binary DWARF Info"
Description = ""
Tags = []
Categories = []
Date = 2021-01-02T03:32:37+00:00
column = "left"
+++

In my very first blog post, [Dissecting Go Binaries](/blog/dissecting-go-binaries), I began to explore ELF files. That is the default format of executable binaries that Go produces on unix-like operating systems like Linux and MacOS. My most recent project, [weaver](https://github.com/grantseltzer/weaver), has me exploring a related object file format that Go leverages, [DWARF](http://dwarfstd.org/).

The DWARF specification is, of course, not Go specific. The DWARF object file specification describes the functions, variables, and types of a compiled program. Entries of a DWARF file are organized in a tree structure where each node can have children and siblings. For example, an entry node that describes a function would have children that describe the parameters. An entry node that describes a struct would have children that describe the fields of it.

As the unofficial backronym for DWARF (Debugging With Attributed Record Formats) purports, the format is used by debugging tools to gather useful information such as data types or memory offsets. There's a ton of information that you can leverage for reverse engineering, debugging, or learning about systems programming. The Go standard library conveniently includes the [debug/dwarf](https://golang.org/pkg/debug/dwarf/) package for reading this information.

Let's build a program for parsing the DWARF out of any ELF binary and see what useful information we can find.

```
import (
	"debug/elf"
	"log"
)

func main() {
	elfFile, err := elf.Open("/path/to/binary")
	if err != nil {
		log.Fatal(err)
	}

	dwarfData, err := elfFile.DWARF()
	if err != nil {
		log.Fatal(err)
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

The `Offset` represents the offset of the entry within the DWARF data. This is not to be confused with the offset of the symbol in the actual ELF binary. You can use `dwarf.Reader`'s `Seek` method with this offset. 

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

You can sort of think about `Field`'s as key value pairs, where the `Attr` is the key, and the `Val` is the value. The `Class` field provides additional context about how to read the raw bytes of data in `Val`.

The `Attr` (or 'attribute') is the description of what this Field represents. As per the previous example, if this Field represents the name of the entry it is contained in, the Attr would be `AttrName`. Another example could be `AttrType`, which means the Field represents the type of the entry it is contained in.

The contents of `Val` are what the attribute describes. If the attribute is `AttrName` then the `Val` is the actual name. In order to read the value you must take notice of how `Class` is set. This can vary based on your compiler but some examples include `ClassAddress` or `ClassString`, referring to how to find the actual value of `Val`.

With all this mind, let's look at how we can add to our above program the functionality to print out the names of all functions:

```
	...
		for {
			// Read all entries in sequence
			entry, err := entryReader.Next()
			if err == io.EOF {
				// We've reached the end of DWARF entries
				break 
			}

			// Check if this entry is a function
			if entry.Tag == dwarf.TagSubprogram {
				
				// Go through fields 
				for _, field := range entry.Field {

					if field.Attr == dwarf.AttrName {
						fmt.Println(field.Val.(string))
					}
				}
			}
		}
	...
```

(Full program [here](https://gist.github.com/grantseltzer/51c7c0827b95e9a1c07796d6b352076c))

All function parameters have their own entries and are placed in order right after the function's entry. They have the tag `TagFormalParameter`. We can read what datatype the parameter is by reading the `AttrType` field. All we need to do in that case would be to have a second `Reader` jump to the entry of the type definition. We would just continue reading entries while checking if they're function parameters. Like so:

```
...
		if !(readingAStruct && entry.Tag == dwarf.TagFormalParameter) {
			continue
		}

		for _, field := range entry.Field {

			if field.Attr == dwarf.AttrName {
				name = field.Val.(string)
			}

			if field.Attr == dwarf.AttrType {
				typeReader.Seek(field.Val.(dwarf.Offset))
				typeEntry, err := typeReader.Next()
				if err != nil {
					log.Fatal(err)
				}

				for i := range typeEntry.Field {
					if typeEntry.Field[i].Attr == dwarf.AttrName {
						typeName = typeEntry.Field[i].Val.(string)
					}
				}
			}
		}

		fmt.Printf("\t%s %s\n", name, typeName)
...
```
(Full program [here](https://gist.github.com/grantseltzer/7e30682b215567976298dc8a2cc4d92f))

Compiling this binary and running it on itself we can see all of our functions, plus of course all the runtime dependencies that Go packs into our binaries as well:

```
.
.
.
debug/dwarf.(*Data).Reader
	d *debug/dwarf.Data
fmt.Printf
	format string
	a []interface {}
	n int
	err error
main.entryIsEmpty
	e *debug/dwarf.Entry
type..eq.[2]interface {}
	p *[2]interface {}
	q *[2]interface {}
	r bool
main.main
```

If you try running this yourself you'll also notice that you can get return types and their names as well. Those have the attribute `AttrVarParam`.

There is a lot to cover and a lot of possibilities that you can use this information for, far more than I can fit into a single blog post. As part of refactoring [weaver](github.com/grantseltzer/weaver) i'm writing a higher level package for querying type information from binaries, so please keep an eye out!
