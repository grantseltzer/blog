+++
title = "Tracing Go Functions with eBPF Part 2"
Description = ""
Tags = []
Categories = []
Date = 2020-05-10T03:32:37+00:00
+++

![gopher](/weaver/glitch-gopher.png)

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

Just to refresh your memory, the following eBPF function, `get_arguments`, is going to be set up so that it's executed inside the eBPF virtual machine everytime `simpleFunction` is called in a running Go program:

```
#include <uapi/linux/ptrace.h>

inline int get_arguments(struct pt_regs *ctx) {

    // TODO: Code to extract the value of arguments

    return 0;
}
```

The cool thing about eBPF programs is that they have access to all of addressable memory. This of course includes the stack and heap of the processes that are running our programs! For more context let's take a look at the definition of `struct pt_regs`, which will be populated for us as the parameter in our eBPF function:

```
struct pt_regs {

    unsigned long sp;
	unsigned long bx;
	unsigned long cx;
	unsigned long dx;
	unsigned long si;
	unsigned long di;
	unsigned long bp;
	unsigned long ax;

    // more fields ...
};
```

These fields represent the registers that the process instructions are using. If we were tracing a C program, parameters are loaded into particular registers automatically. For example, let's say we're tracing a C function that takes a single integer. We would be able to read the contents of the `di` register as an integer and see what value was passed to it anytime it's been called.

When a Go function is called, the runtime places the parameters on the stack, rather than using registers. We can get a pointer to the stack from the `sp` register like so:

`void* stackAddr = (void*)ctx->sp;`

From there we can calculate starting/ending offsets of our parameters and extract their values accordingly. In the case of our example, the offsets would be `sp+8` -> `sp+16`. This is because the return address of functions takes up the first 8 bytes, and then the `int` parameter is 8 bytes. Here's what that would look like in ebpf:

```
#include <uapi/linux/ptrace.h>

BPF_PERF_OUTPUT(events);

inline int get_arguments(struct pt_regs *ctx) {
		void* stackAddr = (void*)ctx->sp;
		long parameter_value;
		bpf_probe_read(&parameter_value, sizeof(parameter_value), stackAddr+8); 
		events.perf_submit(ctx, &parameter_value, sizeof(parameter_value));
}
```

<i>The full code for this example can be found [here](https://gist.github.com/grantseltzer/468471da422568cdc0647751c5c08014) </i>

## Calculating stack offsets

When we have multiple parameters in the function we're tracing, you have to do some math to decide their offset from the top of the stack.

Parameters are padded on the stack based on the largest data type amongst them. If the largest data type amongst parameters is a uint32, which is 4 bytes, then every parameter is padded to 4 bytes. This is capped at 8 bytes.

| Datatypes   | Size (in bytes) | Note |
| :---------- | :-------------- | :-------------|
| int8, uint8 | 1 | 
| int16, uint16 | 2 |
| int32, uint32 | 4 |
| int, uint, int64, uint64 | 8 |
| float32 | 4 |
| float64 | 8 |
| bool | 1 |
| byte | 1 | 
| rune | 4 | 
| string | 16 | 8 for address of array, then 8 for length |
| pointers | 8 | Same size regardless of what it's a pointer to.
| structs | 8 | Address of the struct. The same padding logic described below applies within the struct content. |
| interfaces | 16 | Requires knowledge of the type by parsing DWARF info. |

To calculate the actual offset of each parameter from the top of the stack, we look at the size of the largest data type that's being parsed to see the size of the 'window'. Each successive parameter is limited by if it would fit into the current window. If it would go over the limits of a window, pad the current windows, and start a new one.

For example let's say we're trying to parse the function:

```
func parseMe(a int, b bool, c float32) { ... }
```

The largest data type is the `int` at 8 bytes. The offsets for the parameter `a` would therefore be `sp+8` through `sp+15`. The parameter `b` is one byte, so its offset is `sp+16`. The parameter `c` is 4 bytes, so that would be `sp+17` through `sp+20`.

Here's what the code for that would look like:

```
#include <uapi/linux/ptrace.h>

BPF_PERF_OUTPUT(events);

inline int get_arguments(struct pt_regs *ctx) {
		void* stackAddr = (void*)ctx->sp;

		long argument1;
		bpf_probe_read(&argument1, sizeof(argument1), stackAddr+8); 
		events.perf_submit(ctx, &argument1, sizeof(argument1));

		char argument2;
		bpf_probe_read(&argument2, sizeof(argument2), stackAddr+16); 
		events.perf_submit(ctx, &argument2, sizeof(argument2));

		float argument3;
		bpf_probe_read(&argument3, sizeof(argument3), stackAddr+17); 
		events.perf_submit(ctx, &argument3, sizeof(argument3));			
}
```

<i>Full code for this example [here](https://gist.github.com/grantseltzer/76468d7e9ab4644170d15d1a4ae39d99)</i>

For an example of how this process can be generalized checkout my project, [weaver](https://github.com/grantseltzer/weaver), which calculates offsets in Go code and generates eBPF code using a text template.