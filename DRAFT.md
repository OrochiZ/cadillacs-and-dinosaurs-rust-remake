# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**§92 开工版**：上一版是 `9cbc552` 收尾版（记 §91/A.55 完成状态与 §92 起步），开工读过后消费完毕，旧版残差不再保留。

## 30 秒版现状（开工当场核）

- HEAD `9cbc552`，`git status --short` 为空。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**。
- `DESIGN_DIFF_NOTES.md` 实测：**14724 行 / 107 张 mermaid / 3222 表格行 / 540 栅栏 / §0–§91 / A.1–A.55 正文定义 55 / 表格块严格口径 412 块 0 不一致 / 双口径不去重窄 1885 宽 1952 缺文件 0 越界 0 / 悬空 >91 为 0 / CR=0 无 BOM**。顶部 L16 已是 `14724 行 ... 3222 表格行`，**不要引旧数**。
- `R:\Temp` 无残留；本轮开工按 `system-prompt.txt` 读了 `CODEBUDDY.md` → `9cbc552` 收尾版 DRAFT → `git log -8` / `git status --short`。

## 本轮 §92 定题（先查重，不按零匹配排序）

**题目**：`flow/skip.rs` + `game/mod.rs:328-346` —— **按住攻击或跳，过场快进三倍：快进的不是帧率，是「一轮任务」在一个 vblank 里跑几遍**。

一句话结论：**一个按键把「轮数」从 1 改成 3，而不是把动画播快**；所有按轮计数的 `sleep(n)` 因此约 n 轮就结束，而投币中断、输入 cooking / `prev` 快照、显示锁存仍每 vblank 只做一次。§47 / §64 只把 `skip_wait_rounds()` 登记为 `tick` 调度链的一格，本节展开它内部「什么按轮算、什么按 vblank 算」的契约。

**排除链（A.50.3 双向化，两个方向都核）**：
- **§47 / §64 调度链**：`skip_wait_rounds` / `0x9E38C` / `skip_tick` / `flow_round_start` 在主文件**有匹配**（L146、L163、L2740、L2806、L2812、L2842、L2845、L6359、L6380），但都是「一帧调度链的第 7 步 / lag 字段表 / 跨 vblank 续算点」的步骤名与字段清单，没写「按住键为什么能三倍、哪些工作不跟着快进」。这是「**有匹配 ≠ 已展开**」的又一次成组应用（A.54.2），与 §90 `drivers.rs` 同构。
- **§57 三类计时器 / 全局时间门**：那里 `scripted != 0` 是「挡住续关倒计时 / HUD / waveTimer」的暂停门；本节 `script.b4d8 & 1` 是「允许快进」的准入位（脚本动作 `0x28` 置、脚本结束清）。同一字节两条线，不合并、不串等价。
- **§60 长任务跨帧 / video frame 边界切断 / CUTS / 不模拟 CPU 时间片**：本节是「一个 vblank 塞几轮」的输入快进，不是长任务被边界切断；`ranking_cut` / `CUTS` / `task.wait` 续算点不重写。按 §0 把 `record.lua` / `game_clock` 记录合并剥掉，只登记 `skip_join_more` 属记录层、不写成设计差异。
- **§86 影片时间线 / §63 attract demo**：attract 计数在 handler 内不走、计数撞表只跑一个 handler；本节是 **in-game scripted 场景**按住键，不同阶段、不同机制；`profiles.rs` 的 1200 计数跨 1398 帧与 §86 同构，只作并列。
- **§81 打字机 fast / §14 输入边沿**：§81 是攻击键**边沿** `now!=before 且 ==0x10` 一次打完、按住或带方向不跳；本节是 cooked pad **电平** `w.input[i] & 0x30` 持续生效、方向不算、非在场英雄不算。同为「按键加速演出」，一个边沿一个电平，只作并列。
- **§55 续关倒计时**：`press & 0x30` 每按一次 `frames=60; seconds--`（按键一次换一秒）；本节是按住持续三倍轮数，不合并。
- **附录 A 工程路线**（两套循环 / lag 不可模拟 / FBA vs MAME）：按 §0 隔离存档，本节只谈游戏逻辑本意，不重提工程路线结论。
- **主文件零匹配面**：`SKIP_ROUNDS` / `skip_wait_active` / `skip_join_more` / `0x4CC` / `0x4D8 bit 0` / `SKIP_ROUNDS=3` / `2.2 轮` 全部零匹配；但定题依据不是零匹配，是上面七条语义查重。

