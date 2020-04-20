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
"I never broke the encoding:".

![Overlong.exe Message Box](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Overlong/images/overlong_message_box.png)

The message box doesn't give us too much to go on, so let's go ahead and open the executable in IDA Pro, and navigate to the entry point (`start`).

![Overlong.exe - IDA - Entry Point](https://raw.githubusercontent.com/SecSuperN0va/CTF-Writeups/master/Flare-on/2019/01%20-%20Overlong/images/overlong_ida_start.png)

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



### Detailed Analysis
TODO
## Tools Used
TODO

Tool name|URL (if necessary)
:---|:---
IDA Pro | https://www.hex-rays.com/products/ida/