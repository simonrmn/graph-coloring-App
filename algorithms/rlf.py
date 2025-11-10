def rlf_algorithm(adjazenz):
    adjazenz = {v: (set(nbs) if not isinstance(nbs, set) else nbs)
                for v, nbs in adjazenz.items()}

    U = set(adjazenz.keys())
    current_color = 0
    color = {}

    while len(U) > 0:
        F = set()
        W = set()

        start = max(U, key=lambda k: len(adjazenz[k] & U))
        W.add(start)

        F |= (adjazenz[start] & U)

        while True:
            possible_vertices = U - W - F
            if not possible_vertices:
                break

            optimal_vertice = None
            most_neighbors = -1
            highest_degree = -1
            for vertice in possible_vertices:
                neighbors = len(adjazenz[vertice] & F)
                degree = len(adjazenz[vertice] & possible_vertices)

                if (neighbors > most_neighbors or
                        (neighbors == most_neighbors and degree > highest_degree) or
                        (neighbors == most_neighbors and degree == highest_degree and (
                                optimal_vertice is None or vertice < optimal_vertice))):
                    optimal_vertice = vertice
                    most_neighbors = neighbors
                    highest_degree = degree

            W.add(optimal_vertice)

            F |= (adjazenz[optimal_vertice] & U)

        for vertice in W:
            color[vertice] = current_color
        current_color = current_color + 1
        U = U - W

    def color_count(color_dict):
        highest_color = -1
        for node, color in color_dict.items():
            if color > highest_color:
                highest_color = color
        return highest_color

    return color