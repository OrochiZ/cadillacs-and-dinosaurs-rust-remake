# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：把「看到一段 ANI 编号就知道是哪一招」补上（第五格）

**背景**：前四格到 `6841d80b`，51 域 / 382 条、58/58 自测，工作区干净。
Stop hook 催办后继续。回 `re/specs/anim/SPEC.md §3.2 / §3.6` 发现用户举例的 ANI
那一层还有最直接的一块缺口：`anim_set` 只转了「6 套」的套号，套里每段编号
（ANI 表 `u16 offset[id]` 的 id）是哪一招没转；而 §3.6 的 punch chain 有代码级
出处，能把「动画 id → 哪一招 → $58 → 状态字 → 连段计数」串起来。

### 回源与取舍

- §3.2：6 套 × 4 角色，`table = u32(set_ptr + 4*b03)`，每套有效 id 数各角色不同，
  id 只是 `offset[id]` 的下标。
- §3.6 只逐段列了 **Jack** 的 set 0 / 1 / 2，并明写 `ids O, labels I from art`；
  set 3/4/5 只有套级用途。所以：
  - 三个 `jack_anim_setN` 域的 scope 写成 `dino / Jack only`、context_dependent，
    标签按 SPEC 标 I；set1 的 0..7 用 punch chain 代码标 O，id 15 标 U。
  - `10-13 jump attacks` 是 SPEC 明写的一族连续编号，才用范围键；其余一律离散键。
  - 未列出的 id 不登记、不硬答。
  - 其余三角色逐段表按纪律不转，理由写进 `coverage.not_registered`：
    不能把 Jack 的编号意义套到别人身上。
- `combo_counter`（+$B2）：§3.6 punch chain 标 [O]，只在命中确认时 +1，
  动画演完才按它翻页；把「连段是打出来的」落成一个可查取值。

### 交付

- `semantics.json` 新增 4 域：`jack_anim_set0`（26 条）/ `jack_anim_set1`（11 键）/
  `jack_anim_set2`（8 条）/ `combo_counter`（3 条），共 48 条；
  `coverage.registered` anim 组补 4 域；`not_registered` 加「其余三角色逐段表不转」。
- `lookup.py` 新增 `SET_DOMAINS` 与 `anim_id <set> <id>` 命令：按套 + 段直接查，
  先给套级意义，再给该段意义，set 1 额外提示四张表对齐；set 3/4/5 直说「没有
  逐段编号表，不猜」。域数量断言 `>= 55`，新增 8 条自测。

### 实跑验证

- `--selftest` → **66/66 通过**。
- `coverage` → 「合计 55 个域 / 431 条；索引缺 0 个域、多 0 个域」。
- 抽查：`anim_id 1 4` → 终结拳（$58 = 4、状态 0x0200000C、3 帧叠加 comp 0xA8）；
  `anim_id 0 21` → 跳跃踢（帧类型 4、攻击盒 0x0B / 0x0C / 0x0D）；
  `anim_id 3 0` → 只给套级用途、不猜逐段。
- `py_compile` OK；`git status --short` 只有两处 M。

### 边界

- **0 次 ROM**；只读 rep 内 SPEC 与离线脚本，未碰 `g:/wof/wt1` 源码。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 假红，不改 `CLAUDE.md` / `.gitignore`。
- 不恢复「以 ROM 审 repo」框架；不把 `[I]` 写成 `[O]`；不从字段名 / 常量名猜意义。
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

- 校验两份文件 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、
  `git status --short`；`git commit -F` 后 `Remove-Item` 临时信息，再复核干净工作区。
