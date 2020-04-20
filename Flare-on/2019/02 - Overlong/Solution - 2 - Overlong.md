# Challenge 2 - Overlong

## Message
> The secret of this next challenge is cleverly hidden. However, with the right approach, finding the solution will not take an <b>overlong</b> amount of time.


## Provided Files
```
./2 - Overlong\Message.txt
./2 - Overlong\Overlong.exe
```
## Methodology

### Initial Triage

Jumping right in, if we run the provided `Overlong.exe`, a message box pops up containing the title text: "Output", alongside the message text: 
"I never broke the encoding: ".

![Overlong.exe Message Box](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_message_box.png)

The message box doesn't give us too much to go on, so let's go ahead and open the executable in IDA Pro, and navigate to the entry point (`start`).

![Overlong.exe - IDA - Entry Point](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_ida_start.png)

In order to start from something familiar, we focus our attention on the call to `MessageBoxA` at 0x004011FD. 
According to the [MSDN documentation](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messageboxa), `MessageBoxA` takes the following parameters:

```
int MessageBoxA(
  HWND   hWnd,
  LPCSTR lpText,
  LPCSTR lpCaption,
  UINT   uType
);
```

Conveniently, IDA has already labelled the appropriate values for us in the disassembly window. From our initial execution of the binary, 
we are expecting two strings to be passed to this function: "Output" as the `lpCaption` parameter, and "I never broke the encoding:" as the `lpText` parameter.

Let's start hunting for these parameters. Firstly, since we know that `Overlong.exe` is a 32-bit executable, and `MessageBoxA` is a `WINAPI` function 
(thus following the `__stdcall` calling convention), we can be sure that all arguments passed to the function will be first pushed onto the stack. 
Working backwards from the call instruction, we first find `push 0`, corresponding with the `hWnd` parameter. Next we see `push edx`, which is populating 
the `lpText` parameter. The value of `edx` in this instruction is dependent on the previous instruction: `lea edx, [ebp+Text]`, where `ebp+Text` is a pointer 
to a memory location within the local stack frame; we'll return to this shortly. The final parameter we want to locate is `lpCaption`, which we can see being 
pushed to the stack at 0x004011EF. We can quickly see that the address being pushed is in fact a pointer to the string "Output", as we were expecting.

Returning to `lpText`, we know that the pushed value contains an address within the local stack frame, however we haven't yet identified where the contents get 
populated. In order to find the population code, we search from the start of the function, looking for references to the local `Text` variable.

![Overlong.exe - IDA - Populate Text Call Site](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_ida_call_decode.png)

Our search identifes the address of the local `Text` variable being passed to a function (`sub_401160` in the above image), alongside two other values.
One of these values is the immediate value 0x1C, and the other is a pointer to a global data buffer. The return value of the function (`eax`) is being
stored in `var_4` and is then immediately retrieved and used as an offset from the address pointed to by `Text`, where a null byte is then being stored.
This behaviour could indicate the return value represents a size or length of `Text` once the function has returned. Since we know that `Text` must contain 
a string for the subsequent call to `MessageBoxA`, it is reasonable to be appending a null-terminator to the apparent end of a string to prevent over-reading. 
Another interesting at this point, is that the value 0x1C is infact the length of the string "I never broke the encoding: ". 

We now have a decent amount of information about the function we're interested in, which we can apply to the function prototype in IDA:

- The first parameter (`lpOutput`) contains a pointer to a locally allocated `char[]`;
- The second parameter (`lpInput`) contains a pointer to a global statically allocated `unsigned char[]`;
- The third parameter (`cbSize`) is an `unsigned int` likely representing size of the string to write to 
- The function returns an integer representing the size of the outputted string.

![Overlong.exe - IDA - Rename Decode Function](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_ida_rename_decode_function.png)

![Overlong.exe - IDA - Re-Type Decode Function](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_ida_retype_decode_function.png)

Now this has been retyped, let's take a look at the internals of this function. A quick skim over this function shows that it contains a loop, which iterates until either the loop counter exceeds 
`cbSize`, or alternatively `var_8` is set to 0. The bulk of the loop appears to operate on the values contained in `lpInput` and `lpOutput`, with the use of function `sub_401000`. 

At this point, we could either keep delving inwards and identify exactly what is happening in this function, and any functions called within. On the other hand, we could fire up a debugger and 
dynamically instrument the input values and observe their corresponding outputs to see if that leads us in the right direction. In the hopes that the dynamic route saves us time, we'll try that first.

Executing `Overlong.exe` in your favourite debugger, make note of the image load address since this may be different to the address IDA used. 
In my case, IDA loaded the image at its desired load address (0x00400000), whereas WinDbg loaded the image at 0x00940000. We will need to 
take this into account when trying to locate the function we're interested in.

![Overlong.exe - WinDbg - Find Base Address](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_windbg_lm.png)

No that we have an interactive debugging session in the target executable, we need to work out where our function of interest is. In my IDB, the call to `PopulateTextBuffer` is 
located at 0x004011D7. This translates to a relative address of 0x11D7, which can be added to the load address in the debugger to find the relevant address.

![Overlong.exe - WinDbg - Located Target Call Site](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_windbg_located.png)

We will now want to add a breakpoint to this address so that we can inspect the parameters on the stack, before stepping over the call to inspect the result.

