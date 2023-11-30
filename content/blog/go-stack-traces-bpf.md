+++
title = "Building Go Stack Traces from BPF"
Description = ""
Tags = []
Categories = []
Date = 2025-11-15T00:00:00+00:00
column = "left"
+++

In my posts from a few years ago I explored the idea of attaching bpf programs to Go functions via uprobes. The second post dived into how to extract values of parameters. This can be seen as part 3 of the series as i'm going to demonstrate how to get a stack trace from bpf code.

The purpose of a stack trace is simple. When a function is called, we want to know the order of execution of every function/line that lead to the function invocation. You can see an example of a stack trace everytime a panic occurs in Go, which are helpful to find offending code.

Take the following code as an example,

```
func stack_A() {
	stack_B()
}

func stack_B() {
	stack_C()
}

func stack_C() {
	print("hello!")
}

func main() {
    stack_A()
}
```

If we want a stack trace on invocations of `stack_C()` it would look something like this:

```
  "main.stack_B (/home/vagrant/StackTraceExample/main.go:8)",
  "main.stack_A (/home/vagrant/StackTraceExample/main.go:3)",
  "main.main (/home/vagrant/StackTraceExample/main.go:45)"
```
 
### Stack Unwinding

The proccess we'll use for getting a basic stack trace is a simple and well documented set of steps. The basic principle is that we're going to collect program counters (locations of machine code) as we traverse through pointers that the Go compiler saves throughout the flow of execution.

When a function is called, a new "stack frame" is allocated. This basically means that a section of the program's stack is allocated to accomodate local variables in the new function.

When a new frame is allocated, the stack address of the previous frame is pushed onto the stack. After that, the return address is pushed onto the stack. The return address is the program counter in which the function will 'return' to when the function exits.