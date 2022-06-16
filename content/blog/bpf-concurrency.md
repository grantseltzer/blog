+++
title = "BPF Map Concurrency Techniques"
Description = ""
Tags = []
Categories = []
Date = 2022-06-16T00:00:00+00:00
column = "left"
+++

There are times when developing your BPF projects when you need to ensure safe access to shared memory. You may have a counter that you're updating from various different BPF programs and reading in userspace. You may also be updating map values from both userspace and from BPF. In this post i'll demonstrate a couple different techniques for handing these scenarios safely. 

## Per-cpu maps

Per-cpu maps are types of maps where each possible CPU has its own copy of underlying memory. Since BPF programs can't be preempted, when you access a value inside one of these maps from your BPF program, you know that it's the only program touching that value. The userspace program can _read_ these values at any time safely. 

Note that this is only safe if the read can occur with a single operation. If the value in the map requires multiple reads (such as a large struct), it's possible that userspace only reads a partial update. The same is true of BPF programs that can sleep and are using large data types as values.

The advantage of this approach is completely avoiding lock contention. It's therefore the most performant way of sharing a value that's only updated in BPF.

The disadvantage of this approach is that you can't update the map values from userspace safely.

A simple example of how per-cpu maps are useful is updating a shared counter. There are plenty of reasons why you might need to use a counter, such as keeping track of lost events when using ring buffers.

Let's work through a simple example, counting the number of times a BPF program is called.

We'll start with defining the per-cpu map, in this case a per-cpu array.

```
struct {
	__uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, __u64);
} percpu_counter SEC(".maps");
```
{{< subtext >}}
Defining the per-cpu array
{{< /subtext >}}

Note that this only has 1 entry. This is because we only need it for a single counter. However, each CPU will have its own version of this single entry. Therefore, on my machine (which has an 8 core CPU), it technically has 8 entries. To demonstrate this, I ran `bpftool map dump name percpu_counter` to show the layout of the underlying structure:

```json
[{
        "key": 0,
        "values": [{
                "cpu": 0,
                "value": 0
            },{
                "cpu": 1,
                "value": 0
            },{
                "cpu": 2,
                "value": 0
            },{
                "cpu": 3,
                "value": 0
            },{
                "cpu": 4,
                "value": 0
            },{
                "cpu": 5,
                "value": 0
            },{
                "cpu": 6,
                "value": 0
            },{
                "cpu": 7,
                "value": 0
            }
        ]
    }
]

```
{{< subtext >}}
Underlying layout of the per-cpu array defined above
{{< /subtext >}}

Using this map in BPF is the same as a normal BPF array:

```
SEC("fentry/__x64_sys_mmap")
int mmap_fentry(struct pt_regs *ctx)
{
    __u32 key = 0;
    __u8 *value = bpf_map_lookup_elem(&percpu_counter, &key);
    if (value) {
        *value += 1;
    }

    return 0;
}
```

In userspace you have to read each value from the map into a memory region equal to the size of the value multiplied by the number of cpu. The values will be read as an ordered array, where the index corresponds with the cpu number.

```
...
    int num_cpus;
    __u32 value_size;

    num_cpus = libbpf_num_possible_cpus();
    value_size = bpf_map__value_size(map);
    void *data = malloc(roundup(value_size, 8) * num_cpus);

    int err = bpf_map_lookup_elem(map->fd, key, data);
    if (err) {
            free(data);
            return libbpf_err_ptr(err);
    }
...
```

## Spinlocks
 
Spinlocks are featured in BPF programs. They enable programs to hold onto values that are stored in maps. They allow for sharing of a single value between multiple BPF programs, as well as simple operations from userspace. Let's look at a simple example.

If you have a map of integers where you want to protect each value. Note that this is different from locking the entire map itself.

We'll define the value type and map as follows:

```
struct map_locked_value {
    int value;
    struct bpf_spin_lock lock;
};

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, struct map_locked_value);
} counters_hash_map SEC(".maps");
```

In this case, we only have one value. Let's say we use this as a counter for tracking lost events in a ringbuffer. Take note that we use `bpf_spin_lock()` and `bpf_spin_unlock()` around editing of the counter:

```
...
    int *event;
    struct map_locked_value *lost_event_counter;
    int key = 1;

    lost_event_counter = bpf_map_lookup_elem(&counter_hash_map, &key);
    if (!lost_event_counter) {
        return 0;
    }

    // Reserve space on the ringbuffer for the sample
    event = bpf_ringbuf_reserve(&events, sizeof(int), ringbuffer_flags);
    if (!event) {
        bpf_spin_lock(&lost_event_counter->lock);
        lost_event_counter->val++;
        bpf_spin_unlock(&lost_event_counter->lock);
        return 0;
    }

    *event = 9999;
    bpf_ringbuf_submit(event, ringbuffer_flags);
...
```

In userspace, it's then possible to safely read or update these values, however you can't do both. This can be done by passing the flag `BPF_F_LOCK` to `bpf_update_elem()` or `bpf_lookup_elem()`. Since it would break the safety guarantees of BPF to let user space hold the lock indefinitely (and therefore prevent a BPF program from completing), you can only rely on the individual calls to lookup and update to complete atomically. This is certainly a downside, but still an advantage to per-cpu maps in that you can update values safely. This also likely degrades performance significantly because of lock contention.

## Atomic operations

At the time of writing this, atomic operations have been merged into the BPF instruction set. Toolchain support is to follow, but regardless likely available to BPF programs are [atomic builtin functions](https://llvm.org/docs/Atomics.html#libcalls-atomic).

These functions are useful for sharing single values between multiple BPF programs. They however do not allow for locking of values between userspace and BPF.

```
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, int);
} counter_hash_map SEC(".maps");

SEC("fentry/__x64_sys_mmap")
int mmap_fentry(struct pt_regs *ctx)
{
    int *counter;
    int key = 1;

    counter = bpf_map_lookup_elem(&counter_hash_map, &key);
    if (!counter) {
        return 0;
    }

    __atomic_add_fetch(counter, 1, 0);
    bpf_printk("Counter: %d\n", *counter);
}
```

See [official documentation](https://llvm.org/docs/Atomics.html) for proper usage.
