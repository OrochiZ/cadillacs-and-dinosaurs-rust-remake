# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `64c43468`，工作区干净，临时提交信息文件不存在。

- 前一轮（同一会话）已提交：`d062b9d9`（wof 半边同一个 `4`）、`c0f55f79`（`moment` 合成）、`209dc4e8`（「一拍也不是一条数据」接回外推文第三节）、`3602f95b`（阅读顺序第 7 条）、`64c43468`（`moment` 补 SPR 环，三环并排）。

- 本轮第一格 `997a3898`：补齐讲两侧却只有半边样本的三条 —— `death`（`enemy_hurt_reaction 14` 后滑 vs `wof_reaction 14` 碎尸）、`feel`（`attack_field +3` 命中定格）、`values`（`box_index_zero dino/wof`）；自测把两侧约束扩到五条。先验证前提救回一次误判：`combo` 看着像讲两侧，回外推文 §二边界见「不并成同一套因果」，不补。

- 本轮第二格 `68650f53`：把「哪些算讲两侧」在剩余三节核完，§五边界明写都是 dino 侧、§六没提 wof、§七「两边调度层同构」wof 侧按边界不转；三条不该补的理由写进各自 `cannot_check` 与 `legacy.note`，总入口补半句，自测固化。

- 本轮第三格（本格）：做缓存自身的体检。一次性审计六项，五项全绿，只查出一处：`box_index_zero` 标了 `context_dependent` 却没有 `note`（其余上下文相关域都写了「查之前要确认什么」）。补上说明：`dino` / `wof` 不是同一编号的两种读法，是两款游戏给了相反规则，跨游戏搬判定代码时最该改的是那句 `==0` 早退。同时把体检固化进自测：新增四条断言（每个域有 `label`、上下文域带 `note`、三条索引引用的 215 处域名真实存在、`not_registered` 每条有 `what/why`），与既有「scope/source/meaning/tag」那段并列。`229/229` 通过。总入口第 227 行已写过盒索引 `0` 两侧读反的例子，不重复补文。

- 验证：`--selftest` exit 0、`py_compile` exit 0、`semantics.json` 可 `json.load`、`git diff --check` exit 0、四个文件 `CR=False BOM=False`，新改的两个文件 `over2000=0`（总入口只剩既存 3 行超长）。

- 本轮未触发 ROM 取证；没碰产物层；没改 `check_docs.py`；没回查载具 / 特殊关卡换面。未新增 `semantics.json` 域，没动 `coverage` 分组 / `themes` 分组 / `legacy` 判断条目（只补了一个域的 `note`）。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；总入口「阅读顺序」第 7 条是压缩恢复后找它们的入口。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算（正文不并成共同架构、或 wof 侧按边界不转），`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- `notes/08-wof-cs-gaps.md` 记的是 C# 移植侧欠账，不是 wof 原机缺机制。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
