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

Standardized streams let you string together multiple commands with a pipe (`|`) in bash like this:

`cat /dev/urandom | less `

In this example, bash executes the commands on both sides of the pipe and writes the stdout of `cat` to stdin of `less`. For both, stderr is written to the terminal. Most programs, like `less`, are made to write to stdout/stderr and read from stdin for this exact reason.

Let's take a look at how we'd implement pipes in Go!

/*

    Create commands (exec.Cmd) for each one
    Point out that stdout/stderr are io.Writer
    and stdin is io.Reader

    Since these are such powerful interfaces (link to that post), we could theoretically
    replace them with anything, like files

    In fact, outside of Go, stdin/stdout/stderr map to special files. `ls -lah /proc/1/fd/...`

    Set stdin of second command to stdout of first one

*/




When a new process is created, file descriptors are opened for each of these standardized streams.