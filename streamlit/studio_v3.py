import streamlit as st
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from math import floor, log10
from numpy import random as np
import matplotlib.pyplot as plt
import random
import copy
import logging
import pandas as pd
import numpy as np
import csv
import plotly.graph_objects as go
import string
import re

#st.title("My Tabbed Dashboard")

# Create the tabs
config_tab, microenv_tab, celltypes_tab, user_params_tab, rules_tab, run_tab, plot_tab = st.tabs(["Config Basics", "Microenv", "Cell Types", "User Params", "Rules", "Run", "Plot"])
st.set_page_config(layout="wide")


st.markdown("""

<style>
.st-be {
    background: orange;
    padding: 0 1em;
}
.st-bd {
    color: black;
}
.st-c9 {
    background-color: black;
}
.st-emotion-cache-1r4qj8v {
    background: #ECECEC;
}
</stle>
            
""", unsafe_allow_html=True)



#----------------------------------------------------------
with config_tab:
    # st.header("Config Basics")
    # st.write("This tab contains a chart.")
    # st.line_chart([1, 5, 2, 6, 3])
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
        
        # st.title("Configuration")
        
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

    render_config_tab()

#----------------------------------------------------------
with microenv_tab:

    class SubstrateDef:
        def __init__(self, config_tab):
            self.param_d = {}
            self.current_substrate = None
            self.xml_root = None
            self.config_tab = config_tab
            self.new_substrate_count = 1
            self.is_3D = False
            self.default_rate_units = "1/min"
            self.dirichlet_units = "mmHG"
            self.ics_tab = None
            self.rules_tab = None
            self.celldef_tab = None
            self.dirichlet_options_exist = False

        def render(self):
            """Main render function for Streamlit"""
            
            # Initialize session state
            if 'substrates' not in st.session_state:
                st.session_state.substrates = {}
            if 'current_substrate' not in st.session_state:
                st.session_state.current_substrate = None
            if 'gradients' not in st.session_state:
                st.session_state.gradients = False
            if 'track_in_agents' not in st.session_state:
                st.session_state.track_in_agents = False
            
            # Update param_d reference
            self.param_d = st.session_state.substrates
            
            # Layout with columns
            col1, col2 = st.columns([1, 3])
            
            with col1:
                self.render_substrate_tree()
            
            with col2:
                self.render_substrate_params()
        
        def render_substrate_tree(self):
            """Left sidebar with substrate list and controls"""
            st.markdown("### Substrate")
            
            # Action buttons
            col_new, col_copy, col_delete = st.columns([1, 1, 1])
            
            with col_new:
                if st.button("➕ New", use_container_width=True, key="btn_new"):
                    self.new_substrate()
            
            with col_copy:
                if st.button("📋 Copy", use_container_width=True, key="btn_copy"):
                    self.copy_substrate()
            
            with col_delete:
                if st.button("🗑️ Delete", use_container_width=True, key="btn_delete"):
                    self.delete_substrate()
            
            st.divider()
            
            # List substrates
            if st.session_state.substrates:
                substrate_names = list(st.session_state.substrates.keys())
                
                # Radio buttons for selection
                selected = st.radio(
                    "Select Substrate:",
                    substrate_names,
                    index=substrate_names.index(st.session_state.current_substrate) 
                        if st.session_state.current_substrate in substrate_names else 0,
                    label_visibility="collapsed"
                )
                
                if selected != st.session_state.current_substrate:
                    st.session_state.current_substrate = selected
                    st.rerun()
            else:
                st.info("No substrates. Click 'New' to create one.")
        
        def render_substrate_params(self):
            """Right panel with substrate parameters"""
            if not st.session_state.current_substrate:
                st.info("👈 Select or create a substrate to edit parameters")
                return
            
            substrate = st.session_state.substrates[st.session_state.current_substrate]
            
            st.markdown(f"### {st.session_state.current_substrate}")
            
            # Basic parameters
            st.markdown("#### Basic Parameters")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                substrate['diffusion_coef'] = st.number_input(
                    "Diffusion coefficient",
                    value=float(substrate.get('diffusion_coef', 100000.0)),
                    format="%.2f",
                    key=f"diff_{st.session_state.current_substrate}"
                )
            with col2:
                st.markdown("<div style='padding-top: 32px;'>micron²/min</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                substrate['decay_rate'] = st.number_input(
                    "Decay rate",
                    value=float(substrate.get('decay_rate', 0.1)),
                    format="%.4f",
                    key=f"decay_{st.session_state.current_substrate}"
                )
            with col2:
                st.markdown(f"<div style='padding-top: 32px;'>{self.default_rate_units}</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                substrate['init_cond'] = st.number_input(
                    "Initial condition",
                    value=float(substrate.get('init_cond', 0.0)),
                    format="%.2f",
                    key=f"init_{st.session_state.current_substrate}"
                )
            with col2:
                units = substrate.get('init_cond_units', self.dirichlet_units)
                st.markdown(f"<div style='padding-top: 32px;'>{units}</div>", unsafe_allow_html=True)
            
            st.divider()
            
            # Dirichlet BC
            st.markdown("#### Dirichlet Boundary Conditions")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                substrate['dirichlet_bc'] = st.number_input(
                    "Dirichlet BC",
                    value=float(substrate.get('dirichlet_bc', 0.0)),
                    format="%.2f",
                    key=f"dbc_{st.session_state.current_substrate}"
                )
            with col2:
                units = substrate.get('dirichlet_bc_units', self.dirichlet_units)
                st.markdown(f"<div style='padding-top: 32px;'>{units}</div>", unsafe_allow_html=True)
            with col3:
                if st.button("Apply to all", key=f"apply_{st.session_state.current_substrate}"):
                    self.apply_dc_cb()
            
            st.markdown("**Dirichlet options per boundary:**")
            
            # Boundary conditions
            boundaries = ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']
            
            for boundary in boundaries:
                # Disable Z boundaries if not 3D
                disabled = (boundary in ['zmin', 'zmax'] and not self.is_3D)
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.markdown(f"**{boundary}:**")
                with col2:
                    substrate[f'dirichlet_{boundary}'] = st.number_input(
                        f"{boundary}",
                        value=float(substrate.get(f'dirichlet_{boundary}', 0.0)),
                        format="%.2f",
                        key=f"d_{boundary}_{st.session_state.current_substrate}",
                        label_visibility="collapsed",
                        disabled=disabled
                    )
                with col3:
                    substrate[f'enable_{boundary}'] = st.checkbox(
                        "on",
                        value=substrate.get(f'enable_{boundary}', False),
                        key=f"en_{boundary}_{st.session_state.current_substrate}",
                        disabled=disabled
                    )
            
            st.divider()
            
            # Global options
            st.markdown("#### For all substrates:")
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.gradients = st.checkbox(
                    "Calculate gradients",
                    value=st.session_state.gradients,
                    key="gradients_checkbox"
                )
            with col2:
                st.session_state.track_in_agents = st.checkbox(
                    "Track in agents",
                    value=st.session_state.track_in_agents,
                    key="track_in_agents_checkbox"
                )
        
        def apply_dc_cb(self):
            """Apply Dirichlet BC value to all boundaries"""
            if not st.session_state.current_substrate:
                return
            
            substrate = st.session_state.substrates[st.session_state.current_substrate]
            bc_value = substrate.get('dirichlet_bc', 0.0)
            
            boundaries = ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']
            for boundary in boundaries:
                substrate[f'dirichlet_{boundary}'] = bc_value
                # Also update the widget keys to force update
                key = f"d_{boundary}_{st.session_state.current_substrate}"
                if key in st.session_state:
                    st.session_state[key] = bc_value
            
            st.rerun()
        
        def update_3D(self):
            """Check if simulation is 3D based on config tab"""
            try:
                zmax = float(st.session_state.get('zmax', 0))
                zmin = float(st.session_state.get('zmin', 0))
                zdel = float(st.session_state.get('zdel', 1))
            except:
                st.error("Invalid value in Z domain of Config tab.")
                return
            
            self.is_3D = (zmax - zmin) > zdel
        
        def new_substrate(self):
            """Create a new substrate"""
            # Find unique name
            while True:
                subname = f"substrate{self.new_substrate_count:02d}"
                if subname not in st.session_state.substrates:
                    break
                self.new_substrate_count += 1
            
            # Create new substrate with default values (copy from current if exists)
            if st.session_state.current_substrate:
                new_sub = copy.deepcopy(st.session_state.substrates[st.session_state.current_substrate])
            else:
                new_sub = {}
            
            # Zero out values
            new_sub.update({
                'diffusion_coef': 0.0,
                'decay_rate': 0.0,
                'init_cond': 0.0,
                'init_cond_units': 'dimensionless',
                'dirichlet_bc': 0.0,
                'dirichlet_bc_units': 'dimensionless',
                'dirichlet_enabled': False,
                'dirichlet_xmin': 0.0, 'enable_xmin': False,
                'dirichlet_xmax': 0.0, 'enable_xmax': False,
                'dirichlet_ymin': 0.0, 'enable_ymin': False,
                'dirichlet_ymax': 0.0, 'enable_ymax': False,
                'dirichlet_zmin': 0.0, 'enable_zmin': False,
                'dirichlet_zmax': 0.0, 'enable_zmax': False,
            })
            
            st.session_state.substrates[subname] = new_sub
            st.session_state.current_substrate = subname
            self.new_substrate_count += 1
            
            # Notify other tabs
            if self.celldef_tab:
                self.celldef_tab.add_new_substrate(subname)
            if self.config_tab:
                self.config_tab.add_new_substrate(subname)
            if self.ics_tab:
                self.ics_tab.add_new_substrate(subname)
            
            st.rerun()
        
        def copy_substrate(self):
            """Copy the current substrate"""
            if not st.session_state.current_substrate:
                st.warning("No substrate selected to copy")
                return
            
            subname = f"substrate{self.new_substrate_count:02d}"
            source = st.session_state.substrates[st.session_state.current_substrate]
            
            st.session_state.substrates[subname] = copy.deepcopy(source)
            st.session_state.substrates[subname]['name'] = subname
            st.session_state.current_substrate = subname
            self.new_substrate_count += 1
            
            # Notify other tabs
            if self.celldef_tab:
                self.celldef_tab.add_new_substrate(subname)
            if self.config_tab:
                self.config_tab.add_new_substrate(subname)
            if self.ics_tab:
                self.ics_tab.add_new_substrate(subname)
            
            st.rerun()
        
        def delete_substrate(self):
            """Delete the current substrate"""
            if len(st.session_state.substrates) == 1:
                st.error("Not allowed to delete all substrates.")
                return

            if not st.session_state.current_substrate:
                return
            
            substrate_names = list(st.session_state.substrates.keys())
            current_idx = substrate_names.index(st.session_state.current_substrate)
            
            # Delete from rules tab first
            if self.rules_tab:
                self.rules_tab.delete_substrate(st.session_state.current_substrate)
            
            # Remove substrate
            del st.session_state.substrates[st.session_state.current_substrate]
            
            # Select next substrate
            substrate_names = list(st.session_state.substrates.keys())
            if substrate_names:
                new_idx = min(current_idx, len(substrate_names) - 1)
                st.session_state.current_substrate = substrate_names[new_idx]
            else:
                st.session_state.current_substrate = None
            
            # Notify other tabs
            if self.celldef_tab:
                self.celldef_tab.delete_substrate(current_idx, st.session_state.current_substrate)
            if self.config_tab:
                self.config_tab.delete_substrate(current_idx)
            if self.ics_tab:
                self.ics_tab.delete_substrate(current_idx)
            
            st.rerun()
        
        def populate_tree(self):
            """Load substrates from XML"""
            logging.debug('==== microenv populate_tree ====')
            
            uep = self.xml_root.find(".//microenvironment_setup")
            if not uep:
                return
            
            st.session_state.substrates.clear()
            substrate_0th = None
            
            idx = 0
            for var in uep:
                if var.tag == 'variable':
                    substrate_name = var.attrib['name']
                    self.current_substrate = substrate_name
                    
                    if idx == 0:
                        substrate_0th = substrate_name
                    
                    st.session_state.substrates[substrate_name] = {}
                    substrate = st.session_state.substrates[substrate_name]
                    
                    idx += 1
                    
                    # Parse XML values
                    var_param_path = self.xml_root.find(f".//microenvironment_setup//variable[{idx}]//physical_parameter_set")
                    var_path = self.xml_root.find(f".//microenvironment_setup//variable[{idx}]")
                    
                    substrate['diffusion_coef'] = float(var_param_path.find('.//diffusion_coefficient').text)
                    substrate['decay_rate'] = float(var_param_path.find('.//decay_rate').text)
                    substrate['init_cond'] = float(var_path.find('.//initial_condition').text)
                    substrate['init_cond_units'] = var_path.find('.//initial_condition').attrib['units']
                    
                    dirichlet_bc_path = var_path.find('.//Dirichlet_boundary_condition')
                    substrate['dirichlet_bc'] = float(dirichlet_bc_path.text)
                    substrate['dirichlet_bc_units'] = dirichlet_bc_path.attrib['units']
                    substrate['dirichlet_enabled'] = dirichlet_bc_path.attrib['enabled'].lower() != "false"
                    
                    # Initialize boundary values
                    for boundary in ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']:
                        substrate[f'dirichlet_{boundary}'] = 0.0
                        substrate[f'enable_{boundary}'] = False
                    
                    # Parse boundary options if they exist
                    options_path = var_path.find('.//Dirichlet_options')
                    if options_path:
                        self.dirichlet_options_exist = True
                        for bv in options_path:
                            boundary_id = bv.attrib['ID'].lower()
                            substrate[f'dirichlet_{boundary_id}'] = float(bv.text)
                            substrate[f'enable_{boundary_id}'] = bv.attrib['enabled'].lower() == 'true'
                    else:
                        # Use default enabled state for all boundaries
                        default_enabled = substrate['dirichlet_enabled']
                        for boundary in ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']:
                            substrate[f'enable_{boundary}'] = default_enabled
                
                elif var.tag == 'options':
                    st.session_state.gradients = False
                    st.session_state.track_in_agents = False
                    
                    for opt in var:
                        if "calculate_gradients" in opt.tag:
                            st.session_state.gradients = opt.text.lower() == 'true'
                        elif "track_internalized_substrates_in_each_agent" in opt.tag:
                            st.session_state.track_in_agents = opt.text.lower() == 'true'
            
            # Select first substrate
            if substrate_0th:
                st.session_state.current_substrate = substrate_0th
            
            logging.debug('==== leaving microenv populate_tree ====')
        
        def fill_xml(self):
            """Generate XML from current substrate parameters"""
            logging.debug('----------- microenv_tab.py: fill_xml() ----------')
            
            uep = self.xml_root.find('.//microenvironment_setup')
            if not uep:
                return False
            
            # Remove all existing variables
            for var in uep.findall('variable'):
                uep.remove(var)
            
            # Get list of substrates
            substrates_in_tree = list(st.session_state.substrates.keys())
            logging.debug(f'substrates_in_tree = {substrates_in_tree}')
            
            indent1 = '\n'
            indent6 = '\n      '
            indent8 = '\n        '
            indent10 = '\n          '
            
            idx = 0
            for substrate_name in substrates_in_tree:
                substrate = st.session_state.substrates[substrate_name]
                
                # Validate numeric values
                for key in substrate:
                    if "enable" not in key and "units" not in key:
                        sfx = key[-4:]
                        if ("min" in sfx or "max" in sfx) and substrate.get(f"enable_{sfx}"):
                            try:
                                float(substrate[key])
                            except:
                                st.error("Invalid (non-numeric) Microenvironment parameter values. Please fix them.")
                                return False
                
                # Create XML element
                elm = ET.Element("variable", 
                        {"name": substrate_name, "units": "dimensionless", "ID": str(idx)})
                elm.tail = '\n' + indent6
                elm.text = indent8
                
                # Physical parameters
                subelm = ET.SubElement(elm, 'physical_parameter_set')
                subelm.text = indent10
                subelm.tail = indent8
                
                subelm2 = ET.SubElement(subelm, "diffusion_coefficient", {"units": "micron^2/min"})
                subelm2.text = str(substrate['diffusion_coef'])
                subelm2.tail = indent10
                
                subelm2 = ET.SubElement(subelm, "decay_rate", {"units": self.default_rate_units})
                subelm2.text = str(substrate['decay_rate'])
                subelm2.tail = indent8
                
                # Initial condition
                subelm = ET.SubElement(elm, 'initial_condition', 
                                    {"units": substrate.get('init_cond_units', 'dimensionless')})
                subelm.text = str(substrate['init_cond'])
                subelm.tail = indent8
                
                # Dirichlet BC
                dirichlet_BC_flag = any([
                    substrate.get('enable_xmin'), substrate.get('enable_xmax'),
                    substrate.get('enable_ymin'), substrate.get('enable_ymax')
                ])
                
                if self.is_3D:
                    dirichlet_BC_flag = dirichlet_BC_flag or substrate.get('enable_zmin') or substrate.get('enable_zmax')
                
                subelm = ET.SubElement(elm, "Dirichlet_boundary_condition",
                        {"units": substrate.get('dirichlet_bc_units', 'dimensionless'),
                        "enabled": str(dirichlet_BC_flag).lower()})
                subelm.text = str(substrate['dirichlet_bc'])
                subelm.tail = indent8
                
                # Dirichlet options
                subelm = ET.SubElement(elm, "Dirichlet_options")
                subelm.text = indent10
                subelm.tail = indent8
                
                for boundary in ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']:
                    subelm2 = ET.SubElement(subelm, "boundary_value",
                            {"ID": boundary, "enabled": str(substrate.get(f'enable_{boundary}', False)).lower()})
                    subelm2.text = str(substrate.get(f'dirichlet_{boundary}', 0.0))
                    subelm2.tail = indent10 if boundary != 'zmax' else indent8
                
                uep.insert(idx, elm)
                idx += 1
            
            # Global options
            self.xml_root.find(".//options//calculate_gradients").text = str(st.session_state.gradients).lower()
            self.xml_root.find(".//options//track_internalized_substrates_in_each_agent").text = str(st.session_state.track_in_agents).lower()
            
            # Handle ICs tab CSV option
            if hasattr(self.ics_tab, 'ic_substrates_enabled') and self.ics_tab.ic_substrates_enabled:
                ic_elem = self.xml_root.find(".//microenvironment_setup//options//initial_condition")
                if ic_elem is None:
                    elm = ET.Element("initial_condition", {"type": "csv", "enabled": 'True'})
                    ET.SubElement(elm, 'filename')
                    self.xml_root.find('.//microenvironment_setup//options').insert(2, elm)
                
                self.xml_root.find(".//microenvironment_setup//options//initial_condition").attrib['type'] = 'csv'
                self.xml_root.find(".//microenvironment_setup//options//initial_condition").attrib['enabled'] = 'true'
                self.xml_root.find(".//microenvironment_setup//options//initial_condition//filename").text = self.ics_tab.full_substrate_ic_fname
            elif self.xml_root.find(".//microenvironment_setup//options//initial_condition") is not None:
                ic_elem = self.xml_root.find(".//microenvironment_setup//options//initial_condition")
                if ic_elem.attrib.get('type', '').lower() == 'csv':
                    ic_elem.attrib['enabled'] = 'false'
            
            return True
        
        def first_substrate_name(self):
            """Get the name of the first substrate"""
            uep = self.xml_root.find(".//microenvironment_setup//variable")
            if uep:
                return uep.attrib['name']
            return None
        
        def popup_msg(self, msg):
            """Show popup message (Streamlit version)"""
            st.error(msg)

    # Create instance and render
    substrate_def = SubstrateDef(config_tab=None)
    substrate_def.render()


