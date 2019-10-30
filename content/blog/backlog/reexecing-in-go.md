+++
title = "Re-execing Go"
Description = ""
Tags = []
Categories = []
Date = 2023-08-05T03:32:37+00:00
+++


runningProcessExecutable, err := os.Readlink("/proc/self/exe")
if err != nil {
    panic("couldn't confirm executable path, do you have a procfs, bruh??")
}



