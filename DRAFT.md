# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `7f6e67a1`，三处未提交改动（后提交为 `d062b9d9`：wof 半边同一个 `4` 接回「数值没有全局意思」）。`git diff` 的中文乱码是 PowerShell 显示层，Read 直读确认完整。

- 本轮依次提交：
  - `d062b9d9` 收尾上一轮未提交的三处改动。
  - `c0f55f79` 新增 `lookup.py moment [10|12] <帧记录> [attack <8 bytes>]`，把同一帧几份数据合成「在干嘛」；比 `chain` 多一层「攻击记录不是任何时候都能挂」。`live` 按 `frame_type` 域修准为 4 / 6 两类攻击帧，盒索引写成 `0x1A`。总入口补两段设计判断。自测 `207/207`。
  - `209dc4e8` 把「一拍也不是一条数据」倒推回 `GAMEPLAY_LEGACY.md` 第三节；`legacy.swing.can_check` 补上合成入口、probe 加 `moment` 真跑样本；自测 `210/210`。

- 核过边界而不是补表：`coverage.not_registered` 13 条逐条都有具体回源理由，没有「笼统划掉、其实该转」的；总入口 181 行已写明 `themes` 就是「按玩法问题」那条索引，173–190 行六行横向表是综合分析路径、不承诺域映射 —— 「再建一层问题索引」属重复造轮子，没做。`re/notes/session-*.md` 等工程存档按既定边界不回翻。

- 本格补的是**可恢复性**：总入口「阅读顺序（压缩恢复后先读这里）」6 条里一次都没指向 `semantics.json` / `lookup.py`，缓存要到 200 行以后才被提到。补第 7 条，写清查某个取值 / 某段 ANI·SPR 数据该去哪、三条索引各按什么分组、喂字节的解码入口有哪些、`chain` 是说明版，以及「查不到会直说未登记，别读成游戏里没有」。另加一条自测把这条导航固化：14 个入口无参数真跑，确认没退化成未知域。自测 `211/211`。

- 验证：`--selftest` exit 0、`py_compile` exit 0、`git diff --check` exit 0、三个文件 `CR=False BOM=False`，新改的两个文件 `over2000=0`（总入口只剩既存 3 行超长）。

- 本轮未触发 ROM 取证；没碰产物层；没改 `check_docs.py`；没回查载具 / 特殊关卡换面。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；总入口「阅读顺序」第 7 条是压缩恢复后找它们的入口。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- `notes/08-wof-cs-gaps.md` 记的是 C# 移植侧欠账，不是 wof 原机缺机制。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
