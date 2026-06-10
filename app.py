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

    species_db = [
        "mouse",
        "mice",
        "rat",
        "rabbit",
        "dog",
        "cat",
        "cow",
        "pig",
        "horse",
        "human",
        "rhinoceros",
        "rhino",
        "elephant",
        "tiger"
    ]
    marker_db = [
        "vimentin",
        "fibronectin",
        "col1a1",
        "col3a1",
        "ki67",
        "pcna",
        "sox2",
        "oct4",
        "nanog",
        "cd73",
        "cd90",
        "cd105",
        "bax",
        "bcl2",
        "caspase",
        "tp53"
    ]
    analysis_db = [
        "qpcr",
        "rt-pcr",
        "rna-seq",
        "western blot",
        "immunohistochemistry",
        "immunocytochemistry",
        "flow cytometry",
        "elisa",
        "transcriptome"
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
        "adipose"
    ]
    species_count = {}

    for s in species_db:
    
        species_count[s] = combined_lower.count(s)
    
    species_df = pd.DataFrame({
    
        "Species":species_count.keys(),
        "Count":species_count.values()
    
    })
    
    species_df = species_df.sort_values(
        "Count",
        ascending=False
    )

    marker_count = {}

    for m in marker_db:
    
        marker_count[m] = combined_lower.count(m)
    
    marker_df = pd.DataFrame({
    
        "Marker":marker_count.keys(),
        "Count":marker_count.values()
    
    })
    
    marker_df = marker_df.sort_values(
        "Count",
        ascending=False
    )
    analysis_count = {}

    for a in analysis_db:
    
        analysis_count[a] = combined_lower.count(a)
    # ===============================
    # RESEARCH DESIGN
    # ===============================

    st.subheader(
        "Research Design Recommendation"
    )

    st.markdown(
        "### Research Question"
    )

    st.info(
        f"How does {query} affect biological processes and outcomes?"
    )

    st.markdown(
        "### Hypothesis"
    )

    st.info(
        f"{query} significantly influences cellular and molecular responses."
    )

    st.markdown(
        "### Suggested Species"
    )

    st.write(
        """
• Mouse

• Rat

• Rabbit

• Wildlife species
"""
    )

    st.markdown(
        "### Suggested Sampling"
    )

    st.write(
        """
• Blood

• Tissue biopsy

• Cell culture

• Fibroblast sample
"""
    )

    st.markdown(
        "### Suggested Biomarkers"
    )

    st.write(
        """
• Ki67

• PCNA

• Vimentin

• Fibronectin

• COL1A1
"""
    )

    st.markdown(
        "### Suggested Analyses"
    )

    st.write(
        """
• Histopathology

• Immunohistochemistry

• RT-qPCR

• RNA-seq

• Flow Cytometry
"""
    )

    st.markdown(
        "### Suggested Statistics"
    )

    st.write(
        """
• ANOVA

• T-test

• PCA

• Correlation Analysis
"""
    )

# ==================================
# HYPOTHESIS PATHWAY
# ==================================

st.subheader(
    "Hypothesis Pathway"
)

pathway_nodes = []
query = " ".join([
    keyword1,
    keyword2,
    keyword3
]).strip()

query_lower = query.lower()
query_lower = query.lower()

if "fibroblast" in query_lower:

    pathway_nodes.extend([
        "Skin Biopsy",
        "Fibroblast Isolation",
        "Cell Expansion",
        "Cryopreservation",
        "Cell Viability",
        "Gene Expression",
        "Conservation Outcome"
    ])

elif "stem" in query_lower:

    pathway_nodes.extend([
        "Stem Cell",
        "Differentiation",
        "Marker Expression",
        "Tissue Regeneration",
        "Biological Outcome"
    ])

elif "ipsc" in query_lower:

    pathway_nodes.extend([
        "Fibroblast",
        "Reprogramming",
        "iPSC",
        "Differentiation",
        "Functional Cells",
        "Conservation Application"
    ])

else:

    if "freq" in locals():

        top_terms = [
            w
            for w,c
            in freq.most_common(6)
        ]
    
    else:
    
        top_terms = [
            keyword1,
            keyword2,
            keyword3
        ]

    pathway_nodes = top_terms

G_path = nx.DiGraph()

for i in range(
    len(pathway_nodes)-1
):

    G_path.add_edge(
        pathway_nodes[i],
        pathway_nodes[i+1]
    )

fig, ax = plt.subplots(
    figsize=(12,4)
)

pos = {}

for i,node in enumerate(
    pathway_nodes
):

    pos[node] = (i,0)

nx.draw_networkx_nodes(
    G_path,
    pos,
    node_size=4000,
    node_color="lightblue",
    alpha=0.9
)

nx.draw_networkx_edges(
    G_path,
    pos,
    arrows=True,
    arrowsize=25,
    width=3
)

nx.draw_networkx_labels(
    G_path,
    pos,
    font_size=10,
    font_weight="bold"
)

ax.axis("off")

st.pyplot(fig)

st.subheader(
    "Mechanistic Hypothesis"
)

hypothesis_text = " → ".join(
    pathway_nodes
)

st.success(
    hypothesis_text
)
