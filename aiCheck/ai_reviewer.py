import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AIReviewer:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL")

        if not self.api_key:
            raise ValueError("❌ 未设置 DASHSCOPE_API_KEY")

        print(f"🔧 AIReviewer 初始化: base_url={self.base_url}, model={self.model}")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    async def review_code_changes(self, code_blocks: List[Dict[str, str]]) -> str:
        if not code_blocks:
            return "⚠️ 未检测到有效代码变更。"

        code_text = "\n".join(
            f"// File: {block['file']}\n{block['code']}" for block in code_blocks
        )

        system_prompt = (
            "你是一位资深代码与安全审计专家，负责对 Git 提交中的新增/修改代码进行精准评审。\n"
            "请严格遵循以下规则：\n"
            "1. **只关注高风险或中风险问题**：如安全漏洞（硬编码密钥、SQL注入、路径遍历、命令注入等）、"
            "严重性能缺陷（如循环内查库）、空指针、资源泄漏、除零错误等。\n"
            "2. **忽略低价值建议**：如命名风格、格式缩进、无害的魔法数字等。\n"
            "3. **输出必须极其简洁**：每条问题用一句话说明，不要解释原理或写开场白/总结语。\n"
            "4. **按文件分组**，使用如下格式：\n"
            "   ### 文件: path/to/file.ext\n"
            "   - ⚠️ [类型] 问题描述。\n"
            "5. 如果未发现任何实质性问题，请直接返回：「✅ 未发现高风险问题。」\n"
            "6. **禁止使用代码块、引用、列表标题以外的 Markdown**，确保 GitLab 评论可读。\n"
            "7. 全程使用中文，语气专业、冷静、无冗余。"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请评审以下新增代码：\n\n{code_text}"}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip() or "🤖 AI 返回为空。"
        except Exception as e:
            return f"❌ AI 调用失败: {type(e).__name__}: {str(e)}"