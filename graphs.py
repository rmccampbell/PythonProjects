import collections, heapq, math

def _func1(f, default=None):
    if default is not None and isinstance(f, dict):
        return lambda x: f.get(x, default)
    if hasattr(f, '__getitem__'):
        return f.__getitem__
    assert callable(f)
    return f

def _func2(f, default=None):
    if default is not None and isinstance(f, dict):
        return lambda x, y: f.get((x, y), default)
    if isinstance(f, collections.abc.Sequence):
        return lambda x, y: f[x][y]
    if hasattr(f, '__getitem__'):
        return lambda x, y: f[x, y]
    assert callable(f)
    return f


def get_path(s, t, pred):
    path = [t]
    while t != s:
        t = pred[t]
        path.append(t)
    return path[::-1]

def bfs_all(adj, s):
    adj = _func1(adj, ())
    q = collections.deque([s])
    d = {s: 0}
    pred = {s: None}
    while q:
        u = q.popleft()
        du = d[u]
        for v in adj(u):
            if v in pred:
                continue
            d[v] = du + 1
            pred[v] = u
            q.append(v)
    return d, pred

def bfs(adj, s, t):
    adj = _func1(adj, ())
    q = collections.deque([s])
    d = {s: 0}
    pred = {s: None}
    while q:
        u = q.popleft()
        du = d[u]
        for v in adj(u):
            if v in pred:
                continue
            d[v] = dv = du + 1
            pred[v] = u
            if v == t:
                return dv, get_path(s, t, pred)
            q.append(v)
    return None, None


def dijkstra_all(adj, w, s):
    adj = _func1(adj, ())
    w = _func2(w)
    q = [(0, s)]
    d = {s: 0}
    pred = {s: None}
    seen = set()
    while q:
        du, u = heapq.heappop(q)
        if u in seen:
            continue
        seen.add(u)
        for v in adj(u):
            if v in seen:
                continue
            dv = du + w(u, v)
            if dv < d.get(v, math.inf):
                d[v] = dv
                pred[v] = u
                heapq.heappush(q, (dv, v))
    return d, pred

def dijkstra(adj, w, s, t):
    adj = _func1(adj, ())
    w = _func2(w)
    q = [(0, s)]
    d = {s: 0}
    pred = {s: None}
    seen = set()
    while q:
        du, u = heapq.heappop(q)
        if u == t:
            return du, get_path(s, t, pred)
        if u in seen:
            continue
        seen.add(u)
        for v in adj(u):
            if v in seen:
                continue
            dv = du + w(u, v)
            if dv < d.get(v, math.inf):
                d[v] = dv
                pred[v] = u
                heapq.heappush(q, (dv, v))
    return None, None



def manhattan_dist(u, v):
    return sum(abs(ui-vi) for ui, vi in zip(u, v))

def euclidean_dist(u, v):
    return math.sqrt(sum((ui-vi)**2 for ui, vi in zip(u, v)))

def chebyshev_dist(u, v):
    return max(abs(ui-vi) for ui, vi in zip(u, v))

l1_dist = manhattan_dist
l2_dist = euclidean_dist
l_inf_dist = chebyshev_dist

def a_star(adj, w, s, t, h=manhattan_dist):
    adj = _func1(adj, ())
    w = _func2(w)
    f = {s: h(s, t)}
    g = {s: 0}
    q = [(f[s], g[s], s)]
    pred = {s: None}
    seen = set()
    while q:
        fu, gu, u = heapq.heappop(q)
        if u == t:
            return gu, get_path(s, t, pred)
        if u in seen:
            continue
        seen.add(u)
        for v in adj(u):
            if v in seen:
                continue
            gv = gu + w(u, v)
            if gv < g.get(v, math.inf):
                fv = gv + h(v, t)
                f[v] = fv
                g[v] = gv
                pred[v] = u
                heapq.heappush(q, (fv, gv, v))
    return None, None


def max_flow(adj, cap, s, t):
    adj = _func1(adj, ())
    cap = _func2(cap, default=0)
    maxf = 0
    flow = {}
    path = aug_path(adj, cap, flow, s, t)
    while path:
        cf = min(cap(u, v) - flow.get((u, v), 0) for u, v in path)
        maxf += cf
        for (u, v) in path:
            f = flow.get((u, v), 0) + cf
            flow[u, v] = f
            flow[v, u] = -f
        path = aug_path(adj, cap, flow, s, t)
    return maxf, flow

def aug_path(adj, cap, flow, s, t):
    q = collections.deque([s])
    pred = {s: None}
    while q:
        u = q.popleft()
        for v in adj(u):
            if v in pred or flow.get((u, v), 0) >= cap(u, v):
                continue
            pred[v] = u
            if v == t:
                return get_path_edges(s, t, pred)
            q.append(v)
    return None

def get_path_edges(s, t, pred):
    path = []
    v = t
    while v != s:
        u = pred[v]
        path.append((u, v))
        v = u
    return path[::-1]


def matrix_to_adj_fun(mat):
    return lambda v: [u for u, x in enumerate(mat[v]) if x]

def matrix_to_adj_list(mat):
    return [[u for u, x in enumerate(row) if x] for row in mat]

def edges_to_adj(edges, directed=True):
    adj = {}
    for u, v in edges:
        adj.setdefault(u, set()).add(v)
        if not directed:
            adj.setdefault(v, set()).add(u)
    return adj

def von_neumann_neighborhood(v=None, width=None, height=None):
    if v is None:
        return lambda v: von_neumann_neighborhood(v, width=width, height=height)
    x, y = v
    neighbors = [(x+1, y), (x, y+1), (x-1, y), (x, y-1)]
    return [(x2, y2) for x2, y2 in neighbors
            if (width is None or 0 <= x2 < width)
            and (height is None or 0 <= y2 < height)]

def moore_neighborhood(v=None, width=None, height=None):
    if v is None:
        return lambda v: moore_neighborhood(v, width=width, height=height)
    x, y = v
    neighbors = [(x+1, y), (x+1, y+1), (x, y+1), (x-1, y+1),
                 (x-1, y), (x-1, y-1), (x, y-1), (x+1, y-1)]
    return [(x2, y2) for x2, y2 in neighbors
            if (width is None or 0 <= x2 < width)
            and (height is None or 0 <= y2 < height)]

four_neighborhood = von_neumann_neighborhood
eight_neighborhood = moore_neighborhood
