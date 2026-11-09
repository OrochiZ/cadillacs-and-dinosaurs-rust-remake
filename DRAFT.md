# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `7f6e67a1`，三处未提交改动，临时提交信息文件不存在；逐条核过 diff 确认是上一步验证后的内容，`git diff` 的中文乱码是 PowerShell 显示层，Read 直读文件确认完整。该批提交为 `d062b9d9`（wof 半边同一个 `4` 接回「数值没有全局意思」）。

- 第二格提交为 `c0f55f79`：新增 `lookup.py moment [10|12] <帧记录> [attack <8 bytes>]`，把同一帧的几份数据合起来说「在干嘛」；比 `chain` 多一层「攻击记录不是任何时候都能挂」的判断。`live` 判据按 `frame_type` 域修准为 4 / 6 两类攻击帧（0 / 2 是抓投探测，8 / 10 / 12 / 14 不发起攻击），盒索引改按 SPEC 写成 `0x1A`。总入口补两段设计判断（一拳不是一条数据；画面与判定是两套数据）。自测 `207/207`。

- 提交后先核了边界而不是补表：`coverage.not_registered` 13 条逐条都有具体回源理由，没有「笼统划掉、其实该转」的；`legacy` 九条 probe 都挂了真跑命令。总入口 181 行已写明 `themes` 就是「按玩法问题」那条索引，173–190 行那份更细的六行横向表是综合分析路径、不承诺域映射 —— 所以「再建一层问题索引」是重复造轮子，没做。

- 本格做的是把第二格的判断倒推回外推文：`GAMEPLAY_LEGACY.md` 第三节在「一套动作是时间里的结构化事件序列，拍子一半藏在这里」之后补一段「另一半藏在『一拍』自己也不是一条数据」——身份 / 画面 / 判定 / 后果分在几本互不统属的册子里，要同一 tick 由对的对象对上才算这一拳；所以老游戏的拍子不是全场一个时钟，是几个当事对象各自数完、恰好对齐的一拍。按既有口径这是接 192 行的补句，不另算第十条判断。
  - `semantics.json` 的 `legacy.swing.can_check` 补上「一次喂进去合成一句、并拦住错配」，`probe` 加一条 `moment` 真跑样本（expect「两本册子」）。
  - `lookup.py` 加两条自测固化「底座接上合成样本」与「样本真跑出两本册子」；`210/210` 通过。
  - 未新增域，没动 `coverage` / `themes`；`legacy.swing` 的 title / question / domains 本来就覆盖这一段，不用改。

- 验证：`--selftest` exit 0、`py_compile` exit 0、`semantics.json` 可 `json.load`、`git diff --check` exit 0、五个文件 `CR=False BOM=False`，新改的三个文件 `over2000=0`（总入口只剩既存 3 行超长）。实跑 `legacy swing` 确认四条样本都列出。

- 本轮未触发 ROM 取证；没碰产物层；没改 `check_docs.py`；没回查载具 / 特殊关卡换面。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果在看不到 GFX 时推断这一帧在干嘛。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- `notes/08-wof-cs-gaps.md` 记的是 C# 移植侧欠账，不是 wof 原机缺机制。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
