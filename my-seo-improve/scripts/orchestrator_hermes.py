import os
import json
from dotenv import load_dotenv

# Load API keys and config from .env (check project root)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path)

# Environment variables for LLM platform
HERMES_MODEL = os.getenv("HERMES_MODEL", "gpt-4o-mini")
HERMES_PROVIDER = os.getenv("HERMES_PROVIDER", "openai")
HERMES_API_KEY = os.getenv("HERMES_API_KEY")
HERMES_BASE_URL = os.getenv("HERMES_BASE_URL")

# Standardize environment variables and resolve base URL
if HERMES_PROVIDER == "openai":
    os.environ["OPENAI_API_KEY"] = HERMES_API_KEY
    if not HERMES_BASE_URL:
        HERMES_BASE_URL = "https://api.openai.com/v1"
elif HERMES_PROVIDER == "gemini":
    os.environ["GOOGLE_API_KEY"] = HERMES_API_KEY
    if not HERMES_BASE_URL:
        HERMES_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
elif HERMES_PROVIDER == "openrouter":
    os.environ["OPENROUTER_API_KEY"] = HERMES_API_KEY
    if not HERMES_BASE_URL:
        HERMES_BASE_URL = "https://openrouter.ai/api/v1"

# Set HERMES_HOME to the active profile if not already set to avoid fallback warnings
if not os.environ.get("HERMES_HOME"):
    hermes_root = os.path.expanduser("~/.hermes")
    active_profile_path = os.path.join(hermes_root, "active_profile")
    if os.path.exists(active_profile_path):
        try:
            with open(active_profile_path, "r") as f:
                profile_name = f.read().strip()
                if profile_name:
                    os.environ["HERMES_HOME"] = os.path.join(hermes_root, "profiles", profile_name)
        except Exception:
            pass

from run_agent import AIAgent

def initialize_seo_cmo():
    """Initialize the master SEO CMO agent with token-saving constraints"""
    agent = AIAgent(
        model=HERMES_MODEL,
        provider=HERMES_PROVIDER,
        api_key=HERMES_API_KEY,
        base_url=HERMES_BASE_URL,
        api_mode="chat_completions",
        ephemeral_system_prompt="""You are an EFFICIENT SEO Agent.
        COST CONTROL IS CRITICAL. 
        1. Only read the files ABSOLUTELY necessary for the fix.
        2. Do NOT re-read the same file multiple times.
        3. Apply fixes IMMEDIATELY using 'apply_fix.py'.
        4. Finish the entire task in under 5 turns.
        5. Once a fix is applied, do not keep the code in your memory for the next turn.
        Focus only on high-impact SEO wins (Title, Meta, H1).""", 
        quiet_mode=True
    )
    return agent

def run_daily_workflow():
    agent = initialize_seo_cmo()
    
    # Read UI inputs from environment
    target_url = os.getenv("TARGET_URL", "https://thespecialcharacter.com/")
    repo_url = os.getenv("GITHUB_REPO", "https://github.com/tirthpatel143/The-Special-Character.git")
    
    # Read strategy files
    strategy_path = os.path.join(os.getcwd(), "data/strategy.json")
    strategy = {}
    if os.path.exists(strategy_path):
        with open(strategy_path, "r") as f:
            strategy = json.load(f)
    
    # Agent executes the full workflow with UI context
    prompt = f"""Execute the full SEO automation for:
    TARGET WEBSITE: {target_url}
    TARGET GITHUB REPO: {repo_url}
    
    STRATEGY CONTEXT: {strategy}
    
    YOUR TASK:
    1. Scan the local codebase (located in the current directory) for SEO gaps matching the strategy.
    2. IMMEDIATELY use 'apply_fix.py' to patch identified issues.
    3. Ensure changes are pushed to the '{repo_url}' repository using the GITHUB_TOKEN from the environment.
    4. You must provide a link to the Pull Request or branch created on GitHub."""
    
    response = agent.chat(prompt)
    print("\n🚀 Hermes Automation Result:", response)
    
    # 5. Automatically publish social signals
    print("\n📢 Hermes is now publishing social signals to X and Mastodon...")
    import subprocess
    import sys
    social_result = subprocess.run([sys.executable, "scripts/publish_socials.py"], capture_output=True, text=True)
    if social_result.returncode == 0:
        print("✅ Social signals published successfully!")
    else:
        print(f"⚠️ Social publishing encountered issues: {social_result.stdout}")

if __name__ == "__main__":
    run_daily_workflow()