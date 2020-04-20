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

In order to start from something familiar, we focus our attention on the call to `MessageBoxA` at `0x00000000004011FD`. 
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
pushed to the stack at `0x00000000004011EF`. We can quickly see that the address being pushed is in fact a pointer to the string "Output", as we were expecting.

Returning to `lpText`, we know that the pushed value contains an address within the local stack frame, however we haven't yet identified where the contents get 
populated. In order to find the population code, we search from the start of the function, looking for references to the local `Text` variable.

![Overlong.exe - IDA - Populate Text Call Site](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/02%20-%20Overlong/images/overlong_ida_call_decode.png)

Our search identifes the address of the local `Text` variable being passed to a function (`sub_401160` in the above image), alongside two other values.
One of these values is the immediate value `0x1C`, and the other is a pointer to a global data buffer. The return value of the function (`eax`) is being
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



### Detailed Analysis
TODO
## Tools Used
TODO

Tool name|URL (if necessary)
:---|:---
IDA Pro | https://www.hex-rays.com/products/ida/