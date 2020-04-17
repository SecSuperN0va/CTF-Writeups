# Challenge 1 - Memecat Battlestation

## Message
> Welcome to the Sixth Flare-On Challenge! 
> 
> This is a simple game. Reverse engineer it to figure out what "weapon codes" you need to enter to defeat each of the two enemies and the victory screen will reveal the flag. Enter the flag here on this site to score and move on to the next level.
> 
> * This challenge is written in .NET. If you don't already have a favorite .NET reverse engineering tool I recommend dnSpy
> 
> ** If you already solved the full version of this game at our booth at BlackHat  or the subsequent release on twitter, congratulations, enter the flag from the victory screen now to bypass this level.

## Provided Files
```
./1 - Memecat Battlestation\MemeCatBattlestation.exe
./1 - Memecat Battlestation\Message.txt
```
## Methodology

### Initial Overview

Let's start by getting a feel for the program, and what exactly it is we're trying to achieve. 

When we run `MemeCatBattlestation.exe` we are eventually presented with the following screen:

![Stage 1 Prompt for MemeCatBattlestation](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_stage_1_prompt.png)

As per `Message.txt`, we need to identify the relevant "weapon codes" in order to reveal the flag for this level. An incorrect weapon code issues an `Invalid Weapon Code` message.

`Message.txt` tells us that the challenge has been written in .NET. We can confirm this by using opening the file in CFF Explorer, as shown below where a couple of key indicators have been highlighted:

![CFF Explorer window showing the MemeCatBattlestation.exe File Attributes](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_cff_explorer.png)

The good first step for reversing a .NET binary is to attempt decompilation. In a lot of cases, a good .NET decompiler will be able to reproduce the bulk of the 
source code for a given binary (less any comments since these get stripped out during compilation). Let's see how well the dnSpy .NET decompiler handles this executable.

Once you've started dnSpy, drag the `MemeCatBattlestation.exe` binary onto the panel on the left (or click through File->Open->...). 
The executable will then be analysed and decompiled, with the class heirarchy and decompiled code navigable on the left hand side, as shown here:

![dnSpy Window with MemeCatBattlestation.exe Loaded](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_first_load.png)

We can now begin hunting through the "source" for something that will help us find the first weapon code.

### Locating the First Weapon Code




## Tools Used

Tool name|URL (if necessary)
:---|:---
CFF Explorer | https://ntcore.com/?page_id=388
dnSpy | https://github.com/0xd4d/dnSpy