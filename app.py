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

    st.write(
        "Keywords:"
    )

    st.write(keywords)
for kw in keywords:

    url = (
        "https://api.openalex.org/works"
        f"?search={kw}"
        "&per-page=200"
    )
