import altair as alt
import streamlit as st

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Page title
st.title("Welcome to the ATM Project!")
# Enable Altair dark theme
alt.themes.enable("dark")

# Add markdown text for objectives
st.markdown(
    """
## Objectives

- Show statistics about the separation between flights and whether or not the separation requirements are fulfilled:
    - Radar
    - Wake
    - Letter of Agreement
- Show statistics of the position and corrected altitude when the departure (from 24L) starts turning.
- Show whether radial 234 is crossed when departing.
- Show IAS of departures at 850, 1500, and 3500 ft for both runways.
- Altitude corrected and IAS of traffic at threshold when departing at 24L and 06R.
- Horizontal (stereographical) distance from departures to TMR-40 when departing from 24L.
"""
)

st.write(
    "On the left sidebar, you can navigate to the different sections of the project to view the statistics and visualizations."
)
