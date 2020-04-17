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

![dnSpy - Stage1Form.InitializeComponent this.fireButton Handler](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_stage_1_fire_button_handler.png)

When the fire button is clicked, the player's weapon code (`this.codeTextBox.Text`) is compared against the static string `"RAINBOW"`. 
If the two strings match, then we can see that UI elements are made invisible, the weapon code is stored in `this.WeaponCode`, 
and a victory animation is started. We can also see that if the string comparison indicates the strings do not match, then 
`this.invalidWeaponLabel` (i.e. the "Invalid Weapon Code" message) is made visible. 

Our analysis has retrieved us the first weapon code! Let's test is out in a running instance of `MemeCatBattlestation.exe`.

![Winning Stage 1](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_stage_1_success.png)

![Stage 2 Prompt for MemeCatBattlestation](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_stage_2_prompt_.png)

As you can see, we've now progressed to the second stage, and can begin work on finding the second weapon code.

### Locating the Second Weapon Code

The process for finding the second weapon code is very similar to the first, in the sense that we need to find the "on-click" handler for the fire button 
in the form. To avoid repeating myself, I'll skip over the steps for locating the handler, since it should be obvious from how we handled the first stage.

![dnSpy - Stage2Form.fireButton Handler](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_stage_2_fire_button_handler.png)

This handler function is very similar to the previous level's, however this time, rather than directly comparing the provided weapon code to a static string, 
the test logic has been separated into its own function: `this.isValidWeaponCode`. Based on the flow of the handler, we can assert that if 
`this.isValidWeaponCode` returns a _truthy_ value, then the weapon code is correct, otherwise it is not. Let's take a look at the weapon code testing 
function.

![dnSpy - Stage2Form.isValidWeaponCode](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_stage_2_code_test_function.png)

This may look more complicated than the test in Stage 1, however it remains relatively straight-forward. The `for loop` in this function 
is simply iterating over each character in the provided weapon code, and performing an in-place XOR operation against the value 0x41 (the ordinal value of 'A').
This results in a `char[]` containing an encoded version of the weapon code.

The final part of the function is a comparison between two `char[]` values, with one being the encoded weapon code, and the other a statically defined array of characters.
The result of the `SequenceEqual` function will be `true` if the two arrays contain the same values. This means that the statically defined array of characters must 
represent the encoded weapon code. 

> This approach is commonly used to avoid exposing decoded or decrypted data, since if the application was to decode the string itself when performing the test, 
> it would be simple to extract the decoded weapon code from memory.

Our next step is to attempt to decode the static array of characters, using what we know about how the weapon code gets encoded. 

It is first necessary to cover a couple of key principles regarding the XOR operation:

```
x ^ x = 0           anything XOR'd with itself equals 0.
x = (x ^ y) ^ y     XOR'ing a value with the same key twice equals the original value (by virtue of the above).
```

Using these principles, we can take each byte of the static encoded data (either by hand, or using a simple script), and XOR it 
against the original key (0x41, the ordinal value of 'A'). The result of each iteration is the original, decoded character.

Once decoded, we are left with the characters that make up the weapon code: `"Bagel_Cannon"`.

Once again, entering this code into the game will result in the victory animation being played.

![Winning Stage 2](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_stage_2_success.png)

You will now be presented with the victory screen, containing the flag for this level.

![Level 1 Flag](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_flag.png)


### Additional Notes for the Interested

After all of this, you might be thinking to yourself: "Surely there was an easier way to get the flag", especially since 
it's just shown to you in a text box on the victory screen. Well, the developers of this obviously had the same thought. 
To avoid this exact scenario, the `VictoryForm` doesn't store the decoded flag anywhere, until of course both stages 
have been won. 

At the end of each stage, the weapon code submitted by the player is stored in `this.WeaponCode` 
(once it's been confirmed as correct). When both levels are completed, and both weapon codes have been found, they are joined 
together by `Program.Main` to produce a string that resembles `<stage2Form.WeaponCode>,<stage1Form.WeaponCode>`. 
This string is then passed as the `Arsenal` argument to the `VictoryForm` constructor.

![dnSpy - Creation of the VictoryForm instance](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_victory_form_creation.png)

Within `VictoryForm.InitializeComponent`, you can see that the value of `this.flagLabel.Text` is being set to 
the placeholder value `EXAMPLE_KEY@flare-on.com`. This function also registers an "on-load" handler by appending 
`this.VictoryForm_Load` to `base.Load`.

![dnSpy - VictoryForm.VictoryForm_Load](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Memecat%20Battlestation/images/mcb_dnspy_victoryform_load.png)

This callback function looks similar to the weapon code encoding function in stage 2. It begins with a statically defined `byte[]`, 
then creates a second `byte[]` containing the relevant representation of `this.Arsenal`. Using a similar technique to 
`Stage2Form.isValidWeaponCode`, an XOR operation is performed, this time using `this.Arsenal` as the key (thanks to modulo arithmetic).
The resulting `byte[]` contains the decoded flag, which is then set to be the contents of `this.flagLabel`. 

The only way to get the correct flag decoded, is to know the key for the decoding, which is derived from the weapon codes from each stage. 

## Tools Used

Tool name|URL (if necessary)
:---|:---
CFF Explorer | https://ntcore.com/?page_id=388
dnSpy | https://github.com/0xd4d/dnSpy