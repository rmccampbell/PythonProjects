#!/usr/bin/env python3
import sys, pygame, math, re, argparse
from pygame.locals import *

__all__ = ['Grapher', 'main', 'preprocess', 'test_equality']

DISPLAY = (500, 500)
WINDOW = (50, 50, 400, 400)
BOUNDS = (-10, -10, 20, 20)

BGCOLOR = (255, 255, 255)
AXISCOLOR = (0, 0, 0)
COLOR = (0, 0, 255)

TURNS = 5
TMAX = 10 * math.pi
RES = 100
POL_RES = 8000
PAR_RES = 1000
IMP_RES = 1

def preprocess(expr):
    # fix exponents
    parsed = expr.replace('^', '**')

    # fix multiplication:
    # a closing parenthesis followed by an identifier, number, or parenthesis
    parsed = re.sub(r'([)])(?=[(]|\w)', r'\1*', parsed)
    # a number followed by an identifier or parenthesis, but not
    # exponent or imaginary notation
    parsed = re.sub(r'(\b\d+\.?(?:[Ee][+-]?\d+)?)' +
                    r'(?=[A-Za-z_]|\s*[(])(?![Ee][+-]?\d|j\b)',
		    r'\1*', parsed)
    return parsed

def test_equality(a, b, eps1=.003, eps2=.04):
    return abs(a-b) <= eps1 * (abs(a) + abs(b)) + eps2

def split_parametric(expr1, expr2):
    xexpr, yexpr, expr3 = None, None, None
    for expr in expr1, expr2:
        try:
            var, expr = map(str.strip, expr.split('=', 1))
            if var == 'x':
                xexpr = expr
            elif var == 'y':
                yexpr = expr
            else:
                raise Exception(
                    "parameric equations not in correct format.")
        except ValueError:
            if expr3 is None:
                expr3 = expr
            elif yexpr is None:
                yexpr = expr
            else:
                xexpr = expr
    if xexpr is None:
        xexpr = expr3
    elif yexpr is None:
        yexpr = expr3

    if xexpr is None or yexpr is None:
        raise Exception("parametric must have an x and a y equation")

    return xexpr, yexpr

def get_real(n):
    try:
        if not n.imag or abs(n.imag) < 1e-9:
            return n.real
        raise ValueError
    except (AttributeError, TypeError):
        raise TypeError('value is not a number.')

def get_color(o):
    if isinstance(o, pygame.Color):
        return o
    if isinstance(o, (tuple, list)):
        return pygame.Color(*o)
    return pygame.Color(o)


class ClosedError(Exception):
    pass

