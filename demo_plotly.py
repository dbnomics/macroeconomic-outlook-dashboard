import dbnomics
import plotly.graph_objects as go
import streamlit as st
from pandas import DataFrame

series_list = [
    "OECD/KEI/NAEXKP01.DEU.GP.Q",
    "OECD/KEI/NAEXKP01.FRA.GP.Q",
    "OECD/KEI/NAEXKP01.GBR.GP.Q",
    "OECD/KEI/NAEXKP01.JPN.GP.Q",
    "OECD/KEI/NAEXKP01.ITA.GP.Q",
    "OECD/KEI/NAEXKP01.USA.GP.Q",
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


# ----------operations----------
df_raw = get_series_data(series_list)
df = pivot_and_slice_dataframe(df_raw, "2021-Q4")
fig = draw_multiple_series_trace(df_raw, series_list, "2019-Q4")

# ----------output----------
"# Growth Rates"
df
fig
