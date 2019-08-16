+++
title = "Debugging Go tests"
Description = ""
Tags = []
Categories = []
Date = 2019-08-15T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
This post discusses building go test binaries and walking through them with delve
</span>

I recently was working on debugging a unit test I wrote in Go. I couldn't figure out why one of my test cases was causing a runtime error that never happened when running my actual program. I was using a runtime directive so I suspected there may be some difference between doing a `go test` and a `go run`. I was looking through Go build mode [documentation](https://golang.org/cmd/go/#hdr-Build_modes) while wondering if I could step through it with a debugger. Lo and behold you can compile your tests into an ELF executable! As a result I was able to step through my unit tests using a debugger.

Let's take a look at this esoteric example <i>(inspired by [Dave Cheney](https://twitter.com/davecheney/status/1133172785440624640))</i>:

```
package switchers

func SwitchFunction(a, b int, c *int) string {
    switch *c {
    case a:
       return "a"
    case b:
       return "b"
    default:
       return "c"
    }
}
```

```
package switchers

import "testing"

func TestSwitch(t *testing.T) {

    var (
      a int 
      b int
      c = &b
    )

    x := SwitchFunction(a, b, c)

    if x != "c" {
        t.Error("wtf?")
    }
}
```

We can compile a test binary with `go test -c`. As it turns out, the go `test` command is completely configurable with all linker, loader, and runtime flags. For example, you can change your `GOOS` and `GOARCH` environment variables to compile different test files.

You can then go ahead and run that binary through a debugger, such as [delve](https://github.com/go-delve/delve) with `dlv exec switchers.test`

You're going to want to set a breakpoint for the unit test you're trying to debug and continue to it:

![breakcontinue](/test-build-modes/breakcontinue.png)

From there you can step through your test one line (`step`) or instruction (`stepi`) at a time. Try out this example and see if you can figure out what's going on! Find the example code [here](https://github.com/grantseltzer/switchers-blog-example).