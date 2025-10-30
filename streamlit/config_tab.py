"""
Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Converted to Streamlit
"""

import streamlit as st
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from math import floor, log10

st.set_page_config(page_title="Config Basics")

def init_session_state():
    """Initialize session state variables"""
    if 'xml_root' not in st.session_state:
        st.session_state.xml_root = None
    if 'substrate_list' not in st.session_state:
        st.session_state.substrate_list = []
    if 'sync_output' not in st.session_state:
        st.session_state.sync_output = True
    if 'default_time_units' not in st.session_state:
        st.session_state.default_time_units = "min"

def update_max_time_from_spinboxes():
    """Calculate max time from day/hour/minute components"""
    new_time = (st.session_state.get('day_spin', 0) * 1440 + 
                st.session_state.get('hour_spin', 0) * 60 + 
                st.session_state.get('minute_spin', 0) + 
                st.session_state.get('minute_fraction_spin', 0.0))
    new_time = max(0, new_time)
    st.session_state.max_time = str(new_time)

def max_time_to_components(max_time_str):
    """Convert max time to day/hour/minute components"""
    try:
        time = floor(float(max_time_str))
        fraction_minutes = float(max_time_str) - time
    except:
        time = 0
        fraction_minutes = 0
    
    minutes = time % 60
    time -= minutes
    time = int(time / 60)
    hours = time % 24
    time -= hours
    time = int(time / 24)
    days = time
    
    return days, hours, minutes, fraction_minutes

def fill_substrates_comboboxes():
    """Fill substrate dropdown from XML"""
    st.session_state.substrate_list.clear()
    if st.session_state.xml_root is not None:
        uep = st.session_state.xml_root.find('.//microenvironment_setup')
        if uep:
            for var in uep.findall('variable'):
                name = var.attrib['name']
                st.session_state.substrate_list.append(name)

