+++
title = "Replacing procfs with bpf"
Description = ""
Tags = []
Categories = []
Date = 2025-06-21T00:00:00+00:00
column = "left"
+++

_You can find all the code displayed in this post in my repo [here](https://github.com/grantseltzer/bpf-iter-test)._

The [proc file system](https://man7.org/linux/man-pages/man5/proc.5.html) provides to users information about the processes on a running linux system via a file system interface. The directory structure is organized such that every process has its own directory. The files in the directory are useful for finding out permissions, state, open files, and more. I wrote a [small post](https://www.grant.pizza/blog/procfs/) about it in 2019.

Commonly used utilities like `ps` and `top` work by iterating over every directory in the procfs and reading the files like `stat` and `status`. The files themselves [aren't real files](https://docs.kernel.org/filesystems/vfs.html), so reading each of these files doesn't involve reading from disk at all. However, performance wise, reading of each file _does_ pay the cost of the system calls used as if they were disk backed. A simple strace on my system shows that for each process ps calls 7 system calls (newfstatat x3, openat, read, close).

I bring up performance because there's another convenient way of gathering this information which is far more performant. It's called the task bpf iterator.

### bpf iterators

_From [kernel docs](https://docs.kernel.org/bpf/bpf_iterators.html):_

_A BPF iterator is a type of BPF program that allows users to iterate over specific types of kernel objects. Unlike traditional BPF tracing programs that allow users to define callbacks that are invoked at particular points of execution in the kernel, BPF iterators allow users to define callbacks that should be executed for every entry in a variety of kernel data structures._

There's one such bpf iterator already implemented for the `task_struct`, the kernel's representation of a process. We can write a bpf program which, when manually activated, gets called on each `task_struct`. So instead of iterating over each directory in procfs, we can write a bpf program that iterates over each task. This means one activation of the iterator, and not switching between kernel/user contexts for every single process by using lots of system calls.

Here's an example task bpf iterator program:

```
SEC("iter/task")
int ps(struct bpf_iter__task *ctx)
{
	struct seq_file *seq = ctx->meta->seq;
	struct task_struct *task = ctx->task;
	if (task == NULL) {
		return 0;
	}
	// Only process thread group leaders (to dedepulicate threads)
	if (task->group_leader != task) {
		return 0;
	}

	info_t info = {
		.pid = task->tgid,
		.ppid = task->parent->tgid,
		.uid = task->cred->uid.val,
		.gid = task->cred->gid.val,
	};

	long err = bpf_probe_read_kernel_str(info.comm, sizeof(info.comm), (void *)task->comm);
	if (err < 0) {
		bpf_printk("could not read kernel str comm: %ld", err);
		return 0;
	}
	err = bpf_seq_write(seq, &info, sizeof(info));
	if (err < 0) {
		bpf_printk("could not seq write: %ld", err);
		return 0;
	}
	return 0;
}
```

The kernel docs linked above do a good job explaining about the sequence file structure so I won't break it down line by line. The only thing you need in order to understand what this program is doing is that it's called on each task tracked by the running kernel. On each invocation, `ctx->task` references the target task.

In the simple example above we populate a struct with relevant fields (pid, ppid, uid, gid, comm) and write it as binary data to a sequential file.

### User space

A nice thing about the design of bpf iterators is that they're triggered on demand. When you load a bpf iterator, making a `read` system call on the resulting file descriptor will cause the bpf iterator to trigger. The result of the read call will be the combined sequential output of the bpf program.

In the case of our bpf program above, the resulting output data will be the binary data of each populated `info_t`. Here's code in Go that loads, reads, and decodes this data:

```
...
    // Load the compiled bpf object
	collection, err := ebpf.LoadCollection("task.bpf.o")
	if err != nil {
		log.Fatalf("Failed to load module: %v", err)
	}

	// Get the iterator program from the loaded object
	taskDump, ok := collection.Programs["ps"]
	if !ok {
		log.Fatal("no task dump")
	}

	// Attach the iterator program
	iter, err = link.AttachIter(link.IterOptions{
		Program: taskDump,
	})
	if err != nil {
		log.Fatalf("Failed to load module: %v", err)
	}

	// Open the iterator to get an io.ReadCloser
	reader, err := iter.Open()
	if err != nil {
		log.Fatalf("Failed to open iterator: %v", err)
	}

	wholeBuffer := []byte{}
	tempBuf := make([]byte, 1024)

	for {
		// Read from the reader
		n, err := reader.Read(tempBuf)
		if err != nil && err != io.EOF {
			log.Printf("Failed to read: %v", err)
			break
		}
		if err == io.EOF {
			break
		}
		wholeBuffer = append(wholeBuffer, tempBuf[:n]...)
	}

	// Decode the binary data into a Go struct with same framing as info_t
	infos := ProcsInfo{}
	infoSize := int(unsafe.Sizeof(Info{}))
	for i := 0; i < len(wholeBuffer); i += infoSize {
		if i+infoSize <= len(wholeBuffer) {
			info := (*Info)(unsafe.Pointer(&wholeBuffer[i]))
			infos[int(info.pid)] = info
		}
	}

	// Print result
	for pid, info := range p {
		fmt.Printf("PID: %d, PPID: %d, UID: %d, GID: %d, Comm: %s\n", pid, info.ppid, info.uid, info.gid, info.comm)
	}
```

Output:

```
[*] sudo ./bpf-iter-test                                                                                                                

PID: 50, PPID: 2, UID: 0, GID: 0, Comm: kworker/R-kinte
PID: 776901, PPID: 2, UID: 0, GID: 0, Comm: kworker/1:3
PID: 883945, PPID: 294281, UID: 1000, GID: 1000, Comm: node
PID: 33, PPID: 2, UID: 0, GID: 0, Comm: cpuhp/3
PID: 85, PPID: 2, UID: 0, GID: 0, Comm: kworker/R-charg
...
```

### pinning

Another possible improvement is to pin the bpf iterator program to a file. This approach is particularly useful for monitoring systems that need to run as non-root users but still need access to process information.

Here's how to pin the iterator:

```
// After attaching the iterator
err = iter.Pin("/sys/fs/bpf/my_task_iter")
if err != nil {
    log.Fatalf("Failed to pin iterator: %v", err)
}
```

Once pinned, any user with permissions to read this file can read the data with `cat /sys/fs/bpf/my_task_iter`.

# Comparison

### Benchmarks

I ran benchmarks on current code in the datadog-agent which reads the relevant data from procfs as described at the beginning of this post. I then implemented benchmarks for capturing the same data with bpf. The performance results were a major improvement.

On a linux system with around 250 Procs it took the procfs implemention 5.45 ms vs 75.6 us for bpf (__bpf is ~72x faster__). On a linux system with around 10,000 Procs it took the procfs implemention ~296ms ms vs 3ms us for bpf (__bpf is ~100x faster__).

The performance difference comes from several key factors. Procfs reading requires multiple system calls per process. BPF iterators use just one system call regardless of process count. Each system call involves user/kernel context switches. BPF iterators eliminate this per-process overhead by running entirely in kernel space until completion. Also BPF programs access kernel data structures directly, this eliminates file system overhead and buffer copying. 

### More Info, and More Iterators

There is more information we can get from bpf iterator that we can't from procfs as well. For example:

- Scheduling stats, vruntime, load weight, schedule policy
- Memory management internals
- Security credentials (cred, seccomp, lsm labels)
- Namespace pointers
- Cgroup details
- Signal handling internals
- ...

These above ideas are only from the task iterator, there's also already upstream iteartors for:

- Open Files
- Virtual memory areas
- Sockets
- Bpf maps/programs
- Kernel symbols

Any kernel object can have an iterator implemented for it as well! 

The future of system monitoring is increasingly moving toward bpf, and task iterators are just one example of how it can solve real performance problems in production systems. 

_You can find all the code displayed in this post in my repo [here](https://github.com/grantseltzer/bpf-iter-test)._
