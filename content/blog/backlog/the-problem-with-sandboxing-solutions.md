+++
title = "The problem with sandboxing solutions"
Description = ""
Tags = []
Categories = []
Date = 2119-12-07T03:32:37+00:00
+++

Let's say we're building a chat bot for the public to use to automate some tasks of your companies offering. The main feature is serving user-specific API keys.

The chatbot was designed to take user input from clients, do some authorization computation, read secrets from files, and respond over HTTPS. It wasn't designed to, let's say, run arbitrary shell code, or load kernel modules. This may seem obvious and mundane to point out if you're not in security but new vulnerabilities in popular software are disclosed [constantly](https://twitter.com/CVEnew).

So if we accept that it's fully possible that our chatbot is exploitable, what can we do about it?

Well, the Linux kernel (which we'll be running our chat bot on) provides a bunch of powerful security tools and systems. The way most of them work is to limit the priviledges and resources that the application process has available. Let's dive into an example:

## <b>System Calls and Seccomp</b>

Remember when you broke down the functionality of your slackbot? Reading files containing API keys, and sending/receiving messages over HTTPS? Your kernel doesn't understand, nor care, about the higher level tasks that your application is trying to accomplish. The kernel instead completes the services that your application requests of it, along with those of every other process that's running. I'm talking about system calls.

System calls are the interface between userspace applications and the operating system itself. For example, in order to read those files our chatbot doesn't need to know how to find the actual 1's and 0's on the physical hard drive where the files are located. The kernel handles that for us. Instead, your chatbot uses the [read](http://man7.org/linux/man-pages/man2/read.2.html) system call, to which the kernel responds with the contents of the file.

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

You can read more about any particular system call with `man 2 <syscall name>`

The ability to use system calls are a fundamental resource which all programs utilize to operate. As such, limiting the priviledge to use them has strong implications for security. This is what <b>seccomp</b> provides for linux. Seccomp allows software developers or operators to create filters on a per-process basis. You can specify what system calls are allowed, or which aren't. You can also create fine-grained filters for specifying system calls only with specific arguments.

Here's a few examples of system calls you'd want to block:

<u>umount, unshare, setns, clone</u> - used for changing namespaces, a fundamental piece of containers

<u>quotactl</u> - used for changing hardware resource limits of the process

<u>create_module, delete_module</u> - interacting with kernel modules

<u>bpf, ptrace, kcmp</u> - kernel tracing mechanisms

<u>reboot</u> - reboots the machine

## <b>How seccomp is used</b>

If you've ever run a docker container, you've used seccomp. The open container initiative maintains [a specification](https://github.com/opencontainers/runtime-spec/blob/master/schema/config-linux.json#L194) for how to define what seccomp filters you want to run your container process with.

Here's an example of a seccomp configuration that you can use to block the `getcwd` system call and allow all others: 

<center>![no-getcwd](/karn/no_getcwd.png)</center>

You can run a container with a seccomp proifle using the `--security-opt` flag like so:

`docker run -it --security-opt seccomp=./block_getcwd.json fedora bash`

You may be wondering why you have never interacted with this before. The reason is, thankfully, there is a default profile most container runtimes use! It was originally written by the esteemed Jess Frazelle. The default takes into account what system calls 99% of applications will need to function without breaking them. The system calls I used as examples above are of course <i>not</i> allowed by default. You can find info on the default list [here](https://docs.docker.com/engine/security/seccomp/).

If it's not a containerized application it works the same way. Every process in linux has a seccomp context which is consulted on every system call. You can install seccomp filters in your program using [libseccomp](https://github.com/seccomp/libseccomp).

## <b>The scary part</b>

Plenty of people try to do things in containers that the default seccomp profile does not allow. When they do, i'd bet 99 times out of 100 those people run the container fully privileged (i.e. use the `--privileged` flag). That's a understandable thing to do. They're trying to do something cool and they're getting a useless 'Permission Denied' error which is killing their vibe.

The problem is that when you run with the privileged flag, you're granting full device access, granting all capabilities, and disabling seccomp, apparmor, and SELinux.

This is exactly the problem with most security tools, especially kernel level ones. <b>If your security tool is easier to turn off than use, everyone will just turn off!</b>

Look at SELinux, when was the last time you wrote a custom SELinux policy for VLC player when you got an EPERM while trying to watch Rick and Morty? That's right, NEVER!

So the challenge is: how to get people to stop disabling seccomp.

## <b>A common attempt at a solution</b>

It's simple to get visibility into system calls being used. You can use `strace` for example. That will give us every system call a specific command uses as they're called.

Some engineers at Red Hat even productionized using eBPF to trace containers as they run for system call usage ([blog](https://podman.io/blogs/2019/10/15/generate-seccomp-profiles.html)). This way you can run your tests in a tracing environment and generate an appropriate seccomp profile accordingly. 

The problem with that however, is that no one has 100% test coverage, leaving yourself open to missing system calls that a fringe branch of execution utilizes.  Even if every branch was covered, the profiling has to be redone for every new version of the application or any of its dependencies.

It also requires mature infrastructure to automate the profiling as part of CI/CD.

