import requests
from typing import List, Dict, Any

class GitLabClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"PRIVATE-TOKEN": token}

    def find_open_mr(self, project_id: int, source_branch: str, target_branch: str) -> Dict[str, Any] | None:
        """查找匹配的 open MR"""
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests"
        params = {
            "state": "opened",
            "source_branch": source_branch,
            "target_branch": target_branch
        }
        resp = requests.get(url, headers=self.headers, params=params)
        print(f"Find open MR: {resp}")
        resp.raise_for_status()
        mrs = resp.json()
        return mrs[0] if mrs else None

    def get_mr_changes(self, project_id: int, mr_iid: int) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def post_comment(self, project_id: int, mr_iid: int, body: str) -> None:
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
        data = {"body": body}
        resp = requests.post(url, headers=self.headers, json=data)
        resp.raise_for_status()

    def has_existing_comment(self, project_id: int, mr_iid: int, keyword: str = "[Code Auditor]") -> bool:
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            return False
        notes = resp.json()
        return any(keyword in note.get("body", "") for note in notes)