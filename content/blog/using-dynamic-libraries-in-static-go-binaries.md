+++
title = "Using dynamic libraries in static Go binaries"
Description = ""
Tags = []
Categories = []
Date = 2019-04-09T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
This post highlights a linker directive in Go. It allows us to import functions from a dynamic library even when CGO is disabled. I use the example of a contribution I recently made to the net and runtime packages to demonstrate its use case.
</span>

Go has many little known features that allow you to give instructions to the compiler, linker, and other parts of the toolchain using special comments. Dave Cheney wrote an excellent post on them [here](https://dave.cheney.net/2018/01/08/gos-hidden-pragmas). One such 'pragma' as Cheney calls them is  `//go:cgo_import_dynamic`. This is a linker directive. It tells the linker to pull in a specific function from a dynamic library such as libc.

Let's check out an example from my [recent contribution](https://go-review.googlesource.com/c/go/+/166297) to the runtime package.

First, in lookup_darwin.go we use the cgo_import_dynamic directive for `res_search`

<script src="https://gist.github.com/grantseltzer/1d6fdd3ba81a18ea5fbb48d62b2f91c5.js"></script>

When the linker is run after compilation it executes this directive. The linker pulls in the `res_search` routine from the libSystem dynamic library (found at the given path). It then makes the routine referenceable in Go's assembly code by the name `libc_res_search`.

Now in order to link assembly code to Go we have a couple of pieces of glue to put in place. Let's take a look first, and then analyze:

<script src="https://gist.github.com/grantseltzer/38c76591c532f3bc40e1367c19502167.js"></script>

The first thing to look at is the symbol definition of `res_search_trampoline()` <i>(line 13)</i>. This is a function which will be defined in assembly. Defining the symbol in Go code allows the linker to make it referenceable. 

We also need a helper function which takes the arguments to pass to the assembly routine, and makes a call to `libcCall()`. This is a helper function defined inside the runtime package. It takes both the trampoline symbol address, and address of the arguments. It uses these to orchestrate the actual call.

Finally we define the assembly routine for `res_search_trampoline` which is linked by the Go symbol above.

<script src="https://gist.github.com/grantseltzer/0327af2124ddab0f50682f158e23863c.js"></script>

All this routine does is load the arguments by their offset (calculated by size) and call `libc_res_search`. It also checks a possible error and calls `libc_error` (another statically linked function!) accordingly.

From these definitions we can now call the res_search helper function as if it's the res_search function in libSystem. This is all of course regardless of if CGO is enabled! 

Do keep in mind, this directive is purposely not part of the language specification. It should probably only be done in Go's runtime package. 