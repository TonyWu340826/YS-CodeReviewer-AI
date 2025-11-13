# streamlit_app.py

import streamlit as st
import yaml
import sys
import os
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到 Python 路径（确保能导入自定义模块）
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from webApi.aduit_api_ctl import trigger_audit, init_dependencies, AuditRequest
from aiCheck.ai_reviewer import AIReviewer
from gitlab.gitlab_client import GitLabClient

# ==============================
# 自定义样式
# ==============================
st.markdown("""
<style>
    /* 全局字体和背景 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* 主标题样式 */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* 卡片容器 */
    .main-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }

    /* 输入框样式优化 */
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        transition: all 0.3s ease;
    }

    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* 按钮样式 */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
        border: none;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
    }

    /* 表单标签样式 */
    .stNumberInput label, .stTextInput label, .stTextArea label {
        font-weight: 600;
        color: #374151;
        font-size: 0.95rem;
    }

    /* 成功/警告/错误消息样式 */
    .stSuccess, .stWarning, .stError, .stInfo {
        border-radius: 10px;
        padding: 1rem;
    }

    /* 对话框样式 */
    [data-testid="stDialog"] {
        border-radius: 16px !important;
    }

    /* 信息框样式 */
    .info-box {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    /* 响应卡片 */
    .result-card {
        background: #f9fafb;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        border: 1px solid #e5e7eb;
    }

    .result-card strong {
        color: #667eea;
    }

    /* caption样式 */
    .css-1544g2n {
        color: #6b7280;
        font-size: 0.95rem;
    }

    /* Tab样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }

    /* 批量任务表格样式 */
    .batch-task-item {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        transition: all 0.3s ease;
    }

    .batch-task-item:hover {
        border-color: #667eea;
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.1);
    }

    .task-status-pending {
        color: #9ca3af;
    }

    .task-status-running {
        color: #3b82f6;
    }

    .task-status-success {
        color: #10b981;
    }

    .task-status-failed {
        color: #ef4444;
    }

    /* 功能卡片样式 */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
        border-color: #667eea;
    }

    .feature-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 1rem;
    }

    .gradient-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .gradient-blue { background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%); }
    .gradient-orange { background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); }
    .gradient-green { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .gradient-indigo { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
    .gradient-pink { background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%); }

    /* 工作流步骤 */
    .workflow-step {
        background: linear-gradient(135deg, #f9fafb 0%, #f3e8ff 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        position: relative;
    }

    .workflow-number {
        display: inline-flex;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 1rem;
        font-size: 18px;
    }

    /* 架构图样式 */
    .arch-node {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem;
        text-align: center;
        min-width: 120px;
    }

    .arch-layer {
        text-align: center;
        margin: 2rem 0;
        position: relative;
    }

    .arch-arrow {
        text-align: center;
        color: #667eea;
        font-size: 24px;
        margin: 0.5rem 0;
    }

    /* 标签徽章 */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }

    .badge-purple { background: #ede9fe; color: #6d28d9; }
    .badge-pink { background: #fce7f3; color: #be185d; }
    .badge-blue { background: #dbeafe; color: #1e40af; }
</style>
""", unsafe_allow_html=True)


# ==============================
# 初始化依赖（仅执行一次）
# ==============================
@st.cache_resource
def initialize_services():
    config_path = project_root / "config" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    gitlab_client = GitLabClient(config["gitlab"]["url"], config["gitlab"]["token"])
    ai_reviewer = AIReviewer()
    init_dependencies(gitlab_client, ai_reviewer)
    return True


# 触发初始化
initialize_services()


# ==============================
# 批量审计函数
# ==============================
async def batch_audit_tasks(tasks):
    """执行批量审计任务"""
    results = []
    for i, task in enumerate(tasks):
        try:
            req = AuditRequest(
                project_id=task['project_id'],
                source_branch=task['source_branch'],
                target_branch=task['target_branch']
            )
            result = await trigger_audit(req)
            results.append({
                'index': i + 1,
                'task': task,
                'status': 'success',
                'result': result
            })
        except Exception as e:
            results.append({
                'index': i + 1,
                'task': task,
                'status': 'failed',
                'error': str(e)
            })
    return results


