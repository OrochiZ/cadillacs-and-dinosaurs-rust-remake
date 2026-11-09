# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对（本会话起点）：HEAD `fe07f040`，工作区干净，临时提交信息文件不存在；`CODEBUDDY.md` / `CLAUDE.md` / `DRAFT.md` 都读过。上一格（文档层）已按 `GAMEPLAY_LEGACY.md` 第 481 行停止条件收口。

- 本轮第一格已提交 `dc71f468`：给缓存加 `unknown` 入口，一次列出两类「还没弄明白」（标 `[U]` 的取值 / 整类按纪律不转的表），`semantics.json` 新增 `coverage.unknown_note`，自测 230 → 237。

- 本格（第二格）做的是解码输出层的真实破口：实证核出「查单值 / 列域 / 反查」都带 `[O]/[I]/[U]` 标签，但几条「喂原始字节翻意义」的命令把标签静默丢了。
  - 实证：`frame_type 0 / 6` 是 `[I 推断]`，喂 `moment 10 ... 0605 ...`（必杀帧）时第 1 环写「特殊 / 必杀攻击帧」不带标签；`frame` 逐字段行标了 `[I 推断]`，但「这一帧在干嘛」那段又把同一个值说成确定事实。`jack_anim_set1` 有 3 条 `[I]` + 1 条 `[U]`，`emit()` 那路是好的，带出的攻击后果两行没带。
  - `re/specs/lookup.py` 新增 `say()`：解码命令里凡是直接引用缓存意义的，连标签一起说。改到 `cmd_frame` 帧类型 / 盒示例、`infer()` 身份、`cmd_moment` 第 1 环与盒示例、`cmd_wof_attack` 的 `describe()` / shake、`cmd_anim_id` 带出的攻击后果；doc 边界句同步。
  - **字段 / 位偏移说明不挂标签**（「+0..3 是伤害随机偏移」讲的是这一格叫什么、不是某个取值的意义），按取值反查排除字段偏移域的同一纪律；这条写进 `say()` 的说明与自测，避免以后被「统一」回去。
  - 自测新增 5 条：喂必杀帧 / 中立帧 / wof 参数行 / `anim_id` 都验标签在，且字段布局没被冒充成取值。230 → 237 → 242。

- 验证：`--selftest` exit 0、`242/242` 通过、`py_compile` exit 0、`git diff --check` exit 0；`lookup.py` `CR=0 BOM=False`，新增行 `over2000=[]`。

- 本轮仍未动任何设计文档（不改 `DESIGN_DIFF_NOTES.md` / `GAMEPLAY_LEGACY.md` / `notes/08`）、未触发 ROM 取证、没碰产物层、没改 `check_docs.py`、没回查载具 / 特殊关卡换面；`GAMEPLAY_LEGACY.md` 第 481 行停止条件仍有效。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；总入口「阅读顺序」第 7 条是压缩恢复后找它们的入口。`unknown` 是「一次列出哪些还没弄明白」的入口，两类未登记分开说，未登记 ≠ 不存在。解码命令翻取值意义时也带 `[O]/[I]/[U]` 标签，字段 / 位偏移说明不挂（那是格子名不是取值）。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`。
- 回源路径一律从仓库根写全（如 `dino-rs/crates/dino-assets/...`），不留 `dino-assets/` 这类裸前缀；`legacy.list[*].title` 与 `GAMEPLAY_LEGACY.md` 九节标题逐字对应、顺序一致，改标题两边同步。
- **停止条件**：`GAMEPLAY_LEGACY.md` 第 481 行「不改总入口、不加新节号、不回文档自洽循环」；415–481 补层已闭合、`legacy` 九条索引只对应前九节，不补后半部底座。伪代码 / 流程图各卷已很多；总入口 153–157 行三个实际问题落点、`coverage.not_registered` 13 条理由、`themes` 已是按玩法问题那条索引 —— 都核过，别再翻。`notes/08` 是移植侧欠账清单、非原机缺机制，已核过与缓存口径一致。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算，`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
