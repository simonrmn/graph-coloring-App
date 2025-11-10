import numpy as np
#from scipy.optimize import linear_sum_assignment
from math import ceil
from math import inf

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
    #### Hungarian-Algorithmus
    def linear_sum_assignment(cost_matrix):
        """
        Rein-Python-Version des Hungarian-Algorithmus.
        Kompatible Rückgabe zu scipy.optimize.linear_sum_assignment:
        -> (row_ind, col_ind) als Listen von Indizes.

        - cost_matrix: 2D list/ndarray (>=0 empfohlen), rechteckig erlaubt.
        """
        # -- in ndarray konvertieren
        C = np.asarray(cost_matrix, dtype=float)
        if C.size == 0:
            return [], []

        n_rows, n_cols = C.shape
        n = max(n_rows, n_cols)

        # -- auf quadratisch auffüllen (Padding mit 0)
        if n_rows != n_cols:
            P = np.zeros((n, n), dtype=float)
            P[:n_rows, :n_cols] = C
            C = P

        # -- Zeilen- und Spaltenreduktion
        C -= C.min(axis=1, keepdims=True)
        C -= C.min(axis=0, keepdims=True)

        n = C.shape[0]
        # match_col[c] = r  (wenn Spalte c der Zeile r zugeordnet ist), sonst -1
        match_col = np.full(n, -1, dtype=int)

        def try_augment(r, seen_cols, zero_mask):
            """DFS: augmentierender Pfad im Nullgraphen."""
            for c in range(n):
                if zero_mask[r, c] and not seen_cols[c]:
                    seen_cols[c] = True
                    if match_col[c] == -1 or try_augment(match_col[c], seen_cols, zero_mask):
                        match_col[c] = r
                        return True
            return False

        while True:
            zero_mask = (C == 0.0)

            # Maximum Matching im Nullgraphen
            match_col[:] = -1
            for r in range(n):
                seen = np.zeros(n, dtype=bool)
                try_augment(r, seen, zero_mask)

            if np.all(match_col != -1):
                # Vollständiges Matching -> fertig
                break

            # Minimum Vertex Cover konstruieren (Kőnig):
            # Starred zeros = aktuelles Matching
            # Markierte Reihen = freie Reihen (nicht gematcht)
            matched_rows = np.full(n, False)
            for c, r in enumerate(match_col):
                if r != -1:
                    matched_rows[r] = True
            rows_marked = ~matched_rows
            cols_marked = np.zeros(n, dtype=bool)

            # BFS/Wechselwege entlang Nullkanten
            changed = True
            while changed:
                changed = False
                # (1) markierte Zeilen -> markiere Spalten mit Nullen
                for r in np.where(rows_marked)[0]:
                    for c in np.where(zero_mask[r])[0]:
                        if not cols_marked[c]:
                            cols_marked[c] = True
                            changed = True
                            # (2) markierte Spalten -> markiere die Zeile des "starred" Nulls (Match)
                            if match_col[c] != -1 and not rows_marked[match_col[c]]:
                                rows_marked[match_col[c]] = True
                                changed = True

            # Minimale Überdeckung: (UNmarkierte Reihen) U (markierte Spalten)
            # Uncovered Elemente: markierte Reihen & UNmarkierte Spalten
            uncovered_rows = rows_marked
            uncovered_cols = ~cols_marked

            # Wenn alles überdeckt wäre (kann numerisch vorkommen) -> Ende
            if not uncovered_rows.any() or not uncovered_cols.any():
                # kleine numerische Korrektur:
                C += 0.0  # no-op
            else:
                m = np.min(C[np.ix_(uncovered_rows, uncovered_cols)])
                # Matrix anpassen
                C[uncovered_rows, :] -= m
                C[:, cols_marked] += m
            # Danach neue Nullen entstanden -> nächste Matching-Runde

        # Zuordnung extrahieren und auf Originalgröße zurückfiltern
        rows, cols = [], []
        for c, r in enumerate(match_col):
            if r != -1 and r < n_rows and c < n_cols:
                rows.append(int(r))
                cols.append(int(c))
        return rows, cols
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