**dino 取证行号**：
- `flow/skip.rs:1-9` 文件头：skip wait task `0x9E38C` 是**最后一个任务槽 0xF0**，每 pass yield；任务内核 `0x83C` 按槽序一轮一轮跑，VBlank 中断 `0x542` 让 sleeping task 的计数器每帧减一次（`0x5E2`：state 1、counter-1、到 0 变 state 4 ready）。按住攻击/跳时它把「每个 `sleep(n)` 在约 n **轮** 后结束」施加到**所有**任务上，而不是只加速自己。
- `flow/skip.rs:5-6` 准入四门：`G.$4CC`（in a game）、`G.$4D8 bit 0`（scripted control，脚本动作 `0x28` at `0x1DEA0` 置、`0x1E2BE` 脚本结束清）、在场英雄的 cooked pad `G.$16/$17/$18` 带 `0x30` 掩码、`+$00 of the hero not 0`。
- `flow/skip.rs:8-9` 效果：game task `0xA914`（`sleep(G.$4D6 & 15)`）每轮跑一个 game frame、fade task 每轮一步、system 与其它任务同样；脚本化行走 / 换区 / 登场约三倍速。
- `flow/skip.rs:11-16` CPU 时间上限：**一个 vblank 塞几轮不是代码里的数**，由一轮的 CPU 时间决定；录制给 2.2（换区淡出 `m517_ep1_jack`）、3.1（整段 lag 记录）、4（`ep6_jack`）、1.7（`ep7_3p` 重场景）；端口取固定 `SKIP_ROUNDS = 3`（`skip.rs:31`）。按 repo 侧注释如实登记，不评价移植完成度、不把这些实测当 ROM 表抄进正文。
- `flow/skip.rs:18-20` **什么算一轮**：`flow_tasks`（system / join / game / intro / tally）加 `run_fade_task` 各跑一遍，计数器与正常帧同一套；**不重复**的是中断工作（coin interrupt、input cooking 与 `prev` bytes、`Game::tick` 的 display latches），每 vblank 一次。
- `flow/skip.rs:22-26` `skip_join_more`：area change 期间（fade task 在跑，或相机在 area end `0x20C6A / 0x20CC0 / 0x20CE6` 三态）把多个 tick 并成一条 game clock 记录；这是**宿主侧记录口径**，按 §0 剥掉，不写成设计差异、不评价 rep 侧实现。
- `flow/skip.rs:33-41` `skip_wait_active`：`flow.in_game == 0` 或 `flow.script.b4d8 & 1 == 0` 直接 false；`(0..3).any(...)` 要求该英雄 `live != 0` 且 `w.input[i] & 0x30 != 0`。**读电平、不读边沿**；debug 分支 `G.$4AA` 未移植（按 repo 侧如实登记，不臆断）。
- `flow/skip.rs:43-55` `skip_wait_rounds`：先 `flow.skip_tick = skip_wait_active()`；`for _ in 1..SKIP_ROUNDS` 里若条件失效或 `flow.lag > 0` 就 break，否则 `flow_round_start()` + `flow_tasks()` + `run_fade_task()`。**最多补两轮，连第一轮共三轮**。
- `flow/skip.rs:57-61` `skip_join_more`：`skip_tick && (fade.task.is_some() || (cam.s2.mode == 1 && cam.s2.sub in 4|6|8))`。
- `flow/skip.rs:80-100` 单测 `the_condition_needs_a_game_the_script_flag_and_a_held_button_of_a_present_hero`：逐门钉死四条件；`0x20`（jump）也算，`0x0F`（纯方向）不算，英雄缺席不算，3P 在场算。
- `flow/skip.rs:102-123` 单测 `the_fade_of_a_skipped_scene_runs_three_steps_a_tick`：fade 16 步，第一个 tick 后 `16-3`、第二个 `16-6`、松手后 `16-7`；`skip_tick` 随松手变 false。**这是「快进 = 轮数 ×3」最硬的行为证据**。
- `flow/skip.rs:125-140` 单测 `skip_join_more`：无 fade / 无换区时 false，相机 `mode=1,sub=4` 或 fade task 在跑时 true，`skip_tick=false` 时 false。
- `game/mod.rs:328-346` `tick()` 全序：`cam.display_y2/y1` 快照 → `w.sounds/snd_reqs.clear()` → `flow_frame()`（第一轮）→ `run_fade_task()` → **`skip_wait_rounds()`（额外轮）** → `cam.latch_scroll(regs)` / `sprites.latch()` / `pal.latch()`（**每 vblank 一次、在额外轮之后**）。注释明写视频硬件显示的是两帧前的 scroll X / sprite list、一帧前的 scroll Y 与 layer regs。
- `game/mod.rs:348-355` `game_frame()` 序：`rank_tick / objects_update / collision / hud_update / build_sprite_list`，是「一轮」内部的一个 game frame，§47 已展开，本节不重写。

