+++
title = "How Go slices work"
Description = ""
Tags = []
Categories = []
Date = 2023-11-30T00:00:00+00:00
column = "left"
+++

I recently ran into a hard to find bug in my Go code when using slices. Since I've been using Go for over 8 years now, I figured this is something that others will run into and want to share what I had forgotten about how slices work.

Take a look at the following Go code:

```
x := []int{1,2,3}
y := append([]int{}, x...)
z := x
```

We have three separate slices. What I want to briefly explore is the difference between y, and z. The difference has to do with how slices are implemented by Go. This can sometimes make it hard to track down bugs, so it's important to know.

Try running the following code:

```
package main

import "fmt"

func main() {

	x := []int{1, 2, 3}
	y := append([]int{}, x...)
	z := x

	fmt.Printf("X: %v\nY: %v\nZ: %v\n", x, y, z)

	y[0] = 5
	z[1] = 15

	fmt.Printf("\nX: %v\nY: %v\nZ: %v\n", x, y, z)
}
```

You'll see that the change to z[1] also affected x[1], but the change to y[0] did not have any affect on x[0]:

```
X: [1 2 3]
Y: [1 2 3]
Z: [1 2 3]

X: [6 2 3]
Y: [5 2 3]
Z: [6 2 3]
```

You may think to print the address of the slices but you would see that they are totally unique slices:

```
...
	fmt.Printf("%p %p\n", &x, &z)
}
```
```
0xc0000a0000 0xc0000a0018
```

What gives? In order to understand what's going on, lets take a look at the definition of a slice. There's a full description on the go dev blog [here](https://go.dev/blog/slices-intro) but this image sums it up:

![slices](/slice-struct.png)

Slices are implemented as structs under the hood. They have three fields. A pointer to an array (so the address of a location in memory in which each element is laid out consecutively), as well as the length and capacity of that array. This means that in the above example, even though the slices `x` and `z` are unique, the address of the underlying array has been copied over!

### Demonstration 

In order to demonstrate, I'm going to use a product I'm building at Datadog. It's the [Dynamic Instrumentation](https://www.datadoghq.com/product/dynamic-instrumentation/) product for Go. It lets me hook specific functions and print the values of their parameters any time they're called.

Take a look at this code:

```
package main

import "fmt"

func doNothing(x []int) {}

func printSlice(x []int) {
	fmt.Printf("%v\n", x)
}

func changeElement(x []int) {
	x[0] = 99
}

func main() {

	originalSlice := []int{1, 2, 3}
	doNothing(originalSlice)

	changeElement(originalSlice)
	printSlice(originalSlice)
}
```

Based on what we've gone over so far, we would expect the function `changeElement()` to actually change the element at index 0 in the array that `originalSlice` points to. We're going to use dynamic instrumentation to hook both `doNothing()` and `changeElement()` to confirm this:

```
{
 "ProbeID": "doNothing",
 "PID": 758847,
 "UID": 1000,
 "StackTrace": [
  "main.main (/home/vagrant/slice_demo/main.go:384)"
 ],
 "Argdata": [
  {
   "Kind": "slice",
   "Size": 30,
   "Fields": [
    {
     "ValueStr": "0x4000016138",
     "Kind": "ptr",
     "Size": 8
    },
    {
     "ValueStr": "3", // Length
     "Kind": "int",
     "Size": 8
    },
    {
     "ValueStr": "3", // Capacity
     "Kind": "int",
     "Size": 8
    }
   ]
  }
 ]
}
{
 "ProbeID": "changeElement",
 "PID": 758847,
 "UID": 1000,
 "StackTrace": [
  "main.main (/home/vagrant/slice_demo/main.go:385)"
 ],
 "Argdata": [
  {
   "Kind": "slice",
   "Size": 30,
   "Fields": [
    {
     "ValueStr": "0x4000016138",
     "Kind": "ptr",
     "Size": 8
    },
    {
     "ValueStr": "3",
     "Kind": "int",  // Length
     "Size": 8
    },
    {
     "ValueStr": "3", // Capacity
     "Kind": "int",
     "Size": 8
    }
   ]
  }
 ]
}
```

Running this program also confirms that the element in the original underlying array was in fact changed after running `changeElement()`. The note here is that despite go being pass by value (meaning the parameter `x` in `changeElement()` is a newly allocated slice), the field for the address is the same, and therefore affects the original similar to if it were pass by reference.

The advantage of slices (as opposed to arrays) is that you can seemingly infinitely grow them. You'd typically do this using `append`. The main thing you have to understand here is that if you append to a slice with a length equal to its capacity, Go will create a whole new array with double the capacity of the original one. Therefore the address field that points to the array will be overwritten. Further changes to the original array won't affect the new one (and the memory gets reclaimed).

So repeating the same experiment except with an append occuring instead of changing an element will confirm a new address:

```
func expandSlice(x []int) {
	x = append(x, []int{9, 10, 11, 12}...)
	doNothing(x)
}
```

```
{
 "ProbeID": "main.expandSlice",
 "PID": 812027,
 "UID": 1000,
 "StackTrace": [
  "main.main (/home/vagrant/slice_demo/main.go:386)"
 ],
 "Argdata": [
  {
   "Kind": "slice",
   "Size": 30,
   "Fields": [
    {
     "ValueStr": "0x4000099BD0",
     "Kind": "ptr",
     "Size": 8
    },
    {
     "ValueStr": "3",
     "Kind": "int",
     "Size": 8
    },
    {
     "ValueStr": "3",
     "Kind": "int",
     "Size": 8
    }
   ]
  }
 ]
}
{
 "ProbeID": "main.doNothing",
 "PID": 812027,
 "UID": 1000,
 "StackTrace": [
  "main.expandSlice (/home/vagrant/slice_demo/main.go:372)"
 ],
 "Argdata": [
  {
   "Kind": "slice",
   "Size": 30,
   "Fields": [
    {
     "ValueStr": "0x400001E0C0",
     "Kind": "ptr",
     "Size": 8
    },
    {
     "ValueStr": "7",
     "Kind": "int",
     "Size": 8
    },
    {
     "ValueStr": "8",
     "Kind": "int",
     "Size": 8
    }
   ]
  }
 ]
}
```

### Conclusion

Be careful about passing slices into functions. Passing references to slices can also get complicated very quickly. If you're going to transform slices, it's probably best to pass slices into functions that return the resulting slice, and use that result from then on. Similar caution should be used when transforming slices in the seperate scopes of different goroutines. 