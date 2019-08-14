+++
title = "Debugging Go tests"
Description = ""
Tags = []
Categories = []
Date = 2019-08-05T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
This post discusses building go test binaries and walking through them in dlv
</span>

I recently was working on debugging a unit test I wrote in Go. I couldn't figure out why one of my test cases was causing a runtime error that never happened when running my actual program. I was using a runtime directive so I suspected there may be some difference between doing a `go test` and a `go run`. I was looking through Go build mode [documentation](https://golang.org/cmd/go/#hdr-Build_modes) while wondering if I could step through it with a debugger. Lo and behold you can compile your tests into an ELF executable!

Let's take a look at this simple example:



```
package test


type Node struct {
    Value int
    Next *Node
}

func TestWalkList(t *testing.T) {
    var Head *Node
    
    for {

    }
}

```

