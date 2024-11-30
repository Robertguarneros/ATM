import streamlit as st
import numpy as np
import pandas as pd
import pandas as pd
import altair as alt


st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")
    
st.title("ATM Project")
chart_data = pd.DataFrame(
     np.random.randn(20, 3),
     columns=['a', 'b', 'c'])

st.line_chart(chart_data)

map_data = pd.DataFrame(
    np.random.randn(1000, 2) / [50, 50] + [41.3874, 2.1686],
    columns=['lat', 'lon'])

st.map(map_data)
