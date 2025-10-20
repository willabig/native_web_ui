import streamlit as st

st.set_page_config(page_title="Config Basics")

# Main page content
st.markdown("# Config Basics")
st.sidebar.markdown("# Config Basics")

left, middle, right = st.columns(3, gap="medium", vertical_alignment="top", width="stretch")
left.text_input("Xmin", key="xmin")
middle.text_input("Xmax", key="xmax")
right.text_input("dx", key="dx")
