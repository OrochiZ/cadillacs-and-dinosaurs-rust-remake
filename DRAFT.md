# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：把开工时漏扫的 HANDOFF 目录收口（第十一格）

**背景**：`88b185a6`（SPR composition 解码）与 `49332e74`（把「一拍摆成
什么样」接回外推文）已提交，工作区干净。开工扫 `re/specs/**/*.md` 时
核过 `CONTEXT.md` / `flow/ENDING.md` / `enemy/B50-B76.md`，还剩六份
`HANDOFF.md` 没核；按「检索范围本身会漏目录」的教训，这一格收口。

### 核到什么

- 六份标题与章节（Ported / Stubbed / Next steps / Known issues / 验证记录 /
  函数地址 / 调用点）一致：都是**移植开发阶段的工程交接**，不是玩法数值表。
  用户已明说「本 rep 目前不是移植开发阶段而是回顾分析」。
- `anim/HANDOFF.md` 里那张 pool C 效果类编号表（`0x00..0xA4` 的 handler
  地址与 spawn 调用点）多数意义未明；少数点名的是特效对象（hit spark /
  水花 / 火焰 / 水波），不是「取值 → 抽象意义」的稳定玩法语义。
  按「用途未明不从字段名猜」不转。
- 另外三份此前已划界：`flow/ENDING.md` 结局专属演出、
  `enemy/B50-B76.md` Boss 登场对白服务 → 特殊段落不构成通则；
  `CONTEXT.md` 的 `pool_tag` 早已收进 `coverage` 第 8 组。

### 落点

- `re/specs/semantics.json` 的 `coverage.not_registered` 加一条：
  HANDOFF 六份是工程台账、不是玩法表，pool C 类编号多数只给地址与
  调用点；**已核过一遍，别再当漏查重复翻**。9 → 10 条。
- `re/specs/lookup.py` 自测加一条断言固化这条边界，82 → **83/83**。
- 没有新增语义域：`coverage` 仍 58 域 / 445 条、缺 0 多 0，
  `themes` 六类不动。

### 实跑验证

- `--selftest` 83/83；`py_compile` OK；
  `coverage` 输出完整、索引一致性不变。
- 改动两文件 `CR=0 BOM=False`、新增行 `over2000=0`；
  `DESIGN_DIFF_NOTES.md` 的 3 条超长仍是既存 57 / 89 / 154 行；
  `git diff --check` exit=0。

### 边界

- **0 次 ROM**；只读 rep 内文件与离线脚本，未碰 `g:/wof/wt1` 源码。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 假红，
  不改 `CLAUDE.md` / `.gitignore`。
- 不恢复「以 ROM 审 repo」框架；不把 `[I]` 写成 `[O]`；不从字段名猜意义。
- 载具 / 特殊关卡 / 单个 Boss 专属演出不构成通则，不往那里钻。

### 长期口径（细则在耐久层，不在本文件展开）

- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。
  Stop hook 是客户端自动重发催办，**不直读 goal 状态**；按「继续合理授权工作」直接做。
- 不写「下一格 / 短期不再动笔」当收尾；提到方向就当轮把第一步做掉。
- 交付一律**说人话**：人类理解中的游戏设计，不报内部编号、校验数字当主体。
- 产物层无分析意义；ROM 主要服务于 data 调查，仅在 `wof_cs` 非常可疑时才核实。
- 写盘 LF 无 BOM；提交信息走 `git commit -F` 临时文件随后清理。
- 新增语义域必须带 source / scope / tag；`coverage.registered` 与
  `themes.list[*].domains` 都必须覆盖所有域且每域只归一处。

## 收尾

- 校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、
  `git status --short`；`git commit -F` 后 `Remove-Item` 临时信息，再复核干净工作区。
