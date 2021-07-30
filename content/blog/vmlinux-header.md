+++
title = "What is vmlinux.h?"
Description = ""
Tags = []
Categories = []
Date = 2021-03-11T00:00:00+00:00
column = "left"
+++

{{< intro >}}

A version of this post was also uploaded to Aqua's blog <a href="https://blog.aquasec.com/vmlinux.h-ebpf-programs">here</a>

{{< /intro >}}


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

For example, Linux represents the concept of a process with a type called [`task_struct`](https://elixir.bootlin.com/linux/latest/source/include/linux/sched.h#L649). If you want to inspect values in a task_struct from your bpf program, you're going to need to know the definition of it.

![vmlinux](/libbpf/vmlinux.png)

Since the vmlinux.h file is generated from your installed kernel, your bpf program could break if you try to run it on another machine without recompiling if it’s running a different kernel version. This is because, from version to version, definitions of internal structs change within the linux source code.

However, by using libbpf, you can enable something called "CO:RE" or "Compile once, run everywhere". There are macros defined in libbpf (such as `BPF_CORE_READ`) that will analyze what fields you're trying to access in the types that are defined in your `vmlinux.h`. If the field you want to access has been moved within the struct definition that the running kernel uses, the macro/helpers will find it for you. It doesn't matter if you compile your bpf program with the `vmlinux.h` file you generated from your own kernel and then ran on a different one. 

You'll also notice an interesting set of lines at the top of vmlinux.h

```
#ifndef BPF_NO_PRESERVE_ACCESS_INDEX
#pragma clang attribute push (__attribute__((preserve_access_index)), apply_to = record)
#endif
```

This applies the 'preserve_access_index' attribute to all of the data structures defined in this massive header file. It enables preserving the type's debug information indices which the CO:RE helpers make use of. You could apply this attribute to structs in the various normal header files you'd import and skip vmlinux.h altogether though there's some challenge to that which you may ran into. The attribute is then turned off at the bottom of the header:

```
#ifndef BPF_NO_PRESERVE_ACCESS_INDEX
#pragma clang attribute pop
#endif
```

Macros defined in Linux are not defined in DWARF/BTF, and will not be part of the generated vmlinux.h file.

Refer to Andrii Nakryiko's blog post [here](https://nakryiko.com/posts/bpf-portability-and-co-re/) on the subject of BPF + CO:RE.