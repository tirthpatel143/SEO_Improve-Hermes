#!/usr/bin/env python3
"""
GitHub Repo Scanner & Auto-Fixer
Scans any GitHub repo for issues, shows them, and fixes all with one click.
"""

import sys
import os
import json
import re
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# ── Issue Definition ───────────────────────────────────────────────────────────

class Issue:
    def __init__(self, category, severity, file_path, line_num, description, fix_desc="", fix_code=None):
        self.category = category
        self.severity = severity
        self.file_path = file_path
        self.line_num = line_num
        self.description = description
        self.fix_desc = fix_desc
        self.fix_code = fix_code  # callable that takes content, returns new content
        self.fixed = False
        self.fix_branch = ""

    def to_dict(self):
        return {
            "category": self.category,
            "severity": self.severity,
            "file": self.file_path,
            "line": self.line_num,
            "description": self.description,
            "fix": self.fix_desc,
            "fixed": self.fixed,
            "branch": self.fix_branch
        }

# ── Scanners ───────────────────────────────────────────────────────────────────

def scan_python_file(repo_dir, fpath):
    issues = []
    try:
        content = fpath.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
    except:
        return issues

    rel = str(fpath.relative_to(repo_dir))
    # Skip test files and vendor dirs
    if any(skip in rel for skip in ['test_', '_test.py', 'tests/', 'vendor/', 'node_modules/', '.venv/', 'venv/']):
        return issues

    for i, line in enumerate(lines, 1):
        s = line.strip()
        if re.match(r'^except\s*:', s):
            issues.append(Issue("Code Quality", "high", rel, i,
                "Bare 'except:' catches all exceptions", "Replace with 'except Exception:'"))
        if re.search(r'(password|secret|api_key|token)\s*=\s*[\'"][^\'"]+[\'"]', s, re.IGNORECASE):
            if 'os.environ' not in s and 'getenv' not in s and 'config' not in s and '#' not in s[:5]:
                issues.append(Issue("Security", "critical", rel, i,
                    f"Hardcoded secret: {s[:60]}", "Use os.environ.get()"))
        if re.match(r'^\s*print\s*\(', s) and not s.startswith('#'):
            issues.append(Issue("Code Quality", "low", rel, i,
                "print() statement (use logging)", "Replace with logger.info()"))
        if re.match(r'^\s*from\s+\S+\s+import\s+\*', s):
            issues.append(Issue("Code Quality", "medium", rel, i,
                "Wildcard import 'from X import *'", "Use explicit imports"))
    return issues

def scan_js_file(repo_dir, fpath):
    issues = []
    try:
        content = fpath.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
    except:
        return issues

    rel = str(fpath.relative_to(repo_dir))
    if any(skip in rel for skip in ['node_modules/', 'vendor/', 'dist/', 'build/']):
        return issues

    for i, line in enumerate(lines, 1):
        s = line.strip()
        if re.match(r'^\s*var\s+', s):
            issues.append(Issue("Code Quality", "low", rel, i,
                "Using 'var' (use let/const)", "Replace 'var' with 'const'"))
        if 'console.log' in s and not s.startswith('//'):
            issues.append(Issue("Code Quality", "low", rel, i,
                "console.log statement", "Remove or use logger"))
        if re.search(r'(password|secret|api_key|token)\s*[:=]\s*[\'"][^\'"]+[\'"]', s, re.IGNORECASE):
            if 'process.env' not in s and 'import.meta' not in s:
                issues.append(Issue("Security", "critical", rel, i,
                    f"Hardcoded secret: {s[:60]}", "Use process.env"))
        if re.search(r'\beval\s*\(', s):
            issues.append(Issue("Security", "critical", rel, i,
                "Dangerous eval() usage", "Use safer alternative"))
    return issues

def scan_html_file(repo_dir, fpath):
    issues = []
    try:
        content = fpath.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
    except:
        return issues

    rel = str(fpath.relative_to(repo_dir))

    if '<title>' not in content:
        issues.append(Issue("SEO", "high", rel, 1,
            "Missing <title> tag", "Add <title> in <head>"))
    if 'name="description"' not in content and "name='description'" not in content:
        issues.append(Issue("SEO", "high", rel, 1,
            "Missing meta description", 'Add <meta name="description">'))
    if 'name="viewport"' not in content:
        issues.append(Issue("SEO", "high", rel, 1,
            "Missing viewport meta (not mobile-friendly)", 'Add viewport meta tag'))
    if 'rel="canonical"' not in content:
        issues.append(Issue("SEO", "medium", rel, 1,
            "Missing canonical URL", 'Add <link rel="canonical">'))
    if 'property="og:' not in content:
        issues.append(Issue("SEO", "medium", rel, 1,
            "Missing Open Graph tags", "Add og:title, og:description, og:image"))
    if not re.search(r'<html[^>]*lang=', content):
        issues.append(Issue("SEO", "medium", rel, 1,
            "Missing lang on <html>", 'Add lang="en"'))
    if not re.search(r'<h1[^>]*>', content, re.IGNORECASE):
        issues.append(Issue("SEO", "high", rel, 1,
            "Missing <h1> heading", "Add descriptive <h1>"))

    # Images without alt
    for j, l in enumerate(lines, 1):
        for img in re.findall(r'<img[^>]*>', l, re.IGNORECASE):
            if 'alt=' not in img.lower():
                issues.append(Issue("SEO/Accessibility", "medium", rel, j,
                    f"Image missing alt: {img[:60]}", 'Add alt="" to <img>'))
    return issues

