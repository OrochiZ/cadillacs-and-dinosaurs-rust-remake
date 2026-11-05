# 复刻方法论与 wof 路线决策笔记

> 记录 2026-11-05 在 `G:\wof\dino` 会话中形成的结论。
> 讨论对象：`G:\wof\wt1`（用户自己的 wof / C# 逐字节项目）与 `G:\wof\dino`（dino / Rust native port）。
> 原始对话档案：`re/notes/session-01a1a8e4.md`（由 `re/tools/session_notes.py` 生成）。
> 本文件是**提炼结论**，不是流水记录；证据细节与原始措辞回档案查。

## 0. 为什么有这份文档

本会话被压缩多次，中途结论曾只能靠回读 transcript 恢复，没有沉淀。故落两份互补产物：

- `re/tools/session_notes.py` — 通用抽取脚本，可复用于任意会话 `.jsonl`。
- `re/notes/session-01a1a8e4.md` — 机器抽取的**原始对话档案**（真实用户消息 + 助手回答 + 压缩点索引 + 压缩摘要全文 + 工具调用清单），不丢细节。
- 本文件 — 可提交、给人读的**决策依据**。

以后长会话结束跑一次脚本即可，不再依赖上下文窗口。

## 1. 两套真值模型

| | wt1 | dino |
|---|---|---|
| 真值 | 机器级大端内存映像 `Cps1Memory.WRAM byte[0x10000]`，FBA `.fr/.fs` 逐字节比 WRAM / GFXRAM / CPS 寄存器 | 语义层 typed state，`Game::tick()` 一帧，对象字段 / 全局 / sprite list / tilemap / palette / sound request 逐帧对拍 |
| 中间态 | 不允许；`worse=0` 是非回归判据，没有终点 | 允许：M3 占位类打通全流程，未移植类 `trace_hold` 冻结 |
| 残差 | 登记但不豁免 | `allow/final.txt` 编号 + 原因 + `Player sees:`，声明不改玩法 / 伤害 / 分数 / 掉落 / 敌人 / Boss / 结局 |

**澄清**：dino 不是"降低标准到局部可玩性同步"，而是**从机器字节层换到语义字段层 + 公开残差 + 允许中间态**；终态仍逐帧严格。

## 2. 完成度与快慢

- dino `STATUS.md`：M0–M9 Done，M10 In progress 23/26；**没有自述 100%**；`allow/final.txt` 自称 "FINAL LIST OF KNOWN DIFFERENCES BETWEEN THE PORT AND MAME"。
- dino 快的原因：差异可定位、typed 状态空间小、逐帧状态灌入、单代码工人 + 所有权、M3 占位骨架、bot 自动通关、设计前置。
- wof 慢的原因：逐字节真值把终态判据施加到过程态；调度器 / 中断 / CPU 预算也进入验收范围；FBA `.fr/.fs` 全量测量口径负担；合并 / 台账 / 审计消耗；无终点 `worse=0`。

## 3. 硬件中断 / 执行次数不确定 → dino 怎么解

- 删掉可挂起 PC / 任务槽 / 时间片：`Game::tick()` 固定帧序（`flow_frame → run_fade_task → skip_wait_rounds → latch`），无 68000 PC / USP。
- `SKIP_ROUNDS = 3` 固定替代原机随负载 2.2–5 轮变化的 skip wait。
- `port.sh` 四模式：`run` / `follow` / `step` / `lagsync`。`step` 每帧从 MAME 上一帧状态启动，差异只来自本帧；`lagsync` 在 lag / catch-up record 后重灌状态，lag record 本身豁免（`diff.py --no-skip-lag`）。
- 帧存档来源：MAME 0.289 CLI + Lua `record.lua`，`0xFF0152` 帧标志 write tap 取帧末快照，dump `ram` / `gfx` / `cpsa` / `cpsb` 四 region 原始字节；`DINOTRC1` 64 字节块增量，**不是 savestate**。
- 冷启动反而是 dino 最硬的验收：M1 / M3 与 power-on traces 对开机→吸引循环→投币→结局→回 attract 逐帧对拍。

