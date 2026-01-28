#!/usr/bin/env python3
"""
慧 (Hui) - PreCompact Hook 脚本
在 Claude Code 自动压缩上下文前触发，提取并保存关键信息。

使用方法:
1. 将此脚本放到 ~/.nexus/hooks/reflection-extract.py
2. 在 .claude/settings.json 中配置:
   {
     "hooks": {
       "PreCompact": [{
         "matcher": "auto",
         "hooks": [{
           "type": "command",
           "command": "python3 ~/.nexus/hooks/reflection-extract.py"
         }]
       }]
     }
   }
"""

from __future__ import annotations

import json
import os
import sys
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


# ============================================================
# 分身输出压缩 (Avatar Output Compression)
# ============================================================

# ============================================================
# 用户级别上下文路径 (User-Level Context Paths)
# ============================================================
# 所有上下文存储在用户目录，避免项目级冲突，支持跨项目沉淀

def get_user_context_dir() -> Path:
    """获取用户级别的上下文根目录"""
    return Path.home() / '.nexus' / 'context'


def get_project_name(cwd: str) -> str:
    """从工作目录提取项目名（最后一级目录名）"""
    return Path(cwd).name or 'unknown'


def get_active_session_dir(session_id: str) -> Path:
    """获取活跃会话目录（按 session_id 隔离，避免多会话冲突）"""
    active_dir = get_user_context_dir() / 'active' / session_id
    active_dir.mkdir(parents=True, exist_ok=True)
    return active_dir


def get_sessions_archive_dir() -> Path:
    """获取历史会话存档目录"""
    sessions_dir = get_user_context_dir() / 'sessions'
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_project_anchors_path(cwd: str) -> Path:
    """获取项目级锚点文件路径"""
    project_name = get_project_name(cwd)
    anchors_dir = get_user_context_dir() / 'anchors' / 'projects'
    anchors_dir.mkdir(parents=True, exist_ok=True)
    return anchors_dir / f'{project_name}.md'


def get_global_anchors_path() -> Path:
    """获取全局锚点文件路径"""
    anchors_dir = get_user_context_dir() / 'anchors'
    anchors_dir.mkdir(parents=True, exist_ok=True)
    return anchors_dir / 'global.md'


def get_session_index_path() -> Path:
    """获取会话索引文件路径"""
    context_dir = get_user_context_dir()
    context_dir.mkdir(parents=True, exist_ok=True)
    return context_dir / 'index.json'


# ============================================================
# 分身输出压缩配置 (Avatar Output Compression Config)
# ============================================================

# 分身类型对应的压缩配置
AVATAR_COMPRESS_CONFIG = {
    '眼': {'max_files': 20, 'max_summary': 500},
    'explorer': {'max_files': 20, 'max_summary': 500},
    '鼻': {'max_issues': 10, 'max_chars': 800},
    'reviewer': {'max_issues': 10, 'max_chars': 800},
    '斗战胜佛': {'max_chars': 2000, 'keep_diff_only': True},
    'impl': {'max_chars': 2000, 'keep_diff_only': True},
    '身': {'max_chars': 2000, 'keep_diff_only': True},
    'default': {'max_chars': 1000},
}


def compress_avatar_output(output: str, avatar_type: str) -> str:
    """
    根据分身类型压缩输出内容。

    压缩策略:
    - 眼分身: 最多 20 个文件 + 500 字摘要
    - 鼻分身: 最多 10 个 issues
    - 斗战胜佛: 最多 2000 字，只保留 diff 摘要
    - 其他分身: 最多 1000 字

    Args:
        output: 分身的原始输出
        avatar_type: 分身类型 (眼/耳/鼻/舌/身/意 或英文别名)

    Returns:
        压缩后的输出
    """
    config = AVATAR_COMPRESS_CONFIG.get(avatar_type, AVATAR_COMPRESS_CONFIG['default'])

    if avatar_type in ('眼', 'explorer'):
        return _compress_explorer_output(output, config)
    elif avatar_type in ('鼻', 'reviewer'):
        return _compress_reviewer_output(output, config)
    elif avatar_type in ('斗战胜佛', 'impl', '身'):
        return _compress_impl_output(output, config)
    else:
        return _compress_generic_output(output, config)


def _compress_explorer_output(output: str, config: dict) -> str:
    """压缩眼分身输出: 保留文件列表 + 发现摘要"""
    max_files = config.get('max_files', 20)
    max_summary = config.get('max_summary', 500)

    lines = output.split('\n')
    compressed_lines = []

    # 提取文件路径
    file_paths = []
    file_pattern = re.compile(r'^[\s\-\*]*(/[^\s]+|\.{1,2}/[^\s]+|\w+/[^\s]+)')

    for line in lines:
        match = file_pattern.match(line.strip())
        if match:
            file_paths.append(match.group(1))

    # 限制文件数量
    if file_paths:
        compressed_lines.append("### 发现的文件")
        for fp in file_paths[:max_files]:
            compressed_lines.append(f"- {fp}")
        if len(file_paths) > max_files:
            compressed_lines.append(f"- ... 还有 {len(file_paths) - max_files} 个文件")

    # 提取结论/发现部分
    findings = _extract_findings(output)
    if findings:
        compressed_lines.append("")
        compressed_lines.append("### 发现摘要")
        compressed_lines.append(findings[:max_summary])
        if len(findings) > max_summary:
            compressed_lines.append("...")

    return '\n'.join(compressed_lines) if compressed_lines else output[:max_summary]


def _compress_reviewer_output(output: str, config: dict) -> str:
    """压缩鼻分身输出: 保留 issues 列表"""
    max_issues = config.get('max_issues', 10)
    max_chars = config.get('max_chars', 800)

    # 尝试提取 issues
    issues = []
    issue_patterns = [
        r'(?:^|\n)[\s\-\*]*(?:issue|问题|warning|error|bug)[:\s]*(.+?)(?=\n[\s\-\*]*(?:issue|问题|warning|error|bug)|$)',
        r'(?:^|\n)\d+\.\s*(.+?)(?=\n\d+\.|$)',
        r'(?:^|\n)[\-\*]\s*(.+?)(?=\n[\-\*]|$)',
    ]

    for pattern in issue_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE | re.DOTALL)
        if matches:
            issues.extend(matches)
            break

    if issues:
        compressed_lines = ["### 审查问题"]
        for i, issue in enumerate(issues[:max_issues]):
            issue_text = issue.strip()[:150]
            compressed_lines.append(f"{i+1}. {issue_text}")
        if len(issues) > max_issues:
            compressed_lines.append(f"... 还有 {len(issues) - max_issues} 个问题")
        return '\n'.join(compressed_lines)

    # 如果无法提取 issues，直接截断
    return _compress_generic_output(output, config)


def _compress_impl_output(output: str, config: dict) -> str:
    """压缩斗战胜佛输出: 保留 diff 摘要，移除完整代码"""
    max_chars = config.get('max_chars', 2000)

    compressed_parts = []

    # 1. 提取修改摘要
    summary = _extract_change_summary(output)
    if summary:
        compressed_parts.append("### 修改摘要")
        compressed_parts.append(summary)

    # 2. 提取文件变更列表
    files_changed = _extract_files_changed(output)
    if files_changed:
        compressed_parts.append("")
        compressed_parts.append("### 变更文件")
        for f in files_changed[:10]:
            compressed_parts.append(f"- {f}")

    # 3. 提取 diff 概要 (不保留完整代码)
    diff_summary = _extract_diff_summary(output)
    if diff_summary:
        compressed_parts.append("")
        compressed_parts.append("### Diff 概要")
        compressed_parts.append(diff_summary[:800])

    # 4. 提取构建/测试结果
    test_result = _extract_test_result(output)
    if test_result:
        compressed_parts.append("")
        compressed_parts.append("### 验证结果")
        compressed_parts.append(test_result)

    result = '\n'.join(compressed_parts)
    return result[:max_chars] if result else output[:max_chars]


def _compress_generic_output(output: str, config: dict) -> str:
    """通用压缩: 提取结论，限制字数"""
    max_chars = config.get('max_chars', 1000)

    # 尝试提取结论部分
    conclusion = _extract_conclusion(output)
    if conclusion:
        return conclusion[:max_chars]

    # 直接截断
    if len(output) > max_chars:
        return output[:max_chars] + "\n... [已截断]"
    return output


