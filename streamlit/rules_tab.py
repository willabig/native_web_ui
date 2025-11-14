import streamlit as st
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import csv
import os
from pathlib import Path
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="PhysiCell Rules Editor", layout="wide")

# Initialize session state
if 'rules_df' not in st.session_state:
    st.session_state.rules_df = pd.DataFrame(columns=[
        'Use', 'Cell Type', 'Signal', 'Direction', 'Behavior', 
        'Saturation Value', 'Half-max', 'Hill Power', 'Apply to Dead', 'Base Value'
    ])
if 'substrates' not in st.session_state:
    st.session_state.substrates = ['oxygen', 'glucose']
if 'cell_types' not in st.session_state:
    st.session_state.cell_types = ['default', 'cancer', 'immune']

# Helper functions
def hill_function(x, base_val=0.0, saturation_val=1.0, half_max=0.5, hill_power=2):
    """Calculate Hill function response"""
    z = (x / half_max) ** hill_power
    return base_val + (saturation_val - base_val) * (z / (1.0 + z))

def create_signal_list(substrates, cell_types):
    """Generate list of possible signals"""
    signal_l = []
    
    # Substrate-based signals
    for s in substrates:
        signal_l.extend([s, f"intracellular {s}", f"{s} gradient"])
    
    # Physical signals
    signal_l.extend(["pressure", "volume"])
    
    # Cell contact signals
    for ct in cell_types:
        signal_l.append(f"contact with {ct}")
    
    # Special signals
    signal_l.extend([
        "contact with live cell", "contact with dead cell", "contact with BM",
        "damage", "dead", "total attack time", "damage delivered", 
        "time", "apoptotic", "necrotic"
    ])
    
    return signal_l

def create_behavior_list(substrates, cell_types):
    """Generate list of possible behaviors"""
    behavior_l = []
    
    # Substrate behaviors
    for s in substrates:
        behavior_l.extend([
            f"{s} secretion", f"{s} secretion target",
            f"{s} uptake", f"{s} export"
        ])
    
    # Cycle behaviors
    behavior_l.append("cycle entry")
    for idx in range(6):
        behavior_l.append(f"exit from cycle phase {idx}")
    
    # Death and damage
    behavior_l.extend([
        "apoptosis", "necrosis", "attack damage rate", "attack duration",
        "damage rate", "damage repair rate"
    ])
    
    # Migration
    behavior_l.extend([
        "migration speed", "migration bias", "migration persistence time"
    ])
    
    # Chemotaxis
    for s in substrates:
        behavior_l.append(f"chemotactic response to {s}")
    
    # Adhesion
    behavior_l.extend([
        "cell-cell adhesion", "cell-cell adhesion elastic constant",
        "relative maximum adhesion distance", "cell-cell repulsion",
        "cell-BM adhesion", "cell-BM repulsion"
    ])
    
    # Cell type specific behaviors
    for ct in cell_types:
        behavior_l.append(f"adhesive affinity to {ct}")
    
    # Phagocytosis
    behavior_l.extend([
        "phagocytose apoptotic cell", "phagocytose necrotic cell",
        "phagocytose other dead cell"
    ])
    
    # Interaction behaviors
    for verb in ["phagocytose ", "attack ", "fuse to ", "transform to ", 
                 "immunogenicity to ", "asymmetric division to "]:
        for ct in cell_types:
            behavior_l.append(f"{verb}{ct}")
    
    # Attachment
    behavior_l.extend([
        "is_movable", "cell attachment rate", "cell detachment rate",
        "maximum number of cell attachments"
    ])
    
    return behavior_l

def load_csv_rules(file):
    """Load rules from CSV file"""
    try:
        # Read CSV, handling comments
        rules = []
        file.seek(0)
        content = file.read().decode('utf-8')
        
        for line in content.split('\n'):
            # Remove comments (lines starting with // or #)
            line = line.split('//')[0].split('#')[0].strip()
            if line:
                rules.append(line)
        
        # Parse CSV
        from io import StringIO
        csv_content = '\n'.join(rules)
        df = pd.read_csv(StringIO(csv_content), header=None, names=[
            'Cell Type', 'Signal', 'Direction', 'Behavior',
            'Saturation Value', 'Half-max', 'Hill Power', 'Apply to Dead'
        ])
        
        # Add Use and Base Value columns
        df.insert(0, 'Use', True)
        df['Base Value'] = '??'
        
        # Convert Apply to Dead to boolean
        df['Apply to Dead'] = df['Apply to Dead'].astype(int).astype(bool)
        
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return None

def save_csv_rules(df, filename):
    """Save rules to CSV file"""
    try:
        # Prepare data for CSV (exclude Use and Base Value columns)
        output_df = df[df['Use'] == True].copy()
        output_df = output_df[[
            'Cell Type', 'Signal', 'Direction', 'Behavior',
            'Saturation Value', 'Half-max', 'Hill Power', 'Apply to Dead'
        ]]
        
        # Convert boolean to int
        output_df['Apply to Dead'] = output_df['Apply to Dead'].astype(int)
        
        # Save to CSV
        output_df.to_csv(filename, index=False, header=False)
        return True
    except Exception as e:
        st.error(f"Error saving CSV: {str(e)}")
        return False

