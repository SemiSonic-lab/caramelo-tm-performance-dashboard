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
k2.metric("IGP promedio", f"{view[igp_col].mean():.1f}" if igp_col else "N/D")
k3.metric("Carreras completadas", f"{metric_sum(races_col):,.0f}")
k4.metric("Puntos de carrera", f"{metric_sum(points_col):,.0f}")

tab_overview, tab_comparator, tab_ranking, tab_awards, tab_performance, tab_profile, tab_evolution, tab_data = st.tabs(
    ["📊 Resumen", "⚖️ Comparador", "🏆 Ranking", "🎖️ Reconocimientos", "🚦 Rendimiento", "👤 Perfil", "📈 Evolución", "📋 Datos"]
)

with tab_overview:
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Top 10 • IGP total")
        if igp_col:
            top = view.nlargest(10, igp_col).sort_values(igp_col, ascending=True)
            fig = px.bar(top, x=igp_col, y="Integrante", orientation="h",
                         text=igp_col, color_discrete_sequence=[ORANGE])
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
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
    st.dataframe(summary.round(1), use_container_width=True, hide_index=True)

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
            comparison_table.round(1),
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
            f"{ranking_data.iloc[0][selected_metric]:,.1f}" if not ranking_data.empty else "N/D",
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
            fig.update_traces(texttemplate="%{text:,.1f}", textposition="outside", cliponaxis=False)
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
                ranking_data.head(top_n).round(1),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "⬇️ Descargar ranking CSV",
                ranking_data.round(1).to_csv(index=False).encode("utf-8-sig"),
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

with tab_awards:
    st.subheader("Reconocimientos del equipo")
    st.caption(
        "Distinciones calculadas automáticamente con los indicadores disponibles "
        "en la hoja Caramelo y los filtros seleccionados."
    )

    award_candidates = []

    def add_award(title, description, metric_label, numerator_col, denominator_col=None, suffix=""):
        if not numerator_col:
            return
        numerator = pd.to_numeric(view[numerator_col], errors="coerce")
        if denominator_col:
            denominator = pd.to_numeric(view[denominator_col], errors="coerce").replace(0, float("nan"))
            values = numerator.div(denominator).mul(100)
        else:
            values = numerator
        valid = values.dropna()
        if valid.empty:
            return
        best_value = valid.max()
        winners = sorted(view.loc[valid[valid.eq(best_value)].index, "Integrante"].tolist())
        award_candidates.append({
            "Reconocimiento": title,
            "Integrante(s)": ", ".join(winners),
            "Indicador": metric_label,
            "Resultado": f"{best_value:,.1f}{suffix}",
            "Descripción": description,
        })

    add_award(
        "Máximo ganador",
        "Mayor número de carreras ganadas",
        "Carreras ganadas",
        wins_col,
    )
    add_award(
        "Mejor promedio de puntos",
        "Mayor promedio de puntos por carrera",
        "Promedio de puntos por carrera",
        avg_points_col,
    )
    add_award(
        "Mayor efectividad de victorias",
        "Carreras ganadas divididas entre carreras completadas",
        "Efectividad de victorias",
        wins_col,
        races_col,
        "%",
    )
    add_award(
        "Mayor efectividad de podios",
        "Podios divididos entre carreras completadas",
        "Efectividad de podios",
        podiums_col,
        races_col,
        "%",
    )
    add_award(
        "Mayor actividad",
        "Mayor número de carreras completadas registradas",
        "Carreras completadas",
        races_col,
    )

    if award_candidates:
        award_cols = st.columns(3)
        for index, award in enumerate(award_candidates):
            with award_cols[index % 3]:
                st.metric(award["Reconocimiento"], award["Integrante(s)"])
                st.caption(f'{award["Indicador"]}: {award["Resultado"]}')
        st.markdown("#### Detalle de reconocimientos")
        awards_table = pd.DataFrame(award_candidates)
        st.dataframe(
            awards_table[["Reconocimiento", "Integrante(s)", "Indicador", "Resultado", "Descripción"]],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "⬇️ Descargar reconocimientos CSV",
            awards_table.to_csv(index=False).encode("utf-8-sig"),
            file_name="caramelo_tm_reconocimientos.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay indicadores numéricos suficientes para calcular reconocimientos.")

    st.info(
        "Nota metodológica: «Mayor actividad» reconoce el mayor número de carreras completadas. "
        "No se presenta como «más constante», porque los datos acumulados no permiten medir "
        "la regularidad de participación o rendimiento carrera a carrera."
    )

