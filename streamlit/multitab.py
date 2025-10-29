import streamlit as st

st.title("My Tabbed Dashboard")

# Create the tabs
tab1, tab2, tab3 = st.tabs(["Dashboard", "Data", "About"])

with tab1:
    st.header("Dashboard")
    st.write("This tab contains a chart.")
    st.line_chart([1, 5, 2, 6, 3])

with tab2:
    st.header("Raw Data")
    st.write("This tab shows some raw data.")
    st.dataframe({"Column 1": [1, 2, 3], "Column 2": [4, 5, 6]})

with tab3:
    st.header("About This App")
    st.write("This app demonstrates a simple tabbed layout using `st.tabs()`.")

