+++
title = "Linux Overlayfs"
Description = ""
Tags = []
Categories = []
Date = 2019-09-18T03:32:37+00:00
+++

Remember back to when your teacher in grade school would write on sheets of clear plastic, stack them, and display them with an overhead projector? That is exactly how `overlayfs` works... except with filesystems.

Overlay filesystems allow you to take multiple directory trees and view them as if they were merged together. The added benefit is that changes in the merged view do not affect the underlying directories. There are many use cases for this, mostly related to containers, but more on that at the end.

Let's look at an example:

<center>![seperate](/overlay/seperate.png)</center>

Here we have three seperate directories. They each contain various files. You may also notice that both `/tmp/middle` and `/tmp/upper` contain files with the same name (`c.txt`).

Let's say I want to create an overlayfs with these three directories. You can do it from the command like this:

`mount -t overlay....` //TODO:

The order here is important. You can create an overlay with any amount of directories. The order in which you specify them is the order that they're effectively stacked on top of one another.

<center>![stacked](/overlay/stacked.png)</center>

Here's what creating the overlayfs mount is effectively doing. The 'overlay' is what you see if you were to look through all these layers like sheets of clear plastic on an overhead projector:

<center>![overlayview](/overlay/overlayview.png)</center>

In the case of `c.txt` here, the instance of the file that's in the highest most layer is what's displayed.

All of the layers except the top one are read-only. This means changes made to files from the unfified overlay directory will not change the actual files. Changes would be written to a new file in the top most layer and displayed over the original. If you don't want any changes to files in your bottom layers you can just create an empty directory to use as your top layer.

Here's what this all looks like in terminal:

//TODO:


# Why?

//TODO: