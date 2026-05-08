import os
import json
import subprocess
import sys
import yaml
from dotenv import load_dotenv

# Load API keys and Profile Config
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))

try:
    from swarms import Agent, Swarm, SequentialWorkflow
except ImportError:
    print("⚠️ Swarms library not found. Please run 'pip install swarms'")
    sys.exit(1)

# Hermes Profile Settings
HERMES_MODEL = os.getenv("HERMES_MODEL", "gpt-4o-mini")
HERMES_PROVIDER = os.getenv("HERMES_PROVIDER", "openai")
SWARM_CONFIG_PATH = os.getenv("SWARM_CONFIG_PATH", os.path.expanduser("~/.hermes/profiles/swarm/swarm.yaml"))
SWARM_ROLES_DIR = os.getenv("SWARM_ROLES_DIR", os.path.expanduser("~/.hermes/profiles/swarm/roles"))

# --- Tools ---
def run_audit(url: str):
    """Run the SEO audit script for a given URL"""
    result = subprocess.run([sys.executable, os.path.join(base_dir, "scripts/analyze_site.py"), url], capture_output=True, text=True)
    return result.stdout

def run_fix(action_id: str, title: str, repo: str):
    """Run the SEO fix script for a specific task"""
    result = subprocess.run([sys.executable, os.path.join(base_dir, "scripts/apply_fix.py"), action_id, title, repo], capture_output=True, text=True)
    return result.stdout

def run_social_publish():
    """Run the social media publishing script"""
    result = subprocess.run([sys.executable, os.path.join(base_dir, "scripts/publish_socials.py")], capture_output=True, text=True)
    return result.stdout

# Dynamic Agent Factory
def create_agent_from_config(worker_config):
    agent_id = worker_config['id']
    role = worker_config['role']
    role_file = os.path.join(SWARM_ROLES_DIR, f"{agent_id}.md")
    
    # Read persona from role file if exists
    persona = f"You are the {role} in the SEO Swarm."
    if os.path.exists(role_file):
        with open(role_file, "r") as f:
            persona = f.read()
            
    # Assign tools based on role
    tools = []
    role_lower = role.lower()
    if "auditor" in role_lower or "scraper" in role_lower or "reader" in role_lower:
        tools = [run_audit]
    elif "fix" in role_lower or "builder" in role_lower or "pr" in role_lower or "executor" in role_lower:
        tools = [run_fix]
    elif "social" in role_lower or "generator" in role_lower:
        tools = [run_social_publish]
        
    return Agent(
        agent_name=f"{role} ({agent_id})",
        system_prompt=persona,
        model_name=HERMES_MODEL,
        tools=tools,
        max_loops=1,
        autosave=True,
        dashboard=False,
        workspace_dir=base_dir
    )

def run_hermes_swarm():
    if not os.path.exists(SWARM_CONFIG_PATH):
        print(f"❌ Swarm config not found at {SWARM_CONFIG_PATH}")
        return

    with open(SWARM_CONFIG_PATH, "r") as f:
        swarm_config = yaml.safe_load(f)

    print(f"🚀 Initializing Hermes-Driven Swarm: {swarm_config.get('project')}")
    
    agents = []
    for worker in swarm_config.get('workers', []):
        agents.append(create_agent_from_config(worker))

    # Initialize Sequential Workflow with ALL 12 specialized agents
    workflow = SequentialWorkflow(
        name="Hermes-SEO-Full-Swarm",
        agents=agents,
        max_loops=1
    )

    target_url = os.getenv("TARGET_URL", "https://thespecialcharacter.com/")
    repo_url = os.getenv("GITHUB_REPO", "")

    task_description = f"""
    OBJECTIVE: Execute a complete SEO optimization cycle for {target_url} and deploy to {repo_url}.
    
    MISSION PARAMETERS:
    1.  ORCHESTRATOR: Initialize the mission and coordinate roles.
    2.  AUDIT READER: Analyze the technical SEO health report for {target_url}.
    3.  RAW SCRAPE ANALYZER: Extract deep product intelligence from raw data.
    4.  STRATEGY BUILDER: Construct a 30-day SEO growth roadmap.
    5.  KEYWORD ANALYST: Map semantic targets and intent for {target_url}.
    6.  SCHEMA REVIEWER: Plan structural JSON-LD optimizations.
    7.  INTERNAL LINKING OPTIMIZER: Define authority flow and silo structure.
    8.  FIX PATCH PLANNER: Detail the code-level modifications required.
    9.  GITHUB PR EXECUTOR: Commit and push technical fixes to {repo_url}.
    10. QA CHECKER: Verify code integrity and deployment success.
    11. SOCIAL POST GENERATOR: Draft and publish 'Build in Public' updates.
    12. FINAL APPROVAL GATE: Conduct the final review and archive the mission report.
    """
    
    print("🤖 The 12-agent specialized swarm is engaging...")
    workflow.run(task_description)
    print("✅ SEO Swarm Mission Complete!")

if __name__ == "__main__":
    run_hermes_swarm()