# Main UI
st.title("🔬 PhysiCell Rules Editor")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Rules enabled checkbox
    rules_enabled = st.checkbox("Enable Rules", value=True)
    
    st.divider()
    
    # File management
    st.subheader("File Management")
    rules_folder = st.text_input("Rules Folder", value="config")
    rules_file = st.text_input("Rules File", value="rules.csv")
    
    # Import rules
    uploaded_file = st.file_uploader("Import Rules CSV", type=['csv'])
    if uploaded_file is not None:
        loaded_df = load_csv_rules(uploaded_file)
        if loaded_df is not None:
            st.session_state.rules_df = loaded_df
            st.success("Rules loaded successfully!")
    
    # Save rules
    if st.button("💾 Save Rules", type="primary", use_container_width=True):
        filepath = os.path.join(rules_folder, rules_file)
        if save_csv_rules(st.session_state.rules_df, filepath):
            st.success(f"Rules saved to {filepath}")
    
    st.divider()
    
    # Data sources configuration
    st.subheader("Data Sources")
    
    # Substrates
    substrate_input = st.text_input("Substrates (comma-separated)", 
                                     value=",".join(st.session_state.substrates))
    st.session_state.substrates = [s.strip() for s in substrate_input.split(',') if s.strip()]
    
    # Cell types
    celltype_input = st.text_input("Cell Types (comma-separated)", 
                                    value=",".join(st.session_state.cell_types))
    st.session_state.cell_types = [c.strip() for c in celltype_input.split(',') if c.strip()]

# Main content area
tab1, tab2, tab3 = st.tabs(["📝 Add Rule", "📊 Rules Table", "📈 Plot Rules"])

# Tab 1: Add New Rule
with tab1:
    st.header("Add New Rule")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Signal")
        cell_type = st.selectbox("Cell Type", st.session_state.cell_types, key="new_cell_type")
        
        signal_list = create_signal_list(st.session_state.substrates, st.session_state.cell_types)
        signal = st.selectbox("Signal", signal_list, key="new_signal")
        
        direction = st.selectbox("Direction", ["increases", "decreases"], key="new_direction")
    
    with col2:
        st.subheader("Behavior")
        behavior_list = create_behavior_list(st.session_state.substrates, st.session_state.cell_types)
        behavior = st.selectbox("Behavior", behavior_list, key="new_behavior")
    
    st.divider()
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        base_value = st.number_input("Base Value", value=0.1, format="%.4f", key="new_base")
    
    with col4:
        saturation_value = st.number_input("Saturation Value", value=1.0, format="%.4f", key="new_sat")
    
    with col5:
        half_max = st.number_input("Half-max", value=0.5, format="%.4f", key="new_half")
    
    col6, col7 = st.columns(2)
    
    with col6:
        hill_power = st.number_input("Hill Power", value=4, min_value=1, key="new_hill")
    
    with col7:
        apply_to_dead = st.checkbox("Apply to Dead", key="new_dead")
    
    # Validation and add button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("➕ Add Rule", type="primary", use_container_width=True):
            # Validate saturation vs base value
            valid = True
            if direction == "increases" and saturation_value < base_value:
                st.error("Saturation value must be >= base value for 'increases'")
                valid = False
            elif direction == "decreases" and saturation_value > base_value:
                st.error("Saturation value must be <= base value for 'decreases'")
                valid = False
            
            if valid:
                new_rule = pd.DataFrame([{
                    'Use': True,
                    'Cell Type': cell_type,
                    'Signal': signal,
                    'Direction': direction,
                    'Behavior': behavior,
                    'Saturation Value': saturation_value,
                    'Half-max': half_max,
                    'Hill Power': hill_power,
                    'Apply to Dead': apply_to_dead,
                    'Base Value': base_value
                }])
                st.session_state.rules_df = pd.concat([st.session_state.rules_df, new_rule], 
                                                       ignore_index=True)
                st.success("Rule added!")
                st.rerun()
    
    with col_btn2:
        if st.button("📊 Plot New Rule", use_container_width=True):
            # Plot the new rule
            X = np.linspace(0.0, 2.0 * half_max, 101)
            Y = hill_function(X, base_val=base_value, saturation_val=saturation_value, 
                            half_max=half_max, hill_power=hill_power)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=X, y=Y, mode='lines', name='Response',
                                    line=dict(color='red', width=2)))
            
            fig.update_layout(
                title=f"New Rule: {cell_type}",
                xaxis_title=f"Signal: {signal}",
                yaxis_title=f"Response: {behavior}",
                hovermode='x unified',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Tab 2: Rules Table
with tab2:
    st.header("Current Rules")
    
    if len(st.session_state.rules_df) > 0:
        # Display editable dataframe
        edited_df = st.data_editor(
            st.session_state.rules_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Use": st.column_config.CheckboxColumn("Use", default=True),
                "Apply to Dead": st.column_config.CheckboxColumn("Apply to Dead"),
                "Saturation Value": st.column_config.NumberColumn("Saturation Value", format="%.4f"),
                "Half-max": st.column_config.NumberColumn("Half-max", format="%.4f"),
                "Hill Power": st.column_config.NumberColumn("Hill Power", format="%.1f"),
            }
        )
        
        st.session_state.rules_df = edited_df
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("🗑️ Clear All Rules", type="secondary"):
                st.session_state.rules_df = pd.DataFrame(columns=st.session_state.rules_df.columns)
                st.rerun()
        
        with col2:
            # Download as CSV
            csv = st.session_state.rules_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name="rules_export.csv",
                mime="text/csv"
            )
        
        st.info(f"Total rules: {len(st.session_state.rules_df)} | Active rules: {st.session_state.rules_df['Use'].sum()}")
    else:
        st.info("No rules defined yet. Add rules in the 'Add Rule' tab.")

