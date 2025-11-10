import pandas as pd
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from functions.create_adjacency import create_adjazenz_list_per_constraint, connect_all_constraints
from algorithms import backtracking_coloring
from algorithms.dsatur import dsatur
from algorithms.greedy import greedy_algorithm
from algorithms import rlf_algorithm
from algorithms import welsh_powell_algorithm
from functions.timetable_algo import create_timetable
from functions import export_detailed_timetable_to_excel
from datetime import date
from functions import get_edges, get_density, get_highest_degree

st.set_page_config(page_title="Stundenplan-Optimierung", layout="wide")

st.title("Stundenplan-Optimierung mit Graphfärbung")

st.markdown("""
<style>
section.main h1 {
    background: linear-gradient(90deg, #C8102E 0%, #A60C25 100%);
    color: white !important;
    text-align: center;
    padding: 16px 24px;
    border-radius: 0 0 14px 14px;
    margin: -1rem -1rem 1.25rem -1rem; 
    line-height: 1.25;
    box-shadow: 0 2px 12px rgba(0,0,0,.15);
}
</style>
""", unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    st.subheader("Konfiguration")

    file = st.file_uploader("Datensatz hochladen (CSV)", type=["csv"])
    delimiter = st.selectbox("Trennzeichen", [",", ";", "\\t"], format_func=lambda s: {"\\t": "Tab"}.get(s, s))
    if file:
        sep = {"\\t": "\t"}.get(delimiter, delimiter)
        try:
            df = pd.read_csv(file, sep=sep)
        except Exception as e:
            st.error(f"CSV konnte nicht gelesen werden: {e}")
            df = None

        if isinstance(df, pd.DataFrame):
            st.caption(f"Vorschau ({len(df)} Zeilen, {len(df.columns)} Spalten)")
            st.dataframe(df.head(10), use_container_width=True)

            node_col = st.selectbox("Welche Spalte definiert die Knoten?", df.columns)

            constraint_cols = st.multiselect(
                "Welche Spalten sind Constraints? (Gleicher Wert ⇒ Konflikt)",
                [c for c in df.columns if c != node_col]
            )

            strategy = st.selectbox(
                "Färbe-Strategie",
                ["Greedy-Algorithmus", "Welsh-Powell-Algorithmus", "Backtracking-Algorithmus", "DSATUR-Algorithmus", "RLF-Algorithmus"],
            )

            run = st.button("Färbung ausführen", type="primary")

            if run:
                if not node_col:
                    st.warning("Bitte eine Knoten-Spalte auswählen.")
                elif not constraint_cols:
                    st.warning("Bitte mindestens eine Constraint-Spalte auswählen.")
                else:
                    all_constraint_dicts = []
                    node_index = df.columns.get_loc(node_col)
                    for c in constraint_cols:
                        c_index = df.columns.get_loc(c)
                        ajd_dict = create_adjazenz_list_per_constraint(df, node_index, c_index)
                        all_constraint_dicts.append(ajd_dict)

                    all_edges = connect_all_constraints(*all_constraint_dicts)

                    if strategy == "Greedy-Algorithmus":
                        color_dict = greedy_algorithm(all_edges)
                    elif strategy == "Welsh-Powell-Algorithmus":
                        color_dict = welsh_powell_algorithm(all_edges)
                    elif strategy == "DSATUR-Algorithmus":
                        color_dict = dsatur(all_edges)
                    elif strategy == "RLF-Algorithmus":
                        color_dict = rlf_algorithm(all_edges)
                    elif strategy == "Backtracking-Algorithmus":
                        color_dict = backtracking_coloring(all_edges)

                    timetable_raw = create_timetable(df, all_edges, color_dict)

                    st.session_state["timetable_result"] = timetable_raw
                    st.session_state["color_count"] = timetable_raw["k"]
                    st.session_state["satisfaction"] = timetable_raw["satisfaction"]
                    st.session_state["dataset"] = df
                    st.session_state["node_col"] = node_col
                    st.session_state["all_edges"] = all_edges
                    st.session_state["all_nodes"] = df[node_col].astype(str).unique().tolist()
                    st.session_state["adjacency"] = all_edges
                    st.session_state["color_dict"] = color_dict


                    def _edges_from_adj(adj):
                        return list({tuple(sorted((str(u), str(v)))) for u in adj for v in adj[u] if str(u) != str(v)})


                    G_tmp = nx.Graph()
                    G_tmp.add_nodes_from(df[node_col].astype(str).unique().tolist())
                    G_tmp.add_edges_from(_edges_from_adj(all_edges))
                    pos = nx.spring_layout(G_tmp, seed=42)
                    st.session_state["graph_pos"] = pos


            if "timetable_result" in st.session_state:
                st.markdown("---")
                st.subheader("Excel-Export")

                start_dt = st.date_input("Startdatum für Kalender (Montag empfohlen)", value=date.today(),
                                         key="export_start")
                start_dt_str = start_dt.strftime("%Y-%m-%d")

                df_for_export = st.session_state["dataset"]
                node_col_for_export = st.session_state["node_col"]


                room_col = next((c for c in ["room", "Room", "Raum", "raum"] if c in df_for_export.columns), None)
                instructor_col = next((c for c in ["lecturer", "Lecturer", "Dozent", "dozent", "instructor"] if
                                       c in df_for_export.columns), None)
                title_col = next((c for c in ["title", "Title", "Modul", "modul", "course_name", "CourseName"] if
                                  c in df_for_export.columns), None)

                with st.expander("Spaltenzuordnung (optional anpassen)"):
                    course_col = st.selectbox("Kurs-ID Spalte", list(df_for_export.columns),
                                              index=list(df_for_export.columns).index(node_col_for_export))
                    room_choice = st.selectbox("Raum-Spalte (oder '— keine —')",
                                               ["— keine —"] + list(df_for_export.columns),
                                               index=(["— keine —"] + list(df_for_export.columns)).index(
                                                   room_col) if room_col else 0)
                    instructor_choice = st.selectbox("Dozent-Spalte (oder '— keine —')",
                                                     ["— keine —"] + list(df_for_export.columns),
                                                     index=(["— keine —"] + list(df_for_export.columns)).index(
                                                         instructor_col) if instructor_col else 0)
                    title_choice = st.selectbox("Titel/Modul (oder '— keine —')",
                                                ["— keine —"] + list(df_for_export.columns),
                                                index=(["— keine —"] + list(df_for_export.columns)).index(
                                                    title_col) if title_col else 0)

                    room_col = None if room_choice == "— keine —" else room_choice
                    instructor_col = None if instructor_choice == "— keine —" else instructor_choice
                    title_col = None if title_choice == "— keine —" else title_choice

                if "course_col" not in locals():
                    course_col = node_col_for_export


                try:
                    xls_bytes = export_detailed_timetable_to_excel(
                        result=st.session_state["timetable_result"],
                        dataset=df_for_export,
                        start_date=start_dt_str,
                        file_path=None,
                        course_col=course_col,
                        room_col=room_col,
                        instructor_col=instructor_col,
                        title_col=title_col,
                        use_german_headers=True
                    )
                    st.download_button(
                        "Stundenplan als Excel herunterladen",
                        data=xls_bytes,
                        file_name="stundenplan.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Excel-Export fehlgeschlagen: {e}")

with right:
    st.markdown('<div class="split-divider">', unsafe_allow_html=True)
    st.subheader("Ergebnisse")
    st.markdown('<div class="split-divider">', unsafe_allow_html=True)

    if "all_edges" in st.session_state and st.session_state["all_edges"] is not None:
        adj = st.session_state["all_edges"]

        e_count = get_edges(adj)
        max_deg = get_highest_degree(adj)
        dens = get_density(adj)

        c1, c2, c3 = st.columns(3)
        c1.metric("Anzahl Kanten", e_count)
        c2.metric("Maximaler Grad", max_deg)
        c3.metric("Dichte", f"{dens:.3f}")

        if "timetable_result" in st.session_state:
            tr = st.session_state["timetable_result"]
            c4, c5, c6 = st.columns(3)
            c4.metric("Anzahl Farben", tr["k"])
            c5.metric("Soft-Constraint-Score", f"{tr['satisfaction'] * 100:.1f}%")
            c6.metric("Erfüllte Präferenzen", f"{tr['satisfied']} / {tr['total']}")


        def _edges_from_adj(adj):
            return list({tuple(sorted((str(u), str(v)))) for u in adj for v in adj[u] if str(u) != str(v)})


        nodes = list({str(u) for u in adj.keys()})
        edges = _edges_from_adj(adj)
        G = nx.Graph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        pos = st.session_state.get("graph_pos")
        if pos is None:
            pos = nx.spring_layout(G, seed=42)
            st.session_state["graph_pos"] = pos

        color_dict = st.session_state.get("color_dict", {})

        node_count = G.number_of_nodes()
        node_size = max(100, 8000 / max(1, node_count))
        font_size = max(4, 14 - node_count / 10)

        st.markdown("**Konfliktgraph (ungefärbt)**")
        plt.figure(figsize=(6.0, 5.0))
        nx.draw_networkx_nodes(G, pos, node_size=node_size)
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.6)
        nx.draw_networkx_labels(G, pos, font_size=font_size)
        plt.axis("off")
        st.pyplot(plt.gcf())

        if color_dict:
            st.markdown("**Konfliktgraph (gefärbt)**")

            node_colors = [color_dict.get(n, color_dict.get(str(n), -1)) for n in G.nodes()]
            cmap = plt.cm.tab20
            plt.figure(figsize=(6.0, 5.0))
            nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color=node_colors, cmap=cmap)
            nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.6)
            nx.draw_networkx_labels(G, pos, font_size=font_size)
            plt.axis("off")
            st.pyplot(plt.gcf())
        else:
            st.info("Noch keine Färbung vorhanden.")

    else:
        st.info("Bitte links die Färbung ausführen – dann erscheinen hier die Kennzahlen.")




    st.markdown("</div>", unsafe_allow_html=True)
