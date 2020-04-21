# Challenge 4 - Dnschess

## Message
> Some suspicious network traffic led us to this unauthorized chess program running on an Ubuntu desktop. This appears to be the work of cyberspace computer hackers. You'll need to make the right moves to solve this one. Good luck!


## Provided Files
```
./4 - Dnschess\capture.pcap
./4 - Dnschess\ChessAI.so
./4 - Dnschess\ChessUI
./4 - Dnschess\Message.txt
```
## Methodology

Let's begin by taking a look at `capture.pcap` in Wireshark. The capture is full of DNS queries and their associated responses.
The DNS requests originate from IP address `192.168.122.1` (the host) with the responses coming from `192.168.122.29` (the server).

![dnschess - Wireshark - Capture.pcap](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_pcap.png)

Each request seems to represent a single chess move. For example `rook-c3-c6.game-of-thrones.flare-on.com` indicates a move of a rook 
from c3 to c6 on the virtual chess board. 

Additionally, the corresponding response for each request contains a resolved IP address within the "loopback" address range (127.0.0.0/8). 

There doesn't appear to be much more to be learned from manually analysing the packet capture, so let's move onto analysing the executables.

### Analysing ChessUI

From the message, we know that this executable was extracted from a Ubuntu maching, so we know that the `ChessUI` executable is likely to be 
in the ELF format. IDA Pro is able to disassemble ELF files, so let's see what we can learn from the internals of `ChessUI`.

![dnschess - IDA - strings](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_strings.png)

After loading the executable in IDA and opening the strings window, we can see several strings relating to the chess game-play such as "king", "pawn", "ChessBoard" etc.

Another string that jumps out as interesting is the one that starts "Could not load ChessAI.so". This is the name of one of the other files we were provided with, 
so it appears that `ChessAI.so` is infact a module used by the `ChessAI` executable. We will return to the .so file later, but for now let's see what the 
executable intends to do with it.

Cross references to the "Could not load ChessAI.so" string bring us to what appears to be the initialisation function for the UI and other game structures. 
The beginning of this function contains many references to `_gtk` functions, responsible to configuring UI components, as well as a call to `_dlopen`, with the 
first argument of "./ChessAI.so".

![dnschess - IDA - init](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_init.png)

Since we're currently focussing on the usage of `ChessAI.so` we can ignore the `_gtk` functions and focus on the use of `_dlopen` and subsequent calls 
to `_dlsym`, since these are the core functions used to load and interact with libraries in linux. Following the call to `_dlopen`, a `test` is performed 
on the return value (`rax`) and if it the value is null, then execution branches to the node where the error message "Could not load ChessAI.so..." is used. 
If the return value was not null, execution instead passes to the start of a chain of calls to `_dlsym`.

![dnschess - IDA - dlsym](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_init_dlsym.png)

`_dlsym` is used to acquire a pointer to data or a function within a loaded library dependant on an exported symbol. In the case in the image above, the symbol 
name is "getAiName". The return value from this call to `_dlsym` will be a pointer to the function "getAiName" in the loaded module. Each call to `_dlsym` in 
this function is logically wrapped in a check that logs a message if a symbol cannot be found in the provided library. The executable uses this technique to get 
pointers to the functions: `getAiName`; `getAiGreeting`; and `getNextMove`, with the pointer to `getNextMove` being stored in in a global function pointer 
within the executable, as shown below.

```
getAiName
getAiGreeting
getNextMove
```

![dnschess - IDA - Store getNextMove](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_id_init_store_getnextmove.png)

Now we know what aspects of `ChessAI.so` are being used, we can now cross-reference the stored `fGetNextMove` function pointer to identify calling locations.
If we bring up the cross-references to `fGetNextMove` they indicate a single call-site (`sub_4310+3A` in the image below):

![dnschess - IDA - fGetNextMove Xrefs](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_xref_getNextMove.png)

Following this cross-reference, we arrive at a function that takes one of three possible branches, dependent on the return value of the call to ChessAI.getNextMove (`fGetNextMove`). 
I have named this function `HandleSingleTurn`.

