+++
title = "Tracing Go Functions with eBPF"
Description = ""
Tags = []
Categories = []
Date = 2020-02-14T03:32:37+00:00
+++

<center>![manhattangopher](/weaver/DrManhattanGopher.png)</center>
<center><i>eBPF makes you an omniscient gopher</i></center>

eBPF is a virtual machine, similar in concept to the JVM, except inside the Linux kernel. It lets you write 'C-like' or 'eBPF' code, compile it, and load the byte code into the kernel. You can then attach hooks to your loaded eBPF program to trigger it to run. Those hooks could be things like system calls, [kprobes](https://lwn.net/Articles/132196/), or  [uprobes](https://www.kernel.org/doc/ols/2007/ols2007v1-pages-215-224.pdf).

There's many usecases for eBPF. Considering eBPF programs have full sysem visibility there are very few limits on what you can do. You can write an eBPF program which logs everytime certain files are modified. You use eBPF to profile performance of your other programs. You can implement host-based networking rules, or for [writing malware](https://www.youtube.com/watch?v=yrrxFZfyEsw).

I have become obssesed with eBPF. In particular the most interesting functionality to me is the ability to attach eBPF programs to uprobes. These are a seperate technology from eBPF but they play very well together. Uprobes let you create a hook at a memory address anywhere in userspace. That means after you compile a program, lets say one written in Go, you can attach a hook to a specified function inside that program. Let's look at an example:

<b>main.go</b>
```
package main

func functionA() {
    ...
}

func main() {
    functionA()
}
```

When you `go buld` it, `functionA()` is created as a symbol in the created binary. We can see it here with this command:

```
[*] objdump --syms ./test | grep functionA
0000000000452330 g     F .text	0000000000000001 main.functionA
```

`objdump` is used to list all the symbols in the binary. In the above output just worry about the memory offset all the way to the left, and the fact that it corresponds to our funciton `main.functionA`. (<i>Check out my other post, '[Dissecting Go Binaries](/blog/dissecting-go-binaries)' for more info on this.</i>)

So in this case, you can attach a uprobe to the `functionA` symbol, which you can have trigger an eBPF program. The uprobe is copied into memory anytime the binary is executed, meaning it will trigger anytime any process runs that function. Here's a diagram to help better visualize this:

![diagram](/weaver/uprobe-ebpf.png)

# Let's write some eBPF

The best way to instrument eBPF programs is using a library called [bcc](https://github.com/iovisor/bcc) which has bindings for high level languages like Go or Python. It lets you load, run, and receive output from eBPF programs to your userspace program. You can think of it as a compiler and runtime that you can use as a Go package.

Take the following example Go program that we're going to trace:

```
package main

import (
	"fmt"
	"log"
	"net/http"
)

//go:noinline
func handlerFunction(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hi there from %s!", r.Host)
}

func main() {
	http.HandleFunc("/", handlerFunction)
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```

This is just a simple webserver that serves a polite greeting. Doing a `curl localhost:8080` or going to `localhost:8080` in your browser will hit the endpoint.

 We're going to use eBPF and uprobes to tell us everytime the function `handlerFunction` is called, and therefore everytime someone connects to our webserver.