with tab_performance:
    st.subheader("Semáforo de rendimiento")
    st.caption(
        "Clasificación relativa entre todos los integrantes registrados. "
        "El índice prioriza promedio y efectividad; la cantidad de carreras se muestra como contexto."
    )

    performance = pd.DataFrame({"Integrante": df["Integrante"]})
    component_scores = {}
    component_weights = {}

    def relative_percentile(series):
        """Escala cada métrica de 0 a 100; los empates reciben el promedio de su posición."""
        numeric = pd.to_numeric(series, errors="coerce")
        valid = numeric.dropna()
        result = pd.Series(float("nan"), index=series.index, dtype="float64")
        count = len(valid)
        if count == 1:
            result.loc[valid.index] = 50.0
        elif count > 1:
            ranks = valid.rank(method="average", ascending=True)
            result.loc[valid.index] = (ranks - 1) / (count - 1) * 100
        return result

    # Pesos del índice: promedio de puntos 40%, efectividad de victorias 30%,
    # efectividad de podios 30%. Si falta una métrica, los pesos se redistribuyen.
    if avg_points_col:
        component_scores["Promedio de puntos"] = relative_percentile(df[avg_points_col])
        component_weights["Promedio de puntos"] = 0.40

    if races_col and wins_col:
        completed = pd.to_numeric(df[races_col], errors="coerce").replace(0, float("nan"))
        win_rate = pd.to_numeric(df[wins_col], errors="coerce").div(completed).mul(100)
        component_scores["Efectividad de victorias"] = relative_percentile(win_rate)
        component_weights["Efectividad de victorias"] = 0.30

    if races_col and podiums_col:
        completed = pd.to_numeric(df[races_col], errors="coerce").replace(0, float("nan"))
        podium_rate = pd.to_numeric(df[podiums_col], errors="coerce").div(completed).mul(100)
        component_scores["Efectividad de podios"] = relative_percentile(podium_rate)
        component_weights["Efectividad de podios"] = 0.30

    if component_scores:
        score_frame = pd.DataFrame(component_scores, index=df.index)
        weighted_values = []
        weighted_validity = []
        for metric_name, weight in component_weights.items():
            weighted_values.append(score_frame[metric_name].fillna(0) * weight)
            weighted_validity.append(score_frame[metric_name].notna().astype(float) * weight)
        performance["Índice de rendimiento"] = (
            sum(weighted_values) / sum(weighted_validity).replace(0, float("nan"))
        )
        performance["Clasificación"] = performance["Índice de rendimiento"].apply(
            lambda value: (
                "🟢 Alto" if pd.notna(value) and value >= 66.7
                else "🟡 Intermedio" if pd.notna(value) and value >= 33.3
                else "🔴 En desarrollo" if pd.notna(value)
                else "Sin datos"
            )
        )

        if races_col:
            performance["Carreras completadas"] = pd.to_numeric(df[races_col], errors="coerce")
            median_races = performance["Carreras completadas"].median()
            performance["Referencia de actividad"] = performance["Carreras completadas"].apply(
                lambda value: (
                    "Por debajo de la mediana" if pd.notna(value) and pd.notna(median_races) and value < median_races
                    else "Igual o superior a la mediana" if pd.notna(value) and pd.notna(median_races)
                    else "Sin dato"
                )
            )

        for metric_name in component_scores:
            performance[metric_name] = score_frame[metric_name]

        performance_view = performance[performance["Integrante"].isin(selected_players)].copy()
        performance_view = performance_view.sort_values(
            "Índice de rendimiento", ascending=False, na_position="last"
        )

        score_col1, score_col2, score_col3 = st.columns(3)
        valid_scores = performance_view["Índice de rendimiento"].dropna()
        score_col1.metric("Índice promedio", f"{valid_scores.mean():.1f}" if not valid_scores.empty else "N/D")
        score_col2.metric("Nivel alto", f"{(performance_view['Clasificación'] == '🟢 Alto').sum():,.0f}")
        score_col3.metric("Integrantes evaluados", f"{len(valid_scores):,.0f}")

        chart_data = performance_view.dropna(subset=["Índice de rendimiento"]).sort_values(
            "Índice de rendimiento", ascending=True
        )
        if not chart_data.empty:
            fig = px.bar(
                chart_data,
                x="Índice de rendimiento",
                y="Integrante",
                color="Clasificación",
                orientation="h",
                text="Índice de rendimiento",
                color_discrete_map={
                    "🟢 Alto": "#22C55E",
                    "🟡 Intermedio": "#EAB308",
                    "🔴 En desarrollo": "#EF4444",
                    "Sin datos": "#737373",
                },
            )
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
            fig.update_layout(
                template="plotly_dark",
                height=max(360, 38 * len(chart_data) + 100),
                margin=dict(l=10, r=45, t=20, b=10),
                xaxis=dict(title="Índice relativo (0–100)", range=[0, 110]),
                yaxis_title="",
                legend_title="Clasificación",
            )
            st.plotly_chart(fig, use_container_width=True)

        table_columns = ["Integrante", "Índice de rendimiento", "Clasificación"]
        if "Carreras completadas" in performance_view.columns:
            table_columns += ["Carreras completadas", "Referencia de actividad"]
        table_columns += list(component_scores.keys())
        st.markdown("#### Detalle de evaluación")
        st.dataframe(
            performance_view[table_columns].round(1),
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "Metodología: el índice combina percentiles internos del equipo: promedio de puntos (40%), "
            "efectividad de victorias (30%) y efectividad de podios (30%). "
            "Alto: 66,7–100; intermedio: 33,3–menos de 66,7; en desarrollo: menos de 33,3. "
            "Los empates comparten puntuación. La actividad no suma puntos al índice; se muestra como contexto. "
            "La clasificación es relativa al equipo, no una calificación absoluta del juego."
        )
    else:
        st.warning(
            "No hay métricas suficientes para calcular el semáforo. "
            "Se requiere al menos el promedio de puntos o indicadores de efectividad."
        )

