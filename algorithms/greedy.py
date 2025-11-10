import random

def greedy_algorithm(adjazenz):
    U = list(adjazenz.keys())
    random.shuffle(U)
    vertices_colors = {}
    for vertice in U:
        neighbors = set()
        for neighbor in adjazenz[vertice]:
            if neighbor in vertices_colors:
                neighbors.add(neighbor)

        forbidden_colors = set()
        for i in neighbors:
            forbidden_colors.add(vertices_colors[i])

        smallest_color = None
        for u in range(len(forbidden_colors) + 1):
            if u in forbidden_colors:
                continue
            else:
                smallest_color = u
                break

        vertices_colors[vertice] = smallest_color

    def color_count(color_dict):
        highest_color = -1
        for node, color in color_dict.items():
            if color > highest_color:
                highest_color = color
        return highest_color

    return vertices_colors