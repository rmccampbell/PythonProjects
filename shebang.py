#!/usr/bin/env python3
import sys, os, re, argparse, glob

pattern = re.compile(r'(#!.*python)(\d(?:\.\d){,2})?')

def shebang(fname, num='', text=None, add=False, change=False, remove=False,
            altext=False, silent=False, directory=False):
    """Change, add, or remove a shebang line of a python script."""
    if not (altext or fname.endswith(('.py', '.pyw'))):
        if not (silent or directory):
            print("File '{}' doesn't end with .py or .pyw.".format(fname),
                  file=sys.stderr)
        return

    if not isinstance(num, str):
        if num is None:
            num = ''
        else:
            try:
                num = '.'.join(map(str, num))
            except TypeError:
                num = str(num)
    shebang_text = (text or '#!/usr/bin/env python' + num) + '\n'

    mode = 'r+' if add or change or remove else 'r'
    with open(fname, mode) as file:
        firstline, rest = file.readline(), file.read()
        if pattern.match(firstline):
            if remove:
                newcode = rest
            elif change:
                if text:
                    newline = shebang_text
                else:
                    newline = pattern.sub(r'\g<1>' + num, firstline)
                newcode = newline + rest
            else:
                if not silent:
                    print('Shebang already in file:', fname, file=sys.stderr)
                    print(firstline, end='', file=sys.stderr)
                return
        else:
            if add and not remove:
                newcode = shebang_text + firstline + rest
            else:
                if not silent:
                    print('No shebang found in file:', fname, file=sys.stderr)
                return
        file.seek(0)
        file.truncate()
        file.write(newcode)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num',
                        help='Python version number (Default is empty).')
    parser.add_argument('-t', '--text', help='Custom shebang text.')
    parser.add_argument('-a', '--add', action='store_true',
                        help='Insert shebang line if not present.')
    parser.add_argument('-c', '--change', action='store_true',
                        help='Change shebang line if present.')
    parser.add_argument('-r', '--remove', action='store_true',
                        help='Remove shebang line if present.')
    parser.add_argument('-x', '--altext', action='store_true',
                        help='Allow alternate file extensions.')
    parser.add_argument('-d', '--directory', action='store_true',
                        help='Walk directories recursively.')
    parser.add_argument('-s', '--silent', action='store_true',
                        help='Don\'t show status messages.')
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    for file in args.files:
        files = glob.glob(file)
        if not files: print("'{}' does not match any files.".format(file),
                            file=sys.stderr)
        for file in files:
            if os.path.isdir(file):
                if args.directory:
                    for root, dirs, files in os.walk(file):
                        for file in files:
                            file = os.path.join(root, file)
                            shebang(file, args.num, args.text, args.add,
                                    args.change, args.remove, args.altext,
                                    args.silent, True)
                else:
                    if not args.silent:
                        print("'{}' is a directory.".format(file),
                              file=sys.stderr)
            else:
                shebang(file, args.num, args.text, args.add, args.change,
                        args.remove, args.altext, args.silent)
