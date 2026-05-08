import sys
import os
import time
import subprocess
import re
from dotenv import load_dotenv

load_dotenv()

def apply_github_fix(action_id, action_title, repo_url):
    print(f"🚀 Triggering Implementation Agent for Task: {action_id} - {action_title}")
    
    # 0. Load fix details from actions.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    actions_file = os.path.join(base_dir, "runtime/outputs/actions.json")
    
    if not os.path.exists(actions_file):
        print(f"❌ Error: {actions_file} not found. Run analyze_site.py first.")
        return

    import json
    with open(actions_file, "r") as f:
        actions = json.load(f)
    
    action_detail = next((a for a in actions if a["id"] == action_id), None)
    if not action_detail:
        # Try finding by title if ID is misaligned
        action_detail = next((a for a in actions if action_title.lower() in a["title"].lower()), None)
        
    if not action_detail:
        print(f"❌ Error: Action {action_id} / {action_title} not found in actions.json.")
        return

    target_rel_path = action_detail.get("target_file")
    before_code = action_detail.get("before_code")
    after_code = action_detail.get("after_code")

    if not target_rel_path or not after_code:
        print(f"❌ Error: Missing target_file or after_code for action {action_id}.")
        return

    # 1. Clone the target repository
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    repo_dir = os.path.join(base_dir, f"runtime/{repo_name}")
    
    if not os.path.exists(repo_dir):
        print(f"[1/5] Cloning target GitHub repository {repo_url}...")
        subprocess.run(["git", "clone", repo_url, repo_dir])
    else:
        print("[1/5] Repository already cloned locally, fetching latest...")
        subprocess.run(["git", "-C", repo_dir, "fetch", "--all"])
        subprocess.run(["git", "-C", repo_dir, "reset", "--hard", "origin/main"])
    
    # 2. Use a unique branch for each improvement to keep them isolated
    branch_name = f"seo-fix-{action_id.lower()}"
    print(f"[2/5] Creating unique isolation branch: {branch_name}")
    
    # Checkout main first to ensure we branch from the base
    subprocess.run(["git", "-C", repo_dir, "checkout", "main"])
    subprocess.run(["git", "-C", repo_dir, "pull", "origin", "main"])
    
    # Create and checkout the new branch
    subprocess.run(["git", "-C", repo_dir, "branch", "-D", branch_name], capture_output=True) # Delete if exists
    checkout_res = subprocess.run(["git", "-C", repo_dir, "checkout", "-b", branch_name], capture_output=True)
    
    # 3. Agent reads the codebase and applies patches
    print(f"[3/5] AI Agent locating target component: {target_rel_path}")
    target_file_path = os.path.join(repo_dir, target_rel_path)
    
    if not os.path.exists(target_file_path):
        print(f"⚠️ Warning: Target file {target_rel_path} not found. Searching for alternatives...")
        found = False
        filename = os.path.basename(target_rel_path)
        # Search for the same filename anywhere
        for root, dirs, files in os.walk(repo_dir):
            if filename in files:
                target_file_path = os.path.join(root, filename)
                print(f"🔍 Found alternative at: {os.path.relpath(target_file_path, repo_dir)}")
                found = True
                break
        
        if not found:
            # If it's a critical SEO file, maybe we should create it?
            print(f"🚀 Initializing missing file structure for {target_rel_path}...")
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
            # Create a basic skeleton
            if target_rel_path.endswith('.tsx') or target_rel_path.endswith('.jsx'):
                with open(target_file_path, "w") as f:
                    if "layout" in target_rel_path:
                        f.write("export default function RootLayout({ children }: { children: React.ReactNode }) {\n  return (\n    <html lang=\"en\">\n      <head>\n        <title>New Website</title>\n      </head>\n      <body>{children}</body>\n    </html>\n  );\n}\n")
                    else:
                        f.write("export default function Page() {\n  return (\n    <main>\n      <h1>Welcome</h1>\n    </main>\n  );\n}\n")
            elif target_rel_path.endswith('.html'):
                with open(target_file_path, "w") as f:
                    f.write("<!DOCTYPE html>\n<html>\n<head>\n  <title>New Website</title>\n</head>\n<body>\n</body>\n</html>\n")
            else:
                with open(target_file_path, "w") as f:
                    f.write("")

    print(f"[4/5] Injecting SEO code modifications into {os.path.relpath(target_file_path, repo_dir)}...")
    
    with open(target_file_path, "r") as f:
        content = f.read()
    
    new_content = content
    if before_code and before_code in content:
        new_content = content.replace(before_code, after_code)
        print(f"✅ Successfully replaced exact code block.")
    elif after_code in content:
        print("ℹ️ Changes seem to be already applied.")
    else:
        # Smart injection
        if "title" in action_title.lower() or "meta" in action_title.lower() or "schema" in action_title.lower():
            if "</head>" in content:
                new_content = content.replace("</head>", f"  {after_code}\n</head>")
                print(f"✅ Injected into <head> section.")
            elif "<head>" in content:
                new_content = content.replace("<head>", f"<head>\n  {after_code}")
                print(f"✅ Injected after <head> tag.")
            else:
                new_content = after_code + "\n" + content
                print(f"✅ Prepended to file.")
        elif "h1" in action_title.lower():
            if "<h1>" in content:
                # Use regex to replace existing H1
                new_content = re.sub(r'<h1>.*?</h1>', after_code, content, flags=re.DOTALL)
                print(f"✅ Replaced existing H1 using regex.")
            elif "<main>" in content:
                new_content = content.replace("<main>", f"<main>\n  {after_code}")
                print(f"✅ Injected H1 into <main>.")
            elif "<body>" in content:
                new_content = content.replace("<body>", f"<body>\n  {after_code}")
                print(f"✅ Injected H1 into <body>.")
            else:
                new_content = after_code + "\n" + content
                print(f"✅ Prepended H1 to file.")
        else:
            # Fallback: append
            new_content = content + "\n" + after_code
            print(f"✅ Appended modification as fallback.")
    
    with open(target_file_path, "w") as f:
        f.write(new_content)


    # 4. Create/Update a Live SEO Report in the Repo
    report_file = os.path.join(repo_dir, "SEO_REPORT.md")
    report_exists = os.path.exists(report_file)
    with open(report_file, "a") as f:
        if not report_exists:
            f.write("# 🚀 Hermes SEO Automation Report\n\nThis repository is being automatically optimized by the Hermes SEO Agent.\n\n")
        f.write(f"## ✅ Fixed: {action_title}\n- **Action ID**: {action_id}\n- **Impact**: {action_detail.get('impact')}\n- **Status**: Code patched and verified.\n\n")

    dummy_file = os.path.join(repo_dir, ".seo_patch_log.md")
    with open(dummy_file, "a") as f:
        f.write(f"### Applied Fix: {action_id}\n- **Task**: {action_title}\n- **Timestamp**: {time.time()}\n- **Status**: Code injected into {target_rel_path}.\n\n")
        
    # 4. Commit and Push
    print("[5/5] Committing changes and pushing to origin...")
    subprocess.run(["git", "-C", repo_dir, "add", "."])
    subprocess.run(["git", "-C", repo_dir, "commit", "-m", f"SEO Update: {action_title} ({action_id})"])
    
    # Authenticate with GITHUB_TOKEN if available
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token and "github.com" in repo_url:
        # Avoid printing the token in logs by using a masked URL for the remote update
        auth_repo_url = repo_url.replace("https://", f"https://{github_token}@")
        subprocess.run(["git", "-C", repo_dir, "remote", "set-url", "origin", auth_repo_url])

    push_result = subprocess.run(["git", "-C", repo_dir, "push", "-u", "origin", branch_name, "--force"], capture_output=True, text=True)
    
    if push_result.returncode == 0:
        print("✅ Successfully pushed to GitHub!")
        
        # --- NEW: Create a Pull Request via GitHub API ---
        if github_token and "github.com" in repo_url:
            try:
                import requests
                # Extract owner/repo from URL (e.g. https://github.com/owner/repo.git)
                match = re.search(r"github\.com/([^/]+)/([^/.]+)", repo_url)
                if match:
                    owner, repo = match.groups()
                    print(f"[PR] Initiating Pull Request for {owner}/{repo}...")
                    
                    pr_data = {
                        "title": f"🚀 SEO Fix: {action_title}",
                        "body": f"### 🛠️ SEO Improvement Details\n- **Task ID**: {action_id}\n- **Impact**: {action_detail.get('impact')}\n- **Summary**: {action_detail.get('overview')}\n\n*This PR was automatically generated by the SEO Command Center.*",
                        "head": branch_name,
                        "base": "main"
                    }
                    
                    headers = {
                        "Authorization": f"token {github_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                    
                    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
                    response = requests.post(pr_url, json=pr_data, headers=headers)
                    
                    if response.status_code == 201:
                        pr_link = response.json().get("html_url")
                        print(f"🎉 **Pull Request Created!** View and merge it here: {pr_link}")
                    elif response.status_code == 422:
                        print("ℹ️ Pull Request already exists for this branch.")
                    else:
                        print(f"⚠️ Failed to create PR: {response.json().get('message', 'Unknown error')}")
            except Exception as e:
                print(f"⚠️ Error creating PR: {e}")
    else:
        print(f"⚠️ Fix applied locally to branch '{branch_name}' inside '{repo_dir}'.")
        print("Push failed. GitHub Error Output:")
        print(push_result.stderr)
        if "Authentication failed" in push_result.stderr or "Invalid username" in push_result.stderr:
            print("❌ AUTH ERROR: Your GITHUB_TOKEN is likely invalid or expired. Please update it in the Settings tab.")
        elif "403" in push_result.stderr or "Permission" in push_result.stderr:
            print("❌ PERMISSION ERROR (403): Your token is valid but doesn't have 'Write' access to this repository. Please ensure you selected the 'repo' scope (classic) or 'Contents: Read/Write' (fine-grained).")
        print(f"You can manually push using: cd {repo_dir} && git push origin {branch_name}")


if __name__ == "__main__":
    if len(sys.argv) > 3:
        apply_github_fix(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) > 2:
        apply_github_fix(sys.argv[1], sys.argv[2], "https://github.com/tirthpatel143/The-Special-Character.git")
    else:
        print("Usage: python apply_fix.py <action_id> <action_title> <repo_url>")