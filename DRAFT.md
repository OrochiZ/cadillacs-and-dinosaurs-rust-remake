# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `64c43468`，工作区干净，临时提交信息文件不存在。

- 前一轮（同一会话）已提交：`d062b9d9`（wof 半边同一个 `4`）、`c0f55f79`（`moment` 合成）、`209dc4e8`（「一拍也不是一条数据」接回外推文第三节）、`3602f95b`（阅读顺序第 7 条）、`64c43468`（`moment` 补 SPR 环，三环并排）。

- 本轮第一格 `997a3898`：核证据底座，补齐讲两侧却只有半边样本的三条 —— `death` 加 `enemy_hurt_reaction 14`（后滑，与原 `wof_reaction 14` 碎尸并排）、`feel` 加 `attack_field +3`（命中定格）、`values` 加 `box_index_zero dino/wof`（关盒 / 合法表项）。自测把「两侧」约束从 `beat / swing` 扩到五条。**先验证前提救回一次误判**：`combo` 看着像讲两侧，回外推文 §二边界见「wof 那句不并成同一套因果、不放大成共同架构」，且 wof 续拳窗口无可查取值，按不从概括固化不补。

- 本轮第二格（本格）：把「哪些算讲两侧」在剩下几条核完，别只抽查六条。外推文 §五边界明写「都是 dino 侧登记、wof 侧按 §11.0 不臆断」；§六正文根本没提 wof；§七虽写「两边调度层还都是协作式任务轮」，但那是结构同构观察、wof 侧按边界没有转成取值的域。三条都不该补 wof 样本，理由写进各自 `cannot_check` 与 `legacy.note`，总入口那段也补上半句，自测加一条固化「三条都写清理由」。`225/225` 通过。

- 两格合起来判据才完整：该补的两侧补上真跑证据，不该补的写清为什么不补，压缩恢复后不会看到一句「两边」就去凑一条没验的样本。按 §94.23 属同一批事实的证据补齐，不另算设计。

- 验证：`--selftest` exit 0、`py_compile` exit 0、`semantics.json` 可 `json.load`、`git diff --check` exit 0、四个文件 `CR=False BOM=False`，新改的三个文件 `over2000=0`（总入口只剩既存 3 行超长）。实跑 `legacy death / feel / values / combo` 四条输出逐条读过。

- 本轮未触发 ROM 取证；没碰产物层；没改 `check_docs.py`；没回查载具 / 特殊关卡换面。未新增 `semantics.json` 域，没动 `coverage` / `themes`。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；总入口「阅读顺序」第 7 条是压缩恢复后找它们的入口。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算（正文不并成共同架构、或 wof 侧按边界不转），`difficulty` 正文没提 wof。理由都已写进各自 `cannot_check`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- `notes/08-wof-cs-gaps.md` 记的是 C# 移植侧欠账，不是 wof 原机缺机制。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