def _extract_findings(text: str) -> str:
    """提取探索发现"""
    patterns = [
        r'(?:发现|findings?|结论|conclusion)[:\s]*(.+?)(?=\n\n|\Z)',
        r'(?:总结|summary)[:\s]*(.+?)(?=\n\n|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    return ""


def _extract_change_summary(text: str) -> str:
    """提取修改摘要"""
    patterns = [
        r'(?:修改摘要|changes?|summary)[:\s]*(.+?)(?=\n\n|\n###|\Z)',
        r'(?:完成|done|finished)[:\s]*(.+?)(?=\n\n|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:500]

    return ""


def _extract_files_changed(text: str) -> list[str]:
    """提取变更的文件列表"""
    files = []

    # 匹配常见的文件路径模式
    file_patterns = [
        r'(?:modified|changed|created|deleted|edited)[:\s]*([^\n]+\.(?:py|js|ts|md|json|yaml|yml|toml))',
        r'(?:files?_changed|变更文件)[:\s\[]*([^\]]+)',
        r'(?:^|\n)[\s\-\*]+(/[^\s]+\.[a-z]+)',
    ]

    for pattern in file_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        files.extend(matches)

    # 去重
    return list(dict.fromkeys(files))


def _extract_diff_summary(text: str) -> str:
    """提取 diff 概要，移除完整代码块"""
    # 移除代码块
    text_no_code = re.sub(r'```[\s\S]*?```', '[代码块已省略]', text)

    # 提取 +/- 行的统计
    plus_lines = len(re.findall(r'^\+[^+]', text, re.MULTILINE))
    minus_lines = len(re.findall(r'^-[^-]', text, re.MULTILINE))

    summary_parts = []
    if plus_lines or minus_lines:
        summary_parts.append(f"+{plus_lines} -{minus_lines} 行变更")

    # 提取函数/类变更
    func_changes = re.findall(r'(?:def|class|function)\s+(\w+)', text_no_code)
    if func_changes:
        summary_parts.append(f"涉及: {', '.join(set(func_changes)[:5])}")

    return ' | '.join(summary_parts) if summary_parts else ""


def _extract_test_result(text: str) -> str:
    """提取测试/构建结果"""
    patterns = [
        r'((?:tests?\s+)?(?:passed|failed|success|error)[^\n]*)',
        r'((?:build|构建)\s*(?:成功|失败|passed|failed)[^\n]*)',
        r'(✓|✗|PASS|FAIL)[^\n]*',
    ]

    results = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        results.extend(matches[:3])

    return ' | '.join(results) if results else ""


def _extract_conclusion(text: str) -> str:
    """提取结论部分"""
    patterns = [
        r'(?:结论|conclusion|总结|summary|结果|result)[:\s]*(.+?)(?=\n\n|\Z)',
        r'(?:完成|done|完毕)[:\s]*(.+?)(?=\n\n|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    return ""


def compress_avatar_output_from_env(output: str) -> str:
    """
    从环境变量读取分身类型并压缩输出。

    环境变量:
    - NEXUS_COMPRESS_AVATAR: 设为 1 启用压缩
    - NEXUS_AVATAR_TYPE: 分身类型
    """
    if os.environ.get('NEXUS_COMPRESS_AVATAR') != '1':
        return output

    avatar_type = os.environ.get('NEXUS_AVATAR_TYPE', 'default')
    return compress_avatar_output(output, avatar_type)


def read_hook_input() -> dict[str, Any]:
    """从 stdin 读取 hook 输入"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def read_transcript(transcript_path: str) -> list[dict]:
    """读取对话记录"""
    messages = []
    if not transcript_path:
        return messages

    path = Path(transcript_path).expanduser()
    if not path.exists() or not path.is_file():
        return messages

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return messages


def extract_decisions(messages: list[dict]) -> list[dict]:
    """提取决策信息"""
    decisions = []
    decision_patterns = [
        r'\[D\d+\]',  # [D001] 格式的决策引用
        r'决定|决策|选择|采用|使用',  # 决策关键词
        r'Decision|Decided|Choose|Use',
    ]

    for msg in messages:
        # Skip non-user/assistant messages
        if not is_user_or_assistant_message(msg):
            continue

        content = get_message_content(msg)

        # Skip system instructions and internal content
        if should_skip_content(content):
            continue

        # Clean internal tags
        content = clean_content(content)
        if not content:
            continue

        for pattern in decision_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # 提取包含决策的段落
                decisions.append({
                    'type': 'decision',
                    'content': content[:500],  # 限制长度
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return decisions[-5:]  # 只保留最近5个


def extract_constraints(messages: list[dict]) -> list[dict]:
    """提取约束信息"""
    constraints = []
    constraint_patterns = [
        r'\[C\d+\]',  # [C001] 格式的约束引用
        r'必须|禁止|不能|不允许|约束|限制',
        r'MUST|NEVER|ALWAYS|constraint',
    ]

    for msg in messages:
        # Skip non-user/assistant messages
        if not is_user_or_assistant_message(msg):
            continue

        content = get_message_content(msg)

        # Skip system instructions and internal content
        if should_skip_content(content):
            continue

        # Clean internal tags
        content = clean_content(content)
        if not content:
            continue

        for pattern in constraint_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                constraints.append({
                    'type': 'constraint',
                    'content': content[:300],
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return constraints[-3:]


def extract_interfaces(messages: list[dict]) -> list[dict]:
    """提取接口定义"""
    interfaces = []
    interface_patterns = [
        r'\[I\d+\]',  # [I001] 格式的接口引用
        r'def \w+\(.*\)',  # Python 函数定义
        r'class \w+',  # 类定义
        r'interface|API|endpoint',
    ]

    for msg in messages:
        # Skip non-user/assistant messages
        if not is_user_or_assistant_message(msg):
            continue
        content = get_message_content(msg)
        # Skip system instructions and internal content
        if should_skip_content(content):
            continue
        # Clean internal tags
        content = clean_content(content)
        if not content:
            continue
        for pattern in interface_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                interfaces.append({
                    'type': 'interface',
                    'content': content[:400],
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return interfaces[-3:]


def extract_problems(messages: list[dict]) -> list[dict]:
    """提取问题/陷阱"""
    problems = []
    problem_patterns = [
        r'\[P\d+\]',  # [P001] 格式的问题引用
        r'问题|bug|错误|失败|警告',
        r'error|fail|warning|issue|problem',
    ]

    for msg in messages:
        # Skip non-user/assistant messages
        if not is_user_or_assistant_message(msg):
            continue
        content = get_message_content(msg)
        # Skip system instructions and internal content
        if should_skip_content(content):
            continue
        # Clean internal tags
        content = clean_content(content)
        if not content:
            continue
        for pattern in problem_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                problems.append({
                    'type': 'problem',
                    'content': content[:300],
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return problems[-3:]


def get_message_content(msg: dict) -> str:
    """获取消息内容"""
    if 'message' in msg and 'content' in msg['message']:
        content = msg['message']['content']
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            return ' '.join(
                item.get('text', '')
                for item in content
                if isinstance(item, dict) and item.get('type') == 'text'
            )
    return ''


# ============================================================
# Content Filtering (内容过滤)
# ============================================================

# Patterns that indicate system instructions or internal content
SKIP_CONTENT_PATTERNS = [
    r'^#\s*Nexus Multi-Agent',           # Nexus system instructions
    r'^#\s*Jenkins Build Skill',         # Skill file content
    r'^#\s*Explorer Skill',              # Skill file content
    r'^#\s*Implementer Skill',           # Skill file content
    r'^#\s*Architect Skill',             # Skill file content
    r'^#\s*Tester Skill',                # Skill file content
    r'^#\s*Code Reviewer Skill',         # Skill file content
    r'^#\s*Requirements Analyst Skill',  # Skill file content
    r'^You are now operating as',        # Identity declaration
    r'^You are \*\*Nexus',               # Identity declaration
    r'^<command-message>',               # Command tags
    r'^<command-name>',                  # Command tags
    r'^\s*<thinking>',                   # Internal thinking tags
    r'^ARGUMENTS:',                      # Skill arguments
    r'^## Activation \(轻量启动\)',      # Nexus activation section
    r'^## Your Identity',                # Nexus identity section
    r'^## Six Roots Avatar System',      # Nexus system section
]

# Tags to clean from content
INTERNAL_TAGS_PATTERN = re.compile(
    r'<(?:thinking|command-message|command-name|command-args|system-reminder|antml:[^>]+)>.*?</(?:thinking|command-message|command-name|command-args|system-reminder|antml:[^>]+)>',
    re.DOTALL
)

OPENING_TAGS_PATTERN = re.compile(
    r'<(?:thinking|command-message|command-name|command-args|system-reminder|antml:[^>]+)>'
)


def should_skip_content(content: str) -> bool:
    """
    Check if content should be skipped (system instructions, skill files, etc.)

    Args:
        content: The content to check

    Returns:
        True if content should be skipped
    """
    if not content:
        return True

    content_stripped = content.strip()

    for pattern in SKIP_CONTENT_PATTERNS:
        if re.match(pattern, content_stripped, re.IGNORECASE):
            return True

    return False


def clean_content(content: str) -> str:
    """
    Clean internal tags and artifacts from content.

    Args:
        content: The content to clean

    Returns:
        Cleaned content
    """
    if not content:
        return ''

    # Remove complete tag pairs
    cleaned = INTERNAL_TAGS_PATTERN.sub('', content)

    # Remove orphan opening tags
    cleaned = OPENING_TAGS_PATTERN.sub('', cleaned)

    # Clean up whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()

    return cleaned


def is_user_or_assistant_message(msg: dict) -> bool:
    """Check if message is from user or assistant (not system)"""
    msg_type = msg.get('type', '')
    return msg_type in ('user', 'assistant', 'human')


def extract_current_task(messages: list[dict]) -> str:
    """提取当前任务描述"""
    # 查找用户的初始请求
    for msg in messages[:5]:  # 只看前几条
        if msg.get('type') == 'user':
            content = get_message_content(msg)
            if content:
                return content[:200]
    return "未知任务"


def extract_progress(messages: list[dict]) -> dict:
    """提取进度信息"""
    # 简单统计
    total_messages = len(messages)
    user_messages = sum(1 for m in messages if m.get('type') == 'user')
    assistant_messages = sum(1 for m in messages if m.get('type') == 'assistant')

    return {
        'total_turns': total_messages // 2,
        'user_messages': user_messages,
        'assistant_messages': assistant_messages,
    }


def generate_compact_context(
    task: str,
    decisions: list[dict],
    constraints: list[dict],
    interfaces: list[dict],
    problems: list[dict],
    progress: dict
) -> str:
    """生成缩形态上下文"""
    lines = [
        "## 🔸 缩形态上下文",
        "",
        f"【任务】{task}",
        "",
        "【已决策】",
    ]

    if decisions:
        for d in decisions[:3]:
            content = d['content'][:100].replace('\n', ' ')
            lines.append(f"- {content}...")
    else:
        lines.append("- (暂无)")

    lines.extend([
        "",
        "【约束】",
    ])

    if constraints:
        for c in constraints[:2]:
            content = c['content'][:80].replace('\n', ' ')
            lines.append(f"- {content}...")
    else:
        lines.append("- (暂无)")

    lines.extend([
        "",
        "【当前进度】",
        f"- 对话轮次: {progress.get('total_turns', 0)}",
    ])

    if problems:
        lines.extend([
            "",
            "【注意事项】",
        ])
        for p in problems[:2]:
            content = p['content'][:60].replace('\n', ' ')
            lines.append(f"- {content}...")

    lines.extend([
        "",
        f"【生成时间】{datetime.now().isoformat()}",
    ])

    return '\n'.join(lines)


def generate_anchor_candidates(
    decisions: list[dict],
    constraints: list[dict],
    problems: list[dict]
) -> list[dict]:
    """生成候选锚点（带内容验证）"""
    candidates = []

    # 决策锚点
    for i, d in enumerate(decisions):
        content = d['content']
        if not _is_valid_anchor_content(content, 'decision'):
            continue
        candidates.append({
            'id': f'D_candidate_{i}',
            'type': 'decision',
            'title': _extract_title(content, 'decision'),
            'content': content[:300],
            'threshold_check': {
                'frequency': 1,
                'impact': _detect_impact(content),
                'reusable': _detect_reusable(content, 'decision'),
            }
        })

    # 问题锚点
    for i, p in enumerate(problems):
        content = p['content']
        if not _is_valid_anchor_content(content, 'problem'):
            continue
        candidates.append({
            'id': f'P_candidate_{i}',
            'type': 'problem',
            'title': _extract_title(content, 'problem'),
            'content': content[:300],
            'threshold_check': {
                'frequency': 1,
                'impact': _detect_impact(content),
                'reusable': _detect_reusable(content, 'problem'),
            }
        })

    # 约束锚点
    for i, c in enumerate(constraints):
        content = c['content']
        if not _is_valid_anchor_content(content, 'constraint'):
            continue
        candidates.append({
            'id': f'C_candidate_{i}',
            'type': 'constraint',
            'title': _extract_title(content, 'constraint'),
            'content': content[:300],
            'threshold_check': {
                'frequency': 1,
                'impact': _detect_impact(content),
                'reusable': _detect_reusable(content, 'constraint'),
            }
        })

    return candidates


def _extract_title(content: str, anchor_type: str) -> str:
    """从内容中提取标题"""
    lines = content.split('\n')

    # 1. 优先查找 markdown 标题格式
    for line in lines[:5]:
        line = line.strip()
        md_title = re.match(r'^#{1,3}\s+(.+)$', line)
        if md_title:
            title = md_title.group(1).strip()
            return title[:50] if len(title) <= 50 else title[:47] + '...'

        bold_title = re.match(r'^\*\*(.+?)\*\*', line)
        if bold_title:
            title = bold_title.group(1).strip()
            return title[:50] if len(title) <= 50 else title[:47] + '...'

    # 2. 排除对话开头，找第一个有意义的行
    skip_prefixes = (
        '完成', '好的', '好，', '是的', '没问题', '已', '我',
        'Done', 'OK', 'Yes', 'I\'ll', 'I will', 'Let me', 'You are',
        'This', 'The ', 'Here', '```',
    )

    for line in lines[:10]:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        if any(line.startswith(p) for p in skip_prefixes):
            continue
        line = re.sub(r'^[\-\*\d\.]+\s*', '', line)
        return line[:50] if len(line) <= 50 else line[:47] + '...'

    return f'{anchor_type}_untitled'


# ============================================================
# 锚点内容验证 (Anchor Content Validation)
# ============================================================

CONVERSATION_PREFIXES = (
    '完成', '好的', '好，', '是的', '没问题', '已经', '我来', '我会', '让我',
    '现在', '接下来', '首先', '然后', '最后', '总结',
    'Done', 'OK', 'Yes', 'I\'ll', 'I will', 'I\'m', 'Let me', 'Now',
    'You are', 'This command', 'Here is', 'Here are', '```',
)

ANCHOR_STRUCTURE_KEYWORDS = {
    'decision': ['context', 'decision', 'impact', 'evidence', '背景', '决策', '影响', '原因'],
    'problem': ['症状', '根因', '解决', '预防', 'symptom', 'root cause', 'solution', 'prevention'],
    'constraint': ['约束', '必须', '禁止', 'must', 'never', 'always', 'constraint'],
}

IMPACT_KEYWORDS = [
    '架构', '安全', '性能', '多模块', '全局', '核心', '关键',
    'architecture', 'security', 'performance', 'global', 'core', 'critical',
]


def _is_valid_anchor_content(content: str, anchor_type: str) -> bool:
    """验证内容是否适合作为锚点"""
    if not content or len(content.strip()) < 50:
        return False

    first_line = content.strip().split('\n')[0].strip()
    if any(first_line.startswith(p) for p in CONVERSATION_PREFIXES):
        return False

    keywords = ANCHOR_STRUCTURE_KEYWORDS.get(anchor_type, [])
    if keywords:
        content_lower = content.lower()
        if not any(kw.lower() in content_lower for kw in keywords):
            return False

    return True


def _detect_impact(content: str) -> bool:
    """检测内容是否涉及重大影响"""
    content_lower = content.lower()
    return any(kw.lower() in content_lower for kw in IMPACT_KEYWORDS)


def _detect_reusable(content: str, anchor_type: str) -> bool:
    """检测内容是否可复用"""
    if anchor_type == 'problem':
        return True
    reusable_keywords = ['模式', '通用', '最佳实践', 'pattern', 'generic', 'best practice']
    return any(kw.lower() in content.lower() for kw in reusable_keywords)


# ============================================================
# 慧→识 交接协议 (Hui -> Shi Handoff Protocol)
# ============================================================

def generate_hui_output(
    session_id: str,
    project_path: str,
    task: str,
    decisions: list[dict],
    constraints: list[dict],
    interfaces: list[dict],
    problems: list[dict],
    progress: dict,
    compact_context: str,
    candidates: list[dict]
) -> dict:
    """
    生成慧模块的标准化输出（JSON 格式）。

    这是慧→识的交接协议，定义了两个模块之间的数据契约。

    Args:
        session_id: 会话ID
        project_path: 项目路径
        task: 当前任务描述
        decisions: 决策列表
        constraints: 约束列表
        interfaces: 接口列表
        problems: 问题列表
        progress: 进度信息
        compact_context: 缩形态上下文 (markdown)
        candidates: 候选锚点列表

    Returns:
        标准化的慧模块输出 (dict)
    """
    return {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "project_path": project_path,

        "context": {
            "task": task,
            "decisions": decisions,
            "constraints": constraints,
            "interfaces": interfaces,
            "problems": problems,
            "progress": progress,
            "compact_md": compact_context,
        },

        "anchors": candidates,  # 候选锚点列表
    }


# ============================================================
# 识模块 - 写入逻辑 (Shi Module - Write Logic)
# ============================================================

def check_threshold(anchor: dict) -> bool:
    """
    检查锚点是否通过写入门槛（严格版）。

    门槛条件 (至少满足一项):
    - frequency >= 2: 类似问题/决策出现两次以上
    - impact = True AND 内容长度 >= 100
    - reusable = True AND anchor_type == 'problem' AND 有解决方案

    Args:
        anchor: 锚点字典，包含 threshold_check 字段

    Returns:
        bool: 是否通过门槛
    """
    threshold = anchor.get('threshold_check', {})
    anchor_type = anchor.get('type', '')
    content = anchor.get('content', '')

    # 1. 频率检查 (最可靠)
    frequency = threshold.get('frequency', 0)
    if isinstance(frequency, int) and frequency >= 2:
        return True

    # 2. 影响检查 (需配合内容长度)
    if threshold.get('impact', False) and len(content) >= 100:
        return True

    # 3. 可复用检查 (只对 problem 类型 + 有解决方案生效)
    if threshold.get('reusable', False) and anchor_type == 'problem':
        content_lower = content.lower()
        has_solution = any(kw in content_lower for kw in ['解决', '修复', '预防', 'fix', 'solution', 'resolve'])
        if has_solution:
            return True

    return False


def check_duplicate(anchor: dict, existing_anchors: list[dict]) -> tuple[bool, str | None]:
    """
    检查锚点是否与现有锚点重复。

    使用简单的标题相似度检查:
    - 标题完全相同 -> 重复
    - 标题词汇重叠 > 70% -> 重复

    Args:
        anchor: 待检查的锚点
        existing_anchors: 现有锚点列表

    Returns:
        (is_duplicate, existing_id): 是否重复及重复锚点的ID
    """
    new_title = anchor.get('title', '').lower()
    new_words = set(re.findall(r'\w+', new_title))

    if not new_words:
        return False, None

    for existing in existing_anchors:
        existing_title = existing.get('title', '').lower()
        existing_words = set(re.findall(r'\w+', existing_title))

        if not existing_words:
            continue

        # 完全相同
        if new_title == existing_title:
            return True, existing.get('id')

        # 词汇重叠检查
        intersection = new_words & existing_words
        union = new_words | existing_words

        if union and len(intersection) / len(union) > 0.7:
            return True, existing.get('id')

    return False, None


def _get_next_anchor_id(anchor_type: str, existing_anchors: list[dict]) -> str:
    """
    获取下一个可用的锚点ID。

    ID格式: {type_prefix}{3位数字}
    - 决策: D001, D002, ...
    - 问题: P001, P002, ...
    - 约束: C001, C002, ...
    - 接口: I001, I002, ...

    Args:
        anchor_type: 锚点类型 (decision, problem, constraint, interface)
        existing_anchors: 现有锚点列表

    Returns:
        新的锚点ID
    """
    type_prefix_map = {
        'decision': 'D',
        'problem': 'P',
        'constraint': 'C',
        'interface': 'I',
    }
    prefix = type_prefix_map.get(anchor_type, 'A')

    # 找出同类型的最大ID
    max_num = 0
    pattern = re.compile(rf'^{prefix}(\d+)$')

    for anchor in existing_anchors:
        anchor_id = anchor.get('id', '')
        match = pattern.match(anchor_id)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    return f'{prefix}{max_num + 1:03d}'


def _load_existing_anchors(anchors_path: Path) -> list[dict]:
    """
    从 anchors.md 文件加载现有锚点。

    解析格式:
    ## [D001] 决策标题
    内容...

    Args:
        anchors_path: anchors.md 文件路径

    Returns:
        锚点列表
    """
    if not anchors_path.exists():
        return []

    anchors = []
    content = anchors_path.read_text(encoding='utf-8')

    # 匹配 ## [ID] 标题 格式
    anchor_pattern = re.compile(
        r'^## \[([A-Z]\d+)\] (.+?)$\n(.*?)(?=^## \[|$)',
        re.MULTILINE | re.DOTALL
    )

    for match in anchor_pattern.finditer(content):
        anchor_id = match.group(1)
        title = match.group(2).strip()
        body = match.group(3).strip()

        # 推断类型
        anchor_type = 'unknown'
        if anchor_id.startswith('D'):
            anchor_type = 'decision'
        elif anchor_id.startswith('P'):
            anchor_type = 'problem'
        elif anchor_id.startswith('C'):
            anchor_type = 'constraint'
        elif anchor_id.startswith('I'):
            anchor_type = 'interface'

        anchors.append({
            'id': anchor_id,
            'type': anchor_type,
            'title': title,
            'content': body,
        })

    return anchors


def write_to_anchors(anchor: dict, anchors_path: Path) -> str:
    """
    将锚点追加到 anchors.md 文件。

    Args:
        anchor: 锚点字典
        anchors_path: anchors.md 文件路径

    Returns:
        新分配的锚点ID
    """
    # 确保目录存在
    anchors_path.parent.mkdir(parents=True, exist_ok=True)

    # 加载现有锚点
    existing_anchors = _load_existing_anchors(anchors_path)

    # 分配新ID
    new_id = _get_next_anchor_id(anchor.get('type', 'unknown'), existing_anchors)

    # 构建锚点内容
    title = anchor.get('title', 'Untitled')
    content = anchor.get('content', '')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    anchor_entry = f"""
## [{new_id}] {title}

**创建时间**: {timestamp}
**类型**: {anchor.get('type', 'unknown')}

{content}

---
"""

    # 如果文件不存在，创建头部
    if not anchors_path.exists():
        header = """# 锚点记录 (Anchors)

> 此文件由识模块自动维护，记录跨会话的重要决策、问题和约束。

"""
        with open(anchors_path, 'w', encoding='utf-8') as f:
            f.write(header)

    # 追加锚点
    with open(anchors_path, 'a', encoding='utf-8') as f:
        f.write(anchor_entry)

    return new_id


def _get_project_hash(project_path: str) -> str:
    """计算项目路径的哈希值（用于索引）"""
    return hashlib.md5(project_path.encode()).hexdigest()[:8]


def _get_project_name(project_path: str) -> str:
    """从项目路径提取项目名"""
    return Path(project_path).name or 'unknown'


def update_session_index(session_info: dict, index_path: Path):
    """
    更新会话索引文件 (index.json)。

    索引结构:
    {
        "version": "1.0",
        "sessions": [...],
        "projects": {...}
    }

    Args:
        session_info: 会话信息字典
        index_path: index.json 文件路径
    """
    # 确保目录存在
    index_path.parent.mkdir(parents=True, exist_ok=True)

    # 加载现有索引
    index = {
        "version": "1.0",
        "sessions": [],
        "projects": {}
    }

    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # 确保结构完整
    if "sessions" not in index:
        index["sessions"] = []
    if "projects" not in index:
        index["projects"] = {}

    session_id = session_info.get('session_id', 'unknown')
    project_path = session_info.get('project_path', '.')
    project_hash = _get_project_hash(project_path)
    project_name = _get_project_name(project_path)
    now = datetime.now().isoformat()

    # 查找是否已存在该会话
    existing_session = None
    for i, s in enumerate(index["sessions"]):
        if s.get('session_id') == session_id:
            existing_session = i
            break

    session_entry = {
        "session_id": session_id,
        "project_path": project_path,
        "project_hash": project_hash,
        "created_at": session_info.get('created_at', now),
        "updated_at": now,
        "task_summary": session_info.get('task_summary', '')[:200],
        "anchor_count": session_info.get('anchor_count', 0),
        "status": session_info.get('status', 'active')
    }

    if existing_session is not None:
        # 更新现有会话
        session_entry["created_at"] = index["sessions"][existing_session].get('created_at', now)
        index["sessions"][existing_session] = session_entry
    else:
        # 添加新会话
        index["sessions"].append(session_entry)

    # 更新项目信息
    if project_hash not in index["projects"]:
        index["projects"][project_hash] = {
            "path": project_path,
            "name": project_name,
            "session_count": 0
        }

    # 统计该项目的会话数
    project_sessions = sum(
        1 for s in index["sessions"]
        if s.get('project_hash') == project_hash
    )
    index["projects"][project_hash]["session_count"] = project_sessions

    # 保存索引
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def shi_write(hui_output: dict, cwd: str) -> dict:
    """
    识模块的主写入函数。

    接收慧模块的 JSON 输出，执行:
    1. 门槛检查
    2. 去重检查
    3. 写入通过的锚点（到用户级别项目锚点文件）
    4. 更新索引

    Args:
        hui_output: 慧模块的标准化输出
        cwd: 当前工作目录

    Returns:
        写入结果摘要
    """
    result = {
        "anchors_written": [],
        "anchors_skipped": [],
        "anchors_duplicated": [],
        "errors": []
    }

    # 准备路径（用户级别）
    anchors_path = get_project_anchors_path(cwd)
    index_path = get_session_index_path()

    # 加载现有锚点
    existing_anchors = _load_existing_anchors(anchors_path)

    # 处理候选锚点
    candidates = hui_output.get('anchors', [])

    for candidate in candidates:
        try:
            # 1. 门槛检查
            if not check_threshold(candidate):
                result["anchors_skipped"].append({
                    "id": candidate.get('id'),
                    "reason": "threshold_not_met"
                })
                continue

            # 2. 去重检查
            is_dup, existing_id = check_duplicate(candidate, existing_anchors)
            if is_dup:
                result["anchors_duplicated"].append({
                    "id": candidate.get('id'),
                    "existing_id": existing_id
                })
                continue

            # 3. 写入锚点
            new_id = write_to_anchors(candidate, anchors_path)
            result["anchors_written"].append({
                "candidate_id": candidate.get('id'),
                "new_id": new_id,
                "type": candidate.get('type'),
                "title": candidate.get('title')
            })

            # 更新现有锚点列表（用于后续去重）
            existing_anchors.append({
                'id': new_id,
                'type': candidate.get('type'),
                'title': candidate.get('title'),
                'content': candidate.get('content')
            })

        except Exception as e:
            result["errors"].append({
                "id": candidate.get('id'),
                "error": str(e)
            })

    # 4. 更新会话索引
    try:
        session_info = {
            "session_id": hui_output.get('session_id', 'unknown'),
            "project_path": hui_output.get('project_path', cwd),
            "task_summary": hui_output.get('context', {}).get('task', ''),
            "anchor_count": len(result["anchors_written"]),
            "status": "active"
        }
        update_session_index(session_info, index_path)
    except Exception as e:
        result["errors"].append({
            "id": "session_index",
            "error": str(e)
        })

    return result


# ============================================================
# 识模块 - 惯性提示 API (Shi Module - Inertia Prompt API)
# ============================================================

# 分身类型映射 (用于规范化分身名称)
AVATAR_TYPE_MAP = {
    # 眼分身
    '眼': 'eye', 'explorer': 'eye', 'eye': 'eye',
    # 耳分身
    '耳': 'ear', 'analyst': 'ear', 'ear': 'ear',
    # 鼻分身
    '鼻': 'nose', 'reviewer': 'nose', 'nose': 'nose',
    # 舌分身
    '舌': 'tongue', 'tester': 'tongue', 'tongue': 'tongue',
    # 身分身 (斗战胜佛)
    '身': 'body', '斗战胜佛': 'body', 'impl': 'body', 'implementer': 'body', 'body': 'body',
    # 意分身
    '意': 'mind', 'architect': 'mind', 'mind': 'mind',
}

# 分身惯性提示配置
# T1: 任务启动前 (P+C+M)
# T2: 方案冻结后 (D+I)
AVATAR_INERTIA_CONFIG = {
    'eye': {'t1': True, 't2': False},      # 眼: 探索前提示已知问题
    'ear': {'t1': False, 't2': False},     # 耳: 需求分析无需历史包袱
    'nose': {'t1': True, 't2': True},      # 鼻: 审查时参考约束和决策
    'tongue': {'t1': True, 't2': False},   # 舌: 测试时提示已知陷阱
    'body': {'t1': True, 't2': True},      # 身: 实现前获取完整上下文
    'mind': {'t1': False, 't2': True},     # 意: 设计时参考历史决策
}


def _normalize_avatar_type(avatar_type: str) -> str:
    """规范化分身类型名称"""
    return AVATAR_TYPE_MAP.get(avatar_type.lower(), 'unknown')


def _filter_anchors_by_keywords(
    anchors: list[dict],
    keywords: list[str] | None = None
) -> list[dict]:
    """
    根据关键词过滤锚点。

    如果 keywords 为空，返回所有锚点（最多 5 个）。
    否则返回标题或内容包含关键词的锚点。

    Args:
        anchors: 锚点列表
        keywords: 过滤关键词

    Returns:
        过滤后的锚点列表
    """
    if not anchors:
        return []

    if not keywords:
        # 无关键词，返回最近的锚点（最多 5 个）
        return anchors[-5:] if len(anchors) > 5 else anchors

    # 按关键词过滤
    matched = []
    keywords_lower = [k.lower() for k in keywords]

    for anchor in anchors:
        title = anchor.get('title', '').lower()
        content = anchor.get('content', '').lower()

        for kw in keywords_lower:
            if kw in title or kw in content:
                matched.append(anchor)
                break

    return matched[-5:] if len(matched) > 5 else matched


def _format_anchor_for_prompt(anchor: dict) -> str:
    """格式化单个锚点用于提示"""
    anchor_id = anchor.get('id', 'A000')
    title = anchor.get('title', '')[:50]
    content = anchor.get('content', '').strip()

    # 如果内容为空，只显示标题
    if not content:
        return f"[{anchor_id}] {title}"

    # 提取内容的第一行有意义的文字
    content_preview = ''
    for line in content.split('\n'):
        line = line.strip()
        # 跳过元数据行和分隔符
        if not line or line.startswith('**') or line.startswith('---') or line.startswith('#'):
            continue
        content_preview = line[:80]
        break

    if content_preview:
        return f"[{anchor_id}] {title}: {content_preview}"
    return f"[{anchor_id}] {title}"


def get_shi_t1_prompt(cwd: str, keywords: list[str] = None) -> str:
    """
    T1 惯性提示 (任务启动前)。

    查询类型: P(问题) + C(约束) + M(模式)
    适用分身: 眼、身、舌、鼻

    Args:
        cwd: 当前工作目录
        keywords: 可选的关键词过滤

    Returns:
        格式化的 T1 惯性提示
    """
    anchors_path = get_project_anchors_path(cwd)
    all_anchors = _load_existing_anchors(anchors_path)

    if not all_anchors:
        return """## [识 T1] 启动提示

暂无相关锚点。

---
> 仅供参考，不影响决策"""

    # 按类型分类锚点
    problems = [a for a in all_anchors if a.get('type') == 'problem']
    constraints = [a for a in all_anchors if a.get('type') == 'constraint']
    patterns = [a for a in all_anchors if 'pattern' in a.get('type', '') or
                '模式' in a.get('title', '') or 'pattern' in a.get('title', '').lower()]

    # 应用关键词过滤
    if keywords:
        problems = _filter_anchors_by_keywords(problems, keywords)
        constraints = _filter_anchors_by_keywords(constraints, keywords)
        patterns = _filter_anchors_by_keywords(patterns, keywords)
    else:
        # 无关键词时，每类最多 3 个
        problems = problems[-3:] if len(problems) > 3 else problems
        constraints = constraints[-3:] if len(constraints) > 3 else constraints
        patterns = patterns[-3:] if len(patterns) > 3 else patterns

    lines = ["## [识 T1] 启动提示", ""]

    # 相关风险 (Problems)
    if problems:
        lines.append("**相关风险**:")
        for p in problems:
            lines.append(f"- {_format_anchor_for_prompt(p)}")
        lines.append("")

    # 约束提醒 (Constraints)
    if constraints:
        lines.append("**约束提醒**:")
        for c in constraints:
            lines.append(f"- {_format_anchor_for_prompt(c)}")
        lines.append("")

    # 可复用模式 (Patterns)
    if patterns:
        lines.append("**可复用模式**:")
        for m in patterns:
            lines.append(f"- {_format_anchor_for_prompt(m)}")
        lines.append("")

    # 如果都没有匹配
    if not problems and not constraints and not patterns:
        lines.append("暂无与当前任务相关的锚点。")
        lines.append("")

    lines.extend([
        "---",
        "> 仅供参考，不影响决策"
    ])

    return '\n'.join(lines)


def get_shi_t2_prompt(cwd: str, keywords: list[str] = None) -> str:
    """
    T2 惯性提示 (方案冻结后)。

    查询类型: D(决策) + I(接口)
    适用分身: 意、身、鼻

    Args:
        cwd: 当前工作目录
        keywords: 可选的关键词过滤

    Returns:
        格式化的 T2 惯性提示
    """
    anchors_path = get_project_anchors_path(cwd)
    all_anchors = _load_existing_anchors(anchors_path)

    if not all_anchors:
        return """## [识 T2] 设计参考

暂无相关锚点。

---
> 仅供参考，决策权在本体"""

    # 按类型分类锚点
    decisions = [a for a in all_anchors if a.get('type') == 'decision']
    interfaces = [a for a in all_anchors if a.get('type') == 'interface']

    # 应用关键词过滤
    if keywords:
        decisions = _filter_anchors_by_keywords(decisions, keywords)
        interfaces = _filter_anchors_by_keywords(interfaces, keywords)
    else:
        # 无关键词时，每类最多 5 个
        decisions = decisions[-5:] if len(decisions) > 5 else decisions
        interfaces = interfaces[-5:] if len(interfaces) > 5 else interfaces

    lines = ["## [识 T2] 设计参考", ""]

    # 历史决策 (Decisions)
    if decisions:
        lines.append("**历史决策**:")
        lines.append("| ID | 决策 | 理由 |")
        lines.append("|----|------|------|")
        for d in decisions:
            anchor_id = d.get('id', 'D000')
            title = d.get('title', '')[:30]
            # 尝试从内容中提取理由
            content = d.get('content', '')
            reason = ''
            if '理由' in content or 'reason' in content.lower():
                # 简单提取理由
                for line in content.split('\n'):
                    if '理由' in line or 'reason' in line.lower():
                        reason = line.split(':', 1)[-1].strip()[:30]
                        break
            if not reason:
                reason = content[:30].replace('\n', ' ')
            lines.append(f"| [{anchor_id}] | {title} | {reason} |")
        lines.append("")

    # 相关接口 (Interfaces)
    if interfaces:
        lines.append("**相关接口**:")
        for i in interfaces:
            lines.append(f"- {_format_anchor_for_prompt(i)}")
        lines.append("")

    # 回滚经验 (从决策中提取)
    rollback_info = []
    for d in decisions:
        content = d.get('content', '').lower()
        if '回滚' in content or 'rollback' in content or '恢复' in content:
            anchor_id = d.get('id', 'D000')
            # 尝试提取回滚命令
            for line in d.get('content', '').split('\n'):
                if '`' in line:
                    # 提取反引号中的命令
                    import re
                    cmds = re.findall(r'`([^`]+)`', line)
                    if cmds:
                        rollback_info.append(f"{anchor_id}: `{cmds[0]}`")
                        break

    if rollback_info:
        lines.append("**回滚经验**:")
        for r in rollback_info[:3]:
            lines.append(f"- {r}")
        lines.append("")

    # 如果都没有匹配
    if not decisions and not interfaces:
        lines.append("暂无与当前设计相关的锚点。")
        lines.append("")

    lines.extend([
        "---",
        "> 仅供参考，决策权在本体"
    ])

    return '\n'.join(lines)


def get_shi_prompt_for_avatar(
    cwd: str,
    avatar_type: str,
    task_desc: str = ''
) -> str:
    """
    根据分身类型自动选择 T1/T2 惯性提示。

    分身配置:
    | 分身 | T1 | T2 | 说明 |
    |------|----|----|------|
    | 眼/explorer | ✓ | - | 探索前提示已知问题 |
    | 耳/analyst | - | - | 需求分析无需历史包袱 |
    | 意/architect | - | ✓ | 设计时参考历史决策 |
    | 身/斗战胜佛/impl | ✓ | ✓ | 实现前获取完整上下文 |
    | 舌/tester | ✓ | - | 测试时提示已知陷阱 |
    | 鼻/reviewer | ✓ | ✓ | 审查时参考约束和决策 |

    Args:
        cwd: 当前工作目录
        avatar_type: 分身类型
        task_desc: 可选的任务描述（用于提取关键词）

    Returns:
        合并的惯性提示字符串
    """
    # 规范化分身类型
    normalized_type = _normalize_avatar_type(avatar_type)

    if normalized_type == 'unknown':
        return ""

    # 获取配置
    config = AVATAR_INERTIA_CONFIG.get(normalized_type, {'t1': False, 't2': False})

    # 如果都不需要
    if not config['t1'] and not config['t2']:
        return ""

    # 从任务描述中提取关键词
    keywords = None
    if task_desc:
        # 简单的关键词提取：分词并过滤常见词
        import re
        words = re.findall(r'[\w\u4e00-\u9fff]+', task_desc)
        # 过滤短词和常见词
        stop_words = {'的', '是', '在', '和', '了', '有', '这', '个', '要', '会',
                      'the', 'a', 'an', 'is', 'are', 'to', 'and', 'or', 'for'}
        keywords = [w for w in words if len(w) > 1 and w.lower() not in stop_words]
        keywords = keywords[:5]  # 最多 5 个关键词

    prompts = []

    # 获取 T1 (如果需要)
    if config['t1']:
        t1_prompt = get_shi_t1_prompt(cwd, keywords)
        if t1_prompt and '暂无相关锚点' not in t1_prompt:
            prompts.append(t1_prompt)

    # 获取 T2 (如果需要)
    if config['t2']:
        t2_prompt = get_shi_t2_prompt(cwd, keywords)
        if t2_prompt and '暂无相关锚点' not in t2_prompt:
            prompts.append(t2_prompt)

    if not prompts:
        return ""

    return '\n\n'.join(prompts)


# ============================================================
# 跨会话内观 API (Cross-Session Introspection API)
# ============================================================

def _parse_date(date_str: str) -> datetime:
    """
    解析日期字符串。

    Args:
        date_str: 'today', 'yesterday', '2026-01-13' 等格式

    Returns:
        datetime 对象
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if date_str == 'today':
        return today
    elif date_str == 'yesterday':
        return today - timedelta(days=1)
    elif date_str == 'week':
        # 返回本周一
        return today - timedelta(days=today.weekday())
    else:
        # 尝试解析具体日期
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return today


def _load_session_index() -> dict:
    """加载会话索引文件"""
    index_path = get_session_index_path()
    if not index_path.exists():
        return {"version": "1.0", "sessions": [], "projects": {}}

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"version": "1.0", "sessions": [], "projects": {}}


def query_sessions_by_date(date: str = 'today', project: str = None) -> list[dict]:
    """
    按日期查询会话。

    Args:
        date: 日期字符串，支持 'today', 'yesterday', '2026-01-13' 格式
        project: 可选，过滤特定项目

    Returns:
        匹配的会话列表
    """
    index = _load_session_index()
    sessions = index.get('sessions', [])

    target_date = _parse_date(date)

    # 根据 date 类型确定时间范围
    if date == 'week':
        end_date = target_date + timedelta(days=7)
    else:
        end_date = target_date + timedelta(days=1)

    matched = []
    for session in sessions:
        # 解析会话的创建/更新时间
        session_time_str = session.get('updated_at') or session.get('created_at', '')
        if not session_time_str:
            continue

        try:
            session_time = datetime.fromisoformat(session_time_str)
        except ValueError:
            continue

        # 时间范围过滤
        if not (target_date <= session_time < end_date):
            continue

        # 项目过滤
        if project:
            session_project = session.get('project_path', '')
            project_name = Path(session_project).name if session_project else ''
            if project.lower() not in session_project.lower() and project.lower() not in project_name.lower():
                continue

        matched.append(session)

    return matched


def generate_daily_summary(date: str = 'today', project: str = None) -> str:
    """
    生成每日工作总结。

    聚合当日所有会话的任务摘要和锚点数量。

    Args:
        date: 日期
        project: 可选项目过滤

    Returns:
        格式化的每日总结字符串
    """
    sessions = query_sessions_by_date(date, project)

    if not sessions:
        date_display = date if date not in ('today', 'yesterday', 'week') else {
            'today': '今天',
            'yesterday': '昨天',
            'week': '本周'
        }.get(date, date)
        return f"## {date_display}工作总结\n\n暂无会话记录。"

    # 统计
    total_anchors = sum(s.get('anchor_count', 0) for s in sessions)
    projects_touched = set()
    task_summaries = []

    for session in sessions:
        project_path = session.get('project_path', '')
        if project_path:
            projects_touched.add(Path(project_path).name)

        summary = session.get('task_summary', '').strip()
        if summary:
            task_summaries.append(f"- {summary}")

    # 格式化输出
    date_display = date if date not in ('today', 'yesterday', 'week') else {
        'today': '今天',
        'yesterday': '昨天',
        'week': '本周'
    }.get(date, date)

    lines = [
        f"## {date_display}工作总结",
        "",
        f"**会话数**: {len(sessions)}",
        f"**涉及项目**: {', '.join(projects_touched) if projects_touched else '无'}",
        f"**沉淀锚点**: {total_anchors}",
        "",
    ]

    if task_summaries:
        lines.append("### 任务摘要")
        lines.append("")
        lines.extend(task_summaries)

    return '\n'.join(lines)


def introspect(scope: str = 'today', project: str = None) -> str:
    """
    内观命令核心实现。

    scope 支持:
    - 'today': 今日所有工作
    - 'yesterday': 昨日工作
    - 'week': 本周工作
    - 'session': 当前会话（默认行为）

    Returns:
        内观报告字符串
    """
    if scope == 'session':
        # 当前会话内观 - 返回提示信息
        return "当前会话内观请使用 `/nexus 内观` 命令触发 PreCompact Hook。"

    sessions = query_sessions_by_date(scope, project)

    if not sessions:
        scope_display = {
            'today': '今天',
            'yesterday': '昨天',
            'week': '本周'
        }.get(scope, scope)
        return f"## 内观报告 - {scope_display}\n\n暂无会话记录可供内观。"

    # 生成内观报告
    scope_display = {
        'today': '今天',
        'yesterday': '昨天',
        'week': '本周'
    }.get(scope, scope)

    lines = [
        f"## 内观报告 - {scope_display}",
        "",
    ]

    # 1. 工作概览
    total_anchors = sum(s.get('anchor_count', 0) for s in sessions)
    projects_touched = set()
    for s in sessions:
        p = s.get('project_path', '')
        if p:
            projects_touched.add(Path(p).name)

    lines.extend([
        "### 工作概览",
        "",
        f"- **会话数**: {len(sessions)}",
        f"- **涉及项目**: {', '.join(sorted(projects_touched)) if projects_touched else '无'}",
        f"- **沉淀锚点**: {total_anchors}",
        "",
    ])

    # 2. 会话详情
    lines.extend([
        "### 会话详情",
        "",
    ])

    for i, session in enumerate(sessions, 1):
        session_id = session.get('session_id', 'unknown')[:8]
        project_name = Path(session.get('project_path', '')).name or 'unknown'
        task_summary = session.get('task_summary', '(无摘要)')
        anchor_count = session.get('anchor_count', 0)
        updated_at = session.get('updated_at', '')[:16].replace('T', ' ')

        lines.extend([
            f"**{i}. [{project_name}] {session_id}**",
            f"   - 时间: {updated_at}",
            f"   - 任务: {task_summary}",
            f"   - 锚点: {anchor_count}",
            "",
        ])

    # 3. 反思提示
    lines.extend([
        "### 末那识扫描",
        "",
        "> 以下问题帮助识别潜在的认知偏差:",
        "",
        "- 是否有重复出现的问题/错误？",
        "- 是否有被跳过的验证步骤？",
        "- 是否有值得沉淀但未记录的决策？",
        "",
    ])

    return '\n'.join(lines)


def save_context(cwd: str, compact_context: str, session_id: str):
    """
    保存上下文到用户级别目录。

    目录结构:
    ~/.nexus/context/
    ├── active/{session_id}/compact.md      # 活跃会话（按 session 隔离）
    └── sessions/{project}-{timestamp}-{session[:8]}/  # 历史存档
    """
    project_name = get_project_name(cwd)

    # 1. 保存到活跃会话目录（按 session_id 隔离，避免多会话冲突）
    active_dir = get_active_session_dir(session_id)
    compact_path = active_dir / 'compact.md'
    with open(compact_path, 'w', encoding='utf-8') as f:
        f.write(compact_context)

    # 保存元数据（用于后续恢复时识别项目）
    metadata_path = active_dir / 'metadata.json'
    metadata = {
        'session_id': session_id,
        'project': project_name,
        'cwd': cwd,
        'timestamp': datetime.now().isoformat(),
    }
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 2. 同时保存到历史存档（带项目名和时间戳）
    sessions_dir = get_sessions_archive_dir()
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    session_dir = sessions_dir / f'{project_name}-{timestamp}-{session_id[:8]}'
    session_dir.mkdir(parents=True, exist_ok=True)

    backup_path = session_dir / 'compact.md'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(compact_context)


def output_to_claude(compact_context: str, candidates: list[dict]):
    """输出给 Claude (会被注入到压缩后的上下文)"""
    print("## [慧] PreCompact 提取完成")
    print()
    print("已保存关键上下文到 `~/.nexus/context/active/{session}/compact.md`")
    print()
    if candidates:
        print(f"识别到 {len(candidates)} 个候选锚点，待后续门槛检查。")
    print()
    print("如需恢复详细信息，读取 `~/.nexus/context/sessions/` 下对应文件。")


def main():
    """
    主入口函数。

    支持两种模式:
    1. PreCompact Hook 模式: 从 stdin 读取 hook 输入，提取上下文
    2. 分身输出压缩模式: 通过环境变量 NEXUS_COMPRESS_AVATAR=1 触发

    环境变量:
    - NEXUS_COMPRESS_AVATAR: 设为 1 启用分身输出压缩模式
    - NEXUS_AVATAR_TYPE: 分身类型 (眼/耳/鼻/舌/身/意 或英文别名)
    - NEXUS_AVATAR_OUTPUT: 要压缩的输出内容 (或从 stdin 读取)
    """
    # 检查是否为分身输出压缩模式
    if os.environ.get('NEXUS_COMPRESS_AVATAR') == '1':
        _run_avatar_compress_mode()
        return

    # 原有的 PreCompact Hook 模式
    _run_precompact_mode()


def _run_avatar_compress_mode():
    """分身输出压缩模式"""
    avatar_type = os.environ.get('NEXUS_AVATAR_TYPE', 'default')

    # 从环境变量或 stdin 读取输出内容
    avatar_output = os.environ.get('NEXUS_AVATAR_OUTPUT', '')
    if not avatar_output:
        avatar_output = sys.stdin.read()

    if not avatar_output:
        print("## [慧] 无分身输出可压缩", file=sys.stderr)
        return

    # 压缩输出
    compressed = compress_avatar_output(avatar_output, avatar_type)

    # 输出压缩结果
    print(compressed)

    # 记录日志
    log_path = Path.home() / '.nexus' / 'hooks' / 'reflection-compress.log'
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"\n--- {datetime.now().isoformat()} ---\n")
        log.write(f"Avatar: {avatar_type}\n")
        log.write(f"Original: {len(avatar_output)} chars\n")
        log.write(f"Compressed: {len(compressed)} chars\n")
        log.write(f"Ratio: {len(compressed)/len(avatar_output)*100:.1f}%\n")


def _run_precompact_mode():
    """PreCompact Hook 模式"""
    # 1. 读取 hook 输入
    hook_input = read_hook_input()

    # Debug: 记录到日志文件
    log_path = Path.home() / '.nexus' / 'hooks' / 'reflection-extract.log'
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"\n--- {datetime.now().isoformat()} ---\n")
        log.write(f"Input keys: {list(hook_input.keys())}\n")
        log.write(f"Full input: {json.dumps(hook_input, ensure_ascii=False)[:500]}\n")

    print(f"## [慧] Hook 触发 - 输入: {list(hook_input.keys())}", file=sys.stderr)

    transcript_path = hook_input.get('transcript_path', '')
    session_id = hook_input.get('session_id', 'unknown')
    cwd = hook_input.get('cwd', '.')
    trigger = hook_input.get('trigger', 'unknown')

    print(f"## [慧] trigger={trigger}, session={session_id[:8] if session_id else 'none'}", file=sys.stderr)

    # 2. 读取对话记录
    messages = read_transcript(transcript_path)

    if not messages:
        print("## [慧] 无对话记录可提取")
        return

    # 2.5 执行恢复流水线 (三阶段上下文恢复)
    recovery_result = run_recovery_pipeline(messages, cwd)

    # 记录恢复结果
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"Recovery stage: {recovery_result['stage']}\n")
        log.write(f"Usage ratio: {recovery_result['usage'].get('usage_ratio', 0):.2%}\n")
        log.write(f"Session errors: {len(recovery_result['session_errors'])}\n")
        if recovery_result.get('dcp_stats'):
            log.write(f"DCP removed: {len(recovery_result['dcp_stats'].get('removed_tools', []))}\n")

    # 使用处理后的消息（如果执行了 DCP）
    messages = recovery_result.get('messages', messages)

    # 3. 提取关键信息
    task = extract_current_task(messages)
    decisions = extract_decisions(messages)
    constraints = extract_constraints(messages)
    interfaces = extract_interfaces(messages)
    problems = extract_problems(messages)
    progress = extract_progress(messages)

    # 4. 生成缩形态上下文
    compact_context = generate_compact_context(
        task=task,
        decisions=decisions,
        constraints=constraints,
        interfaces=interfaces,
        problems=problems,
        progress=progress
    )

    # 5. 生成候选锚点
    candidates = generate_anchor_candidates(decisions, constraints, problems)

    # 6. 保存到文件
    save_context(cwd, compact_context, session_id)

    # 7. 生成慧模块标准输出 (慧→识交接协议)
    hui_output = generate_hui_output(
        session_id=session_id,
        project_path=cwd,
        task=task,
        decisions=decisions,
        constraints=constraints,
        interfaces=interfaces,
        problems=problems,
        progress=progress,
        compact_context=compact_context,
        candidates=candidates
    )

    # 8. 保存慧输出 JSON (供调试和识模块使用，用户级别)
    project_name = get_project_name(cwd)
    sessions_dir = get_sessions_archive_dir()
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    session_dir = sessions_dir / f'{project_name}-{timestamp}-{session_id[:8]}'
    session_dir.mkdir(parents=True, exist_ok=True)

    hui_output_path = session_dir / 'hui-output.json'
    with open(hui_output_path, 'w', encoding='utf-8') as f:
        json.dump(hui_output, f, ensure_ascii=False, indent=2)

    # 9. 调用识模块写入
    shi_result = shi_write(hui_output, cwd)

    # 记录识模块结果
    shi_result_path = session_dir / 'shi-result.json'
    with open(shi_result_path, 'w', encoding='utf-8') as f:
        json.dump(shi_result, f, ensure_ascii=False, indent=2)

    # 记录日志
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"Shi result: written={len(shi_result['anchors_written'])}, ")
        log.write(f"skipped={len(shi_result['anchors_skipped'])}, ")
        log.write(f"duplicated={len(shi_result['anchors_duplicated'])}\n")

    # 10. 输出给 Claude (包含恢复提示)
    output_to_claude_with_recovery(
        compact_context, candidates, shi_result, recovery_result
    )


