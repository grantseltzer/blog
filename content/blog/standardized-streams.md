+++
title = "Standardized Streams and Shells"
Description = ""
Tags = []
Categories = []
Date = 2019-05-15T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
In this post we discuss how standardized streams (`stdin`/`stdout`/`stderr`) work on Linux and how to interact with them in Go
</span>

Every well known operating system has a concept of standardized streams. These consist of standard input, output, and error. As their name purports, they are the standard places to read input, and send output. They're a crucial concept that allows various running procceses to easily communicate.

Standardized streams enable you to string together multiple commands with a pipe (`|`) in your shell like this:

`$~ cat /dev/urandom | less `

In this example, bash executes the commands on both sides of the pipe and writes the stdout of `cat` to stdin of `less`. For both, stderr is written to the terminal. Most programs, like `less`, are made to write to stdout/stderr and read from stdin for this exact reason.

When a new process is created, file descriptors are opened for each of these standardized streams. You can view each processes open file descriptors in `/proc` like this:

```
$~ ls -l /proc/$PPID/fd
lrwx------ 1 root root 64 May 20 16:58 0 -> /dev/pts/0
lrwx------ 1 root root 64 May 20 16:58 1 -> /dev/pts/0
lrwx------ 1 root root 64 May 20 16:58 2 -> /dev/pts/0
```

In the above output you can see that the process has file descriptors `0`, `1`, and `2`. By convention these correspond to `stdin`, `stdout`, and `stderr` respecitvely. These all point to the pseudo-terminal `/dev/pts/0`.  

Your terminal application runs a shell (such as bash or zsh) and provides for it a GUI to display input and output. When you open a terminal it has its own set of standard streams. As mentioned above, it also creates a special device file like `/dev/pts/0` which other processes can read from and write to. In addition to running the commands that you enter, it listens for their input and output from the pseudo-terminal device file. In the case of input, it passes it to the running command. In the case of output, it displays it to the terminal GUI.


## Play along at home

You can actually access the standard streams of other proccesses. Try taking the following steps:

1) Open up two terminal sessions

2) From the first terminal run the command `ls -l /proc/$PPID/fd`. This will tell you what pseudo-terminal you can write to.

```
TODO:

- Open a container w/ Bash
- Exec into it from another terminal
- write to each others stdout (/dev/pty0, /dev/pty1)
-

```
