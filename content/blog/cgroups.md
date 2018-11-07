+++
title = "cgroups: what they're hiding will blow your mind!"
Description = ""
Tags = []
Categories = []
Date = 2018-10-13T03:32:37+00:00
+++

<span style="color:grey;font-style: italic;font-size: 14px">
This post will introduce you to cgroups. Everything from what they are, how they're implemented, how they're used, and how you can use them will be discussed. The goal is to make cgroups accesible and easy to understand as they are very powerful and widely used.
</span>

Cgroups are a feature of the Linux kernel by which groups of processes can be monitored and have their resources limited. For example, if you don't want a google-chrome process (or its many child processes) to exceed a gigabyte of RAM or 30% total CPU usage, cgroups would let you do that. Configuring cgroups is also one of the central mechanisms by which containers 'contain'. They are an extremely powerful tool by which you can guarentee performance, but understanding how they work and how to use them can be a little daunting. In this post we're going to survey the various resources we can limit with cgroups, dive into how they work under the hood, and learn how we can start using them! 

Before we get into cgroups, there's a few bases we should cover. One of the fundamental pieces of any operating system is the process, which is just a running instance of a program.  When you want to run a program the Linux kernel loads the executable into memory, asigns a process ID to it, allocates various resources' for it, and begins to run it. Throughout the lifetime of a process the kernel keeps track of its various state and resource information. The data structure in the Linux source code is called a [task_struct](https://github.com/torvalds/linux/blob/master/include/linux/sched.h#L590). This is represented in the diagram below:

![DIAGRAM](DIAGRAM.png)

<!-- Briefly go into the css_set field of the task_struct -->

<!-- Each of those corresponds to the proccess' membership to individual cgroups -->

<!-- So what are cgroups? -->

<!-- For example, let's look at the memory cgroup -->

<!-- So how would you limit a process' memory using cgroups? (cgroupfs) -->

<!-- This is how containers do it! (containerd/cgroups) -->

<!-- Alright, so what's going on under the hood -->

<!-- Other examples of cgroups and how they're used -->

Cgroups, or 'Control groups', are a mechanism by which the Linux kernel allows users to specify  limits on the hardware resources that tasks have available to them. For example, particularly memory hungry programs can be launched in a cgroup that only has access to 10% of the CPU and 512MB of memory. 

// something about how each subsystem will handle this differently, like "That way if it runs out of memory it'll be restarted or will be scheduled away, etc...


 In this way you can ensure other workloads on the system will not be starved of memory 

With that in mind, let's break down what cgroups actually are and what the various resources are that you can limit with them.

In the first version of cgroups <i>(which is the most widely used)</i> there are 13 unique cgroup 'controllers'. 

launching Chrome and don't want it to completely eat your processor and RAM you can run it in a cgroup that only has access to 10% of total CPU utilization and 512MB of memory. 