## 4. 端序与"rep 外先验"

- Lua recorder 不做语义端序转换，只 `string.pack(">I2", ...)` 还原硬件字节序列。
- Rust 侧显式：`dino-extract/src/rom.rs` 加载 zip 时按 `ROM_LOAD16_WORD_SWAP` 交换每 16-bit word，`u16/u32` 用 `from_be_bytes`；`harness.rs` 读 `G.$0` 用 `u16::from_be_bytes([ram[0x8000], ram[0x8001]])`；容器头 / 块索引用 `from_le_bytes`。
- **wof 不需要复合结构语义**：只要每个变量单独起始地址 + 宽度，`BU16/BS16` 即可。
- "rep 外"的定义（用户纠正）：不是"结果文件不在 repo"，而是"**结论不是用 repo 内方法工具得到的**"。语义先验部分来自被忽略的会话观察与 probe logs，`decomp.c` 不入库 —— 不是纯机械可再生。但见 §11：这些先验一旦写进 port 并对拍通过，就固化成 repo 内可执行规格。

## 5. 功能范围

- F2 是 `--debug-keys` 下 kill all，**不是**服务键；服务键 `9` 只加 credit。
- `D5-final-plan.md` decision 4 刻意 out of scope：operator test menu / EEPROM edits / service mode / debug dip / anti-tamper / 非 World region。

## 6. 渲染与 SDL

- `macroquad 0.4` / miniquad / OpenGL GLSL ES；核心是 `DrawTarget` trait、palette-indexed atlas、pen mask、屏幕延迟 latch、384×224 RenderTarget、`Cpu` headless 软件渲染器。
- SDL 可承接 `DrawTarget` / CPU renderer / latch / harness；最大缺口是**验证 harness** 和可选资产层，而资产层对写回 ROM 不需要。
- 不建议照搬 `AssetPack` 与 Rust 游戏内容。

## 7. MAME vs FBA

- dino：MAME 0.289 CLI + Lua（**不是** MAME2xx）。FBA 无 Lua，但用户已直接改 C++ 核心，有 `.fs` 逐帧、a68k trace、mem watch、replay、state、`-nothrottle/-norender/-noatrace/-fslevel`。
- FBA 缺 dino 式 `--load-state` / `--step-from` / `--lagsync` 以及 64 字节增量 trace。
- 性能：MAME probe 约 20x real time；FBA `-nothrottle` 实测 223 fps（默认 57.4）但含全量 `.fs` 压缩。真正差距是**每帧约 1.9KB 增量 vs 272KB 全量**，以及**dino 把模拟器移出了迭代内循环**。

## 8. 三路线 / VBCC / 语言成本

- 三条路线：① wofrep 内按综合优点改造，继续 C#；② dinorep 改造成面向 wof，继续 Rust；③ 同②但从头写 C89。
- **三条路线都不会丢 wofrep 的地址注释**（用户纠正）。真正的担心是 C# / Rust 源码无法简单或等价翻译成 VBCC 表达 —— 68K 上没有 C# / Rust 编译器。
- 结论：**最终必须有一份 C89**；C# 作 oracle，C89 是终点；语言翻译不自动等价，靠 FBA 对拍验证行为等价；Rust 路线多一层语言落差。
- 规模：`dino-rs` 全库 116,064 行，`dino-game` 107,904 行，大部分是 dino 专属内容；真正语言转换影响的框架约 2 万行；`re/harness` 对 Rust 耦合只有 5 个 shell 脚本的构建命令 / 路径。**大成本永远是把游戏内容换成 wof，与语言无关。**

## 9. AssetPack 单向门 —— 后续修正（重要）

