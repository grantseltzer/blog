+++
title = "BPF Map Concurrency Techniques"
Description = ""
Tags = []
Categories = []
Date = 2022-05-17T00:00:00+00:00
column = "left"
+++

There are times when developing your BPF projects when you need to ensure safe access to shared memory. You may have a counter that you're updating from various different BPF programs and reading in userspace. You may also be updating map values from both userspace and from BPF. In this post i'll demonstrate a couple different techniques for handing this scenarios safely. 

## Per-cpu maps

Per-cpu maps are types of maps where each CPU has its own copy of underlying memory. Since BPF programs can't be preempted, when you access a value inside one of these maps from your BPF program, you know that it's the only program touching that value. The userspace program can _read_ these values at any time safely.

The advantage of this approach is completely avoiding lock contention. It's therefore the most performant way of sharing a value that's only updated in BPF.

The disadvantage of this approach is that you can't update the map values from userspace safely.

### Example

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