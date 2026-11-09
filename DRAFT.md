# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `37200c9d`，工作区干净，临时提交信息文件不存在；`CODEBUDDY.md` / `CLAUDE.md` / `DRAFT.md` 都读过。前两格是「把挨打后演哪一段接进数据链」与「核清敌人侧不是同一套组织法」，自测 277/277。
- 本轮先**验证上一轮留下的前提**：`enemy_hurt_reaction.note` 写了「按兵种的逐类动画表按 coverage.not_registered 不转」，但全量导出 `not_registered` 只有 13 条，根本没有这一条——是悬空引用。同时敌人册子 15 条 meaning 里到处是「anim 0 / 1 / 2 / 3」，缓存里却没有能查这些编号的域，正是用户要的「看到数据就知道抽象意义」的缺口。
  - 回源 `re/specs/enemy/SPEC.md:1135-1179`（§10.2，[O]）：`set_hit_anim(e, anim)` 的 0..4 是**跨兵种一致的姿态槽语义**（轻畏缩 A/B、击倒 A/B、起身），只是每一槽最终用哪套图要按 `e.w84` 查 `L[0x2E68C + e.w84]`。两层要分开。
  - **新增 `enemy_hurt_anim` 域**（69 域，5 槽，全 `[O]`）：按槽号可查哪些反应直接分派来，`reactions` 用十进制、与 `enemy_hurt_reaction` 键同一套；只列直接分派，轻击改判击倒那种条件分支不挂进去，免得读成同时播。
  - **补 `not_registered` 第 14 条**：逐兵种图集内容按纪律不转（SPEC 只给查表入口与按类型索引，没给逐行意义），理由里点明槽位语义已单独登记在 `enemy_hurt_anim`。两条 note 的引用改准：`enemy_hurt_reaction` 指向第 14 条与新域，`player_hurt_anim` 改成「敌人侧另有一张槽位表、编号体系不同」。
  - **接环**：新增 `enemy_hurt_anim_for()`，`reaction_brief()` 把玩家侧 / 敌人侧两条下游**各自紧跟自己那本册子**（而不是堆在末尾串成一条链）；`hurt_anim_for()` 输出改成子行缩进。`chain` 说明版从「这一环只在玩家侧成立」改成「两侧都能再往下一环，但各走各的」。实际跑 `attack` 看过输出，两本册子各带一行下游，层级清楚。
  - 同步：`coverage.registered` enemy 组、`themes.state_machine`、用法说明、`SMOKE_CASES`（38 → 40）、自测 6 条（敌人侧接环、两侧下游顺序不串、悬空引用落实为第 14 条、reactions 都能查到、新域两层边界、说明版改准）。277 → 282。
- 验证：`--selftest` 282/282 exit 0、`py_compile` exit 0、`json.load` 通过、`git diff --check` exit 0；两个文件 `CR=0 BOM=False`，新增行 70、`over2000=[]`。
- 本轮 0 次 ROM 取证、没碰产物层、没改 `check_docs.py`、没动任何设计文档正文（`DESIGN_DIFF_NOTES.md` / `GAMEPLAY_LEGACY.md` / `notes/*`）、没回改早期卷、没回查载具 / 特殊关卡换面；`GAMEPLAY_LEGACY.md` 第 481 行停止条件仍有效。wt1 仓库只读、未改。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果 → 受击反应 → 挨打的人怎么演，在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；入口有三处：`CLAUDE.md` 指向的 `re/README.md` / `re/specs/CONTEXT.md` 路径清册、`DESIGN_DIFF_NOTES.md`「阅读顺序」第 7 条、以及 `lookup.py` 不带参数的用法说明。`unknown` 一次列出哪些还没弄明白（两类未登记分开说，未登记 ≠ 不存在，每条带 blocked_at）；`themes` 按玩法问题查数时带观察 / 推断 / 未登记的成色并指向 `unknown`。解码命令翻取值意义时也带 `[O]/[I]/[U]` 标签，字段 / 位偏移说明不挂（那是格子名不是取值）；后果环把反应门票并排翻到 dino 两本受击册子、**各自的下游紧跟自己那本册子**（玩家 set2 段号 / 敌人姿态槽），不串 wof、也不串两侧。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`，且要讲清「查之前先确认哪一侧 / 哪个对象 / 哪一层档位」——状态机四层（mode / 地面 / 跑动 / 空中）都在内。**多个键写同一句意义不算错**（武器段被特例切两段、多变体同规则、多段同标签），但要在 note 里讲清为什么，别让人当成抄重去「修正」。**新增或改动解码命令后，`SMOKE_CASES` 要跟着加**（现在 40 条）；每条命令必须 `return 0`，别让 `main() -> int` 拿到 `None`。
- **`[U]` 不是漏查清单**：每条 `[U]` 必须带 `blocked_at`，写清回源走到哪一行 / 哪一段、为什么停（SPEC 自己标 [U]、上游 Open gaps 明列、只给 handler 没给逐项意义、编号合并成一类）。`blocked_at` 里的路径从仓库根写全、行号不越界，自测会扫。有充分证据的 `[U]` 要真升级成 `[O]` / `[I]` 并补条目级 `source`——升级时别忘 `unknown` 的条数与「该域是否还在 unknown 里」会跟着变；没证据的别硬答，也别反复回源翻同一批。当前 17 条 `[U]` 已逐条回源核过，别再从头翻；`legacy.difficulty` 现在挂两条 probe（波次 + 贴脸按档停顿），别只留一条。
- **动画编号有三层，别混**：`player_hurt_anim` 是 [O]「玩家受击代码播 set2 第几段」、四个角色通用；`enemy_hurt_anim` 是 [O]「敌人受击代码分派到哪个姿态槽」、跨兵种一致的槽位语义；`jack_anim_set2` 是 [I]「Jack 那一段长什么样」。敌人每槽具体图集要按 `e.w84` 查 `L[0x2E68C + e.w84]`，逐兵种内容按 `not_registered` 第 14 条不转；§3.6 只列到 #7，#8 / #9 只在 §5 受击代码里出现，#5 无调用点。两侧反应编号集合本就不同，别互套、别跨对象推全表。**note 里引用 `coverage.not_registered` 之前先确认真有对应条目**，别留悬空引用（本轮修的正是这个）。
- 回源路径一律从仓库根写全（如 `dino-rs/crates/dino-assets/...`），不留 `dino-assets/` 这类裸前缀、也不留纯文件名；`§N` 要指向真能翻到的标题（早期卷若只分 `N.1`–`N.k` 子节，就写子节范围，别写总节号）。`legacy.list[*].title` 与 `GAMEPLAY_LEGACY.md` 九节标题逐字对应、顺序一致，改标题两边同步。自测会查文件真实存在、行号范围与 `§号` 标题，白名单只放命令示例 `lookup.py` 与通配符 `/HANDOFF.md`。
- **停止条件**：`GAMEPLAY_LEGACY.md` 第 481 行「不改总入口、不加新节号、不回文档自洽循环」；415–481 补层已闭合、`legacy` 九条索引只对应前九节，不补后半部底座。伪代码 / 流程图各卷已很多；总入口 153–157 行三个实际问题落点、`themes` 已是按玩法问题那条索引 —— 都核过，别再翻。`not_registered` 现在 14 条理由，逐条都有回源，别再从头翻。`notes/08` 是移植侧欠账清单、非原机缺机制，锚点与注释已核过与当前 wt1 源码一致。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算，`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
