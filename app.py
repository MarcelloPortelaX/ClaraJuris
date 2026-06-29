from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, dcc, html

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "anotacoes.db"

APP_TITLE = "ClaraJuris Dashboard"
LIGHT_PINK_SCALE = ["#fde2ee", "#f8adc9", "#ee6aa7", "#c9387f", "#7b1b52"]
DARK_PINK_SCALE = ["#2a1424", "#5f1b43", "#a72d70", "#e75a9d", "#ffd2e4"]
PINK_SCALE = LIGHT_PINK_SCALE
FIG_TEMPLATE = "plotly_white"

THEME_CONFIG = {
    "light": {
        "template": "plotly_white",
        "font": "#3b2633",
        "grid": "rgba(142, 87, 118, 0.18)",
        "scale": LIGHT_PINK_SCALE,
        "discrete": ["#d94388", "#7b1b52", "#f06aa6", "#b9802e", "#257b63", "#c94466"],
    },
    "dark": {
        "template": "plotly_dark",
        "font": "#f7eaf1",
        "grid": "rgba(255, 210, 228, 0.18)",
        "scale": DARK_PINK_SCALE,
        "discrete": ["#ff78b5", "#ffd2e4", "#cf4f98", "#f3b76b", "#72d6bc", "#ff8aa7"],
    },
}


def normalize_theme(theme: str | None) -> str:
    return "dark" if theme == "dark" else "light"


def theme_config(theme: str | None) -> dict[str, object]:
    return THEME_CONFIG[normalize_theme(theme)]

TOPIC_COLUMNS = [
    "id",
    "materia",
    "tema",
    "incidencia_concurso",
    "dificuldade",
    "prioridade_oab",
    "prioridade_concurso_publico",
    "area_concurso",
    "descricao_curta",
]

COLUMN_LABELS = {
    "id": "ID",
    "codigo": "Código",
    "materia": "Matéria",
    "tema": "Tema",
    "incidencia_concurso": "Incidência",
    "dificuldade": "Dificuldade",
    "prioridade_oab": "Prioridade OAB",
    "prioridade_concurso_publico": "Prioridade concursos",
    "area_concurso": "Área / prova",
    "descricao_curta": "Descrição curta",
    "score_prioridade": "Score",
    "prioridade": "Prioridade",
    "concurso_x": "Concurso",
    "peso_concurso_x": "Peso no concurso",
    "faixa_concurso_x": "Faixa",
    "peso_medio": "Peso médio",
    "peso_total": "Peso total",
    "temas_quentes": "Temas quentes",
    "temas": "Temas",
    "titulo": "Título",
    "autor": "Autor",
    "nivel": "Nível",
    "uso_recomendado": "Uso recomendado",
    "observacao": "Observação",
    "url_amazon": "Amazon",
    "origem": "Origem",
    "criado_em": "Criado em",
}

# Perfis de prova usados para responder à pergunta central:
# "qual matéria cai mais no concurso X?".
# Os pesos são iniciais e editáveis. Eles combinam incidência geral,
# foco em OAB/concurso público e bônus quando a área aparece na base.
EXAM_RULES = {
    "OAB": {
        "label": "OAB",
        "base_column": "prioridade_oab",
        "keywords": ["OAB"],
        "description": "Prova da OAB, com peso maior para temas clássicos e recorrentes em questões objetivas.",
    },
    "TJ": {
        "label": "Tribunais de Justiça / TJ",
        "base_column": "prioridade_concurso_publico",
        "keywords": ["TJ", "Analista"],
        "description": "Recorte para carreiras e cargos ligados a Tribunais de Justiça.",
    },
    "MP": {
        "label": "Ministério Público / MP",
        "base_column": "prioridade_concurso_publico",
        "keywords": ["MP"],
        "description": "Recorte para provas com perfil forte em Direito Público, Penal, Processo e proteção institucional.",
    },
    "ANALISTA": {
        "label": "Analista jurídico",
        "base_column": "prioridade_concurso_publico",
        "keywords": ["Analista", "TJ"],
        "description": "Recorte para analista judiciário e cargos técnicos de tribunais/órgãos públicos.",
    },
    "GERAL": {
        "label": "Concursos públicos gerais",
        "base_column": "prioridade_concurso_publico",
        "keywords": ["TJ", "MP", "Analista", "OAB"],
        "description": "Visão ampla para concursos jurídicos, sem travar em uma banca específica.",
    },
}


def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return pd.read_csv(path)


