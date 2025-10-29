import streamlit as st

#st.title("My Tabbed Dashboard")

# Create the tabs
config_tab, microenv_tab, celltypes_tab, userparams_tab, rules_tab, run_tab, plot_tab = st.tabs(["Config Basics", "Microenv", "Cell Types", "User Params", "Rules", "Run", "Plot"])

with config_tab:
    st.header("Config Basics")
    st.write("This tab contains a chart.")
    st.line_chart([1, 5, 2, 6, 3])

with plot_tab:
    st.header("Plot results")
    st.write("This tab shows some raw data.")
    st.dataframe({"Column 1": [1, 2, 3], "Column 2": [4, 5, 6]})