def scan_config_files(repo_dir):
    issues = []

    if not (repo_dir / ".gitignore").exists():
        issues.append(Issue("Config", "medium", ".gitignore", 1,
            "Missing .gitignore file", "Create .gitignore"))
    else:
        gi = (repo_dir / ".gitignore").read_text(encoding='utf-8', errors='ignore')
        for pat in ['node_modules', '.env', '__pycache__', '*.pyc', '.DS_Store', 'dist', 'build']:
            if pat not in gi:
                issues.append(Issue("Config", "low", ".gitignore", 1,
                    f"Missing pattern: {pat}", f"Add '{pat}'"))

    if not (repo_dir / "README.md").exists():
        issues.append(Issue("Documentation", "medium", "README.md", 1,
            "Missing README.md", "Create README.md"))

    # Check for committed secrets
    for secret_file in ['.env', 'credentials.json', 'service-account.json', 'secrets.json']:
        if (repo_dir / secret_file).exists():
            issues.append(Issue("Security", "critical", secret_file, 1,
                f"Secret file '{secret_file}' committed to repo!",
                f"Remove from git, add to .gitignore, use env vars"))

    return issues

def scan_docker_file(repo_dir):
    issues = []
    df = repo_dir / "Dockerfile"
    if df.exists():
        content = df.read_text(encoding='utf-8', errors='ignore')
        if not re.search(r'^\s*RUN\s+useradd|^\s*USER\s+', content, re.MULTILINE | re.IGNORECASE):
            issues.append(Issue("Security", "high", "Dockerfile", 1,
                "Dockerfile runs as root", "Add 'USER nonroot' instruction"))
        for i, line in enumerate(content.split('\n'), 1):
            if re.search(r'FROM\s+\S+:latest', line, re.IGNORECASE):
                issues.append(Issue("Security", "medium", "Dockerfile", i,
                    "Using ':latest' tag", "Pin to specific version"))
    return issues

# ── Main Scanner ───────────────────────────────────────────────────────────────

def scan_repo(repo_dir):
    """Scan entire repo and return all issues."""
    all_issues = []
    repo_dir = Path(repo_dir)

    skip_dirs = {'.git', 'node_modules', '__pycache__', '.next', 'venv', '.venv', 'vendor', 'dist', '.cache'}

    for fpath in repo_dir.rglob('*'):
        if not fpath.is_file():
            continue
        if any(sd in fpath.parts for sd in skip_dirs):
            continue

        ext = fpath.suffix.lower()
        if ext == '.py':
            all_issues.extend(scan_python_file(repo_dir, fpath))
        elif ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'):
            all_issues.extend(scan_js_file(repo_dir, fpath))
        elif ext == '.html':
            all_issues.extend(scan_html_file(repo_dir, fpath))

    all_issues.extend(scan_config_files(repo_dir))
    all_issues.extend(scan_docker_file(repo_dir))

    return all_issues

# ── Auto-Fixer ─────────────────────────────────────────────────────────────────