# Tab 3: Plot Rules
with tab3:
    st.header("Visualize Rules")
    
    if len(st.session_state.rules_df) > 0:
        # Select rule to plot
        rule_options = [f"Rule {i+1}: {row['Cell Type']} - {row['Signal']} → {row['Behavior']}" 
                       for i, row in st.session_state.rules_df.iterrows()]
        
        selected_rule_idx = st.selectbox("Select Rule to Plot", 
                                         range(len(rule_options)), 
                                         format_func=lambda x: rule_options[x])
        
        if st.button("📈 Plot Selected Rule", type="primary"):
            rule = st.session_state.rules_df.iloc[selected_rule_idx]
            
            # Generate plot
            half_max_val = float(rule['Half-max'])
            X = np.linspace(0.0, 2.0 * half_max_val, 101)
            
            base_val = float(rule['Base Value']) if rule['Base Value'] != '??' else (
                1.0 if rule['Direction'] == 'decreases' else 0.0
            )
            
            Y = hill_function(X, 
                            base_val=base_val,
                            saturation_val=float(rule['Saturation Value']),
                            half_max=half_max_val,
                            hill_power=int(rule['Hill Power']))
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=X, y=Y, mode='lines', name='Response',
                                    line=dict(color='red', width=3)))
            
            # Add reference lines
            fig.add_hline(y=base_val, line_dash="dash", line_color="blue", 
                         annotation_text="Base Value")
            fig.add_hline(y=float(rule['Saturation Value']), line_dash="dash", 
                         line_color="green", annotation_text="Saturation Value")
            fig.add_vline(x=half_max_val, line_dash="dash", line_color="orange",
                         annotation_text="Half-max")
            
            fig.update_layout(
                title=f"Rule {selected_rule_idx+1}: {rule['Cell Type']}",
                xaxis_title=f"Signal: {rule['Signal']}",
                yaxis_title=f"Response: {rule['Behavior']}",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display rule details
            with st.expander("Rule Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Cell Type:** {rule['Cell Type']}")
                    st.write(f"**Signal:** {rule['Signal']}")
                    st.write(f"**Direction:** {rule['Direction']}")
                    st.write(f"**Behavior:** {rule['Behavior']}")
                with col2:
                    st.write(f"**Base Value:** {rule['Base Value']}")
                    st.write(f"**Saturation Value:** {rule['Saturation Value']}")
                    st.write(f"**Half-max:** {rule['Half-max']}")
                    st.write(f"**Hill Power:** {rule['Hill Power']}")
                    st.write(f"**Apply to Dead:** {'Yes' if rule['Apply to Dead'] else 'No'}")
        
        # Plot all rules comparison
        if st.checkbox("Show All Rules Comparison"):
            st.subheader("All Rules Overlay")
            
            fig_all = go.Figure()
            
            for idx, rule in st.session_state.rules_df.iterrows():
                if not rule['Use']:
                    continue
                    
                half_max_val = float(rule['Half-max'])
                X = np.linspace(0.0, 2.0 * half_max_val, 101)
                
                base_val = float(rule['Base Value']) if rule['Base Value'] != '??' else (
                    1.0 if rule['Direction'] == 'decreases' else 0.0
                )
                
                Y = hill_function(X, 
                                base_val=base_val,
                                saturation_val=float(rule['Saturation Value']),
                                half_max=half_max_val,
                                hill_power=int(rule['Hill Power']))
                
                fig_all.add_trace(go.Scatter(
                    x=X, y=Y, mode='lines',
                    name=f"Rule {idx+1}: {rule['Cell Type'][:10]}...",
                    line=dict(width=2)
                ))
            
            fig_all.update_layout(
                title="All Active Rules",
                xaxis_title="Signal Strength",
                yaxis_title="Response",
                hovermode='x unified',
                height=600
            )
            
            st.plotly_chart(fig_all, use_container_width=True)
    else:
        st.info("No rules to plot. Add some rules first!")

# Footer
st.divider()
st.caption("PhysiCell Rules Editor - Streamlit Version | Based on PhysiCell Studio")