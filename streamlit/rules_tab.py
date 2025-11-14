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
if 'num_rules' not in st.session_state:
    st.session_state.num_rules = 0
if 'plot_window_open' not in st.session_state:
    st.session_state.plot_window_open = False

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

def strip_comments(lines):
    """Strip comments from CSV lines"""
    for line in lines:
        raw = line.split('//')[0].split('#')[0].strip()
        if raw:
            yield raw

def load_csv_rules(file):
    """Load rules from CSV file"""
    try:
        file.seek(0)
        content = file.read().decode('utf-8')
        lines = content.split('\n')
        
        rules = []
        for line in strip_comments(lines):
            if line:
                rules.append(line)
        
        from io import StringIO
        csv_content = '\n'.join(rules)
        
        df = pd.read_csv(StringIO(csv_content), header=None, names=[
            'Cell Type', 'Signal', 'Direction', 'Behavior',
            'Saturation Value', 'Half-max', 'Hill Power', 'Apply to Dead'
        ])
        
        df.insert(0, 'Use', True)
        df['Base Value'] = '??'
        df['Apply to Dead'] = df['Apply to Dead'].astype(int).astype(bool)
        
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return None

def save_csv_rules(df, filepath):
    """Save rules to CSV file"""
    try:
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            for idx, row in df.iterrows():
                if not row['Use']:
                    continue
                
                rule_parts = [
                    str(row['Cell Type']),
                    str(row['Signal']),
                    str(row['Direction']),
                    str(row['Behavior']),
                    str(row['Saturation Value']),
                    str(row['Half-max']),
                    str(int(row['Hill Power'])),
                    str(1 if row['Apply to Dead'] else 0)
                ]
                f.write(','.join(rule_parts) + '\n')
        
        return True
    except Exception as e:
        st.error(f"Error saving CSV: {str(e)}")
        return False

