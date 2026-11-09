# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对（本会话起点）：HEAD `fe07f040`，工作区干净，临时提交信息文件不存在；`CODEBUDDY.md` / `CLAUDE.md` / `DRAFT.md` 都读过。上一格（文档层）已按 `GAMEPLAY_LEGACY.md` 第 481 行停止条件收口。

- 本会话已提交八格，自测 230 → 258：`dc71f468`（`unknown` 入口）、`ec46b2f6`（解码输出带 `[O]/[I]/[U]` 标签）、`0d591f8b`（反应门票接下一环）、`54c9fbc6`（回源路径真能点开）、`b4a99935`（`themes` 给证据成色）、`d0c70050`（`CLAUDE.md` 必读层指得到缓存）、`384dba4a`（37 条命令全量冒烟，顺手修 `cmd_list()` 漏 `return 0`）、第八格（本格，上下文相关域的内容核查）。

- 核过、无需改动的层，别再重复翻：`wof_hurt_book` 记的是入口路径类别而非 9 项手册本身（wof 侧没有对称断环）；`legacy` 九条挂的 18 条可跑样本逐条真跑全过；`notes/08-wof-cs-gaps.md` 全部 `文件:行号` 锚点 0 处找不到、0 处越界，抽查注释与当前 wt1 源码一致；总入口「阅读顺序」第 7 条与 `lookup.py` 用法说明的可恢复性链是通的。

- 第八格：自测原本只保证「上下文相关域都带 `note`」，没验内容。先把 18 个这类域的 note 逐条读过，内容都讲清了「先确认哪一侧 / 哪个对象 / 哪个档位」，没有不合格的；但由此看出一处**结构不一致**：
  - `player_run_state` / `player_air_state` 都标了 `context_dependent`，note 明说「同一个状态字 `$06` 在地面 / 跑动 / 空中三张表里各有一本手册」；可主表 `player_ground_state` 与最上层 `player_mode` **都没标**。于是查地面状态表、按编号反查、列它未登记的取值时，都不会提醒「先确认 mode / sub / `$06` 三层」——而同一个编号在这几张表里意思完全不同，正是这个标记要防的误读。
  - `semantics.json`：两个域补 `context_dependent: true`，note 补上「查之前先说清 mode=2 / sub=0 / `$06=0` 三层」（保留原有的设计观察：连段是几个各占一格的独立状态、靠命中确认才往下翻）。
  - `lookup.py`：`cmd_unknown()` 单域视图也打印「注意（上下文相关）」，与 `emit()` / `collide` 的提示口径一致；全览不逐域铺 note，避免变吵。
  - 自测 4 条：状态机四层都标了上下文相关且 note 讲清三层、查单值会提示、反查同一个 `4` 时那行带 `[上下文相关]`、`unknown <上下文域>` 也带提示。254 → 258。

- 验证：`--selftest` exit 0、`258/258` 通过、`py_compile` exit 0、`json.load` 通过、`git diff --check` exit 0；`lookup.py` / `semantics.json` 均 `CR=0 BOM=False`，新增行 `over2000=[]`。

- 本会话始终未动任何设计文档正文（不改 `DESIGN_DIFF_NOTES.md` / `GAMEPLAY_LEGACY.md` / `notes/08`）、0 次 ROM 取证、没碰产物层、没改 `check_docs.py`、没回查载具 / 特殊关卡换面；`GAMEPLAY_LEGACY.md` 第 481 行停止条件仍有效。wt1 仓库只读、未改。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；入口有三处：`CLAUDE.md` 指向的 `re/README.md` / `re/specs/CONTEXT.md` 路径清册、`DESIGN_DIFF_NOTES.md`「阅读顺序」第 7 条、以及 `lookup.py` 不带参数的用法说明。`unknown` 一次列出哪些还没弄明白（两类未登记分开说，未登记 ≠ 不存在）；`themes` 按玩法问题查数时带观察 / 推断 / 未登记的成色并指向 `unknown`。解码命令翻取值意义时也带 `[O]/[I]/[U]` 标签，字段 / 位偏移说明不挂（那是格子名不是取值）；后果环把反应门票并排翻到 dino 两本受击册子，不串 wof。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`，且 note 要讲清「查之前先确认哪一侧 / 哪个对象 / 哪一层档位」——状态机四层（mode / 地面 / 跑动 / 空中）都在内。**新增或改动解码命令后，`SMOKE_CASES` 要跟着加**；每条命令必须 `return 0`，别让 `main() -> int` 拿到 `None`（`sys.exit(None)` 会伪装成退出码 0）。
- 回源路径一律从仓库根写全（如 `dino-rs/crates/dino-assets/...`），不留 `dino-assets/` 这类裸前缀、也不留纯文件名；`legacy.list[*].title` 与 `GAMEPLAY_LEGACY.md` 九节标题逐字对应、顺序一致，改标题两边同步。自测会查文件真实存在与行号范围，白名单只放命令示例 `lookup.py` 与通配符 `/HANDOFF.md`。
- **停止条件**：`GAMEPLAY_LEGACY.md` 第 481 行「不改总入口、不加新节号、不回文档自洽循环」；415–481 补层已闭合、`legacy` 九条索引只对应前九节，不补后半部底座。伪代码 / 流程图各卷已很多；总入口 153–157 行三个实际问题落点、`coverage.not_registered` 13 条理由、`themes` 已是按玩法问题那条索引 —— 都核过，别再翻。`notes/08` 是移植侧欠账清单、非原机缺机制，锚点与注释已核过与当前 wt1 源码一致。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算，`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
