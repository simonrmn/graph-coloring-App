def get_edges(adj):
    edges = set()
    for u, nbrs in adj.items():
        for v in nbrs:
            if v == u:
                continue
            edges.add(tuple(sorted((u, v))))
    return len(edges)

def get_highest_degree(adj):
    hd = 0
    for i in adj.keys():
        if len(adj[i]) > hd:
            hd = len(adj[i])
    return hd

def get_density(adj):
    E = get_edges(adj)
    V = len(adj.keys())
    density = (2 * E) / (V * (V - 1))
    return density