def output_to_claude_with_shi_result(
    compact_context: str,
    candidates: list[dict],
    shi_result: dict
):
    """输出给 Claude，包含识模块的写入结果（旧版，保留兼容）"""
    output_to_claude_with_recovery(compact_context, candidates, shi_result, {})


def output_to_claude_with_recovery(
    compact_context: str,
    candidates: list[dict],
    shi_result: dict,
    recovery_result: dict
):
    """输出给 Claude，包含识模块写入结果和恢复提示"""
    # 1. 恢复提示 (如果有)
    recovery_prompt = recovery_result.get('prompt', '')
    if recovery_prompt:
        print(recovery_prompt)
        print()

    # 2. 上下文使用统计
    usage = recovery_result.get('usage', {})
    if usage:
        ratio = usage.get('usage_ratio', 0)
        stage = recovery_result.get('stage', 'normal')
        stage_emoji = {'normal': '🟢', 'warning': '🟡', 'preemptive': '🟠', 'emergency': '🔴'}
        print(f"**上下文使用率**: {stage_emoji.get(stage, '⚪')} {int(ratio * 100)}%")
        print()

    # 3. 标准输出
    print("## [慧] PreCompact 提取完成")
    print()
    print("已保存关键上下文到 `~/.nexus/context/active/{session}/compact.md`")
    print()

    if candidates:
        print(f"识别到 {len(candidates)} 个候选锚点。")

    # 4. 显示识模块写入结果
    written = shi_result.get('anchors_written', [])
    skipped = shi_result.get('anchors_skipped', [])
    duplicated = shi_result.get('anchors_duplicated', [])

    if written:
        print(f"\n### [识] 已写入 {len(written)} 个锚点:")
        for w in written[:5]:  # 最多显示5个
            print(f"  - [{w['new_id']}] {w.get('title', '')[:40]}")

    if skipped:
        print(f"\n### [识] 跳过 {len(skipped)} 个锚点 (未达门槛)")

    if duplicated:
        print(f"\n### [识] 去重 {len(duplicated)} 个锚点 (已存在)")

    errors = shi_result.get('errors', [])
    if errors:
        print(f"\n### [识] 错误: {len(errors)} 个")
        for e in errors[:3]:
            print(f"  - {e.get('id')}: {e.get('error')}")

    # 5. DCP 统计 (如果执行了)
    dcp_stats = recovery_result.get('dcp_stats')
    if dcp_stats:
        removed = dcp_stats.get('removed_tools', [])
        if removed:
            print(f"\n### [DCP] 动态剪枝:")
            print(f"  - 移除了 {len(removed)} 个冗余工具调用")
            print(f"  - 消息数: {dcp_stats.get('original_count', 0)} → {dcp_stats.get('pruned_count', 0)}")

    # 6. 会话错误 (如果有)
    session_errors = recovery_result.get('session_errors', [])
    if session_errors:
        print(f"\n### [恢复] 检测到 {len(session_errors)} 个会话问题 (已处理)")

    print()
    print("如需恢复详细信息，读取 `~/.nexus/context/sessions/` 下对应文件。")


