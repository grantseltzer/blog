+++
title = "Linux Procfs"
Description = ""
Tags = []
Categories = []
Date = 2019-10-02T03:32:37+00:00
column = "left"
+++

I love the procfs because it provides an intuitive and easy to use interface for interacting with the kernel. In the same way you'd normally use the command line for exploring files, you can control and find out information about currently running processes. All without the need for system calls.

A procfs is mounted at `/proc` by default. If you go into `/proc` you'll see something like this:

![toplevel](/procfs/toplevel.png)

You'll notice a lot of the directories that are just named by numbers. There is one for each individual process. The directory names correspond to the process ID. One directory for each process.

They all have the same layout:

![process_dir](/procfs/process_dir.png)

Among these files you can find out information such as performance of the process, where the executable is located, resource limits, or namespace information. There's a lot to explore but here's some highlights:

## <b> - `/proc/[pid]/fd` </b>

A file descriptor is a process' handle on an open file. This directory contains symbolic links to open file descriptors that the process has. Most importantly you can find the file descriptors for [standardized streams](/blog/standardized-streams-and-shells). One use case for this is using `tail` to follow logs printed to standard error of a particular process (`tail -f /proc/[pid]/fd/2`)

## <b> - `/proc/[pid]/exe` and `/proc/[pid]/cmdline` </b>

The `exe` file is a symbolic link to the executable that spawned the process. This could be useful if you have a program that wants to re-execute itself. The `cmdline` file will tell you what arguments were passed at the command line to run that process.

## <b> - `/proc/[pid]/stat` / `/proc/[pid]/status` </b>

The `stat` and `status` files contain resource usage information about the process. Everything from what CPU core the process is running on, to how many clock ticks the process has spent running or idle. Any system monitor program such as `top` would read the `stat` file every few seconds for CPU and Memory share percentages.

## <b> - `/proc/kallsyms` </b>

Here's a really cool one. This contains every symbol (function or variable) in your kernels code. If you `cat` it as root it'll also give you their static memory addresses. This is used for setting [kprobes](https://lwn.net/Articles/132196/) or for use in kernel modules.

## <b> - `/proc/self` </b>

This is a symlink to the <i>currently running</i> process. Meaning this will be the `/proc/[pid]` directory of whatever process requests access to it.

![self](/procfs/self.png)

The directories and files in `/proc` don't actually exist on disk. The procfs is the kernel representing the proceses on your system <i>as if</i> they were files. Whenever a process requests files in the procfs, the kernel responds with the contents of the theoretical file.

Now if only Apple would enable procfs on Macos...