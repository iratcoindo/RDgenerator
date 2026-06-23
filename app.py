import streamlit as st
import pandas as pd
import requests
import fitz
import io

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

    if len(keywords) == 0:
        st.warning("Please enter at least one keyword.")
        st.stop()

    query = " ".join(keywords)

    url = (
        "https://api.openalex.org/works"
        f"?search={query}"
        "&per-page=200"
    )

    try:

        with st.spinner("Searching papers..."):

            r = requests.get(
                url,
                timeout=30
            )

            data = r.json()

            all_papers = []

            keywords_lower = [
                k.lower()
                for k in keywords
            ]

            for paper in data.get("results", []):

                title = paper.get(
                    "display_name",
                    ""
                )

                # reconstruct abstract
                abstract = ""

                if paper.get(
                    "abstract_inverted_index"
                ):

                    inv = paper[
                        "abstract_inverted_index"
                    ]

                    positions = {}

                    for word, inds in inv.items():
                        for i in inds:
                            positions[i] = word

                    abstract = " ".join(
                        positions[i]
                        for i in sorted(
                            positions.keys()
                        )
                    )

                text = (
                    title + " " + abstract
                ).lower()

                # semua keyword harus ada
                if not all(
                    kw in text
                    for kw in keywords_lower
                ):
                    continue

                doi = paper.get(
                    "doi",
                    ""
                )

                publisher = ""

                primary = paper.get(
                    "primary_location"
                )

                if primary:

                    source = primary.get(
                        "source"
                    )

                    if source:
                        publisher = source.get(
                            "display_name",
                            ""
                        )

                pdf_link = ""

                open_access = paper.get(
                    "open_access"
                )

                if open_access:
                    pdf_link = open_access.get(
                        "oa_url",
                        ""
                    )

                if pdf_link is None:
                    pdf_link = ""

                all_papers.append(
                    {
                        "Title": title,
                        "Publisher": publisher,
                        "DOI": doi,
                        "Download": pdf_link
                    }
                )

            df = pd.DataFrame(
                all_papers
            )

            if len(df) == 0:
                st.warning(
                    "No papers found."
                )

            else:

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
                # =======
                st.subheader("Method Extraction")

                paper_idx = st.selectbox(
                    "Select Paper",
                    df.index,
                    format_func=lambda x:
                        df.loc[x, "Title"]
                )
                
                if st.button("Extract Methods"):
                
                    pdf_url = df.loc[
                        paper_idx,
                        "Download"
                    ]
                
                    if pdf_url == "":
                        st.error(
                            "No PDF link available."
                        )
                        st.stop()
                
                    try:
                
                        with st.spinner(
                            "Downloading PDF..."
                        ):
                
                            r = requests.get(
                                pdf_url,
                                timeout=60
                            )
                
                            pdf = fitz.open(
                                stream=r.content,
                                filetype="pdf"
                            )
                
                            full_text = ""
                
                            for page in pdf:
                                full_text += (
                                    page.get_text()
                                    + "\n"
                                )
                
                        st.success(
                            "PDF downloaded."
                        )
                
                        st.session_state[
                            "paper_text"
                        ] = full_text
                
                    except Exception as e:
                        st.error(e)

                if "paper_text" in st.session_state:

                    text = st.session_state[
                        "paper_text"
                    ]
                
                    lower = text.lower()
                
                    headers = [
                        "materials and methods",
                        "materials & methods",
                        "methods",
                        "methodology",
                        "experimental design",
                        "animal experiments"
                    ]
                
                    start = -1
            
                for h in headers:
            
                    pos = lower.find(h)
            
                    if pos != -1:
                        start = pos
                        break
            
                if start != -1:
            
                    end = len(text)
            
                    next_headers = [
                        "results",
                        "discussion",
                        "conclusion",
                        "references"
                    ]
            
                    for h in next_headers:
            
                        pos = lower.find(
                            h,
                            start + 100
                        )
            
                        if (
                            pos != -1
                            and
                            pos < end
                        ):
                            end = pos
            
                    methods_text = text[
                        start:end
                    ]
            
                    st.subheader(
                        "Methods Section"
                    )
            
                    st.text_area(
                        "",
                        methods_text,
                        height=500
                    )
            
                    st.session_state[
                        "methods_text"
                    ] = methods_text
                if "methods_text" in st.session_state:

                    methods = st.session_state[
                        "methods_text"
                    ]
                
                    info = []
                
                    keywords = {
                        "Species":[
                            "rat",
                            "mouse",
                            "rabbit",
                            "guinea pig",
                            "macaque"
                        ],
                
                        "Strain":[
                            "sprague dawley",
                            "wistar",
                            "c57bl/6",
                            "balb/c"
                        ],
                
                        "Histology":[
                            "hematoxylin",
                            "eosin",
                            "masson",
                            "pas"
                        ],
                
                        "Methods":[
                            "elisa",
                            "western blot",
                            "qpcr",
                            "immunohistochemistry",
                            "immunofluorescence",
                            "flow cytometry"
                        ]
                    }
                
                    lower = methods.lower()
                
                    for cat, words in keywords.items():
                
                        found = []
                
                        for w in words:
                
                            if w in lower:
                                found.append(w)
                
                        info.append(
                            {
                                "Category": cat,
                                "Information":
                                ", ".join(found)
                            }
                        )
                
                    result_df = pd.DataFrame(
                        info
                    )
                
                    st.subheader(
                        "Experimental Information"
                    )
                
                    st.dataframe(
                        result_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
            
                    st.warning(
                        "Methods section not found."
                    )

                # =======

                csv = df.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    "📥 Download CSV",
                    csv,
                    file_name="journal_miner.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(
            f"Error: {e}"
        )
