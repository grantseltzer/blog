+++
title = "Using Karn for Seccomp Enforcement"
Date = 2019-12-11T03:32:37+00:00
+++

<center>![karn](/karn/karn_art.jpeg)</center>
<center><i>me when someone turns off seccomp</i></center>


[Karn](https://github.com/grantseltzer/karn) aims to provide for Linux what [entitlements](https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/AboutEntitlements.html) provide for iOS, or what [pledge](https://man.openbsd.org/pledge.2) provides for OpenBSD. It does this by translating a high level set of intuitive 'entitlements' into complex seccomp profiles. 

For example, A developer using Karn can simply specify that their application needs to make network connections, or exec other processes and karn will handle granting it permission to do those things (and nothing else!).

So, how does it work?

[Seccomp](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html) is a powerful security system inside the linux kernel that allows programmers to limit system call privileges for running procceses. This is useful because you can do some scary things via system calls like load a kernel module, install bpf programs, or reboot a machine.

Most container runtimes use seccomp as a way of limiting privilege by default. If a program running inside the container is potentially exploitable, seccomp is a useful line of defense, keeping attackers from doing serious damage.

Here's an example of a seccomp configuration that you can use to block the `getcwd` system call and allow all others: 

<center>![no-getcwd](/karn/no_getcwd.png)</center>
<center><i>an example seccomp profile</i></center>

You can run a container with the above profile. When a process tries to use the `getcwd` syscall a seccomp filter will be run that prevents it:

<center>![no-getcwd](/karn/running_getcwd.png)</center>


Although containers have [default profiles](https://docs.docker.com/engine/security/seccomp/) which grant all the permissions most applications will need, there are plenty of potential applications which will not be allowed. In those cases most people will instantly go for running their container with the `privileged` flag, disabling seccomp, apparmor, SELinux, and granting full device access. This opens applications up to a whole slew of risks. It's also an example of my most strongly held beliefs in security:

<b>If it's easier to disable a security control than it is to configure, it's getting disabled.</b>

For example, when was the last time you heard about someone configuring SELinux instead of turning it off when they got a violation?

The reason so few people write custom seccomp configurations instead of turning seccomp off is because it requires a ton of domain knowledge of system calls, and a lot of work to profile applications. There are hundreds of system calls, often they're architecture specific, and different versions of the same library may use different versions of the same system call (i.e. fchownat vs fchown).

A common approach people could take is to trace and profile their applications to see what system calls it uses and generate a profile based on that ([example](https://podman.io/blogs/2019/10/15/generate-seccomp-profiles.html)). This however is fraught with difficulty and is fragile to the point of not actually solving the issue of stopping people from disabling seccomp.

The central philosophy that lead me to writing Karn is this: <i>In order to have effective and sustainable security the operator has to strike a balance between usability and actual effectiveness.</i>

With that in mind, let's look at the design principles of Karn:

<b>1. Use high level entitlements that match how a developer/user thinks about their application.</b> 

People think of software as needing to make network connections, not needing to `setsockopt`, `bind`, `listen`, `sendmsg`, or `recvfrom`. Karn accomplishes this with it's custom written set of [entitlements](https://github.com/grantseltzer/karn/blob/master/pkg/entitlements/entitlements.go).


<b>2. Let developers use Karn how they want to.</b>

If the goal is to make seccomp as easy and accessible as possible then Karn shouldn't change anyone's workflow. It accomplishes this by generating [OCI-compliant](https://github.com/opencontainers/runtime-spec) profiles for containers. It <i>also</i> provides simple [libraries](https://github.com/grantseltzer/karn/blob/master/docs/quickstart.md#library) that you can use in your non-containerized programs to enforce seccomp rules at the start of your process execution. Currently libraries are available in both C and Go with more languages to come.

<b>3. Denylist instead of allowlist.</b>

This could be a controversial one. The seccomp man page and community typically encourages creating an allowlist. This means specifying what system calls are allowed, and denying all others by default. This would protect you in the case that a new system call is introduced in a newer kernel which is potentially dangerous.

However, I feel this is too much of an ask for most users. The lift to profile an application is heavy, and fragile. Non-profiling techniques include static analysis which isn't effective.

Missing a needed system call is way too common of an occurrence. If the generated profile breaks user's applications they aren't going to give Karn another chance. The added benefit from denying large swaths of dangerous system calls is so great that it's worth the small risk of missing one if it'll actually be used.


## <b>Get Started!</b>

For more hands on documentation check out the [quickstart](https://github.com/grantseltzer/karn/blob/master/docs/quickstart.md) over on github. Feel free to reach out on twitter to discuss, or if i've convinced you to give Karn a try I encourage you to create issues or make a contribution! Above all, I hope you keep in mind the balance worth striking between effective and usable security.