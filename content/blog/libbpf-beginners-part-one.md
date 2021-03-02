+++
title = "Getting started with libbpf"
Description = ""
Tags = []
Categories = []
Date = 2021-02-20T00:00:00+00:00
column = "left"
+++

In my [previous posts](/blog/tracing-go-functions-with-ebpf-part-1) on the subject of bpf I used a project called BCC to compile, load, and interact with my bpf programs. I, and many other developers, have recently heard about a relatively new way of building ebpf projects called [libbpf](https://github.com/libbpf/libbpf). There are a few good resources to use when developing libbpf based programs but getting started can still be a little intimidating. The goal of this post is to provide a simple and effective introduction to developing libbpfgo programs.

libbpf is library that you can import in your userspace program. It provides developers with an API for loading and interacting with bpf programs. It is maintained in the linux kernel [source tree](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/lib/bpf) which makes it a very promising package to rely on.

In order to illustrate the nature of libbpf and how to use it, we're going to write a simple bpf program that tells us everytime a process uses the `mmap` system call.

Let's start with the imports:

```
#include <bpf/bpf_helpers.h>  
#include "vmlinux.h"
```

The `bpf_helpers.h` header file is a self descriptively named part of libbpf.

I wrote a complementary blog post on `vmlinux.h`, you can find it [here](/blog/vmlinux-header).

////


{{< gist grantseltzer bf0cc4dc0c68407b95823693ae52e514 >}}

The bpf program itself is just this function, there is no '`main()`'. We can define and import other functions of course, but those must be marked with the `__always_inline` attribute. This is to limit complexity and avoid any recursion as bpf programs must terminate! 

So, let's break this down.

```
SEC("kprobe/sys_mmap")
```

This is the section macro (defined in [bpf_helpers.h](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/lib/bpf/bpf_helpers.h#n25)). All programs must have one to tell libbpf what part of the compiled binary to place the program. This is essentially a qualified name for your program. There isn't a strict rule for what it should be but you should follow the conventions defined in libbpf.