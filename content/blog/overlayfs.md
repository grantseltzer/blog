+++
title = "Linux Overlayfs"
Description = ""
Tags = []
Categories = []
Date = 2019-09-11T03:32:37+00:00
+++

Remember back to when your teacher in grade school would write on sheets of clear acetate, stack them, and display them with an overhead projector. That is exactly how `overlayfs` works... except with filesystems.

Overlay filesystems allow you to take multiple directory trees and create a unified view of them as if they were merged together. You can combine any amount of directories in ordered layers. All of the layers except the top one are read-only, meaning changes made to their files from the unfified overlay directory will not affect them. The top most directory, however, is read and write.