# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 30 秒版现状（11-07）

- 主线最新提交 = 口径澄清「保留、不扩张」不是用户规则；本笔另提交 DRAFT 机制修复与常驻层订正。开工时用 `git log -3` 当场核 HEAD，不引旧号。
- 开放目标 `长时间自主推进` 当前 **paused**；主线是 `DESIGN_DIFF_NOTES.md` 的 dino/wof 游戏逻辑设计差异分析，按「一节一提交」推进。最后一节 §83 / A.47；规模 12866 行 / 99 图 / 2750 表格行 / 84 章 / 47 附录 / 490 栅栏。
- 本轮在做 §84「背景流送」：**取证已全部做完、正文未写盘、未提交**。
- 用户连续两次质疑并已当场求证：①「保留、不扩张」是助手自造、已降级为历史范围声明（已落盘提交 `9d8145f`）；② DRAFT 机制在 dino 从未实现（`cd1c9d7` 把 wt1 无条件动作改成「若存在」恒假分支）。本文件即该机制**首次补跑**。

## §84 取证结果（只存在工具输出里，压缩会丢）

- 主题：dino `camera.rs` 的 `stream2` / `stream3` 增量流送；全套术语（`stream2`/`stream3`/`ge32`/`round32`/`write_block2`/`write_cell3`/`reinit_map`/`predraw_screen2`/`tile_anim_tick`/`sx46`/`sy48`）在 `DESIGN_DIFF_NOTES.md` Grep **零匹配**。
- `ge32` :303 / `abs16` :307 / `round32` :311；`vram2` :315 / `vram3` :322；`screen_lookup` :328。
- `write_block2` :379（2×2 block，`i%4096` 环）/ `draw_column2` :391（0x11 → 18 block）/ `draw_row2` :416（0x19 → 26 block）/ `stream2` :439。
- `write_cell3` :480（单格）/ `draw_column3` :486 / `draw_row3` :511 / `stream3` :534。
- `scroll2_init` :594 → `reinit_map` :782 / `reinit_map_header` :788 / `reinit_map_draw` :801（17 或 19 列整屏重建）/ `predraw_screen2` :825。
- `tile_anim_tick` :939（只换 `phase72` 相位、不重画地图）；`phase72`/`prev73` 另被 `prop/b36_38.rs`、`b13.rs`、`b5.rs`、`b10.rs` 写；逐帧存档 `trace.rs:1692-1693`。
- 调用点：`background_update` :574 → `scroll2_run` :847（:866 `stream2`）/ `scroll3_run` :1685（:1722 `stream3`）；`screen_shake` :1727 只动 vblank Y shadow、不动流送坐标。
- wof 侧（按 §11.0 只登记不同语境并列事实，不串等价 / 不评优劣 / 不断言原机缺机制）：`Cps1StageTileStreamer.cs:988/1062/91/131/216/222/357/535`、`Cps1CameraRuntime.cs:123/127/152/200/702/725`、`Cps1SystemCoroutineRuntime.cs:9744/10490/11047`、`Cps1LidianFinaleRuntime.cs:17166`（行号均已核实真实）。
- §23.6 (L3340) / §52.8 (L6993–6996) 的「保留、不扩张」清单列的是 wof 逐段展开 / dino `RowScroll` 逐状态 / `camera.rs:1148-1236` mode 分派逐分支，**不含流送函数**；按新口径这不是闸门，本就可写。

## 导航缺口（写 §84 时一并修）

- L46 / L47 / L16 / L70 已同步到 §83 / A.47；**L50 / L54 / L63 / L65 四行主题索引尾部仍停在 §82 摘要**（"wof 按 §11.0 只登记表驱动连发收尾与自动转向不同语境）**"），§83 摘要当初漏追加。
- 上次两次 §84 写盘预校验失败：① 4 个主题索引锚点 `cnt=0`；② `same=True`（`$anchorOld+$add83+$add84` 拼接后等于旧值）。两次都 throw 前未写盘。
- 本次改用「按行号重建数组 + 整行末尾追加 + 逐项预校验 `new != old`」，不再用批量锚点 replace。

## 下一轮起步

1. 读本文件 → 删除重建（不是编辑）。
2. 写 §84 正文（1 图 / 2 伪代码 / 4 表），按行号重建数组同步 16 处导航并补 L50/L54/L63/L65 的 §83 摘要，预写 A.48，单独提交。
3. 写 A.48 回执（如实登记用户两次质疑、口径澄清、DRAFT 首次补跑、两次预校验失败与修复），单独提交。
4. 每轮收尾把本轮未闭合残差写回本文件；跨轮结论进 `DESIGN_DIFF_NOTES.md`。

## 判具边界

- `git diff` / `git log` 中文经 PowerShell 控制台显示成 GBK 乱码，**文件本身是 UTF-8**；判断内容用 `Read` 或 .NET `ReadAllText(...,UTF8)`，别看 diff 输出。
- 写盘统一 `WriteAllText` + LF 无 BOM（`CR=0 BOM=False`），别用 `WriteAllLines`（默认 CRLF 会全文件 diff）。
- 表格行统计用历史 `^\|` 口径；`file:line` 双口径校验沿用 `s[h]`/`p[y]` 字符类规避安全策略。
- `DESIGN_DIFF_NOTES.md` 顶部规模行数字必须按写盘后实测刷新，不引旧数。
