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

A good first step for reversing a .NET binary is to attempt decompilation. In a lot of cases, a good .NET decompiler will be able to reproduce the bulk of the 
source code for a given binary (less any comments since these get stripped out during compilation). Let's see how well the dnSpy .NET decompiler handles this executable.

Download and run dnSpy, then drag the `MemeCatBattlestation.exe` binary onto the panel on the left (or click through File->Open->...). 
The executable will then be analysed and decompiled, with the class heirarchy and decompiled code navigable on the left hand side, as shown here:

![dnSpy Window with MemeCatBattlestation.exe Loaded](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_first_load.png)

We can now begin hunting through the "source" for something that will help us find the first weapon code.

### Locating the First Weapon Code

Taking a look at the class heirarchy, we can see that this application contains a series of "Forms", which we can assume correspond with 
the various screens we see throughout the game. The main entry point for a .NET application is `Program.Main`, which we can see exists within the `MemeCatBattlestation` module.

![dnSpy - Program.Main function](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_program_main.png)

The body of `Program.Main` can be seen to be running some boilerplate code, then calling `Application.Run` on a new instance of the `LogoForm`. 
This is responsible for creating and displaying the splash screen to the player. We're not currently interested in the behaviour of the splash screen, 
so let's progress onwards. Immediately following the `LogoForm` creation, we can see an instance of `Stage1Form` being created, and passed to `Application.Run`. 
We can assume from this class' name, that this corresponds with the "Stage 1" screen that we need the weapon code for, so let's take a deeper look into it.

![dnSpy - Stage1Form.InitializeComponent](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_stage_1_init.png)

In the function `Stage1Form.InitializeComponent` we can see a large amount of initialisation code for the various variables and objects that make 
up the `Stage1Form` instance. A couple of these member variables stand out as being potentially interesting. These are `this.codeTextBox` and `this.fireButton`. 
We know from interacting with the UI, that when we click the button labelled "Fire!", we get a message stating the weapon code was incorrect. This means that 
there must be some logic attached to the button so that when it's clicked, the code we have provided is tested. If the code fails the test, we are obviously presented 
with a failure message. We can thus assume that if we pass the test, then we have the correct weapon code. Let's now look for the logic attached to the fire button.

About half way through `Stage1Form.InitializeComponent` we can see the initialisation of `this.fireButton`. Other than setting up the colour scheme, 
label, size etc. we can also see the assignment `this.fireButton.Click += this.FireButton_Click`. This assignment is adding an "on-click" handler 
to the button. This logically translates to: "when the button is clicked, run this function". 

![dnSpy - Stage1Form.InitializeComponent this.fireButton Handler Assignment](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_stage_1_fire_button_handler_assign.png)

`Stage1Form.FireButton_Click` is a rather simple function and it should be immediately obvious how the logic works here. 

 ![dnSpy - Stage1Form.InitializeComponent this.fireButton Handler Assignment](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_stage_1_fire_button_handler.png)

When the fire button is clicked, the player's weapon code (`this.codeTextBox.Text`) is compared against the static string "RAINBOW". 
If the two strings match, then we can see that UI elements are made invisible, the weapon code is stored in `this.WeaponCode`, 
and a victory animation is started. We can also see that if the string comparison indicates the strings do not match, then 
`this.invalidWeaponLabel` (i.e. the "Invalid Weapon Code" message) is made visible. 

Our analysis has retrieved us the first weapon code! Let's test is out in a running instance of `MemeCatBattlestation.exe`.

![Winning Stage 1](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_stage_1_success.png)

![Stage 2 Prompt for MemeCatBattlestation](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_stage_2_prompt.png)

As you can see, we've now progressed to the second stage, and can begin work on finding the second weapon code.



## Tools Used

Tool name|URL (if necessary)
:---|:---
CFF Explorer | https://ntcore.com/?page_id=388
dnSpy | https://github.com/0xd4d/dnSpy