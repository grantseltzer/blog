+++
title = "Tracing Go Functions with eBPF Part 2"
Description = ""
Tags = []
Categories = []
Date = 2020-05-15T03:32:37+00:00
+++

In [part 1](/blog/tracing-go-functions-with-ebpf-part-1) of this series we learned about how to attach uprobes and eBPF programs to specific functions in Go programs. We went through an example where we attached our probe to the handler of a webserver. Everytime the probe was triggered we simply printed out a log saying that the handler was called. This could be adapted to record metrics, perhaps using counters instead of log lines.

In this post we're going to delve a bit deeper. We're going to use the capabilities that eBPF has for traversing through the memory of the program we're tracing.

## Arguments

Let's say we want to get the argument values of specific functions anytime it's called. For example, the function `simpleFunction` here:

```
package main

func simpleFunction(x int) {
    // some code
}

func main() {
    simpleFunction(99)
}
```

We would attach a uprobe and eBPF program to it in the same way as in Part 1. We'll just focus on eBPF code that we'll load, the Go code is the same as the previous post. You can find that [here](https://gist.github.com/grantseltzer/f82d5e2471e563f6aaf800ad9cdcf8a1).

Just to refresh your <i>memory</i>, the following eBPF function, `get_arguments`, is going to be set up so that it's executed inside the eBPF virtual machine everytime `simpleFunction` is called in a running Go program:

```
#include <uapi/linux/ptrace.h>

inline int get_arguments(struct pt_regs *ctx) {

    // TODO: Code to extract the value of arugments

    return 0;
}
```

The cool thing about eBPF programs is that they all have access to all of addressable memory. This of course includes the stack and heap of the procceses that are running our programs! For more context lets take a look at the definition of `struct pt_regs`, which will be populated for us as the parameter in our eBPF function:

```
struct pt_regs {

	unsigned long bx;
	unsigned long cx;
	unsigned long dx;
	unsigned long si;
	unsigned long di;
	unsigned long bp;
	unsigned long ax;
    unsigned long sp;

    // more fields ...
};
```

These fields represent the registers in x86 assembly at the time the hook was called. 