import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import copy
import random
import string

# Page configuration
st.set_page_config(page_title="Cell Definitions", layout="wide")

# Initialize session state
if 'param_d' not in st.session_state:
    st.session_state.param_d = {}
if 'current_cell_def' not in st.session_state:
    st.session_state.current_cell_def = None
if 'substrate_list' not in st.session_state:
    st.session_state.substrate_list = ['oxygen', 'glucose']
if 'master_custom_var_d' not in st.session_state:
    st.session_state.master_custom_var_d = {}

# Helper functions
def random_name(prefix, num_chars=3):
    """Generate random name with prefix"""
    letters = string.ascii_lowercase
    rstring = ''.join(random.choice(letters) for i in range(num_chars))
    return prefix + rstring

def init_default_cycle_params(cdname):
    """Initialize default cycle parameters"""
    st.session_state.param_d[cdname]['cycle_choice_idx'] = 0
    st.session_state.param_d[cdname]['cycle_live_00_trate'] = '0.00072'
    st.session_state.param_d[cdname]['cycle_duration_flag'] = False

def init_default_death_params(cdname):
    """Initialize default death parameters"""
    st.session_state.param_d[cdname]['apoptosis_death_rate'] = '5.31667e-05'
    st.session_state.param_d[cdname]['apoptosis_01_duration'] = '516'
    st.session_state.param_d[cdname]['apoptosis_unlysed_rate'] = '0.05'
    st.session_state.param_d[cdname]['necrosis_death_rate'] = '0.0'
    st.session_state.param_d[cdname]['necrosis_01_duration'] = '86400'

def init_default_volume_params(cdname):
    """Initialize default volume parameters"""
    st.session_state.param_d[cdname]['volume_total'] = '2494'
    st.session_state.param_d[cdname]['volume_fluid_fraction'] = '0.75'
    st.session_state.param_d[cdname]['volume_nuclear'] = '540'
    st.session_state.param_d[cdname]['volume_fluid_change_rate'] = '0.05'
    st.session_state.param_d[cdname]['volume_cytoplasmic_rate'] = '0.0045'
    st.session_state.param_d[cdname]['volume_nuclear_rate'] = '0.0055'

def init_default_mechanics_params(cdname):
    """Initialize default mechanics parameters"""
    st.session_state.param_d[cdname]['mechanics_adhesion'] = '0.4'
    st.session_state.param_d[cdname]['mechanics_repulsion'] = '10.0'
    st.session_state.param_d[cdname]['mechanics_adhesion_distance'] = '1.25'
    st.session_state.param_d[cdname]['cell_adhesion_affinity'] = {}

def init_default_motility_params(cdname):
    """Initialize default motility parameters"""
    st.session_state.param_d[cdname]['speed'] = '1.0'
    st.session_state.param_d[cdname]['persistence_time'] = '5.0'
    st.session_state.param_d[cdname]['migration_bias'] = '0.5'
    st.session_state.param_d[cdname]['motility_enabled'] = False
    st.session_state.param_d[cdname]['motility_chemotaxis'] = False

def init_default_secretion_params(cdname):
    """Initialize default secretion parameters"""
    st.session_state.param_d[cdname]['secretion'] = {}
    for substrate in st.session_state.substrate_list:
        st.session_state.param_d[cdname]['secretion'][substrate] = {
            'secretion_rate': '0.0',
            'secretion_target': '1.0',
            'uptake_rate': '0.0',
            'net_export_rate': '0.0'
        }

def init_default_custom_data(cdname):
    """Initialize custom data"""
    st.session_state.param_d[cdname]['custom_data'] = {}

def new_cell_def(cdname):
    """Create a new cell definition with default parameters"""
    st.session_state.param_d[cdname] = {}
    st.session_state.param_d[cdname]['ID'] = str(len(st.session_state.param_d))
    
    # Initialize all parameter categories
    init_default_cycle_params(cdname)
    init_default_death_params(cdname)
    init_default_volume_params(cdname)
    init_default_mechanics_params(cdname)
    init_default_motility_params(cdname)
    init_default_secretion_params(cdname)
    init_default_custom_data(cdname)

def copy_cell_def(source_cdname, new_cdname):
    """Copy an existing cell definition"""
    st.session_state.param_d[new_cdname] = copy.deepcopy(st.session_state.param_d[source_cdname])
    st.session_state.param_d[new_cdname]['ID'] = str(len(st.session_state.param_d))

