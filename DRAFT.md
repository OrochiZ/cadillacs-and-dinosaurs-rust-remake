# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：从「一招的后果」到「九条判断的证据底座」（第二十～二十二格 + 一次入口修订，四次提交）

**背景**：用户「继续」。前几格在做设计判断（时间 / 空间维度），本轮回到用户
反复强调的真实任务「把各种表数值的抽象意义都转成缓存」。开工先核：六份 SPEC
成表已转过一轮（64 域 / 516 条），HUD 消息环按 02 卷 §26「保留、不扩张」，
enemy SPEC §17 是逐 class 专属状态机，`not_registered` 12 条边界都站得住。

**找题过程（先验证真空白，不猜方向）**：sound / flow 两份 SPEC 的成表都已在
缓存里；读 `frame` / `infer` / `chain` 发现真实断口——`frame` 读出「攻击盒 #2」，
`box` 却要人手敲六个 i16，`attack_field` / `box_field` 只有字段偏移语义，
没有「一招的完整后果」成品。回源 anim SPEC §4.1 / §4.5：明写 Jack 两个示例
盒的六个 i16、三拳逐字节攻击属性记录；`jack_anim_set1` 里 `$58 = 0/2/4`
正指这三拳，`attack_id` 是 `$58` → 招名（14 条，只有 0/2/4 有逐字节记录）。

### 第二十格（`6cd75d37`，已提交）

- `semantics.json` 新增 `jack_attack_record`（键 `$58=0/2/4`，带 `k0/k1/k2`
  alias 与 `bytes`）、`jack_box_example`（`0x02` / `0x1A`）两域，均标
  `dino / Jack only`、带 source / [O]，note 写明 reaction 6 是 [I]、示例不套
  别人；coverage / themes 同步补齐 → 66 域 / 521 条。
- `lookup.py` 新增 `attack <8 bytes>`（自动认出 k0/k1/k2、并排讲三拳代价递进、
  未登记直说不猜）；`frame` 命中示例盒带出形状（限定 Jack）；`chain` 补第四环。
- `DESIGN_DIFF_NOTES.md` 补新查法 + 三拳代价递进落点（§94.23 不重复计数）。
- 自查收紧：去掉 k0 重复；「才不会被掐掉」的因果推断改成「按 input_buffer
  的读法」，reaction 6 明标 [I]。自测 115 → 129。

### 第二十一格（`35596e27`，已提交）

- `anim_id 1 4` 只说「终结拳，对齐查 attack_id」，没把人带到刚补的后果。
  `cmd_anim_id` 从段意义里的 `$58 = N` 查 `attack_id` 招名、查
  `jack_attack_record` 逐字节记录，直接打印后果并给 `lookup.py attack <bytes>`；
  没有逐字节记录的 `$58` 档位直说在 ROM 里、不猜；没写 `$58` 的伸臂 / 命中
  变体说明「攻击记录随主招，不另配数值」。自测 129 → 132。

### 第二十二格（`2df148f6`，已提交）

- 外推文九节、逐拍还原、证据边界、时间 / 空间维度判断都核过，继续加设计判断
  会注水；改找结构性缺口：`GAMEPLAY_LEGACY.md` 九条判断和 `semantics.json`
  的 66 域目前是两张皮，`themes` 按玩法问题分组，没说「这句判断能查到什么、
  查不到什么」。
- `semantics.json` 新增顶层 `legacy`：九条，每条带 key / title / question /
  domains / can_check / cannot_check。关键不是列域名，而是**必须写清查不到
  什么、为什么**——玩家实感无逐帧 trace、rank / aggression 是量按 §94.3 不转、
  wof 民间资料四列未验、当代同类做法是外推观察不占域。
- `lookup.py` 新增 `legacy [key]`（无参列九条，带 key 只展开一条），doc 与
  dispatch 同步；`DESIGN_DIFF_NOTES.md` 补入口说明，标明是证据底座盘点、
  按 §94.23 不重复计数。自测 132 → 139/139；实跑 `legacy` / `legacy difficulty`
  核过全量与单条。

### 入口一致性修订（随本次提交落地）

- 审计 doc 用法与 `main()` 分发，发现 doc 第 9 行把「无参数」误写成「列出
  所有可查的域」；实际无参数打印用法说明，列域是 `list` 命令。另发现
  `list` 末尾提示还停在 `chain` / `spawn`，没提后来加的 `attack` / `script`
  和三个索引 —— 这是压缩恢复后第一眼看的入口，不能停在旧能力上。
- 修 doc 加 `lookup.py list` 行；`cmd_list()` 末尾改成完整导航（解码命令 +
  `coverage` / `themes` / `legacy` 三个索引）；自测加 2 条防回归，139 → 141/141。

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
  每条必须同时写 can_check 与 cannot_check，外推观察不占域。
- 每次加命令都要同步 doc 用法与 `cmd_list()` 末尾导航，自测留一条防回归。
