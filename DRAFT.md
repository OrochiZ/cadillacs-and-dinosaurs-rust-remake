# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `7f6e67a1`，三处未提交改动（`DESIGN_DIFF_NOTES.md` / `DRAFT.md` / `re/specs/lookup.py`），临时提交信息文件不存在。逐条核过 diff 确认是上一步验证后的内容；PowerShell 里 `git diff` 的中文乱码是显示层编码，用 Read 直读文件确认中文完整。该批已提交为 `d062b9d9`（把 wof 半边同一个 `4` 接回「数值没有全局意思」）。

- 提交后继续推进用户原话里「顺着 ANI → SPR → 判定框，虽然你看不见 GFX，但能猜出是在干嘛吧」：核实 `chain` 只是**一段固定说明**，喂不进数据；`frame` / `comp` / `box` / `attack` 各自能查，但真拿到一帧还得手工跑几条命令自己拼。缺的是「合起来」。

- 本格做成：
  - `lookup.py moment [10|12] <帧记录> [attack <8 bytes>]`：一次喂进同一帧的几份数据，合成「这一帧在干嘛」——身份 / 一拍多长 / SPR 指向 / 盒表说够得着谁 / 攻击记录说打中多疼 / 自己会不会被打。
  - 比 `chain` 多一层判断：攻击记录不是任何时候都能挂。抓投探测帧、受击 / 倒地 / 抓姿势帧、关盒帧喂进去会被拦下并说清理由；`+$58` 由状态代码按招式挂上，什么时候挂不归帧记录管。
  - 判据修准：`live` 不能只认 `kind == 4`，`frame_type 6` 是特殊 / 必杀攻击帧；盒索引按 SPEC 写成 `0x1A` 而不是十进制 `26`；w1 叠加层分支改成三支说清。
  - doc / `cmd_list()` / `cmd_chain()` 末尾 / `main()` dispatch 四处接上 `moment`；自测加 11 条，`207/207` 通过。
  - 总入口补两段设计判断：一拳不是一条数据，是身份、空间、后果三本册子在同一拍由对的对象对上；画面与判定根本是两套数据，判定框不跟着造型走。按 §94.23 算「场上没有一本总账」往细处走，不另算一条设计。

- 验证：`--selftest` exit 0、`py_compile` exit 0、`git diff --check` exit 0、四个文件 `CR=False BOM=False`，新改的两个文件 `over2000=0`（总入口只剩既存 3 行超长）。

- 本轮未新增 `semantics.json` 域，没动 `coverage` / `themes` / `legacy`（按 §94.23 不另算判断，无需扩索引）。未触发 ROM 取证；没碰产物层；没改 `check_docs.py`；没回查载具 / 特殊关卡换面。

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