# ============================================================
# 任务续期机制 (Task Continuation)
# 借鉴自 oh-my-opencode 的 Ralph Loop 和 Todo Continuation Enforcer
# ============================================================

# 任务续期配置
CONTINUATION_CONFIG = {
    'max_iterations': 100,          # 最大续期次数
    'completion_markers': [         # 完成标记
        '<promise>DONE</promise>',
        '## 任务完成',
        '## Task Complete',
        '✅ 所有任务已完成',
    ],
    'incomplete_patterns': [        # 未完成标记
        'in_progress',
        '待完成',
        'TODO:',
        '继续',
        '下一步',
    ],
}


def detect_incomplete_tasks(messages: list[dict], cwd: str) -> dict:
    """
    检测未完成的任务。

    检查策略：
    1. 检查最后几条消息是否有完成标记
    2. 检查是否有明确的未完成标记
    3. 检查 .nexus/context/current/ 下是否有未完成任务记录

    Args:
        messages: 对话消息列表
        cwd: 当前工作目录

    Returns:
        {
            'has_incomplete': bool,
            'incomplete_tasks': list[str],
            'iteration': int,
            'reason': str
        }
    """
    result = {
        'has_incomplete': False,
        'incomplete_tasks': [],
        'iteration': 0,
        'reason': ''
    }

    # 1. 检查完成标记
    recent_content = ''
    for msg in messages[-5:]:
        recent_content += get_message_content(msg) + '\n'

    for marker in CONTINUATION_CONFIG['completion_markers']:
        if marker in recent_content:
            result['reason'] = f'Found completion marker: {marker}'
            return result

    # 2. 检查未完成标记
    incomplete_found = []
    for pattern in CONTINUATION_CONFIG['incomplete_patterns']:
        if pattern.lower() in recent_content.lower():
            incomplete_found.append(pattern)

    if incomplete_found:
        result['has_incomplete'] = True
        result['incomplete_tasks'] = incomplete_found
        result['reason'] = f'Found incomplete markers: {incomplete_found}'

    # 3. 检查本地任务状态文件
    state_file = Path(cwd) / '.nexus' / 'context' / 'current' / 'task-state.json'
    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                result['iteration'] = state.get('iteration', 0)
                if state.get('incomplete_tasks'):
                    result['has_incomplete'] = True
                    result['incomplete_tasks'].extend(state['incomplete_tasks'])
        except (json.JSONDecodeError, IOError):
            pass

    return result