**七条设计结论**：
① **快进的准入是四个条件同时成立且读电平**：`in_game`、`script.b4d8 & 1`、cooked pad `0x30`、该英雄 `live`；与 §81 打字机 fast 的边沿判据只作并列（一个边沿一次打完、一个电平持续三倍）；方向键不算、非在场英雄不算。
② **快进不改变动画帧率或时间常数，而是把「一轮任务」在一个 vblank 里跑三遍**：`tick` 先 `flow_frame()`、`run_fade_task()`，再由 `skip_wait_rounds()` 补最多两轮 `flow_round_start + flow_tasks + run_fade_task`。所有按轮计数的 `sleep(n)` 约 n 轮结束；fade 16 步 6 个 tick 走完，单测钉死 `16-3 / 16-6 / 松手 16-7`。
③ **哪些工作不跟着快进**：投币中断、输入 cooking 与 `prev` 字节、`display latch`（`latch_scroll` / `sprites.latch` / `pal.latch`）每 vblank 只在 `tick` 尾部做一次，且**在额外轮之后**。所以按住键期间新按下的边沿仍按 vblank 采样，不会因第三轮被读三次变成三次按下；显示锁存的一 / 两帧延迟（§45 / §56）也不被压缩。这是把「按轮算」与「按 vblank 算」拆成两层。
④ **三不是常数而是实测中值**：原机「一个 vblank 塞几轮」由 CPU 时间决定（2.2 / 3.1 / 4 / 1.7 随场景负载），端口取固定 `SKIP_ROUNDS=3`；`flow.lag > 0` 时额外轮立即停。按 repo 侧如实登记，不评价移植完成度、不把实测数值当 ROM 表抄进正文。
⑤ **skip 是最后一个任务槽 0xF0 且每轮 yield**：它不改任务槽顺序，只在自己这一轮里请求「再跑一轮」；system / join / game / intro / tally / fade 全部按原顺序重复，没有哪个子系统被单独加速。与 §86「计数撞表只跑一个 handler」不同路：那里计数不走，这里计数照走三遍。
⑥ **准入门 `script.b4d8 & 1` 与 §57 的 `scripted` 门同字不同用**：§57 是「挡住续关倒计时 / HUD / waveTimer」的全局暂停门；这里是「允许快进」的准入位，由脚本动作 `0x28` 置、脚本结束清。同一字节两条线，不合并、不串等价。
⑦ **资源门与边界**：`skip_join_more` 把 area change 期间的多个 tick 并成一条 game clock 记录，属宿主侧记录口径，按 §0 剥掉；`mame_check.rs` 的 `ranking_cut_report` / `record.lua` 同属宿主层，不展开；`G.$4AA` debug 分支未移植按 repo 侧如实登记、不臆断。本节不写成「dino 有三倍速系统」这种完成度判断，只登记源码注释钉死的原机节拍。

