+++
title = "Supporting CO:RE in Tracee"
Description = ""
Tags = []
Categories = []
Date = 2023-07-23T03:32:37+00:00
column = "left"
+++

If you're used to developing software in a high level language like Go or Java you probably haven't thought about supporting different operating system versions much. Sure you want to be able to run on Linux, Macos, or Windows, but that's mostly abstracted away for you. 

If you're developing eBPF software, however, you have to think about the hundreds of Linux kernel versions that your users may be using. When your eBPF programs are reading in specific kernel data structure fields, there's no guarantee of backwards compatibility or stable APIs. Take a look at this example:

In Linux version 4.18, in order to get the pid of a process within a PID namespace you would read fields in the following order:

`task_struct->group_leader->pids[PIDTYPE_PID].pid->numbers[LEVEL].nr`

but starting in kernel 4.19 this data was moved to:

`task_struct->group_leader->thread_pid->numbers[LEVEL].nr`

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

This works by replacing libbpf helper functions like `bpf_probe_read` which simply reads from one location to another. Instead you could just use `bpf_core_read`. This helper uses offset relocation for source address using __builtin_preserve_access_index(). An overly simple explanation of how it works is that the helper uses kernel debug info (BTF) to find where kernel structure fields have been relocated to. For an actual in depth explanation of how this works, check out Andrii Nakriyko's [blog post](https://nakryiko.com/posts/bpf-portability-and-co-re/) on the subject.

## Adding this support to Tracee

#### vmlinux.h

The first thing we needed to do was generate a `vmlinux.h` file. I wrote a whole [post](/blog/vmlinux-header) about this file but in summary, it contains all the kernel data structure definitions of a particular kernel. We generated a single vmlinux.h file and commmitted it to source control. All the kernel data structure accesses in tracee bpf code use those definitions.

#### Updating our kernel-read macro

Tracee defines a custom macro that it uses for reading data structures named `READ_KERN`. You can see it used above. Before recent CO:RE changes it's definition looked like this:

```
#define READ_KERN(ptr) ({ typeof(ptr) _val;                             \
                          __builtin_memset(&_val, 0, sizeof(_val));     \
                          bpf_probe_read(&_val, sizeof(_val), &ptr);    \
                          _val;                                         \
                        })
```

It creates a value, zeroes out memory, reads in the value with `bpf_probe_read`, and 'returns' the address.

All the CO:RE changes did was change bpf_probe_read to `bpf_core_read`:

```
#ifndef CORE
#define READ_KERN(ptr) ({ typeof(ptr) _val;                             \
                          __builtin_memset(&_val, 0, sizeof(_val));     \
                          bpf_probe_read(&_val, sizeof(_val), &ptr);    \
                          _val;                                         \
                        })
#else
#define READ_KERN(ptr) ({ typeof(ptr) _val;                             \
                          __builtin_memset(&_val, 0, sizeof(_val));     \
                          bpf_core_read(&_val, sizeof(_val), &ptr);    \
                          _val;                                         \
                        })
#endif
```

You can see that we use a compile time variable called "CORE". That's passed via clang using `-DCORE`. Alternatively you can use `bpf_core_read` directly or even better yet `BPF_CORE_READ`/`BPF_CORE_READ_INTO` from libbpf.

One important thing to note is that as a result of this change we had to un-nest succesive calls of `READ_KERN`. Under the hood `bpf_core_read()` applies the clang function `__builtin_preserve_access_index()` which causes the compiler to describe type and relocation information. You cannot nest calls to `__builtin_preserve_access_index()` so we ended up with changes like this:

```
static __always_inline u32 get_mnt_ns_id(struct nsproxy *ns)
{
    return READ_KERN(READ_KERN(ns->mnt_ns)->ns.inum);
}
```

turned into:

```
static __always_inline u32 get_mnt_ns_id(struct nsproxy *ns)
{
    struct mnt_namespace* mntns = READ_KERN(ns->mnt_ns);
    return READ_KERN(mntns->ns.inum);
}
```

#### Missing Macros



2) Missing macros/functions

3) Verifier/performance turmoil