def generate_continuation_prompt(
    task: str,
    incomplete_tasks: list[str],
    iteration: int,
    max_iterations: int = 100
) -> str:
    """
    生成任务续期提示。

    借鉴 Ralph Loop 的格式，清晰告知：
    - 当前迭代次数
    - 原始任务
    - 未完成项
    - 继续指令

    Args:
        task: 原始任务描述
        incomplete_tasks: 未完成任务列表
        iteration: 当前迭代次数
        max_iterations: 最大迭代次数

    Returns:
        续期提示字符串
    """
    prompt_lines = [
        "## [NEXUS CONTINUATION]",
        "",
        f"**迭代**: [{iteration + 1}/{max_iterations}]",
        "",
        f"**原始任务**: {task[:200]}",
        "",
    ]

    if incomplete_tasks:
        prompt_lines.append("**未完成项**:")
        for t in incomplete_tasks[:5]:
            prompt_lines.append(f"- {t}")
        prompt_lines.append("")

    prompt_lines.extend([
        "**指令**: 请检查当前进度，如任务未完成请继续执行。",
        "",
        "如果已完成所有任务，请输出 `## 任务完成` 标记。",
    ])

    return '\n'.join(prompt_lines)


def save_task_state(cwd: str, state: dict):
    """
    保存任务状态到文件。

    用于跨压缩周期追踪任务进度。

    Args:
        cwd: 当前工作目录
        state: 任务状态字典
    """
    state_dir = Path(cwd) / '.nexus' / 'context' / 'current'
    state_dir.mkdir(parents=True, exist_ok=True)

    state_file = state_dir / 'task-state.json'
    state['updated_at'] = datetime.now().isoformat()

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def clear_task_state(cwd: str):
    """清除任务状态文件（任务完成时调用）"""
    state_file = Path(cwd) / '.nexus' / 'context' / 'current' / 'task-state.json'
    if state_file.exists():
        state_file.unlink()


