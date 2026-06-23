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

st.header("📚 iRATco Journal Miner")

keyword_input = st.text_input(
    "Keywords (separate by comma)",
    placeholder="osteoporosis, ovariectomy, stem cell"
)

if st.button("🔍 Search Papers"):

    keywords = [
        k.strip()
        for k in keyword_input.split(",")
        if k.strip()
    ]

    query = " ".join(keywords)

    if len(keywords) == 0:
        st.warning("Please enter at least one keyword.")
        st.stop()

    all_papers = []

    progress = st.progress(0)

    query = " ".join(keywords)

    url = (
        "https://api.openalex.org/works"
        f"?search={query}"
        "&per-page=200"
    )
    
    r = requests.get(url, timeout=30)
    data = r.json()

        try:
            r = requests.get(url, timeout=30)
            data = r.json()

            for paper in data["results"]:

                title = paper.get(
                    "display_name",
                    ""
                )

                doi = paper.get(
                    "doi",
                    ""
                )

                publisher = ""

                if (
                    "primary_location"
                    in paper
                    and paper["primary_location"]
                ):

                    source = (
                        paper["primary_location"]
                        .get("source")
                    )

                    if source:
                        publisher = source.get(
                            "display_name",
                            ""
                        )

                pdf_link = ""

                if (
                    "open_access"
                    in paper
                    and paper["open_access"]
                ):
                    pdf_link = (
                        paper["open_access"]
                        .get("oa_url", "")
                    )

                if pdf_link is None:
                    pdf_link = ""

                all_papers.append(
                    {
                        "Keyword": kw,
                        "Title": title,
                        "Publisher": publisher,
                        "DOI": doi,
                        "Download": pdf_link
                    }
                )

        except Exception as e:
            st.error(
                f"Error searching '{kw}': {e}"
            )

    df = pd.DataFrame(
        all_papers
    )

    if len(df) > 0:

        df = df.drop_duplicates(
            subset=["DOI"]
        )

        st.success(
            f"{len(df)} papers found."
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download CSV",
            csv,
            file_name="journal_miner.csv",
            mime="text/csv"
        )

    else:
        st.warning(
            "No papers found."
        )