![Overlong.exe - WinDbg - Set Breakpoint](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_windbg_set_bp.png)

Releasing the debugger, it should stop at the breakpoint address. We now have the ability to be able to see the contents of the stack before the function call is executed. 
In WinDbg, the `dd <reg|addr>` command allows us to see memory contents. The following is the output of the `dd esp` command which dumps DWORD values from the
address pointed to by the stack pointer.

```
0:000> dd esp
00cff818  00cff824 00942008 0000001c 00000000
00cff828  00000000 00000000 00000000 00000000
00cff838  00000000 00000000 00000000 00000000
00cff848  00000000 00000000 00000000 00000000
00cff858  00000000 00000000 00000000 00000000
00cff868  00000000 00000000 00000000 00000000
00cff878  00000000 00000000 00000000 00000000
00cff888  00000000 00000000 00000000 00000000
```

In order, we can see a pointer to an address on the stack (look at the simlarity to the stack addresses on the left hand side); a pointer to an address within the confines of 
the executable; and the `cbSize` value 0x1C. We can also see a large number of null bytes, which represents the buffer that was allocated to hold `Text` in the local stack frame. 
If we were to dump more data from `esp`, we would see the following:

```
0:000> dd esp L25
00cff818  00cff824 00942008 0000001c 00000000
00cff828  00000000 00000000 00000000 00000000
00cff838  00000000 00000000 00000000 00000000
00cff848  00000000 00000000 00000000 00000000
00cff858  00000000 00000000 00000000 00000000
00cff868  00000000 00000000 00000000 00000000
00cff878  00000000 00000000 00000000 00000000
00cff888  00000000 00000000 00000000 00000000
00cff898  00000000 00000000 00000000 00000000
00cff8a8  00cff8b8
```

We can clearly see a total of 0x84 consecutive null bytes, which represents the 0x84 bytes allocated in the local stack frame at the beginning of the main function. 

If we step over this function call, based on our knowledge of the behaviour of the main function, we expect this 0x84 byte buffer to be partially 
filled with the string "I never broke the encoding: ", and `eax` will be set to the length of the string.

```
0:000> p
eax=0000001c ebx=00aaf000 ecx=0000001c edx=00000020 esi=009411c0 edi=009411c0
eip=009411dc esp=00cff818 ebp=00cff8a8 iopl=0         nv up ei pl zr na pe nc
cs=0023  ss=002b  ds=002b  es=002b  fs=0053  gs=002b             efl=00000246
Overlong+0x11dc:
009411dc 83c40c          add     esp,0Ch

0:000> db esp
00cff818  40 f8 cf 00 48 20 94 00-1c 00 00 00 49 20 6e 65  @...H ......I ne
00cff828  76 65 72 20 62 72 6f 6b-65 20 74 68 65 20 65 6e  ver broke the en
00cff838  63 6f 64 69 6e 67 3a 20-00 00 00 00 00 00 00 00  coding: ........
00cff848  00 00 00 00 00 00 00 00-00 00 00 00 00 00 00 00  ................
00cff858  00 00 00 00 00 00 00 00-00 00 00 00 00 00 00 00  ................
00cff868  00 00 00 00 00 00 00 00-00 00 00 00 00 00 00 00  ................
00cff878  00 00 00 00 00 00 00 00-00 00 00 00 00 00 00 00  ................
00cff888  00 00 00 00 00 00 00 00-00 00 00 00 00 00 00 00  ................

```

The above WinDbg output shows the `p` command being used to step over an instruction; the register values once the instruction has been executed; 
the next instruction to be executed; then a byte-dump of esp showing the updated contents. As we can see, our empty buffer is no longer empty, and 
does in fact contain the string we expected. We can also see the return value of the function is as expected (`eax=0000001c`).

Now that we've confirmed the behaviour of the function, we can re-run the executable in the debugger and rather than simply observing memory, 
we can modify it. The first thing I thought of to modify was the `cbSize` value that gets passed into the population function. It seems unusual 
that a 0x84 byte buffer would be allocated for a string which only contains 0x1C characters. Let's see what happens if we change the value, once it's 
been pushed to the stack, to 0x84, since this is the maximum number of bytes that could fit in the allocated memory.

Resetting the debugger to our breakpoint, we can use the `ed` command to write a DWORD into memory at the address where `cbSize` has been pushed.

```
0:000> ed esp+8 0x84
0:000> db esp L 10
00d3fe00  0c fe d3 00 08 20 94 00-84 00 00 00 00 00 00 00  ..... ..........
```

Stepping over the function again, and dumping the byte contents of `esp` again shows additional data in our buffer. 
Releasing the debugger results in a message box being shown with the full decoded string, containing the flag for this level.

![Overlong.exe - Success](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_success.png)

In summary, the `PopulateTextBuffer` function calls some "complicated" decoding function, iterating untill the counter exceeds `cbSize`. 
All we've done is increase the value of `cbSize` so that the loop doesn't break out untill all of the data in the encoded buffer has been decoded, 
rather that breaking when it hits the `cbSize` limit.

## Tools Used
Tool name|URL (if necessary)
:---|:---
IDA Pro | https://www.hex-rays.com/products/ida/
WinDbg Preview | https://www.microsoft.com/en-gb/p/windbg-preview/9pgjgd53tn86?activetab=pivot:overviewtab