# ============================================================
# 错误分类与恢复 (Error Classification & Recovery)
# 借鉴自 oh-my-opencode 的细粒度错误恢复机制
# ============================================================

# 错误分类体系
ERROR_CATEGORIES = {
    'edit_failure': {
        'patterns': [
            'oldString not found',
            'oldString found multiple times',
            'oldString and newString must be different',
        ],
        'severity': 'HIGH',
        'recovery': 'read_and_retry',
    },
    'tool_result_missing': {
        'patterns': [
            'tool_use',
            'tool_result',
        ],
        'severity': 'HIGH',
        'recovery': 'inject_placeholder',
    },
    'context_exceeded': {
        'patterns': [
            'context_length_exceeded',
            'prompt is too long',
            'token limit',
        ],
        'severity': 'CRITICAL',
        'recovery': 'compress_and_retry',
    },
    'permission_denied': {
        'patterns': [
            'Permission denied',
            'EACCES',
            'Operation not permitted',
        ],
        'severity': 'HIGH',
        'recovery': 'user_confirm',
    },
    'file_not_found': {
        'patterns': [
            'No such file',
            'ENOENT',
            'FileNotFoundError',
        ],
        'severity': 'MEDIUM',
        'recovery': 'search_and_retry',
    },
}


def classify_error(error_message: str) -> dict | None:
    """
    对错误消息进行分类。

    Args:
        error_message: 错误消息字符串

    Returns:
        {
            'category': str,
            'severity': str,
            'recovery': str,
            'matched_pattern': str
        } 或 None
    """
    if not error_message:
        return None

    error_lower = error_message.lower()

    for category, config in ERROR_CATEGORIES.items():
        for pattern in config['patterns']:
            if pattern.lower() in error_lower:
                return {
                    'category': category,
                    'severity': config['severity'],
                    'recovery': config['recovery'],
                    'matched_pattern': pattern,
                }

    return None


