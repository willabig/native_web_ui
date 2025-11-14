import streamlit as st

st.set_page_config(
    page_title="Welcome Page",
    page_icon="👋",
)
st.markdown("# Welcome Page")
st.sidebar.markdown("# Welcome Page")

# Define the pages
page_1 = st.Page("pages/page_1.py", title="Page 1")
page_2 = st.Page("pages/page_2.py", title="Page 2")
page_3 = st.Page("pages/page_3.py", title="Page 2")

# Set up navigation
pg = st.navigation([page_1, page_2, page_3])

# Run
pg.run()

st.write("Please select a page from the navigation to continue")
