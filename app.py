import streamlit as st
import requests
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import plotly.express as px
import re

from collections import Counter
from itertools import combinations
from wordcloud import WordCloud
from community import community_louvain

# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="iRATco Research Design Generator",
    page_icon="📚",
    layout="wide"
)

st.title("📚 iRATco Research Design Generator")

st.write(
    "Literature Review + Research Design Recommendation"
)

# ==================================
# INPUT
# ==================================

keyword1 = st.text_input("Keyword 1")
keyword2 = st.text_input("Keyword 2")
keyword3 = st.text_input("Keyword 3")

n_articles = st.slider(
    "Number of Articles",
    20,
    200,
    50
)

# ==================================
# FUNCTIONS
# ==================================

def reconstruct_abstract(inv):

    if not inv:
        return ""

    words = []

    for word, positions in inv.items():

        for pos in positions:

            words.append((pos, word))

    words.sort()

    return " ".join(
        word for pos, word in words
    )

# ==================================
# SEARCH
# ==================================

if st.button("Search Literature"):

    query = " ".join(
        [
            keyword1,
            keyword2,
            keyword3
        ]
    ).strip()

    if len(query) == 0:

        st.warning(
            "Please enter at least one keyword."
        )

        st.stop()

    url = (
        "https://api.openalex.org/works"
        f"?search={query}"
        f"&per-page={n_articles}"
    )

    with st.spinner("Searching OpenAlex..."):

        r = requests.get(
            url,
            timeout=30
        )

    if r.status_code != 200:

        st.error(
            f"OpenAlex Error: {r.status_code}"
        )

        st.stop()

    results = r.json()["results"]

    # ===============================
    # BUILD DATAFRAME
    # ===============================

    records = []

    all_abstracts = []

    for paper in results:

        title = paper.get(
            "title",
            ""
        )

        year = paper.get(
            "publication_year",
            ""
        )

        citations = paper.get(
            "cited_by_count",
            0
        )

        journal = ""

        if paper.get(
            "primary_location"
        ):

            source = paper[
                "primary_location"
            ].get(
                "source"
            )

            if source:

                journal = source.get(
                    "display_name",
                    ""
                )

        abstract = reconstruct_abstract(
            paper.get(
                "abstract_inverted_index"
            )
        )

        all_abstracts.append(
            abstract
        )

        records.append({

            "Title": title,
            "Year": year,
            "Journal": journal,
            "Citations": citations,
            "Abstract": abstract

        })

    df = pd.DataFrame(records)

    # ===============================
    # TABLE
    # ===============================

    st.subheader(
        "Literature Table"
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    # ===============================
    # DOWNLOAD
    # ===============================

    csv = df.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    st.download_button(
        "⬇ Download CSV",
        csv,
        "literature.csv",
        "text/csv"
    )

    # ===============================
    # SUMMARY
    # ===============================

    st.subheader(
        "Literature Summary"
    )

    combined = " ".join(
        all_abstracts
    )

    summary = " ".join(
        combined.split()[:1000]
    )

    st.text_area(
        "Summary",
        summary,
        height=300
    )

    # ===============================
    # PUBLICATION TREND
    # ===============================

    st.subheader(
        "Publication Trend"
    )

    trend = (
        df.groupby("Year")
        .size()
        .reset_index(
            name="Count"
        )
    )

    fig = px.line(
        trend,
        x="Year",
        y="Count",
        markers=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ===============================
    # TOP JOURNALS
    # ===============================

    st.subheader(
        "Top Journals"
    )

    st.bar_chart(
        df["Journal"]
        .value_counts()
        .head(10)
    )

    # ===============================
    # KEYWORDS
    # ===============================

    text = " ".join(
        df["Title"].fillna("")
        + " "
        + df["Abstract"].fillna("")
    )

    words = re.findall(
        r"[A-Za-z]+",
        text.lower()
    )

    stopwords = {

        "the","and","for",
        "with","from","that",
        "this","were","have",
        "been","using","into",
        "study","studies",
        "research","review",
        "paper","article",
        "also","more",
        "based","recent"

    }

    keywords = [

        w

        for w in words

        if len(w) > 4
        and w not in stopwords

    ]

    freq = Counter(
        keywords
    )

    # ===============================
    # WORD CLOUD
    # ===============================

    st.subheader(
        "Word Cloud"
    )

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white"
    ).generate(
        " ".join(keywords)
    )

    fig, ax = plt.subplots(
        figsize=(12,6)
    )

    ax.imshow(wc)

    ax.axis("off")

    st.pyplot(fig)

    # ===============================
    # NETWORK
    # ===============================

    st.subheader(
        "Keyword Network"
    )

    top_words = [

        w

        for w,c

        in freq.most_common(20)

    ]

    G = nx.Graph()

    for abstract in df["Abstract"]:

        abs_words = re.findall(
            r"[A-Za-z]+",
            str(abstract).lower()
        )

        abs_words = [

            w

            for w in abs_words

            if w in top_words

        ]

        for a,b in combinations(
            set(abs_words),
            2
        ):

            if G.has_edge(a,b):

                G[a][b]["weight"] += 1

            else:

                G.add_edge(
                    a,
                    b,
                    weight=1
                )

    partition = community_louvain.best_partition(
        G
    )

    centrality = nx.eigenvector_centrality(
        G,
        max_iter=1000
    )

    pos = nx.spring_layout(
        G,
        seed=42
    )

    fig, ax = plt.subplots(
        figsize=(10,8)
    )

    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=[
            5000*centrality[n]
            for n in G.nodes()
        ],
        node_color=[
            partition[n]
            for n in G.nodes()
        ],
        cmap=plt.cm.Set3
    )

    nx.draw_networkx_edges(
        G,
        pos,
        alpha=0.3
    )

    nx.draw_networkx_labels(
        G,
        pos,
        font_size=8
    )

    ax.axis("off")

    st.pyplot(fig)

    # ===============================
    # CENTRALITY
    # ===============================

    st.subheader(
        "Centrality Ranking"
    )

    central_df = pd.DataFrame({

        "Keyword":
        list(
            centrality.keys()
        ),

        "Centrality":
        list(
            centrality.values()
        )

    })

    central_df = central_df.sort_values(
        "Centrality",
        ascending=False
    )

    st.dataframe(
        central_df.head(20)
    )

    # ===============================
    # RESEARCH GAPS
    # ===============================

    st.subheader(
        "Potential Research Gaps"
    )

    gaps = freq.most_common()[-15:]

    for word,count in gaps:

        st.write(
            f"• {word}"
        )

    # ==========================================
    # LITERATURE MINING
    # ==========================================
    
    st.subheader(
        "Literature-derived Research Components"
    )
    
    combined_lower = combined.lower()
    
    species_db = [
        "mouse","mice","rat","rabbit",
        "dog","cat","cow","cattle",
        "horse","pig","human",
        "rhinoceros","rhino",
        "elephant","tiger",
        "buffalo","goat","sheep"
    ]
    
    marker_db = [
    
        "vimentin",
        "fibronectin",
        "col1a1",
        "col3a1",
        "ki67",
        "pcna",
        "oct4",
        "sox2",
        "nanog",
        "klf4",
        "cd73",
        "cd90",
        "cd105",
        "bax",
        "bcl2",
        "caspase",
        "tp53",
        "myod",
        "myogenin"
    
    ]
    
    analysis_db = [
    
        "qpcr",
        "rt-pcr",
        "rt qpcr",
        "rna-seq",
        "western blot",
        "immunohistochemistry",
        "immunocytochemistry",
        "flow cytometry",
        "elisa",
        "transcriptome",
        "sequencing"
    
    ]
    
    sample_db = [
    
        "blood",
        "serum",
        "plasma",
        "skin",
        "ear",
        "biopsy",
        "fibroblast",
        "bone marrow",
        "adipose",
        "tissue"
    
    ]
    
    def mine_terms(database):
    
        counts = {}
    
        for item in database:
    
            counts[item] = combined_lower.count(item)
    
        df_tmp = pd.DataFrame({
            "Term": counts.keys(),
            "Count": counts.values()
        })
    
        df_tmp = (
            df_tmp[df_tmp["Count"] > 0]
            .sort_values(
                "Count",
                ascending=False
            )
        )
    
        return df_tmp
    
    species_df = mine_terms(species_db)
    marker_df = mine_terms(marker_db)
    analysis_df = mine_terms(analysis_db)
    sample_df = mine_terms(sample_db)

    col1,col2 = st.columns(2)

    with col1:
    
        st.markdown(
            "### Species Most Frequently Used"
        )
    
        st.dataframe(
            species_df.head(10)
        )
    
    with col2:
    
        st.markdown(
            "### Biomarkers Most Frequently Used"
        )
    
        st.dataframe(
            marker_df.head(10)
        )
    
    st.markdown(
        "### Analytical Methods"
    )
    
    st.dataframe(
        analysis_df.head(10)
    )
    
    st.markdown(
        "### Sampling Types"
    )
    
    st.dataframe(
        sample_df.head(10)
    )
    # ===============================
    # RESEARCH DESIGN
    # ===============================

    st.subheader(
        "Research Design Recommendation"
    )
    
    top_species = species_df.head(5)
    top_marker = marker_df.head(10)
    top_analysis = analysis_df.head(10)
    top_sample = sample_df.head(10)
    
    st.markdown(
        "### Recommended Species"
    )
    
    for s in top_species["Term"]:
    
        st.write(
            f"• {s}"
        )
    
    st.markdown(
        "### Recommended Sampling"
    )
    
    for s in top_sample["Term"]:
    
        st.write(
            f"• {s}"
        )
    
    st.markdown(
        "### Recommended Biomarkers"
    )
    
    for s in top_marker["Term"]:
    
        st.write(
            f"• {s}"
        )
    
    st.markdown(
        "### Recommended Analytical Methods"
    )
    
    for s in top_analysis["Term"]:
    
        st.write(
            f"• {s}"
        )
