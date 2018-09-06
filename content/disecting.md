+++
title = "Dissecting Go Binaries"
Description = ""
Tags = []
Categories = []
Date = 2018-08-31T03:32:37+00:00
+++

<!-- Intro -->

Assembly code cannot lie. By reading assembly we become as close as possible to knowing what’s being run on our computer chips. This is exactly why disassembly is important! If you have a binary with malicious intentions, disassembling it will expose them. If you can't figure out a performance bottleneck in your code, you can disassemble it for clarity. 

If you're not up to snuff on reading x86_64 assembly, don't worry, most of us aren't. You don't have to read any assembly for the purpose of this post, although it may make it more interesting. For an introduction to x86 assembly I highly recommend [this article](https://www.nayuki.io/page/a-fundamental-introduction-to-x86-assembly-programming).

So, what is disassembly? 

Disassembly is the process of converting a compiled binary file back into assembly code. To clarify let’s first go in the direction we’re used to, from source code to a compiled binary:

<center>![Compilation](/CompilerDiagram.png)</center>

The assembly code is an intermedediate form. The compiler will first turn the source code into architecture specific assembly code before 'assembling' it into the executable binary. As the name alludes to, disassembly is doing this process in reverse:

<center>![Disassembly](/DisassemblerDiagram.png)</center>

Thankfully Go has a fantastic standard toolchain that lets you play with this process. You can see the assembly code before it gets turned into 1’s and 0’s by compiling your program with the following command: <span style="color:red">`go build -gcflags -S program.go`.</span> If you already have a compiled program and want to see the assembly code you can disassemble it with <span style="color:red">`go tool objdump binaryFile`</span>.

We could end this post right here but I think it'd be a lot more interesting to build a disassembler ourselves. Let's do that.

<!-- Capstone -->

First of all, in order to build a disassembler we need to know what all of the binary machine code translates to in assembly instructions. To do this we must have a reference for all assembly instructions for the architecture of the compiled binary. If you're not familiar with this task you wouldn't think it'd be so difficult. However, there are multiple micro-architectures, assembly syntaxes, sparsley-documented instructions, and encoding schemes that change over time. If you want more analysis on why this is difficult I enjoy [this article](https://stefanheule.com/blog/how-many-x86-64-instructions-are-there-anyway/). Thankfully all of the heavy lifting has been done for us by the authors and maintainers of [Capstone](http://www.capstone-engine.org/), a disassembly framework. Capstone is widely accepted as the standard to use for writing disassembly tools and there's not much to be gained by reimplementing it.

By using Capstone and it's accompanying Go bindings, [gapstone](https://github.com/bnagy/gapstone), our only real task is to extract the relevant information from the binary file and feed it through Capstone's engine. Let's dive into how that works.

<!-- ELF's -->
When you compile a Go program on your laptop the outputted binary is probably a 64-bit ELF (`Executable Linkable Format`). There are many parts of the [ELF format specification](http://man7.org/linux/man-pages/man5/elf.5.html) but for the sake of disassembly we really only care about two of them. We care about the symbol table and the text section. 

<center>![ELF64](/ELF_64.png)</center>

First we need to define the term **symbol**. This is any name identifiable object in our code. Variables, functions, types, and constants are all symbols. The Go compiler compiles each symbol and stores reference information about in the **symbol table**. We can see in the gapstone definition of `Symbol` that each entry in the symbol table contains the symbol's name, size, memory offset, and type:

```go
// A Symbol represents an entry in an ELF symbol table section.
type Symbol struct {
	Name        string
	Info, Other byte
	Section     SectionIndex
	Value, Size uint64
}
```

_Note: Although it's not clear by naming convention, the memory offset is stored in `Value`._

Now, that seems clear, but how do we find the actual symbol? 

## Further reading

- [How many x86-64 Instructions Are There Anyway?](https://stefanheule.com/blog/how-many-x86-64-instructions-are-there-anyway/)