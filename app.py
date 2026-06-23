import streamlit as st
import pandas as pd
import requests
import numpy as np
from io import BytesIO
import time
import re

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

st.header(
    "📚 iRATco Journal Miner"
)

keyword_input = st.text_input(
    "Keywords (separate by comma)",
    placeholder="osteoporosis, ovariectomy, stem cell"
)
if st.button(
    "🔍 Search Papers"
):

    keywords = [k.strip()
        for k in keyword_input.split(",")
        if k.strip()
    ]

for kw in keywords:

    url = (
        "https://api.openalex.org/works"
        f"?search={kw}"
        "&per-page=200"
    )
