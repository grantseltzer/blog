+++
title = "Effective security is understandable security"
Description = ""
Tags = []
Categories = []
Date = 2019-12-07T03:32:37+00:00
+++

Let's say you're building a chat bot for the public to use to automate some tasks of your companies offering. The main feature is serving user-specific API keys.

You certainly did your best to sanitize input, you have a robust authorization workflow, you used a modern 'safe' language, and only the latest encryption schemes. However, you know no software is perfect and want to make sure you aren't leaving open any unnesecary risk for your bot to be exploited. When you evaluate your mission, the goal can be plainly stated: <i>your application shouldn't be able to do what it's not designed to do.</i> 

The chatbot was designed to take user input from clients, do some authorization computation, read secrets from files, and respond over HTTPS. It wasn't design to, let's say, run arbitrary shell code, or load kernel modules. This may seem obvious and mundane to point out if you're not in security but believe me new vulnerabilities in popular software are disclosed [constantly](https://twitter.com/CVEnew).

So if we accept that it's fully possible your chatbot is exploitable, what can we do about it?

Well, the Linux kernel (which you'll be running your chat bot server on) provides a bunch of security tools and systems. The way most of them work is to limit the priviledges and resources that the application process has available. Let's dive into an example:

## Seccomp

Remember when you broke down the functionality of your slackbot? Reading files containing API keys, and sending/receiving messages over HTTPS? Your kernel doesn't understand, nor care, about the higher level tasks that your application is trying to accomplish. The kernel instead completes the services that your application requests of it, along with those of every other process that's running. I'm talking about system calls.

System calls are the interface between userspace applications and the operating system itself. For example, in order to read those files your chatbot doesn't need to know how to find the actual 1's and 0's on the physical hard drive where the files are located. The kernel handles that for it. Instead, your chatbot uses the [read](http://man7.org/linux/man-pages/man2/read.2.html) system call, to which the kernel responds with the contents of the file.

There are <b>hundreds</b> of system calls and programs are using them constantly. They are how any program gets anything done. For example, try running the command `strace ls`. This will run the `ls` command, and print a line for every system call that's used:

```
[*] strace ls                                                                                                                    
execve("/usr/bin/ls", ["ls"], 0x7ffe949616d0 /* 60 vars */) = 0
brk(NULL)                               = 0x561b87ef0000
arch_prctl(0x3001 /* ARCH_??? */, 0x7ffee85d4660) = -1 EINVAL (Invalid argument)
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
fstat(3, {st_mode=S_IFREG|0644, st_size=113194, ...}) = 0
mmap(NULL, 113194, PROT_READ, MAP_PRIVATE, 3, 0) = 0x7fc1a4802000
close(3)                                = 0
openat(AT_FDCWD, "/lib64/libselinux.so.1", O_RDONLY|O_CLOEXEC) = 3
read(3, "\177ELF\2\1\1\0\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0P\210\0\0\0\0\0\0"..., 832) = 832
fstat(3, {st_mode=S_IFREG|0755, st_size=188664, ...}) = 0
mmap(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x7fc1a4800000
mmap(NULL, 181744, PROT_READ, MAP_PRIVATE|MAP_DENYWRITE, 3, 0) = 0x7fc1a47d3000
mprotect(0x7fc1a47da000, 139264, PROT_NONE) = 0
mmap(0x7fc1a47da000, 106496, PROT_READ|PROT_EXEC, MAP_PRIVATE|MAP_FIXED|MAP_DENYWRITE, 3, 0x7000) = 0x7fc1a47da000
mmap(0x7fc1a47f4000, 28672, PROT_READ, MAP_PRIVATE|MAP_FIXED|MAP_DENYWRITE, 3, 0x21000) = 0x7fc1a47f4000
mmap(0x7fc1a47fc000, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_F
...
```

<i>A fraction of the output of `strace ls`</i>

With that in mind, you may be wondering why I'm bringing up system calls and what it has to do with security. 