**wof 侧按 §11.0 只登记不同语境并列事实**（四格都是既有注释 / 调用面复述；FBA 实测 / CS 卡值 / 逐帧对读 / 置信度等宿主对拍内容按 §0 剥掉）：
- `Cps1EventObjectRuntime.cs:5088-5090`：`对话框_B00_展开_可能对应ASM_56314` 注释「上一个对白协程仍在等待且 F2 非零时，本次展开以四倍步长推进，并把 E1 置为 3」，语境 = **对话框展开的几何步长**。
- `Cps1EventObjectRuntime.cs:5271-5274`：`对话框_B06_收起_可能对应ASM_564D0` 注释「D0/D1/D2 由 B00 算出后传入，不是硬编码」，语境 = **对话框收起的 delta 步长**。
- `Cps1EventObjectRuntime.cs:8490-8491`：`0x563F8`（对白快进：`OBJ24-8` 写 `0xFF7F1F`）与「剧本 `cnt`（`0xFF7F10`）拿不到快进追加」，语境 = **剧本计数器**。
- `Cps1EventQueueTask.cs:61-66`：`0xD000` 每处理一个事件 `trap#4` 让出、下一轮 `0x0700` 再取，「一帧内消费几项取决于本帧扫了几轮 0x0700」，语境 = **事件队列每帧消费量**。
- 四格**不串成等价、不评优劣、不把未登记写成缺失**；wof 侧未见「按住攻击/跳让整条任务轮跑三遍」的直接注释，不臆断、不据此断言原机缺机制；0 次 ROM 取证，§11.6 未触发。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；临时片段用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s92_patch.txt` / `a56_patch.txt`。
- 大段中文 markdown 用 Write 落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → **按行号直接对数组元素就地赋值**（坑 5）→ 逐项预校验 `cnt=1` 且 `new != old` → 一次 `WriteAllText`（`Join("`n")` + 末尾 LF，无 BOM）。**写盘 / 校验都落 `.ps1` 再执行**，不用长命令行 here-string。片段首行空 + 末行 `---`。
- 坑 1：数组字面量里 `+` 拼接解析错位，含 `+` 的字符串先赋独立变量；写盘后核 L46 长度变化与 `EndsWith(' | 有效 |')`。
- 坑 2：回执别写「`§N+` 引用 0」，改写「超出 §N 的章号引用 0」。
- 坑 3：表格单元格禁止裸竖线；精确表达式放非表格伪代码块。**表格块严格口径必须先剥离转义竖线 `\|`**（A.55.3，上一轮误报 5 块的教训）。
- 坑 4：`file:line` 全量校验**不去重**、无 `(?<![\w/])` 后视、多根 basename 索引、`s[h]` / `p[y]` 字符类；OOB 用「任一同名候选文件行数覆盖即通过」；悬空阈值随最大章号调为 > 92。**校验脚本属一次性脚手架，用完即删，需要就重建；重建时按 `s91_verify.ps1` 修正后口径，别再漏剥 `\|`**。
- 坑 5：导航替换别用 `[ordered]@{}` 存数字行号再 `ContainsKey($i+1)`（int）查；改 `$LA[$ln-1]=$line`。写盘后核 L16 新数字、L46 长度与 `EndsWith(' | 有效 |')`、四处主题索引 `§N` 命中、L70 `A.N` 命中、diff 删除恰为 8 条导航行。
- 导航固定 12 处：L16 七处、L46 两处、L47 两处、L50 / L54 / L63 / L65 各一处、L70 一处。回执追加时不改导航结构，只刷新 L16 行数与表格行数并补 A.N 正文定义。
- §92 摘要（L46 与四行主题索引共用，禁裸竖线）：`§92（按住攻击或跳过场快进三倍 / 快进的不是帧率 是在一个 vblank 里把一轮任务跑三遍 / 准入四门 in_game·script.b4d8 bit0·cooked pad 0x30·在场英雄 且读电平不是边沿 / tick 先 flow_frame 再 run_fade_task 再 skip_wait_rounds 补最多两轮 / 按轮计数的 sleep 约 n 轮结束 fade 16 步 6 tick 走完 单测钉死 / 投币中断·输入 cooking 与 prev·display latch 每 vblank 只一次 不被压缩 / SKIP_ROUNDS=3 是实测 2.2 到 4 的中值 flow.lag 大于 0 立即停 / skip 是最后槽 0xF0 每轮 yield 不改任务槽顺序 / script.b4d8 与 §57 scripted 暂停门同字不同用 / wof 按 §11.0 只登记对白展开四倍步长·收起 delta·剧本 cnt 快进追加·事件队列每帧消费量不同语境）`
- 校验固定项：片段逐行零缺失 / 表格块严格口径 0 不一致 / 全量 `file:line` 双口径零缺零越界且 HEAD 基线差等于新区引用数 / `CR=0 BOM=False` / `git diff -U0` 删除行逐条核为纯导航行 / 悬空章号 0 / 写盘后导航命中复核。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；提交用 `git -c i18n.commitEncoding=UTF-8 commit -F`。
- 每块一提交：DRAFT 定题 → §92 正文 → A.56 回执 → DRAFT 收尾，四笔；顶部规模行、导航在 §92 提交时一次同步并预写 A.56。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