- 初判：`Game` 硬依赖 `&'static AssetPack`、逻辑从不读 ROM bytes、字段按语义命名 → "最不可逆的单向门，回不到 68K"。
- **修正**：`dino-game/src/game/trace.rs` 头部明确
  > Every field the port models is listed here once, by its original address (work RAM at 0xFF0000, `G.$x` = 0xFF8000 + x, objects at their handle). One list per struct drives both … frame record addresses are converted here in both directions.

  并有 `FieldVisitor::field(addr, size, name, v)` 与 `(addr, size, name)` 收集器；`frame_addr` / `frame_id` 双向转换；资产带 `rom_addr` 与 `frame_by_addr` / `raw_by_addr` 反向索引。
- 所以**地址没丢，且集中在 trace / harness 边界，是机器可读的一等公民**；丢的是**代码侧 PC ↔ 语义绑定**（固定 tick 无 PC）。
- 正确表述：门关的是"**实现编译回 68K**"，不是"**知识 / 地址查询回去**"。这是 §11 的钥匙。

## 10. Opus 5.5 核实与推论（含不确定性标注）

- 来源：2026-11-05 `WebSearch`，**中文科技媒体 / 百科二手报道，非 Anthropic 一手公告**。
- 发布：多数报道 **2026-09-22**；百度百科专页 / 知乎写 9-23 正式、9-21 内测 → 1 天口径差（内测 / 正式 / 时区），不影响结论。
- 能力：证实且更强。多家把 vibe-coding 游戏反编译 / 重编译热潮归因于 Opus 5.5；"把读懂机器码的门槛砍到地板"；数百个浏览器移植项目集中涌现；发布当天数小时出现黑暗之魂 / 微软模拟飞行 / 马力欧赛车原型。规格：100 万 token 上下文、128K 输出、长时 Agent、$4/$20 每百万 token。
- **用户未提到的反转**：
  - 10/21 前后 Opus 5.5 开始拒绝配合 **REA**（打包 Ghidra / IDA 等 41 个工具的逆向工具），逆向回答中途被安全检查打断；GameLook "Claude 已经无法再 Reverse Engineer Anything"。
  - 10/25 IT之家"被曝悄悄限制逆向工程能力"，并明确 **Anthropic 没有官宣新版本**（用户反馈 + 服务端改动）。
  - 10/27 前后 Claude Code 服务端推送 `tengu_heron_brook` 规则：允许原创 / 品类 / 自有素材游戏，禁止重建某款特定现有游戏（改名或声称原创也不行）；10/30 开发者 Chasm 在 X 发帖（浏览 200 万+），Anthropic 官方确认，10/31 gamedeveloper 报道。
  - OpenAI 10/21 发新版使用政策，11/20 生效。媒体评价"可能已经太晚""难被真正拦住"。
- **与本项目直接相关**：`CLAUDE.md` 里 "REA cannot open 68000 code; use Ghidra headless" —— 被拒配合的正是这个工具。
- dino 时间线（git 核实）：最早提交 **2026-10-12**、最新 2026-11-05、566 提交**全部在 9/22 之后**（之前 0 个）、跨度 24 天、M1–M9 集中在 10/13–10/21、`D5-final-plan.md` 写于 10/13。项目比发布晚 20 天立项；repo 内**没有**把路线选择归因于 Opus 5.5 或 AI 复刻热潮的记录。

### 由"共识"改为"成本差"

- 用户论断："作者用半个月说明共识是'看起来像'没价值" → **字面不成立**：单人项目 + `STATUS.md` 里 "three Claude Desktop sessions (Opus, Sonnet, Haiku)" ≠ 共识；同期数百个原型是反向的多数行为；真实情况是**分岔**。
- dino 也不是"对抗 AI"样本，而是**AI 武装后做精确复刻**的样本（file mailbox 派单、大量 `desktop sonnet/opus/haiku task N` 提交）。半个月是 **AI 加速后的成本下限**，不是壁垒高度。
- 正确表述：AI 把"像"的边际成本压到≈0 后，价值**迁移** —— 从"实现"到"可验证性"；"像"在精确复刻的验收函数里 0 分，在市场 / 2 小时熊孩子的验收函数里满分。

