+++
title = "The Beauty of io.Writer"
Description = ""
Tags = []
Categories = []
Date = 2019-04-04T03:32:37+00:00
column = "left"
+++

<span style="color:grey;font-style: italic;font-size: 14px">
In this post we explore best practices of defining interfaces in Go. We use `io.Writer` to break down patterns and antipatterns.
</span>

A perfect example of a properly designed Go interface is `io.Writer`:

```
type Writer interface {
    Write(p []byte) (n int, err error)
}
```

It is short, simple, and powerful. The `Write` method takes a very generic slice of bytes and writes it to <i>something</i>.

In Rob Pike's [Go Proverbs talk](https://youtu.be/PAAkCSZUG1c?t=317) he talks about how in Go, interfaces are not declared to be satisfied, they're satisfied implicitly. An interface should be a way of classifying types, not a blueprint for declaring them. In practical terms, an interface should not at all care about how it's  implemented.

Let's think about how `io.Writer` embodies this ideal. The `Write` method takes the most generic form of data, a slice of bytes. Any other data type, no matter how complex, can become a slice of bytes. In this way the method does not care about what's it's passed. It leaves so much up to the implementation's discretion. 

For example, you can define a writer that takes that slice of bytes, encodes it as a jpeg, and writes it to a specific file. You can define a writer that takes the slice of bytes, treats it as a string, and prints it to standard error. You can also define a writer that takes the slice of bytes, encodes it as mp3 data and writes it to an audio device. Currently there are over 75 types that satisfy the `io.Writer` interface in the Go standard library alone. 

This flexibility is subtle but very intentional.

Let's say you create a package that produces some kind of data, ASCII art for example. It is not your job to worry about what other programmers are using that art for. If you are exporting API that creates the art, and writes it to a file specified by a path, you are reinventing the wheel. You would have to then create an function for every possible output location. You would also be denying your users a ton of flexibility to use any of the unlimited `io.Writer`'s they may want to use. 

```
// This defeats the purpose of io.Writer
func WriteAsciiArtToFile(path string) error { 
    f, err := os.Open(path)
    if err != nil {
        return err
    }
    artBytes := makeSomeArt()
    _, err = f.Write(artBytes)
    return err
}

// Not an anti-pattern, idgaf what you do with my ascii art
func WriteAsciiArt(w io.Writer) (n int, error) {
    artBytes := makeSomeArt()
    return w.Write(artBytes)
}
```

The more methods a type has to define to conform to an interface, the less abstraction the interface provides. It's better to break up the functionality into multiple interfaces, or none at all. For the former, consider [bytes.Buffer](https://golang.org/pkg/bytes/#Buffer). It implements both `io.Reader` and `io.Writer` interfaces, meaning it has `Read` and `Write` methods. The same is true of `os.File`. 

When defining an interface you should consider the beauty of `io.Writer`. It makes for easy testing, it's flexible, easy to understand, and does not have any opinions. Be one with `io.Writer`. 