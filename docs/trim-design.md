# Nexus 深度裁剪设计

> 设计版本: 1.0
> 设计者: 意分身 (Architect)
> 日期: 2026-02-03

## Summary

将 Nexus 从 7 分身复杂系统裁剪为 3 分身极简系统 (body/eye/mind)，删除 80%+ 的协议文件，最终只保留：分身定义 + 极简本体约束 (protocol.md)。

---

## 裁剪目标

- 从 **7 分身** -> **3 分身** (body, eye, mind)
- 从 **复杂多层协议** -> **极简本体约束**
- 从 **~25 个文件** -> **~8 个文件**
- 核心原则: **非必要不加**

---

## 删除清单

### nexus-dist/agents/ (删除全部 7 个)

| 文件 | 理由 |
|------|------|
| `explorer.md` | 用中文版 eye.md 替代 |
| `analyst.md` | 删除，功能合并到 eye |
| `reviewer.md` | 删除，功能合并到 eye |
| `tester.md` | 删除，功能合并到 body |
| `implementer.md` | 用中文版 body.md 替代 |
| `architect.md` | 用中文版 mind.md 替代 |
| `planner.md` | 删除，L1 路由不再需要 |

### nexus-dist/protocol/ (删除)

| 文件 | 理由 |
|------|------|
| `agent-protocol.md` | 737 行，过度复杂；精简后合并到 protocol.md |

### nexus-dist/parallel/ (删除)

| 文件 | 理由 |
|------|------|
| `parallel-protocol.md` | 511 行，3 分身场景下不需要复杂并行协议 |

### nexus-dist/reflection/ (删除)

| 文件 | 理由 |
|------|------|
| `reflection.md` | 610 行，反思系统增加复杂度，非核心功能 |

### nexus-dist/commands/ (删除 2/3)

| 文件 | 理由 |
|------|------|
| `plan.md` | 220 行，L0/L1 路由系统删除 |
| `reflection.md` | 262 行，反思命令删除 |
| ~~`nexus.md`~~ | **保留但大幅精简** |

### nexus-dist/context/ (删除全部)

| 文件/目录 | 理由 |
|-----------|------|
| `aggregator.py` | Python 上下文管理，过度工程 |
| `cleanup.py` | 同上 |
| `importance.py` | 同上 |
| `snapshot.py` | 同上 |
| `cli.py` | 同上 |
| `example_usage.py` | 同上 |
| `__init__.py` | 同上 |

### nexus-dist/hooks/ (删除全部)

| 文件 | 理由 |
|------|------|
| `reflection-extract.py` | 反思系统的 hook |
| `on_stop.py` | 过度工程 |
| `on_subagent_stop.py` | 过度工程 |

### runtime/ (删除大部分)

| 文件 | 理由 |
|------|------|
| `scheduler.py` | 复杂调度器，3 分身不需要 |
| `cli.py` | L0/L1 路由 CLI |
| `anchor_manager.py` | 反思系统相关 |
| `artifact_manager.py` | 过度工程 |
| `event_bus.py` | 过度工程 |
| `health_monitor.py` | 过度工程 |
| `metrics.py` | 过度工程 |
| `state_manager.py` | 过度工程 |
| `visualizer.py` | 过度工程 |
| ~~`selfcheck.py`~~ | **保留但精简** |

### 根目录文件

| 文件 | 操作 |
|------|------|
| `AGENTS.md` | **大幅精简** (从 143 行 -> ~50 行) |

---

## 保留清单

| 文件 | 修改内容 |
|------|----------|
| `nexus-dist/rules/00-nexus-core.md` | **重写为极简 protocol.md** (~60 行) |
| `nexus-dist/commands/nexus.md` | **大幅精简** (从 242 行 -> ~40 行) |
| `nexus-dist/agents/body.md` | **新建** (复制自 ~/.claude/agents/body.md) |
| `nexus-dist/agents/eye.md` | **新建** (复制自 ~/.claude/agents/eye.md) |
| `nexus-dist/agents/mind.md` | **新建** (复制自 ~/.claude/agents/mind.md) |
| `runtime/selfcheck.py` | **精简** |
| `AGENTS.md` | **重写** |
| `CLAUDE.md` | **精简** |
| `README.md` | **精简** |
| `install.sh` | **精简** |

---

## 新协议设计

### protocol.md (极简本体约束)

```markdown
# Nexus Protocol (极简版)

> 三分身: body (实现) | eye (探索) | mind (设计)

## 本体铁律

你是**调度者**，不是执行者。

| 操作 | 阈值 | 正确做法 |
|------|------|----------|
| 探索代码库 | 多文件 | @eye |
| 写/改代码 | >10 行 | @body |
| 架构设计 | 任何 | @mind |

## 允许操作

1. **调度** - 召唤分身
2. **验证** - 检查输出
3. **对话** - 与用户沟通

## 召唤分身

```python
# 探索 (后台)
Task(subagent_type="eye", prompt="...", run_in_background=True,
     allowed_tools=["Read", "Glob", "Grep"])

