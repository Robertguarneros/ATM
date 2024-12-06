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

st.title("ATM Project - Separation Losses")
st.write("Here you can see the distance between flights when taking off")
st.write("You can filter by Radar, Wake or LoA")
