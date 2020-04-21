# Challenge 3 - Flarebear

## Message
> We at Flare have created our own Tamagotchi pet, the flarebear. He is very fussy. Keep him alive and happy and he will give you the flag.

## Provided Files
```
./3 - Flarebear\flarebear.apk
./3 - Flarebear\Message.txt
```
## Methodology

In this level, we are provided with an Android .apk file containing a digital pet, and our job is to "keep the flarebear happy".

The first thing we'll need is a way to run Android applications, whether that be an emulator or a physical device. I'll be using the Android Studio AVD emulator.

After installing Android Studio, and letting it download the necessary emulation packages, open the AVD Manager and create a new emulated device.

The emulated hardware specification shouldn't really matter, so long as the version of Android you install is sufficient to run the Flarebear .apk.

### Install flarebear.apk

Once your emulator is powered on, we can use the Android Debug Bridge (adb) to side-load flarebear.apk on the device.

Open a command prompt in `%USERPROFILE%\AppData\Local\Android\sdk\platform-tools\`, then run the following commands 
(substituting the path for the location of your flarebear.apk):

```
> adb devices
List of devices attached
emulator-5554   device

> adb.exe install "C:\path\to\flarebear.apk"
Performing Streamed Install
Success
```

The application should now be accessible on the device and we can go ahead and open it.

![Flarebear - Application Installed](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_app.png)

### Flarebear Overview

![Flarebear - Application Running](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_app_running.png)

The flarebear application has three buttons corresponding to the actions:
- feed
- clean
- play

Clicking each of these buttons triggers an animation associated with the relevant action.

### Reversing Flarebear

The first thing we'll need to do is understand what it means for the flarebear to be "happy".

In order to do this, we are going to need to be able to see how certain actions affect the flarebear; information that can be gleaned from the code.

Android applications are written predominantley in Java, which is then compiled into a language known as "dex". The compiled dex is the code that will 
actually run on the android device, and is similar to the intermediate language used by Java and .NET. In a similar way that we were able to decompile 
the binary in level 1, we can convert (roughly) the dex file contained in flarebear.apk back into compiled Java, which can then be decompiled. 
This will make it easier to work out the behaviour of the various actions within the application.

The tool we can use to convert the apk to java is called dex2jar. Dex2jar will take the apk as input, and produce a .jar file. The .jar file can then be 
opened in a Java decompiler, such as JDGui, to inspect the decompiled class heirarchy. This process is shown below.

![Flarebear - dex2jar](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_dex2jar.png)

![Flarebear - jdgui](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_jdgui.png)

#### Actions

Firstly, let's work out what happens when each of the action buttons are pressed within the application.

Searching for "feed", "clean", and "play" in the decompiler reveal the following functions:

![Flarebear - jdgui - feed](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_feed.png)
![Flarebear - jdgui - clean](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_clean.png)
![Flarebear - jdgui - play](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_play.png)

From these handlers we can assume the presence of the following attributes:
- mass
- happy
- clean
- pooCount

We can also make the following assumptions

- "feed" action results in:
  - activity "f" is saved
  - mass += 10
  - happy += 2
  - clean -= 1
  - pooCount += 0.34

- "clean" action results in:
  - activity "c" is saved
  - happy -= 1
  - clean += 6
  - pooCount -= 1
  - setMood() is called

- "play" action results in:
  - activity "p" is saved
  - mass -= 2
  - happy += 4
  - clean -= 1

An interesting feature to note is that when an "activity" is saved (i.e. "f", "c", or "p"), 
the corresponding character is appended to a string in the persistent application preferences, effectively keeping track of the order 
in which actions were performed. This string is also used to retrieve the quantity of each action when `getStat()` is called.

![Flarebear - jdgui - saveActivity](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_save_activity.png)

#### Flag Decryption

Looking through the class structure, we come across the function `FlareBearActivity.danceWithFlag()`, which performs decryption of some data 
using a password provided by the `FlareBearActivity.getPassword()` function. 

![Flarebear - jdgui - danceWithFlag](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_dance_with_flag.png)

The `getPassword()` function makes use of the quantities of the three activities ("f", "p", and "c"), to construct the final password. 
The three quantities must be the correct values for the password to be generated correctly, and thus decrypt the data that is 
likely to contain the flag for this level.

![Flarebear - jdgui - getPassword](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_get_password.png)

Brute-forcing a password of this complexity does not sound like something we want to do, at least not as a first attempt. Instead, let's shift our focus to the conditions 
that need to be met for the `danceWithFlag()` function to be called, since it is likely that this function only get's called when it has a decent chance of being able 
to execute without failing.

#### `setMood()`

![Flarebear - jdgui - setMood](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_set_mood.png)

As we can see, the `danceWithFlag()` function is called from within `FlareBearActivity.setMood()` if both the conditions `isHappy()` and `isEcstatic()` 
are true. We know from our analysis of the three actions available to the user, that `setMood()` is only called when the "clean" action is performed, so if 
we can work out what relative conditions must be met for these two additional checks to return true, then we might move closer to revealing the flag.

#### `isHappy()`

![Flarebear - jdgui - isHappy](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_ishappy.png)

Starting with `isHappy()`, we can see the first thing to happen is the "stat" values for "f" and "p" are retrieved, corresponding with the number of times that 
"feed" and "play" actions have been performed. These two values are plugged into an equation whereby the result represents the ratio of `feed:play` actions. 
The `isHappy()` function returns `true` if this ratio is between 2.0 and 2.5. This would be the case for example if there had been 4 feed actions and 2 play actions.

#### `isEcstatic()`

![Flarebear - jdgui - isEcstatic](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_isecstatic.png)

The `isEcstatic()` function performs more specific checks on the `mass`, `happy`, and `clean` attributes, returning true if and only if the following 
conditions are met:
- `mass` == 72
- `happy` == 30
- `clean` == 0

#### Solving the Simultaneous Equations

From all of the above we need to work out which values of `f`, `p`, and `c` allow all of following conditions to hold. 

`feed:play ratio`: `2p <= f <= 2.5p`

`mass`: `72 = 10f + 0c - 2p`

`happy`: `30 = 2f - 1c + 4p`

`clean`: `0 = -1f + 6c - 1p`

Entering the above into a [system of equations solver](https://www.emathhelp.net/calculators/algebra-2/simultaneous-equations-solver/?s=10f-2p%3D72%2C2f-c%2B4p%3D30%2C-f%2B6c-p%3D0&v=f%2Cp%2Cc) (or in your head if you'd rather), 
you will arrive at the result:

`f = 8`, `p = 4`, `c = 2`

This result represents a game state whereby the flarebear has been fed 8 times, played with 4 times, and cleaned twice.

#### Getting the Flag

With our results from the simultaneous equations, we can try this out in the emulator to see what happens, remembering that the `setMood()` 
function only gets called when the `clean` action is performed (i.e. make sure this is the last action you perform.).

I suggest completely removing the application and any application data from the device to prevent a miscount when entering your button presses.

Once the application has been reinstalled, open the app, enter your flarebear's name and begin entering your button presses, 
making sure to keep track of how many of each you have entered. I suggest the following pattern:

`feed:feed:feed:feed:feed:feed:feed:feed:play:play:play:play:clean:clean`

The final time you press `clean`, you should be greated with the following screen, containing the flag for this level.

![Flarebear - jdgui - success](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/03%20-%20Flarebear/images/flarebear_success.png)


## Tools Used
Tool name|URL (if necessary)
:---|:---
Android Studio | https://developer.android.com/studio
dex2jar | https://sourceforge.net/projects/dex2jar/
JDGui | http://java-decompiler.github.io/