+++
title = "Linux Procfs (A love letter)"
Description = ""
Tags = []
Categories = []
Date = 2019-10-02T03:32:37+00:00
+++

The proc filesystem (procfs) provides a convenient way of interacting with the running proccess' on your machine by simply reading and writing to files. The procfs is mounted at `/proc` by default. 

If you go into `/proc` you'll see something like this:

<center>![toplevel](/procfs/toplevel.png)</center>

You'll notice all of the directories that are just named by numbers. There is one for each individual procces. The directory names correspond to the process ID. One directory for each process.

They all have the same content:

<center>![process_dir](/procfs/process_dir.png)</center>

Among these files you can find out information such as performance of the process, where the executable is located, memory regions, open file descriptors, resource limits, or namespace information. There's a lot to poke around through but here's some highlights:

## - `/proc/[pid]/fd`

A file descriptor is a proccess' handle on an open file. This directory contains links to open file descriptors that the process has.

- /proc/pid/fd
- /proc/pid/status
- /proc/pid/exe & /proc/pid/cmdline
- /proc/kallsyms
- /proc

The directories and files in `/proc` don't actually exist on disk. The procfs is the kernel representing the procceses on your system <i>as if</i> they were files.