def delete_cell_def(cdname):
    """Delete a cell definition"""
    if len(st.session_state.param_d) > 1:
        del st.session_state.param_d[cdname]
        # Set current to first remaining cell def
        st.session_state.current_cell_def = list(st.session_state.param_d.keys())[0]
        return True
    return False

# Custom CSS
st.markdown("""
<style>
    .cell-def-header {
        background-color: orange;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
        font-weight: bold;
    }
    .section-divider {
        border-top: 2px solid #ccc;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Main Title
st.title("🧬 Cell Definitions")

# Sidebar for cell type management
with st.sidebar:
    st.header("Cell Type Management")
    
    # Cell type selector
    if st.session_state.param_d:
        cell_types = list(st.session_state.param_d.keys())
        current_index = cell_types.index(st.session_state.current_cell_def) if st.session_state.current_cell_def in cell_types else 0
        selected_cell = st.selectbox(
            "Select Cell Type",
            cell_types,
            index=current_index,
            key="cell_selector"
        )
        st.session_state.current_cell_def = selected_cell
    else:
        st.info("No cell types defined. Create one below.")
    
    st.divider()
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ New", use_container_width=True, type="primary"):
            new_name = random_name("cell_", 3)
            while new_name in st.session_state.param_d:
                new_name = random_name("cell_", 3)
            new_cell_def(new_name)
            st.session_state.current_cell_def = new_name
            st.rerun()
    
    with col2:
        if st.button("📋 Copy", use_container_width=True, type="primary"):
            if st.session_state.current_cell_def:
                new_name = random_name("copy_", 3)
                while new_name in st.session_state.param_d:
                    new_name = random_name("copy_", 3)
                copy_cell_def(st.session_state.current_cell_def, new_name)
                st.session_state.current_cell_def = new_name
                st.rerun()
    
    if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
        if st.session_state.current_cell_def:
            if delete_cell_def(st.session_state.current_cell_def):
                st.rerun()
            else:
                st.error("Cannot delete the last cell type!")
    
    st.divider()
    
    # ID Management
    st.checkbox("Auto-number IDs when saved", value=True)
    
    # Display current cell types
    if st.session_state.param_d:
        st.subheader("Current Cell Types")
        for cdname, params in st.session_state.param_d.items():
            is_current = cdname == st.session_state.current_cell_def
            prefix = "▶ " if is_current else "  "
            st.text(f"{prefix}{cdname} (ID: {params.get('ID', 'N/A')})")

# Main content area
if not st.session_state.current_cell_def or not st.session_state.param_d:
    st.info("👈 Please create or select a cell type from the sidebar to begin.")
else:
    cdname = st.session_state.current_cell_def
    params = st.session_state.param_d[cdname]
    
    # Tabs for different parameter categories
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Cycle", "Death", "Volume", "Mechanics", "Motility", "Secretion", "Custom Data"
    ])
    
    # ==================== CYCLE TAB ====================
    with tab1:
        st.markdown('<div class="cell-def-header">Cycle Parameters</div>', unsafe_allow_html=True)
        
        cycle_models = ["Live", "Basic Ki67", "Advanced Ki67", "Flow Cytometry", 
                       "Flow Cytometry Separated", "Cycling Quiescent"]
        cycle_choice = st.selectbox(
            "Cycle Model",
            cycle_models,
            index=params.get('cycle_choice_idx', 0)
        )
        params['cycle_choice_idx'] = cycle_models.index(cycle_choice)
        
        col1, col2 = st.columns(2)
        with col1:
            params['cycle_live_00_trate'] = st.text_input(
                "Transition Rate (1/min)",
                value=params.get('cycle_live_00_trate', '0.00072')
            )
        
        with col2:
            params['cycle_duration_flag'] = st.checkbox(
                "Use Duration Instead of Rate",
                value=params.get('cycle_duration_flag', False)
            )
    
    # ==================== DEATH TAB ====================
    with tab2:
        st.markdown('<div class="cell-def-header">Death Parameters</div>', unsafe_allow_html=True)
        
        # Apoptosis
        st.subheader("Apoptosis")
        col1, col2 = st.columns(2)
        
        with col1:
            params['apoptosis_death_rate'] = st.text_input(
                "Death Rate (1/min)",
                value=params.get('apoptosis_death_rate', '5.31667e-05'),
                key="apop_rate"
            )
        
        with col2:
            params['apoptosis_01_duration'] = st.text_input(
                "Phase Duration (min)",
                value=params.get('apoptosis_01_duration', '516'),
                key="apop_dur"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            params['apoptosis_unlysed_rate'] = st.text_input(
                "Unlysed Fluid Change Rate",
                value=params.get('apoptosis_unlysed_rate', '0.05'),
                key="apop_unlysed"
            )
        
        with col4:
            params['apoptosis_lysed_rate'] = st.text_input(
                "Lysed Fluid Change Rate",
                value=params.get('apoptosis_lysed_rate', '0.0'),
                key="apop_lysed"
            )
        
        st.divider()
        
        # Necrosis
        st.subheader("Necrosis")
        col1, col2 = st.columns(2)
        
        with col1:
            params['necrosis_death_rate'] = st.text_input(
                "Death Rate (1/min)",
                value=params.get('necrosis_death_rate', '0.0'),
                key="nec_rate"
            )
        
        with col2:
            params['necrosis_01_duration'] = st.text_input(
                "Phase 0 Duration (min)",
                value=params.get('necrosis_01_duration', '86400'),
                key="nec_dur"
            )
    
    # ==================== VOLUME TAB ====================
    with tab3:
        st.markdown('<div class="cell-def-header">Volume Parameters</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            params['volume_total'] = st.text_input(
                "Total Volume (μm³)",
                value=params.get('volume_total', '2494')
            )
            
            params['volume_fluid_fraction'] = st.text_input(
                "Fluid Fraction",
                value=params.get('volume_fluid_fraction', '0.75')
            )
            
            params['volume_nuclear'] = st.text_input(
                "Nuclear Volume (μm³)",
                value=params.get('volume_nuclear', '540')
            )
        
        with col2:
            params['volume_fluid_change_rate'] = st.text_input(
                "Fluid Change Rate (1/min)",
                value=params.get('volume_fluid_change_rate', '0.05')
            )
            
            params['volume_cytoplasmic_rate'] = st.text_input(
                "Cytoplasmic Biomass Change Rate (1/min)",
                value=params.get('volume_cytoplasmic_rate', '0.0045')
            )
            
            params['volume_nuclear_rate'] = st.text_input(
                "Nuclear Biomass Change Rate (1/min)",
                value=params.get('volume_nuclear_rate', '0.0055')
            )
    
    # ==================== MECHANICS TAB ====================
    with tab4:
        st.markdown('<div class="cell-def-header">Mechanics Parameters</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            params['mechanics_adhesion'] = st.text_input(
                "Cell-Cell Adhesion Strength (μm/min)",
                value=params.get('mechanics_adhesion', '0.4')
            )
            
            params['mechanics_repulsion'] = st.text_input(
                "Cell-Cell Repulsion Strength (μm/min)",
                value=params.get('mechanics_repulsion', '10.0')
            )
        
        with col2:
            params['mechanics_adhesion_distance'] = st.text_input(
                "Relative Maximum Adhesion Distance",
                value=params.get('mechanics_adhesion_distance', '1.25')
            )
        
        st.divider()
        
        # Cell Adhesion Affinity
        st.subheader("Cell Adhesion Affinity")
        if 'cell_adhesion_affinity' not in params:
            params['cell_adhesion_affinity'] = {}
        
        for other_cell in st.session_state.param_d.keys():
            if other_cell not in params['cell_adhesion_affinity']:
                params['cell_adhesion_affinity'][other_cell] = '1.0'
            
            params['cell_adhesion_affinity'][other_cell] = st.text_input(
                f"Affinity to {other_cell}",
                value=params['cell_adhesion_affinity'][other_cell],
                key=f"affinity_{cdname}_{other_cell}"
            )
    
    # ==================== MOTILITY TAB ====================
    with tab5:
        st.markdown('<div class="cell-def-header">Motility Parameters</div>', unsafe_allow_html=True)
        
        params['motility_enabled'] = st.checkbox(
            "Enable Motility",
            value=params.get('motility_enabled', False)
        )
        
        if params['motility_enabled']:
            col1, col2 = st.columns(2)
            
            with col1:
                params['speed'] = st.text_input(
                    "Speed (μm/min)",
                    value=params.get('speed', '1.0')
                )
                
                params['persistence_time'] = st.text_input(
                    "Persistence Time (min)",
                    value=params.get('persistence_time', '5.0')
                )
            
            with col2:
                params['migration_bias'] = st.text_input(
                    "Migration Bias",
                    value=params.get('migration_bias', '0.5')
                )
            
            st.divider()
            
            # Chemotaxis
            params['motility_chemotaxis'] = st.checkbox(
                "Enable Chemotaxis",
                value=params.get('motility_chemotaxis', False)
            )
            
            if params['motility_chemotaxis']:
                params['motility_chemotaxis_substrate'] = st.selectbox(
                    "Chemotaxis Substrate",
                    st.session_state.substrate_list,
                    key=f"chemo_sub_{cdname}"
                )
                
                params['motility_chemotaxis_towards'] = st.radio(
                    "Direction",
                    ["Towards", "Against"],
                    index=0 if params.get('motility_chemotaxis_towards', True) else 1,
                    horizontal=True
                ) == "Towards"
    
    # ==================== SECRETION TAB ====================
    with tab6:
        st.markdown('<div class="cell-def-header">Secretion Parameters</div>', unsafe_allow_html=True)
        
        if 'secretion' not in params:
            init_default_secretion_params(cdname)
        
        selected_substrate = st.selectbox(
            "Select Substrate",
            st.session_state.substrate_list,
            key=f"sec_substrate_{cdname}"
        )
        
        if selected_substrate:
            st.subheader(f"Parameters for {selected_substrate}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                params['secretion'][selected_substrate]['secretion_rate'] = st.text_input(
                    "Secretion Rate (1/min)",
                    value=params['secretion'][selected_substrate].get('secretion_rate', '0.0'),
                    key=f"sec_rate_{cdname}_{selected_substrate}"
                )
                
                params['secretion'][selected_substrate]['uptake_rate'] = st.text_input(
                    "Uptake Rate (1/min)",
                    value=params['secretion'][selected_substrate].get('uptake_rate', '0.0'),
                    key=f"uptake_{cdname}_{selected_substrate}"
                )
            
            with col2:
                params['secretion'][selected_substrate]['secretion_target'] = st.text_input(
                    "Secretion Target",
                    value=params['secretion'][selected_substrate].get('secretion_target', '1.0'),
                    key=f"sec_target_{cdname}_{selected_substrate}"
                )
                
                params['secretion'][selected_substrate]['net_export_rate'] = st.text_input(
                    "Net Export Rate (total/min)",
                    value=params['secretion'][selected_substrate].get('net_export_rate', '0.0'),
                    key=f"export_{cdname}_{selected_substrate}"
                )
    
    # ==================== CUSTOM DATA TAB ====================
    with tab7:
        st.markdown('<div class="cell-def-header">Custom Data</div>', unsafe_allow_html=True)
        
        if 'custom_data' not in params:
            params['custom_data'] = {}
        
        # Add new custom variable
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_var_name = st.text_input("New Variable Name", key=f"new_var_{cdname}")
        with col2:
            new_var_value = st.text_input("Initial Value", value="0.0", key=f"new_val_{cdname}")
        with col3:
            if st.button("➕ Add", key=f"add_var_{cdname}"):
                if new_var_name and new_var_name not in params['custom_data']:
                    params['custom_data'][new_var_name] = [new_var_value, False]
                    if new_var_name not in st.session_state.master_custom_var_d:
                        st.session_state.master_custom_var_d[new_var_name] = [0, '', '']
                    st.rerun()
                elif new_var_name in params['custom_data']:
                    st.error("Variable name already exists!")
        
        st.divider()
        
        # Display existing custom data
        if params['custom_data']:
            custom_data_list = []
            for var_name, var_data in params['custom_data'].items():
                custom_data_list.append({
                    'Name': var_name,
                    'Value': var_data[0],
                    'Conserved': var_data[1]
                })
            
            df = pd.DataFrame(custom_data_list)
            
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                column_config={
                    "Name": st.column_config.TextColumn("Name", disabled=True),
                    "Value": st.column_config.TextColumn("Value"),
                    "Conserved": st.column_config.CheckboxColumn("Conserved")
                },
                hide_index=True,
                key=f"custom_data_{cdname}"
            )
            
            # Update params with edited values
            for idx, row in edited_df.iterrows():
                var_name = row['Name']
                params['custom_data'][var_name] = [row['Value'], row['Conserved']]
            
            # Delete button
            var_to_delete = st.selectbox(
                "Select variable to delete",
                list(params['custom_data'].keys()),
                key=f"del_var_{cdname}"
            )
            if st.button("🗑️ Delete Variable", key=f"del_btn_{cdname}"):
                if var_to_delete:
                    del params['custom_data'][var_to_delete]
                    st.rerun()
        else:
            st.info("No custom data variables defined. Add one above.")

# Footer with export options
st.divider()
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.info(f"📊 Total Cell Types: {len(st.session_state.param_d)}")

with col2:
    if st.button("💾 Export XML", use_container_width=True):
        st.success("XML export functionality to be implemented")

with col3:
    if st.button("📥 Import XML", use_container_width=True):
        st.info("XML import functionality to be implemented")