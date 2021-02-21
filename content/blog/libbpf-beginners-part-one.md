+++
title = "Getting started with libbpf"
Description = ""
Tags = []
Categories = []
Date = 2021-02-20T00:00:00+00:00
column = "left"
+++

In my [previous posts](/blog/tracing-go-functions-with-ebpf-part-1) on the subject of bpf I used a project called BCC to compile, load, and interact with my bpf programs. I and many other developers, have recently heard about a relatively new way of building ebpf projects called [libbpf](https://github.com/libbpf/libbpf). There are some great resources to use when developing libbpf based programs but getting started can still be a little intimidating. The goal of this post is to provide a simple and effective introduction to developing libbpfgo programs.

libbpf is library that you can import in your userspace program. It provides developers with an API for loading and interacting with bpf programs. It is maintained in the linux kernel [source tree](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/lib/bpf) which makes it a very promising package to rely on.

Let's take this simple bpf program:

{{< gist grantseltzer b7fca3e0df72fe8766a748ec39158a75 >}}
