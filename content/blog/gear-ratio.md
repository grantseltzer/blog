+++
title = "Bike gear ratio explained"
Description = ""
Tags = []
Categories = []
Date = 2029-03-18T00:00:00+00:00
column = "left"
+++

When collecting components for a new bike, or upgrading an existing one, there are many options to consider. Most important, but often overlooked, is the choice of gearing. By this, I mean the choice of front chainrings, back cassette cogs, and the ratio between them. 

As you pedal, you pull your chain over a front chainring and around a back gear. When you change gears, you're moving the chain onto a larger or smaller gear in the cassette. The same applies to shifting your chain between your front chainrings. **The gear ratio is an expression of which front chainring you're using, divided by which back gear you're using**. This is much more than a notation though, there's some really cool math involved. 

**The gear ratio expresses how many times your back wheel will spin, everytime you complete a revolution of your pedals**. Let's dive into what the means.

Let's say your chain is on a front chainring with 42 teeth, and on a back gear with 11 teeth. This means your gear ratio is `42 / 11 = 3.82`. In other words, everytime you complete one full pedal stroke, the back wheel will turn just shy of 4 complete times. Conversely if your chain is on the 42 tooth chainring, and 42 tooth back gear, your gear ratio is `42 / 42 = 1.00`.

<img of drivetrain on marigold>

So what do these numbers mean in experience? At the most basic level, the higher the number, the harder you have to pedal to turn your wheel. If you're going downhill, you want a higher gear ratio so that you can comfortably pedal, the same goes for a lower gear ratio when going uphill. Additionally, if you want to sustain higher speeds and are pedaling with more power, you want that higher ratio.

To make this feel less abstract, consider cadence. **Cycling cadence is how many times your pedals complete a revolution per minute**. In other words, how fast your pedaling. A comfortable cadence is between 85-100. **You should strive to gernally keep the same cadence regardless of speed, or gradient**.

**Speed (mph) = Cadence * (Gear Ratio * Wheel Diameter) * (Pi/1056)**

**Speed (kph) = Cadence * (Gear Ratio * Wheel Diameter) * (Pi/644)**

//////////////


This is a short explanation about how to reason about what cassette and chainring to choose when building a bike drivetrain. The same logic applies no matter if you're building a road, mountain, cyclocross, gravel, or any other kind of bike. Though your usecase for the bike will influence your decision. 

Your cassette cogs and your chainring use the same size teeth. As such, you can think about your gear ratio in terms of fractions of teeth. 

Take a look at my bike drive train:

![drivetrain](/drivetrain.png)

I only have one front chainring. It has 42 teeth. The smallest cog in my cassette has 11 teeth and the largest has 42 teeth. 

_If my chain is on the smallest cog my gear ratio will be `42 / 11 = 3.82`. This means that every time I pedal one full revolution, my back wheel will make 3.82 full revolutions._ If my chain is on the largest cog, every time I pedal one revolution, the back wheel will also complete one revolution (`42 /42 = 1.0`).

