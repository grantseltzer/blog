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

Let's take a look at how we'd implement pipes, using standardized streams, in Go!

We'll start by making two executable commands, one for each in the example above.

```
    catCommand := exec.Command("cat", "/dev/urandom")
    lessCommand := exec.Command("less")
```

The `Cmd` type in Go's exec package has a field for each standardized streams:

```
type Cmd struct {
    Stdin  io.Reader
    Stdout io.Writer
    Stderr io.Writer
    Args   []string
    ...    // a bunch more fields
}
```

Each of the streams is represented by an `io.Reader` or `io.Writer`. This is very good design which I wrote about [here](/blog/the-beauty-of-io-writer). By default the reader and writer's will be populated by files. `os.File` implements both `io.Reader` and `io.Writer`. 

You may be wondering why a file would be used to represent stdin, stdout, and stderr. The simple answer is that everything is a file in Linux world. The useful answer is that when you open a terminal it has its own set of standard standard streams. It also creates a special file in `/dev` which other proc

```
[root@117bcc9d4064 /]# ls -l /proc/self/fd/0
lrwx------ 1 root root 64 May 19 18:03 /proc/1/fd/0 -> /dev/pts/0
```


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