with tab_profile:
    st.subheader("Perfil individual")
    st.caption("Consulta el desempeño, los indicadores competitivos y el historial disponible de cada integrante.")

    profile_player = st.selectbox(
        "Seleccionar integrante",
        options=all_players,
        index=all_players.index(selected_player) if selected_player in all_players else 0,
        key="individual_profile_player",
    )
    profile_row = df[df["Integrante"] == profile_player].iloc[0]

    def profile_value(column, suffix=""):
        if not column or column not in profile_row.index:
            return "N/D"
        value = pd.to_numeric(pd.Series([profile_row[column]]), errors="coerce").iloc[0]
        return f"{value:,.1f}{suffix}" if pd.notna(value) else "N/D"

    profile_kpis = st.columns(4)
    profile_kpis[0].metric("IGP total", profile_value(igp_col))
    profile_kpis[1].metric("Carreras completadas", profile_value(races_col))
    profile_kpis[2].metric("Puntos de carrera", profile_value(points_col))
    profile_kpis[3].metric("Promedio de puntos", profile_value(avg_points_col))

    profile_kpis_2 = st.columns(4)
    profile_kpis_2[0].metric("Carreras ganadas", profile_value(wins_col))
    profile_kpis_2[1].metric("Podios", profile_value(podiums_col))

    profile_races = pd.to_numeric(pd.Series([profile_row[races_col]]), errors="coerce").iloc[0] if races_col else float("nan")
    profile_wins = pd.to_numeric(pd.Series([profile_row[wins_col]]), errors="coerce").iloc[0] if wins_col else float("nan")
    profile_podiums = pd.to_numeric(pd.Series([profile_row[podiums_col]]), errors="coerce").iloc[0] if podiums_col else float("nan")
    win_percentage = profile_wins / profile_races * 100 if pd.notna(profile_wins) and pd.notna(profile_races) and profile_races > 0 else float("nan")
    podium_percentage = profile_podiums / profile_races * 100 if pd.notna(profile_podiums) and pd.notna(profile_races) and profile_races > 0 else float("nan")
    profile_kpis_2[2].metric("Efectividad de victorias", f"{win_percentage:.1f}%" if pd.notna(win_percentage) else "N/D")
    profile_kpis_2[3].metric("Efectividad de podios", f"{podium_percentage:.1f}%" if pd.notna(podium_percentage) else "N/D")

    if component_scores and "Índice de rendimiento" in performance.columns:
        profile_score = performance.loc[performance["Integrante"] == profile_player].iloc[0]
        st.markdown("#### Evaluación de rendimiento")
        profile_score_col, profile_level_col = st.columns(2)
        profile_score_col.metric(
            "Índice relativo",
            f"{profile_score['Índice de rendimiento']:.1f}" if pd.notna(profile_score["Índice de rendimiento"]) else "N/D",
        )
        profile_level_col.metric("Clasificación", profile_score["Clasificación"])

        profile_components = sorted(
            [
                (name, float(profile_score[name]))
                for name in component_scores
                if pd.notna(profile_score[name])
            ],
            key=lambda item: item[1],
            reverse=True,
        )
        if profile_components:
            strongest_name, strongest_value = profile_components[0]
            weakest_name, weakest_value = profile_components[-1]
            if len(profile_components) == 1 or abs(strongest_value - weakest_value) < 0.1:
                st.info(f"Los indicadores evaluados muestran un comportamiento equilibrado. Principal referencia: {strongest_name}.")
            else:
                insight_left, insight_right = st.columns(2)
                insight_left.success(f"Fortaleza relativa: **{strongest_name}** ({strongest_value:.1f}/100)")
                insight_right.warning(f"Oportunidad relativa: **{weakest_name}** ({weakest_value:.1f}/100)")
            st.caption(
                "Las fortalezas y oportunidades se identifican comparando percentiles del integrante "
                "frente al resto del equipo; no representan un diagnóstico absoluto."
            )

    st.markdown("#### Historial individual")
    history_found = False
    if position_cols:
        position_rows = []
        for col in position_cols:
            match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", col)
            value = pd.to_numeric(pd.Series([profile_row[col]]), errors="coerce").iloc[0]
            if match and pd.notna(value):
                position_rows.append({"Fecha": match.group(1), "Posición": value})
        if position_rows:
            position_history = pd.DataFrame(position_rows).sort_values("Fecha")
            fig = px.line(position_history, x="Fecha", y="Posición", markers=True)
            fig.update_yaxes(autorange="reversed", title="Puesto en el club (1 = mejor)")
            fig.update_layout(template="plotly_dark", height=320, xaxis_title="Fecha", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            history_found = True

    if reputation_cols:
        reputation_rows = []
        for col in reputation_cols:
            match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", col)
            value = pd.to_numeric(pd.Series([profile_row[col]]), errors="coerce").iloc[0]
            if match and pd.notna(value):
                reputation_rows.append({"Fecha": match.group(1), "Reputación": value})
        if reputation_rows:
            reputation_history = pd.DataFrame(reputation_rows).sort_values("Fecha")
            fig = px.line(reputation_history, x="Fecha", y="Reputación", markers=True)
            fig.update_layout(template="plotly_dark", height=320, xaxis_title="Fecha", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            history_found = True

    if not history_found:
        st.info("Este integrante no tiene datos históricos suficientes para mostrar una evolución.")

with tab_evolution:
    st.subheader("Tendencias e historial del equipo")
    st.caption(
        "Compara los cambios observados entre las fechas históricas disponibles. "
        "La evolución refleja snapshots registrados en el Excel, no resultados carrera a carrera."
    )

    # Construir series históricas a partir de las columnas fechadas del Excel.
    position_rows = []
    for _, player_row in view.iterrows():
        for col in position_cols:
            match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", col)
            value = pd.to_numeric(pd.Series([player_row[col]]), errors="coerce").iloc[0]
            if match and pd.notna(value):
                position_rows.append({
                    "Integrante": player_row["Integrante"],
                    "Fecha": match.group(1),
                    "Posición": float(value),
                })

    reputation_rows = []
    for _, player_row in view.iterrows():
        for col in reputation_cols:
            match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", col)
            value = pd.to_numeric(pd.Series([player_row[col]]), errors="coerce").iloc[0]
            if match and pd.notna(value):
                reputation_rows.append({
                    "Integrante": player_row["Integrante"],
                    "Fecha": match.group(1),
                    "Reputación": float(value),
                })

    position_history = pd.DataFrame(position_rows)
    reputation_history = pd.DataFrame(reputation_rows)

    if not position_history.empty:
        position_history = position_history.sort_values(["Fecha", "Integrante"])
        position_dates = sorted(position_history["Fecha"].unique().tolist())

        # Comparación del primer y último snapshot disponible por integrante.
        position_summary = (
            position_history.sort_values("Fecha")
            .groupby("Integrante", as_index=False)
            .agg(
                **{
                    "Primera posición": ("Posición", "first"),
                    "Última posición": ("Posición", "last"),
                    "Snapshots": ("Fecha", "nunique"),
                }
            )
        )
        position_summary["Cambio de posición"] = (
            position_summary["Primera posición"] - position_summary["Última posición"]
        )
        position_summary["Tendencia"] = position_summary["Cambio de posición"].apply(
            lambda value: "Mejora" if value > 0 else ("Retroceso" if value < 0 else "Sin cambio")
        )

        improved = int((position_summary["Cambio de posición"] > 0).sum())
        declined = int((position_summary["Cambio de posición"] < 0).sum())
        unchanged = int((position_summary["Cambio de posición"] == 0).sum())

        st.markdown("#### Balance de posiciones")
        trend_kpis = st.columns(4)
        trend_kpis[0].metric("Snapshots disponibles", f"{len(position_dates):,.0f}")
        trend_kpis[1].metric("Integrantes que mejoran", f"{improved:,.0f}")
        trend_kpis[2].metric("Integrantes que retroceden", f"{declined:,.0f}")
        trend_kpis[3].metric("Sin cambio neto", f"{unchanged:,.0f}")

        st.caption(
            "Un cambio positivo significa que el número de puesto disminuyó y, por tanto, "
            "el integrante mejoró su posición. La comparación usa el primer y último dato "
            "disponible de cada integrante; puede haber fechas faltantes."
        )

        st.markdown("#### Evolución comparativa de posiciones")
        default_focus = [selected_player] if selected_player in view["Integrante"].tolist() else []
        position_focus = st.multiselect(
            "Integrantes para comparar",
            options=sorted(view["Integrante"].unique().tolist()),
            default=default_focus,
            key="phase4_position_focus",
        )
        plotted_positions = position_history[
            position_history["Integrante"].isin(position_focus)
        ]
        if not plotted_positions.empty:
            fig = px.line(
                plotted_positions, x="Fecha", y="Posición",
                color="Integrante", markers=True,
            )
            fig.update_yaxes(autorange="reversed", title="Puesto en el club (1 = mejor)")
            fig.update_layout(
                template="plotly_dark", height=440,
                xaxis_title="Fecha", legend_title="Integrante",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecciona al menos un integrante para ver su evolución de posiciones.")

        st.markdown("#### Clasificación histórica por fecha")
        selected_snapshot = st.selectbox(
            "Consultar snapshot",
            options=position_dates,
            index=len(position_dates) - 1,
            key="phase4_snapshot_date",
        )
        snapshot_table = (
            position_history[position_history["Fecha"] == selected_snapshot]
            .sort_values(["Posición", "Integrante"])
            .copy()
        )
        snapshot_table.insert(
            0, "Puesto histórico",
            snapshot_table["Posición"].rank(method="min", ascending=True).astype(int),
        )
        snapshot_table = snapshot_table.rename(columns={"Posición": "Puesto en el club"})
        st.dataframe(
            snapshot_table[["Puesto histórico", "Integrante", "Puesto en el club"]].round(1),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### Resumen de avance por integrante")
        position_summary = position_summary.sort_values(
            ["Cambio de posición", "Integrante"], ascending=[False, True]
        )
        st.dataframe(
            position_summary.round(1), use_container_width=True, hide_index=True
        )
        st.download_button(
            "⬇️ Descargar evolución de posiciones CSV",
            position_summary.round(1).to_csv(index=False).encode("utf-8-sig"),
            file_name="caramelo_tm_evolucion_posiciones.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay snapshots numéricos de posición disponibles para los integrantes seleccionados.")

    st.markdown("---")
    st.markdown("#### Evolución de reputación")
    if not reputation_history.empty:
        reputation_focus = st.multiselect(
            "Integrantes para comparar reputación",
            options=sorted(view["Integrante"].unique().tolist()),
            default=[selected_player] if selected_player in view["Integrante"].tolist() else [],
            key="phase4_reputation_focus",
        )
        plotted_reputation = reputation_history[
            reputation_history["Integrante"].isin(reputation_focus)
        ]
        if not plotted_reputation.empty:
            fig = px.line(
                plotted_reputation, x="Fecha", y="Reputación",
                color="Integrante", markers=True,
            )
            fig.update_layout(
                template="plotly_dark", height=410,
                xaxis_title="Fecha", yaxis_title="Reputación",
                legend_title="Integrante",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecciona al menos un integrante para ver la evolución de reputación.")

        reputation_summary = (
            reputation_history.sort_values("Fecha")
            .groupby("Integrante", as_index=False)
            .agg(
                **{
                    "Primera reputación": ("Reputación", "first"),
                    "Última reputación": ("Reputación", "last"),
                    "Snapshots": ("Fecha", "nunique"),
                }
            )
        )
        reputation_summary["Variación de reputación"] = (
            reputation_summary["Última reputación"] - reputation_summary["Primera reputación"]
        )
        st.markdown("#### Variación de reputación")
        st.dataframe(
            reputation_summary.sort_values(
                "Variación de reputación", ascending=False
            ).round(1),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "⬇️ Descargar evolución de reputación CSV",
            reputation_summary.round(1).to_csv(index=False).encode("utf-8-sig"),
            file_name="caramelo_tm_evolucion_reputacion.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay snapshots numéricos de reputación disponibles para los integrantes seleccionados.")

    st.info(
        "Alcance de los datos: estas tendencias comparan los snapshots históricos presentes "
        "en el archivo Excel. No permiten atribuir cambios a carreras concretas ni calcular "
        "la evolución histórica de puntos, victorias o podios por periodo. Para eso se necesitaría "
        "guardar una copia fechada del Excel en cada actualización o disponer de registros por carrera."
    )

with tab_data:
    st.subheader("Base de datos consultable")
    st.caption("Vista de las columnas principales; la hoja Capitanias no forma parte de esta aplicación.")
    st.dataframe(view[display_cols].round(1), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Descargar datos filtrados CSV",
        view[display_cols].round(1).to_csv(index=False).encode("utf-8-sig"),
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
