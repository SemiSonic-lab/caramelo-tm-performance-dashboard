import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# Caramelo TM | Team Performance Dashboard
# Fuente: hoja "Caramelo" del archivo Excel ubicado junto a app.py
# La hoja "Capitanias" se ignora intencionalmente.
# ------------------------------------------------------------

st.set_page_config(
    page_title="Caramelo TM | Team Performance",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded",
)

ORANGE = "#F97316"
DARK = "#171717"
PANEL = "#242424"
GRAY = "#A3A3A3"
EXCEL_FILE = Path(__file__).with_name("Caramelo TM.xlsx")

st.markdown(
    f"""
    <style>
      .stApp {{ background: #111315; color: #F5F5F5; }}
      [data-testid="stSidebar"] {{ background: #191B1F; }}
      [data-testid="stMetric"] {{
        background: #202328; border: 1px solid #343941;
        padding: 15px 17px; border-radius: 12px;
      }}
      [data-testid="stMetricLabel"] {{ color: #B8BEC7; }}
      [data-testid="stMetricValue"] {{ color: #F97316; }}
      h1, h2, h3 {{ color: #F5F5F5; }}
      div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: #F97316; border-bottom-color: #F97316;
      }}
      .hero {{
        background: linear-gradient(110deg, #202328 0%, #171717 68%, #38200F 100%);
        border: 1px solid #343941; border-left: 5px solid {ORANGE};
        padding: 22px 25px; border-radius: 14px; margin-bottom: 18px;
      }}
      .hero-title {{ font-size: 30px; font-weight: 800; letter-spacing: 1.5px; }}
      .hero-sub {{ color: #B8BEC7; font-size: 13px; letter-spacing: 2px; }}
      .small-note {{ color: #A3A3A3; font-size: 12px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def load_data():
    if not EXCEL_FILE.exists():
        st.error(
            f"No encuentro el archivo **{EXCEL_FILE.name}**. "
            "Debe estar en la misma carpeta que app.py."
        )
        st.stop()

    try:
        # Se lee exclusivamente la hoja Caramelo; Capitanias no se importa.
        raw = pd.read_excel(EXCEL_FILE, sheet_name="Caramelo")
    except Exception as exc:
        st.error(f"No fue posible leer la hoja Caramelo: {exc}")
        st.stop()

    raw.columns = [str(c).strip() for c in raw.columns]
    if "Integrante" not in raw.columns:
        st.error("La hoja Caramelo no contiene la columna obligatoria 'Integrante'.")
        st.stop()

    data = raw.dropna(subset=["Integrante"]).copy()
    data["Integrante"] = data["Integrante"].astype(str).str.strip()
    data = data[data["Integrante"].ne("") & data["Integrante"].str.casefold().ne("nan")]
    data = data.drop_duplicates(subset=["Integrante"], keep="last")

    # Las columnas entre "Nuevos Comienzos" y "Total Participaciones GP"
    # contienen resultados GP (incluidos códigos como F y Q) y deben conservarse.
    gp_start = raw.columns.get_loc("Nuevos Comienzos") if "Nuevos Comienzos" in raw.columns else None
    gp_end = raw.columns.get_loc("Total Participaciones GP") if "Total Participaciones GP" in raw.columns else None
    gp_result_cols = (
        set(raw.columns[gp_start:gp_end])
        if gp_start is not None and gp_end is not None and gp_start < gp_end
        else set()
    )

    # Convertir todas las métricas a número, sin alterar los códigos de resultados GP.
    # La conversión explícita evita que IGP TOTAL y los totales GP queden como texto
    # por contener las letras "GP" en el nombre de la columna.
    for col in data.columns:
        if col == "Integrante" or col in gp_result_cols:
            continue
        data[col] = pd.to_numeric(data[col], errors="coerce")

    return data


df = load_data()


def find_col(prefix):
    matches = [c for c in df.columns if c.lower().startswith(prefix.lower())]
    return matches[0] if matches else None


def metric_sum(col):
    return pd.to_numeric(df[col], errors="coerce").sum() if col else 0


def metric_mean(col):
    return pd.to_numeric(df[col], errors="coerce").mean() if col else float("nan")


igp_col = find_col("IGP TOTAL")
races_col = find_col("Carreras Completadas")
points_col = find_col("Puntos Carrera")
avg_points_col = find_col("Promedio Puntos por Carrera")
wins_col = find_col("Carreras Ganadas")
podiums_col = find_col("Podios")

# Detectar columnas históricas de posiciones y reputación usando las fechas del encabezado.
position_cols = [c for c in df.columns if "Puesto en el club" in c]
reputation_cols = [c for c in df.columns if "Reputación" in c and "Avance" not in c]
position_cols = sorted(position_cols, key=lambda c: re.search(r"\((\d{4}-\d{2}-\d{2})\)", c).group(1)
                       if re.search(r"\((\d{4}-\d{2}-\d{2})\)", c) else "")
reputation_cols = sorted(reputation_cols, key=lambda c: re.search(r"\((\d{4}-\d{2}-\d{2})\)", c).group(1)
                         if re.search(r"\((\d{4}-\d{2}-\d{2})\)", c) else "")

st.markdown(
    """
    <div class="hero">
      <div class="hero-sub">TEAM ANALYTICS • MOTORSPORT PERFORMANCE</div>
      <div class="hero-title">🏁 CARAMELO TM</div>
      <div style="color:#D4D4D4;margin-top:5px;">TEAM PERFORMANCE DASHBOARD</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar filters
st.sidebar.markdown("## 🏎️ Panel de consulta")
st.sidebar.caption("Los filtros afectan las tablas y los análisis de integrantes.")
all_players = sorted(df["Integrante"].unique().tolist())
selected_players = st.sidebar.multiselect(
    "Integrantes", all_players, default=all_players, help="Selecciona uno o varios integrantes."
)
if not selected_players:
    st.sidebar.warning("Selecciona al menos un integrante para visualizar los datos.")
    st.stop()

view = df[df["Integrante"].isin(selected_players)].copy()
selected_player = st.sidebar.selectbox("Analizar integrante", sorted(selected_players))

# KPIs generales del conjunto filtrado
k1, k2, k3, k4 = st.columns(4)
k1.metric("Integrantes", f"{len(view):,}")
k2.metric("IGP promedio", f"{view[igp_col].mean():.2f}" if igp_col else "N/D")
k3.metric("Carreras completadas", f"{metric_sum(races_col):,.0f}")
k4.metric("Puntos de carrera", f"{metric_sum(points_col):,.0f}")

tab_overview, tab_comparator, tab_ranking, tab_evolution, tab_data = st.tabs(
    ["📊 Resumen", "⚖️ Comparador", "🏆 Ranking", "📈 Evolución", "📋 Datos"]
)

with tab_overview:
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Top 10 • IGP total")
        if igp_col:
            top = view.nlargest(10, igp_col).sort_values(igp_col, ascending=True)
            fig = px.bar(top, x=igp_col, y="Integrante", orientation="h",
                         text=igp_col, color_discrete_sequence=[ORANGE])
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig.update_layout(template="plotly_dark", height=410, margin=dict(l=10,r=35,t=15,b=10),
                              xaxis_title="IGP total", yaxis_title="", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Carreras vs. promedio de puntos")
        if races_col and avg_points_col:
            fig = px.scatter(
                view, x=races_col, y=avg_points_col, color=igp_col if igp_col else None,
                hover_name="Integrante", size=podiums_col if podiums_col else None,
                color_continuous_scale=["#737373", ORANGE],
            )
            fig.update_layout(template="plotly_dark", height=410,
                              margin=dict(l=10,r=10,t=15,b=10),
                              xaxis_title="Carreras completadas",
                              yaxis_title="Promedio de puntos por carrera")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Indicadores individuales")
    display_cols = [c for c in [
        "Integrante", igp_col, races_col, points_col, avg_points_col,
        wins_col, podiums_col
    ] if c and c in view.columns]
    summary = view[display_cols].sort_values(igp_col, ascending=False) if igp_col else view[display_cols]
    st.dataframe(summary, use_container_width=True, hide_index=True)

with tab_comparator:
    st.subheader("Comparador de integrantes")
    st.caption(
        "Selecciona entre dos y cinco integrantes para comparar sus indicadores. "
        "Las tasas se calculan sobre las carreras completadas."
    )

    comparison_players = st.multiselect(
        "Integrantes para comparar",
        options=all_players,
        default=all_players[:min(3, len(all_players))],
        key="comparison_players",
    )
    if len(comparison_players) > 5:
        st.warning("Para facilitar la lectura, compara máximo cinco integrantes a la vez.")
        comparison_players = comparison_players[:5]

    if len(comparison_players) < 2:
        st.info("Selecciona al menos dos integrantes para iniciar la comparación.")
    else:
        comparison = df[df["Integrante"].isin(comparison_players)].copy()

        # Tasas de eficiencia: victorias y podios respecto a carreras completadas.
        if races_col and wins_col:
            races = pd.to_numeric(comparison[races_col], errors="coerce").replace(0, float("nan"))
            comparison["Tasa de victorias (%)"] = (
                pd.to_numeric(comparison[wins_col], errors="coerce") / races * 100
            )
        if races_col and podiums_col:
            races = pd.to_numeric(comparison[races_col], errors="coerce").replace(0, float("nan"))
            comparison["Tasa de podios (%)"] = (
                pd.to_numeric(comparison[podiums_col], errors="coerce") / races * 100
            )

        comparison_metrics = [
            ("IGP TOTAL", igp_col),
            ("Carreras completadas", races_col),
            ("Puntos de carrera", points_col),
            ("Promedio de puntos por carrera", avg_points_col),
            ("Carreras ganadas", wins_col),
            ("Podios", podiums_col),
        ]
        available_metrics = [(label, col) for label, col in comparison_metrics if col]
        efficiency_metrics = [
            label for label in ["Tasa de victorias (%)", "Tasa de podios (%)"]
            if label in comparison.columns
        ]

        # Tabla comparativa con valores absolutos y tasas calculadas.
        table_cols = ["Integrante"] + [col for _, col in available_metrics] + efficiency_metrics
        comparison_table = comparison[table_cols].copy()
        comparison_table = comparison_table.rename(
            columns={col: label for label, col in available_metrics}
        )
        st.markdown("#### Comparación de indicadores")
        st.dataframe(
            comparison_table.round(2),
            use_container_width=True,
            hide_index=True,
        )

        # Radar indexado a 100 frente al mejor valor del grupo seleccionado.
        radar_metrics = [
            (label, col) for label, col in available_metrics
            if col in [igp_col, races_col, points_col, avg_points_col, wins_col, podiums_col]
        ]
        if len(radar_metrics) >= 3:
            radar = []
            for _, player in comparison.iterrows():
                values = []
                for _, col in radar_metrics:
                    group_values = pd.to_numeric(comparison[col], errors="coerce")
                    maximum = group_values.max()
                    value = pd.to_numeric(pd.Series([player[col]]), errors="coerce").iloc[0]
                    values.append(
                        float(value / maximum * 100)
                        if pd.notna(value) and pd.notna(maximum) and maximum > 0
                        else 0
                    )
                radar.append((player["Integrante"], values))

            fig = go.Figure()
            categories = [label for label, _ in radar_metrics]
            for player_name, values in radar:
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=player_name,
                    opacity=0.65,
                ))
            fig.update_layout(
                template="plotly_dark",
                title="Perfil comparativo (índice relativo, máximo del grupo = 100)",
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                height=520,
                margin=dict(l=35, r=35, t=65, b=30),
                legend=dict(orientation="h", y=-0.15),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "El gráfico normaliza cada indicador por separado para facilitar la comparación. "
                "Consulta la tabla para ver los valores reales."
            )

        if efficiency_metrics:
            st.markdown("#### Eficiencia competitiva")
            efficiency = comparison[["Integrante"] + efficiency_metrics].melt(
                id_vars="Integrante",
                var_name="Indicador",
                value_name="Porcentaje",
            )
            fig = px.bar(
                efficiency,
                x="Integrante",
                y="Porcentaje",
                color="Indicador",
                barmode="group",
                text_auto=".1f",
                color_discrete_sequence=[ORANGE, "#A3A3A3"],
            )
            fig.update_layout(
                template="plotly_dark",
                height=390,
                yaxis_title="Porcentaje de carreras",
                xaxis_title="",
                margin=dict(l=10, r=10, t=25, b=10),
                legend_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Tasa de victorias = carreras ganadas / carreras completadas. "
                "Tasa de podios = podios / carreras completadas. "
                "Si un integrante no tiene carreras completadas, la tasa queda sin dato."
            )

