import re
from typing import List, Dict, Any
import re
from typing import List, Dict, Any, Tuple

DANGEROUS_PATTERNS = [
    # Python / JS / PHP
    (r"\beval\s*\(", "避免使用 eval()，存在代码注入风险"),
    (r"\bexec\s*\(", "避免使用 exec()，存在代码注入风险"),
    (r"password\s*=\s*[\"'][^\"']+[\"']", "硬编码密码，请使用环境变量"),
    (r"pickle\.loads", "避免使用 pickle.loads，存在反序列化漏洞"),

    # Java 特有
    (r"\bint\s+\w+\s*=\s*0\s*;", "硬编码整数 0，可能导致除零风险？"),
    (r"\b\w+\s*/\s*\b0\b", "检测到除以字面量 0，会导致 ArithmeticException！"),
    (r"System\.out\.println", "避免在生产代码中使用 System.out.println"),
    (r"printStackTrace\(\)", "禁止使用 printStackTrace，请使用日志框架"),
    (r"@RequestMapping\([^)]*\bmethod\s*=\s*RequestMethod\.GET\b[^)]*\)\s+public.*\bdelete\b", "GET 方法不应执行删除操作"),
]

def analyze_diff(changes: List[Dict[str, Any]]) -> List[str]:
    issues = []
    for change in changes:
        new_path = change.get("new_path")
        if not new_path or not any(new_path.endswith(ext) for ext in [".java", ".py", ".js", ".ts", ".php"]):
            continue

        diff = change.get("diff", "")
        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                code = line[1:].strip()
                for pattern, msg in DANGEROUS_PATTERNS:
                    if re.search(pattern, code, re.IGNORECASE):
                        issues.append(f"- 文件 `{new_path}`：{msg}\n  > `{code}`")
    return issues





def extract_added_code_blocks(changes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    从 GitLab diff 中提取所有新增的代码块（按文件分组）
    返回: [{"file": "xxx.java", "code": "int a=1;\nint b=0;..."}, ...]
    """
    added_blocks = []

    for change in changes:
        new_path = change.get("new_path")
        if not new_path or not any(new_path.endswith(ext) for ext in [".java", ".py", ".js", ".ts", ".php"]):
            continue

        diff = change.get("diff", "")
        lines = diff.splitlines()
        current_block = []
        in_hunk = False

        for line in lines:
            if line.startswith("@@"):
                # 新的代码块开始，保存上一个块（如果有）
                if current_block:
                    added_blocks.append({"file": new_path, "code": "\n".join(current_block)})
                    current_block = []
                in_hunk = True
            elif in_hunk:
                if line.startswith("+") and not line.startswith("+++"):
                    current_block.append(line[1:])  # 去掉 '+' 号
                elif line.startswith("-"):
                    continue  # 忽略删除行
                else:
                    # 上下文行（未变），可选是否保留（这里不保留，只取新增）
                    pass

        # 保存最后一个块
        if current_block:
            added_blocks.append({"file": new_path, "code": "\n".join(current_block)})

    return added_blocks