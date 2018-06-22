#!/usr/bin/env python3
import sys, os, argparse, subprocess, shlex

def winsplit(s=None):
    lex = shlex.shlex(s, posix=True)
    lex.quotes = '"'
    lex.commenters = ''
    lex.escape = ''
    lex.whitespace_split = True
    return list(lex)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs=argparse.REMAINDER)
    parser.add_argument('-a', '--arg-file', default='-')
    parser.add_argument('-d', '--delimiter')
    parser.add_argument('-N', '--newline', dest='delimiter',
                        action='store_const', const='\n')
    parser.add_argument('-0', '--null', dest='delimiter',
                        action='store_const', const='\0')
    parser.add_argument('-I', '--replace')
    args = parser.parse_args()

    command = args.command or ['echo']
    if args.arg_file == '-':
        file = sys.stdin
        stdin = subprocess.DEVNULL
    else:
        file = open(args.arg_file)
        stdin = None

    delim = args.delimiter
    if delim == '\n':
        xargs = file.read().splitlines()
    elif delim:
        xargs = file.read().split(delim)
    elif os.name == 'nt':
        xargs = winsplit(file)
    else:
        xargs = shlex.split(file)

    if args.replace:
        while xargs and args.replace in command:
            command[command.index(args.replace)] = xargs.pop(0)

    shell = os.name == 'nt' # Pass command to shell on windows
    subprocess.call(command + xargs, shell=shell, stdin=stdin)