#----------------------------------------------------------

with rules_tab:

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

#--------------------------------------------------------------

with celltypes_tab:

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
    
    container = st.container(border=None, key=None, width="stretch", height="content", horizontal=False, horizontal_alignment="left", vertical_alignment="top", gap="small")
    container.write("Cell Type Management")

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


#----------------------------------------------------------
with user_params_tab:
    class UserParams:
        def __init__(self):
            self.xml_root = None
            self.max_rows = 100
            
            # Column indices
            self.var_icol_name = 0
            self.var_icol_type = 1
            self.var_icol_value = 2
            self.var_icol_units = 3
            self.var_icol_desc = 4
            
        def initialize_session_state(self):
            """Initialize Streamlit session state for user parameters"""
            if 'user_params_data' not in st.session_state:
                st.session_state.user_params_data = []
                # Initialize with empty rows
                for i in range(10):  # Start with 10 rows
                    st.session_state.user_params_data.append({
                        'name': '',
                        'type': 'double',
                        'value': '',
                        'units': '',
                        'description': ''
                    })
            
            if 'user_params_count' not in st.session_state:
                st.session_state.user_params_count = 10
                
            if 'delete_row' not in st.session_state:
                st.session_state.delete_row = None
        
        def validate_varname(self, name):
            """Validate variable name (must start with letter, contain only alphanumeric and underscore)"""
            if not name:
                return True
            pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
            return bool(re.match(pattern, name))
        
        def validate_utable(self):
            """Validate the user parameters table"""
            errors = []
            
            # Get non-empty entries
            entries = [row for row in st.session_state.user_params_data if row['name']]
            
            # Check for duplicate names
            names = [row['name'] for row in entries]
            duplicates = [name for name in set(names) if names.count(name) > 1]
            
            if duplicates:
                errors.append(f"Duplicate User Params: {duplicates}")
            
            # Validate doubles
            for row in entries:
                if row['type'] == 'double' and row['value']:
                    try:
                        float(row['value'])
                    except ValueError:
                        errors.append(f"Invalid double value for '{row['name']}': {row['value']}")
            
            # Validate ints
            for row in entries:
                if row['type'] == 'int' and row['value']:
                    try:
                        val = float(row['value'])
                        if not val.is_integer():
                            errors.append(f"Invalid int value for '{row['name']}': {row['value']}")
                    except:
                        errors.append(f"Invalid int value for '{row['name']}': {row['value']}")
            
            # Validate bools
            for row in entries:
                if row['type'] == 'bool' and row['value']:
                    if row['value'].lower() not in ['true', 'false']:
                        errors.append(f"Invalid bool value for '{row['name']}': {row['value']} (must be True or False)")
            
            return len(errors) == 0, errors
        
        def search_params(self, search_term):
            """Filter parameters by search term"""
            if not search_term:
                return list(range(len(st.session_state.user_params_data)))
            
            matching_indices = []
            for idx, row in enumerate(st.session_state.user_params_data):
                if search_term.lower() in row['name'].lower():
                    matching_indices.append(idx)
            return matching_indices
        
        def delete_row(self, row_idx):
            """Delete a row from the parameters table"""
            if 0 <= row_idx < len(st.session_state.user_params_data):
                st.session_state.user_params_data.pop(row_idx)
                # Add an empty row at the end
                st.session_state.user_params_data.append({
                    'name': '',
                    'type': 'double',
                    'value': '',
                    'units': '',
                    'description': ''
                })
        
        def add_rows(self, num_rows=10):
            """Add empty rows to the table"""
            for _ in range(num_rows):
                st.session_state.user_params_data.append({
                    'name': '',
                    'type': 'double',
                    'value': '',
                    'units': '',
                    'description': ''
                })
            st.session_state.user_params_count += num_rows
        
        def fill_gui_from_xml(self, xml_root):
            """Populate GUI from XML"""
            self.xml_root = xml_root
            uep_user_params = xml_root.find(".//user_parameters")
            
            if uep_user_params is None:
                return
            
            # Clear existing data
            st.session_state.user_params_data = []
            
            idx = 0
            for var in uep_user_params:
                if 'type' in var.keys() and "divider" in var.attrib['type']:
                    continue
                
                var_type = 'double'  # default
                if 'type' in var.keys():
                    if "double" in var.attrib['type']:
                        var_type = 'double'
                    elif "int" in var.attrib['type']:
                        var_type = 'int'
                    elif "bool" in var.attrib['type']:
                        var_type = 'bool'
                    else:
                        var_type = 'string'
                
                st.session_state.user_params_data.append({
                    'name': var.tag,
                    'type': var_type,
                    'value': var.text if var.text else '',
                    'units': var.attrib.get('units', ''),
                    'description': var.attrib.get('description', '')
                })
                idx += 1
            
            # Add empty rows if needed
            while len(st.session_state.user_params_data) < 10:
                st.session_state.user_params_data.append({
                    'name': '',
                    'type': 'double',
                    'value': '',
                    'units': '',
                    'description': ''
                })
        
        def fill_xml(self, xml_root):
            """Generate XML from GUI data"""
            self.xml_root = xml_root
            uep = xml_root.find('.//user_parameters')
            
            if uep is not None:
                # Remove all existing user params
                for var in list(uep):
                    uep.remove(var)
            
            # Add parameters from GUI
            knt = 0
            elm = None
            
            for row in st.session_state.user_params_data:
                if row['name']:  # Only process rows with names
                    elm = ET.Element(row['name'], {
                        "type": row['type'],
                        "units": row['units'],
                        "description": row['description']
                    })
                    elm.text = row['value']
                    elm.tail = '\n        '
                    uep.insert(knt, elm)
                    knt += 1
            
            if elm:
                elm.tail = '\n    '
        
        def render(self):
            """Render the Streamlit UI"""
            self.initialize_session_state()
            
            st.title("User Parameters")
            
            # Search box
            search_term = st.text_input("🔍 Search for Name...", key="search_box", max_chars=400)
            
            st.info("(Note: validation check performed at Save or Run)")
            
            # Get matching indices for search highlighting
            matching_indices = self.search_params(search_term) if search_term else []
            
            # Create a container for the table
            st.markdown("### Parameters Table")
            
            # Display instructions
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption("Click row number to select, then click Delete button")
            
            # Track which row to delete
            row_to_delete = None
            
            # Display rows with editable fields
            for idx in range(min(len(st.session_state.user_params_data), 50)):  # Limit display for performance
                row = st.session_state.user_params_data[idx]
                
                # Highlight matching search results
                if search_term and idx in matching_indices:
                    st.markdown(f"**🔍 Row {idx}**")
                
                cols = st.columns([0.5, 2, 1.5, 2, 2, 3, 0.8])
                
                with cols[0]:
                    if st.button("❌", key=f"del_{idx}", help=f"Delete row {idx}"):
                        row_to_delete = idx
                
                with cols[1]:
                    new_name = st.text_input(
                        "Name",
                        value=row['name'],
                        key=f"name_{idx}",
                        label_visibility="collapsed",
                        placeholder="variable_name"
                    )
                    if new_name != row['name']:
                        if self.validate_varname(new_name):
                            st.session_state.user_params_data[idx]['name'] = new_name
                            # Auto-add rows if we're near the end
                            if idx >= len(st.session_state.user_params_data) - 5:
                                self.add_rows(10)
                        else:
                            st.error("Invalid name format", icon="⚠️")
                
                with cols[2]:
                    new_type = st.selectbox(
                        "Type",
                        options=['double', 'int', 'bool', 'string'],
                        index=['double', 'int', 'bool', 'string'].index(row['type']),
                        key=f"type_{idx}",
                        label_visibility="collapsed"
                    )
                    if new_type != row['type']:
                        st.session_state.user_params_data[idx]['type'] = new_type
                
                with cols[3]:
                    new_value = st.text_input(
                        "Value",
                        value=row['value'],
                        key=f"value_{idx}",
                        label_visibility="collapsed",
                        placeholder="value"
                    )
                    if new_value != row['value']:
                        st.session_state.user_params_data[idx]['value'] = new_value
                
                with cols[4]:
                    new_units = st.text_input(
                        "Units",
                        value=row['units'],
                        key=f"units_{idx}",
                        label_visibility="collapsed",
                        placeholder="units"
                    )
                    if new_units != row['units']:
                        st.session_state.user_params_data[idx]['units'] = new_units
                
                with cols[5]:
                    new_desc = st.text_input(
                        "Description",
                        value=row['description'],
                        key=f"desc_{idx}",
                        label_visibility="collapsed",
                        placeholder="description"
                    )
                    if new_desc != row['description']:
                        st.session_state.user_params_data[idx]['description'] = new_desc
                
                # Show row number
                with cols[6]:
                    st.caption(f"#{idx}")
            
            # Handle row deletion
            if row_to_delete is not None:
                self.delete_row(row_to_delete)
                st.rerun()
            
            # Validation button
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 3])
            
            with col1:
                if st.button("✅ Validate", type="primary"):
                    is_valid, errors = self.validate_utable()
                    if is_valid:
                        st.success("All parameters are valid!")
                    else:
                        for error in errors:
                            st.error(error)
            
            with col2:
                if st.button("🔄 Add 10 Rows"):
                    self.add_rows(10)
                    st.rerun()


    # Main app
    def main():
        st.set_page_config(page_title="User Parameters", layout="wide")
        
        user_params = UserParams()
        user_params.render()


    if __name__ == "__main__":
        main()

#--------------------------------------------------------------------
with plot_tab:
    # st.header("Plot results")
    # st.write("This tab shows some raw data.")
    # st.dataframe({"Column 1": [1, 2, 3], "Column 2": [4, 5, 6]})
    fig, ax = plt.subplots()
    low = -500
    high = 500
    size = 300
    xvals = [random.uniform(low,high) for _ in range(size)]
    yvals = [random.uniform(low,high) for _ in range(size)]
    ax.scatter(xvals, yvals)
    ax.set_box_aspect(1)
    # other plotting actions...
    st.pyplot(fig)