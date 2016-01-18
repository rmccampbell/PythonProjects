#!/usr/bin/env python3
import sys, argparse, subprocess, shlex

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
    args = parser.parse_args()

    command = args.command or ['echo']
    if args.arg_file == '-':
        file = sys.stdin
        stdin = subprocess.DEVNULL
    else:
        file = open(args.arg_file)
        stdin = None

    delim = args.delimiter
    if delim:
        xargs = file.read().splitlines()
        if delim != '\n':
            xargs = ' '.join(lines).split(delim)
    else:
        xargs = winsplit(file)

    subprocess.call(command + xargs, shell=True, stdin=stdin)
