# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：把「能查到什么」从声明变成真跑的样本（第二十三格；本轮此前四格已提交）

**背景**：用户「继续」。本轮此前四格把「看到数据 → 知道意义 → 接回设计判断」
接成链：`6cd75d37` 补 Jack 三拳攻击记录与示例判定盒 + `attack` 命令；
`35596e27` 给 `anim_id` 接上「这一拳的后果」导航；`2df148f6` 给外推文九条
判断建 `legacy` 证据底座；`a34bfc31` 修 doc 与 `cmd_list()` 两个入口。
缓存 66 域 / 521 条，自测 141/141，工作区干净。

**这一格的问题**：`legacy` 九条的 `can_check` 只是作者写的声明，没验证过；
按「声明不算证明」，逐条核它在 66 个域里到底有没有取值支撑。

### 查出来的真问题（不是猜）

- 只在 `domains` 的 label / note / values 里数关键词（排除 `legacy` 自己写的字）：
  「左右人数」「包抄」「每帧清」「名单」「准入门」「硬直门」「闪白」
  「群体命中锁」全部 0 次；「六个」只出现在 `box_field`（6×i16）、
  `enemy_ai_state`、`dino_script_action`（41 项），都不指接近槽。
- ⇒ `legacy.crowd` 把「六个接近槽 / 按上一帧左右人数定包抄 / 名单每帧清空 /
  各条链自带准入门」写成能查，其实是 enemy SPEC §14 与 05 卷 §78 的**叙事结论**；
  `legacy.feel` 把「wof 一字节兼硬直门 / 闪白 / 群体命中锁」写成能查，
  其实缓存只登记了同一字节在不同链里的字段语义。两处都属「把概括固化」。

### 落盘内容

- `semantics.json`：两条的 `can_check` 改窄成缓存里真有的取值
  （class 2 AI 状态逐档 / 六种入场 / 几人局与难度门 / 波次收尾 / 相机锁；
  八字段攻击记录 / wof 两张参数行字段语义 / 武器耐久 / 掉落码），
  落空的说法连同理由挪进 `cannot_check`；`legacy.note` 补「probe 是真跑样本，
  can_check 只写真有取值或真有命令能翻出来的东西，叙事结论一律放 cannot_check」。
- 九条各加 `probe`（argv + expect）：`frame_timer bit7=1` / `input_buffer $AD` /
  `frame 10 ...` / `wof_reaction 14` / `enemy_ai_state 2` / `wave_ctrl_r4 0` /
  `dino_script_record +4` / `attack_field +3` / `collide 4`。
  用 Python 脚本一次精确插入并断言每处唯一命中，未重排 JSON 格式。
- `lookup.py`：`cmd_legacy` 单条视图打印可跑样本；`--selftest` 里
  `capture(main, probe["argv"])` 逐条实跑并断言 expect，再加
  「crowd / feel 已降级」「九条 probe 都有 argv 与 expect」等断言。
  141 → **153/153**。
- `DESIGN_DIFF_NOTES.md` 补一段：这两条判断目前靠的是代码叙事不是可查数据，
  读外推文要放在另一档；按 §94.23 不重复计数。

**验证**：`--selftest 153/153`、`py_compile`、`git diff --check`、
CR=0 / BOM=False、新增行 `over2000=0`（`DESIGN_DIFF_NOTES.md` 那 3 行是既存）、
实跑 `legacy crowd` / `legacy feel` 核过降级后文案。

### 长期口径（细则在耐久层，不在本文件展开）

- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。
  Stop hook 是客户端自动重发催办，**不直读 goal 状态**；按「继续合理授权工作」直接做。
- 不写「下一格 / 短期不再动笔」当收尾；提到方向就当轮把第一步做掉。
- 交付一律**说人话**：人类理解中的游戏设计，不报内部编号、校验数字当主体。
- 产物层无分析意义；ROM 主要服务于 data 调查，仅在 `wof_cs` 非常可疑时才核实。
- 写盘 LF 无 BOM；提交信息走 `git commit -F` 临时文件随后清理；新提交不 amend。
- 新增语义域必须带 source / scope / tag；`coverage.registered` 与
  `themes.list[*].domains` 都必须覆盖所有域且每域只归一处；
  离散编号不连成范围；位域 / 字段偏移域继续被 `collide` 排除。
- 示例数据（Jack 专属）一律带角色限定，不套到别的角色 / 敌人；盒索引要连盒表一起读。
- `legacy` 是顶层索引不是 `domains`，不影响 coverage / themes 的一一对应；
  每条必须同时写 can_check / cannot_check / probe，叙事结论不进 can_check，
  外推观察不占域；probe 必须能被 `--selftest` 真跑通。
- 每次加命令都要同步 doc 用法与 `cmd_list()` 末尾导航，自测留一条防回归。
