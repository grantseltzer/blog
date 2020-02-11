+++
title = "Tracing Go Functions with eBPF"
Description = ""
Tags = []
Categories = []
Date = 2029-02-10T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
Over the past couple of months I have become obssesed with eBPF. This post will cover some cool things I learned while working on [weaver](https://github.com/grantseltzer/weaver)
</span>

<center>![manhattangopher](/weaver/DrManhattanGopher.png)</center>


In case you're not familiar, eBPF is A virtual machine inside the Linux kernel. It lets you write ‘C’ code and attach it to hooks that you can set inside the kernel. It’s being widely adopted as a platform for creating performance monitoring, debugging, and security tools.

eBPF programs have unique visibility and privilege since they run inside the kernel. They also run very quickly since they don’t pay a penalty for using system calls... amongst other reasons.

The best way to instrument eBPF programs is using a library called [bcc](https://github.com/iovisor/bcc) which has bindings for high level languages like Go or Python. It lets you load, run, and receive output from eBPF programs to your userspace program.

 <center>![](/weaver/arch.png)</center>