# Custom CSS to match original styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .add-rule-btn button {
        background-color: #90EE90 !important;
    }
    .plot-btn button {
        background-color: #90EE90 !important;
    }
    .save-btn button {
        background-color: #FFFF00 !important;
        color: black !important;
    }
    .delete-btn button {
        background-color: #FFFF00 !important;
        color: black !important;
    }
    .section-header {
        text-align: center;
        font-size: 16px;
        font-weight: bold;
        border-bottom: 1px solid #ccc;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("Rules")

# Top section - Cell Type selection and buttons
col_top1, col_top2, col_top3, col_top4 = st.columns([2, 2, 1, 1])

with col_top1:
    st.markdown("**Cell Type**")
    cell_type = st.selectbox("Cell Type", st.session_state.cell_types, label_visibility="collapsed", key="cell_type_select")

with col_top2:
    st.write("")  # spacing

with col_top3:
    st.write("")
    st.markdown('<div class="add-rule-btn">', unsafe_allow_html=True)
    add_rule_btn = st.button("Add rule", key="add_rule_main")
    st.markdown('</div>', unsafe_allow_html=True)

with col_top4:
    st.write("")
    st.markdown('<div class="plot-btn">', unsafe_allow_html=True)
    plot_new_rule_btn = st.button("Plot", key="plot_new_rule")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Signal and Behavior sections side by side
col_left, col_right = st.columns([1, 1])

with col_left:
    # Signal section
    st.markdown('<div class="section-header">----- Signal -----</div>', unsafe_allow_html=True)
    
    signal_list = create_signal_list(st.session_state.substrates, st.session_state.cell_types)
    signal = st.selectbox("Signal", signal_list, label_visibility="collapsed", key="signal_select")
    
    st.write("")
    st.write("")
    
    # Base value (read-only style)
    st.markdown("**Base value**")
    base_value = st.text_input("Base value", value="0.1", disabled=True, label_visibility="collapsed", key="base_val")
    
    st.write("")
    
    # Half-max and Saturation value
    col_hm, col_sat = st.columns(2)
    with col_hm:
        st.markdown("**Half-max**")
        half_max = st.number_input("Half-max", value=0.5, format="%.4f", label_visibility="collapsed", key="half_max")
    
    with col_sat:
        st.markdown("**Saturation value**")
        saturation_value = st.number_input("Saturation value", value=1.0, format="%.4f", label_visibility="collapsed", key="sat_val")
    
    st.write("")
    
    # Hill power and Apply to dead
    col_hp, col_dead = st.columns(2)
    with col_hp:
        st.markdown("**Hill power**")
        hill_power = st.number_input("Hill power", value=4, min_value=1, label_visibility="collapsed", key="hill_power")
    
    with col_dead:
        st.write("")
        apply_to_dead = st.checkbox("apply to dead", key="apply_dead")

with col_right:
    # Behavior section
    col_beh_header, col_direction = st.columns([2, 1])
    
    with col_beh_header:
        st.markdown('<div class="section-header">----- Behavior -----</div>', unsafe_allow_html=True)
    
    with col_direction:
        direction = st.selectbox("", ["increases", "decreases"], label_visibility="collapsed", key="direction_select")
    
    behavior_list = create_behavior_list(st.session_state.substrates, st.session_state.cell_types)
    behavior = st.selectbox("Behavior", behavior_list, label_visibility="collapsed", key="behavior_select")
    
    st.write("")
    st.write("")
    
    # Rules enabled and Save section
    st.markdown("**Enable rules:**")
    rules_enabled = st.checkbox("", value=True, label_visibility="collapsed", key="rules_enabled")
    
    st.info("Make sure to save rules below before running simulations!")
    
    col_save1, col_save2, col_save3 = st.columns([1, 2, 2])
    
    with col_save1:
        st.markdown('<div class="save-btn">', unsafe_allow_html=True)
        save_btn = st.button("Save", key="save_rules")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_save2:
        rules_folder = st.text_input("to:", value="config", label_visibility="collapsed", key="rules_folder")
    
    with col_save3:
        rules_file = st.text_input("file", value="rules.csv", label_visibility="collapsed", key="rules_file")
    
    # Import button
    st.markdown('<div class="save-btn">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Import", type=['csv'], key="import_rules", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        loaded_df = load_csv_rules(uploaded_file)
        if loaded_df is not None:
            st.session_state.rules_df = loaded_df
            st.session_state.num_rules = len(loaded_df)
            st.success("Rules imported successfully!")
            st.rerun()

st.divider()

# Rules Table
st.markdown("### Rules Table")

if len(st.session_state.rules_df) > 0:
    # Display the table
    edited_df = st.data_editor(
        st.session_state.rules_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Use": st.column_config.CheckboxColumn("Use", default=True, width="small"),
            "Cell Type": st.column_config.TextColumn("CellType", width="medium"),
            "Signal": st.column_config.TextColumn("Signal", width="large"),
            "Direction": st.column_config.TextColumn("Direction", width="small"),
            "Behavior": st.column_config.TextColumn("Behavior", width="large"),
            "Saturation Value": st.column_config.NumberColumn("Saturation value", format="%.4f", width="small"),
            "Half-max": st.column_config.NumberColumn("Half-max", format="%.4f", width="small"),
            "Hill Power": st.column_config.NumberColumn("Hill power", format="%.0f", width="small"),
            "Apply to Dead": st.column_config.CheckboxColumn("Apply to dead", width="small"),
            "Base Value": st.column_config.TextColumn("Base value", width="small"),
        },
        hide_index=True,
        key="rules_table"
    )
    
    st.session_state.rules_df = edited_df
    st.session_state.num_rules = len(edited_df)
else:
    st.info("No rules defined. Use 'Add rule' button to create rules.")

st.write("")

# Action buttons below table
col_act1, col_act2, col_act3, col_act4 = st.columns([2, 2, 2, 6])

with col_act1:
    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
    if st.button("Delete rule", key="delete_rule"):
        if len(st.session_state.rules_df) > 0:
            st.session_state.rules_df = st.session_state.rules_df.iloc[:-1]
            st.session_state.num_rules = len(st.session_state.rules_df)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_act2:
    st.markdown('<div class="plot-btn">', unsafe_allow_html=True)
    plot_rule_btn = st.button("Plot rule", key="plot_selected_rule")
    st.markdown('</div>', unsafe_allow_html=True)

with col_act3:
    st.markdown('<div class="plot-btn">', unsafe_allow_html=True)
    plot_rules_btn = st.button("Plot rules", key="plot_all_rules")
    st.markdown('</div>', unsafe_allow_html=True)

with col_act4:
    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
    if st.button("Clear table", key="clear_table"):
        st.session_state.rules_df = pd.DataFrame(columns=st.session_state.rules_df.columns)
        st.session_state.num_rules = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Handle Add Rule button
if add_rule_btn:
    # Validation
    valid = True
    base_val_float = float(base_value)
    
    if direction == "increases" and saturation_value < base_val_float:
        st.error(f"Error: Behavior {behavior} cannot be increased with the given [Saturation value]. [Saturation value] must be greater than [Base value].")
        valid = False
    elif direction == "decreases" and saturation_value > base_val_float:
        st.error(f"Error: Behavior {behavior} cannot be decreased with the given [Saturation value]. [Saturation value] must be lower than [Base value].")
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
        st.session_state.rules_df = pd.concat([st.session_state.rules_df, new_rule], ignore_index=True)
        st.session_state.num_rules = len(st.session_state.rules_df)
        st.success("Rule added!")
        st.rerun()

# Handle Plot New Rule button
if plot_new_rule_btn:
    st.markdown("---")
    st.markdown("### Rule Plot")
    
    base_val_float = float(base_value)
    X = np.linspace(0.0, 2.0 * half_max, 101)
    Y = hill_function(X, base_val=base_val_float, saturation_val=saturation_value, 
                    half_max=half_max, hill_power=hill_power)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=X, y=Y, mode='lines', name='Response',
                            line=dict(color='red', width=2)))
    
    fig.update_layout(
        title=f"[New rule] cell type: {cell_type}",
        xaxis_title=f"signal: {signal}",
        yaxis_title=f"response: {behavior}",
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Handle Plot Selected Rule button
if plot_rule_btn:
    if len(st.session_state.rules_df) > 0:
        st.markdown("---")
        st.markdown("### Rule Plot")
        
        # Use last rule as selected (simplified - could add selection mechanism)
        irow = len(st.session_state.rules_df) - 1
        rule = st.session_state.rules_df.iloc[irow]
        
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
                                line=dict(color='red', width=2)))
        
        fig.update_layout(
            title=f"Rule {irow+1}: cell type: {rule['Cell Type']}",
            xaxis_title=f"signal: {rule['Signal']}",
            yaxis_title=f"response: {rule['Behavior']}",
            hovermode='x unified',
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("You need to select a row in the table")

# Handle Plot All Rules button
if plot_rules_btn:
    if len(st.session_state.rules_df) > 0:
        st.markdown("---")
        st.markdown("### All Rules Plot")
        
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
                name=f"{rule['Cell Type']}: {rule['Signal']} → {rule['Behavior']}"[:50],
                line=dict(width=2)
            ))
        
        fig_all.update_layout(
            title="All Active Rules",
            xaxis_title="Signal",
            yaxis_title="Response",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig_all, use_container_width=True)
    else:
        st.info("No rules to plot")

# Handle Save button
if save_btn:
    filepath = os.path.join(rules_folder, rules_file)
    if save_csv_rules(st.session_state.rules_df, filepath):
        st.success(f"Rules saved to {filepath}")