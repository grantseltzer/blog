+++
title = "Building Go Stack Traces from BPF"
Description = ""
Tags = []
Categories = []
Date = 2023-12-06T00:00:00+00:00
column = "left"
+++

In a couple of my posts from a few years ago ([1](/blog/tracing-go-functions-with-ebpf-part-1), [2](/blog/tracing-go-functions-with-ebpf-part-2)) I explored the idea of attaching bpf programs to Go functions via uprobes. The second post dived into how to extract values of parameters. This can be seen as part 3 of the series as I'm going to demonstrate how to get a stack trace from bpf code. The work described in this post is in contribution to my work at Datadog on the [Dynamic Instrumentation](https://www.datadoghq.com/product/dynamic-instrumentation/) product, allowing users to hook specific functions and get snapshots of parameter values and stack traces.

The purpose of a stack trace is simple. When a function is called, we want to know the order of execution of every function/line that lead to the function invocation. You can see an example of a stack trace everytime a panic occurs in Go, which are helpful to find offending code.

Take the following code as an example,

```
func stack_A() {
    stack_B()
}

func stack_B() {
    stack_C()
}

func stack_C() {
    print("hello!")
}

func main() {
    stack_A()
}
```

If we want a stack trace on invocations of `stack_C()` it would look something like this:

```
  "main.stack_B (/home/vagrant/StackTraceExample/main.go:8)",
  "main.stack_A (/home/vagrant/StackTraceExample/main.go:3)",
  "main.main (/home/vagrant/StackTraceExample/main.go:45)"
```
 
### Stack Unwinding

The process we'll use for getting a basic stack trace is a simple and well documented set of steps. The basic principle is that we're going to collect program counters (locations of machine code) as we traverse through pointers that the Go compiler saves throughout the flow of execution.

When a function is called, a new "stack frame" is allocated. This basically means that a section of the program's stack is allocated to accommodate local variables in the new function.

On ARM, when a function is called a new frame is opened, the current program counter is written to the stack. This is the return address, meaning this is the program counter we will start executing once the next routine has been completed. The value of the frame pointer is then pushed to the stack. This allows the function to restore the calling function's frame when the next routine has completed. On intel this is a little different, see [internal ABI docs](https://github.com/golang/go/blob/go1.21.4/src/cmd/compile/abi-internal.md).

To unwind the stack from the entry point of a function we read the base pointer (on ARM this is in r29). This is the stack address that stores the frame pointer. Above this on the stack is the return address of the previous frame. We save this return address! Next we dereference the frame pointer, which brings us to the previous frame pointer. The process starts again until we hit a frame pointer of 0 (meaning this is frame 0, or the beginning of the program).

The only thing to note is that uprobes trigger a bpf program right at the start of a routine. On ARM, this is before the return address is written to the stack, the very first return address will be in r30. On intel this wouldn't be the case as the return address is pushed by the call instruction. Here's what that collection looks like in bpf code:

```
struct event {
    char probe_id[40];
    __u64 program_counters[10];
};

...

__u64 bp = ctx->regs[29];
bpf_probe_read(&bp, sizeof(__u64), (void*)bp); // dereference bp to get current stack frame
__u64 ret_addr = ctx->regs[30];                // when bpf prog enters, the return address hasn't yet been written to the stack

int i;
for (i = 0; i < STACK_DEPTH_LIMIT; i++)
{
    if (bp == 0) {
        break;
    }
    bpf_probe_read(&event->program_counters[i], sizeof(__u64), &ret_addr); // Read return address to saved program counters
    bpf_probe_read(&ret_addr, sizeof(__u64), (void*)(bp-8));               // Get the next return address 
    bpf_probe_read(&bp, sizeof(__u64), (void*)bp);                         // Dereference the base pointer (traverse to next frame)
}
```

In short, on function entry a bpf program can collect all program counters that correspond to return addresses which give us a full stack trace of a program. After the above snippet of code we can submit the event over a ringbuffer to hand it off to userspace for translation.

### Translating program counters

Go provides a very simple API for translating program counters into symbols, including for line numbers of specific function calls. We open the same ELF file that we've collected program counters from, and use the `gosym` package to create a struct we can use for convenient PC to symbol resolution.