class Grapher:
    def __init__(self,
                 displaysize=DISPLAY, window=WINDOW, bounds=BOUNDS,
                 bgcolor=BGCOLOR, axiscolor=AXISCOLOR, color=COLOR,
                 turns=TURNS, tmax=TMAX, res=RES, pol_res=POL_RES,
                 par_res=PAR_RES, imp_res=IMP_RES):
        self.init(displaysize, window, bounds, bgcolor, axiscolor, color,
                  turns, tmax, res, pol_res, par_res, imp_res)
    def init(self,
             displaysize=DISPLAY, window=WINDOW, bounds=BOUNDS,
             bgcolor=BGCOLOR, axiscolor=AXISCOLOR, color=COLOR,
             turns=TURNS, tmax=TMAX, res=RES, pol_res=POL_RES,
             par_res=PAR_RES, imp_res=IMP_RES):
        pygame.init()
        self.screen = pygame.display.set_mode(displaysize)
        self.window = pygame.Rect(window) or pygame.Rect((0, 0), displaysize)
        self.surface = self.screen.subsurface(self.window)
        self.bounds = pygame.Rect(bounds)

        self.bgcolor = bgcolor = get_color(bgcolor)
        self.axiscolor = axiscolor = get_color(axiscolor)
        self.color = color = get_color(color)

        self.turns = turns
        self.tmax = tmax
        self.res = res
        self.pol_res = pol_res
        self.par_res = par_res
        self.imp_res = imp_res

        self.closed = False
        self.clear()

        self.ns = {}
        self.ns.update({name: value for name, value in vars(math).items()
                       if name[0] != '_'})
        self.ns['graph'] = self
        self.ns['Color'] = pygame.Color
        self.ns['Rect'] = pygame.Rect
        self.ns['config'] = self.config
        self.ns['bounds'] = lambda x, y, w, h: self.config(bounds=(x, y, w, h))
        self.ns['color'] = lambda color: self.config(color=color)
        self.ns.update(DISPLAY=DISPLAY, WINDOW=WINDOW, BOUNDS=BOUNDS,
                       COLOR=COLOR, BGCOLOR=BGCOLOR, AXISCOLOR=AXISCOLOR,
                       TURNS=TURNS, TMAX=TMAX, RES=RES, POL_RES=POL_RES,
                       PAR_RES=PAR_RES, IMP_RES=IMP_RES)

        self.running = False

    def main(self, *equations):
        if self.closed:
            raise ClosedError('Graph has been closed.')
        try:
            self.running = True

            if equations:
                for equation in equations:
                    self.graph(equation)
            else:
                self.get_graph()

            while self.running:
                # check user input
                for e in pygame.event.get():
                    if e.type == KEYDOWN:
                        if (e.key == K_ESCAPE or
                            e.key == K_F4 and e.mod & KMOD_ALT):
                            # quit
                            self.running = False
                        elif e.key == K_r:
                            # reset graph
                            self.clear()
                            self.get_graph()
                        elif e.key == K_RETURN:
                            # add another graph
                            self.get_graph()
                    elif e.type == QUIT:
                        #quit
                        self.running = False
        finally:
            self.close()

    def graph(self, eq, implicit=False, **kwargs):
        if self.closed:
            raise ClosedError('Graph has been closed.')

        turns = kwargs.get('turns', self.turns)
        tmax = kwargs.get('tmax', self.tmax)
        res = kwargs.get('res', self.res)
        pol_res = kwargs.get('pol_res', self.pol_res)
        par_res = kwargs.get('par_res', self.par_res)
        imp_res = kwargs.get('imp_res', self.imp_res)

        # preprocess equation
        eq = preprocess(eq)

        # handle parametric functions
        try:
            expr1, expr2 = map(str.strip, eq.split(';', 1))
        except ValueError:
            pass
        else:
            xexpr, yexpr = split_parametric(expr1, expr2)
            return self.graph_parametric(xexpr, yexpr, tmax, par_res)

        # handle non-parametric
        try:
            left, right = map(str.strip, re.split(r'==?', eq, 1))
        except ValueError:
            right = eq.strip()
            if 'theta' in right:
                left = 'r'
            else:
                left = 'y'

        if left == 'r':
             return self.graph_polar(right, turns, pol_res)

        # equations not in "y=" form are automatically implicit
        elif implicit or left != 'y':
            return self.graph_implicit(left, right, imp_res)

        else:
            return self.graph_function(right, res)

    def graph_function(self, expr, res=RES):
        code = compile(expr, '<string>', 'eval')
        #pixels = pygame.surfarray.pixels3d(self.surface)
        wx, wy, ww, wh = self.window
        bx, by, bw, bh = self.bounds

        # total graph resolution is res * self.window.w
        for i in range(int(res * ww)):
            # get pixel x and coordinate x
            px = i / res
            x = (px * bw / ww) + bx
            self.ns.update(x=x, t=x, n=x)

            # get y value(s)
            ys = []
            try:
                val = eval(code, self.ns)
            except (ArithmeticError, ValueError):
                pass
            else:
                try:
                    ys = [get_real(val)]
                except ValueError:
                    pass
                except TypeError as e:
                    try:
                        ys = map(get_real, val)
                    except TypeError:
                        raise e

            for y in ys:
                # convert coordinate y to pixel y
                py = wh - (y - by) * wh / bh
                # plot point
                if 0 <= py < wh:
                    self.surface.set_at((int(px), int(py)), self.color)
                    #pixels[px, py] = self.color[:3]
                    #pygame.display.update((wx + px, wy + py, 1, 1))
                    if i % 100 == 0:
                        pygame.display.flip()

            # check user input
            if self.check_events():
                break

        del self.ns['x'], self.ns['t'], self.ns['n']
        pygame.display.flip()

    def graph_polar(self, expr, turns=TURNS, res=POL_RES):
        code = compile(expr, '<string>', 'eval')
        wx, wy, ww, wh = self.window
        bx, by, bw, bh = self.bounds

        for i in range(int(turns * res)):
            # get angle
            theta = i * 2 * math.pi / res
            self.ns['theta'] = theta

            # get radius
            try:
                r = get_real(eval(code, self.ns))
            except (ArithmeticError, ValueError):
                pass

            else:
                # convert to rectangular coordinates
                x, y = r * math.cos(theta), r * math.sin(theta)
                # convert x and y coordinates to pixel values
                px =      (x - bx) * ww / bw
                py = wh - (y - by) * wh / bh
                if 0 <= px < ww and 0 <= py < wh:
                    self.surface.set_at((int(px), int(py)), self.color)
                    if i % 100 == 0:
                        pygame.display.flip()
                    #pygame.display.update((wx + px, wy + py, 1, 1))

            # check user input
            if self.check_events():
                break

        del self.ns['theta']
        pygame.display.flip()

    def graph_parametric(self, xexpr, yexpr, tmax=TMAX, tres=PAR_RES):
        xcode = compile(xexpr, '<string>', 'eval')
        ycode = compile(yexpr, '<string>', 'eval')
        wx, wy, ww, wh = self.window
        bx, by, bw, bh = self.bounds

        for i in range(int(tres*tmax)):
            t = i / tres
            self.ns['t'] = t

            # get x and y values
            try:
                x = get_real(eval(xcode, self.ns))
                y = get_real(eval(ycode, self.ns))
            except (ArithmeticError, ValueError):
                pass

            else:
                # convert x and y coordinates to pixel values
                px =      (x - bx) * ww / bw
                py = wh - (y - by) * wh / bh
                if 0 <= px < ww and 0 <= py < wh:
                    self.surface.set_at((int(px), int(py)), self.color)
                    if i % 100 == 0:
                        pygame.display.flip()
                    #pygame.display.update((wx + px, wy + py, 1, 1))

            # check user input
            if self.check_events():
                break

        del self.ns['t']
        pygame.display.flip()

    def graph_implicit(self, left, right, res=IMP_RES):
        # compile expressions into code
        leftc = compile(left, '<string>', 'eval')
        rightc = compile(right, '<string>', 'eval')

        wx, wy, ww, wh = self.window
        bx, by, bw, bh = self.bounds
        stop = False

        for i in range(int(ww * res)):
            for j in range(int(wh * res)):
                px, py = i / res, j / res
                # get coordinate values from pixel values
                x, y = (px * bw / ww) + bx, -(py * bh / wh) - by
                self.ns.update(x=x, y=y)

                # get exprssion values
                try:
                    leftval = get_real(eval(leftc, self.ns))
                    rightval = get_real(eval(rightc, self.ns))
                except (ArithmeticError, ValueError):
                    pass

                else:
                    # test equality and plot point
                    if test_equality(leftval, rightval):
                                     #eps1=0.003/res,
                                     #eps2=0.04/res):
                        self.surface.set_at((int(px), int(py)), self.color)
                        pygame.display.update((wx + px, wy + py, 1, 1))

                # check user input
                stop = self.check_events()

                if stop: break
            if stop: break

        del self.ns['x'], self.ns['y']
        pygame.display.flip()

    def get_graph(self, **kwargs):
        eq = ''
        while not eq:
            try:
                eq = input('Equation: ')
            except EOFError:
                return

        if eq.startswith('@'):
            try:
                c = compile(eq[1:].strip() + '\n', '<string>', 'single')
                exec(c, self.ns)
            except Exception as e:
                print('{}: {}\n'.format(type(e).__name__, e), file=sys.stderr)
            self.get_graph(**kwargs)
            return

        try:
            self.graph(eq, **kwargs)
        except ClosedError:
            raise
        except Exception as e:
            print('{}: {}\n'.format(type(e).__name__, e), file=sys.stderr)
            self.get_graph(**kwargs)

    def config(self, bounds=None, display=None, window=None,
               color=None, bgcolor=None, axiscolor=None,
               turns=None, tmax=None,
               res=None, pol_res=None, par_res=None, imp_res=None):
        if display:
            self.screen = pygame.display.set_mode(display)
            self.window = self.window.clip(pygame.Rect((0,0), display))
            self.surface = self.screen.subsurface(self.window)
        if window is not None:
            self.window = pygame.Rect(window).clip(self.screen.get_rect()) or \
                          pygame.Rect(self.screen.get_rect())
            self.surface = self.screen.subsurface(self.window)
        if bounds:
            self.bounds = pygame.Rect(bounds)

        if color:
            self.color = get_color(color)
        if bgcolor:
            self.bgcolor = get_color(bgcolor)
        if axiscolor:
            self.axiscolor = get_color(axiscolor)

        if turns:
            self.turns = turns
        if tmax:
            self.tmax = tmax
        if res:
            self.res = res
        if pol_res:
            self.pol_res = pol_res
        if par_res:
            self.par_res = par_res
        if imp_res:
            self.imp_res = imp_res

        if display or window is not None or bounds:
            self.clear()

    def clear(self):
        if self.closed:
            raise ClosedError('Graph has been closed.')

        self.screen.fill(self.bgcolor)

        window, bounds = self.window, self.bounds
        # axis pixel positions
        xaxis_p = -bounds.x * window.w / bounds.w
        yaxis_p = window.h + bounds.y * window.h / bounds.h

        pygame.draw.rect(self.screen, self.axiscolor, window.inflate(2, 2), 1)
        pygame.draw.line(self.surface, self.axiscolor,
                         (xaxis_p, 0), (xaxis_p, window.h), 2)
        pygame.draw.line(self.surface, self.axiscolor,
                         (0, yaxis_p), (window.w, yaxis_p), 2)

        xpow = max(int(math.log10(bounds.w) - .7), 0)
        xstep = 10**xpow
        for x in range(bounds.left, bounds.right+1, xstep):
            px = (x - bounds.x) * window.w / bounds.w
            pygame.draw.line(self.surface, self.axiscolor,
                             (px, yaxis_p), (px, yaxis_p-5), 2)

        ypow = max(int(math.log10(bounds.h) - .7), 0)
        ystep = 10**ypow
        for y in range(bounds.top, bounds.bottom+1, ystep):
            py = window.h - (y - bounds.y) * window.h / bounds.h
            pygame.draw.line(self.surface, self.axiscolor,
                             (xaxis_p, py), (xaxis_p+5, py), 2)

        pygame.display.flip()
        pygame.event.pump()

    def check_events(self):
        # true return value tells graph function to quit
        stop = False
        for e in pygame.event.get():
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    stop = True
                elif e.key == K_F4 and e.mod & KMOD_ALT:
                    stop = True
                    self.running = False
            elif e.type == QUIT:
                stop = True
                self.running = False
        return stop

    def close(self):
        if not self.closed:
            self.surface = None
            if self.screen is pygame.display.get_surface():
                pygame.quit()
            self.closed = True

