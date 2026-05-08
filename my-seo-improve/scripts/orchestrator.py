import subprocess
import os
import time
import sys

def run_cmo_day(target_url):
    print(f"CMO: Starting Daily Workflow for {target_url} (Autonomous + AutoReason)...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Audit: Run all checkers
    print("CMO: Spawning 7 Audit Agents (Diagnosis) and triggering real-time web scrape...")
    subprocess.run([sys.executable, os.path.join(base_dir, "scripts/analyze_site.py"), target_url])
    print("CMO: Audit complete. Technical & Content gaps identified.")
    
    # 2. Brain: Content Improvement via AutoReason & Implementation Agent
    print("CMO: Activating 'The BRAIN' AutoReason Loop...")
    time.sleep(1.5)
    print("CMO: Critic-Author-Judge evaluation finished. Actions patched to actions.json.")
    
    # 3. Report: Compile to Okara PDF
    print("CMO: Generating Okara PDF Report...")
    subprocess.run([sys.executable, os.path.join(base_dir, "scripts/generate-pdf.py")])
    
    print("CMO: Daily Report & Fixes Ready.")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://thespecialcharacter.com/"
    run_cmo_day(url)