def fix_issues_on_github(repo_dir, repo_url, github_token, issues):
    """Fix all issues and push to GitHub. Returns list of fixed issues with PR links."""
    results = []
    repo_dir = Path(repo_dir)

    if not github_token:
        return [{"error": "No GITHUB_TOKEN set. Add it in Settings tab."}]

    # Parse owner/repo
    match = re.search(r'github\.com/([^/]+)/([^/.]+)', repo_url)
    if not match:
        return [{"error": f"Could not parse GitHub URL: {repo_url}"}]
    owner, repo_name = match.groups()

    # Set up auth remote
    auth_url = repo_url.replace("https://", f"https://x-access-token:{github_token}@")
    if auth_url.startswith("http://"):
        auth_url = auth_url.replace("http://", f"http://x-access-token:{github_token}@")

    subprocess.run(["git", "-C", str(repo_dir), "remote", "set-url", "origin", auth_url],
                   capture_output=True)

    # Ensure we're on main/master
    subprocess.run(["git", "-C", str(repo_dir), "fetch", "--all"], capture_output=True)
    for branch in ["main", "master"]:
        res = subprocess.run(["git", "-C", str(repo_dir), "checkout", branch],
                             capture_output=True, text=True)
        if res.returncode == 0:
            subprocess.run(["git", "-C", str(repo_dir), "pull", "origin", branch],
                           capture_output=True)
            break

    # Fix each issue in its own branch
    for idx, issue in enumerate(issues):
        branch_name = f"auto-fix/{issue.category.lower().replace(' ', '-')}-{idx+1}"

        # Create fresh branch from main
        subprocess.run(["git", "-C", str(repo_dir), "checkout", "-"], capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "branch", "-D", branch_name],
                       capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "checkout", "-b", branch_name],
                       capture_output=True)

        # Apply fix
        target_file = repo_dir / issue.file_path
        fixed = False

        if target_file.exists():
            try:
                content = target_file.read_text(encoding='utf-8', errors='ignore')
                new_content = content

                # Apply specific fixes based on issue type
                if "Bare 'except:'" in issue.description:
                    new_content = content.replace("except:", "except Exception:")
                    fixed = True
                elif "print() statement" in issue.description:
                    lines = content.split('\n')
                    if issue.line_num <= len(lines):
                        lines[issue.line_num - 1] = lines[issue.line_num - 1].replace("print(", "# print(", 1)
                        new_content = '\n'.join(lines)
                        fixed = True
                elif "console.log" in issue.description:
                    lines = content.split('\n')
                    if issue.line_num <= len(lines):
                        lines[issue.line_num - 1] = lines[issue.line_num - 1].replace("console.log", "// console.log", 1)
                        new_content = '\n'.join(lines)
                        fixed = True
                elif "Wildcard import" in issue.description:
                    pass  # Can't auto-fix without knowing imports
                elif "Using 'var'" in issue.description:
                    lines = content.split('\n')
                    if issue.line_num <= len(lines):
                        lines[issue.line_num - 1] = lines[issue.line_num - 1].replace("var ", "const ", 1)
                        new_content = '\n'.join(lines)
                        fixed = True
                elif issue.category == "SEO":
                    if "Missing <title>" in issue.description:
                        new_content = content.replace("</head>", "  <title>Project Title</title>\n</head>")
                        fixed = True
                    elif "Missing meta description" in issue.description:
                        new_content = content.replace("</head>", '  <meta name="description" content="Project description">\n</head>')
                        fixed = True
                    elif "Missing viewport" in issue.description:
                        new_content = content.replace("</head>", '  <meta name="viewport" content="width=device-width, initial-scale=1">\n</head>')
                        fixed = True
                    elif "Missing <h1>" in issue.description:
                        new_content = content.replace("<body>", "<body>\n  <h1>Main Heading</h1>")
                        fixed = True
                    elif "Missing canonical" in issue.description:
                        new_content = content.replace("</head>", '  <link rel="canonical" href="https://example.com">\n</head>')
                        fixed = True
                    elif "Missing Open Graph" in issue.description:
                        og_tags = '  <meta property="og:title" content="Title">\n  <meta property="og:description" content="Description">\n  <meta property="og:image" content="https://example.com/image.png">\n'
                        new_content = content.replace("</head>", og_tags + "</head>")
                        fixed = True
                    elif "Missing lang" in issue.description:
                        new_content = content.replace("<html>", '<html lang="en">')
                        fixed = True
                    elif "Image missing alt" in issue.description:
                        lines = content.split('\n')
                        if issue.line_num <= len(lines):
                            lines[issue.line_num - 1] = re.sub(r'<img([^>]*)>', r'<img\1 alt="">', lines[issue.line_num - 1], flags=re.IGNORECASE)
                            new_content = '\n'.join(lines)
                            fixed = True
                elif issue.category == "Config" and "Missing .gitignore" in issue.description:
                    gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
venv/
env/
.venv/

# Environment
.env
.env.local

