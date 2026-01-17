#!/usr/bin/env python3

import sys, argparse, collections, itertools

def is_num_option(s):
    return s.startswith('-') and s[1:].isdigit()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('n_or_files', nargs='*', metavar=('[-NUM]', 'FILE'))
    p.add_argument('-n', '--lines', metavar='NUM', type=int, default=10)
    p.add_argument('-d', '--delimiter', default='--')
    args = p.parse_args()

    if args.n_or_files and is_num_option(args.n_or_files[0]):
        lines = -int(args.n_or_files[0])
        files = args.n_or_files[1:]
    else:
        lines = args.lines
        files = args.n_or_files
    files = files or ['-']
    print_filenames = len(files) > 1
    if args.delimiter and not args.delimiter.endswith('\n'):
        args.delimiter += '\n'

    for filename in files:
        file = open(filename) if filename != '-' else sys.stdin
        if print_filenames:
            sys.stdout.write(f'==> {file.name} <==\n')
        sys.stdout.writelines(itertools.islice(file, lines))
        tail_lines = collections.deque(file, maxlen=lines + 1)
        if len(tail_lines) == lines + 1:
            if args.delimiter:
                sys.stdout.write(args.delimiter)
            tail_lines.popleft()
        sys.stdout.writelines(tail_lines)

if __name__ == '__main__':
    main()
