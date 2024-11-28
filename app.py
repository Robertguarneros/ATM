import streamlit as st
import numpy as np


st.title("ATM Project")
dataframe = np.random.randn(10, 20)
st.dataframe(dataframe)