disciplinas_df = load_csv("disciplinas_5_periodo.csv")
temas_df = load_csv("temas_concursos.csv")
livros_df = load_csv("livros_direito.csv")


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS anotacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                materia TEXT NOT NULL,
                tema TEXT,
                titulo TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                prioridade TEXT DEFAULT 'Normal',
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS temas_personalizados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                materia TEXT NOT NULL,
                tema TEXT NOT NULL,
                incidencia_concurso INTEGER NOT NULL DEFAULT 50,
                dificuldade INTEGER NOT NULL DEFAULT 3,
                prioridade_oab INTEGER NOT NULL DEFAULT 3,
                prioridade_concurso_publico INTEGER NOT NULL DEFAULT 3,
                area_concurso TEXT NOT NULL DEFAULT 'Geral',
                descricao_curta TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL
            )
            """
        )
        conn.commit()


def insert_note(materia: str, tema: str | None, titulo: str, conteudo: str, prioridade: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO anotacoes (materia, tema, titulo, conteudo, prioridade, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (materia, tema or "", titulo.strip(), conteudo.strip(), prioridade, now, now),
        )
        conn.commit()


def read_notes(limit: int = 40) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT id, materia, tema, titulo, conteudo, prioridade, criado_em FROM anotacoes ORDER BY id DESC LIMIT ?",
            conn,
            params=(limit,),
        )


def count_notes() -> int:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*) FROM anotacoes").fetchone()
        return int(row[0] or 0)


def insert_custom_topic(
    materia: str,
    tema: str,
    incidencia: int,
    dificuldade: int,
    prioridade_oab: int,
    prioridade_concurso: int,
    area: str,
    descricao: str,
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO temas_personalizados (
                materia, tema, incidencia_concurso, dificuldade, prioridade_oab,
                prioridade_concurso_publico, area_concurso, descricao_curta, criado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                materia,
                tema.strip(),
                int(incidencia),
                int(dificuldade),
                int(prioridade_oab),
                int(prioridade_concurso),
                (area or "Geral").strip(),
                (descricao or "Tema adicionado manualmente.").strip(),
                now,
            ),
        )
        conn.commit()


def read_custom_topics(include_meta: bool = False) -> pd.DataFrame:
    columns = TOPIC_COLUMNS + (["origem", "criado_em"] if include_meta else [])
    with sqlite3.connect(DB_PATH) as conn:
        try:
            df = pd.read_sql_query("SELECT * FROM temas_personalizados ORDER BY id DESC", conn)
        except Exception:
            return pd.DataFrame(columns=columns)
    if df.empty:
        return pd.DataFrame(columns=columns)
    df["origem"] = "Personalizado"
    for col in ["incidencia_concurso", "dificuldade", "prioridade_oab", "prioridade_concurso_publico"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    keep = TOPIC_COLUMNS + (["origem", "criado_em"] if include_meta else [])
    return df[keep]


def all_topics() -> pd.DataFrame:
    base = temas_df.copy()
    base["origem"] = "Base"
    custom = read_custom_topics(include_meta=False)
    if not custom.empty:
        # IDs dos temas personalizados ficam negativos no painel para evitar conflito visual com a base CSV.
        custom = custom.copy()
        custom["id"] = custom["id"].apply(lambda value: -abs(int(value)))
        custom["origem"] = "Personalizado"
        combined = pd.concat([base, custom], ignore_index=True)
    else:
        combined = base
    for col in ["incidencia_concurso", "dificuldade", "prioridade_oab", "prioridade_concurso_publico"]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0).astype(int)
    return combined


def priority_score(row: pd.Series) -> float:
    return round(
        row["incidencia_concurso"] * 0.55
        + row["prioridade_oab"] * 6
        + row["prioridade_concurso_publico"] * 7
        + row["dificuldade"] * 3,
        1,
    )


def enrich_topics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["score_prioridade"] = out.apply(priority_score, axis=1)
    out["prioridade"] = pd.cut(
        out["score_prioridade"],
        bins=[0, 85, 105, 1000],
        labels=["Revisar", "Importante", "Prioridade máxima"],
    ).astype(str)
    return out.sort_values("score_prioridade", ascending=False)


def get_enriched_topics() -> pd.DataFrame:
    return enrich_topics(all_topics())


def filter_topics(materias: Iterable[str] | None, dificuldade: int | None, area: str | None) -> pd.DataFrame:
    df = get_enriched_topics().copy()
    if materias:
        df = df[df["materia"].isin(list(materias))]
    if dificuldade:
        df = df[df["dificuldade"] >= int(dificuldade)]
    if area and area != "Todas":
        df = df[df["area_concurso"].astype(str).str.contains(area, case=False, na=False)]
    return df


def filter_books(materias: Iterable[str] | None, nivel: str | None) -> pd.DataFrame:
    df = livros_df.copy()
    if materias:
        df = df[df["materia"].isin(list(materias))]
    if nivel and nivel != "Todos":
        df = df[df["nivel"] == nivel]
    return df


def score_for_exam(row: pd.Series, exam: str) -> float:
    """Calcula o peso de cobrança de um tema para um concurso específico.

    O score fica em escala 0-100: incidência geral, prioridade do tipo
    de prova, dificuldade e bônus quando a área do tema combina com o concurso.
    A regra é simples de auditar e pode ser substituída por estatística real
    por banca quando houver base histórica de questões.
    """
    rule = EXAM_RULES.get(exam, EXAM_RULES["GERAL"])
    area = str(row.get("area_concurso", ""))
    base_priority = float(row.get(rule["base_column"], 0)) * 20
    incidence = float(row.get("incidencia_concurso", 0))
    difficulty = float(row.get("dificuldade", 0))
    area_bonus = 10 if any(keyword.lower() in area.lower() for keyword in rule["keywords"]) else 0
    score = incidence * 0.48 + base_priority * 0.40 + difficulty * 2.4 + area_bonus
    return round(min(score, 100), 1)


def topics_for_exam(df: pd.DataFrame, exam: str) -> pd.DataFrame:
    out = df.copy()
    out["concurso_x"] = EXAM_RULES.get(exam, EXAM_RULES["GERAL"])["label"]
    out["peso_concurso_x"] = out.apply(lambda row: score_for_exam(row, exam), axis=1)
    out["faixa_concurso_x"] = pd.cut(
        out["peso_concurso_x"],
        bins=[0, 70, 84, 100],
        labels=["Baixa/média", "Alta", "Muito alta"],
        include_lowest=True,
    ).astype(str)
    return out.sort_values("peso_concurso_x", ascending=False)


def subjects_for_exam(df: pd.DataFrame, exam: str) -> pd.DataFrame:
    exam_df = topics_for_exam(df, exam)
    if exam_df.empty:
        return pd.DataFrame(columns=["materia", "peso_medio", "peso_total", "temas_quentes", "temas"])
    grouped = (
        exam_df.groupby("materia", as_index=False)
        .agg(
            peso_medio=("peso_concurso_x", "mean"),
            peso_total=("peso_concurso_x", "sum"),
            temas_quentes=("peso_concurso_x", lambda values: int((values >= 85).sum())),
            temas=("tema", "count"),
        )
        .sort_values(["peso_medio", "temas_quentes"], ascending=False)
    )
    grouped["peso_medio"] = grouped["peso_medio"].round(1)
    grouped["peso_total"] = grouped["peso_total"].round(1)
    return grouped


def build_exam_subject_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for exam_key, rule in EXAM_RULES.items():
        grouped = subjects_for_exam(df, exam_key)
        for _, row in grouped.iterrows():
            rows.append(
                {
                    "concurso": rule["label"],
                    "materia": row["materia"],
                    "peso_medio": row["peso_medio"],
                }
            )
    return pd.DataFrame(rows)


def metric_card(title: str, value: str, subtitle: str = "", tone: str = "") -> html.Div:
    cls = "metric-card" + (f" metric-{tone}" if tone else "")
    return html.Div(
        className=cls,
        children=[
            html.Div(title, className="metric-title"),
            html.Div(value, className="metric-value"),
            html.Div(subtitle, className="metric-subtitle"),
        ],
    )


def panel(title: str, children, subtitle: str | None = None) -> html.Div:
    body = [html.H2(title)]
    if subtitle:
        body.append(html.P(subtitle))
    if isinstance(children, list):
        body.extend(children)
    else:
        body.append(children)
    return html.Div(className="panel", children=body)


def data_table(df: pd.DataFrame, page_size: int = 8, filterable: bool = False) -> dash_table.DataTable:
    visible = df.copy()
    visible = visible.fillna("")
    return dash_table.DataTable(
        data=visible.to_dict("records"),
        columns=[{"name": COLUMN_LABELS.get(col, col.replace("_", " ").title()), "id": col} for col in visible.columns],
        page_size=page_size,
        sort_action="native",
        filter_action="native" if filterable else "none",
        style_table={"overflowX": "auto", "width": "100%", "minWidth": "100%"},
        style_header={
            "backgroundColor": "var(--table-header-bg)",
            "color": "var(--table-header-text)",
            "fontWeight": "800",
            "border": "1px solid var(--table-border)",
        },
        style_cell={
            "backgroundColor": "var(--table-cell-bg)",
            "color": "var(--table-cell-text)",
            "border": "1px solid var(--table-border)",
            "fontFamily": "Inter, Segoe UI, Roboto, Arial",
            "fontSize": "13px",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "minWidth": "130px",
            "width": "170px",
            "maxWidth": "380px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "padding": "10px 12px",
            "lineHeight": "1.35",
        },
        style_filter={
            "backgroundColor": "var(--table-cell-bg)",
            "color": "var(--table-cell-text)",
            "border": "1px solid var(--table-border)",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "var(--table-alt-bg)"},
        ],
    )


def base_fig(fig: go.Figure, height: int = 430, theme: str | None = "light") -> go.Figure:
    config = theme_config(theme)
    fig.update_layout(
        template=config["template"],
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": config["font"], "family": "Inter, Segoe UI, Roboto, Arial"},
        title={"font": {"color": config["font"]}},
        margin={"l": 26, "r": 22, "t": 62, "b": 34},
        coloraxis_showscale=False,
        legend={"font": {"color": config["font"]}},
    )
    fig.update_xaxes(gridcolor=config["grid"], zerolinecolor=config["grid"], linecolor=config["grid"], tickfont={"color": config["font"]}, title_font={"color": config["font"]})
    fig.update_yaxes(gridcolor=config["grid"], zerolinecolor=config["grid"], linecolor=config["grid"], tickfont={"color": config["font"]}, title_font={"color": config["font"]})
    return fig


def figure_priority(df: pd.DataFrame, theme: str | None = "light") -> go.Figure:
    top = df.sort_values("score_prioridade", ascending=True).tail(12)
    fig = px.bar(
        top,
        x="score_prioridade",
        y="tema",
        orientation="h",
        color="score_prioridade",
        color_continuous_scale=theme_config(theme)["scale"],
        hover_data=["materia", "incidencia_concurso", "dificuldade", "area_concurso"],
        title="Temas com maior prioridade de estudo",
        labels={"score_prioridade": "Score", "tema": "Tema"},
    )
    return base_fig(fig, 500, theme)


def figure_by_subject(df: pd.DataFrame, theme: str | None = "light") -> go.Figure:
    grouped = (
        df.groupby("materia", as_index=False)
        .agg(incidencia_media=("incidencia_concurso", "mean"), temas=("tema", "count"))
        .sort_values("incidencia_media", ascending=False)
    )
    fig = px.bar(
        grouped,
        x="materia",
        y="incidencia_media",
        color="temas",
        color_continuous_scale=theme_config(theme)["scale"],
        title="Incidência média por matéria",
        labels={"incidencia_media": "Incidência média", "materia": "Matéria", "temas": "Nº de temas"},
    )
    fig.update_xaxes(tickangle=-28)
    return base_fig(fig, 430, theme)


def figure_difficulty(df: pd.DataFrame, theme: str | None = "light") -> go.Figure:
    fig = px.scatter(
        df,
        x="dificuldade",
        y="incidencia_concurso",
        size="score_prioridade",
        color="materia",
        color_discrete_sequence=theme_config(theme)["discrete"],
        hover_name="tema",
        title="Dificuldade × incidência em concursos",
        labels={"dificuldade": "Dificuldade", "incidencia_concurso": "Incidência"},
    )
    return base_fig(fig, 470, theme)


def figure_subjects_by_exam(df: pd.DataFrame, exam: str, theme: str | None = "light") -> go.Figure:
    grouped = subjects_for_exam(df, exam).sort_values("peso_medio", ascending=True)
    exam_label = EXAM_RULES.get(exam, EXAM_RULES["GERAL"])["label"]
    fig = px.bar(
        grouped,
        x="peso_medio",
        y="materia",
        orientation="h",
        color="temas_quentes",
        color_continuous_scale=theme_config(theme)["scale"],
        hover_data=["peso_total", "temas_quentes", "temas"],
        title=f"Qual matéria cai mais em {exam_label}",
        labels={
            "peso_medio": "Peso médio de cobrança",
            "materia": "Matéria",
            "temas_quentes": "Temas quentes",
            "peso_total": "Peso total",
            "temas": "Nº de temas",
        },
    )
    return base_fig(fig, 500, theme)


def figure_top_topics_by_exam(df: pd.DataFrame, exam: str, theme: str | None = "light") -> go.Figure:
    exam_df = topics_for_exam(df, exam).sort_values("peso_concurso_x", ascending=True).tail(10)
    exam_label = EXAM_RULES.get(exam, EXAM_RULES["GERAL"])["label"]
    fig = px.bar(
        exam_df,
        x="peso_concurso_x",
        y="tema",
        orientation="h",
        color="materia",
        color_discrete_sequence=theme_config(theme)["discrete"],
        hover_data=["materia", "dificuldade", "incidencia_concurso", "area_concurso"],
        title=f"Top temas para {exam_label}",
        labels={"peso_concurso_x": "Peso no concurso", "tema": "Tema"},
    )
    return base_fig(fig, 500, theme)


def figure_exam_heatmap(df: pd.DataFrame, theme: str | None = "light") -> go.Figure:
    matrix = build_exam_subject_matrix(df)
    if matrix.empty:
        fig = go.Figure()
        fig.update_layout(title="Mapa matéria × concurso")
        return base_fig(fig, 420, theme)
    pivot = matrix.pivot(index="materia", columns="concurso", values="peso_medio").fillna(0)
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale=theme_config(theme)["scale"],
            hovertemplate="Matéria: %{y}<br>Concurso: %{x}<br>Peso médio: %{z:.1f}<extra></extra>",
        )
    )
    fig.update_layout(title="Mapa de calor: matéria × tipo de concurso")
    return base_fig(fig, 460, theme)


def topic_cards(df: pd.DataFrame, limit: int = 6) -> html.Div:
    cards = []
    for _, row in df.head(limit).iterrows():
        cards.append(
            html.Div(
                className="topic-card",
                children=[
                    html.Span(row["prioridade"], className="tag"),
                    html.H3(row["tema"]),
                    html.Div(f"{row['materia']} · {row['area_concurso']}", className="metric-subtitle"),
                    html.Div(str(row["score_prioridade"]), className="score"),
                    html.P(row["descricao_curta"]),
                ],
            )
        )
    return html.Div(className="card-grid", children=cards)


def book_cards(df: pd.DataFrame, limit: int = 9) -> html.Div:
    cards = []
    for _, row in df.head(limit).iterrows():
        url = str(row.get("url_amazon", "")).strip() if "url_amazon" in row else ""
        children = [
            html.Span(row["nivel"], className="tag"),
            html.H3(row["titulo"]),
            html.Div(row["autor"], className="metric-subtitle"),
            html.P(f"{row['materia']} · {row['uso_recomendado']}"),
            html.P(row["observacao"]),
        ]
        if url:
            children.append(
                html.A(
                    "Ver na Amazon",
                    href=url,
                    target="_blank",
                    rel="noopener noreferrer",
                    className="book-link",
                )
            )
        cards.append(html.Div(className="book-card", children=children))
    return html.Div(className="card-grid", children=cards)


def note_cards(df: pd.DataFrame) -> html.Div:
    if df.empty:
        return html.Div(
            className="note-card",
            children=[html.H3("Nenhuma anotação ainda"), html.P("Escreva uma nota de aula, dúvida ou resumo. Ela será salva no SQLite local.")],
        )
    cards = []
    for _, row in df.iterrows():
        cards.append(
            html.Div(
                className="note-card",
                children=[
                    html.Span(row["prioridade"], className="tag"),
                    html.H3(row["titulo"]),
                    html.Div(f"{row['materia']} · {row['tema'] or 'tema livre'} · {row['criado_em']}", className="metric-subtitle"),
                    html.P(row["conteudo"]),
                ],
            )
        )
    return html.Div(className="card-grid", children=cards)


def dropdown_options(values: Iterable[str]) -> list[dict[str, str]]:
    return [{"label": str(v), "value": str(v)} for v in sorted(set(values))]


init_db()

app = Dash(__name__, suppress_callback_exceptions=True, title=APP_TITLE)
server = app.server

materia_options = dropdown_options(disciplinas_df["materia"])
nivel_options = [{"label": "Todos", "value": "Todos"}] + dropdown_options(livros_df["nivel"])
area_options = [
    {"label": "Todas", "value": "Todas"},
    {"label": "OAB", "value": "OAB"},
    {"label": "TJ", "value": "TJ"},
    {"label": "MP", "value": "MP"},
    {"label": "Analista", "value": "Analista"},
]
concurso_options = [{"label": rule["label"], "value": key} for key, rule in EXAM_RULES.items()]

app.layout = html.Div(
    id="app-shell",
    className="app-shell theme-light",
    children=[
        dcc.Store(id="theme-store", data="light"),
        dcc.Store(id="notes-refresh", data=0),
        dcc.Store(id="topics-refresh", data=0),
        html.Aside(
            className="sidebar",
            children=[
                html.Div(["CLARA", html.Span("JURIS")], className="brand"),
                html.Div("Dashboard de estudos · 5º módulo · Direito UFLA", className="brand-subtitle"),
                html.Button("Tema escuro", id="theme-toggle", n_clicks=0, className="theme-toggle"),
                html.Div(
                    className="sidebar-card",
                    children=[
                        html.H3("Como usar"),
                        html.Ol(
                            [
                                html.Li("Filtre as matérias do 5º módulo."),
                                html.Li("Compare peso por prova."),
                                html.Li("Abra a biblioteca por disciplina."),
                                html.Li("Salve resumos e dúvidas."),
                                html.Li("Alterne entre tema claro e escuro."),
                            ]
                        ),
                    ],
                ),
                html.Div(
                    className="control-group",
                    children=[
                        html.Label("Matérias"),
                        dcc.Dropdown(
                            id="filter-materias",
                            options=materia_options,
                            value=[opt["value"] for opt in materia_options],
                            multi=True,
                            placeholder="Selecione matérias",
                        ),
                        html.Label("Dificuldade mínima"),
                        dcc.Slider(
                            id="filter-difficulty",
                            min=1,
                            max=5,
                            step=1,
                            value=1,
                            marks={i: str(i) for i in range(1, 6)},
                        ),
                        html.Label("Foco de prova"),
                        dcc.Dropdown(id="filter-area", options=area_options, value="Todas", clearable=False),
                        html.Label("Concurso específico"),
                        dcc.Dropdown(id="filter-concurso-x", options=concurso_options, value="OAB", clearable=False),
                        html.Label("Nível de livro"),
                        dcc.Dropdown(id="filter-nivel", options=nivel_options, value="Todos", clearable=False),
                    ],
                ),
                html.Div(
                    className="sidebar-card",
                    children=[
                        html.H3("Base do painel"),
                        html.P(
                            "Matriz configurada para Civil IV, Trabalho I, Ética Profissional, Penal IV e Processual Civil II. A base já vem preenchida e a aba Personalizar permite adicionar temas próprios sem mexer nos CSVs."
                        ),
                    ],
                ),
            ],
        ),
        html.Main(
            className="main",
            children=[
                html.Div(
                    className="hero",
                    children=[
                        html.Div("DIREITO · CONCURSOS · LIVROS · ANOTAÇÕES", className="eyebrow"),
                        html.H1(["Painel de estudos para ", html.Span("Direito")]),
                        html.P(
                            "Um painel de estudos claro para organizar o quinto módulo: matérias, temas de revisão, peso por concurso, biblioteca recomendada e anotações persistentes."
                        ),
                        html.Div(
                            className="hero-actions",
                            children=[
                                html.Div([html.Strong("01"), html.Span("Filtrar matérias")]),
                                html.Div([html.Strong("02"), html.Span("Ver concursos")]),
                                html.Div([html.Strong("03"), html.Span("Ler e anotar")]),
                            ],
                        ),
                        html.Div(
                            "Construído para consulta rápida: o que estudar, por que estudar e qual livro abrir primeiro.",
                            className="notice",
                        ),
                    ],
                ),
                html.Div(id="metrics", className="metrics-grid"),
                dcc.Tabs(
                    id="tabs",
                    value="resumo",
                    className="tabs",
                    children=[
                        dcc.Tab(label="Resumo", value="resumo", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Matérias", value="materias", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Concursos", value="concursos", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Biblioteca", value="biblioteca", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Anotações", value="anotacoes", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Plano", value="plano", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Personalizar", value="personalizar", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Dados", value="dados", className="tab", selected_className="tab-selected"),
                    ],
                ),
                html.Div(id="tab-content", className="tab-content"),
            ],
        ),
    ],
)


@app.callback(
    Output("theme-store", "data"),
    Output("theme-toggle", "children"),
    Output("app-shell", "className"),
    Input("theme-toggle", "n_clicks"),
)
def toggle_theme(n_clicks):
    theme = "dark" if int(n_clicks or 0) % 2 else "light"
    label = "Tema claro" if theme == "dark" else "Tema escuro"
    return theme, label, f"app-shell theme-{theme}"


@app.callback(
    Output("metrics", "children"),
    Input("filter-materias", "value"),
    Input("filter-difficulty", "value"),
    Input("filter-area", "value"),
    Input("filter-concurso-x", "value"),
    Input("notes-refresh", "data"),
    Input("topics-refresh", "data"),
)
def update_metrics(materias, dificuldade, area, concurso_x, _notes_refresh, _topics_refresh):
    filtered = filter_topics(materias, dificuldade, area)
    avg_inc = filtered["incidencia_concurso"].mean() if not filtered.empty else 0
    top = filtered.iloc[0]["tema"] if not filtered.empty else "N/A"
    exam_subjects = subjects_for_exam(filtered, concurso_x)
    top_subject = exam_subjects.iloc[0]["materia"] if not exam_subjects.empty else "N/A"
    exam_label = EXAM_RULES.get(concurso_x, EXAM_RULES["GERAL"])["label"]
    return [
        metric_card("Matérias", str(len(materias or [])), "selecionadas"),
        metric_card("Temas", str(len(filtered)), "no recorte atual"),
        metric_card("Incidência", f"{avg_inc:.1f}", "média de prova", "gold"),
        metric_card("Top concurso X", top_subject[:26], exam_label, "danger"),
        metric_card("Livros", str(len(filter_books(materias, None))), "na biblioteca"),
        metric_card("Anotações", str(count_notes()), f"top: {top[:24]}", "ok"),
    ]


@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
    Input("filter-materias", "value"),
    Input("filter-difficulty", "value"),
    Input("filter-area", "value"),
    Input("filter-concurso-x", "value"),
    Input("filter-nivel", "value"),
    Input("theme-store", "data"),
    Input("notes-refresh", "data"),
    Input("topics-refresh", "data"),
)
def render_tab(tab, materias, dificuldade, area, concurso_x, nivel, theme, _notes_refresh, _topics_refresh):
    topics = filter_topics(materias, dificuldade, area)
    books = filter_books(materias, nivel)

    if tab == "resumo":
        return html.Div(
            children=[
                panel(
                    "Prioridades do recorte",
                    topic_cards(topics, limit=6),
                    "Comece pelos temas com maior combinação entre incidência, dificuldade e relevância para OAB/concurso.",
                ),
                html.Div(
                    className="two-column",
                    children=[
                        html.Div(className="panel", children=[dcc.Graph(figure=figure_priority(topics, theme))]),
                        html.Div(className="panel", children=[dcc.Graph(figure=figure_by_subject(topics, theme))]),
                    ],
                ),
            ]
        )

    if tab == "materias":
        subject_blocks = []
        for materia in materias or []:
            subset = topics[topics["materia"] == materia].sort_values("score_prioridade", ascending=False)
            subject_blocks.append(
                html.Div(
                    className="panel",
                    children=[
                        html.H2(materia),
                        html.P("Temas organizados por prioridade para ajudar a decidir por onde começar."),
                        data_table(
                            subset[["tema", "incidencia_concurso", "dificuldade", "prioridade", "area_concurso", "descricao_curta"]],
                            page_size=6,
                        ),
                    ],
                )
            )
        return html.Div(subject_blocks or [panel("Sem matéria selecionada", html.P("Selecione pelo menos uma matéria na lateral."))])

    if tab == "concursos":
        exam_label = EXAM_RULES.get(concurso_x, EXAM_RULES["GERAL"])["label"]
        exam_description = EXAM_RULES.get(concurso_x, EXAM_RULES["GERAL"])["description"]
        exam_topics = topics_for_exam(topics, concurso_x)
        return html.Div(
            children=[
                panel(
                    f"Concurso específico: {exam_label}",
                    html.Div(
                        className="exam-intro",
                        children=[
                            html.P(exam_description),
                            html.P(
                                "Use o filtro lateral para trocar o concurso X. O ranking recalcula o peso por matéria e por tema sem mexer nos outros filtros."
                            ),
                        ],
                    ),
                    "Ranking por matéria e por tema para o concurso escolhido.",
                ),
                html.Div(
                    className="two-column",
                    children=[
                        html.Div(className="panel", children=[dcc.Graph(figure=figure_subjects_by_exam(topics, concurso_x, theme))]),
                        html.Div(className="panel", children=[dcc.Graph(figure=figure_top_topics_by_exam(topics, concurso_x, theme))]),
                    ],
                ),
                html.Div(className="panel", children=[dcc.Graph(figure=figure_exam_heatmap(topics, theme))]),
                html.Div(className="panel", children=[dcc.Graph(figure=figure_difficulty(topics, theme))]),
                panel(
                    "Tabela de temas por concurso X",
                    data_table(
                        exam_topics[
                            [
                                "concurso_x",
                                "materia",
                                "tema",
                                "peso_concurso_x",
                                "faixa_concurso_x",
                                "incidencia_concurso",
                                "dificuldade",
                                "prioridade_oab",
                                "prioridade_concurso_publico",
                                "area_concurso",
                                "score_prioridade",
                            ]
                        ],
                        page_size=12,
                    ),
                    "Pesos iniciais ajustáveis. Podem ser substituídos por dados históricos de questões por banca quando a base existir.",
                ),
            ]
        )

    if tab == "biblioteca":
        return html.Div(
            children=[
                panel(
                    "Biblioteca jurídica recomendada",
                    book_cards(books, limit=12),
                    "Banco inicial de livros por matéria, nível e uso. Dá para expandir com links, edição, preço e status de leitura.",
                ),
                panel("Tabela da biblioteca", data_table(books, page_size=10)),
            ]
        )

    if tab == "anotacoes":
        tema_options = dropdown_options(topics["tema"]) if not topics.empty else []
        notes = read_notes()
        return html.Div(
            children=[
                html.Div(
                    className="panel",
                    children=[
                        html.H2("Nova anotação"),
                        html.P("Campo para resumo de aula, dúvidas, revisão ou mini-fichamento."),
                        html.Div(
                            className="form-grid",
                            children=[
                                html.Div(
                                    children=[
                                        html.Label("Matéria"),
                                        dcc.Dropdown(
                                            id="note-materia",
                                            options=materia_options,
                                            value=(materias or [materia_options[0]["value"]])[0],
                                            clearable=False,
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Tema"),
                                        dcc.Dropdown(id="note-tema", options=tema_options, placeholder="Tema relacionado", clearable=True),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Prioridade"),
                                        dcc.Dropdown(
                                            id="note-prioridade",
                                            options=[
                                                {"label": "Normal", "value": "Normal"},
                                                {"label": "Revisar", "value": "Revisar"},
                                                {"label": "Urgente", "value": "Urgente"},
                                            ],
                                            value="Normal",
                                            clearable=False,
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Título"),
                                        dcc.Input(id="note-title", className="input", placeholder="Ex: diferença entre anulação e revogação"),
                                    ]
                                ),
                                html.Div(
                                    className="full",
                                    children=[
                                        html.Label("Conteúdo"),
                                        dcc.Textarea(id="note-content", placeholder="Escreva aqui..."),
                                    ],
                                ),
                                html.Div(
                                    className="full",
                                    children=[
                                        html.Button("Salvar anotação", id="save-note", n_clicks=0, className="button"),
                                        html.Div(id="note-status", className="status"),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                panel("Anotações salvas", note_cards(notes), "Persistem no arquivo data/anotacoes.db quando o app roda localmente."),
            ]
        )

    if tab == "plano":
        plan = topics[["materia", "tema", "score_prioridade", "prioridade", "dificuldade", "descricao_curta"]].copy()
        plan["ação sugerida"] = plan["prioridade"].map(
            {
                "Prioridade máxima": "Ler doutrina + fazer questões + revisar em 48h",
                "Importante": "Resumo curto + questões + revisão semanal",
                "Revisar": "Leitura leve + marcação para revisão",
            }
        )
        plan["status"] = "Não iniciado"
        return html.Div(
            children=[
                panel(
                    "Plano de ataque",
                    data_table(plan, page_size=14),
                    "O objetivo é distribuir esforço por prioridade, dificuldade e incidência provável.",
                ),
                html.Div(
                    className="three-column",
                    children=[
                        html.Div(
                            className="panel",
                            children=[
                                html.H3("1. Alta incidência"),
                                html.P("Priorize temas com muita cobrança: eles aumentam segurança e previsibilidade."),
                            ],
                        ),
                        html.Div(
                            className="panel",
                            children=[
                                html.H3("2. Alta dificuldade"),
                                html.P("Comece cedo nos temas difíceis para evitar acúmulo antes da prova."),
                            ],
                        ),
                        html.Div(
                            className="panel",
                            children=[
                                html.H3("3. Livro certo"),
                                html.P("Use um livro base e um material de revisão para manter foco."),
                            ],
                        ),
                    ],
                ),
            ]
        )

    if tab == "personalizar":
        custom_topics = read_custom_topics(include_meta=True)
        return html.Div(
            children=[
                html.Div(
                    className="panel",
                    children=[
                        html.H2("Adicionar tema personalizado"),
                        html.P("Ela pode completar a base com o que o professor passou, tópico de aula, lista de exercícios ou tema de prova."),
                        html.Div(
                            className="form-grid",
                            children=[
                                html.Div(
                                    children=[
                                        html.Label("Matéria"),
                                        dcc.Dropdown(
                                            id="custom-materia",
                                            options=materia_options,
                                            value=(materias or [materia_options[0]["value"]])[0],
                                            clearable=False,
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Tema"),
                                        dcc.Input(id="custom-tema", className="input", placeholder="Ex: honorários sucumbenciais"),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Incidência estimada: 0 a 100"),
                                        dcc.Input(id="custom-incidencia", className="input", type="number", min=0, max=100, value=70),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Dificuldade: 1 a 5"),
                                        dcc.Input(id="custom-dificuldade", className="input", type="number", min=1, max=5, value=3),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Prioridade OAB: 1 a 5"),
                                        dcc.Input(id="custom-oab", className="input", type="number", min=1, max=5, value=3),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Prioridade concursos: 1 a 5"),
                                        dcc.Input(id="custom-concurso", className="input", type="number", min=1, max=5, value=3),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label("Área / prova"),
                                        dcc.Input(id="custom-area", className="input", placeholder="Ex: OAB/TJ/Analista", value="OAB/TJ"),
                                    ]
                                ),
                                html.Div(
                                    className="full",
                                    children=[
                                        html.Label("Descrição curta"),
                                        dcc.Textarea(id="custom-descricao", placeholder="Explique o que entra nesse tema e por que revisar."),
                                    ],
                                ),
                                html.Div(
                                    className="full",
                                    children=[
                                        html.Button("Adicionar tema", id="save-custom-topic", n_clicks=0, className="button"),
                                        html.Div(id="custom-topic-status", className="status"),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                panel(
                    "Temas adicionados por ela",
                    data_table(custom_topics, page_size=10, filterable=False) if not custom_topics.empty else html.P("Nenhum tema personalizado ainda."),
                    "Esses registros ficam salvos em data/anotacoes.db quando o app roda localmente.",
                ),
            ]
        )

    if tab == "dados":
        topics_all = get_enriched_topics()
        return html.Div(
            children=[
                panel("Disciplinas", data_table(disciplinas_df, page_size=8, filterable=True)),
                panel("Temas e concursos", data_table(topics_all, page_size=12, filterable=True)),
                panel("Livros", data_table(livros_df, page_size=12, filterable=True)),
                html.Div(
                    className="footer-note",
                    children="Para editar a base fixa, altere os CSVs dentro da pasta data/. Para completar sem mexer em arquivo, use a aba Personalizar.",
                ),
            ]
        )

    return panel("Aba não encontrada", html.P("Algo falhou no roteamento da interface."))


@app.callback(
    Output("custom-topic-status", "children"),
    Output("topics-refresh", "data"),
    Input("save-custom-topic", "n_clicks"),
    State("custom-materia", "value"),
    State("custom-tema", "value"),
    State("custom-incidencia", "value"),
    State("custom-dificuldade", "value"),
    State("custom-oab", "value"),
    State("custom-concurso", "value"),
    State("custom-area", "value"),
    State("custom-descricao", "value"),
    State("topics-refresh", "data"),
    prevent_initial_call=True,
)
def save_custom_topic(n_clicks, materia, tema, incidencia, dificuldade, prioridade_oab, prioridade_concurso, area, descricao, refresh):
    if not n_clicks:
        return "", refresh
    if not materia or not tema:
        return "Preencha pelo menos matéria e tema.", refresh
    try:
        incidencia = max(0, min(100, int(incidencia if incidencia is not None else 50)))
        dificuldade = max(1, min(5, int(dificuldade if dificuldade is not None else 3)))
        prioridade_oab = max(1, min(5, int(prioridade_oab if prioridade_oab is not None else 3)))
        prioridade_concurso = max(1, min(5, int(prioridade_concurso if prioridade_concurso is not None else 3)))
    except ValueError:
        return "Use números válidos nos campos de incidência e prioridade.", refresh
    insert_custom_topic(
        materia,
        tema,
        incidencia,
        dificuldade,
        prioridade_oab,
        prioridade_concurso,
        area or "Geral",
        descricao or "Tema adicionado manualmente.",
    )
    return "Tema adicionado. Ele já entra nos gráficos, tabelas e rankings.", int(refresh or 0) + 1


@app.callback(
    Output("note-status", "children"),
    Output("notes-refresh", "data"),
    Input("save-note", "n_clicks"),
    State("note-materia", "value"),
    State("note-tema", "value"),
    State("note-title", "value"),
    State("note-content", "value"),
    State("note-prioridade", "value"),
    State("notes-refresh", "data"),
    prevent_initial_call=True,
)
def save_note(n_clicks, materia, tema, title, content, prioridade, refresh):
    if not n_clicks:
        return "", refresh
    if not materia or not title or not content:
        return "Preencha matéria, título e conteúdo antes de salvar.", refresh
    insert_note(materia, tema, title, content, prioridade or "Normal")
    return "Anotação salva com sucesso.", int(refresh or 0) + 1


if __name__ == "__main__":
    print("======================================")
    print(f"{APP_TITLE} iniciando...")
    print("Abra: http://127.0.0.1:8050")
    print("======================================")
    app.run(host="127.0.0.1", port=8050, debug=False)
