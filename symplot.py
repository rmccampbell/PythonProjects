#!/usr/bin/env python3
import sys, sympy, re, argparse

def symplot(*exprs, xlim=(-10, 10), ylim=(-10, 10), implicit=False):
    x, y = sympy.symbols('x y')
    if implicit:
        if len(exprs) > 1:
            raise ValueError("can't plot multiple implicit equations")
        expr = exprs[0]
        if '=' in expr:
            expr = 'Eq({}, {})'.format(*re.split('==?', expr, 1))
        sympy.plot_implicit(sympy.sympify(expr), (x, *xlim), (y, *ylim))
    else:
        sympy.plot(*map(sympy.sympify, exprs), (x, *xlim))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('exprs', nargs='+')
    p.add_argument('-i', '--implicit', action='store_true')
    p.add_argument('-x', '--xlim', nargs=2, type=float, default=[-10, 10],
                   metavar=('XMIN', 'XMAX'))
    p.add_argument('-y', '--ylim', nargs=2, type=float, default=[-10, 10],
                   metavar=('YMIN', 'YMAX'))
    args = p.parse_args()
    try:
        symplot(*args.exprs, xlim=args.xlim, ylim=args.ylim, implicit=args.implicit)
    except Exception as e:
        sys.exit('error: {}'.format(e))
