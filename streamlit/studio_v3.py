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

#st.title("My Tabbed Dashboard")

# Create the tabs
config_tab, microenv_tab, celltypes_tab, userparams_tab, rules_tab, run_tab, plot_tab = st.tabs(["Config Basics", "Microenv", "Cell Types", "User Params", "Rules", "Run", "Plot"])
st.set_page_config(layout="wide")

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


