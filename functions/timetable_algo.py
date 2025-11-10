import numpy as np
from scipy.optimize import linear_sum_assignment
from math import ceil

def create_timetable(dataset, adjazenz, coloring_dict):
    ##############################################################################################
    #### Bevorzugte Zeiten als Dictionary
    def get_preferred_time(dataset):
        array = dataset.to_numpy()
        preferred_time = {}

        length = len(array)
        for i in range(length):
            preferred_time[array[i][0]] = array[i][5]

        return preferred_time

    ##############################################################################################
    #### Anzahl der Farben
    def get_number_of_colors(coloring_dict):
        k = len(set(coloring_dict.values()))
        return k

    ##############################################################################################
    #### Wochenbedarf bestimmen
    def get_weeks(k):
        W = ceil(k / 10)
        return W

    ##############################################################################################
    #### Farbklassen bilden
    def get_color_classes(coloring_dict):
        color_set = set(coloring_dict.values())
        color_classes = {}
        for i in color_set:
            for n in coloring_dict:
                if coloring_dict[n] == i:
                    if i in color_classes:
                        color_classes[i].append(n)
                    else:
                        color_classes[i] = []
                        color_classes[i].append(n)
        return color_classes

    ##############################################################################################
    #### Präferenzverteilung je Farbe berechnen
    def preferences_per_color(color_classes, dataset):
        #### neues verschachteltes dictionary erstellen
        preferences_per_color = {}
        #### Für jede Farbklasse die Anzahl der Präferenzen berechnen und in preferences_per_color einfügen
        for l in color_classes:
            morning_count = 0
            afternoon_count = 0
            for n in color_classes[l]:
                index = dataset.index[dataset["course_id"] == n][0]
                if dataset.loc[index, "preferred_time"] == "Morning":
                    morning_count = morning_count + 1
                elif dataset.loc[index, "preferred_time"] == "Afternoon":
                    afternoon_count = afternoon_count + 1
            preferences_per_color[l] = {"m": morning_count, "a": afternoon_count}
        return preferences_per_color

    ##############################################################################################
    #### Zeitslots erstellen
    def making_time_slots(W):
        days = ["Mo", "Di", "Mi", "Do", "Fr"]
        halves = ["Morning", "Afternoon"]
        slots = [(w, d, h) for w in range(1, W + 1) for d in days for h in halves]
        return slots

    ##############################################################################################
    #### Kostenmatrix erstellen
    def create_cost_matrix(preferences_per_color, slots, colors):
        k = len(colors)
        M = np.zeros((k, len(slots)))

        for row_idx, color in enumerate(colors):
            pref = preferences_per_color[color]
            for col_idx, slot in enumerate(slots):
                half = slot[2]
                if half in ("Morning", "m"):
                    M[row_idx, col_idx] = pref["a"]
                else:
                    M[row_idx, col_idx] = pref["m"]
        return M

    ##############################################################################################
    #### Kostenmatrix minimieren.
    def min_cost_matrix(M):
        M = np.asarray(M)
        rows, cols = linear_sum_assignment(M)
        total_cost = M[rows, cols].sum()

        return rows, cols, float(total_cost)

    ##############################################################################################
    #### Farben den slots zuweisen und Kosten des Algorithmus berechnen
    def map_colors_and_calculate_costs(rows, cols, total_costs, adjazenz, coloring_dict, dataset, slots, colors):
        #### Farbe Slot zuweisen
        color_to_slot = {}
        for r, c in zip(rows, cols):
            color = colors[int(r)]
            slot = slots[int(c)]
            color_to_slot[color] = slot

        #### Kurs Slot zuweisen
        course_to_slot = {}
        for course_id, color in coloring_dict.items():
            course_to_slot[course_id] = color_to_slot[color]

        #### Präferenz-Lookup
        preferred = dict(zip(dataset["course_id"], dataset["preferred_time"]))

        #### Präferenzen zählen
        def half_matches(half, pref):
            if pref is None:
                return False
            if half == "Morning":
                return pref == "Morning"
            if half == "Afternoon":
                return pref == "Afternoon"
            return False

        fulfilled_preferences = 0
        for course_id, slot in course_to_slot.items():
            if half_matches(slot[2], preferred.get(course_id)):
                fulfilled_preferences += 1

        all_courses = len(coloring_dict)
        score = fulfilled_preferences / all_courses if all_courses else 0.0

        return color_to_slot, course_to_slot, score, fulfilled_preferences, all_courses, total_costs

    k = get_number_of_colors(coloring_dict)
    W = get_weeks(k)
    slots = making_time_slots(W)

    color_classes = get_color_classes(coloring_dict)
    pref_per_color = preferences_per_color(color_classes, dataset)

    colors = sorted(set(coloring_dict.values()))

    M = create_cost_matrix(pref_per_color, slots, colors)
    rows, cols, total_costs = min_cost_matrix(M)

    color_to_slot, course_to_slot, score, satisfied, total, assignment_cost = \
        map_colors_and_calculate_costs(rows, cols, total_costs, adjazenz, coloring_dict, dataset, slots, colors)

    return {
        "k": k,
        "weeks": W,
        "slots": slots,
        "colors": colors,
        "cost_matrix": M,
        "assignment_rows": rows,
        "assignment_cols": cols,
        "assignment_cost": assignment_cost,
        "color_to_slot": color_to_slot,
        "course_to_slot": course_to_slot,
        "satisfied": satisfied,
        "total": total,
        "satisfaction": score
    }