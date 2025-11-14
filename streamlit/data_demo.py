import streamlit as st
import pandas as pd
import plotly.express as px
import xml.etree.ElementTree as ET

st.title("Multi-Format Data Plotter")

uploaded_file = st.file_uploader("Upload file", type=['csv', 'xml'])

if uploaded_file:
    try:
        # Read based on file type
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xml'):
            # Try pandas first
            try:
                df = pd.read_xml(uploaded_file)
            except:
                # Fallback to ElementTree
                uploaded_file.seek(0)  # Reset file pointer
                tree = ET.parse(uploaded_file)
                root = tree.getroot()
                
                data = []
                for child in root:
                    row = {elem.tag: elem.text for elem in child}
                    data.append(row)
                df = pd.DataFrame(data)
        
        st.success(f"Loaded {len(df)} rows")
        st.dataframe(df.head())
        
        # Convert to numeric where possible
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
        
        # Plotting
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            st.subheader("Create Plot")
            plot_type = st.selectbox("Plot type", ["Line", "Bar", "Scatter"])
            y_col = st.selectbox("Y axis", numeric_cols)
            
            if plot_type == "Line":
                st.line_chart(df[y_col])
            elif plot_type == "Bar":
                st.bar_chart(df[y_col])
            elif plot_type == "Scatter" and len(numeric_cols) >= 2:
                x_col = st.selectbox("X axis", numeric_cols)
                fig = px.scatter(df, x=x_col, y=y_col)
                st.plotly_chart(fig)
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.write("Please check your XML structure")