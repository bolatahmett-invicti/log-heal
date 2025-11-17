"""
LogHeal - Web Interface
Streamlit-based ELK log analysis and automatic fix system
"""

import streamlit as st
import asyncio
import json
import os
from datetime import datetime
from elk_connector import create_elk_connector
from orchestrator import Orchestrator
import difflib

# Page configuration
st.set_page_config(
    page_title="LogHeal - AI Error Recovery",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styles
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .log-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .log-card:hover {
        background-color: #e9ecef;
        border-color: #1f77b4;
    }
    .error-badge {
        background-color: #dc3545;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .success-badge {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e7f3ff;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .diff-added {
        background-color: #d4edda;
        color: #155724;
    }
    .diff-removed {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state"""
    if 'elk_logs' not in st.session_state:
        st.session_state.elk_logs = []
    if 'selected_log' not in st.session_state:
        st.session_state.selected_log = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'code_changes' not in st.session_state:
        st.session_state.code_changes = {}
    if 'processing' not in st.session_state:
        st.session_state.processing = False


def fetch_elk_logs():
    """Fetch logs from ELK"""
    with st.spinner("🔍 Fetching logs from ELK..."):
        elk = create_elk_connector(
            use_mock=st.session_state.get('use_mock', False),
            host=st.session_state.get('elk_host', 'localhost'),
            port=int(st.session_state.get('elk_port', 9200)),
            username=st.session_state.get('elk_username'),
            password=st.session_state.get('elk_password')
        )
        
        if elk.connect():
            logs = elk.fetch_error_logs(
                time_range_minutes=int(st.session_state.get('time_range', 180))
            )
            st.session_state.elk_logs = logs
            if logs:
                st.success(f"✅ Found {len(logs)} logs")
                # Debug: Show first log fields
                if len(logs) > 0:
                    st.write("Debug - First log keys:", list(logs[0].keys()))
            else:
                st.warning("⚠️ No logs found")
        else:
            st.error("❌ Could not connect to ELK")


def display_log_card(log, index):
    """Display log card"""
    # Card container
    with st.container():
        # Check if selected
        is_selected = (st.session_state.selected_log is not None and 
                      st.session_state.selected_log.get('message') == log.get('message'))
        
        border_color = "#1f77b4" if is_selected else "#ddd"
        bg_color = "#e7f3ff" if is_selected else "#f8f9fa"
        
        # Get log fields (different field names possible)
        service = log.get('service', log.get('service.name', log.get('app', log.get('application', 'Service'))))
        msg = log.get('error_message', log.get('message', log.get('msg', log.get('text', str(log.get('exception', {}).get('message', 'No log message'))))))
        timestamp = log.get('timestamp', log.get('@timestamp', log.get('time', 'N/A')))
        level = log.get('level', log.get('severity', log.get('log.level', 'ERROR')))
        
        # Card HTML
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 0.5rem; border: 2px solid {border_color}; 
                    margin: 0.5rem 0; background-color: {bg_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <strong>📌 {service}</strong><br>
                    <span style="color: #666;">{str(msg)[:80]}...</span>
                </div>
                <div style="text-align: right; min-width: 150px;">
                    <span style="background-color: #dc3545; color: white; padding: 0.25rem 0.5rem; 
                                 border-radius: 0.25rem; font-size: 0.75rem;">{level}</span><br>
                    <small style="color: #666;">{str(timestamp)[:19]}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Full log content - with expander
        with st.expander("📄 Full Log Content", expanded=False):
            st.json(log)
        
        # Button
        if st.button("🔧 Analyze", key=f"analyze_{index}", use_container_width=True):
            st.session_state.selected_log = log
            st.rerun()


async def process_log_async(log, repo_path):
    """Process selected log"""
    orchestrator = Orchestrator(
        repo_path=repo_path,
        enable_rag=True
    )
    
    # Callback to save code changes
    def save_code_changes(filename, original, fixed):
        if 'code_changes' not in st.session_state:
            st.session_state.code_changes = {}
        st.session_state.code_changes[filename] = {
            'original': original,
            'fixed': fixed
        }
    
    result = await orchestrator.process_logs([log], {}, save_changes_callback=save_code_changes)
    return result


def show_code_diff(original, fixed, filename):
    """Show code changes as diff"""
    st.markdown(f"### 📄 {filename}")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Changes", "📝 Original", "✅ Fixed"])
    
    with tab1:
        # Show diff
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f'{filename} (Original)',
            tofile=f'{filename} (Fixed)',
            lineterm=''
        )
        
        diff_text = ''.join(diff)
        if diff_text:
            st.code(diff_text, language='diff')
        else:
            st.info("No changes")
    
    with tab2:
        st.code(original, language='python' if filename.endswith('.py') else 'csharp' if filename.endswith('.cs') else 'java')
    
    with tab3:
        st.code(fixed, language='python' if filename.endswith('.py') else 'csharp' if filename.endswith('.cs') else 'java')


def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🩺 LogHeal - AI Error Recovery</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar - Settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # ELK Connection
        st.subheader("🔌 ELK Connection")
        use_mock = st.checkbox("Use mock data (Test)", value=False)
        st.session_state.use_mock = use_mock
        
        if not use_mock:
            elk_host = st.text_input("ELK Host", value=os.getenv("ELK_HOST", "localhost"))
            elk_port = st.text_input("ELK Port", value=os.getenv("ELK_PORT", "9200"))
            elk_username = st.text_input("Username (optional)", value=os.getenv("ELK_USERNAME", ""))
            elk_password = st.text_input("Password (optional)", type="password", value=os.getenv("ELK_PASSWORD", ""))
            
            st.session_state.elk_host = elk_host
            st.session_state.elk_port = elk_port
            st.session_state.elk_username = elk_username if elk_username else None
            st.session_state.elk_password = elk_password if elk_password else None
        
        time_range = st.slider("Time Range (minutes)", 30, 1440, 180)
        st.session_state.time_range = time_range
        
        st.markdown("---")
        
        # Codebase Settings
        st.subheader("📂 Codebase")
        repo_path = st.text_input(
            "Project Path",
            value=r"C:\Users\AhmetBolat\Projects\Claude\TestSystem"
        )
        st.session_state.repo_path = repo_path
        
        st.markdown("---")
        
        # Fetch Logs
        if st.button("🔄 Refresh Logs", use_container_width=True):
            fetch_elk_logs()
    
    # Main Content
    if not st.session_state.elk_logs:
        # Welcome screen
        st.markdown("""
        <div class="info-box">
            <h3>👋 Welcome!</h3>
            <p>To analyze ELK logs and create automatic fixes:</p>
            <ol>
                <li>Configure settings in the left sidebar</li>
                <li>Click "Refresh Logs" button</li>
                <li>Select a log from the list</li>
                <li>Review analysis results and fixes</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Fetch Logs and Start", type="primary"):
            fetch_elk_logs()
            st.rerun()
    
    else:
        # Two columns: Log List and Details
        col_list, col_detail = st.columns([1, 2])
        
        with col_list:
            st.subheader(f"📋 ELK Logs ({len(st.session_state.elk_logs)})")
            
            # Debug info
            if len(st.session_state.elk_logs) == 0:
                st.warning("⚠️ No logs found!")
            else:
                st.info(f"✅ Listing {len(st.session_state.elk_logs)} logs")
            
            # List logs
            for idx, log in enumerate(st.session_state.elk_logs):
                display_log_card(log, idx)
                st.markdown("---")
        
        with col_detail:
            if st.session_state.selected_log:
                st.subheader("🔍 Log Details")
                
                # Show selected log
                selected = st.session_state.selected_log
                
                # Log information
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.metric("Error Type", selected.get('level', 'N/A'))
                    st.metric("Service", selected.get('service', 'N/A'))
                with info_col2:
                    st.metric("Time", selected.get('timestamp', selected.get('@timestamp', 'N/A')))
                
                # Log message
                st.text_area("Message", selected.get('message', 'N/A'), height=100, disabled=True)
                
                # JSON view
                with st.expander("📄 Full Log (JSON)"):
                    st.json(selected)
                
                st.markdown("---")
                
                # Analysis button
                if not st.session_state.processing:
                    if st.button("🤖 Start AI Analysis", type="primary", use_container_width=True):
                        st.session_state.processing = True
                        st.rerun()
                
                # Analysis process
                if st.session_state.processing:
                    with st.spinner("🔄 AI agents working... (This may take a while)"):
                        try:
                            # Run async function
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            result = loop.run_until_complete(
                                process_log_async(
                                    selected,
                                    st.session_state.repo_path
                                )
                            )
                            loop.close()
                            
                            st.session_state.analysis_result = result
                            st.session_state.processing = False
                            st.success("✅ Analysis completed!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error occurred: {str(e)}")
                            st.session_state.processing = False
                
                # Show results
                if st.session_state.analysis_result and not st.session_state.processing:
                    result = st.session_state.analysis_result
                    
                    st.markdown("---")
                    st.subheader("📊 Analysis Results")
                    
                    if result.success:
                        st.success(f"🎉 Success! Branch: `{result.branch_name}`")
                        
                        # Changed files
                        if result.files_changed:
                            st.markdown("### 📝 Changed Files")
                            
                            for file_path in result.files_changed:
                                st.markdown(f"- ✅ `{file_path}`")
                        
                        # Commit message
                        with st.expander("💬 Commit Message"):
                            st.code(result.commit_message)
                        
                        # Code changes (if any)
                        if hasattr(st.session_state, 'code_changes') and st.session_state.code_changes:
                            st.markdown("---")
                            st.subheader("🔧 Code Changes")
                            
                            for filename, changes in st.session_state.code_changes.items():
                                if 'original' in changes and 'fixed' in changes:
                                    show_code_diff(
                                        changes['original'],
                                        changes['fixed'],
                                        filename
                                    )
                    else:
                        st.warning("⚠️ Operation could not be completed. Check logs for details.")
            
            else:
                st.info("👈 Please select a log from the left")


if __name__ == "__main__":
    main()
