+++
title = "Basic Guide to Linux Mailing Lists"
Description = ""
Tags = []
Categories = []
Date = 2029-09-27T00:00:00+00:00
column = "left"
+++

The Linux kernel is the biggest open source project in existence. It has tens of thousands of contributors from all around the world, from many different companies and communities. 

Linux development does not happen in a single github repository, and likely never will. Instead there are many forks of the linux kernel. Development happens in these forks for very specific subsystems, only a fraction of the overall code. Contributors submit relevant patches to the 'mailing list' that is used for each of these forks. The fork maintainers review these patches, and at regular intervals submit groups of patches 'upstream' to more generalized forks. All these patches eventually make their way up to the 'mainline' kernel which a single maintainer presides over. Eventually the forks pull down the changes from other downstream forks. 

It's a huge task to keep track of this whole system at once but luckily as an individual contributor, you don't need to. Once you know what subsystem community you'd like to be a part of, you can find the correspond _mailing list_.

Mailing lists are where kernel developers discuss ideas, and submit patches. Mailing lists are not much more than an email forwarder. You send an email to the mailing list, and then everyone who is subscribed to the mailing list gets your email. It's an intimidating system so let's dive into how to start using it.

## Subscribe

You can subscribe to the mailing list of your choice using majordomo (a mailing list manager). You can find the many lists for the various subsystem communites [here](http://vger.kernel.org/vger-lists.html). You can find instructions [here](http://vger.kernel.org/majordomo-info.html#subscription) for subscribing, but essentially you want to send an email to `majordomo@vger.kernel.org` with the body of you email saying only `subscribe <list-name>` (where list name would be replaced by something like 'bpf'). You can unsubscribe the same way.


## Organizing yourself in Gmail
- Filter

## Participating in conversation
- how to not top-post

## Submitting patches
