from datetime import datetime
from typing import Literal

import altair as alt
import dbnomics
import pandas as pd
import streamlit as st

series_list = [
    "OECD/KEI/NAEXKP01.DEU.GP.Q",
    "OECD/KEI/NAEXKP01.FRA.GP.Q",
    "OECD/KEI/NAEXKP01.GBR.GP.Q",
    "OECD/KEI/NAEXKP01.USA.GP.Q",
    "OECD/KEI/NAEXKP01.JPN.GP.Q",
]


@st.cache_data
def get_series_data(series_list) -> pd.DataFrame:
    df: pd.DataFrame = dbnomics.fetch_series(series_list)
    df = df.pivot_table(index="Country", columns="original_period", values="value")

    return df


@st.cache_data
def slice_df(df: pd.DataFrame, start_slice, end_slice) -> pd.DataFrame:
    start_column_index = df.columns.get_loc(start_slice)
    end_column_index = df.columns.get_loc(end_slice)

    return df.iloc[:, start_column_index : end_column_index + 1]


@st.cache_data
def period_to_datetime(period: str) -> datetime:
    """
    2020-Q1 -> 2020-01-01
    1970-Q4 -> 1970-10-01
    2022-Q3 -> 2022-07-01
    """

    year, quarter = period.split("-")

    quarter_months = {"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}

    month = quarter_months[quarter]

    return datetime(int(year), month, 1)


@st.cache_data
def datetime_to_period(date: datetime) -> str:
    """
    2020-01-01 -> 2020-Q1
    1970-10-04 -> 1970-Q4
    2022-07-19 -> 2022-Q3
    """

    quarter_map = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}

    year = date.year
    month = date.month

    quarter = (month - 1) // 3 + 1

    period_str = f"{year}-{quarter_map[quarter]}"

    return period_str


@st.cache_data
def get_min_max_periods(df: pd.DataFrame) -> tuple[str, str]:
    melt_df = pd.melt(df)

    min_period = melt_df["original_period"].min()
    max_period = melt_df["original_period"].max()

    return (min_period, max_period)


@st.cache_data
def prepare_chart(chart_type: Literal["Area", "Bar", "Line", "Square"], chart_data):
    if chart_type == "Area":
        c = (
            alt.Chart(chart_data)
            .mark_area(opacity=0.7)
            .encode(x="Period", y="Value", color="Country")
        )
    elif chart_type == "Bar":
        c = (
            alt.Chart(chart_data)
            .mark_bar(opacity=0.7)
            .encode(x="Period", y="Value", color="Country")
        )
    elif chart_type == "Line":
        c = (
            alt.Chart(chart_data)
            .mark_line(opacity=0.7)
            .encode(x="Period", y="Value", color="Country")
        )
    else:
        c = (
            alt.Chart(chart_data)
            .mark_square(opacity=0.7)
            .encode(x="Period", y="Value", color="Country")
        )

    return c


df = get_series_data(series_list)

countries = st.multiselect("Filter by country", set(df.index))

min_period, max_period = get_min_max_periods(df)
min_period_datetime = period_to_datetime(min_period)
max_period_datetime = period_to_datetime(max_period)

period_range = st.slider(
    "Select a period range:",
    value=(min_period_datetime, max_period_datetime),
    format="YYYY-\QQ",
    min_value=min_period_datetime,
    max_value=max_period_datetime,
)

start_slice = datetime_to_period(period_range[0])
end_slice = datetime_to_period(period_range[1])

df = slice_df(df, start_slice, end_slice)

if countries:
    chart_data: pd.DataFrame = df.loc[countries]
else:
    chart_data: pd.DataFrame = df

st.write("### Quarterly GDP growth rate (% change over the previous period)")
st.dataframe(chart_data)

chart_data = chart_data.T.reset_index()
chart_data = pd.melt(chart_data, id_vars=["original_period"]).rename(
    columns={"original_period": "Period", "value": "Value"}
)

chart_type = st.selectbox("Select chart type", ["Area", "Bar", "Line", "Square"])

c = prepare_chart(chart_type, chart_data)

st.altair_chart(c, use_container_width=True)
