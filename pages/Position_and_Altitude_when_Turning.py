import streamlit as st
import altair as alt
import pandas as pd

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Turn data")
st.write("Here we can see info about the turns when departing from runway 24L")