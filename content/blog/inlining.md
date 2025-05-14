+++
title = "Global bpf Functions"
Description = ""
Tags = []
Categories = []
Date = 2025-05-11T00:00:00+00:00
column = "left"
+++

The [bpf verifier](https://docs.ebpf.io/linux/concepts/verifier/) is tasked with ensuring that bpf programs that are loaded will predictably halt and run safely. It follows all branches of bpf instructions, counting each instruction as another permutation of the program's state. As it counts, there's a limit of 1 million instructions. 

If you've been writing bpf programs for a long time or have been looking at outdated examples then you're probably familiar with using the `static` modifier and `__always_inline` macro.

Prior to kernel 4.16 (Release Apr 2018), all functions in a bpf program in fact needed to be inlined. Starting with this release you could do what's called [bpf to bpf function calls](https://docs.cilium.io/en/stable/reference-guides/bpf/architecture/#bpf-to-bpf-calls). However, I didn't realize this until recently (while developing for a 5.15 kernel...). As any bpf developer would know, documentation is sparse and it's hard to know when things change. Therefore, I'd like to explore what inlining does for your program and how preventing function inlining for it expands the capability of bpf programs.

Let's take a look at a simple bpf program:

```c
static __always_inline int print_map_value() {
    __u32 key = 0;
    __u64 *val = bpf_map_lookup_elem(&value_map, &key);
    if (!val) {
        return 1;
    }
    bpf_printk("val: %d", val);
    return 0;
}

SEC("uprobe/foobar")
int foobar(struct pt_regs *ctx) {
    __u64 val = 1;
    __u32 key = 0;
    bpf_map_update_elem(&value_map, &key, &val, 0);
    print_map_value();
    print_map_value();
    print_map_value();
    return 0;
}
```

We are using the `__always_inline` macro, and as such each `print_map_value()` function call is going to be replaced by the full body of `print_map_value()`. So our bpf program will end up having 3 copies of the same set of instructions one after another.

You can verify this by compiling the program and using `llvm-objdump -d <object_file>`.

Demonstrating inlining is not the purpose of this post though. The purpose is to discuss how this affects the number of instructions counted by the verifier.

I'm going to run the above program once compiled through the verifier _(via a [tool](https://github.com/DataDog/datadog-agent/tree/main/pkg/ebpf/verifier/calculator) my coworkers wrote)_ and determine how many instructions the verifier counts:

```
Filename/Program: foo/foobar  
Stack Usage: 28  
Instructions Processed: 56  
Instructions Processed Limit: 1000000  
Max States per Instruction: 0  
Peak States: 4  
Total States: 4  
```

Now let's adapt our code to discourage inlining:

```c
static __noinline int print_map_value() {
    ...
}

SEC("uprobe/foobar")
int foobar(struct pt_regs *ctx) {
    ...
    print_map_value();
    print_map_value();
    print_map_value();
    return 0;
}
```

Running it through the same tool:

```
Filename/Program: foo/foobar
Stack Usage: 12
Instructions Processed: 64
Instructions Processed Limit: 1000000
Max States per Instruction: 0
Peak States: 6
Total States: 6
```

The instruction count got worse! The verifier still has to count each instruction as a possible state. Forcing functions to not be inlined means that we're adding instructions for setting up and tearing down a stack for each frame.

However, the stack usage improved! The stack gets cleared when each function call returns, so this is an important consideration.

### Static vs Global Functions

As you see above we've modified our helper function `print_map_value()` with the `static` keyword. Static functions maintain the verifier context of the function which called them. If a variable that is known to be of a certain range is passed to a static function, that range is still known. Conversely, if a function is not static (therefore global), then this context is not kept and the range and validity of passed variables is not kept. This has both benefit and detriment. 

The benefit of a global function is that it is only verified once independently of its invocations. Meaning that even if a global function is called 100 times, it's only verified once (unless it's also inlined). This is hugely beneficial in many applications for the sake of staying under the verifier complexity threshold.

Conversely, the challenge this presents is that global functions have to check the values of their parameters. If a function isn't called many times this can therefore increases the counted complexity of a program. There are also limitations on the types of parameters or returns of global functions. See [documentation](https://docs.ebpf.io/linux/concepts/functions/#pointers-in-global-functions) for more detail.

Let's take a look at the same example code, first with the static modifier:

```c
static __noinline int print_dereferenced_value(__u32* foo_ptr) {
    __u32 foo;
    int i;
    for (i = 0; i < 100; i++) {
        foo = *foo_ptr;
        bpf_printk("foo+i = %d", foo+i);
    }
    return 0;
}

SEC("uprobe/foobar")
int foobar(struct pt_regs *ctx) {
    __u32 a = 1;
    __u32 *b = &a;
    if (!b) {
        return 1;
    }
    print_dereferenced_value(b);
    return 0;
}

```

Since `print_dereferenced_value()` is static, the verifier knows that dereferencing *foo_ptr is safe, since it was already checked before the function was called. 

By removing static, thus making print_dereferenced_value global would result in a verifier rejection for invalid memory access. As such we'll edit our function for safety and remove the check from the top level 'main' function:

```c
__noinline int print_dereferenced_value(__u32* foo_ptr) {
    if (!foo_ptr) {
        bpf_printk("foo ptr is nil");
        return -1;
    }
    __u32 foo;
    int i;
    for (i = 0; i < 100; i++) {
        foo = *foo_ptr;
        bpf_printk("foo+i = %d", foo+i);
    }
    return 0;
}

SEC("uprobe/foobar")
int foobar(struct pt_regs *ctx) {
    __u32 a = 1;
    __u32 *b = &a;
    print_dereferenced_value(b);
    return 0;
}
```

Now let's look at the complexity comparison:

Static:
```
- Filename/Program: foo/foobar
- Stack Usage: 4
- Instructions Processed: 1612
- Instructions Processed limit: 1000000
- Max States per Instruction: 4
- Peak States: 109
- Total States: 109
```

Global:
```
- Filename/Program: foo/foobar
- Stack Usage: 4
- Instructions Processed: 1629
- Instructions Processed limit: 1000000
- Max States per Instruction: 4
- Peak States: 18
- Total States: 18
```

Again, the instruction count got marginally worse! However, we knew this would happen as we had to add extra instructions for checking if pointer is nil. The complexity benefit to global functions can be seen over multiple invocations:

```c
    int i;
    for(i = 0; i < 100; i++) {
        print_dereferenced_value(b);
    }
```

Static:

```
- Filename/Program: foo/foobar
- Stack Usage: 4
- Instructions Processed: 161305
- Instructions Processed limit: 1000000
- Max States per Instruction: 4
- Peak States: 1555
- Total States: 1555
```

Global:

```
- Filename/Program: foo/foobar
- Stack Usage: 4
- Instructions Processed: 2427
- Instructions Processed limit: 1000000
- Max States per Instruction: 4
- Peak States: 32
- Total States: 32
```

Now we see the improvement! In this case we're only using instructions towards the complexity limit for the sake of making a function call, no matter how big that function is. 

The verifier really only cares that a program will halt, it doesn't set a complexity limit for the sake of setting a limit. As such, if it knows that a function independently will always halt, calling it a limited number of times will not affect its quality of doing so.
