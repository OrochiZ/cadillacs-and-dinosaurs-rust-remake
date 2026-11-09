# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：把 dino 过场脚本的 action 编号转成可查语义（第十六格）

**背景**：`3a03e6fc` 补 wof 指令技状态编码后，工作区干净。
dino 回源文件、wof 脚本轨道边界、`notes/01-early.md §19` 五套脚本
全景都已核过；但用户最早关心的「事件脚本」里，**dino 过场脚本
26 scripts × 6 字节记录 × 41 个 action 的编号 → 意义** 一直只在源码
与笔记里散着，没进缓存。

### 回源

- `notes/00-overview.md §9.4`（945-960 行）：跳表 `0x1DBD6` 41 项；
  记录 `[action, G.$4F0, G.$4FD, G.$506, timer:word]`；
  `timer=0xFFFF` 是 wait-until；笔记已列出多数 action 名。
- `notes/01-early.md §19.1 #1`：五套脚本全景里英雄过场脚本那一套。
- `dino-rs/crates/dino-game/src/game/script.rs:249-343`：`script_action`
  的 match 就是 41 项逐条分派，每条带原地址；文件头注释明写
  「41 actions 的代码移植到这里，各带原地址」。
- `dino-rs/crates/dino-assets/src/script.rs`：`ScriptRecord` 字段语义，
  `action` 是跳表字节偏移而非枚举序号。

### 落点

- `semantics.json` 新增 `dino_script_action`：`0x00..0x50` 步长 2
  共 **41 项**，按「等一个条件 / 覆写输入让角色走自己状态机 /
  直接启动玩家状态 / 改世界（生成对象、字幕、声音、GO、淡出）」
  写成人话；两个 END（`0x0A` 全体 / `0x26` 只自己）的差别写明。
  note 说明这不是动作序号、多数不是播动画、状态字 != 0x0200 会挂起、
  未列偏移走 default 空分支。
- 新增 `dino_script_record`：6 字节记录的 5 个字段键，写明 +1/+3
  是全局规则档位字、会跨记录保留（含 END），字段键排除出 `collide`。
- `coverage.registered` 加第 10 组回源、`themes.event_script` 加两域；
  `OFFSET_KEY_DOMAINS` 加 `dino_script_record`。
- 自测 97 → **105/105**（41 项齐全、`0x2C` 置 GO、十进制 44 也能
  命中 0x2C、两个 END 差别、记录 +3 no_clamp、`collide 4` 现在也列出
  亮相动作、字段偏移排除、置 GO 与波次收尾的 `$7A9` 对上）。
- `DESIGN_DIFF_NOTES.md` 补一段倒推：41 个动作大多不是播动画，是
  「等世界回话」+ 伪造输入；一条记录同时管「演到哪儿」和「这一帧
  按什么规则跑」；`0x2C` 与波次收尾字写同一个 GO，放行权不收在
  中央开关里。标 dino 侧登记、不放大成两款共同架构。
- 顺手修掉一处输入错字（`0x08` 的「不请输入」→「不清输入」）。

### 实跑验证

- `--selftest` 105/105；`py_compile` OK。
- **64 域 / 516 条**；`coverage` 10 组、缺 0 个域；
  `themes` 列出 64 个、去重 64 个。
- `lookup.py dino_script_action 0x2C` 与 `... 44` 都读到
  「置 GO（G.$7A9=1）：把镜头锁放行」。
- 四份改动文件 `CR=0 BOM=False`；`DESIGN_DIFF_NOTES.md` 超 2000 字节的
  仍是既存第 57 / 89 / 154 行，本轮新增行 0 超长；
  `git diff --check` exit=0。

### 边界

- **0 次 ROM**；只读 rep 内 Rust 源码 / 笔记 / 缓存与离线脚本，
  未碰 `g:/wof/wt1` 源码，未恢复「以 ROM 审 repo」框架。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 假红，
  不改 `CLAUDE.md` / `.gitignore`。
- 不把 `[I]` 写成 `[O]`；不从函数名猜意义（只登记源码注释 / 笔记
  明确点名的）；载具标志 `0x4C` 只登记「等标志」，不往载具换面展开；
  特殊关卡 / 单个 Boss 专属编排不构成通则。
- 离散编号不连成范围；位域 / 字段偏移域继续被 `collide` 排除。

### 长期口径（细则在耐久层，不在本文件展开）

- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。
  Stop hook 是客户端自动重发催办，**不直读 goal 状态**；按「继续合理授权工作」直接做。
- 不写「下一格 / 短期不再动笔」当收尾；提到方向就当轮把第一步做掉。
- 交付一律**说人话**：人类理解中的游戏设计，不报内部编号、校验数字当主体。
- 产物层无分析意义；ROM 主要服务于 data 调查，仅在 `wof_cs` 非常可疑时才核实。
- 写盘 LF 无 BOM；提交信息走 `git commit -F` 临时文件随后清理。
- 新增语义域必须带 source / scope / tag；`coverage.registered` 与
  `themes.list[*].domains` 都必须覆盖所有域且每域只归一处。

## 收尾

- 校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、
  `git status --short`；`git commit -F` 后 `Remove-Item` 临时信息，再复核干净工作区。
