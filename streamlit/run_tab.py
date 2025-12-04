"""
run_tab.py - Run tab: execute a simulation and see terminal text output
Streamlit Version

Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Rf. Credits.md
"""

import streamlit as st
import os
import time
import logging
import shutil
import subprocess
import threading
import queue
from pathlib import Path
from datetime import datetime
import tempfile

class RunModel:
    def __init__(self, xml_creator=None):
        self.xml_creator = xml_creator
        
        # Configuration attributes
        self.rules_flag = xml_creator.rules_flag if xml_creator else False
        self.nanohub_flag = False  # Set based on deployment
        self.current_dir = os.getcwd()
        self.config_file = None
        self.output_dir = 'output'
        
        # Tab references (set externally)
        self.microenv_tab = None
        self.user_params_tab = None
        self.rules_tab = None
        self.vis_tab = None
        
        # Process management
        self.process = None
        self.process_running = False
        
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'run_output' not in st.session_state:
            st.session_state.run_output = []
        
        if 'process_running' not in st.session_state:
            st.session_state.process_running = False
            
        if 'exec_name' not in st.session_state:
            if self.nanohub_flag:
                st.session_state.exec_name = 'myproj'
            else:
                st.session_state.exec_name = 'template'
        
        if 'config_xml_name' not in st.session_state:
            st.session_state.config_xml_name = 'config.xml'
            
        if 'output_queue' not in st.session_state:
            st.session_state.output_queue = queue.Queue()
    
    def append_output(self, message):
        """Add message to output display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        st.session_state.run_output.append(formatted_msg)
        
    def clear_output(self):
        """Clear the output display"""
        st.session_state.run_output = []
    
    def read_process_output(self, pipe, output_queue):
        """Read process output in a separate thread"""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    output_queue.put(line.strip())
        except:
            pass
        finally:
            pipe.close()
    
    def run_model_cb(self):
        """Execute the simulation"""
        logging.debug('===========  run_model_cb():  ============')
        
        exec_file = st.session_state.exec_name
        
        # Check if executable exists
        if not Path(exec_file).is_file():
            st.error(f"❌ Exec file {exec_file} does not exist.")
            return False
        
        # Validate cell definitions (if xml_creator available)
        if self.xml_creator:
            try:
                self.xml_creator.celldef_tab.check_valid_cell_defs()
            except Exception as e:
                st.error(f"❌ Cell definition error: {str(e)}")
                return False
        
        # Check SVG/Full interval match (if config_tab available)
        if self.xml_creator and hasattr(self.xml_creator, 'config_tab'):
            config = self.xml_creator.config_tab
            if hasattr(config, 'save_svg') and hasattr(config, 'save_full'):
                if config.save_svg and config.save_full:
                    if config.svg_interval != config.full_interval:
                        st.warning("⚠️ The output intervals for SVG and full (in Config Basics) do not match.")
        
        try:
            # Prepare output directory
            os.chdir(self.current_dir)
            
            if self.nanohub_flag:
                # NanoHUB workflow
                os.system('rm -rf tmpdir*')
                time.sleep(1)
                if os.path.isdir('tmpdir'):
                    tname = tempfile.mkdtemp(suffix='.bak', prefix='tmpdir_', dir='.')
                    shutil.move('tmpdir', tname)
                os.makedirs('tmpdir')
                tdir = os.path.abspath('tmpdir')
                self.output_dir = '.'
            else:
                # Standard workflow
                if self.xml_creator and hasattr(self.xml_creator.config_tab, 'folder'):
                    self.output_dir = self.xml_creator.config_tab.folder
                else:
                    self.output_dir = 'output'
                
                os.system(f'rm -rf {self.output_dir}')
                logging.debug(f'run_tab.py: doing: mkdir {self.output_dir}')
                try:
                    os.makedirs(self.output_dir)
                except:
                    pass
                time.sleep(1)
                tdir = os.path.abspath(self.output_dir)
            
            # Update and save XML
            if self.xml_creator:
                if not self.xml_creator.update_xml_from_gui():
                    st.error("❌ Error updating XML from GUI")
                    return False
                
                self.xml_creator.tree.write(self.config_file)
                # Assuming pretty_print function exists
                # pretty_print(self.config_file, self.config_file)
                
                default_config_file = os.path.join(self.output_dir, "PhysiCell_settings.xml")
                abs_default_config_file = os.path.abspath(default_config_file)
                shutil.copy(self.config_file, default_config_file)
            
            # Change to tmpdir for nanoHUB
            if self.nanohub_flag:
                tdir = os.path.abspath('tmpdir')
                os.chdir(tdir)
            
            # Reset visualization if available
            if self.vis_tab and self.xml_creator:
                self.xml_creator.vis_tab.reset_domain_box()
                self.xml_creator.vis_tab.reset_model_flag = True
                self.xml_creator.vis_tab.reset_plot_range()
                self.xml_creator.vis_tab.output_folder = self.output_dir
                self.xml_creator.vis_tab.output_dir = self.output_dir
                self.xml_creator.vis_tab.reset_model()
                self.xml_creator.vis_tab.update_plots()
            
            # Start the process
            st.session_state.process_running = True
            self.append_output("🚀 Executing process...")
            
            exec_str = st.session_state.exec_name
            xml_str = st.session_state.config_xml_name
            
            self.append_output(f"Command: {exec_str} {xml_str}")
            
            if self.nanohub_flag:
                cmd = ["submit", "--local", exec_str, xml_str]
            else:
                cmd = [exec_str, xml_str]
            
            # Run process in background thread
            def run_process():
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    st.session_state.current_process = process
                    
                    # Read stdout
                    for line in process.stdout:
                        st.session_state.output_queue.put(('stdout', line.strip()))
                    
                    # Read stderr
                    for line in process.stderr:
                        st.session_state.output_queue.put(('stderr', line.strip()))
                    
                    # Wait for process to complete
                    return_code = process.wait()
                    
                    st.session_state.output_queue.put(('finished', return_code))
                    st.session_state.process_running = False
                    
                except Exception as e:
                    st.session_state.output_queue.put(('error', str(e)))
                    st.session_state.process_running = False
            
            # Start process thread
            thread = threading.Thread(target=run_process, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error running simulation: {str(e)}")
            st.session_state.process_running = False
            return False
    
    def cancel_model_cb(self):
        """Cancel the running simulation"""
        if st.session_state.process_running and hasattr(st.session_state, 'current_process'):
            try:
                process = st.session_state.current_process
                if self.nanohub_flag:
                    process.terminate()
                else:
                    process.kill()
                
                self.append_output("🛑 Process cancelled by user")
                st.session_state.process_running = False
                return True
            except Exception as e:
                st.error(f"Error cancelling process: {str(e)}")
                return False
        return False
    
    def check_process_output(self):
        """Check for new output from the running process"""
        if not hasattr(st.session_state, 'output_queue'):
            return
        
        try:
            while not st.session_state.output_queue.empty():
                msg_type, msg_content = st.session_state.output_queue.get_nowait()
                
                if msg_type == 'stdout':
                    self.append_output(msg_content)
                elif msg_type == 'stderr':
                    self.append_output(f"⚠️ {msg_content}")
                elif msg_type == 'finished':
                    self.append_output(f"✅ Process finished with return code: {msg_content}")
                    st.session_state.process_running = False
                elif msg_type == 'error':
                    self.append_output(f"❌ Error: {msg_content}")
                    st.session_state.process_running = False
        except:
            pass
    
    def render(self):
        """Render the Streamlit UI"""
        self.initialize_session_state()
        
        st.title("Run Simulation")
        
        # Control panel
        st.markdown("### Simulation Controls")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Run button
            if st.session_state.process_running:
                st.button(
                    "⏳ Running...",
                    disabled=True,
                    use_container_width=True,
                    type="secondary"
                )
            else:
                if st.button(
                    "▶️ Run Simulation",
                    use_container_width=True,
                    type="primary"
                ):
                    self.clear_output()
                    self.run_model_cb()
                    st.rerun()
        
        with col2:
            # Cancel button
            if st.button(
                "⏹️ Cancel",
                disabled=not st.session_state.process_running,
                use_container_width=True,
                type="secondary"
            ):
                self.cancel_model_cb()
                st.rerun()
        
        # Configuration inputs
        st.markdown("### Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            exec_name = st.text_input(
                "Executable:",
                value=st.session_state.exec_name,
                key="exec_input",
                disabled=st.session_state.process_running
            )
            if exec_name != st.session_state.exec_name:
                st.session_state.exec_name = exec_name
        
        with col2:
            config_name = st.text_input(
                "Config File:",
                value=st.session_state.config_xml_name,
                key="config_input",
                disabled=st.session_state.process_running
            )
            if config_name != st.session_state.config_xml_name:
                st.session_state.config_xml_name = config_name
        
        # Output display
        st.markdown("---")
        st.markdown("### Terminal Output")
        
        # Check for new output if process is running
        if st.session_state.process_running:
            self.check_process_output()
            # Auto-refresh while running
            time.sleep(0.5)
            st.rerun()
        
        # Display output in a text area
        output_text = "\n".join(st.session_state.run_output[-100:])  # Show last 100 lines
        
        output_container = st.container()
        with output_container:
            st.text_area(
                "Output Log",
                value=output_text,
                height=400,
                key="output_display",
                label_visibility="collapsed"
            )
        
        # Status indicator
        if st.session_state.process_running:
            st.info("🔄 Simulation is running... The page will refresh automatically.")
        else:
            st.success("✅ Ready to run simulation")
        
        # Clear output button
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("🗑️ Clear Output", disabled=st.session_state.process_running):
                self.clear_output()
                st.rerun()


# Main app
def main():
    st.set_page_config(
        page_title="Run Simulation",
        page_icon="▶️",
        layout="wide"
    )
    
    # Create RunModel instance
    run_model = RunModel()
    run_model.render()


if __name__ == "__main__":
    main()