### 离散性（用户补充的机制）

- 现代游戏规则自动计算（公式可推导、可泛化、可压缩）；CPS1 / 68000 是离散人为跳变（frame 表、hitbox 手工坐标、伤害 / 掉落查表、palette / tile 硬编码时机、状态特殊 case），值之间无规律、不可插值、不可推导。
- 但精确化三点：
  1. 值本身可机械 dump（`dino-extract` 就在干），难的是**绑定 / 触发 / 时序**（哪个脚本第几帧读哪张表、与中断 / lag 交互）。
  2. 难是**验收标准的函数** —— "看起来像 / 能玩"可用连续规则近似掉（正是 2 小时原型的做法），"逐帧一致 / 实机可验"下近似全部作废。
  3. 对人一样难；LLM 长上下文批量逐条核对反而有优势（1,599 条录像逐条 equal 是证据）。壁垒不是"AI vs 人"，是"**有原始 ROM 证据 + 验证闭环 vs 没有**"。
- **反直觉推论**：离散性**奖励 wof 的做法、惩罚 dino 的做法** —— 离散值无语义可压缩，重排成语义命名 typed 结构（`AssetPack`）只增工作量不减信息；按 ROM 原地址 / 原字节直读才是最省表达。闭合 §9 与 §4"wof 只需单变量起始地址"。

### 壁垒的准确含义

不是"复古平台对 AI 免疫"（限制是系统提示词 / 政策层，报道称可绕过），而是：AI 压缩"写出能跑的实现"，压不动"证明逐帧一致"；证明能力在已积累的地址注释 + FBA 对拍 + 台账里，不在模型里。政策收紧进一步说明**验证回路该放离线 repo 内**，别绑在单一模型可用性上。

## 11. 活的逆向正确性（用户洞察，最有价值的一步）

- Ghidra 正确性三级：label / type / comment（静态断言，无自证）→ `decomp.c`（一次性反编译快照，不跑）→ **port + 1,599 条录像逐帧 equal（可执行规格）**。
- 传统单向流水线：`ROM → Ghidra/decomp → 人理解 → 实现`。这里反向回灌：`已验证的实现 → Ghidra 符号 / 类型 → 更好的 decomp → 再验证`。
- 顺手解决 §4 悬案：会话里的隐性先验一旦写进 port 并对拍通过，就固化成 repo 内可执行、可复现的规格。
- **两边各有一半**：
  - dino_rs 强**数据侧**：`trace.rs` 的 `(原地址, 宽度, 语义名)` 清单 + frame 的 `rom_addr` / `frame_by_addr` → 可灌 Ghidra 数据符号 / 类型 / equate / frame record 结构。
  - wof_cs 强**代码侧**：`CODEMAP.md` 由 `agent_scripts/gen_codemap.py` 从 `*.cs` **自动生成**，命名约定 `中文功能名_对应ASM_地址`，表格带**对应度分级**（对应ASM / 部分对应ASM / 可能对应ASM / 无对应ASM）。这是函数 ↔ ROM 代码地址映射，dino_rs 恰恰缺。
  - Ghidra 现状：`re/ghidra/` 只有 `entries.txt` 入库（proj / 脚本 / `decomp.c` 按 `CLAUDE.md` 不入库）；Ghidra 12.1.4 headless、约 3,560 函数、`DinoSetup.java` / `DinoExport.java`、函数头 `// ==== 00013fa6`；**目前无任何从 port 反哺数据库的机制**。
