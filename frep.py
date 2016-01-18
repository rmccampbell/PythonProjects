import sys, argparse, getfiles, re

def frep(pattern, replace, *files, inplace=False, fixed=False):
    if inplace:
        mode = 'r+'
    else:
        mode = 'r'
        out = sys.stdout
    if fixed:
        pattern = re.escape(pattern)
    files = getfiles.getfiles(files, mode, default='-')

    try:
        for file in files:
            if inplace:
                lines = file.readlines()
                file.seek(0)
                file.truncate()
                out = file
            else:
                lines = file

            for line in lines:
                out.write(re.sub(pattern, replace, line))
    except ValueError:
        raise ValueError('cannot use inplace on stdin')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('pattern')
    p.add_argument('replace')
    p.add_argument('files', nargs='*')
    p.add_argument('-i', '--inplace', action='store_true')
    p.add_argument('-F', '--fixed', action='store_true')

    args = p.parse_args()
    try:
        frep(args.pattern, args.replace, *args.files, inplace=args.inplace,
             fixed=args.fixed)
    except Exception as e:
        getfiles.printerr('{}: {}', type(e).__name__, e)