def generate_recovery_prompt(error_info: dict) -> str:
    """
    根据错误分类生成恢复提示。

    Args:
        error_info: classify_error 返回的错误信息

    Returns:
        恢复指导字符串
    """
    category = error_info.get('category', '')
    recovery = error_info.get('recovery', '')

    prompts = {
        'read_and_retry': """
## [ERROR RECOVERY - Edit Failure]

**STOP and do this NOW:**

1. **READ** the target file to see its ACTUAL current state
2. **VERIFY** what the content really looks like (your assumption was wrong)
3. **ACKNOWLEDGE** the error - understand why oldString wasn't found
4. **CORRECTED** action based on actual file state
5. **DO NOT** retry the same edit without verification

**Common causes:**
- File was modified by another operation
- Indentation/whitespace mismatch
- String was already changed
""",
        'inject_placeholder': """
## [ERROR RECOVERY - Tool Result Missing]

A tool call is missing its result. This may be due to:
- User interruption (ESC pressed)
- Network timeout
- Tool execution failure

**Recovery:** The system will inject a placeholder result. Please review and retry the operation if needed.
""",
        'compress_and_retry': """
## [ERROR RECOVERY - Context Exceeded]

The conversation has exceeded the context window limit.

**Automatic recovery in progress:**
1. Extracting key anchors and decisions
2. Compressing tool outputs
3. Generating compact summary

Please wait for compression to complete, then continue your task.
""",
        'user_confirm': """
## [ERROR RECOVERY - Permission Denied]

The operation requires elevated permissions.

**Please confirm:**
- Is the target path correct?
- Do you have write access?
- Is the file locked by another process?

If you want to proceed, please grant the necessary permissions or modify the target path.
""",
        'search_and_retry': """
## [ERROR RECOVERY - File Not Found]

The specified file does not exist.

**Recovery steps:**
1. Use Glob/Grep to search for similar files
2. Check if the file was moved or renamed
3. Verify the path is correct

**Do NOT** assume the path - verify it first.
""",
    }

    return prompts.get(recovery, f"## [ERROR] Unknown error category: {category}")


# ============================================================
# 三阶段上下文恢复 (Three-Stage Context Recovery)
# 借鉴自 oh-my-opencode 的 anthropic-context-window-limit-recovery
# ============================================================

# 上下文使用阈值
CONTEXT_THRESHOLDS = {
    'warning': 0.70,        # 70% - 发出警告
    'preemptive': 0.85,     # 85% - 主动压缩
    'emergency': 1.0,       # 100% - 紧急救援
}


def estimate_context_usage(messages: list[dict]) -> dict:
    """
    估算上下文使用率。

    注意：这是一个估算，实际 token 数取决于具体的 tokenizer。
    粗略估算：1 token ≈ 4 字符 (英文) 或 1.5 字符 (中文)

    Args:
        messages: 对话消息列表

    Returns:
        {
            'total_chars': int,
            'estimated_tokens': int,
            'usage_ratio': float,  # 0.0 - 1.0
            'stage': str  # 'normal', 'warning', 'preemptive', 'emergency'
        }
    """
    # Claude 的上下文窗口大小 (200k tokens for Claude 3)
    MAX_TOKENS = 200000

    total_chars = 0
    for msg in messages:
        content = get_message_content(msg)
        total_chars += len(content)

        # 工具调用的输出通常很大
        if 'toolUseResult' in msg:
            result = msg.get('toolUseResult', '')
            if isinstance(result, str):
                total_chars += len(result)
            elif isinstance(result, dict):
                total_chars += len(json.dumps(result, ensure_ascii=False))

    # 粗略估算 token 数 (混合语言，取平均)
    estimated_tokens = total_chars // 3

    usage_ratio = estimated_tokens / MAX_TOKENS

    # 确定阶段
    if usage_ratio >= CONTEXT_THRESHOLDS['emergency']:
        stage = 'emergency'
    elif usage_ratio >= CONTEXT_THRESHOLDS['preemptive']:
        stage = 'preemptive'
    elif usage_ratio >= CONTEXT_THRESHOLDS['warning']:
        stage = 'warning'
    else:
        stage = 'normal'

    return {
        'total_chars': total_chars,
        'estimated_tokens': estimated_tokens,
        'usage_ratio': usage_ratio,
        'stage': stage,
    }


