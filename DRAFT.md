# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：接着把「各种表」的抽象意义转成缓存（第二格）

**背景**：上一格 `f9fa84ba` 收口了覆盖索引（43 域 / 306 条、42/42 自测），工作区干净。
按 `长时间自主推进` 继续，用户明确说「各种表数值的抽象意义都要转换缓存」，
所以这一格回源再找仍适合转的**符号 / 档位表**，不碰量。

### 回源与取舍

- 先 Grep 各 SPEC 的章节与表格行，锁定还没转、且确实是「编号 → 身份」的成表：
  `re/specs/player/SPEC.md §4.2` 攻击 id 表、§4.9.1 手持物 kind 与持械状态表；
  `re/specs/enemy/SPEC.md §8.2` 波次控制器 r4 / r5；
  `re/specs/sound/SPEC.md §7` 音序命令字、§9.2 声像运动模式表。
- **一处写盘前订正**：初稿想写「r5=2 碰到 terminator 就转 4」，回源 §8.2 代码确认
  分组 terminator 是重置 7200 帧预算、**回到 r5=0 读下一组阈值**；只有 r5=0 读到
  final 的负 end 才进 r5=4 收尾。已按代码改准，note 里也写清「分组 terminator 不是收尾」。
- **另一处收紧**：`weapon_kind` 初稿把「可边走边开枪」写在 0x206 / 0x207 上，但
  §4.9 摘要与 §4.9.1 状态表口径不完全一致；改成每条只记「是什么」，
  「按攻击键进哪个状态」另立 `weapon_attack_state` 域，避免把两处口径焊成一句。
- `0x209` 的「bazooka」名在 §4.9 标 [I]、行为是 [O]，缓存里明确分开写，不把 [I] 说成 [O]。
- 攻击数据表每行的伤害 / 眩晕 / 反应 / 定格是**量**，按 `coverage.not_registered` 第一条不转；
  这里只转「$58 = 这个编号是哪一招」。

### 交付

- `re/specs/semantics.json`：新增 7 个域 —— `attack_id`、`weapon_kind`、
  `weapon_attack_state`、`wave_ctrl_r4`、`wave_ctrl_r5`、`seq_command`、`pan_mode`；
  全部带 scope / source / tag，两个上下文相关域带 note。
  `coverage.registered` 三个回源分组同步补上，仍是 8 组、无遗漏无多余。
- `re/specs/lookup.py`：域数量断言 `>= 50`；新增 10 条自测（含「同一个 4 在招式表
  和帧类型表里不是一回事」「collide 4 现在也列出招式 / 波次 / 音序」）；
  用法加一行 `attack_id 0x5A` 示例。

### 实跑验证

- `--selftest` → **52/52 通过**。
- `coverage` → 「合计 50 个域 / 376 条；索引缺 0 个域、多 0 个域」。
- 抽查：`attack_id 0x5A` → 冲刺攻击第 2 拍；`weapon_kind 0x209` → 火箭筒；
  `seq_command 0x18` → 设声像（都带别名与回源）。
- `py_compile` OK；`git status --short` 仍只有两处 M。

### 边界

- **0 次 ROM 取证**；全部来自 rep 内 SPEC 只读回源与离线脚本。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 假红，不改 `CLAUDE.md` / `.gitignore`。
- 不恢复「以 ROM 审 repo」框架；不把 `[I]` 写成 `[O]`；不从字段名猜意义。
- 环境硬限制照旧（无 Rust 工具链 / `dino.zip` / `re/rom` / `target`），新脚本 ROM-free。

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
