+++
title = "What is vmlinux.h?"
Description = ""
Tags = []
Categories = []
Date = 2021-03-11T00:00:00+00:00
column = "left"
+++

If you've been reading much bpf code recently, you've probably seen this:

```
#include "vmlinux.h"
```

`vmlinux.h` is generated code. it contains all of the type definitions that your running Linux kernel uses in it's own source code. This is an important concept to wrap your head around so let me explain.

When you build Linux one of the output artifacts is a file called `vmlinux`. It's also typically packaged with major distributions. This is an [ELF](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format) binary that contains the compiled kernel inside it.

There's a tool, aptly named bpftool, that is maintained within the Linux source repository. It has a feature to read the `vmlinux` file and generate a `vmlinux.h` file. Since it contains every type-definition that the installed kernel uses, it's a very large header file.

The actual command is:

`bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h`

It's pretty common in bpf programs to read fields of data structures that are used in the kernel. When you import this header file your bpf program can read memory and know which bytes correspond to which fields of any struct that you want to be working with.

For example, Linux represents the concept of a process with a type called [`task_struct`](https://elixir.bootlin.com/linux/latest/source/include/linux/sched.h#L649). If you want to inspect values in a task_struct from your bpf program, you're going to need to know the definition of it. You're also going to want to make sure it's the same definition that the running kernel is using, as the definition can change from version to version. 

![vmlinux](/libbpf/vmlinux.png)

## What about CO:RE? 

A powerful concept that libbpf enables is something called "CO:RE" or "Compile once, run everywhere". There are macros defined in libbpf (such as `BPF_CORE_READ`) that will analyze what fields you're trying to access in the types that are defined in your `vmlinux.h` file. If the field you want to access has been moved within the struct definition that the running kernel uses, the macro/helpers will find it for you. Therefore, it doesn't matter if you compile your bpf program with the `vmlinux.h` file you generated from your own kernel and then ran on a different one, but including `vmlinux.h` does enable this. 

Refer to Andrii Nakryiko's blog post [here](https://nakryiko.com/posts/bpf-portability-and-co-re/) on the subject.