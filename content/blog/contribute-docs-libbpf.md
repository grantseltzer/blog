+++
title = "The libbpf Documentation Site"
Description = ""
Tags = []
Categories = []
Date = 2021-10-08T00:00:00+00:00
column = "left"
+++

libbpf is the standard implementation of the userspace library for loading and interacting with bpf programs. It defines the bpf ELF file format and CO-RE features. It's a crucial part of the bpf ecosystem and is soon aproaching its first major release. With this in mind, it's important to have proper documentation.

Introducing [libbpf.readthedocs.org](https://libbpf.readthedocs.org). By going to the [API docs](https://libbpf.readthedocs.io/en/latest/api.html) you can see that each libbpf API function, type, enum and macro are listed. This is generated from the libbpf header files. Comments can be placed in code above the relevant API code and displayed on the documentation site. 

If you're interested in contributing, you can find a guide on the format for the API documentation comments [here](https://libbpf.readthedocs.io/en/latest/libbpf_naming_convention.html#api-documentation-convention). Since libbpf is hosted in the linux kernel repo under [tools/lib/bpf](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/lib/bpf), contributing to it unfortunetly requires use of the mailing list. The markdown documents on the documentation site can be found under [Documentation/bpf/libbpf/](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/Documentation/bpf/libbpf). 

This documentation is synced to the [github mirror](https://github.com/libbpf/libbpf). Since libbpf maintainers cut releases from the github mirror, this means that the documentation is also versioned. You can toggle versions on the bottom left corner of the page. 

You can also find relevant documentation for the bpf system call [here](https://www.kernel.org/doc/html/latest/userspace-api/ebpf/syscall.html).