```
...
    elfFile, err := elf.Open(fileName)
    if err != nil {
        return fmt.Errorf("couldn't open elf file: %w", err)
    }

    var symbolTable *gosym.Table

    addr := elfFile.Section(".text").Addr

    lineTableData, err := elfFile.Section(".gopclntab").Data()
    if err != nil {
        return fmt.Errorf("couldn't read go line table: %w", err)
    }
    
    lineTable := gosym.NewLineTable(lineTableData, addr)

    symtab := elfFile.Section(".gosymtab")

    symTableData, err := symtab.Data()
    if err != nil {
        return fmt.Errorf("couldn't read go symbol table: %w", err)
    }

    symbolTable, err = gosym.NewTable(symTableData, lineTable)
    if err != nil {
        return fmt.Errorf("couldn't read go symbol and line tables: %w", err)
    }
...
```

After this, we can use this new gosym.Table to resolve the program counters into symbols. Here's a simple example:

```
//go:noinline
func stack_A() {
    stack_B()
}

//go:noinline
func stack_B() {
    stack_C()
}

//go:noinline
func stack_C() {
    print("hello!")
}

func main() {
    stack_A()
}
```

Collecting a stack trace for a bpf program attached to `stack_C` would look like something this:

```
{
 "ProbeID": "stack_C",
 "PID": 848497,
 "UID": 1000,
 "StackTrace": [
  "main.stack_B (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:317)",
  "main.stack_A (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:312)",
  "main.main (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:388)"
 ],
 "Argdata": []
}
```

### Inlined Functions

You may notice in the above sample code the `go:noinline` pragmas above the small functions. The Go compiler will inline routines where possible for performance optimization. This provides a challenge for developers of things like debuggers or profilers. For the sake of the Dynamic Instrumentation product, we want to be able to show our users a full stack trace regardless of if functions are inlined or not.

The problem with inlined functions is that since a new stack frame isn't allocated for the function contents, a return address is never written to the stack. Therefore even if 5 inlined functions would be called in a row and therefore should be part of the stack frame, we would only get the return address of the function call that started this chain of inlined functions.

Thankfully, Go includes a DWARF entry for every location of inlined functions.

Take a look at this code and the corresponding DWARF entries:

```
//go:noinline
func call_inlined_func_chain() {
    inline_me_1()
}

func inline_me_1() {
    inline_me_2()
}

func inline_me_2() {
    inline_me_3()
}

func inline_me_3() {
    not_inlined()
}

//go:noinline
func not_inlined() {
    print("hello!")
}

func main() {
    call_inlined_func_chain()
}
```

```

0x000118b8:   DW_TAG_subprogram
                DW_AT_name      ("main.call_inlined_func_chain")
                DW_AT_low_pc    (0x000000000009d670)
                DW_AT_high_pc   (0x000000000009d6b0)
                DW_AT_frame_base        (DW_OP_call_frame_cfa)
                DW_AT_decl_file ("/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go")
                DW_AT_decl_line (325)
                DW_AT_external  (0x01)

0x000118ef:     DW_TAG_inlined_subroutine
                  DW_AT_abstract_origin (0x0000000000010689 "main.inline_me_1")
                  DW_AT_low_pc  (0x000000000009d68c)
                  DW_AT_high_pc (0x000000000009d698)
                  DW_AT_call_file       ("/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go")
                  DW_AT_call_line       (326)

0x0001190a:       DW_TAG_inlined_subroutine
                    DW_AT_abstract_origin       (0x00000000000106a0 "main.inline_me_2")
                    DW_AT_low_pc        (0x000000000009d690)
                    DW_AT_high_pc       (0x000000000009d698)
                    DW_AT_call_file     ("/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go")
                    DW_AT_call_line     (330)

0x00011925:         DW_TAG_inlined_subroutine
                      DW_AT_abstract_origin     (0x00000000000106b7 "main.inline_me_3")
                      DW_AT_low_pc      (0x000000000009d694)
                      DW_AT_high_pc     (0x000000000009d698)
                      DW_AT_call_file   ("/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go")
                      DW_AT_call_line   (334)
```

You'll notice that every high program counter (DW_AT_high_pc) of the inlined subroutines are the same, and it fits within the range of program counters of `main.call_inlined_func_chain`. With this in mind, we can collect the high program counters of all inlined subroutines in the binary beforehand and use this for reference when resolving program counters.

