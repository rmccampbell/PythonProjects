#!/usr/bin/env python3
import sys, os, argparse, subprocess, shlex, shutil

def winsplit(s=None):
    lex = shlex.shlex(s, posix=True)
    lex.quotes = '"'
    lex.commenters = ''
    lex.escape = ''
    lex.whitespace_split = True
    return list(lex)

def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i : i+n]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs=argparse.REMAINDER)
    parser.add_argument('-a', '--arg-file', default='-')
    parser.add_argument('-d', '--delimiter', default='\n')
    parser.add_argument('-w', '--whitespace', dest='delimiter',
                        action='store_const', const=None)
    parser.add_argument('-N', '--newline', dest='delimiter',
                        action='store_const', const='\n', help='(default)')
    parser.add_argument('-0', '--null', dest='delimiter',
                        action='store_const', const='\x00')
    parser.add_argument('-I', '--replace')
    parser.add_argument('-i', dest='replace', action='store_const', const='{}')
    parser.add_argument('-S', '--shell', action='store_true')
    parser.add_argument('-L', '--max-lines', type=int)
    parser.add_argument('-l', dest='max_lines', action='store_const', const=1)
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

    if os.name == 'nt' and not args.shell:
        whichcmd = shutil.which(command[0])
        ext = os.path.splitext(whichcmd)[1].lower()
        if ext in ('.py', '.pyw'):
            command[:1] = [sys.executable, whichcmd]

    if args.max_lines:
        for subargs in chunk(xargs, args.max_lines):
            subprocess.call(command + subargs, shell=args.shell, stdin=stdin)
    else:
        subprocess.call(command + xargs, shell=args.shell, stdin=stdin)