# Build
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""
                    (repo_dir / ".gitignore").write_text(gitignore_content, encoding='utf-8')
                    fixed = True
                elif issue.category == "Documentation" and "Missing README.md" in issue.description:
                    readme = f"""# {repo_name}

## Description
Add your project description here.

## Installation
```bash
git clone {repo_url}
cd {repo_name}
```

## Usage
Add usage instructions.

## License
MIT
"""
                    (repo_dir / "README.md").write_text(readme, encoding='utf-8')
                    fixed = True
                elif issue.category == "Security" and "Secret file" in issue.description:
                    # Add to .gitignore and remove from tracking
                    secret_file = issue.file_path
                    gitignore_path = repo_dir / ".gitignore"
                    if gitignore_path.exists():
                        gi_content = gitignore_path.read_text()
                        if secret_file not in gi_content:
                            with open(gitignore_path, "a") as f:
                                f.write(f"\n{secret_file}\n")
                    subprocess.run(["git", "-C", str(repo_dir), "rm", "--cached", secret_file],
                                   capture_output=True)
                    fixed = True

                if fixed and new_content != content:
                    target_file.write_text(new_content, encoding='utf-8')

            except Exception as e:
                results.append({"issue": issue.description, "error": str(e)})
                continue
        elif issue.category in ("Config", "Documentation"):
            # These create new files
            try:
                if "Missing .gitignore" in issue.description:
                    (repo_dir / ".gitignore").write_text("node_modules/\n.env\n__pycache__/\n.DS_Store\n", encoding='utf-8')
                    fixed = True
                elif "Missing README.md" in issue.description:
                    (repo_dir / "README.md").write_text(f"# {repo_name}\n\nProject description.\n", encoding='utf-8')
                    fixed = True
            except Exception as e:
                results.append({"issue": issue.description, "error": str(e)})
                continue

        if not fixed:
            results.append({"issue": issue.description, "status": "skipped", "reason": "Cannot auto-fix"})
            # Go back to main for next branch
            subprocess.run(["git", "-C", str(repo_dir), "checkout", "-"], capture_output=True)
            continue

        # Commit and push
        subprocess.run(["git", "-C", str(repo_dir), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "commit", "-m",
                       f"Auto-fix: {issue.description[:60]} ({issue.category})"], capture_output=True)

        push_res = subprocess.run(
            ["git", "-C", str(repo_dir), "push", "-u", "origin", branch_name],
            capture_output=True, text=True
        )

        pr_link = None
        if push_res.returncode == 0:
            # Create PR via API
            try:
                import requests
                pr_data = {
                    "title": f"🔧 Fix: {issue.description[:80]}",
                    "body": f"**Category:** {issue.category}\n**Severity:** {issue.severity}\n**File:** {issue.file_path}:{issue.line_num}\n\n{issue.fix_desc}\n\n*Auto-fixed by SEO Command Center*",
                    "head": branch_name,
                    "base": "main"
                }
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                resp = requests.post(
                    f"https://api.github.com/repos/{owner}/{repo_name}/pulls",
                    json=pr_data, headers=headers
                )
                if resp.status_code == 201:
                    pr_link = resp.json().get("html_url")
                elif resp.status_code == 422:
                    # Try with master base
                    pr_data["base"] = "master"
                    resp = requests.post(
                        f"https://api.github.com/repos/{owner}/{repo_name}/pulls",
                        json=pr_data, headers=headers
                    )
                    if resp.status_code == 201:
                        pr_link = resp.json().get("html_url")
            except Exception:
                pass

        issue.fixed = True
        issue.fix_branch = branch_name
        results.append({
            "issue": issue.description,
            "category": issue.category,
            "severity": issue.severity,
            "file": issue.file_path,
            "status": "fixed",
            "branch": branch_name,
            "pr_url": pr_link
        })

        # Go back to main for next branch
        subprocess.run(["git", "-C", str(repo_dir), "checkout", "-"], capture_output=True)

    return results

# ── CLI Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python github_scanner.py <scan|fix> <repo_dir> [repo_url] [github_token]")
        sys.exit(1)

    action = sys.argv[1]
    repo_dir = sys.argv[2]
    repo_url = sys.argv[3] if len(sys.argv) > 3 else ""
    token = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("GITHUB_TOKEN", "")

    print(f"Scanning {repo_dir}...")
    issues = scan_repo(repo_dir)

    print(f"\nFound {len(issues)} issues:")
    for sev in ["critical", "high", "medium", "low"]:
        count = sum(1 for i in issues if i.severity == sev)
        print(f"  {sev.upper()}: {count}")

    # Save results
    output = {
        "total": len(issues),
        "by_severity": {
            "critical": sum(1 for i in issues if i.severity == "critical"),
            "high": sum(1 for i in issues if i.severity == "high"),
            "medium": sum(1 for i in issues if i.severity == "medium"),
            "low": sum(1 for i in issues if i.severity == "low"),
        },
        "issues": [i.to_dict() for i in issues]
    }

    report_path = Path(repo_dir) / "scan_report.json"
    report_path.write_text(json.dumps(output, indent=2))
    print(f"\nReport saved to: {report_path}")

    if action == "fix" and repo_url and token:
        print("\nFixing all issues on GitHub...")
        results = fix_issues_on_github(repo_dir, repo_url, token, issues)
        results_path = Path(repo_dir) / "fix_results.json"
        results_path.write_text(json.dumps(results, indent=2))
        print(f"Fix results saved to: {results_path}")
        for r in results:
            status = r.get("status", r.get("error", "unknown"))
            pr = r.get("pr_url", "")
            print(f"  [{status}] {r.get('issue', '')} {pr}")
