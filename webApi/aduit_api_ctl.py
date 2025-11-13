# webApi/audit_api_ctl.py

import logging
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel

from aiCheck.ai_reviewer import AIReviewer
from gitlab.gitlab_client import GitLabClient
from codeHandle.analyzer import extract_added_code_blocks

# 全局依赖（初始为 None）
_gl: Optional[GitLabClient] = None
_ai_reviewer: Optional[AIReviewer] = None
logger = logging.getLogger(__name__)


def init_dependencies(gitlab_client: GitLabClient, ai_reviewer: AIReviewer):
    """在 main.py 中调用此函数完成依赖注入"""
    global _gl, _ai_reviewer
    _gl = gitlab_client
    _ai_reviewer = ai_reviewer


class AuditRequest(BaseModel):
    project_id: int
    source_branch: str
    target_branch: str

'''
被动执行
'''
async def trigger_audit(req: AuditRequest):
    if _gl is None or _ai_reviewer is None:
        raise RuntimeError("Dependencies not initialized! Call init_dependencies first.")

    try:
        logger.info(f"🔍 开始审计项目 {req.project_id}：{req.source_branch} → {req.target_branch}")

        mr = _gl.find_open_mr(req.project_id, req.source_branch, req.target_branch)
        if not mr:
            raise HTTPException(
                status_code=404,
                detail=f"未找到从 '{req.source_branch}' 合并到 '{req.target_branch}' 的 open MR"
            )

        iid = mr["iid"]
        title = mr["title"]
        logger.info(f"✅ 找到 MR !{iid}: {title}")

        if _gl.has_existing_comment(req.project_id, iid):
            logger.info(f"⏭️  MR !{iid} 已被审计过，跳过。")
            return {
                "status": "skipped",
                "message": f"MR !{iid} 已经被审计过，跳过。",
                "mr_iid": iid
            }

        mr_data = _gl.get_mr_changes(req.project_id, iid)
        changes = mr_data.get("changes", [])
        added_blocks = extract_added_code_blocks(changes)

        if not added_blocks:
            comment = "🤖 **[AI Code Auditor]** 未检测到有效代码变更（仅修改非代码文件或删除代码）。"
            _gl.post_comment(req.project_id, iid, comment)
            return {
                "status": "success",
                "result": "no_code_changes",
                "mr_iid": iid,
                "commented": True
            }

        logger.info(f"🧠 正在调用 AI 评审 MR !{iid}（共 {len(added_blocks)} 个文件）...")
        ai_feedback = await _ai_reviewer.review_code_changes(added_blocks)

        comment = f"## 🤖 AI 代码智能评审\n\n{ai_feedback}"
        _gl.post_comment(req.project_id, iid, comment)
        logger.info(f"✅ 已评论到 MR !{iid}")

        return {
            "status": "success",
            "result": "reviewed",
            "mr_iid": iid,
            "title": title,
            "files_reviewed": len(added_blocks),
            "commented": True
        }

    except Exception as e:
        logger.exception("❌ 审计过程中发生错误")
        raise HTTPException(status_code=500, detail=f"审计失败: {str(e)}")