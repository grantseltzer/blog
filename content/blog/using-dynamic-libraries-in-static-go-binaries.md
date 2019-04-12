+++
title = "Using dynamic libraries in static Go binaries"
Description = ""
Tags = []
Categories = []
Date = 2019-04-09T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
In this post we look at a recent change to Go's net and runtime packages.
</span>

I recently got my very first contribution into Go! The change involves using [res_search](https://www.freebsd.org/cgi/man.cgi?query=res_search&apropos=0&sektion=3&manpath=FreeBSD+9-current&format=html), a function for executing a DNS query when CGO is disabled on macos. 

Prior to this change when a Go program would run a DNS query, such as with `net.LookupHost` there were two possible paths that the Go runtime can take to handle that query. If the program was compiled with CGO <i>enabled</i> it will dynamically call `getaddrinfo`, a libc function for hostname/address translation. If the program was compiled with CGO <i>disabled</i>, it will call [code](https://github.com/golang/go/blob/master/src/net/dnsclient_unix.go) written in Go which builds out the request and manually sends it out. 

This was an issue in particular on darwin. If an engineer downloads a binary written in Go <i>(hashicorp tools come to mind)</i> to run on their macbook pro it was surely statically built without CGO. Darwin has features to configure your DNS nameservers which the Go native code does not take into account. [This](https://github.com/golang/go/issues/12524) github issue details the problem.

The solution to this issue is to give developers the best of both worlds. To use libc code for dns resolution (which would be aware of darwin's features), regardless of if CGO is enabled.

<h2><b>//go:cgo_import_dynamic</b></h2>

Go has a bunch of little known features that allow you to give instructions to the compiler, linker, and other related piecesusing special comments. Dave Cheney wrote an excellent post on them [here](https://dave.cheney.net/2018/01/08/gos-hidden-pragmas). One such directive, or 'pragmas' as Cheney puts them, is `//go:cgo_import_dynamic`. This is a linker directive. It tells the linker to pull in a specific function from a dynamic library such as libc. 
