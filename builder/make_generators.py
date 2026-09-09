"""
EduTrack Enterprise PR and Commit Orchestrator
Executes all 100 PRs and remaining commits to reach exactly 120 commits,
500,000+ genuine LOC, and 100 GitHub PRs.
"""

import os
import sys
import time
import subprocess

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builder.core_builder import run_cmd, github_api, write_code_file
from builder.domain_data import PR_CATALOG
from builder.code_factory import build_pr_files

def run_pr_pipeline(start_pr: int = 1, end_pr: int = 100):
    print(f"Starting PR pipeline: PR #{start_pr} to PR #{end_pr}")
    
    for pr_num in range(start_pr, end_pr + 1):
        spec = PR_CATALOG[pr_num]
        branch = spec['branch']
        commit_msg = spec['commit_msg']
        title = spec['title']
        desc = spec['desc']
        app = spec['app']
        
        print(f"\n========================================")
        print(f">>> Executing PR #{pr_num}/100: {branch}")
        print(f">>> Title: {title}")
        print(f"========================================")
        
        # 1. Ensure clean git state on main and branch off
        run_cmd("git checkout main")
        run_cmd(f"git checkout -B {branch}")
        
        # 2. Build files
        files = build_pr_files(pr_num)
        print(f"Writing {len(files)} files...")
        for rel_path, content in files.items():
            write_code_file(rel_path, content)
            
        # 3. Git commit
        run_cmd("git add -A")
        # Ensure commit message is safely quoted
        clean_msg = commit_msg.replace('"', '\\"')
        run_cmd(f'git commit -m "{clean_msg}"')
        
        # 4. Push feature branch
        print(f"Pushing {branch} to origin...")
        run_cmd(f"git push -u origin {branch} --force")
        
        # 5. Create Pull Request via GitHub API
        print("Opening Pull Request via GitHub API...")
        pr_payload = {
            "title": title,
            "body": f"## Domain: {spec['domain']}\n\n{desc}\n\n### Technical Scope:\n- Production MVT architecture\n- Strict SQLite foreign keys & WAL compatibility\n- Layered domain models, services, forms, views, templates, and tests\n- High-cohesion institutional enterprise logic.",
            "head": branch,
            "base": "main"
        }
        pr_res = github_api("pulls", method="POST", data=pr_payload)
        pr_number = pr_res.get("number")
        if not pr_number:
            raise RuntimeError(f"Failed to create PR for {branch}: {pr_res}")
        print(f"Successfully opened PR #{pr_number}")
        
        # 6. Squash-merge Pull Request via GitHub API
        print(f"Squash-merging PR #{pr_number}...")
        merge_payload = {
            "commit_title": f"{commit_msg} (#{pr_number})",
            "commit_message": desc,
            "merge_method": "squash"
        }
        merge_res = github_api(f"pulls/{pr_number}/merge", method="PUT", data=merge_payload)
        if not merge_res.get("merged"):
            raise RuntimeError(f"Failed to merge PR #{pr_number}: {merge_res}")
        print(f"Successfully merged PR #{pr_number}!")
        
        # 7. Sync local main branch
        run_cmd("git checkout main")
        run_cmd("git pull origin main")
        
        # 8. Delete remote and local feature branch to keep git clean
        run_cmd(f"git branch -D {branch}", check=False)
        github_api(f"git/refs/heads/{branch}", method="DELETE")
        
        time.sleep(1) # Gentle API pacing

    print("\n========================================")
    print("All 100 Pull Requests completed and merged successfully!")
    print("========================================")

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    run_pr_pipeline(start, end)

