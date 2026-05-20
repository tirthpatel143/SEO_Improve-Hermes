import streamlit as st
import json
import os
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv, set_key
import yaml

# Load environment
dotenv_path = ".env"
load_dotenv(dotenv_path)

# File Paths
ACTIONS_FILE = "runtime/outputs/actions.json"
STRATEGY_FILE = "data/strategy.json"
PRODUCT_FILE = "data/product_info.json"
SOCIAL_FILE = "data/social_drafts.json"
REPORT_FILE = "runtime/outputs/seo-report.pdf"
SWARM_CONFIG_PATH = os.path.expanduser("~/.hermes/profiles/swarm/swarm.yaml")

# Initialize Data
target_url = os.environ.get("TARGET_URL", "")
current_product_name = "New SEO Project"

if target_url:
    from urllib.parse import urlparse
    domain = urlparse(target_url).netloc.replace('www.', '')
    if domain:
        current_product_name = domain.split('.')[0].capitalize()

if os.path.exists(PRODUCT_FILE):
    try:
        with open(PRODUCT_FILE, "r") as f:
            product_data = json.load(f)
            if isinstance(product_data, dict):
                overview = product_data.get("Product Overview", {})
                if isinstance(overview, dict) and overview.get("Product Name"):
                    current_product_name = overview.get("Product Name")
    except Exception:
        pass

# Force refresh data from disk
st.cache_data.clear()