# ==============================
# 确认对话框（单个审计）
# ==============================
@st.dialog("⚠️ 确认执行 AI 审计")
def confirm_audit_dialog(project_id, source_branch, target_branch):
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); 
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;'>
        <p style='margin: 0; color: #374151; font-size: 1rem;'>
            ⚡ 请确认以下审计信息后继续：
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 信息展示
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**📦 项目 ID**")
        st.markdown("**🌿 源分支**")
        st.markdown("**🎯 目标分支**")
    with col2:
        st.markdown(f"`{project_id}`")
        st.markdown(f"`{source_branch}`")
        st.markdown(f"`{target_branch}`")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 确认执行", type="primary", use_container_width=True):
            st.session_state.confirmed = True
            st.session_state.execute_audit = True
            st.rerun()
    with col2:
        if st.button("❌ 取消", use_container_width=True):
            st.session_state.confirmed = False
            st.rerun()


# ==============================
# 确认对话框（批量审计）
# ==============================
@st.dialog("⚠️ 确认批量执行 AI 审计")
def confirm_batch_audit_dialog(tasks):
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); 
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;'>
        <p style='margin: 0; color: #374151; font-size: 1rem;'>
            ⚡ 即将批量审计 <strong>{}</strong> 个任务，请确认：
        </p>
    </div>
    """.format(len(tasks)), unsafe_allow_html=True)

    # 任务列表展示
    for i, task in enumerate(tasks, 1):
        with st.container():
            st.markdown(f"""
            <div class='batch-task-item'>
                <strong>任务 {i}</strong><br>
                📦 项目ID: <code>{task['project_id']}</code> | 
                🌿 源分支: <code>{task['source_branch']}</code> | 
                🎯 目标分支: <code>{task['target_branch']}</code>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 确认批量执行", type="primary", use_container_width=True):
            st.session_state.execute_batch_audit = True
            st.rerun()
    with col2:
        if st.button("❌ 取消", use_container_width=True):
            st.session_state.execute_batch_audit = False
            st.rerun()


# ==============================
# Streamlit UI
# ==============================
st.set_page_config(
    page_title="YS-AICoding - 新一代代码AI自动检查平台",
    page_icon="🤖",
    layout="centered"
)

# 头部
st.markdown("<br>", unsafe_allow_html=True)
st.title("🤖 YS-AICoding")
st.markdown("### 新一代代码AI自动检查平台")
st.caption("🚀 直接调用内部审计引擎，无需 HTTP 中转 | 智能 · 高效 · 安全")