Looking at the image below, in the instance where `getNextMove()` returns `0`, then execution takes right branch which sets the status bar to the message "Your Move. Click or drag a piece". This is likely to 
indicate a regular successful move. If instead `getNextMove()` returns `1`, then execution takes the shorter branch in the middle. Finally, if the return value is neither `0` nor `1`, 
then execution flows through the branch on the left, displaying a dialog box with the message "Game over" and that the AI "has resigned"; presumably, this is the state we need to enter in 
order to win the game and acquire the flag.

![dnschess - IDA - Handle Turn](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_handle_turn.png)

At the point all three of these branches converge, a global value gets incremented by 1. This likely keeps track of the number of turns that have taken place in the current game.

One thing that is missing at this point is the game loop logic. `HandleSingleTurn` doesn't contain looping of any kind, which means the game loop must be controlled elsewhere.

### The Game Loop

In order to find the game loop logic, and any additional logic surrounding how the game runs, we can find cross-references to `HandleSingleTurn()`; the function containing the call
to `getNextMove()`. The only cross-reference brings us to the parameter construction for a call to `_g_timeout_add`, which refers to the glib function 
[`g_timeout_add`](https://developer.gnome.org/glib/stable/glib-The-Main-Event-Loop.html#g-timeout-add). This function is used to register a callback to be executed at regular intervals, 
until the callback returns 0. 

![dnschess - IDA - Register Game Loop](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_game_loop_registration.png)

The `HandleSingleTurn()` function is provided as the `function` parameter, alongside an `interval` value of 250 milliseconds, meaning every 250 milliseconds, `HandleSingleTurn()` 
will be called, until it returns 0.


### Tackling `ChessAI.so`

Now that we've got a relatively good grasp of the overall gameplay, we turn our focus to the behaviour of the AI opponent. The only interface to the `ChessAI.so` library we've seen 
used so far is the exported function `getNextMove()`, which is called at the start of each call to `HandleSingleTurn()`. Let's open the library in IDA and find 
this function.

Once loaded, checking the "Exports" window will reveal the three symbols that were imported in `ChessUI`. 

Jumping to `getNextMove()` we can see the function's first node starts by populating 5 local variables from values that are passed as parameters to the call. 
From this behaviour, we can retype the `getNextMove()` function to show that it takes 5 parameters. We can also see quite trivially, that the parameter 
passed through `rsi` is used almost immediately as the `src` argument in a call to `_strcpy()`, with the `dest` argument being loaded into `rdi` prior to 
the subsequent 3 call instructions. This behaviour is consistent with string construction, so we can assume that the first 4 calls in this function are responsible 
for building a string from various components.

Working from the bottom of this first node, we can see that the final operation being performed is a call to `_gethostbyname()`, with our constructed buffer 
occupying the `name` parameter. This indicates that the string being constructed is in fact a hostname, on which a DNS lookup will be performed. Casting our 
minds back to the packet capture data in `capture.pcap`, we can recall that all of the DNS queries we observed referenced the domain `game-of-thrones.flare-on.com`, 
which matches the final string to be concatenated to our hostname in this function. The following image shows this first node with all of the above information 
annotated.

![dnschess - IDA - AI - getNextMove First Node](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_getNextMove_1.png)

If the DNS lookup fails, i.e. the return value from `_gethostbyname()` is null, then `getNextMove()` returns the value 2, which as we know will terminate the game.
If the DNS lookup is successful, then execution progresses through a series of checks based on the IP address contained in the DNS response.

Firstly, the first byte of the resolved IP address is checked to ensure it equals 127, meaning the resolved IP address is a loopback address in the range 127.0.0.0/8. 
The remaining code is short-circuited if this value is incorrect.

![dnschess - IDA - AI - getNextMove Loopback Check](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_loopback_check.png)

Second, the final byte of the address is checked to ensure it is an odd number, short-circuiting to return 2 if the final byte is even.

![dnschess - IDA - AI - getNextMove Oddity Check](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_odd_check.png)

The third and final check takes byte 2 of the IP address, performs a bitwise AND operation on it with value 0xF, then compares the result against the `TurnCount` parameter, 
passed into `getNextMove()` via `edi`. The remaining code is short-circuited if the resultant value does not match the value of `TurnCount`.

![dnschess - IDA - AI - getNextMove TurnCount Check](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_turncount_check.png)

If all of the above checks pass, then execution flows into a daunting, linear sequence of instructions that operate on byte 1 of the resolved IP address to 
produce the AI's move, as well as a message to be shown to the user.

During this sequence, two global buffers are accessed. The first is a read-only (in the context of this function) buffer containing the following byte sequence:

```
Offset(h) 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F

00000000  79 5A B8 BC EC D3 DF DD 99 A5 B6 AC 15 36 85 8D  yZ¸¼ìÓßÝ™¥¶¬.6….
00000010  09 08 77 52 4D 71 54 7D A7 A7 08 16 FD D7        ..wRMqT}§§..ý×
```

I will refer to this buffer as the `localEncodedFlag`.

The second global buffer is a write-only (in the context of this function) buffer that is initialised to contain only null bytes on program start. 
I will refer to this buffer as the "localDecodedFlag".

### Decoding the flag

After each valid move, in the sense that each of the three checks on the DNS response have passed, byte 1 of the resolved IP address is 
used as a single byte XOR key, decoding the next 2 bytes of `localEncodedFlag`. The results of this operation are written into the 
appropriate 2 bytes of `localDecodedFlag`. The following pseudocode should help demonstrate this

```
remoteKeyByte = ipAddressBytes[1]
decodedFlagIndex = TurnCount * 2

localDecodedFlag[decodedFlagIndex] = remoteKeyByte ^ localEncodedFlag[decodedFlagIndex]
localDecodedFlag[decodedFlagIndex + 1] = remoteKeyByte ^ localEncodedFlag[decodedFlagIndex + 1]
```

The image below shows how this is performed in assembly:

![dnschess - IDA - AI - getNextMove Flag Decode](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_flag_decode.png)

The result of this is that each successful turn decodes 2 bytes of the flag. 

### Produce the AI Turn and Message

Once the relevant flag bytes have been decoded, the AI then needs to produce its turn to continue the game.

The AI's movement is encoded within the resolved IP address as follows. 

The first positional parameter is encoded within byte 2 of the IP address, and the value is decoded by shifting the byte to the right by 4 bits as shown below.

![dnschess - IDA - AI - getNextMove Position 1 Decode](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_decode_pos1.png)

The second positional parameter is encoded within byt 3 of the IP address, with the value being decoded by simply shifting right by 1 (or performing an integer division by 2).

![dnschess - IDA - AI - getNextMove Position 2 Decode](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_decode_pos2.png)

Once both of these parameters have been decoded, the AI selects one of a pre-defined list of "taunts" to return to the user. The taunt that gets selected corresponds with 
the value of `TurnCount`, which is used as an index into the array of `char*` values. 

![dnschess - IDA - AI - getNextMove Message Lookup](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_message_chart.png)

The array of taunts can be seen below.

![dnschess - IDA - AI - getNextMove Message Chart](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/04%20-%20Dnschess/images/dnschess_ida_ai_message_chart_array.png)

Since the index into `turnMessageChart` is the value of `TurnCount`, we can see that once `TurnCount` reaches the value of 14 (0xE), the returned message will 
be the contents of the `localDecodedFlag` buffer, that has been populated throughout the previous turns (this is named `gFlag` in the screenshots).

We can now be sure that if the correct moves are played for 15 turns, the player should be presented with the flag for this level.

### Playing the Game

In this section, we will be focussing on identifying the turns which need to be played in order to completely decode the flag in memory.

I am working on the assumption that the packet capture in `capture.pcap` contains the appropriate turns in some shape or form.

To begin, I installed the scapy module for Python, and wrote a simple script to load the data from `capture.pcap`.

I then parsed the packets to remove any responses which failed to meet any of the conditions necessary for a valid move to be made.

With this new list of moves, I was able to reconstruct the games that had been played, based on the `TurnCount` value that was encoded 
within byte 2 of the resolved IP addresses for each response.

When I found a complete set of moves, that is a game for which there were 15 consecutive moves, I was able to manually run the decode operation using the key from each packet, to 
decode a copy of `localEncodedFlag` and print it to the screen. I won't go into too much more detail, but a copy of this script is included below for clarity.




## Tools Used
Tool name|URL (if necessary)
:---|:---
IDA Pro | https://www.hex-rays.com/products/ida/
Wireshark | https://www.wireshark.org/