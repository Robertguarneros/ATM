import streamlit as st
import altair as alt

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Welcome to the ATM Project!")
st.write("Use the sidebar to navigate to different sections!")
alt.themes.enable("dark")
