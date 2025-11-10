def backtracking_coloring(adjazenz):
    vertices = list(adjazenz.keys())
    n = len(vertices)
    if n == 0:
        return {}
    order = {v: i for i, v in enumerate(vertices)}
    deg = {v: len(adjazenz[v]) for v in vertices}

    def greedy_dsatur_upper_bound():
        uncolored = set(vertices)
        color = {}
        nbr_colors = {v: set() for v in vertices}
        sat = {v: 0 for v in vertices}
        while uncolored:
            v = max(uncolored, key=lambda x: (sat[x], deg[x], -order[x]))
            c = 0
            while c in nbr_colors[v]:
                c += 1
            color[v] = c
            uncolored.remove(v)
            for u in adjazenz[v]:
                if u in uncolored and c not in nbr_colors[u]:
                    nbr_colors[u].add(c)
                    sat[u] += 1
        return 1 + max(color.values()) if color else 0

    best_assign = None
    best_k = greedy_dsatur_upper_bound() or 1
    assigned = {}
    used_colors = 0
    nbr_colors = {v: set() for v in vertices}
    sat = {v: 0 for v in vertices}
    uncolored = set(vertices)

    def select_vertex():
        return max(uncolored, key=lambda x: (sat[x], deg[x], -order[x]))

    def can_use_color(v, c):
        for u in adjazenz[v]:
            if assigned.get(u) == c:
                return False
        return True

    def dfs():
        nonlocal best_assign, best_k, used_colors
        if not uncolored:
            k = 0 if not assigned else 1 + max(assigned.values())
            if k < best_k:
                best_k = k
                best_assign = assigned.copy()
            return
        if used_colors >= best_k:
            return
        v = select_vertex()
        uncolored.remove(v)
        max_try = min(used_colors, best_k - 1)
        for c in range(max_try):
            if can_use_color(v, c):
                assigned[v] = c
                changed = []
                for u in adjazenz[v]:
                    if u in uncolored and c not in nbr_colors[u]:
                        nbr_colors[u].add(c);
                        sat[u] += 1;
                        changed.append(u)
                dfs()
                for u in changed:
                    nbr_colors[u].remove(c);
                    sat[u] -= 1
                del assigned[v]
        if used_colors + 1 < best_k:
            cnew = used_colors
            if can_use_color(v, cnew):
                assigned[v] = cnew
                prev_used = used_colors
                used_colors += 1
                changed = []
                for u in adjazenz[v]:
                    if u in uncolored and cnew not in nbr_colors[u]:
                        nbr_colors[u].add(cnew);
                        sat[u] += 1;
                        changed.append(u)
                dfs()
                for u in changed:
                    nbr_colors[u].remove(cnew);
                    sat[u] -= 1
                used_colors = prev_used
                del assigned[v]
        uncolored.add(v)

    dfs()
    return best_assign if best_assign is not None else {}