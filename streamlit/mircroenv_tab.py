import streamlit as st
import copy
import logging
import xml.etree.ElementTree as ET

# This should be placed in the microenv_tab section of your code

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
        
        col1, col2 = st.columns([3, 1])
        with col1:
            substrate['diffusion_coef'] = st.number_input(
                "Diffusion coefficient",
                value=float(substrate.get('diffusion_coef', 100000.0)),
                format="%.2f",
                key=f"diff_{st.session_state.current_substrate}"
            )
        with col2:
            st.markdown("<div style='padding-top: 32px;'>micron²/min</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            substrate['decay_rate'] = st.number_input(
                "Decay rate",
                value=float(substrate.get('decay_rate', 0.1)),
                format="%.4f",
                key=f"decay_{st.session_state.current_substrate}"
            )
        with col2:
            st.markdown(f"<div style='padding-top: 32px;'>{self.default_rate_units}</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
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
        
        col1, col2, col3 = st.columns([3, 1, 1])
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
            
            col1, col2, col3 = st.columns([2, 2, 1])
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


# Replace the code in your microenv_tab with block with this:
# Create instance and render
substrate_def = SubstrateDef(config_tab=None)
substrate_def.render()