Here's how it works:

Before instrumenting a binary with bpf, we create a Go map of all inlined subroutine entries. The keys will be the high program counters, and the values are a slice of all DWARF entries which have that high program counter.

```
    dwarfData, err := loadDWARF(binaryPath)
    if err != nil {
        return nil, err
    }

    entryReader := dwarfData.Reader()
    InlinedFunctions := make(map[uint64][]*dwarf.Entry),

    for {
        entry, err := entryReader.Next()
        if err == io.EOF || entry == nil {
            break
        }

        if entry.Tag == dwarf.TagInlinedSubroutine {
            for i := range entry.Field {
                // Find its high program counter (where it exits in the parent routine)
                if entry.Field[i].Attr == dwarf.AttrHighpc {
                    InlinedFunctions[entry.Field[i].Val.(uint64)] = append([]*dwarf.Entry{entry}, InlinedFunctions[entry.Field[i].Val.(uint64)]...)
                    // We put them in backwards to keep them in descending order
                }
            }
        }
        ...
    }
```

When we are translating program counters to symbols as before using the `gosym` package, we can first reference this map to see if there's any functions inlined.

```
...
    stackTrace := []string{}

    for i := range rawProgramCounters {
        if rawProgramCounters[i] == 0 {
            break
        }

        entries, ok := InlinedFunctions[rawProgramCounters[i]]
        if ok {
            for n := range entries {
                inlinedFileName, _, inlinedFunction := SymbolTable.PCToLine(rawProgramCounters[i])

                symName, lineNumber, err := parseInlinedEntry(DwarfReader, rawProgramCounters[i], entries[n])
                if err != nil {
                    return []string{}, fmt.Errorf("could not get inlined entries: %w", err)
                }
                stackTrace = append(stackTrace, fmt.Sprintf("%s (%s:%d) [inlined in %s]", symName, inlinedFileName, lineNumber, inlinedFunction.Name))
            }
        }

        fileName, lineNumber, fn := SymbolTable.PCToLine(rawProgramCounters[i])
        if fn == nil {
            continue
        }
        stackTrace = append(stackTrace, fmt.Sprintf("%s (%s:%d)", fn.Name, fileName, lineNumber))
    }
...

// parseInlinedEntry gets the name and call line of a dwarf entry
func parseInlinedEntry(reader *dwarf.Reader, pc uint64, e *dwarf.Entry) (name string, line int64, err error) {

    var offset dwarf.Offset

    for i := range e.Field {
        if e.Field[i].Attr == dwarf.AttrAbstractOrigin {
            offset = e.Field[i].Val.(dwarf.Offset)
            reader.Seek(offset)
            entry, err := reader.Next()
            if err != nil {
                return "", -1, fmt.Errorf("could not read inlined function origin: %w", err)
            }
            for j := range entry.Field {
                if entry.Field[j].Attr == dwarf.AttrName {
                    name = entry.Field[j].Val.(string)
                }
            }
        }

        if e.Field[i].Attr == dwarf.AttrCallLine {
            line = e.Field[i].Val.(int64)
        }
    }

    return name, line, nil
}
```

Putting this all together, we can see a stack trace of the `main.not_inlined` function:

```
{
 "ProbeID": "not_inlined",
 "PID": 870479,
 "UID": 1000,
 "StackTrace": [
  "main.inline_me_3 (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:334) [inlined in main.call_inlined_func_chain]",
  "main.inline_me_2 (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:330) [inlined in main.call_inlined_func_chain]",
  "main.inline_me_1 (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:326) [inlined in main.call_inlined_func_chain]",
  "main.call_inlined_func_chain (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:327)",
  "main.main (/home/vagrant/go-dynamic-instrumentation/cmd/sample_program/main.go:390)"
 ],
 "Argdata": []
}
```

### Conclusion

It's relatively straightforward to unwind the stack and populate a stack trace, including inlined functions with the help of DWARF. This all is just a small feature of Datadog's Dynamic Instrumentation product which just went into general availability. Currently it's available for Java, .Net, and Python code. I'm of course working on the Go implementation which is not yet available. I'll be sure to write more blog posts in the coming months about progress there!