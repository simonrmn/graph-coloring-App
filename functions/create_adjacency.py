def create_adjazenz_list_per_constraint(datensatz, index_node, index_constraint):
    array = datensatz.to_numpy()
    edges = {}

    length = len(array)
    for i in range(length):
        for t in range(length):
            if t == i:
                continue
            elif array[t][index_constraint] == array[i][index_constraint]:
                if array[i][index_node] in edges:
                    edges[array[i][index_node]].append(array[t][index_node])
                else:
                    edges[array[i][index_node]] = []
                    edges[array[i][index_node]].append(array[t][index_node])

    return edges


def connect_all_constraints(*dicts):
    all_edges = {}

    for G in dicts:
        for n, e in G.items():
            if n not in all_edges:
                all_edges[n] = []

            for i in e:
                if i not in all_edges[n]:
                    all_edges[n].append(i)

    return all_edges