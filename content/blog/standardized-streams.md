+++
title = "Standardized Streams and Go"
Description = ""
Tags = []
Categories = []
Date = 2019-05-15T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
In this post we discuss how standardized streams (`stdin`/`stdout`/`stderr`) work on Linux and how to interact with them in Go
</span>

Every well known operating system has a concept of standardized streams. These consist of standard input, output, and error. As their name purports, they are the standard places to read input, and send output. They're a crucial concept that allows various running procceses to easily communicate.

Standardized streams enable you to string together multiple commands with a pipe (`|`) in bash like this:

`$~ cat /dev/urandom | less `

In this example, bash executes the commands on both sides of the pipe and writes the stdout of `cat` to stdin of `less`. For both, stderr is written to the terminal. Most programs, like `less`, are made to write to stdout/stderr and read from stdin for this exact reason.

The terminal in which you run commands is itself a program. It runs your shell (such as bash or zsh) and provides for it a GUI application to display input and output. When you open a terminal it has its own set of standard standard streams. It also creates a special device file in `/dev` which other processes can read from andwrite to.

```
[root@117bcc9d4064 /]# ls -l /proc/self/fd/0
lrwx------ 1 root root 64 May 19 18:03 /proc/1/fd/0 -> /dev/pts/0
```

When a new process is created, file descriptors are opened for each of these standardized streams.


```
TODO:

- Open a container w/ Bash
- Exec into it from another terminal
- write to each others stdout
-

```

** I'm talking about pseudo-terminals in the same way I would true terminals. 