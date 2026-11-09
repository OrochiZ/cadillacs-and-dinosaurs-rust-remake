# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：补 wof 受击手册选择与玩家输入契约（第七格）

**背景**：`a08c2b8f` 把「一次连段的四本册子」倒推回外推文，工作区干净，
缓存 55 域 / 431 条、66/66。Stop hook 催办后继续。回源找仍贴主线、
有出处的符号层。

### 回源与取舍

- 读 `notes/06-method.md §94.16 / §94.17`：wof 受击是「编号 → 入口路径
  对应的 9 项表 → 状态档位 → 按 ObjId 查 0x25DC 动画表」四层；
  且 §94.17 明确「真正按角色分的是动画数据，不是受击逻辑」，
  宿主函数名带角色 / 序号是命名误导。
- 读 `re/specs/player/SPEC.md §2 Input notes [O]`：**没有输入队列**，
  新按下是 1 帧上升沿，能攒的只有 `$AD` / `$C9` / `$BC` / `$F4/$F5` 四处，
  各自绑在具体处境上。
- 读了 `re/specs/flow/SPEC.md §6` 的 G.$1A / G.$20 前端输入位与 EEPROM
  设置字节，**决定不转**：用户明确排除「适配古代硬件特色和低性能」的部分，
  这些是机台层，不参与关卡里那场架怎么排。理由写进 `coverage.not_registered`，
  免得以后把机台适配误当游戏性。
- `re/specs/enemy/SPEC.md §6.4 rank events`：全是 ±N 的量，按既有
  `not_registered` 第一条不转，不另立域。

### 交付

- `semantics.json` 新增 2 域：
  - `wof_hurt_book`（5 条描述性键，每条 alias 是入口地址，看到 `0x11878`
    这类地址也能直接查；context_dependent，note 写清四层链路与命名误导）；
  - `input_buffer`（5 条字段语义，明写没有输入队列）。
- `coverage.registered` 06 卷组补 `wof_hurt_book`、player 组补 `input_buffer`；
  `not_registered` 加街机前端硬件位一条。
- `lookup.py`：域数量断言 `>= 57`，新增 6 条自测。

### 一处工具失败与订正

- 首跑 `--selftest` 71/72，**唯一 FAIL 是断言写窄了**：条目 `what` 写的是
  「街机前端」而断言找「硬件」。按「工具失败先分两种」核了实际文本，
  数据没错，把判据改成检查 `what` 含「街机前端」且 `why` 同时含
  「硬件」「游戏性」。重跑 72/72。没有为迁就断言去改数据。

### 实跑验证

- `--selftest` → **72/72 通过**。
- `coverage` → 「合计 57 个域 / 441 条；索引缺 0 个域、多 0 个域」。
- 抽查：`wof_hurt_book 0x11878` → 绝大多数敌人共用的受击手册（别名生效）；
  `input_buffer $C9` → 受击中必杀攒 10 帧。
- `py_compile` OK；`git status --short` 只有两处 M。
- 注：`coverage | Select-Object -Last 3` 经 PowerShell 管道出现中文乱码，
  属已知显示问题；完整 coverage 直接运行正常，且 selftest 已断言其内容。

### 边界

- **0 次 ROM**；只读 rep 内 SPEC / 笔记与离线脚本，未碰 `g:/wof/wt1` 源码。
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

- 校验三份文件 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、
  `git status --short`；`git commit -F` 后 `Remove-Item` 临时信息，再复核干净工作区。