def render_config_tab():
    """Main function to render the configuration tab"""
    init_session_state()
    
    st.title("Configuration")
    
    # Domain Section
    st.markdown("### Domain (micron)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.number_input("Xmin", key="xmin", format="%.2f")
        st.number_input("Ymin", key="ymin", format="%.2f")
        st.number_input("Zmin", key="zmin", format="%.2f")
    
    with col2:
        st.number_input("Xmax", key="xmax", format="%.2f")
        st.number_input("Ymax", key="ymax", format="%.2f")
        st.number_input("Zmax", key="zmax", format="%.2f")
    
    with col3:
        st.number_input("dx", key="xdel", format="%.2f", min_value=0.01)
        st.number_input("dy", key="ydel", format="%.2f", min_value=0.01)
        st.number_input("dz", key="zdel", format="%.2f", min_value=0.01)
    
    st.markdown("---")
    
    # Times Section
    st.markdown("### Times")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.text_input("Max Time", key="max_time_input", 
                     help="Total simulation time in minutes")
    
    with col2:
        # Time breakdown in days/hours/minutes
        if 'max_time_input' in st.session_state and st.session_state.max_time_input:
            days, hours, minutes, frac = max_time_to_components(st.session_state.max_time_input)
            
            tcol1, tcol2, tcol3, tcol4 = st.columns(4)
            with tcol1:
                st.number_input("Days", min_value=0, value=days, key="day_spin",
                              on_change=update_max_time_from_spinboxes)
            with tcol2:
                st.number_input("Hours", min_value=0, max_value=23, value=hours, key="hour_spin",
                              on_change=update_max_time_from_spinboxes)
            with tcol3:
                st.number_input("Minutes", min_value=0, max_value=59, value=minutes, key="minute_spin",
                              on_change=update_max_time_from_spinboxes)
            with tcol4:
                st.number_input("Fraction", min_value=0.0, max_value=0.99, value=frac, 
                              format="%.2f", key="minute_fraction_spin",
                              on_change=update_max_time_from_spinboxes)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.number_input(f"Diffusion dt ({st.session_state.default_time_units})", 
                       key="diffusion_dt", format="%.4f", min_value=0.0001)
    
    with col2:
        st.number_input(f"Mechanics dt ({st.session_state.default_time_units})", 
                       key="mechanics_dt", format="%.4f", min_value=0.0001)
    
    with col3:
        st.number_input(f"Phenotype dt ({st.session_state.default_time_units})", 
                       key="phenotype_dt", format="%.4f", min_value=0.0001)
    
    st.markdown("---")
    
    # Misc Runtime Parameters
    st.markdown("### Misc Runtime Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("# threads", key="num_threads", min_value=1, value=1, step=1)
    
    with col2:
        st.text_input("Output folder", key="folder", value="output")
    
    # Random Seed
    st.markdown("**Random seed:**")
    random_seed_type = st.radio(
        "Select random seed type:",
        ["System clock", "Integer seed"],
        key="random_seed_type",
        horizontal=True
    )
    
    if random_seed_type == "Integer seed":
        st.number_input("Seed value", key="random_seed_integer", 
                       min_value=0, step=1, value=0)
        st.warning("⚠️ WARNING: random_seed in user_parameters will take precedence if it remains.")
    
    st.markdown("---")
    
    # Save Data Section
    st.markdown("### Save Data (intervals)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        save_svg = st.checkbox("SVG", key="save_svg", value=True)
        if save_svg:
            st.number_input(f"SVG interval ({st.session_state.default_time_units})", 
                          key="svg_interval", format="%.2f", min_value=0.01)
    
    with col2:
        save_full = st.checkbox("Full", key="save_full", value=False)
        if save_full:
            st.number_input(f"Full interval ({st.session_state.default_time_units})", 
                          key="full_interval", format="%.2f", min_value=0.01)
    
    with col3:
        sync_svg_mat = st.checkbox("Sync", key="sync_svg_mat", 
                                   value=st.session_state.sync_output)
        if sync_svg_mat and save_svg and save_full:
            if 'svg_interval' in st.session_state:
                st.session_state.full_interval = st.session_state.svg_interval
    
    st.markdown("---")
    
    # Plot SVG Substrate Section
    st.markdown("### Plot SVG Substrate")
    
    plot_substrate = st.checkbox("Enable substrate plotting", key="plot_substrate_svg", value=True)
    
    if plot_substrate and len(st.session_state.substrate_list) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Substrate to plot", 
                        st.session_state.substrate_list,
                        key="svg_substrate_to_plot")
            
            st.selectbox("Colormap",
                        ["YlOrRd", "YlOrRd_r", "viridis", "viridis_r", 
                         "turbo", "turbo_r", "plasma", "plasma_r", "jet", "jet_r"],
                        key="svg_substrate_colormap")
        
        with col2:
            limits_enabled = st.checkbox("Limits enabled", key="plot_substrate_limits", value=True)
            
            if limits_enabled:
                st.number_input("Min concentration", key="svg_substrate_min", 
                              format="%.4f")
                st.number_input("Max concentration", key="svg_substrate_max", 
                              format="%.4f")
    
    st.markdown("---")
    
    # Initial Conditions Section
    st.markdown("### Initial Conditions of Cells (x,y,z, type)")
    
    cells_csv_enabled = st.checkbox("Enable CSV cell seeding", key="cells_csv", value=False)
    
    if cells_csv_enabled:
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.text_input("CSV folder", key="csv_folder", value="./data")
        
        with col2:
            st.text_input("CSV file", key="csv_file", value="cells.csv")
        
        with col3:
            if st.button("Import", key="import_seeding"):
                st.info("File import functionality - would open file dialog in desktop app")
    
    st.markdown("---")
    
    # Cell Global Behaviors
    st.markdown("### Cells' Global Behaviors")
    
    st.checkbox("Virtual walls (nudge cells away from domain boundaries)", 
               key="virtual_walls", value=True)
    
    st.markdown("---")
    
    # Action Buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Load XML", use_container_width=True):
            load_xml_config()
    
    with col2:
        if st.button("Save XML", use_container_width=True):
            save_xml_config()
    
    with col3:
        if st.button("Validate", use_container_width=True):
            validate_config()

def load_xml_config():
    """Load configuration from XML"""
    if st.session_state.xml_root is None:
        st.error("No XML root loaded")
        return
    
    try:
        # Load domain values
        st.session_state.xmin = float(st.session_state.xml_root.find(".//x_min").text)
        st.session_state.xmax = float(st.session_state.xml_root.find(".//x_max").text)
        st.session_state.xdel = float(st.session_state.xml_root.find(".//dx").text)
        
        st.session_state.ymin = float(st.session_state.xml_root.find(".//y_min").text)
        st.session_state.ymax = float(st.session_state.xml_root.find(".//y_max").text)
        st.session_state.ydel = float(st.session_state.xml_root.find(".//dy").text)
        
        st.session_state.zmin = float(st.session_state.xml_root.find(".//z_min").text)
        st.session_state.zmax = float(st.session_state.xml_root.find(".//z_max").text)
        st.session_state.zdel = float(st.session_state.xml_root.find(".//dz").text)
        
        # Load time values
        st.session_state.max_time_input = st.session_state.xml_root.find(".//max_time").text
        st.session_state.diffusion_dt = float(st.session_state.xml_root.find(".//dt_diffusion").text)
        st.session_state.mechanics_dt = float(st.session_state.xml_root.find(".//dt_mechanics").text)
        st.session_state.phenotype_dt = float(st.session_state.xml_root.find(".//dt_phenotype").text)
        
        # Load misc parameters
        st.session_state.num_threads = int(st.session_state.xml_root.find(".//omp_num_threads").text)
        st.session_state.folder = st.session_state.xml_root.find(".//save//folder").text
        
        # Load SVG settings
        st.session_state.svg_interval = float(st.session_state.xml_root.find(".//SVG//interval").text)
        svg_enable = st.session_state.xml_root.find(".//SVG//enable").text.lower() == 'true'
        st.session_state.save_svg = svg_enable
        
        # Load substrate list
        fill_substrates_comboboxes()
        
        st.success("Configuration loaded successfully!")
        
    except Exception as e:
        st.error(f"Error loading XML: {str(e)}")

def save_xml_config():
    """Save configuration to XML"""
    if st.session_state.xml_root is None:
        st.error("No XML root to save to")
        return
    
    try:
        # Validate domain parameters
        if (st.session_state.get('xdel', 0) <= 0 or 
            st.session_state.get('ydel', 0) <= 0 or 
            st.session_state.get('zdel', 0) <= 0):
            st.error("Domain spacing (dx, dy, dz) must be positive values!")
            return
        
        # Save domain values
        st.session_state.xml_root.find(".//x_min").text = str(st.session_state.get('xmin', 0))
        st.session_state.xml_root.find(".//x_max").text = str(st.session_state.get('xmax', 0))
        st.session_state.xml_root.find(".//dx").text = str(st.session_state.get('xdel', 0))
        
        st.session_state.xml_root.find(".//y_min").text = str(st.session_state.get('ymin', 0))
        st.session_state.xml_root.find(".//y_max").text = str(st.session_state.get('ymax', 0))
        st.session_state.xml_root.find(".//dy").text = str(st.session_state.get('ydel', 0))
        
        st.session_state.xml_root.find(".//z_min").text = str(st.session_state.get('zmin', 0))
        st.session_state.xml_root.find(".//z_max").text = str(st.session_state.get('zmax', 0))
        st.session_state.xml_root.find(".//dz").text = str(st.session_state.get('zdel', 0))
        
        # Determine if 2D or 3D
        zmin = st.session_state.get('zmin', 0)
        zmax = st.session_state.get('zmax', 0)
        zdel = st.session_state.get('zdel', 1)
        use_2d = 'true' if (zmax - zmin) <= zdel else 'false'
        st.session_state.xml_root.find(".//domain//use_2D").text = use_2d
        
        # Save random seed
        if st.session_state.get('random_seed_type') == "System clock":
            st.session_state.xml_root.find(".//options//random_seed").text = "system_clock"
        else:
            st.session_state.xml_root.find(".//options//random_seed").text = str(
                st.session_state.get('random_seed_integer', 0))
        
        # Save virtual walls
        vwall = 'true' if st.session_state.get('virtual_walls', False) else 'false'
        if st.session_state.xml_root.find(".//virtual_wall_at_domain_edge") is not None:
            st.session_state.xml_root.find(".//virtual_wall_at_domain_edge").text = vwall
        
        st.success("Configuration saved successfully!")
        
    except Exception as e:
        st.error(f"Error saving XML: {str(e)}")

def validate_config():
    """Validate current configuration"""
    errors = []
    warnings = []
    
    # Check domain spacing
    if st.session_state.get('xdel', 0) <= 0:
        errors.append("dx must be positive")
    if st.session_state.get('ydel', 0) <= 0:
        errors.append("dy must be positive")
    if st.session_state.get('zdel', 0) <= 0:
        errors.append("dz must be positive")
    
    # Check time steps
    if st.session_state.get('diffusion_dt', 0) <= 0:
        errors.append("Diffusion dt must be positive")
    if st.session_state.get('mechanics_dt', 0) <= 0:
        errors.append("Mechanics dt must be positive")
    if st.session_state.get('phenotype_dt', 0) <= 0:
        errors.append("Phenotype dt must be positive")
    
    # Check sync
    if (st.session_state.get('sync_svg_mat', False) and 
        st.session_state.get('svg_interval') != st.session_state.get('full_interval')):
        warnings.append("Sync is enabled but intervals don't match")
    
    # Display results
    if errors:
        st.error("❌ Validation failed:")
        for error in errors:
            st.error(f"  • {error}")
    elif warnings:
        st.warning("⚠️ Validation passed with warnings:")
        for warning in warnings:
            st.warning(f"  • {warning}")
    else:
        st.success("✅ Configuration is valid!")

# Example usage
if __name__ == "__main__":
    render_config_tab()
