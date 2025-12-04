"""
User Parameters Tab - Streamlit Version
Translated from PyQt5 to Streamlit

Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
"""

import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import re

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