+++
title = "BPF Attach Cookies"
Description = ""
Tags = []
Categories = []
Date = 2023-08-09T00:00:00+00:00
column = "left"
+++

BPF has a helper function called `bpf_get_attach_cookie`. It's available in bpf programs like kprobes, uprobes, and tracepoints. It can be very useful for many use cases so i'll be explaining how to use it, and going over a few examples from real code i've written.

A cookie is just an unsigned 64-bit integer. That's it. You can assign a cookie to a bpf program when you attach it. For example, here's code using the go `cilium/ebpf` library to assign a cookie to a uprobe:

```
l, err := executable.Uprobe(symbolName, bpfobject.UprobeProgram, &link.UprobeOptions{
	Cookie: uint64(3),
})
```

In this case, for no real reason, I'm assigning the value 3 as the cookie.

Then, in the bpf program, I can get that value using the `bpf_get_attach_cookie` helper:

```
SEC("uprobe/instrument")
int uprobe_instrument(struct pt_regs *ctx)
{
    __u64 cookie_value = bpf_get_attach_cookie(ctx);
    bpf_printk("%d\n", cookie_value);  // prints "3"  
    return 0;
}
```

Cookies are useful because they allow you to provide context to your bpf program as to what it's attached to, or what logic it should follow. Without cookies, if you're sharing a single ringbuffer between multiple instances of the same bpf program, it's difficult to know which program the ringbuffer events came from in user space.

# Example usage

All code from this post can be found [here](https://github.com/grantseltzer/bpf-cookie-examples/tree/main/cmd)

## Event Context

Let's say you're writing a program that attaches a single generic bpf program to multiple symbols via uprobes. The bpf program simply reads the first 50 bytes off the top of the stack on entry and sends them up to user space for analysis. In user space, we want to analyze those bytes for debugging/analysis. We can use a cookie when we attach the bpf program to each symbol, as to tell the bpf program what symbol it's attached to. We'll assign a u64 ID to each symbol's name.

In the example code, we'll just communicate the symbol context back up to user space over the ringbuffer.


#### Assigning the symbol ID cookie in userspace:

```
symbolNamesToID := map[string]uint64{
	"main.foobar": 1,
	"main.bazbuz": 2,
}

for symName, symID := range symbolNamesToID {
	l, err := executable.Uprobe(symName, objs.UprobeInstrument, &link.UprobeOptions{
		Cookie: symID,
	})
	defer l.Close()
	if err != nil {
		log.Fatal(err)
	}
}
```

#### Retrieving the symbol ID cookie in bpf and writing it back to user space:

```
struct event {
    __u64 event_id;
    char stack_content[50];
};
const struct event *unused __attribute__((unused));

SEC("uprobe/instrument")
int uprobe_instrument(struct pt_regs *ctx)
{
    // Get the event ID from the cookie
    __u64 event_id = bpf_get_attach_cookie(ctx);

    struct event *e;
    e = bpf_ringbuf_reserve(&events, sizeof(struct event), 0);
    if (!e) {
        return 0;
    }

	// Send an event over the ringbuffer containing the event's ID, and stack content
    event->event_id = event_id;
    bpf_probe_read(&event->stack_content, 50, ctx->sp);
    bpf_ringbuf_submit(e, 0);

    return 0;
}
```

#### Reading events off the ringbuffer in user space:

```go
for {
	// Blocking wait for events off ringbuffer
	record, err := reader.Read()
	if err != nil {
		if errors.Is(err, ringbuf.ErrClosed) {
			break
		}
		continue
	}

	// Parse the raw bytes from struct representation
	// into the source struct definition
	err = binary.Read(
		bytes.NewBuffer(record.RawSample),
		binary.LittleEndian,
		&event,
	)

	if err != nil {
		log.Printf("failed to interpret binary data from raw sample")
		continue
	}

	fmt.Printf("The symbol %s had the first 50 stack bytes: %w\n", symbolIDToName[event.event_id], event.stack_content))
}
```

## Filtering

Many bpf-based projects will filter events in user space based on various parameters such as PID, UID, or GID. We can use cookies to pass these filter parameters, and therefore cut down on time spent handling it in user space.

```
SEC("kprobe/do_unlinkat")
int kprobe__do_unlinkat(struct pt_regs *ctx)
{
    __u64 target_uid = bpf_get_attach_cookie(ctx);
    __u64 uid = bpf_get_current_uid_gid();

    if (target_uid != uid) {
        return 0;
    }

    struct event *e;
    e = bpf_ringbuf_reserve(&events, sizeof(struct event), 0);
    if (!e) {
        return 0;
    }
    e->uid = uid;

    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

## Map index for arbitrary context (more complex filtering)

While the two examples above are interesting, there's really no limit to what you can do with cookies (except, of course, for the limitations of bpf itself; more on that in the next section).

We can place arbitrary data structures in bpf maps from user space, then set the index of those structures as the bpf cookie, giving us way more context than a single u64 can provide. Here's an example similar to above, except with multiple specified filters:

#### 'Passing' a struct via cookie:

```
	var indexInFilterMap uint64 = 1
	filters := bpfFilters{
		Uid: 0,
		Gid: 0,
	}
	err = objs.FiltersMap.Update(indexInFilterMap, filters, ebpf.UpdateNoExist)
	if err != nil {
		log.Fatal("can't update filter map: ", err)
	}

	_, err = link.Kprobe("do_unlinkat", objs.KprobeDoUnlinkat, &link.KprobeOptions{
		Cookie: indexInFilterMap,
	})
	if err != nil {
		log.Fatal(err)
	}
```

And retrieving: 
```
struct filters {
    int uid;
    int gid;
};

struct bpf_map_def SEC("maps") filters_map = {
	.type        = BPF_MAP_TYPE_HASH,
	.key_size    = sizeof(u64),
	.value_size  = sizeof(struct filters),
	.max_entries = 100, 
};


SEC("kprobe/do_unlinkat")
int kprobe__do_unlinkat(struct pt_regs *ctx)
{

	// Retrieve the index to find the filters struct via the cookie
    __u64 map_index_for_filter = bpf_get_attach_cookie(ctx);

	// Get the filters struct and make checks accordingly
    struct filters* filters = (struct filters*)bpf_map_lookup_elem(&filters_map, &map_index_for_filter);
    if (!filters) {
        bpf_printk("could not find filter");
        return 0;
    }
    __u64 giduid = bpf_get_current_uid_gid();
    __u32 gid = giduid>>32;
    __u32 uid = (__u32)giduid;
    if (filters->uid != uid) {
        bpf_printk("uid did not match");
        return 0;
    }
    if (filters->gid != gid) {
        bpf_printk("gid did not match");
        return 0;
    }
	// etc...
...
}
```

### Conclusion

There is quite a bit that you can do with bpf cookies, far more complex than the examples in this post. In an upcoming blog post I'll be exploring how cookies can be useful across tail calls.