# 实现 (前台)
Task(subagent_type="body", prompt="...",
     allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"])

# 设计 (前台)
Task(subagent_type="mind", prompt="...",
     allowed_tools=["Read", "Write", "Glob", "Grep"])
```

## 验证

> 分身可能说谎 - 必须亲自验证

```
[ ] 文件存在 (Glob/Read)
[ ] 构建通过
[ ] 测试通过
```

**Iron Law**: 没有证据 = 没有完成
```

**设计决策**:
- 从 102 行 -> 约 45 行 (减少 56%)
- 删除: L0/L1 路由、复杂成本配置、扩展技能引用
- 保留: 本体铁律、三个分身召唤、验证规则

---

### AGENTS.md (精简版)

```markdown
# Nexus Multi-Agent System

**3 Specialists** - Minimal but Complete

## Agents

| Agent | Alias | Cost | Background | Purpose |
|-------|-------|------|------------|---------|
| `eye` | @eye, @explorer | CHEAP | Required | Explore, search |
| `body` | @body, @impl | EXPENSIVE | Forbidden | Implement, fix |
| `mind` | @mind, @architect | EXPENSIVE | Forbidden | Design, decide |

## Invocation

```python
Task(subagent_type="eye", prompt="...", run_in_background=True)
Task(subagent_type="body", prompt="...")
Task(subagent_type="mind", prompt="...")
```

## Agent Boundaries

| Agent | CAN DO | CANNOT DO |
|-------|--------|-----------|
| `eye` | Read, Glob, Grep | Write, Edit, Bash, Task |
| `body` | Read, Write, Edit, Bash, Glob, Grep | Task |
| `mind` | Read, Write (.md), Glob, Grep | Edit, Bash, Task |

## Agent Files

```
~/.claude/agents/
├── eye.md
├── body.md
└── mind.md
```
```

---

### nexus.md (命令精简版)

```markdown
# Nexus Command

Activate Nexus multi-agent workflow.

## Usage

```
/nexus              # Activate
/nexus @eye ...     # Direct invoke eye
/nexus @body ...    # Direct invoke body
/nexus @mind ...    # Direct invoke mind
/nexus selfcheck    # Environment check
```

## Workflow

1. Receive task
2. CHECKPOINT: Decide delegation
3. Invoke specialist(s)
4. Verify results
5. Report to user

## @ Syntax

| Tag | Agent | Example |
|-----|-------|---------|
| @eye | Explorer | `/nexus @eye explore auth module` |
| @body | Implementer | `/nexus @body fix login bug` |
| @mind | Architect | `/nexus @mind design cache layer` |
```

---

## 裁剪后结构

```
nexus/
├── AGENTS.md              # 精简版 Agent 注册表 (~50 行)
├── CLAUDE.md              # 精简版开发指南
├── README.md              # 精简版用户文档
├── install.sh             # 精简版安装脚本
├── nexus-dist/
│   ├── rules/
│   │   └── 00-nexus-core.md   # 极简 protocol (~45 行)
│   ├── agents/
│   │   ├── body.md            # 身分身定义
│   │   ├── eye.md             # 眼分身定义
│   │   └── mind.md            # 意分身定义
│   └── commands/
│       └── nexus.md           # 精简版命令 (~40 行)
├── runtime/
│   └── selfcheck.py           # 精简版自检
└── tests/
    └── test_*.py              # 保留测试
```

**文件数量**: 从 ~25 个 -> ~10 个 (减少 60%)
**代码行数**: 从 ~3000 行 -> ~500 行 (减少 83%)

---

## Decisions

### Decision 1: 删除 L0/L1 路由系统

- **决策**: 删除 plan.md 和相关的 cli.py, planner.md
- **理由**:
  - 3 分身场景下，路由选择变得简单
  - 本体 CHECKPOINT 已足够判断应该召唤哪个分身
  - 减少 ~500 行代码
- **备选方案**: 保留简化版路由
- **风险**: 无，3 分身选择直观

### Decision 2: 删除反思系统

- **决策**: 删除 reflection.md, reflection-extract.py 及相关 hooks
- **理由**:
  - 反思系统增加显著复杂度 (~870 行)
  - 非核心功能，用户可手动反思
  - 与"极简"原则冲突
- **备选方案**: 保留简化版反思
- **风险**: 丢失自动化知识提取能力

### Decision 3: 删除并行协议

- **决策**: 删除 parallel-protocol.md
- **理由**:
  - 3 分身场景下，并行场景有限
  - eye 后台 + body/mind 前台已覆盖主要场景
  - 减少 ~511 行代码
- **备选方案**: 保留核心并行规则
- **风险**: 丢失复杂并行模式支持

### Decision 4: 删除 Python 上下文管理

- **决策**: 删除 nexus-dist/context/ 全部 Python 文件
- **理由**:
  - 过度工程，增加维护成本
  - Claude 自身已有上下文管理能力
  - 与"极简"原则冲突
- **备选方案**: 保留简化版
- **风险**: 丢失自动化上下文快照

### Decision 5: 使用中文版分身定义

- **决策**: 从 ~/.claude/agents/ 复制 body.md, eye.md, mind.md
- **理由**:
  - 用户已有成熟的中文版定义
  - 保持一致性
  - 避免重复工作
- **备选方案**: 创建新的英文版
- **风险**: 无

---

## Tradeoffs

1. **功能 vs 简单性**: 选择简单性。删除反思、复杂路由、并行协议，换取代码量减少 83%。

2. **自动化 vs 可控性**: 选择可控性。删除自动化 hooks 和上下文管理，让用户手动控制。

3. **灵活性 vs 一致性**: 选择一致性。固定 3 分身，不支持动态添加分身。

---

## Constraints

- **技术约束**: 必须兼容 Claude Code 的 Task tool
- **用户约束**: 保留现有 body/eye/mind 分身定义格式
- **安装约束**: install.sh 必须继续工作

---

## Risks

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 删除过多导致功能缺失 | 中 | 中 | 分阶段裁剪，每步验证 |
| 破坏现有用户配置 | 低 | 高 | 备份 ~/.claude/ 后再安装 |
| 分身定义格式不兼容 | 低 | 中 | 测试 Task tool 调用 |

---

## Evidence

- Sources:
  - `/Users/DennisWang/SourceCode/ai-coding/nexus/AGENTS.md:1-143`
  - `/Users/DennisWang/SourceCode/ai-coding/nexus/nexus-dist/rules/00-nexus-core.md:1-102`
  - `/Users/DennisWang/SourceCode/ai-coding/nexus/nexus-dist/protocol/agent-protocol.md:1-737`
  - `/Users/DennisWang/.claude/agents/body.md:1-216`
  - `/Users/DennisWang/.claude/agents/eye.md:1-160`
  - `/Users/DennisWang/.claude/agents/mind.md:1-325`

- Assumptions:
  - 用户不需要 4+ 分身的复杂协作
  - 用户不需要自动化反思和知识提取
  - 用户偏好手动控制而非自动化

---

## 执行步骤

### Phase 1: 备份 (安全第一)

```bash
# 备份现有配置
cp -r ~/.claude ~/.claude.backup.$(date +%Y%m%d)
cp -r nexus-dist nexus-dist.backup
```

### Phase 2: 删除文件

```bash
# 删除 nexus-dist/agents/ 全部
rm -rf nexus-dist/agents/

# 删除协议和反思
rm -rf nexus-dist/protocol/
rm -rf nexus-dist/parallel/
rm -rf nexus-dist/reflection/

# 删除 context 和 hooks
rm -rf nexus-dist/context/
rm -rf nexus-dist/hooks/

# 删除命令
rm nexus-dist/commands/plan.md
rm nexus-dist/commands/reflection.md

# 删除 runtime (保留 selfcheck.py)
cd runtime
rm -f scheduler.py cli.py anchor_manager.py artifact_manager.py
rm -f event_bus.py health_monitor.py metrics.py state_manager.py visualizer.py
cd ..
```

### Phase 3: 创建新文件

```bash
# 创建 agents 目录并复制分身定义
mkdir -p nexus-dist/agents/
cp ~/.claude/agents/body.md nexus-dist/agents/
cp ~/.claude/agents/eye.md nexus-dist/agents/
cp ~/.claude/agents/mind.md nexus-dist/agents/
```

### Phase 4: 重写核心文件

1. 重写 `nexus-dist/rules/00-nexus-core.md` (极简 protocol)
2. 重写 `nexus-dist/commands/nexus.md` (精简命令)
3. 重写 `AGENTS.md` (精简注册表)
4. 精简 `CLAUDE.md`
5. 精简 `README.md`
6. 精简 `install.sh`

### Phase 5: 验证

```bash
# 运行安装
./install.sh

# 验证文件存在
ls -la ~/.claude/agents/
ls -la ~/.claude/rules/

# 运行自检
python3 ~/.nexus/runtime/selfcheck.py

# 测试分身调用
# /nexus @eye explore ...
# /nexus @body fix ...
# /nexus @mind design ...
```

### Phase 6: 清理

```bash
# 删除备份 (确认无问题后)
rm -rf nexus-dist.backup
rm -rf ~/.claude.backup.*

# 删除 __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## Next Steps

1. **@body**: 执行 Phase 2 (删除文件)
2. **@body**: 执行 Phase 3 (创建新分身文件)
3. **@body**: 执行 Phase 4 (重写核心文件)
4. **@body**: 执行 Phase 5 (验证)
5. **本体**: 验证裁剪结果
