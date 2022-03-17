+++
title = "Handling errors with CGO"
Description = ""
Tags = []
Categories = []
Date = 2022-03-16T00:00:00+00:00
column = "left"
+++

One of the main projects that I work on is [libbpfgo](https://github.com/aquasecurity/libbpfgo). This is a Go wrapper around [libbpf](https://github.com/libbpf/libbpf), a userspace library for dealing with bpf objects. The wrapper uses CGO to reference individual functions and data types in libbpf, which is written in C.

For example, `BPFLoadObject()` is a libbpfgo API function which calls `bpf_object__load()`, a libbpf API function.

```
func (m *Module) BPFLoadObject() error {
	ret := C.bpf_object__load(m.obj)
	if ret != 0 {
		return fmt.Errorf("failed to load BPF object")
	}

	return nil
}
```

The goal for libbpfgo is to fully implement the libbpf API ([which is pretty big](https://libbpf.readthedocs.io/en/latest/api.html)). One complication with this is that libbpf has very inconsistent error handling. Some APIs will return an integer error code directly, some will return a NULL pointer and set the error code in errno, some will return an error code inside of a pointer, and some return an error code which is also in errno. As a result of trying to maintain libbpfgo's error handling sanity, I've picked up some lessons on how you can use CGO to your advantage.

`errno` is essentially just a global variable. It's used to convey errors in cases where directly surfacing an error isn't always easy. Keep in mind that C functions can't have more than one return value like in Go. errno is also used quite a bit with system calls. 

If you're calling a C function that uses errno, you can add a second return variable to capture the value of errno into an `error` variable. For example:

```
func (m *Module) GetMap(mapName string) (*BPFMap, error) {
	cs := C.CString(mapName)
	bpfMap, errno := C.bpf_object__find_map_by_name(m.obj, cs)
	C.free(unsafe.Pointer(cs))
	if bpfMap == nil {
		return nil, fmt.Errorf("failed to find BPF map %s: %w", mapName, errno)
	}

	return &BPFMap{
		bpfMap: bpfMap,
		name:   mapName,
		fd:     C.bpf_map__fd(bpfMap),
		module: m,
	}, nil
}
```

In the above example, `bpf_object__find_map_by_name()` is an API function which returns a pointer. That pointer will either be a memory address of a bpf map, or in the case of an error, `NULL`. The error code is set to errno. 

C standards assign a specific cause of error to specific integer values. Go has these defined [here](https://pkg.go.dev/syscall#E2BIG). Since these are wrapped in the standard Go error type, you can treat it like any error. You can also cast an integer error code as an `syscall.Errno` for the same benefit. Like so:

```
func (b *BPFMap) Resize(maxEntries uint32) error {
	errC := C.bpf_map__set_max_entries(b.bpfMap, C.uint(maxEntries))
	if errC != 0 {
		return fmt.Errorf("failed to resize map %s to %v: %w", b.name, maxEntries, syscall.Errno(-errC))
	}
	return nil
}
```

In the above example, errC represents an integer error code (libbpf returns them as negative). So `syscall.Errno(-errC)` gives us a workable error type.