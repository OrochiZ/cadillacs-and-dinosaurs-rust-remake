# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：把讲两侧的证据底座接上 wof 半边（第二十八格）

**背景**：第二十七格 `3165d856` 已提交（wof 16 字节参数行解码，
67 域 / 532 条，182/182，工作区干净）。这一格做一次底座一致性核对：
用 PowerShell 读 `semantics.json` 扫九条 `legacy`，看每条挂了几个
`wof_` 域、`can_check` / `cannot_check` 有没有提到 wof。

### 扫描结果：两条真缺，三条是纪律不是漏

- `swing`（第三节）判断正文明确讲 wof 三帧锁依次解锁 3–5 人，
  可查域 8 个全是 dino 的帧 / 盒 / 攻击记录 ⇒ 真缺。
- `beat`（第一节）外推文第 473 行补充讲「定格是双方共同持有的一份
  时间（dino 三处同写、wof `+0x62` 双方同写）」，底座 13 域无 wof ⇒ 真缺。
- `values` 的 `can_check` 写「0 在 dino 是关盒 / wof 是合法表项」，
  靠 `box_index_zero` 一个域就覆盖两侧，不是缺（按 `wof_` 前缀数太粗，
  人工核过）。
- `continuity` 提 wof 是在 `cannot_check`（关卡脚本数量概括 + C# 空桩，
  按 wof 边界不转）；`crowd` / `difficulty` 主体是 dino census / 波次，
  wof 那半边按 §11.0 不臆断 ⇒ 这三条「没有 wof 域」是纪律，别硬塞。

### 落盘内容

- `semantics.json`：
  - `legacy.beat` 加 `wof_shake_left`，`can_check` 补「wof 那一拍由双方
    同写的 `+0x62` 一起数完」。
  - `legacy.swing` 加 `wof_shake_left` / `wof_atk_field` / `wof_reaction`，
    `can_check` 补 wof 半边能查什么，`cannot_check` 补「『能依次打到
    3–5 人』是注释读法、没有逐帧实测」守证据强度。
  - 没新增域 / 键，coverage / themes / probe 不用动。
- `lookup.py`：自测加 4 条断言（swing / beat 接上两侧、swing 的 wof
  半边真跑 `wof_attack ours`、按边界不转的三条没硬塞 wof 域），
  182 → **186/186**。
- `DESIGN_DIFF_NOTES.md`：`legacy` 入口段补一句「判断讲两侧的，底座
  也得跟到两侧」，并写明另三条「缺域」是纪律不是漏查。

**没有新增设计判断**：这两条只是把已经能查的数据接回已有判断，
按 §94.23 不重复计数。

**验证**：`--selftest 186/186`、`py_compile`、`git diff --check`、
CR=False / BOM=False、`over2000` 除 `DESIGN_DIFF_NOTES.md` 既存 3 行外全 0、
实跑 `legacy swing` / `legacy beat` 核过更新后的文案。

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
- `legacy` 是顶层索引不是 `domains`；每条必须同时写 can_check / cannot_check /
  probe，probe 必须能被 `--selftest` 真跑通；有 [O] 回源但没转成域的另带 source。
- 判断讲两侧的，底座也得跟到两侧；但「按 wof 边界不转」的那几条没 wof 域
  是纪律，别见零就补。按 `wof_` 前缀数域只是粗筛，`box_index_zero` 这类
  单域覆盖两侧，人工核过再判缺口。
- 每次加命令都要同步 doc 用法与 `cmd_list()` 末尾导航，自测留一条防回归。
- 工具报错先分「真问题」还是「我的判据不对」；**证据强度也要双向守**：
  不把 [I] 写成 [O]，也不把 [O] 级代码观察降成「叙事」。降级前先回源。
- 「缓存没登记」与「没有证据」是两种缺口，写 cannot_check 时必须选准一种；
  缓存后来补上了域，就得同步改 can_check，别让「查不到」那栏还留着旧说法。
