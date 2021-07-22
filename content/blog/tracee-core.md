+++
title = "Supporting CO:RE in Tracee"
Description = ""
Tags = []
Categories = []
Date = 2022-07-23T03:32:37+00:00
column = "left"
+++

If you're used to developing software in a high level language like Go or Java you probably haven't thought about supporting different operating system versions much. Sure you want to be able to run on Linux, Macos, or Windows, but that's mostly abstracted away for you. 

If you're developing eBPF software, however, you have to think about the hundreds of Linux kernel versions that your users may be using. When your eBPF programs are reading in specific kernel data structure fields, there's no guarantee of backwards compatibility or stable APIs. Take a look at this example:

In Linux version 4.18, in order to get the pid of a process within a PID namespace you would read fields in the following order:

```
task_struct (the kernel representation of a process)

 '-> group_leader

      '-> pids[PIDTYPE_PID]

           '-> pid

                '-> numbers[LEVEL] (where LEVEL refers to the depth of the namespace)

                     '-> nr
```

but starting in kernel 4.19 this data was moved to:


```
task_struct (the kernel representation of a process)

 '-> group_leader

      '-> thread_pid

           '-> numbers[LEVEL] (where LEVEL refers to the depth of the namespace)

                '-> nr
```

You don't have to know what any of these fields are, they're just to demonstrate that things change and it's a lot to keep track of.

Ok, so relevant data structures change from kernel version to version, how do we handle this?

## The fragile tedious way

Check out this snippet of code from tracee:

```
#if (LINUX_VERSION_CODE < KERNEL_VERSION(4, 19, 0)
    // kernel 4.14-4.18:
    return READ_KERN(READ_KERN(group_leader->pids[PIDTYPE_PID].pid)->numbers[level].nr);
#else
    // kernel 4.19 onwards, and CO:RE:
    struct pid *tpid = READ_KERN(group_leader->thread_pid);
    return READ_KERN(tpid->numbers[level].nr);
#endif
}
```

Here we have a simple example where we use macro's we defined for checking kernel versions at runtime and taking action accordingly. This is effective as long as you maintain logic for every different in kernel version for every field you want to read.

## Enter CO:RE (or 'the better way')

What if we could safely read from kernel data structures without having to worry about changes in those structure definitions? That is the promise of 'CO:RE' or 'Compile Once, Run Everywhere'.

This works by replacing libbpf helper functions like `bpf_probe_read` which simply reads from one location to another. Instead you could use `bpf_core_read`. 