- **补写 Ghidra**：`DinoSetup.java` 已在做 preScript import，扩一段批量 `createLabel` / `createData` / `setComment` / `addEquate` 即可让 3,560 个无名函数的 decomp 可读；但**代码侧函数语义名 port 给不出**（PC 已删），需 wof_cs 式地址锚点或人工。产物守 gitignore：Ghidra 数据库 / `decomp.c` 不入库。
- **68K mod**：把"写回 ROM"从**全量重写**降级成**定位 + 打补丁**。ROM 主体仍是原版 68000 代码，只改几个字节 / 表 / 跳转；port 只当**地图**（语义字段 → `trace.rs` 字段清单 / `frame_by_addr` → 原地址）；**不需要 port 能编译回 68K，不需要任何语言翻译**，绕开 §9 单向门与 §8 语言落差；patch 后仍用 FBA 逐帧对拍，**闭环不变**。
- 诚实边界：复刻是 `实现 == 原机`，mod 是 `原机 + Δ == 想要`；Δ 是原机里不存在的行为，**没有原机真值可对拍** —— 对拍只能验"没改坏的部分仍逐帧一致"，改过的部分靠实机观察 + 设计意图；新增离散跳变同样无规律，LLM 帮定位 / 防回归，帮不了设计 Δ。

## 12. 最终路线（未变）

- **产物地基**：ROM 地址 / C89 / 砖块渲染 / 68K-VBCC 可编译 / 实机运行。不照搬 `macroquad`、palette shader、`AssetPack` 硬依赖（那是离开原硬件后补的税）。
- **验证层 / hacky 劫持 / 逐帧对拍**：尽量自动化、尽量用 AI，越便宜越好，因为它不进入产物。
- **dino 可搬的只剩纯方法层**（不含游戏内容 / 语言 / 渲染）：目标定义、公开残差清单取代 `worse=0`、帧标志 tap → 64B 增量 → `step` / `lagsync` 重同步、现象清单 → 有限任务表。
- 稀缺溢价来源：不是"别人觉得它没价值"（需求判断，会被 AI 改写），而是"**别人不愿花这个成本**"（成本壁垒，稳）。守的是"精确复刻 + 实机可运行"这一格，不是整个市场。

## 13. 待办 / 下一步

1. 导出统一 **symbol 表** `(地址, 宽度, 语义名, 置信度, 来源证据)`：一份表三用 —— 喂 Ghidra preScript、喂 mod patch 定位、喂"以语义查 ROM"。这是"活的逆向正确性"的落地形态，也是把§11 从洞察变成工具的一步。
2. 扩 `DinoSetup.java`：批量灌 label / data / equate。
3. `CODEMAP.md` 补"语义 → 地址"反查与数据侧（目前只有地址 → 函数）。
4. 遵守 `CLAUDE.md`：`dino.zip`、Ghidra 数据库、`decomp.c`、raw disassembly、ROM 字节表一律不入库；`re/out/assets/` 是唯一提交的渲染资产例外。
5. 若要移动本笔记到 `G:\wof\wt1`（用户自己的项目），整体搬 `re/notes/` 与档案即可，脚本用 `-o` 指定新路径。

## 14. 证据索引

- 原始对话档案：`re/notes/session-01a1a8e4.md`（`re/tools/session_notes.py` 生成；含压缩点索引、压缩摘要全文、工具调用附录）。
- 关键文件：`re/README.md`、`STATUS.md`、`run.md`、`plan/phase-00-exactness-harness.md`、`plan/game/design/D5-final-plan.md`、`allow/final.txt`、`re/harness/{record.sh,record.lua,port.sh,diff.py}`、`dino-rs/crates/dino-game/src/game/{mod.rs,trace.rs}`、`dino-rs/crates/dino-extract/src/rom.rs`、`dino-rs/crates/dino-assets/src/{lib.rs,enemy.rs}`、`re/ghidra/entries.txt`、`G:\wof\wt1\CODEMAP.md`、`D:\Test\FbaSrc\FBA_CLI_参考.md`。
- 核实方式：本会话内 `git log` / `Grep` / `Read` / `WebSearch`（Opus 5.5 部分为二手来源，已在 §10 标注）。
