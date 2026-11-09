# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：收口「覆盖索引」这一格

**背景**：上一轮 Stop hook 后继续推进，已在 `re/specs/semantics.json` 加了 4 个域
（`sound_command` / `sound_code` / `sound_header_type` / `game_phase`）和顶层 `coverage`，
在 `re/specs/lookup.py` 加了 `cmd_coverage()` 与 dispatch；压缩打断在最后一步之前，
没自测、没编译、没写回 DRAFT、没提交。本轮按开工机制复位后把它做完。

开工核现场：`git log -8` 头 `3b5dd691`；`git status --short` 只有
`M re/specs/lookup.py` / `M re/specs/semantics.json`；无 `R:\Temp\dino_commit_msg.txt`。
回读两份文件，确认 43 个域、`coverage.registered` 已列全、`cmd_coverage()` 与
`main()` dispatch 都在，缺的只是把新表与索引固化进 `--selftest`。

### 本轮改动

- `re/specs/lookup.py`：
  - 域数量断言从 `>= 39` 收紧到 `>= 43`；
  - 新增 4 条覆盖索引断言（每个域都有回源分组、无已删域、无重复登记、
    `cmd_coverage()` 输出含合计与「缺 0 / 多 0」）；
  - 新增 5 条新表抽查（`0xFF06` 淡出、`0x30` 落音效段、声音头 5 即优先级、
    关内阶段 4 = 等清场、`0xFFxx` 命令字不落进普通编号段）。
- `re/specs/semantics.json`：本轮未再改；内容就是上一轮落盘的 43 域 + `coverage`。

### 实跑验证

- `python -X utf8 re/specs/lookup.py --selftest` → **42/42 通过**。
- `python -X utf8 re/specs/lookup.py coverage` →
  「合计 43 个域 / 306 条；索引缺 0 个域、多 0 个域」，8 个回源分组逐条列出。
- `python -m py_compile re/specs/lookup.py` → OK；`__pycache__` 被忽略，未进工作区。
- `git status --short` 仍只有那两个 M，编译没带出新文件。

### 边界

- **0 次 ROM 取证**；全部来自 rep 内 SPEC / 笔记的只读回源与离线脚本。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 因产物前缀报的假红，
  不改 `CLAUDE.md` / `.gitignore` 的产物状态描述。
- 不恢复「以 ROM 审 repo」框架；不把 `[I]` 写成 `[O]`；不从字段名猜意义。
- 环境硬限制照旧：无 Rust 工具链、无 `dino.zip` / `re/rom` / `target` ⇒
  编译、回归、MAME 对拍做不了，不是缺口；新脚本特意 ROM-free。

### 长期口径（细则在耐久层，不在本文件展开）

- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。
  Stop hook 是客户端自动重发催办，**不直读 goal 状态**；按「继续合理授权工作」直接做。
- 不写「下一格 / 短期不再动笔」当收尾；提到方向就当轮把第一步做掉。
- 交付一律**说人话**：人类理解中的游戏设计，不报内部编号、校验数字当主体。
- `dino载具是特殊关卡,没什么好看的` ⇒ 载具 / 特殊关卡 / 单个 Boss 那一段编排不构成通则。
- 产物层无分析意义；ROM 主要服务于 data 调查，仅在 `wof_cs` 非常可疑时才核实。
- 写盘 LF 无 BOM；提交信息走 `git commit -F` 临时文件随后清理。
- 新增语义域必须带 source / scope / tag；`coverage.registered` 必须覆盖所有域；
  离散编号不连成范围；位域 / 字段偏移域继续被 `collide` 排除。

## 收尾

- 校验三份文件 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、
  `git status --short`；`git commit -F` 后 `Remove-Item` 临时信息，再复核干净工作区。