with tab_ranking:
    st.subheader("Ranking avanzado de integrantes")
    st.caption(
        "Consulta la clasificación por diferentes indicadores. Los filtros generales "
        "del panel lateral se aplican también a este ranking."
    )

    ranking_data = view.copy()
    ranking_options = {}

    # Indicadores absolutos disponibles en la hoja Caramelo.
    for label, col in [
        ("IGP total", igp_col),
        ("Puntos de carrera", points_col),
        ("Carreras completadas", races_col),
        ("Carreras ganadas", wins_col),
        ("Podios", podiums_col),
        ("Promedio de puntos por carrera", avg_points_col),
    ]:
        if col and col in ranking_data.columns:
            ranking_options[label] = col

    # Indicadores de eficiencia calculados con los datos originales.
    if races_col and wins_col:
        completed = pd.to_numeric(ranking_data[races_col], errors="coerce").replace(0, float("nan"))
        wins = pd.to_numeric(ranking_data[wins_col], errors="coerce")
        ranking_data["Efectividad de victorias (%)"] = wins.div(completed).mul(100)
        ranking_options["Efectividad de victorias (%)"] = "Efectividad de victorias (%)"

    if races_col and podiums_col:
        completed = pd.to_numeric(ranking_data[races_col], errors="coerce").replace(0, float("nan"))
        podiums = pd.to_numeric(ranking_data[podiums_col], errors="coerce")
        ranking_data["Efectividad de podios (%)"] = podiums.div(completed).mul(100)
        ranking_options["Efectividad de podios (%)"] = "Efectividad de podios (%)"

    if ranking_options:
        preferred_metric = "IGP total" if "IGP total" in ranking_options else next(iter(ranking_options))
        selected_metric = st.selectbox(
            "Clasificar integrantes por",
            options=list(ranking_options.keys()),
            index=list(ranking_options.keys()).index(preferred_metric),
            key="advanced_ranking_metric",
        )
        top_n = st.slider(
            "Integrantes que se muestran",
            min_value=5,
            max_value=max(5, min(30, len(ranking_data))),
            value=min(10, max(5, len(ranking_data))),
            key="advanced_ranking_top_n",
        )

        metric_col = ranking_options[selected_metric]
        position_data = ranking_data.copy()
        ranking_data[metric_col] = pd.to_numeric(ranking_data[metric_col], errors="coerce")
        ranking_data = ranking_data.dropna(subset=[metric_col]).sort_values(
            [metric_col, "Integrante"], ascending=[False, True], kind="stable"
        ).reset_index(drop=True)
        ranking_data.insert(0, "Posición", ranking_data[metric_col].rank(
            method="min", ascending=False
        ).astype(int))
        ranking_data = ranking_data.rename(columns={metric_col: selected_metric})

        first, second = st.columns(2)
        first.metric("Líder actual", ranking_data.iloc[0]["Integrante"] if not ranking_data.empty else "N/D")
        second.metric(
            f"Mejor resultado · {selected_metric}",
            f"{ranking_data.iloc[0][selected_metric]:,.2f}" if not ranking_data.empty else "N/D",
        )

        if not ranking_data.empty:
            chart_data = ranking_data.head(top_n).sort_values(selected_metric, ascending=True)
            fig = px.bar(
                chart_data,
                x=selected_metric,
                y="Integrante",
                orientation="h",
                text=selected_metric,
                color_discrete_sequence=[ORANGE],
            )
            fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside", cliponaxis=False)
            fig.update_layout(
                template="plotly_dark",
                height=max(360, 38 * len(chart_data) + 100),
                margin=dict(l=10, r=45, t=20, b=10),
                xaxis_title=selected_metric,
                yaxis_title="",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Tabla de posiciones")
            st.dataframe(
                ranking_data.head(top_n).round(2),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "⬇️ Descargar ranking CSV",
                ranking_data.to_csv(index=False).encode("utf-8-sig"),
                file_name="caramelo_tm_ranking.csv",
                mime="text/csv",
            )

        # Matriz de posiciones para identificar fortalezas por categoría.
        st.markdown("#### Resumen de posiciones por categoría")
        matrix = pd.DataFrame({"Integrante": position_data["Integrante"].tolist()})
        position_index = position_data.set_index("Integrante")
        for label, col in ranking_options.items():
            values = pd.to_numeric(position_index[col], errors="coerce")
            positions = values.rank(method="min", ascending=False).astype("Int64")
            matrix[label] = matrix["Integrante"].map(positions)
        matrix = matrix.sort_values("Integrante").reset_index(drop=True)
        st.dataframe(matrix, use_container_width=True, hide_index=True)
        st.caption(
            "La posición 1 representa el mejor resultado. Los empates comparten posición; "
            "los indicadores porcentuales se calculan sobre carreras completadas. "
            "Los integrantes sin dato válido no reciben posición en esa categoría."
        )
    else:
        st.info("No se encontraron métricas suficientes para construir el ranking.")

with tab_evolution:
    st.subheader("Evolución de posición en el club")
    if position_cols:
        rows = []
        for _, row in view.iterrows():
            for col in position_cols:
                match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", col)
                val = pd.to_numeric(pd.Series([row[col]]), errors="coerce").iloc[0]
                if match and pd.notna(val):
                    rows.append({"Integrante": row["Integrante"], "Fecha": match.group(1), "Posición": val})
        if rows:
            hist = pd.DataFrame(rows)
            focus = st.multiselect("Integrantes para comparar", sorted(view["Integrante"].unique()),
                                   default=[selected_player], key="position_focus")
            hist = hist[hist["Integrante"].isin(focus)]
            fig = px.line(hist, x="Fecha", y="Posición", color="Integrante", markers=True)
            fig.update_yaxes(autorange="reversed", title="Puesto (1 = mejor posición)")
            fig.update_layout(template="plotly_dark", height=430, xaxis_title="Fecha")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay posiciones históricas numéricas disponibles.")
    else:
        st.info("No se identificaron columnas históricas de posición.")

    st.subheader("Evolución de reputación")
    if reputation_cols:
        rows = []
        for _, row in view.iterrows():
            for col in reputation_cols:
                match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", col)
                val = pd.to_numeric(pd.Series([row[col]]), errors="coerce").iloc[0]
                if match and pd.notna(val):
                    rows.append({"Integrante": row["Integrante"], "Fecha": match.group(1), "Reputación": val})
        if rows:
            hist = pd.DataFrame(rows)
            focus = st.multiselect("Integrantes para comparar", sorted(view["Integrante"].unique()),
                                   default=[selected_player], key="reputation_focus")
            hist = hist[hist["Integrante"].isin(focus)]
            fig = px.line(hist, x="Fecha", y="Reputación", color="Integrante", markers=True)
            fig.update_layout(template="plotly_dark", height=430, xaxis_title="Fecha")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay reputaciones históricas numéricas disponibles.")
    else:
        st.info("No se identificaron columnas históricas de reputación.")

with tab_data:
    st.subheader("Base de datos consultable")
    st.caption("Vista de las columnas principales; la hoja Capitanias no forma parte de esta aplicación.")
    st.dataframe(view[display_cols], use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Descargar datos filtrados CSV",
        view[display_cols].to_csv(index=False).encode("utf-8-sig"),
        file_name="caramelo_tm_datos.csv",
        mime="text/csv",
    )

st.markdown("---")
st.markdown(
    f"<div class='small-note'>Fuente: hoja <b>Caramelo</b> del archivo Excel • "
    f"Registros válidos: {len(df)} integrantes • "
    f"Actualización: reemplazar <b>Caramelo TM.xlsx</b> en el repositorio y reiniciar la aplicación.</div>",
    unsafe_allow_html=True,
)
