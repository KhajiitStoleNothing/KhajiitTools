import os
import re
import argparse
import fileinput

parser = argparse.ArgumentParser()
parser.add_argument("-f","--file", type=str, help="load payload from text file")
parser.add_argument("-b","--binary", help="load payload from binary file",action="store_true")
parser.add_argument("-nt","--notrim",help="don't trim whitespaces and \"0x\" characters", action="store_true")
args = parser.parse_args()

print "[+] Here is your shellcode:\n" 
if args.file:
    if os.path.exists(args.file):
        if args.binary:
            print "\\x" + "\\x".join(re.findall("..",open(args.file,"rb").read().encode("hex")))
        else:
            if args.notrim:
                 print "\\x" + "\\x".join(re.findall("..",open(args.file,"r").read()))
            else:
                 print "\\x" + "\\x".join(re.findall("..",open(args.file,"rb").read().replace(" ","").replace("0x","")))
    else:
        print "[!] File doesn't exist. Check filename\n"
        os.exit()
else:
    for line in fileinput.input():
        print "\\x" + "\\x".join(re.findall("..",line.replace(" ","").replace("0x","")))


            
