import streamlit as st

st.set_page_config(
    page_title="Welcome Page",
    page_icon="👋",
)
st.markdown("# Welcome Page")
st.sidebar.markdown("# Welcome Page")

# Define the pages
page_1 = st.Page("page_1.py", title="Page 1", icon="❄️")
page_2 = st.Page("page_2.py", title="Page 2", icon="🎉")

# Set up navigation
pg = st.navigation([page_1, page_2])

# Run
pg.run()

st.write("Please select a page from the navigation to continue")
