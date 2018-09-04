+++
title = "Dissecting Go Binaries"
Description = ""
Tags = []
Categories = []
Date = 2018-08-31T03:32:37+00:00
+++

Assembly code cannot lie. By reading assembly we become as close as possible to knowing what’s being run on our computer chips. This is exactly why disassembly is important! If you have a binary with malicious intentions, disassembling it will expose them. If you can't figure out a performance bottleneck in your code, you can disassemble it for clarity. 

If you're not up to snuff on reading x86_64 assembly, don't worry, most of us aren't. You don't have to read any assembly for the purpose of this post, although it may make it more interesting. For an introduction to x86 assembly I highly recommend [this article](https://www.nayuki.io/page/a-fundamental-introduction-to-x86-assembly-programming).

So, what is disassembly? 

Disassembly is the process of converting a compiled binary file back into assembly code. To clarify let’s first go in the direction we’re used to, from source code to a compiled binary:

<center>![Compilation](/Compiler.png)</center>

The assembly code is an intermedediate form. The compiler will first turn the source code into architecture specific assembly code before 'assembling' it into the executable binary. As the name alludes to, disassembly is doing this process in reverse:

<center>![Disassembly](/Disassembler.png)</center>

Thankfully Go has a fantastic standard toolchain that lets you play with this process. You can see the assembly code before it gets turned into 1’s and 0’s by compiling your program with the following command: <span style="color:red">`go build -gcflags -S program.go`.</span> If you already have a compiled program and want to see the assembly code you can disassemble it with <span style="color:red">`go tool objdump binaryFile`</span>.

However, I think it'd be a lot more interesting to build a disassembler ourselves. Let's do that.

When you compile a Go program on your laptop the outputted binary is probably a 64-bit ELF (`Executable Linkable Format`). There are many parts of the [ELF format specification](http://man7.org/linux/man-pages/man5/elf.5.html) but for the sake of disassembly we really only care about two of them. We care about the symbol table (or symtab) and the data sections (or .data). Let's take a look at go in-depth on this:

<center>![ELF64](/ELF64.png)</center>