# 徽章展示
st.markdown("""
<div style='margin: 1rem 0;'>
    <span class='badge badge-purple'>智能审计</span>
    <span class='badge badge-pink'>自动化</span>
    <span class='badge badge-blue'>企业级</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 初始化 session state
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False
if 'execute_audit' not in st.session_state:
    st.session_state.execute_audit = False
if 'execute_batch_audit' not in st.session_state:
    st.session_state.execute_batch_audit = False
if 'batch_tasks' not in st.session_state:
    st.session_state.batch_tasks = []

# Tab切换：单个审计 vs 批量审计 vs 功能说明
tab1, tab2, tab3 = st.tabs(["🔍 单个审计", "📋 批量审计", "📚 功能说明"])

# ==============================
# Tab 1: 单个审计
# ==============================
with tab1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    with st.form("audit_form"):
        st.markdown("#### 📝 审计配置")
        st.markdown("<br>", unsafe_allow_html=True)

        project_id = st.number_input(
            "📦 项目 ID (Project ID)",
            min_value=1,
            value=86,
            step=1,
            help="请输入 GitLab 项目的 ID"
        )

        source_branch = st.text_input(
            "🌿 源分支 (Source Branch)",
            value="dev_ai_check01",
            help="需要审计的源分支名称"
        )

        target_branch = st.text_input(
            "🎯 目标分支 (Target Branch)",
            value="dev",
            help="目标合并分支名称"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 开始 AI 审计", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 点击提交按钮时显示确认对话框
    if submitted:
        st.session_state.project_id = int(project_id)
        st.session_state.source_branch = source_branch.strip()
        st.session_state.target_branch = target_branch.strip()
        st.session_state.execute_audit = False
        confirm_audit_dialog(
            st.session_state.project_id,
            st.session_state.source_branch,
            st.session_state.target_branch
        )

    # 确认后执行审计
    if st.session_state.get('execute_audit', False):
        st.session_state.execute_audit = False

        with st.spinner("🔍 正在审计代码，请稍候..."):
            try:
                req = AuditRequest(
                    project_id=st.session_state.project_id,
                    source_branch=st.session_state.source_branch,
                    target_branch=st.session_state.target_branch
                )

                result = asyncio.run(trigger_audit(req))

                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.success("✅ 审计完成！")

                status = result.get("status")
                if status == "skipped":
                    st.info(result["message"])
                elif result.get("result") == "no_code_changes":
                    st.warning("⚠️ 未检测到有效代码变更（仅修改非代码文件或删除代码）")
                else:
                    st.markdown(f"**📋 MR 标题**: {result.get('title', 'N/A')}")
                    st.markdown(f"**🔗 MR IID**: !{result.get('mr_iid', 'N/A')}")
                    st.markdown(f"**📊 评审文件数**: {result.get('files_reviewed', 0)}")
                    st.success("🤖 AI 评审已完成，并已评论到 GitLab MR！")

                with st.expander("📊 查看完整响应", expanded=False):
                    st.json(result)

                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ 审计过程中发生错误：\n\n```\n{str(e)}\n```")
                st.exception(e)

# ==============================
# Tab 2: 批量审计
# ==============================
with tab2:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    st.markdown("#### 📋 批量审计配置")
    st.markdown("每行一个任务，格式：`项目ID,源分支,目标分支`")
    st.markdown("<br>", unsafe_allow_html=True)

    batch_input = st.text_area(
        "📝 批量任务列表",
        value="86,dev_ai_check01,dev\n87,feature_branch,main",
        height=200,
        help="每行一个任务，使用英文逗号分隔：项目ID,源分支,目标分支"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<br>", unsafe_allow_html=True)
    with col2:
        batch_submitted = st.button("🚀 批量审计", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 解析批量任务
    if batch_submitted:
        try:
            tasks = []
            lines = [line.strip() for line in batch_input.strip().split('\n') if line.strip()]

            for i, line in enumerate(lines, 1):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) != 3:
                    st.error(f"❌ 第 {i} 行格式错误，应为：项目ID,源分支,目标分支")
                    break

                try:
                    pid = int(parts[0])
                except ValueError:
                    st.error(f"❌ 第 {i} 行项目ID必须是数字")
                    break

                tasks.append({
                    'project_id': pid,
                    'source_branch': parts[1],
                    'target_branch': parts[2]
                })
            else:
                # 所有任务解析成功
                if tasks:
                    st.session_state.batch_tasks = tasks
                    st.session_state.execute_batch_audit = False
                    confirm_batch_audit_dialog(tasks)
                else:
                    st.warning("⚠️ 请输入至少一个任务")

        except Exception as e:
            st.error(f"❌ 解析任务列表失败: {str(e)}")

    # 执行批量审计
    if st.session_state.get('execute_batch_audit', False):
        st.session_state.execute_batch_audit = False
        tasks = st.session_state.batch_tasks

        st.markdown("### 🔄 批量审计进行中...")
        progress_bar = st.progress(0)
        status_text = st.empty()

        results_container = st.container()

        with results_container:
            for i, task in enumerate(tasks):
                progress = (i + 1) / len(tasks)
                progress_bar.progress(progress)
                status_text.text(f"正在审计任务 {i + 1}/{len(tasks)}...")

                try:
                    req = AuditRequest(
                        project_id=task['project_id'],
                        source_branch=task['source_branch'],
                        target_branch=task['target_branch']
                    )

                    result = asyncio.run(trigger_audit(req))

                    with st.expander(f"✅ 任务 {i + 1}: 项目 {task['project_id']} - 成功", expanded=False):
                        st.markdown(f"**源分支**: `{task['source_branch']}`")
                        st.markdown(f"**目标分支**: `{task['target_branch']}`")

                        if result.get("result") != "no_code_changes":
                            st.markdown(f"**MR 标题**: {result.get('title', 'N/A')}")
                            st.markdown(f"**MR IID**: !{result.get('mr_iid', 'N/A')}")
                            st.markdown(f"**评审文件数**: {result.get('files_reviewed', 0)}")
                        else:
                            st.warning("未检测到有效代码变更")

                        st.json(result)

                except Exception as e:
                    with st.expander(f"❌ 任务 {i + 1}: 项目 {task['project_id']} - 失败", expanded=True):
                        st.markdown(f"**源分支**: `{task['source_branch']}`")
                        st.markdown(f"**目标分支**: `{task['target_branch']}`")
                        st.error(f"错误信息: {str(e)}")

        status_text.text("✅ 所有批量任务已完成！")
        st.success(f"🎉 批量审计完成！共处理 {len(tasks)} 个任务")

# ==============================
# Tab 3: 功能说明
# ==============================
with tab3:
    # 子标签页
    doc_tab1, doc_tab2, doc_tab3 = st.tabs(["核心功能", "系统架构", "工作流程"])

    # 核心功能
    with doc_tab1:
        st.markdown("### 核心功能特性")
        st.markdown("<br>", unsafe_allow_html=True)

        # 功能卡片 - 使用两列布局
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon gradient-purple'>🤖</div>
                <h4 style='color: #374151; font-weight: 700;'>AI 智能审计</h4>
                <p style='color: #6b7280; margin: 0;'>基于大语言模型的代码审查，自动发现潜在问题和优化建议</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon gradient-orange'>⚡</div>
                <h4 style='color: #374151; font-weight: 700;'>批量处理能力</h4>
                <p style='color: #6b7280; margin: 0;'>支持批量审计多个项目，提升团队协作效率</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon gradient-indigo'>🔄</div>
                <h4 style='color: #374151; font-weight: 700;'>智能过滤</h4>
                <p style='color: #6b7280; margin: 0;'>自动识别代码变更类型，跳过非代码文件和删除操作</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon gradient-blue'>🔗</div>
                <h4 style='color: #374151; font-weight: 700;'>GitLab 深度集成</h4>
                <p style='color: #6b7280; margin: 0;'>无缝对接 GitLab MR 流程，自动同步分支差异和评审结果</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon gradient-green'>🛡️</div>
                <h4 style='color: #374151; font-weight: 700;'>安全可靠</h4>
                <p style='color: #6b7280; margin: 0;'>本地化部署，代码不出域，保障企业代码资产安全</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon gradient-pink'>💻</div>
                <h4 style='color: #374151; font-weight: 700;'>多语言支持</h4>
                <p style='color: #6b7280; margin: 0;'>支持主流编程语言，覆盖前端、后端、配置文件等</p>
            </div>
            """, unsafe_allow_html=True)

    # 系统架构
    with doc_tab2:
        st.markdown("### 系统架构图")
        st.markdown("<br>", unsafe_allow_html=True)

        # 架构图
        st.markdown("""
        <div style='background: linear-gradient(135deg, #f9fafb 0%, #f3e8ff 100%); 
                    padding: 2rem; border-radius: 16px; border: 2px dashed #667eea;'>

            <div class='arch-layer'>
                <div class='arch-node gradient-purple'>Streamlit UI</div>
            </div>

            <div class='arch-arrow'>⬇️</div>

            <div class='arch-layer'>
                <div class='arch-node gradient-blue'>Audit API Controller</div>
            </div>

            <div class='arch-arrow'>⬇️</div>

            <div class='arch-layer'>
                <div class='arch-node gradient-green'>GitLab Client</div>
                <div class='arch-node gradient-green'>AI Reviewer</div>
                <div class='arch-node gradient-green'>Config Manager</div>
            </div>

            <div class='arch-arrow'>⬇️</div>

            <div class='arch-layer'>
                <div class='arch-node gradient-orange'>GitLab Server</div>
                <div class='arch-node gradient-orange'>LLM API</div>
            </div>

        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 架构说明
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class='main-card'>
                <h4 style='color: #374151; font-weight: 700; margin-bottom: 1rem;'>🔧 核心组件</h4>
                <ul style='color: #6b7280; line-height: 1.8;'>
                    <li><strong>Streamlit UI</strong>: 用户交互界面</li>
                    <li><strong>Audit API</strong>: 审计业务逻辑</li>
                    <li><strong>GitLab Client</strong>: GitLab 集成</li>
                    <li><strong>AI Reviewer</strong>: LLM 审查引擎</li>
                    <li><strong>Config Manager</strong>: 配置管理</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='main-card'>
                <h4 style='color: #374151; font-weight: 700; margin-bottom: 1rem;'>☁️ 外部依赖</h4>
                <ul style='color: #6b7280; line-height: 1.8;'>
                    <li><strong>GitLab Server</strong>: 代码仓库服务</li>
                    <li><strong>LLM API</strong>: 大语言模型服务</li>
                    <li><strong>YAML Config</strong>: 配置文件管理</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # 架构图例
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📊 图例说明")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div style='text-align: center;'>
                <div style='width: 40px; height: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            border-radius: 8px; margin: 0 auto 0.5rem;'></div>
                <small style='color: #6b7280;'>前端界面</small>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style='text-align: center;'>
                <div style='width: 40px; height: 40px; background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%); 
                            border-radius: 8px; margin: 0 auto 0.5rem;'></div>
                <small style='color: #6b7280;'>API 层</small>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style='text-align: center;'>
                <div style='width: 40px; height: 40px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                            border-radius: 8px; margin: 0 auto 0.5rem;'></div>
                <small style='color: #6b7280;'>服务层</small>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown("""
            <div style='text-align: center;'>
                <div style='width: 40px; height: 40px; background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); 
                            border-radius: 8px; margin: 0 auto 0.5rem;'></div>
                <small style='color: #6b7280;'>外部服务</small>
            </div>
            """, unsafe_allow_html=True)

    # 工作流程
    with doc_tab3:
        st.markdown("### 审计工作流程")
        st.markdown("<br>", unsafe_allow_html=True)

        # 流程步骤
        st.markdown("""
        <div class='workflow-step'>
            <span class='workflow-number'>1</span>
            <div style='display: inline-block; vertical-align: top; width: calc(100% - 60px);'>
                <h4 style='color: #374151; font-weight: 700; margin: 0 0 0.5rem 0;'>提交审计请求</h4>
                <p style='color: #6b7280; margin: 0;'>用户通过 UI 提交项目 ID 和分支信息</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='workflow-step'>
            <span class='workflow-number'>2</span>
            <div style='display: inline-block; vertical-align: top; width: calc(100% - 60px);'>
                <h4 style='color: #374151; font-weight: 700; margin: 0 0 0.5rem 0;'>获取代码差异</h4>
                <p style='color: #6b7280; margin: 0;'>从 GitLab 获取 MR 的文件变更列表和差异内容</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='workflow-step'>
            <span class='workflow-number'>3</span>
            <div style='display: inline-block; vertical-align: top; width: calc(100% - 60px);'>
                <h4 style='color: #374151; font-weight: 700; margin: 0 0 0.5rem 0;'>智能过滤</h4>
                <p style='color: #6b7280; margin: 0;'>过滤非代码文件（如图片、文档）和纯删除操作</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='workflow-step'>
            <span class='workflow-number'>4</span>
            <div style='display: inline-block; vertical-align: top; width: calc(100% - 60px);'>
                <h4 style='color: #374151; font-weight: 700; margin: 0 0 0.5rem 0;'>AI 深度分析</h4>
                <p style='color: #6b7280; margin: 0;'>调用 LLM 对代码进行深度审查，生成评审意见</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='workflow-step'>
            <span class='workflow-number'>5</span>
            <div style='display: inline-block; vertical-align: top; width: calc(100% - 60px);'>
                <h4 style='color: #374151; font-weight: 700; margin: 0 0 0.5rem 0;'>结果回传</h4>
                <p style='color: #6b7280; margin: 0;'>将审计意见自动评论到 GitLab MR，完成审计流程</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 优势与注意事项
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class='main-card' style='background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-color: #10b981;'>
                <h4 style='color: #065f46; font-weight: 700; margin-bottom: 1rem;'>✅ 优势特点</h4>
                <ul style='color: #047857; line-height: 1.8; margin: 0;'>
                    <li>全自动化流程，无需人工干预</li>
                    <li>智能过滤，只审查有效代码变更</li>
                    <li>结果直接回写 GitLab MR</li>
                    <li>支持批量处理，提升效率</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='main-card' style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-color: #3b82f6;'>
                <h4 style='color: #1e40af; font-weight: 700; margin-bottom: 1rem;'>⚠️ 注意事项</h4>
                <ul style='color: #1e3a8a; line-height: 1.8; margin: 0;'>
                    <li>确保 GitLab Token 有足够权限</li>
                    <li>配置正确的 LLM API 端点</li>
                    <li>批量审计时注意并发限制</li>
                    <li>建议先测试单个项目再批量</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 技术栈信息
        st.markdown("""
        <div class='main-card' style='background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border-color: #667eea;'>
            <h4 style='color: #5b21b6; font-weight: 700; margin-bottom: 1rem;'>🛠️ 技术栈</h4>
            <div style='display: flex; flex-wrap: wrap; gap: 0.5rem;'>
                <span class='badge badge-purple'>Python 3.8+</span>
                <span class='badge badge-blue'>Streamlit</span>
                <span class='badge badge-pink'>GitLab API</span>
                <span class='badge badge-purple'>OpenAI / Anthropic</span>
                <span class='badge badge-blue'>Async/Await</span>
                <span class='badge badge-pink'>YAML Config</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# 页脚
# ==============================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div class='main-card' style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;'>
    <p style='margin: 0; font-size: 1.1rem; font-weight: 600;'>
        🚀 YS-AICoding - 让代码审查更智能、更高效
    </p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;'>
        版本 1.0.0 | 基于 Streamlit + GitLab + LLM 构建
    </p>
</div>
""", unsafe_allow_html=True)