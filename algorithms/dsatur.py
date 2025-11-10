def dsatur(adjazenz):

    V = list(adjazenz.keys())
    deg = {v: len(adjazenz[v]) for v in V}

    uncolored = set(V)
    color = {}

    nbr_colors = {v: set() for v in V}
    sat = {v: 0 for v in V}

    while uncolored:

        v = max(uncolored, key=lambda x: (sat[x], deg[x]))

        forbidden = nbr_colors[v]
        c = 0
        while c in forbidden:
            c += 1
        color[v] = c

        uncolored.remove(v)

        for u in adjazenz[v]:
            if u in uncolored:

                if c not in nbr_colors[u]:
                    nbr_colors[u].add(c)
                    sat[u] += 1

    def color_count(color_dict):
        highest_color = -1
        for node, color in color_dict.items():
            if color > highest_color:
                highest_color = color
        return highest_color

    return color