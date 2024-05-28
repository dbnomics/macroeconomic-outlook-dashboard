import dbnomics
import plotly.graph_objects as go
import streamlit as st
from pandas import DataFrame

high_level_series_list = [
    "OECD/KEI/NAEXKP01.DEU.GP.Q",
    "OECD/KEI/NAEXKP01.FRA.GP.Q",
    "OECD/KEI/NAEXKP01.GBR.GP.Q",
    "OECD/KEI/NAEXKP01.JPN.GP.Q",
    "OECD/KEI/NAEXKP01.ITA.GP.Q",
    "OECD/KEI/NAEXKP01.USA.GP.Q",
]

second_level_series_list = [
    "OECD/KEI/NAEXKP01.CHN.GP.Q",
    # originally China data comes from series "OECD/DP_LIVE/CHN.QGDP.TOT.PC_CHGPP.Q" which does not go along with the others
    "OECD/KEI/NAEXKP01.BRA.GP.Q",
    "OECD/KEI/NAEXKP01.MEX.GP.Q",
    "OECD/KEI/NAEXKP01.ZAF.GP.Q",
    "OECD/KEI/NAEXKP01.IDN.GP.Q",
    "OECD/KEI/NAEXKP01.IND.GP.Q",
]


@st.cache_data
def get_series_data(series_list: list[str]) -> DataFrame:
    df: DataFrame = dbnomics.fetch_series(series_list)

    return df


@st.cache_data
def pivot_and_slice_dataframe(
    df: DataFrame, slice_period: str | None = None
) -> DataFrame:
    df = df.pivot_table(index="Country", columns="original_period", values="value")

    start_column_index = 0

    if slice_period is not None:
        start_column_index = df.columns.get_loc(slice_period)

    return df.iloc[:, start_column_index:]


@st.cache_data
def get_growth_level(
    df: DataFrame, series_id: str, base_period: str | None = None
) -> DataFrame:
    df = df[df["series_code"] == series_id]

    if base_period is not None:
        df = df[df["original_period"] >= base_period]

    df["growth"] = None
    df.iloc[0, df.columns.get_loc("growth")] = 100

    for i, _ in enumerate(df.index):
        if i == 0:
            continue

        df.iloc[i, df.columns.get_loc("growth")] = df["growth"].iloc[i - 1] * (
            1 + df["value"].iloc[i] / 100
        )

    return df[["Country", "original_period", "growth"]]


@st.cache_data
def draw_series_trace(df: DataFrame, series_code: str, base_period: str):
    growth_rates = get_growth_level(df, series_code, base_period)
    trace = go.Scatter(
        x=growth_rates["original_period"],
        y=growth_rates["growth"],
        name=growth_rates["Country"].iloc[0],
        mode="lines",
    )

    return trace


@st.cache_data
def draw_multiple_series_trace(df: DataFrame, series_list: list[str], base_period: str):
    fig = go.Figure()

    for series in series_list:
        series_code = series.split("/")[-1]
        trace = draw_series_trace(df, series_code, base_period)
        fig.add_trace(trace)

    fig.update_layout(
        title=f"Quarterly GDP (base 100 in {base_period})",
        xaxis_title="Period",
        yaxis_title="Quarterly GDP growth rate %",
    ).update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all"),
                ]
            )
        ),
    )

    return fig


# ----------output----------
st.set_page_config(layout="wide")
"# Macroeconomic Outlook"

"This is a work in progress."

"This is a port of the [Macroeconomic Outlook presentation](https://www.cepremap.fr/observatoire-macroeconomie/macroeconomic-outlook/) as a web dashboard using [Streamlit](https://streamlit.io/)."

"[Source code](https://git.nomics.world/dbnomics/dbnomics-dashboards/macroeconomic-outlook-dashboard)"

"## Growth and inflation in selected G20 countries"

"### Growth rates were quite similar in advanced economies in the first quarter"

"Growth was positive for all main advanced economies in the first quarter of 2024 (except for Japan), following a strong divergence in 2023. However, the OECD have severely revised downward their growth projections for 2024 for European countries and revised upwards those for the US."


"### Quarterly GDP growth rate (% change over the previous period)"

high_level_df_raw = get_series_data(high_level_series_list)
high_level_df = pivot_and_slice_dataframe(high_level_df_raw, "2021-Q4")
high_level_df

high_level_fig = draw_multiple_series_trace(
    high_level_df_raw, high_level_series_list, "2019-Q4"
)
high_level_fig


"### Growth remains at high levels in emerging Asian countries"

"India, Indonesia and China have overperformed the other developing countries in 2023. South Africa has had a particularly low growth. The OECD have lifted their 2024 growth projections for Brazil and Mexico, but they have revised downwards South-African growth."

second_level_df_raw = get_series_data(second_level_series_list)
second_level_df = pivot_and_slice_dataframe(second_level_df_raw, "2022-Q1")
second_level_df

second_level_fig = draw_multiple_series_trace(
    second_level_df_raw, second_level_series_list, "2019-Q4"
)
second_level_fig
