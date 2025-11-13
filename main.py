# main.py

import yaml
import logging
from fastapi import FastAPI
import uvicorn

from aiCheck.ai_reviewer import AIReviewer
from gitlab.gitlab_client import GitLabClient
from webApi.aduit_api_ctl import trigger_audit, init_dependencies  # 注意拼写 aduit

# ==============================
# 配置与初始化
# ==============================

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

logging.basicConfig(level=logging.INFO)

gitlab_client = GitLabClient(config["gitlab"]["url"], config["gitlab"]["token"])
ai_reviewer_instance = AIReviewer()

# 注入依赖到 audit 模块
init_dependencies(gitlab_client, ai_reviewer_instance)

app = FastAPI(title="GitLab AI Code Auditor API")
app.post("/audit")(trigger_audit)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=7779, reload=True)