# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对（本会话起点）：HEAD `fe07f040`，工作区干净，临时提交信息文件不存在；`CODEBUDDY.md` / `CLAUDE.md` / `DRAFT.md` 都读过。上一格（文档层）已按 `GAMEPLAY_LEGACY.md` 第 481 行停止条件收口。

- 本会话已提交六格：
  - `dc71f468`：`unknown` 入口，一次列出两类「还没弄明白」；`semantics.json` 加 `coverage.unknown_note`。230 → 237。
  - `ec46b2f6`：`say()` 把解码命令里静默丢掉的 `[O]/[I]/[U]` 标签补回来；字段 / 位偏移说明按纪律不挂。237 → 242。
  - `0d591f8b`：`reaction_brief()` 把「反应编号是门票」接成下一环，`attack` / `moment` 都并排翻到 dino 两本受击册子，不串 wof。242 → 247。
  - `54c9fbc6`：回源路径从「格式对」推进到「真能点开」，修 8 处裸文件名、自测查文件存在与行号范围。247 → 249。
  - `b4a99935`：`themes` 按玩法主题给出观察 / 推断 / 未登记的成色，并指向 `unknown <域>`。249 → 252。
  - 第六格（本格）：把入口补到必读层真正指向的地方。

- 本格前先做了几次核查，结论都是**核过、无需改动**，别再重复翻：
  - `wof_hurt_book` 记的是「按入口路径翻哪本 9 项手册」的路径类别，不是那 9 项本身；wof 侧没有与 dino 对称的断环，硬接会造假语义。
  - `legacy` 九条判断挂的 18 条可跑样本逐条真跑，`expect` 全命中、0 失败。
  - `notes/08-wof-cs-gaps.md` 事实核查：wt1 的 `wof_cs/src`、`QUARANTINE.md`、`STATUS.md` 都可达；全部 `文件:行号` 锚点 0 处找不到文件、0 处越界；抽查十几处注释，当前欠账与「不算欠账」的修复记录都还与原标注一致；`Cps1PlayerMulti.cs:249-268` 整段对得上。清单没过期，wt1 只读未改。
  - 总入口「阅读顺序」第 7 条写了「不带参数运行就打印全部用法」，`lookup.py` 用法说明里 `unknown` / 证据标签 / 反应门票两侧并排都在；第 481 行「不改总入口」约束的是外推文那节补层。不补设计文档。

- 第六格的真缺口：`CLAUDE.md`（开工必读）让新会话「Start with `re/README.md` and `re/specs/CONTEXT.md`」，而这两处**一个字都没提** `semantics.json` / `lookup.py`；整套「取值 → 抽象意义」的入口只写在 `DESIGN_DIFF_NOTES.md` 第 7 条与 DRAFT 里。按必读层走会整套漏掉。
  - `re/README.md` 路径表加一行、`re/specs/CONTEXT.md` 路径清单加两行，都是路径导航（英文，保持两个文件原有语言），不是设计判断、不加节号；README 那行顺带指回仓库根 `DESIGN_DIFF_NOTES.md`。
  - 自测加一条：`re/README.md` 与 `CONTEXT.md` 都必须提到 `semantics.json` / `lookup.py`，防止以后重写 README 时又把入口删掉。252 → 253。

- 验证：`--selftest` exit 0、`253/253` 通过、`py_compile` exit 0、`git diff --check` exit 0；`lookup.py` / `README.md` / `CONTEXT.md` 均 `CR=0 BOM=False`，新增行 `over2000=[]`。

- 本会话始终未动任何设计文档正文（不改 `DESIGN_DIFF_NOTES.md` / `GAMEPLAY_LEGACY.md` / `notes/08`）、0 次 ROM 取证、没碰产物层、没改 `check_docs.py`、没回查载具 / 特殊关卡换面；`GAMEPLAY_LEGACY.md` 第 481 行停止条件仍有效。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；入口有三处：`CLAUDE.md` 指向的 `re/README.md` / `re/specs/CONTEXT.md` 路径清册、`DESIGN_DIFF_NOTES.md`「阅读顺序」第 7 条、以及 `lookup.py` 不带参数的用法说明。`unknown` 一次列出哪些还没弄明白（两类未登记分开说，未登记 ≠ 不存在）；`themes` 按玩法问题查数时带观察 / 推断 / 未登记的成色并指向 `unknown`。解码命令翻取值意义时也带 `[O]/[I]/[U]` 标签，字段 / 位偏移说明不挂（那是格子名不是取值）；后果环把反应门票并排翻到 dino 两本受击册子，不串 wof。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`。
- 回源路径一律从仓库根写全（如 `dino-rs/crates/dino-assets/...`），不留 `dino-assets/` 这类裸前缀、也不留纯文件名；`legacy.list[*].title` 与 `GAMEPLAY_LEGACY.md` 九节标题逐字对应、顺序一致，改标题两边同步。自测会查文件真实存在与行号范围，白名单只放命令示例 `lookup.py` 与通配符 `/HANDOFF.md`。
- **停止条件**：`GAMEPLAY_LEGACY.md` 第 481 行「不改总入口、不加新节号、不回文档自洽循环」；415–481 补层已闭合、`legacy` 九条索引只对应前九节，不补后半部底座。伪代码 / 流程图各卷已很多；总入口 153–157 行三个实际问题落点、`coverage.not_registered` 13 条理由、`themes` 已是按玩法问题那条索引 —— 都核过，别再翻。`notes/08` 是移植侧欠账清单、非原机缺机制，锚点与注释已核过与当前 wt1 源码一致。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算，`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
