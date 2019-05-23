+++
title = "Standardized Streams and Shells"
Description = ""
Tags = []
Categories = []
Date = 2019-05-21T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
In this post we discuss how standardized streams (`stdin`/`stdout`/`stderr`) work on Linux, especially related to shells.
</span>

Every well known operating system has a concept of standardized streams. These consist of standard input, output, and error. As their name purports, they are the standard places for proccesses to read input, and send output. They're a crucial concept that allows various running processes to easily communicate.

Standardized streams enable you to string together multiple commands with a pipe (`|`) in your shell like this:

`$~ cat /dev/urandom | less `

In this example, bash executes the commands on both sides of the pipe. It writes the stdout of `cat` to stdin of `less`. For both, stderr is written to the terminal. Most programs, like `less`, are made to write to stdout/stderr and read from stdin for this exact reason.

When a new process is created, file descriptors are opened for each of these standardized streams. You can view each processes open file descriptors in `/proc` like this:

```
$~ ls -l /proc/$PPID/fd
lrwx------ 1 root root 64 May 20 16:58 0 -> /dev/pts/0
lrwx------ 1 root root 64 May 20 16:58 1 -> /dev/pts/0
lrwx------ 1 root root 64 May 20 16:58 2 -> /dev/pts/0
```

In the above output you can see that the process has file descriptors `0`, `1`, and `2`. By convention these correspond to `stdin`, `stdout`, and `stderr` respectively. These all point to the pseudo-terminal `/dev/pts/0`.  

Your terminal application runs a shell (such as bash or zsh) and provides for it a GUI to display input and output. When you open a terminal it has its own set of standard streams. As mentioned above, it also creates a special device file like `/dev/pts/0` which other processes can read from and write to. In addition to running the commands that you enter, it listens for their input and output from the pseudo-terminal device file. In the case of input, it passes it to the running command. In the case of output, it displays it to the terminal GUI.


## Play along at home

You can actually access the standard streams of other processes. Try taking the following steps:

1) Open up two terminal sessions.

2) From the first terminal run the command `ls -l /proc/$PPID/fd`. This will tell you what pseudo-terminal your shell is using to read from and write to.

3) In the second terminal write to the first pseudo-terminal device file with `echo "testing" > /dev/pts/<pts_number>`.

4) Take a look at the first terminal for a special surprise!



<span style="font-style: italic;font-size: 12px">
    If you're interested to see how to play with standardized streams in Go, take a look at [this example](https://github.com/grantseltzer/cmo/blob/022621ec394edbbd41af1cc8e370d7f28a2a0340/main.go#L47)
</span>