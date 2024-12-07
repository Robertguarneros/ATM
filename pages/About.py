import streamlit as st

# Streamlit page configuration
st.set_page_config(
    page_title="ATM Project",
    page_icon="assets/logo_eurocontrol.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Page title
st.markdown(
    """
# About the ATM Project
This project was developed for PGTA in QT-2024 by Group 8:
- Roberto Guarneros
- Angela Nuñez
- David Gracia

For more information visit the [GitHub repository](https://github.com/Robertguarneros/ATM.git)
"""
)