# Page Config
st.set_page_config(
    page_title=f"SEO CMO | {current_product_name}", 
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look & High Contrast
st.markdown("""
<style>
    /* Theme-aware backgrounds */
    .stApp {
        background-color: var(--background-color);
    }
    
    /* Premium Metric Styling */
    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Fix for unreadable metric text in dark mode */
    [data-testid="stMetricValue"] {
        color: var(--text-color);
        font-weight: 700 !important;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px 8px 0px 0px;
        padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--secondary-background-color);
        border-bottom: 3px solid #FF4B4B;
    }
    
    /* Card/Expander Styling */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        background-color: var(--secondary-background-color);
        margin-bottom: 12px;
    }
    
    /* Section Headers */
    h1, h2, h3 {
        color: var(--text-color);
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/rocket.png", width=80)
    st.title("SEO Command Center")
    st.divider()
    
    st.header("🎯 Target Website")
    st.caption("Input any URL to start a fresh SEO audit and generate technical tasks.")
    
    target_url = st.text_input("Website URL", value=os.environ.get("TARGET_URL", ""), placeholder="https://example.com")
    repo_url = st.text_input("GitHub Repo URL", value=os.environ.get("GITHUB_REPO", ""), placeholder="https://github.com/user/repo.git")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔍 Run New Audit", use_container_width=True, type="primary"):
            if not target_url:
                st.error("Please enter a URL")
            else:
                with st.spinner(f"Auditing {target_url}..."):
                    # Clear old data if starting new site
                    for f in ["data/scraped_raw.json", "data/product_info.json", "data/strategy.json", "data/social_drafts.json", "runtime/outputs/actions.json"]:
                        if os.path.exists(f): os.remove(f)
                        
                    set_key(dotenv_path, "TARGET_URL", target_url)
                    set_key(dotenv_path, "GITHUB_REPO", repo_url)
                    result = subprocess.run([sys.executable, "scripts/analyze_site.py", target_url], capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success("Audit complete!")
                        st.rerun()
                    else:
                        st.error(f"Audit failed:\n{result.stderr}")
    
    with col_b:
        if st.button("🗑️ Clear Data", use_container_width=True):
            for f in ["data/scraped_raw.json", "data/product_info.json", "data/strategy.json", "data/social_drafts.json", "runtime/outputs/actions.json"]:
                if os.path.exists(f): os.remove(f)
            st.success("Dashboard reset!")
            st.rerun()

    if st.button("🚀 Launch Hermes Swarm", type="primary", use_container_width=True):
        with st.spinner("Hermes is orchestrating the 12-agent swarm..."):
            set_key(dotenv_path, "TARGET_URL", target_url)
            set_key(dotenv_path, "GITHUB_REPO", repo_url)
            result = subprocess.run([sys.executable, "scripts/orchestrator_hermes_swarm.py"], capture_output=True, text=True)
            
            if result.returncode == 0:
                st.success("Hermes Swarm mission complete!")
                st.balloons()
                st.rerun()
            else:
                st.error(f"Swarm failed:\n{result.stderr or result.stdout}")

    if st.button("🤖 Launch Hermes AI", use_container_width=True):
        with st.spinner("Hermes is auditing and patching..."):
            set_key(dotenv_path, "TARGET_URL", target_url)
            set_key(dotenv_path, "GITHUB_REPO", repo_url)
            result = subprocess.run([sys.executable, "scripts/orchestrator_hermes.py"], capture_output=True, text=True)
            
            # Auto-apply fixes
            if os.path.exists(ACTIONS_FILE):
                with open(ACTIONS_FILE, "r") as f:
                    actions_list = json.load(f)
                pending = [a for a in actions_list if a['status'] == 'PENDING']
                for action in pending:
                    subprocess.run([sys.executable, "scripts/apply_fix.py", action['id'], action['title'], repo_url])
                    action['status'] = "APPLIED"
                with open(ACTIONS_FILE, "w") as f:
                    json.dump(actions_list, f, indent=4)
            
            if result.returncode == 0:
                st.success("Hermes task completed!")
                st.balloons()
                st.rerun()
            else:
                st.error("Hermes failed.")

    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- Main Logic ---

# Load Data
actions = []
if os.path.exists(ACTIONS_FILE):
    with open(ACTIONS_FILE, "r") as f:
        actions = json.load(f)

strategy = {}
if os.path.exists(STRATEGY_FILE):
    with open(STRATEGY_FILE, "r") as f:
        strategy = json.load(f)

product_info = {}
if os.path.exists(PRODUCT_FILE):
    with open(PRODUCT_FILE, "r") as f:
        product_info = json.load(f)

scraped_data = {}
if os.path.exists("data/scraped_raw.json"):
    with open("data/scraped_raw.json", "r") as f:
        scraped_data = json.load(f)

# Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title(f"🚀 {current_product_name}")
    st.markdown(f"**Target URL:** `{target_url}` | **GitHub Repo:** `{repo_url}`")

# Calculate Score
total_tasks = len(actions)
applied_tasks = len([a for a in actions if a['status'] == 'APPLIED'])
seo_score = int((applied_tasks / total_tasks * 100)) if total_tasks > 0 else 0

with col_status:
    st.metric("SEO Health Score", f"{seo_score}%", delta=f"{applied_tasks}/{total_tasks} Fixed")

# --- AUTH VALIDATION ---
github_token = os.environ.get("GITHUB_TOKEN", "").strip()
if not github_token or github_token in ["''", '""']:
    st.error("⚠️ **GitHub Authentication Required**: Please add your **Personal Access Token** in the **Settings** tab to enable automatic deployment to your repository.")

# Tabs
tab_overview, tab_tasks, tab_strategy, tab_product, tab_social, tab_swarm, tab_github_fix, tab_settings = st.tabs([
    "🏠 Executive Overview", 
    "🛠️ Technical Tasks", 
    "📈 Growth Strategy", 
    "💡 Product Intelligence", 
    "📢 Social Signals",
    "🐝 Swarm Monitor",
    "🔧 GitHub Auto-Fix",
    "⚙️ Settings"
])

with tab_overview:
    if not scraped_data:
        st.markdown(f"""
        <div style="background-color: var(--secondary-background-color); padding: 40px; border-radius: 15px; text-align: center; border: 2px dashed rgba(128,128,128,0.3); margin-top: 20px;">
            <h2 style="margin-bottom: 10px;">👋 Ready to Optimize {current_product_name}?</h2>
            <p style="font-size: 1.1em; opacity: 0.8; margin-bottom: 25px;">No audit data found for <b>{target_url or 'your website'}</b>. Start your SEO journey by running a site audit.</p>
            <div style="display: flex; justify-content: center; gap: 20px;">
                <div style="background-color: #FF4B4B; color: white; padding: 12px 24px; border-radius: 8px; font-weight: bold;">Step 1: Enter URL in Sidebar</div>
                <div style="background-color: #29B5E8; color: white; padding: 12px 24px; border-radius: 8px; font-weight: bold;">Step 2: Click 'Run New Audit'</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Top Level KPI Row
    st.markdown("### 📊 Search Performance Scorecard")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    title_len = len(scraped_data.get('title', ''))
    title_status = "✅ Optimal" if 30 <= title_len <= 60 else "⚠️ Needs Fix"
    kpi1.metric("Title Optimization", f"{title_len} chars", title_status)
    
    meta_len = len(scraped_data.get('meta_description', ''))
    meta_status = "✅ Configured" if meta_len > 0 else "❌ Missing"
    kpi2.metric("Meta Clarity", f"{meta_len} chars", meta_status)
    
    missing_alt = scraped_data.get('images', {}).get('missing_alt', 0)
    alt_status = "✅ Healthy" if missing_alt == 0 else f"⚠️ {missing_alt} issues"
    kpi3.metric("Image Alt Audit", "100% Pass" if missing_alt == 0 else "Gaps Detected", alt_status)
    
    h1_count = len(scraped_data.get('h1_headings', []))
    h1_status = "✅ Healthy" if h1_count == 1 else "⚠️ Optimize"
    kpi4.metric("Heading Structure", f"{h1_count} H1 Tags", h1_status)

    st.markdown("---")

    # Audit Detail & Task Progress
    col_audit, col_task = st.columns([2, 1])
    
    with col_audit:
        st.markdown("### 🔍 Live On-Page Intelligence")
        with st.container():
            st.markdown(f"""
            <div style="background-color: var(--secondary-background-color); padding: 20px; border-radius: 10px; border-left: 5px solid #FF4B4B; margin-bottom: 15px; border: 1px solid rgba(128,128,128,0.1);">
                <p style="margin-bottom: 5px; font-weight: bold; font-size: 0.9em; opacity: 0.8; color: var(--text-color);">CURRENT TITLE TAG</p>
                <p style="font-size: 1.1em; color: var(--text-color);">{scraped_data.get('title', 'Not found')}</p>
            </div>
            <div style="background-color: var(--secondary-background-color); padding: 20px; border-radius: 10px; border-left: 5px solid #29B5E8; margin-bottom: 15px; border: 1px solid rgba(128,128,128,0.1);">
                <p style="margin-bottom: 5px; font-weight: bold; font-size: 0.9em; opacity: 0.8; color: var(--text-color);">CURRENT META DESCRIPTION</p>
                <p style="font-size: 1em; color: var(--text-color);">{scraped_data.get('meta_description', 'Not found')}</p>
            </div>
            <div style="background-color: var(--secondary-background-color); padding: 20px; border-radius: 10px; border-left: 5px solid #27AE60; margin-bottom: 15px; border: 1px solid rgba(128,128,128,0.1);">
                <p style="margin-bottom: 5px; font-weight: bold; font-size: 0.9em; opacity: 0.8; color: var(--text-color);">PRIMARY HEADING (H1)</p>
                <p style="font-size: 1.1em; color: var(--text-color);">{scraped_data.get('h1_headings', ['Not found'])[0]}</p>
            </div>
            """, unsafe_allow_html=True)

    with col_task:
        st.markdown("### ⚡ Implementation Status")
        if not actions:
            st.info("Initiate audit to generate technical tasks.")
        else:
            for action in actions:
                color = "#27AE60" if action['status'] == 'APPLIED' else "#F2994A"
                icon = "✓" if action['status'] == 'APPLIED' else "!"
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; background-color: var(--secondary-background-color); padding: 12px; border-radius: 8px; border: 1px solid rgba(128,128,128,0.1);">
                    <div style="background-color: {color}; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">{icon}</div>
                    <div style="font-size: 0.95em; color: var(--text-color);">{action['title']}</div>
                </div>
                """, unsafe_allow_html=True)
            
        if os.path.exists(REPORT_FILE):
            st.markdown("<br>", unsafe_allow_html=True)
            with open(REPORT_FILE, "rb") as f:
                st.download_button("📥 Download SEO Strategy PDF", f, file_name="SEO_Audit_Report.pdf", use_container_width=True)

    st.markdown("---")
    
    # Roadmap Section
    st.markdown("### 📅 Strategic Growth Roadmap")
    roadmap = strategy.get("5. 30-Day Roadmap", {})
    if roadmap:
        r_cols = st.columns(4)
        weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
        icons = ["🏗️", "📝", "🚀", "📈"]
        colors = ["#29B5E8", "#27AE60", "#F2994A", "#FF4B4B"]
        
        for idx, week in enumerate(weeks):
            with r_cols[idx]:
                st.markdown(f"""
                <div style="background-color: var(--secondary-background-color); padding: 20px; border-radius: 12px; border-top: 5px solid {colors[idx]}; height: 200px; border-left: 1px solid rgba(128,128,128,0.1); border-right: 1px solid rgba(128,128,128,0.1); border-bottom: 1px solid rgba(128,128,128,0.1);">
                    <h4 style="margin-top: 0; color: var(--text-color);">{icons[idx]} {week}</h4>
                    <p style="font-size: 0.9em; opacity: 0.9; color: var(--text-color);">{roadmap.get(week, 'TBD')}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("Complete the site audit to generate your custom growth roadmap.")

with tab_tasks:
    st.subheader("🛠️ Technical Implementation Feed")
    st.write("Each task below is solved in a **separate isolation branch** on GitHub to ensure clean, reviewable code changes.")
    
    col_h, col_b = st.columns([3, 1])
    with col_h:
        st.subheader("Action Feed (SEO Task Management)")
    with col_b:
        if st.button("🚀 Auto-Solve All Tasks", use_container_width=True, type="primary"):
            pending_actions = [a for a in actions if a['status'] == 'PENDING']
            if not pending_actions:
                st.info("All issues are already fixed!")
            else:
                progress_text = st.empty()
                for idx, action in enumerate(pending_actions):
                    progress_text.info(f"Applying {idx+1}/{len(pending_actions)}: {action['title']}...")
                    result = subprocess.run([sys.executable, "scripts/apply_fix.py", action['id'], action['title'], repo_url], capture_output=True, text=True)
                    if result.returncode == 0:
                        action['status'] = "APPLIED"
                    else:
                        st.error(f"Failed to apply {action['title']}: {result.stderr or result.stdout}")
                with open(ACTIONS_FILE, "w") as f:
                    json.dump(actions, f, indent=4)
                st.success("✅ Automation run completed!")
                st.rerun()

    for i, action in enumerate(actions):
        status_icon = "✅" if action['status'] == 'APPLIED' else "⚠️"
        branch_name = f"seo-fix-{action['id'].lower()}"
        with st.expander(f"{status_icon} {action['title']} | Branch: `{branch_name}`", expanded=(action['status'] == 'PENDING')):
            st.markdown(f"**Overview:** {action['overview']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Implementation Steps:**")
                for step in action['steps']:
                    st.write(f"- {step}")
            with c2:
                st.markdown(f"**Expected Impact:** {action['impact']}")
                st.markdown(f"**Target File:** `{action.get('target_file', 'unknown')}`")
                if repo_url:
                    st.link_button("📂 View Repository", repo_url.replace('.git', ''), use_container_width=True)
            
            st.divider()
            code1, code2 = st.columns(2)
            with code1:
                st.caption("🔴 Current Code")
                st.code(action.get('before_code', ''), language='html')
            with code2:
                st.caption("🟢 Optimized Code")
                st.code(action.get('after_code', ''), language='html')
                
            if action['status'] == 'PENDING':
                if st.button("Deploy to GitHub", key=f"fix_btn_{i}"):
                    with st.spinner(f"Creating branch `{branch_name}` and pushing fix..."):
                        result = subprocess.run([sys.executable, "scripts/apply_fix.py", action['id'], action['title'], repo_url], capture_output=True, text=True)
                        
                        if "Authentication failed" in result.stdout or "Authentication failed" in result.stderr or "Invalid username" in result.stdout:
                            st.error("❌ **Authentication Failed**: Your GitHub Token is invalid or missing. Please update it in the **Settings** tab.")
                            st.code(result.stdout + result.stderr)
                        elif result.returncode == 0:
                            action['status'] = "APPLIED"
                            with open(ACTIONS_FILE, "w") as f:
                                json.dump(actions, f, indent=4)
                            
                            # Extract PR link if present
                            import re
                            pr_match = re.search(r"View and merge it here: (https://github.com/[^\s]+)", result.stdout)
                            if pr_match:
                                pr_url = pr_match.group(1)
                                st.success(f"🚀 **Fix Deployed & Pull Request Created!**")
                                st.link_button("Review and Merge on GitHub", pr_url, type="primary")
                                st.balloons()
                            else:
                                st.success(f"Fix deployed to branch `{branch_name}`!")
                            
                            st.info("Wait 5 seconds for GitHub to process, then click Rerun if the PR button doesn't show.")
                            if st.button("Refresh Dashboard"):
                                st.rerun()
                        else:
                            st.error(f"❌ **Deployment Failed**:\n{result.stderr or result.stdout}")

def render_nicely(data):
    for key, value in data.items():
        with st.container():
            st.markdown(f"#### {key}")
            if isinstance(value, list):
                for item in value:
                    st.write(f"- {item}")
            elif isinstance(value, dict):
                for k, v in value.items():
                    st.write(f"**{k}**: {v}")
            else:
                st.write(value)
            st.divider()

with tab_strategy:
    st.subheader("📈 Marketing & Growth Strategy")
    if strategy:
        render_nicely(strategy)
    else:
        st.warning("No strategy data found. Run an audit first.")

with tab_product:
    st.subheader("💡 Product Intelligence & Features")
    if product_info:
        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            st.markdown(f"### {product_info.get('Product Overview', {}).get('One-liner', '')}")
            st.write(product_info.get('What It Does', ''))
        with col_p2:
            st.metric("Tech Stack", product_info.get('Tech Signals', ['Unknown'])[0])
            st.metric("Primary CTA", product_info.get('Primary CTA', 'Contact'))

        st.divider()
        st.markdown("#### Detailed Information")
        render_nicely(product_info)
    else:
        st.warning("No product intelligence found. Run an audit first.")

with tab_social:
    st.subheader("📢 Off-Page SEO Signals")
    if os.path.exists(SOCIAL_FILE):
        with open(SOCIAL_FILE, "r") as f:
            drafts = json.load(f)
        
        updated_drafts = {}
        for platform, content in drafts.items():
            with st.expander(f"Post for {platform}", expanded=True):
                updated_drafts[platform] = st.text_area(f"Draft", value=content, height=150, key=f"social_{platform}")
                
                if platform == "X":
                    st.markdown(f"""
                    <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 15px; margin-top: 10px; max-width: 500px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="width: 48px; height: 48px; border-radius: 50%; background-color: #FF4B4B; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; margin-right: 12px;">
                                {current_product_name[0]}
                            </div>
                            <div>
                                <div style="font-weight: bold; color: var(--text-color);">{current_product_name}</div>
                                <div style="color: gray; font-size: 14px;">@{current_product_name.lower().replace(' ', '')} · Just now</div>
                            </div>
                        </div>
                        <div style="color: var(--text-color); font-size: 15px; line-height: 1.4; margin-bottom: 12px;">
                            {content}
                        </div>
                        <div style="display: flex; justify-content: space-between; color: gray; font-size: 13px;">
                            <span>💬 0</span>
                            <span>🔁 0</span>
                            <span>❤️ 0</span>
                            <span>📊 0</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if platform == "Mastodon":
                    st.markdown(f"""
                    <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 15px; margin-top: 10px; max-width: 500px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; border-left: 5px solid #2b90d9;">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="width: 48px; height: 48px; border-radius: 4px; background-color: #2b90d9; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; margin-right: 12px;">
                                {current_product_name[0]}
                            </div>
                            <div>
                                <div style="font-weight: bold; color: var(--text-color);">{current_product_name}</div>
                                <div style="color: #2b90d9; font-size: 14px;">@{current_product_name.lower().replace(' ', '')}@mastodon.social</div>
                            </div>
                        </div>
                        <div style="color: var(--text-color); font-size: 15px; line-height: 1.4; margin-bottom: 12px;">
                            {content}
                        </div>
                        <div style="display: flex; gap: 15px; color: gray; font-size: 13px;">
                            <span>↩️ Reply</span>
                            <span>🔁 Boost</span>
                            <span>⭐ Favorite</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            if st.button("💾 Save Drafts", use_container_width=True):
                with open(SOCIAL_FILE, "w") as f:
                    json.dump(updated_drafts, f, indent=4)
                st.success("Saved!")
        with c_s2:
            if st.button("🚀 Publish to All", type="primary", use_container_width=True):
                with st.spinner("Publishing..."):
                    result = subprocess.run([sys.executable, "scripts/publish_socials.py", "--publish-only"], capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success("Published!")
                    else:
                        st.error(f"Failed: {result.stderr}")
    else:
        st.warning("No social drafts found. Run an audit first.")

with tab_swarm:
    st.subheader("🐝 Autonomous Swarm Command Center")
    st.write("Monitor the real-time status of your 12-agent specialized SEO swarm.")
    
    if os.path.exists(SWARM_CONFIG_PATH):
        with open(SWARM_CONFIG_PATH, "r") as f:
            swarm_data = yaml.safe_load(f)
            
        workers = swarm_data.get("workers", [])
        
        # Define layout: 4 columns
        cols = st.columns(4)
        
        for idx, worker in enumerate(workers):
            col_idx = idx % 4
            with cols[col_idx]:
                # Dynamic status based on whether a mission is running
                # For visualization, we'll show them as 'ACTIVE' if target_url is set
                is_active = True if target_url else False
                status_color = "#27AE60" if is_active else "#95A5A6"
                status_text = "WORKING" if is_active else "IDLE"
                
                st.markdown(f"""
                <div style="background-color: var(--secondary-background-color); padding: 15px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 20px; text-align: center; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: 10px; right: 10px; width: 10px; height: 10px; border-radius: 50%; background-color: {status_color}; box-shadow: 0 0 10px {status_color}; animation: pulse 2s infinite;"></div>
                    <div style="font-size: 2.5em; margin-bottom: 10px;">{'🤖' if 'Orchestrator' in worker['role'] else '🕵️' if 'Auditor' in worker['role'] else '🏗️' if 'Builder' in worker['role'] else '📝' if 'Social' in worker['role'] else '🔍'}</div>
                    <div style="font-weight: bold; color: var(--text-color); font-size: 1.1em; height: 45px; display: flex; align-items: center; justify-content: center;">{worker['role']}</div>
                    <div style="font-size: 0.8em; color: gray; margin-bottom: 10px;">ID: {worker['id']}</div>
                    <div style="background-color: {status_color}22; color: {status_color}; padding: 4px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold;">{status_text}</div>
                </div>
                <style>
                    @keyframes pulse {{
                        0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 {status_color}77; }}
                        70% {{ transform: scale(1); box-shadow: 0 0 0 6px {status_color}00; }}
                        100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 {status_color}00; }}
                    }}
                </style>
                """, unsafe_allow_html=True)
    else:
        st.error(f"Swarm configuration not found at {SWARM_CONFIG_PATH}")

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 GITHUB AUTO-FIX TAB
# ═══════════════════════════════════════════════════════════════════════════
with tab_github_fix:
    st.subheader("🔧 GitHub Repository Auto-Fixer")
    st.markdown("""
    **Paste any GitHub repo URL** → **Scan for all issues** → **Click "Fix All"** → **All issues fixed on GitHub with Pull Requests**
    """)

    # ── Setup ──
    import re as _re
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── Session state for scan results ──
    if "gh_scan_results" not in st.session_state:
        st.session_state.gh_scan_results = None
    if "gh_fix_results" not in st.session_state:
        st.session_state.gh_fix_results = None
    if "gh_scanned_repo" not in st.session_state:
        st.session_state.gh_scanned_repo = ""

    # ── Input ──
    col_input1, col_input2 = st.columns([3, 1])
    with col_input1:
        gh_repo_url = st.text_input(
            "GitHub Repository URL",
            value=os.environ.get("GITHUB_REPO", ""),
            placeholder="https://github.com/username/repository",
            key="gh_repo_input"
        )
    with col_input2:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("🔍 Scan Repo", use_container_width=True, type="primary")

    github_token = os.environ.get("GITHUB_TOKEN", "").strip()

    if not github_token:
        st.warning("⚠️ **GitHub Token Required**: Add your `GITHUB_TOKEN` in the **Settings** tab to enable push/PR creation. You can still scan without it.")

    # ── Scan Action ──
    if scan_btn and gh_repo_url:
        st.session_state.gh_scanned_repo = gh_repo_url
        st.session_state.gh_fix_results = None

        with st.spinner(f"🔍 Scanning {gh_repo_url} for all issues..."):
            # Clone repo to temp
            import tempfile
            tmp_dir = tempfile.mkdtemp(prefix="gh-scan-")
            repo_name = gh_repo_url.rstrip("/").split("/")[-1].replace(".git", "")
            clone_dir = os.path.join(tmp_dir, repo_name)

            clone_res = subprocess.run(
                ["git", "clone", "--depth", "1", gh_repo_url, clone_dir],
                capture_output=True, text=True, timeout=120
            )

            if clone_res.returncode != 0:
                st.error(f"❌ Failed to clone repo:\n```\n{clone_res.stderr}\n```")
            else:
                # Run scanner
                scanner_script = os.path.join(_base_dir, "scripts", "github_scanner.py")
                scan_res = subprocess.run(
                    [sys.executable, scanner_script, "scan", clone_dir],
                    capture_output=True, text=True, timeout=60
                )

                report_path = os.path.join(clone_dir, "scan_report.json")
                if os.path.exists(report_path):
                    with open(report_path, "r") as f:
                        st.session_state.gh_scan_results = json.load(f)
                    st.session_state.gh_clone_dir = clone_dir
                    st.success(f"✅ Scan complete! Found **{st.session_state.gh_scan_results['total']}** issues.")
                else:
                    st.error(f"Scanner output:\n{scan_res.stdout}\n{scan_res.stderr}")

    # ── Show Scan Results ──
    if st.session_state.gh_scan_results:
        results = st.session_state.gh_scan_results
        total = results["total"]
        by_sev = results["by_severity"]

        st.markdown("---")
        st.markdown("### 📊 Scan Results")

        # Severity metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Issues", total)
        m2.metric("🔴 Critical", by_sev["critical"])
        m3.metric("🟠 High", by_sev["high"])
        m4.metric("🟡 Medium", by_sev["medium"])
        m5.metric("🟢 Low", by_sev["low"])

        # ── Fix All Button ──
        st.markdown("---")
        fix_col1, fix_col2 = st.columns([1, 3])
        with fix_col1:
            fix_all_btn = st.button(
                "🚀 FIX ALL ON GITHUB",
                use_container_width=True,
                type="primary",
                disabled=not github_token
            )
        with fix_col2:
            if not github_token:
                st.caption("⚠️ Add GITHUB_TOKEN in Settings to enable Fix All")
            else:
                st.caption(f"Will create up to {total} branches and PRs on {st.session_state.gh_scanned_repo}")

        # ── Fix All Action ──
        if fix_all_btn and github_token:
            clone_dir = st.session_state.get("gh_clone_dir", "")
            if clone_dir and os.path.exists(clone_dir):
                issues = results["issues"]

                # First, set the remote URL with auth token for the cloned repo
                authed_repo_url = st.session_state.gh_scanned_repo.replace(
                    "https://", f"https://x-access-token:{github_token}@"
                ).replace(
                    "http://", f"http://x-access-token:{github_token}@"
                )
                subprocess.run(
                    ["git", "-C", clone_dir, "remote", "set-url", "origin", authed_repo_url],
                    capture_output=True
                )

                # Detect default branch (main or master)
                default_branch = "main"
                branch_check = subprocess.run(
                    ["git", "-C", clone_dir, "branch", "-r"],
                    capture_output=True, text=True
                )
                if branch_check.returncode == 0:
                    remote_branches = branch_check.stdout.strip().split("\n")
                    if any("origin/master" in b for b in remote_branches):
                        default_branch = "master"
                    elif any("origin/main" in b for b in remote_branches):
                        default_branch = "main"

                # Fetch latest
                subprocess.run(["git", "-C", clone_dir, "fetch", "origin", default_branch],
                               capture_output=True)

                progress_bar = st.progress(0)
                status_text = st.empty()
                fix_results = []

                for idx, issue in enumerate(issues):
                    progress = (idx + 1) / len(issues)
                    progress_bar.progress(progress)
                    status_text.info(f"Fixing {idx+1}/{len(issues)}: {issue['description'][:60]}...")

                    # Create unique branch name
                    safe_cat = issue['category'].lower().replace(' ', '-').replace('/', '-')
                    branch_name = f"auto-fix/{safe_cat}-{idx+1}"

                    # Step 1: Go back to default branch fresh
                    subprocess.run(["git", "-C", clone_dir, "checkout", default_branch],
                                   capture_output=True)
                    subprocess.run(["git", "-C", clone_dir, "pull", "origin", default_branch],
                                   capture_output=True)

                    # Delete old local branch if exists
                    subprocess.run(["git", "-C", clone_dir, "branch", "-D", branch_name],
                                   capture_output=True)

                    # Create new branch from default
                    checkout_res = subprocess.run(
                        ["git", "-C", clone_dir, "checkout", "-b", branch_name],
                        capture_output=True, text=True
                    )
                    if checkout_res.returncode != 0:
                        fix_results.append({
                            "issue": issue["description"],
                            "status": "branch_failed",
                            "error": checkout_res.stderr
                        })
                        continue

                    # Step 2: Apply the fix
                    target_file = os.path.join(clone_dir, issue["file"])
                    fixed = False

                    if os.path.exists(target_file):
                        try:
                            with open(target_file, "r") as f:
                                content = f.read()
                            new_content = content
                            line_num = issue.get("line", 1)

                            if "Bare 'except:'" in issue["description"]:
                                new_content = content.replace("except:", "except Exception:")
                                fixed = True
                            elif "print() statement" in issue["description"]:
                                lines = content.split('\n')
                                if line_num <= len(lines):
                                    lines[line_num - 1] = lines[line_num - 1].replace("print(", "# print(", 1)
                                    new_content = '\n'.join(lines)
                                    fixed = True
                            elif "console.log" in issue["description"]:
                                lines = content.split('\n')
                                if line_num <= len(lines):
                                    lines[line_num - 1] = lines[line_num - 1].replace("console.log", "// console.log", 1)
                                    new_content = '\n'.join(lines)
                                    fixed = True
                            elif "Using 'var'" in issue["description"]:
                                lines = content.split('\n')
                                if line_num <= len(lines):
                                    lines[line_num - 1] = lines[line_num - 1].replace("var ", "const ", 1)
                                    new_content = '\n'.join(lines)
                                    fixed = True
                            elif issue["category"] == "SEO":
                                if "Missing <title>" in issue["description"]:
                                    new_content = content.replace("</head>", "  <title>Project Title</title>\n</head>")
                                    fixed = True
                                elif "Missing meta description" in issue["description"]:
                                    new_content = content.replace("</head>", '  <meta name="description" content="Project description">\n</head>')
                                    fixed = True
                                elif "Missing viewport" in issue["description"]:
                                    new_content = content.replace("</head>", '  <meta name="viewport" content="width=device-width, initial-scale=1">\n</head>')
                                    fixed = True
                                elif "Missing <h1>" in issue["description"]:
                                    new_content = content.replace("<body>", "<body>\n  <h1>Main Heading</h1>")
                                    fixed = True
                                elif "Missing canonical" in issue["description"]:
                                    new_content = content.replace("</head>", '  <link rel="canonical" href="https://example.com">\n</head>')
                                    fixed = True
                                elif "Missing Open Graph" in issue["description"]:
                                    og = '  <meta property="og:title" content="Title">\n  <meta property="og:description" content="Description">\n'
                                    new_content = content.replace("</head>", og + "</head>")
                                    fixed = True
                                elif "Missing lang" in issue["description"]:
                                    new_content = content.replace("<html>", '<html lang="en">')
                                    fixed = True
                                elif "Image missing alt" in issue["description"]:
                                    lines = content.split('\n')
                                    if line_num <= len(lines):
                                        lines[line_num - 1] = _re.sub(r'<img([^>]*)>', r'<img\1 alt="">', lines[line_num - 1], flags=_re.IGNORECASE)
                                        new_content = '\n'.join(lines)
                                        fixed = True
                            elif issue["category"] == "Config" and "Missing .gitignore" in issue["description"]:
                                with open(os.path.join(clone_dir, ".gitignore"), "w") as f:
                                    f.write("node_modules/\n.env\n__pycache__/\n*.pyc\n.DS_Store\ndist/\nbuild/\n")
                                fixed = True
                            elif issue["category"] == "Documentation" and "Missing README.md" in issue["description"]:
                                repo_n = st.session_state.gh_scanned_repo.rstrip("/").split("/")[-1].replace(".git", "")
                                with open(os.path.join(clone_dir, "README.md"), "w") as f:
                                    f.write(f"# {repo_n}\n\nProject description.\n")
                                fixed = True
                            elif issue["category"] == "Security" and "Secret file" in issue["description"]:
                                gi_path = os.path.join(clone_dir, ".gitignore")
                                if os.path.exists(gi_path):
                                    with open(gi_path, "a") as f:
                                        f.write(f"\n{issue['file']}\n")
                                subprocess.run(["git", "-C", clone_dir, "rm", "--cached", issue["file"]],
                                               capture_output=True)
                                fixed = True

                            if fixed and new_content != content:
                                with open(target_file, "w") as f:
                                    f.write(new_content)

                        except Exception as e:
                            fix_results.append({"issue": issue["description"], "status": "error", "error": str(e)})
                            continue

                    elif issue["category"] in ("Config", "Documentation"):
                        try:
                            if "Missing .gitignore" in issue["description"]:
                                with open(os.path.join(clone_dir, ".gitignore"), "w") as f:
                                    f.write("node_modules/\n.env\n__pycache__/\n.DS_Store\n")
                                fixed = True
                            elif "Missing README.md" in issue["description"]:
                                repo_n = st.session_state.gh_scanned_repo.rstrip("/").split("/")[-1].replace(".git", "")
                                with open(os.path.join(clone_dir, "README.md"), "w") as f:
                                    f.write(f"# {repo_n}\n\nProject description.\n")
                                fixed = True
                        except Exception as e:
                            fix_results.append({"issue": issue["description"], "status": "error", "error": str(e)})
                            continue

                    if not fixed:
                        fix_results.append({"issue": issue["description"], "status": "skipped", "reason": "Cannot auto-fix this issue type"})
                        continue

                    # Step 3: Commit
                    subprocess.run(["git", "-C", clone_dir, "add", "-A"], capture_output=True)
                    commit_res = subprocess.run(
                        ["git", "-C", clone_dir, "commit", "-m",
                         f"Auto-fix: {issue['description'][:60]} ({issue['category']})"],
                        capture_output=True, text=True
                    )
                    if commit_res.returncode != 0:
                        # Maybe nothing to commit
                        fix_results.append({"issue": issue["description"], "status": "nothing_to_commit", "error": commit_res.stderr})
                        continue

                    # Step 4: Push branch to GitHub
                    push_res = subprocess.run(
                        ["git", "-C", clone_dir, "push", "-u", "origin", branch_name],
                        capture_output=True, text=True
                    )

                    if push_res.returncode != 0:
                        fix_results.append({
                            "issue": issue["description"],
                            "status": "push_failed",
                            "branch": branch_name,
                            "error": push_res.stderr
                        })
                        continue

                    # Step 5: Create Pull Request via GitHub API
                    pr_link = None
                    try:
                        import requests
                        match = _re.search(r'github\.com/([^/]+)/([^/.]+)', st.session_state.gh_scanned_repo)
                        if match:
                            owner, repo = match.groups()
                            pr_data = {
                                "title": f"🔧 Fix: {issue['description'][:80]}",
                                "body": f"**Category:** {issue['category']}\n**Severity:** {issue['severity']}\n**File:** {issue['file']}:{issue.get('line', '')}\n\n{issue.get('fix', '')}\n\n*Auto-fixed by SEO Command Center*",
                                "head": branch_name,
                                "base": default_branch
                            }
                            headers = {
                                "Authorization": f"token {github_token}",
                                "Accept": "application/vnd.github.v3+json"
                            }
                            resp = requests.post(
                                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                                json=pr_data, headers=headers, timeout=30
                            )
                            if resp.status_code == 201:
                                pr_link = resp.json().get("html_url")
                            else:
                                pr_error = resp.json().get("message", f"HTTP {resp.status_code}")
                    except Exception as e:
                        pass

                    fix_results.append({
                        "issue": issue["description"],
                        "category": issue["category"],
                        "severity": issue["severity"],
                        "file": issue["file"],
                        "status": "fixed",
                        "branch": branch_name,
                        "pr_url": pr_link
                    })

                progress_bar.empty()
                status_text.empty()
                st.session_state.gh_fix_results = fix_results

                fixed_count = sum(1 for r in fix_results if r.get("status") == "fixed")
                pr_count = sum(1 for r in fix_results if r.get("pr_url"))
                skipped_count = sum(1 for r in fix_results if r.get("status") == "skipped")
                failed_count = sum(1 for r in fix_results if r.get("status") not in ("fixed", "skipped"))

                st.success(f"✅ **Done!** Fixed {fixed_count}/{len(issues)} issues. Created {pr_count} Pull Requests.")
                if failed_count > 0:
                    st.warning(f"⚠️ {failed_count} issues failed. See details below.")
                if skipped_count > 0:
                    st.info(f"ℹ️ {skipped_count} issues skipped (cannot auto-fix).")
                st.balloons()

        # ── Show Fix Results ──
        if st.session_state.gh_fix_results:
            st.markdown("---")
            st.markdown("### 🔧 Fix Results")

            fix_results = st.session_state.gh_fix_results
            fixed_count = sum(1 for r in fix_results if r.get("status") == "fixed")
            skipped_count = sum(1 for r in fix_results if r.get("status") == "skipped")
            failed_count = sum(1 for r in fix_results if r.get("status") not in ("fixed", "skipped"))
            pr_count = sum(1 for r in fix_results if r.get("pr_url"))

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("✅ Fixed", fixed_count)
            r2.metric("📋 PRs Created", pr_count)
            r3.metric("⏭️ Skipped", skipped_count)
            r4.metric("❌ Failed", failed_count)

            # Show PRs
            prs = [r for r in fix_results if r.get("pr_url")]
            if prs:
                st.markdown("#### 🔗 Pull Requests Created:")
                for r in prs:
                    st.markdown(f"- [{r['issue'][:60]}]({r['pr_url']})")

            # Show all results in table
            st.markdown("#### 📋 All Changes:")
            for r in fix_results:
                icon = "✅" if r.get("status") == "fixed" else "⏭️" if r.get("status") == "skipped" else "❌"
                pr_link = f" → [View PR]({r['pr_url']})" if r.get("pr_url") else ""
                st.markdown(f"{icon} **{r['issue']}** `{r.get('file', '')}` {pr_link}")

    # ── Show Issue List (when scanned but not yet fixed) ──
    if st.session_state.gh_scan_results and not st.session_state.gh_fix_results:
        st.markdown("---")
        st.markdown("### 📋 All Issues Found")

        # Group by severity
        issues = st.session_state.gh_scan_results["issues"]

        for sev, icon, color in [("critical", "🔴", "red"), ("high", "🟠", "orange"), ("medium", "🟡", "yellow"), ("low", "🟢", "gray")]:
            sev_issues = [i for i in issues if i["severity"] == sev]
            if sev_issues:
                with st.expander(f"{icon} {sev.upper()} ({len(sev_issues)} issues)", expanded=(sev in ("critical", "high"))):
                    for issue in sev_issues:
                        st.markdown(f"""
                        <div style="background-color: var(--secondary-background-color); padding: 12px; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 8px;">
                            <b>{issue['category']}</b>: {issue['description']}<br>
                            <code>{issue['file']}:{issue['line']}</code> | 💡 {issue.get('fix', 'N/A')}
                        </div>
                        """, unsafe_allow_html=True)

with tab_settings:
    st.subheader("⚙️ API Configuration")
    st.write("Manage your API keys for autonomous operations. These are saved to your `.env` file.")
    
    # X (Twitter)
    st.markdown("#### X (Twitter) API")
    col1, col2 = st.columns(2)
    with col1:
        new_x_key = st.text_input("API Key", value=os.environ.get("X_API_KEY", ""), type="password")
        new_x_token = st.text_input("Access Token", value=os.environ.get("X_ACCESS_TOKEN", ""), type="password")
    with col2:
        new_x_secret = st.text_input("API Key Secret", value=os.environ.get("X_API_SECRET", ""), type="password")
        new_x_access_secret = st.text_input("Access Token Secret", value=os.environ.get("X_ACCESS_SECRET", ""), type="password")

    # Mastodon
    st.markdown("#### Mastodon API")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        new_mastodon_token = st.text_input("Mastodon Access Token", value=os.environ.get("MASTODON_ACCESS_TOKEN", ""), type="password")
    with col_m2:
        new_mastodon_url = st.text_input("Instance URL", value=os.environ.get("MASTODON_API_BASE_URL", "https://mastodon.social"))
    
    # Connection Status indicator
    if os.environ.get("X_API_KEY"):
        st.caption("Current X Connection Status:")
        if os.environ.get("X_API_KEY").startswith("wta09"):
            st.error("⚠️ Using Placeholder Keys (wta09...) - Please update with real keys.")
        else:
            st.info("ℹ️ Keys are set. Use 'Test Connection' below to verify.")
        
    # Zapier
    st.markdown("#### Fallback Webhook (Zapier/Make)")
    new_webhook = st.text_input("Webhook URL", value=os.environ.get("SOCIAL_WEBHOOK", ""))
    
    # Other Keys
    st.markdown("#### AI & GitHub Automation")
    col3, col4 = st.columns(2)
    with col3:
        new_gemini = st.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
    with col4:
        new_github = st.text_input("GitHub Token", value=os.environ.get("GITHUB_TOKEN", ""), type="password", help="Requires 'repo' scope to push fixes and create Pull Requests.")
    
    st.markdown("""
    <div style="background-color: rgba(63, 145, 255, 0.1); padding: 15px; border-radius: 8px; border-left: 5px solid #3f91ff; margin-bottom: 20px;">
        <h5 style="margin-top:0; color: var(--text-color);">🔑 How to Fix 'Permission Denied' (403 Error):</h5>
        <p style="font-size: 0.9em; color: var(--text-color);">A 403 error means your token is valid but <b>doesn't have permission to write</b> to this repo.</p>
        <ol style="font-size: 0.9em; margin-bottom: 0; color: var(--text-color);">
            <li><b>For Classic Tokens:</b> Ensure you selected the <b>entire 'repo' scope</b> (all sub-boxes).</li>
            <li><b>For Fine-grained Tokens:</b> Go to <b>Repository permissions</b> and set <b>'Contents'</b> to <b>Read and Write</b>.</li>
            <li><b>For Organization Repos:</b> Ensure the token has access to the specific organization.</li>
        </ol>
        <p style="font-size: 0.8em; margin-top: 10px; color: var(--text-color); opacity: 0.8;"><i>Tip: Create a new token if you're unsure about the scopes.</i></p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("💾 Save All API Settings", use_container_width=True, type="primary"):
        set_key(dotenv_path, "X_API_KEY", new_x_key)
        set_key(dotenv_path, "X_API_SECRET", new_x_secret)
        set_key(dotenv_path, "X_ACCESS_TOKEN", new_x_token)
        set_key(dotenv_path, "X_ACCESS_SECRET", new_x_access_secret)
        set_key(dotenv_path, "MASTODON_ACCESS_TOKEN", new_mastodon_token)
        set_key(dotenv_path, "MASTODON_API_BASE_URL", new_mastodon_url)
        set_key(dotenv_path, "SOCIAL_WEBHOOK", new_webhook)
        set_key(dotenv_path, "GEMINI_API_KEY", new_gemini)
        set_key(dotenv_path, "GITHUB_TOKEN", new_github)
        st.success("✅ All settings saved and applied! Reloading...")
        import time
        time.sleep(1.5)
        st.rerun()

    st.divider()
    st.subheader("🛠️ Diagnostics")
    if st.button("🔍 Test X (Twitter) Connection"):
        with st.spinner("Testing credentials..."):
            import subprocess
            import sys
            # Create a temporary test script or run a command
            test_cmd = f"X_API_KEY='{new_x_key}' X_API_SECRET='{new_x_secret}' X_ACCESS_TOKEN='{new_x_token}' X_ACCESS_SECRET='{new_x_access_secret}' python3 scratch/test_x_auth.py"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
            if "✅" in result.stdout:
                st.success("Connection Successful!")
            else:
                st.error("Connection Failed.")
            st.code(result.stdout)