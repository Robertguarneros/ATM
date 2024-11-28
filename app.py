import streamlit as st
import numpy as np
import pandas as pd




st.title("ATM Project")
chart_data = pd.DataFrame(
     np.random.randn(20, 3),
     columns=['a', 'b', 'c'])

st.line_chart(chart_data)

map_data = pd.DataFrame(
    np.random.randn(1000, 2) / [50, 50] + [41.22, -2.10],
    columns=['lat', 'lon'])

st.map(map_data)
