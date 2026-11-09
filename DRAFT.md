# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `fe07f040`，工作区干净，临时提交信息文件不存在；`CODEBUDDY.md` / `CLAUDE.md` / `DRAFT.md` 都读过。

- 上一格（文档层）已按 `GAMEPLAY_LEGACY.md` 第 481 行停止条件收口，本轮**没动任何设计文档**：不改 `DESIGN_DIFF_NOTES.md`、不改 `GAMEPLAY_LEGACY.md`、不碰 `notes/08-wof-cs-gaps.md`、不碰产物层。

- 本格做的是数据层 / 工具层的一个真实缺口：上一轮导出全部 `[U]` 标签（18 条 / 11 个域）后发现，缓存能查「某个值是什么意思」，却没有入口一次列出「哪些值还没写明白」。分析时最容易把「未登记」读成「不存在」，这条得能查。
  - `re/specs/semantics.json` 的 `coverage` 新增 `unknown_note`：把两类「没弄明白」分开讲清 —— 一类是取值在册但意义标 `[U]`，一类是整类按 `not_registered` 不转成域；两类都只是「没写意义」，不等于游戏里没有、也不等于没有证据（不少不转的表在 SPEC 里有 [O] 级代码观察，只是形态是量 / 条件分支 / 随机漂移）；给出「先查域 → 再 collide → 才回源」的查法。
  - `re/specs/lookup.py` 新增 `unknown_rows()` / `cmd_unknown()` 与 `unknown` 命令：`unknown` 全览按域分组逐条列出 18 条 `[U]`（带出处）并并排列出 13 类按纪律不转的理由；`unknown <域>` 只看某一册，没有 `[U]` 的域会明说「不代表整类都清楚」；给不存在的域明确报错并指向 `list`。doc、`cmd_list()` 导航、`main()` dispatch 同步。
  - 自测新增 7 条断言：把「18 条 `[U]` 全部只写部分意义、没有硬给具体意义」这条实证固化下来（以后谁硬编意义会红），并验全览 / 单域 / 空域 / 错域四种视图与边界句。

- 实跑输出核过：`unknown` 全览「共 18 条 / 11 个域」、`unknown player_ground_state` 六条带出处、`unknown frame_type` 明说没有 `[U]`、`unknown no_such_domain` 指向 `list`；中文通顺，无「这些编号」这类指代落空。

- 验证：`--selftest` exit 0、`237/237` 通过（原 230 + 7）、`py_compile` exit 0、`json.load` 通过、`git diff --check` exit 0；`lookup.py` / `semantics.json` / `DRAFT.md` 均 `CR=0 BOM=False`，新增行 `over2000=[]`。

- 本轮未触发 ROM 取证；没碰产物层；没改 `check_docs.py`；没回查载具 / 特殊关卡换面；没往文档自洽循环加层。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；总入口「阅读顺序」第 7 条是压缩恢复后找它们的入口。`unknown` 是「一次列出哪些还没弄明白」的入口，两类未登记分开说，未登记 ≠ 不存在。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`。
- 回源路径一律从仓库根写全（如 `dino-rs/crates/dino-assets/...`），不留 `dino-assets/` 这类裸前缀；`legacy.list[*].title` 与 `GAMEPLAY_LEGACY.md` 九节标题逐字对应、顺序一致，改标题两边同步。
- **停止条件**：`GAMEPLAY_LEGACY.md` 第 481 行「不改总入口、不加新节号、不回文档自洽循环」；415–481 补层已闭合、`legacy` 九条索引只对应前九节，不补后半部底座。伪代码 / 流程图各卷已很多；总入口 153–157 行三个实际问题落点、`coverage.not_registered` 13 条理由、`themes` 已是按玩法问题那条索引 —— 都核过，别再翻。`notes/08` 是移植侧欠账清单、非原机缺机制，已核过与缓存口径一致。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算，`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
