+++
title = "Bike gear ratio explained"
Description = ""
Tags = []
Categories = []
Date = 2029-03-18T00:00:00+00:00
column = "left"
+++

The bicycle drivetrain consists of pedals, cranks, chainrings, a chain, a gear cassette, and derailleurs. As you pedal, you pull your chain over a front chainring and around a back gear. When you change gears, you're moving the chain onto a larger or smaller gear in the cassette. The same applies to shifting your chain between your front chainrings. **The gear ratio is an expression of which front chainring you're using, divided by which back gear you're using.** This is much more than a notation though, there's some really cool math involved. 

**The gear ratio also expresses how many times your back wheel will spin, everytime you spin your cranks.** Let's dive into what the means.

Let's say your chain is on a front chain ring with 42 teeth, and on a back gear with 11 teeth.


//////////////


This is a short explanation about how to reason about what cassette and chainring to choose when building a bike drivetrain. The same logic applies no matter if you're building a road, mountain, cyclocross, gravel, or any other kind of bike. Though your usecase for the bike will influence your decision. 

Your cassette cogs and your chainring use the same size teeth. As such, you can think about your gear ratio in terms of fractions of teeth. 

Take a look at my bike drive train:

![drivetrain](/drivetrain.png)

I only have one front chainring. It has 42 teeth. The smallest cog in my cassette has 11 teeth and the largest has 42 teeth. 

_If my chain is on the smallest cog my gear ratio will be `42 / 11 = 3.82`. This means that every time I pedal one full revolution, my back wheel will make 3.82 full revolutions._ If my chain is on the largest cog, every time I pedal one revolution, the back wheel will also complete one revolution (`42 /42 = 1.0`).

