import streamlit as st
import pandas as pd
import requests

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
