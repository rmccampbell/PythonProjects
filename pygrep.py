#!/usr/bin/env python3
import sys, re, argparse, collections, getfiles

DEF_KWARGS = {
    'match_files': False,
    'no_match_files': False,
    'only_match': False,
    'fixed': False,
    'invert': False,
    'ignore_case': False,
    'line': False,
    'word': False,
    'line_number': False,
    'with_filename': False,
    'count': False,
    'before_context': None,
    'after_context': None,
    'context': 0,
}

def grep(pattern, *files, **kwargs):
    if isinstance(pattern, argparse.Namespace):
        args = pattern
        pattern = args.pattern
        files = args.files
    else:
        kwargs2 = DEF_KWARGS.copy()
        kwargs2.update(kwargs)
        args = argparse.Namespace(pattern=pattern, files=files, **kwargs2)

    files = getfiles.getfiles(files)
    flags = args.ignore_case and re.IGNORECASE

    if args.fixed:
        pattern = re.escape(pattern)
    if args.line:
        pattern = r'^' + pattern + r'$'
    if args.word:
        pattern = r'\b' + pattern + r'\b'

    pattern = re.compile(pattern, flags)

    before = after = args.context
    if args.before_context is not None:
        before = args.before_context
    if args.after_context is not None:
        after = args.after_context
    before_buff = collections.deque(maxlen=before)

    if args.match_files or args.no_match_files:
        args.count, args.with_filename = False, False

    stdout = getfiles.set_encoding()

    for file in files:
        if args.count:
            count = 0

        print_filename = args.with_filename
        before_buff.clear()
        after_limit = 0

        for lno, line in enumerate(file):
            match = pattern.search(line)
            if args.only_match:
                matches = pattern.finditer(line)
            if (match and not args.invert) or (not match and args.invert):
                if args.match_files:
                    print(file.name)
                    break
                if args.no_match_files:
                    break

                if print_filename:
                    print('\n-- {} --'.format(file.name))
                    print_filename = False

                if args.count:
                    count += 1
                    continue

                print(''.join(before_buff), end='')
                before_buff.clear()

                prefix = '{:3}:'.format(lno) if args.line_number else ''

                if args.only_match:
                    print('\n'.join(prefix + m.group() for m in matches))
                else:
                    print(prefix + line, end='')

                after_limit = after

            elif after_limit:
                if args.line_number:
                    line = '{:3}-{}'.format(lno, line)
                print(line, end='')
                after_limit -= 1

            else:
                if args.line_number:
                    line = '{:3}-{}'.format(lno, line)
                before_buff.append(line)

        else:
            if args.no_match_files: print(file.name)

        if args.count:
            print(count)

    getfiles.reset_encoding(stdout)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pattern')
    parser.add_argument('files', nargs='*')
    parser.add_argument('-l', '--match-files', action='store_true')
    parser.add_argument('-L', '--no-match-files', action='store_true')
    parser.add_argument('-o', '--only-match', action='store_true')
    parser.add_argument('-F', '--fixed', action='store_true')
    parser.add_argument('-v', '--invert', action='store_true')
    parser.add_argument('-i', '--ignore-case', action='store_true')
    parser.add_argument('-x', '--line', action='store_true')
    parser.add_argument('-w', '--word', action='store_true')
    parser.add_argument('-n', '--line-number', action='store_true')
    parser.add_argument('-H', '--with-filename', action='store_true')
    parser.add_argument('-c', '--count', action='store_true')
    parser.add_argument('-B', '--before-context', type=int)
    parser.add_argument('-A', '--after-context', type=int)
    parser.add_argument('-C', '--context', type=int, default=0)
    args = parser.parse_args()
    grep(args)
