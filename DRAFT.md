# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `64c43468`，工作区干净，临时提交信息文件不存在。

- 前一轮（同一会话）已提交：`d062b9d9`、`c0f55f79`、`209dc4e8`、`3602f95b`、`64c43468`（语义缓存 / `moment` 三环 / 可恢复性那条线）。

- 本轮五格：
  - `997a3898` 补齐讲两侧却只有半边样本的三条（`death` / `feel` / `values`）；`combo` 按外推文 §二边界不补。
  - `68650f53` 把「不算讲两侧」的理由写死（`combo / crowd / continuity`）。
  - `47671e02` 缓存自身体检，补 `box_index_zero` 的 `note`，四条字段审计进自测。
  - `a2b273b6` 把「拍子也落在当事对象身上」收进总入口「一页设计意图」正文收尾，按 §94.23 不另算设计。
  - 本格（第五格）：做回源对账。外推文九节标题与 `legacy.list[*].title` 逐字对应、顺序一致（改过第三节正文但没动标题，核对无误）；全库 100 段 `source` 里的文件路径扫一遍，查出两处少写 `dino-rs/crates/` 前缀 —— `domains.attack_field.source` 的 `dino-assets/src/sprites.rs:149-158` 与 `coverage.registered` 第 10 组的 `dino-assets/src/script.rs`，按原写法在仓库根找不到文件。已改成完整路径（真实位置经 Glob 核实），复查失效路径归零。两条约束落盘：`legacy.note` 写明九节标题要两边同步、回源路径一律从仓库根写全；自测加一条纯字符串断言拦裸前缀。`230/230` 通过。

- 核过而不重复做的：伪代码 / 流程图各卷已很多；总入口 153–157 行「三个实际问题的落点」已有「优化 wof」四层改动面；`coverage.not_registered` 13 条逐条有回源理由；`themes` 已是「按玩法问题」那条索引。

- 验证：`--selftest` exit 0、`230/230` 通过、`py_compile` exit 0、`semantics.json` 可 `json.load`、`git diff --check` exit 0、三个文件 `CR=False BOM=False` 且 `over2000=0`；路径复活查 `失效路径=0`。

- 本轮未触发 ROM 取证；没碰产物层；没改 `check_docs.py`；没回查载具 / 特殊关卡换面。未新增域，没动 `coverage` 分组 / `themes` 分组 / `legacy` 判断条目（只修 source 路径与 note）。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；总入口「阅读顺序」第 7 条是压缩恢复后找它们的入口。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`。
- 回源路径一律从仓库根写全（如 `dino-rs/crates/dino-assets/...`），不留 `dino-assets/` 这类裸前缀；`legacy.list[*].title` 与 `GAMEPLAY_LEGACY.md` 九节标题逐字对应、顺序一致，改标题两边同步。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算，`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- `notes/08-wof-cs-gaps.md` 记的是 C# 移植侧欠账，不是 wof 原机缺机制。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