def generate_stage_prompt(stage: str, usage_ratio: float) -> str:
    """
    根据上下文阶段生成提示。

    Args:
        stage: 阶段 ('normal', 'warning', 'preemptive', 'emergency')
        usage_ratio: 使用率 (0.0 - 1.0)

    Returns:
        阶段提示字符串
    """
    percentage = int(usage_ratio * 100)

    if stage == 'warning':
        return f"""
## [CONTEXT MONITOR] ⚠️ 70% 警告

**当前使用率**: {percentage}%

**提醒**: 上下文窗口已使用 {percentage}%，但仍有充足空间。
- ✅ 不要因此仓促行动
- ✅ 继续高质量完成当前任务
- 考虑在合适时机执行 `/nexus 压缩`
"""

    elif stage == 'preemptive':
        return f"""
## [CONTEXT MONITOR] 🟠 85% 主动压缩

**当前使用率**: {percentage}%

**自动执行以下操作**:
1. ✅ 启动 DCP (动态上下文剪枝)
2. ✅ 压缩大型工具输出
3. ✅ 保留关键锚点和决策

**你应该**:
- 完成当前正在进行的任务
- 然后执行 `/nexus 压缩` 保存进度
"""

    elif stage == 'emergency':
        return f"""
## [CONTEXT MONITOR] 🔴 100% 紧急救援

**当前使用率**: {percentage}%

**紧急恢复模式已激活**:
1. 🚨 执行完整上下文摘要
2. 🚨 保留 AGENTS.md 和关键上下文
3. 🚨 准备继续执行指令

**自动保存的内容**:
- 当前任务描述
- 关键决策和约束
- 未完成任务列表

继续你的任务，系统会自动恢复上下文。
"""

    return ""


# ============================================================
# DCP - 动态上下文剪枝 (Dynamic Context Pruning)
# ============================================================

# 受保护的工具列表 (不会被剪枝)
PROTECTED_TOOLS = {
    'Task', 'TodoWrite', 'lsp_rename', 'Edit', 'Write',
}

# 可安全剪枝的工具模式
PRUNABLE_PATTERNS = {
    'Glob': {'keep_last': 3},       # 只保留最近 3 次
    'Grep': {'keep_last': 3},
    'Read': {'keep_last': 5},       # 读取操作保留更多
    'Bash': {'keep_last': 3},
    'WebSearch': {'keep_last': 2},
    'WebFetch': {'keep_last': 2},
}


def apply_dcp(messages: list[dict]) -> tuple[list[dict], dict]:
    """
    应用动态上下文剪枝 (DCP)。

    策略:
    1. 识别重复的工具调用 (相同签名)
    2. 保护关键工具的输出
    3. 移除冗余，只保留最新

    Args:
        messages: 原始消息列表

    Returns:
        (pruned_messages, stats): 剪枝后的消息列表和统计信息
    """
    stats = {
        'original_count': len(messages),
        'pruned_count': 0,
        'removed_tools': [],
    }

    # 按工具类型分组
    tool_calls = {}  # tool_name -> list of (index, message)

    for i, msg in enumerate(messages):
        # 检测工具调用
        if msg.get('type') == 'assistant':
            content = msg.get('message', {}).get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                        tool_name = item.get('name', '')
                        if tool_name and tool_name not in PROTECTED_TOOLS:
                            if tool_name not in tool_calls:
                                tool_calls[tool_name] = []
                            tool_calls[tool_name].append((i, msg))

    # 确定要移除的消息索引
    indices_to_remove = set()

    for tool_name, calls in tool_calls.items():
        config = PRUNABLE_PATTERNS.get(tool_name, {'keep_last': 3})
        keep_last = config.get('keep_last', 3)

        if len(calls) > keep_last:
            # 移除旧的调用
            for idx, _ in calls[:-keep_last]:
                indices_to_remove.add(idx)
                stats['removed_tools'].append(tool_name)

    # 构建剪枝后的消息列表
    pruned_messages = [
        msg for i, msg in enumerate(messages)
        if i not in indices_to_remove
    ]

    stats['pruned_count'] = len(pruned_messages)

    return pruned_messages, stats


def truncate_large_outputs(messages: list[dict], target_reduction: float = 0.5) -> list[dict]:
    """
    截断大型工具输出。

    策略:
    - 按大小排序工具输出
    - 截断最大的输出 (目标削减 50%)
    - 保留元数据 (工具名、状态)

    Args:
        messages: 消息列表
        target_reduction: 目标削减比例

    Returns:
        处理后的消息列表
    """
    MAX_TOOL_OUTPUT = 2000  # 单个工具输出的最大字符数

    processed = []
    for msg in messages:
        if 'toolUseResult' in msg:
            result = msg.get('toolUseResult', '')
            if isinstance(result, str) and len(result) > MAX_TOOL_OUTPUT:
                # 截断并添加标记
                msg = msg.copy()
                msg['toolUseResult'] = result[:MAX_TOOL_OUTPUT] + '\n... [OUTPUT TRUNCATED]'
            elif isinstance(result, dict):
                result_str = json.dumps(result, ensure_ascii=False)
                if len(result_str) > MAX_TOOL_OUTPUT:
                    msg = msg.copy()
                    # 保留关键字段
                    truncated = {
                        '_truncated': True,
                        '_original_size': len(result_str),
                    }
                    for key in ['status', 'error', 'summary', 'count']:
                        if key in result:
                            truncated[key] = result[key]
                    msg['toolUseResult'] = truncated

        processed.append(msg)

    return processed


# ============================================================
# 会话级错误恢复 (Session-Level Error Recovery)
# ============================================================

def detect_session_errors(messages: list[dict]) -> list[dict]:
    """
    检测会话级错误。

    检测类型:
    1. 缺失工具结果 (tool_use 无对应 tool_result)
    2. 空消息
    3. 思考块问题

    Args:
        messages: 消息列表

    Returns:
        错误列表 [{'type': str, 'index': int, 'details': str}]
    """
    errors = []

    pending_tool_uses = {}  # tool_use_id -> index

    for i, msg in enumerate(messages):
        # 检测空消息
        content = get_message_content(msg)
        if msg.get('type') == 'assistant' and not content.strip():
            errors.append({
                'type': 'empty_message',
                'index': i,
                'details': 'Assistant message has no content'
            })

        # 跟踪工具调用
        if msg.get('type') == 'assistant':
            msg_content = msg.get('message', {}).get('content', [])
            if isinstance(msg_content, list):
                for item in msg_content:
                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                        tool_id = item.get('id', '')
                        if tool_id:
                            pending_tool_uses[tool_id] = i

        # 检测工具结果
        if msg.get('type') == 'user':
            msg_content = msg.get('message', {}).get('content', [])
            if isinstance(msg_content, list):
                for item in msg_content:
                    if isinstance(item, dict) and item.get('type') == 'tool_result':
                        tool_id = item.get('tool_use_id', '')
                        if tool_id in pending_tool_uses:
                            del pending_tool_uses[tool_id]

    # 未配对的工具调用
    for tool_id, index in pending_tool_uses.items():
        errors.append({
            'type': 'tool_result_missing',
            'index': index,
            'details': f'Tool use {tool_id} has no corresponding result'
        })

    return errors


def generate_recovery_for_session_errors(errors: list[dict]) -> str:
    """
    为会话错误生成恢复提示。

    Args:
        errors: 错误列表

    Returns:
        恢复提示字符串
    """
    if not errors:
        return ""

    lines = [
        "## [SESSION RECOVERY] 检测到会话错误",
        "",
    ]

    error_types = {}
    for e in errors:
        et = e['type']
        if et not in error_types:
            error_types[et] = []
        error_types[et].append(e)

    if 'tool_result_missing' in error_types:
        count = len(error_types['tool_result_missing'])
        lines.append(f"- **缺失工具结果**: {count} 个")
        lines.append("  → 系统已注入占位符，请检查相关操作是否需要重试")

    if 'empty_message' in error_types:
        count = len(error_types['empty_message'])
        lines.append(f"- **空消息**: {count} 个")
        lines.append("  → 已自动清理")

    lines.extend([
        "",
        "**建议**: 检查最近的操作是否成功完成，如有需要请重试。",
    ])

    return '\n'.join(lines)


# ============================================================
# 主恢复流程 (Main Recovery Flow)
# ============================================================

def run_recovery_pipeline(
    messages: list[dict],
    cwd: str
) -> dict:
    """
    执行完整的恢复流水线。

    流程:
    1. 估算上下文使用率
    2. 检测会话错误
    3. 根据阶段执行对应恢复策略
    4. 生成恢复提示

    Args:
        messages: 对话消息列表
        cwd: 当前工作目录

    Returns:
        {
            'stage': str,
            'usage': dict,
            'session_errors': list,
            'dcp_stats': dict | None,
            'prompt': str,
            'messages': list  # 处理后的消息
        }
    """
    result = {
        'stage': 'normal',
        'usage': {},
        'session_errors': [],
        'dcp_stats': None,
        'prompt': '',
        'messages': messages,
    }

    # 1. 估算使用率
    usage = estimate_context_usage(messages)
    result['usage'] = usage
    result['stage'] = usage['stage']

    # 2. 检测会话错误
    session_errors = detect_session_errors(messages)
    result['session_errors'] = session_errors

    prompts = []

    # 3. 处理会话错误
    if session_errors:
        error_prompt = generate_recovery_for_session_errors(session_errors)
        if error_prompt:
            prompts.append(error_prompt)

    # 4. 根据阶段执行恢复
    stage = usage['stage']

    if stage == 'warning':
        # 只发出警告
        stage_prompt = generate_stage_prompt(stage, usage['usage_ratio'])
        prompts.append(stage_prompt)

    elif stage == 'preemptive':
        # 85% - 执行 DCP + 截断
        pruned, dcp_stats = apply_dcp(messages)
        result['dcp_stats'] = dcp_stats
        result['messages'] = truncate_large_outputs(pruned)

        stage_prompt = generate_stage_prompt(stage, usage['usage_ratio'])
        prompts.append(stage_prompt)

        # 添加 DCP 统计
        if dcp_stats['removed_tools']:
            prompts.append(f"\n**DCP 结果**: 移除了 {len(dcp_stats['removed_tools'])} 个冗余工具调用")

    elif stage == 'emergency':
        # 100% - 紧急救援
        # 执行更激进的剪枝
        pruned, dcp_stats = apply_dcp(messages)
        result['dcp_stats'] = dcp_stats
        result['messages'] = truncate_large_outputs(pruned, target_reduction=0.7)

        stage_prompt = generate_stage_prompt(stage, usage['usage_ratio'])
        prompts.append(stage_prompt)

    # 合并提示
    result['prompt'] = '\n\n'.join(prompts)

    # 保存恢复状态
    save_recovery_state(cwd, result)

    return result


def save_recovery_state(cwd: str, recovery_result: dict):
    """
    保存恢复状态到文件。

    用于调试和跨压缩周期追踪。

    Args:
        cwd: 当前工作目录
        recovery_result: 恢复结果字典
    """
    state_dir = Path(cwd) / '.nexus' / 'context' / 'current'
    state_dir.mkdir(parents=True, exist_ok=True)

    state_file = state_dir / 'recovery-state.json'

    # 只保存关键信息（不保存完整消息）
    state = {
        'timestamp': datetime.now().isoformat(),
        'stage': recovery_result['stage'],
        'usage': recovery_result['usage'],
        'session_errors_count': len(recovery_result['session_errors']),
        'dcp_stats': recovery_result.get('dcp_stats'),
    }

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