##    def __del__(self):
##        if not self.closed:
##            self.close()

def main(*equations, **kwargs):
    Grapher(**kwargs).main(*equations)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('equations', nargs='*')
    p.add_argument('-d', '--display', metavar=('W','H'), nargs=2, type=int,
                   default=DISPLAY)
    p.add_argument('-w', '--window', metavar=('X','Y','W','H'), nargs=4,
                   type=int, default=WINDOW)
    p.add_argument('-b', '--bounds', metavar=('X','Y','W','H'), nargs=4,
                   type=int, default=BOUNDS)
    p.add_argument('--color', nargs=3, metavar=('R','G','B'), type=int,
                   default=COLOR)
    p.add_argument('--bgcolor', nargs=3, metavar=('R','G','B'), type=int,
                   default=BGCOLOR)
    p.add_argument('--axiscolor', nargs=3, metavar=('R','G','B'), type=int,
                   default=AXISCOLOR)
    p.add_argument('--turns', type=float, default=TURNS)
    p.add_argument('--tmax', type=float, default=TMAX)
    p.add_argument('--res', type=float, default=RES)
    p.add_argument('--pol-res', type=float, default=POL_RES)
    p.add_argument('--par-res', type=float, default=PAR_RES)
    p.add_argument('--imp-res', type=float, default=IMP_RES)
    args = p.parse_args()

    try:
        main(*args.equations, displaysize=args.display,
             window=args.window, bounds=args.bounds,
             bgcolor=args.bgcolor, axiscolor=args.axiscolor, color=args.color,
             turns=args.turns, tmax=args.tmax,
             res=args.res, pol_res=args.pol_res, par_res=args.par_res,
             imp_res=args.imp_res)
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
