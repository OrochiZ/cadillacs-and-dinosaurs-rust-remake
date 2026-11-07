# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**§88 开工版**：上一版是 `01a3f13` 收尾版（记 §88 起步候选），开工读过后删掉重建为本版定题；旧版残差已消费。

## 30 秒版现状（开工当场核）

- HEAD 序列：`fca39cf`（§87 定题 DRAFT）→ `11484c5`（§87 正文）→ `51e6823`（A.51 回执）→ `01a3f13`（收尾 DRAFT）。工作区干净。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**。
- 当前 `DESIGN_DIFF_NOTES.md`：**13727 行 / 103 图 / 2983 表格行 / 512 栅栏 / 379 表格块严格口径 0 不一致 / §0–§87 / A.1–A.51 正文定义 51 / 双口径不去重窄 1774 宽 1841 缺文件 0 越界 0 / 悬空 0 / CR=0 无 BOM**。顶部 L16 已是 `13727 行 ... 2983 表格行`，不引旧数。
- 上一轮两笔提交已登记两处提交前自修（§87 表格裸竖线 2→0；`file:line` 校验脚本口径漂移自修），A.51 回执完整。

## 本轮 §88 定题（先查重，不按零匹配排序）

**题目**：`enemy/class14*.rs` —— 一条脚本记录造出三个 pool A 对象，**谁是真身由 handle 地址排序的中位数决定**，两端降级成跟随的刀 parts；真身自己再走 30 态状态机与两张随机决策表。
一句话结论：这不是「一个敌人带两个挂件」，而是**生成阶段先占三个槽、按地址排一次序，中间那个才被写成会思考 / 会挨打 / 会被瞄准的本体，两端只留一个反查主体的句柄**。本体身份不是脚本指定的，是池分配结果决定的；三者的生命周期从此分叉：parts 每帧读主体的 mode 与「手里还剩几把刀」决定自己是否还活着、是否显示，主体死了 parts 当帧自毁。

**排除链（本轮六次印证 A.50.3「零匹配 ≠ 机制未展开」，其中四次是开工前查重）**：
- `player_weapon.rs` → §21 L2864–L3008 已展开拾取 / 空枪降级 / 分体动画，排除。
- `effect.rs` `raw_load` / `raw_tick` / `fx_tick_sprite_frame` / pool D 被动记录槽 → §50 L6631 / L6656 / L6703、L6540、§53、§81 L11289 已展开，排除。
- `effect/fxNN.rs` 逐类 → `fx_tally`(§80) / `fx_time_over`(§75/§76) / `fx_cloud`(§56) / `fx33`(§61) / `fx19`(§53) 已登记；余下多为逐类实例，无跨类新契约则不单独成节。
- hit spark 五个 spawn 入口 / `0x237E6` 跳表 / `fx_spark 0x924AA` → §58 L7816–L7925 已有五入口对照表与坐标算法，排除。
- `enemy/claim.rs` → §66 L9399–L9472 已展开跨帧认领、两表排他门、写四处对象头，排除。
- `flow/demo.rs` → §63 L8747–L8822 已展开 RAM clear / 1201 帧帧循环 / RNG 钉死 / 30 条流 / pad 顶替 / wof 三态剧本机，排除。
- `enemy/` 目录 72 个零提及文件绝大多数是逐类敌人实现（§41.7 / A.13 历史取材范围声明），逐类抄表不是新横切面；只有 `class14` 家族（6 文件）带「跨三对象协同」的组织契约。
- 表驱动 AI 决策的**共性**已在 §6 / L688 / L1112 / L1113（`0x4005C / 0x40118 / 0x40156`，rng×variant×距离×aggression 查 32 行表）登记；`class14` 的 `0x41BE8 / 0x41CD0` 双 decision、三槽转正、两阶段 init、parts 反查主体、30 态跳表 `0x407F8` **全部零匹配**。本节只写差异面，不重写共性。

**dino 取证行号**（`dino-rs/crates/dino-game/src/game/enemy/`）：
- `class14.rs:1-13` 文件头：pool A class 14（`+$20=0x38`，handler `0x4020E`）= BLADE（name 6 variant 0）/ RAZOR（name 0x14 variant 2）；`+$06` 状态机 0..0x3A 共 30 handlers 列在 `0x407F8`；**一条脚本记录三个对象**：init `0x40224` 再取两个 pool A 槽、排序三个 handle、中间那个转正，另两个成 class 60 跟随 parts；entrance（var26 低字节）8 档（walk in / stand 0x4B0 / 0x1E0 帧 / 上方跳入 / 跳到目标 / 带两把刀跳入 `0x403E8`）。
- `class14.rs:18-45` 字段表：`BUSY +$A0`（已承诺状态，不做新决策、不转身）/ `KNIVES_TO_THROW +$A1` / `KNIFE_LATCH +$A2` / `TURN_T +$A3` / `OLD_DIR +$A4` / `DIST +$A5`（目标 X 距离档 `0x3293C`）/ `TIMER +$A6` word / `PART_A +$A8` / `PART_B +$AA` / `PAUSE +$AC` / `MOVED +$AD` / `KNIVES +$BE`（0..2，负值由 parts 例程重置）。
- `class14.rs:48-58` mode 分派（`0 => c14_init` 等）；`:62-116` `c14_init 0x40224` 两阶段：`sub != 0` 直接转 `c14_init2`；`free_count() < 2` 或两次 `alloc()` 任一失败 → `enemy_free_pool_a` 整体放弃；把更新中的对象先放回槽 `std::mem::take`；三个 handle `(h, j1, j2)` 三次比较冒泡排序（`class14.rs:76-86` 注释：原机是符号扩展 word，池都在 0x8000 以上，故有符号 long 比较等价于无符号 word 序）；**中位数 `a1` 写成真身**（`live=1 / k20=0x38 / var26 继承 / dir / palette_override / X Y Z / PART_A=a0 / PART_B=a2 / sub=2`）；两端 `a0`、`a2` 写成 class 60 parts（`k20=0xF0`、var26 = 0 或 0x200、`anim_table=0x6FB6A`、`+$A0 = 0xFFFF0000 | a1` 指回真身）。
- `class14.rs:118-135` `c14_init2 0x402E4`：variant 决定 `(id, w84, anim_table)` = BLADE `(6, 0x18, 0x6DA40)` / RAZOR `(0x14, 0x50, 0x6DF2A)`；`box_table=0x103C00`、speed 7、`enemy_set_hp`、`enemy_pick_target`。
- `class14.rs:174` 每帧序列：`0x2B35A` → 掉刀 `0x40428` → parts `0x41D6E` → 场地钳制 `0x193E`；`:275` 另一处 `alloc()` 失败 `return`。
- `class14_entry.rs:1-3` 文件头：状态入口 `0x41278..0x41A1C`、两个决策 `0x41BE8 / 0x41CD0` 与 ROM 表 `0x73214 / 0x73414 / 0x73494 / 0x73514 / 0x73714 / 0x73914`、刀 parts 摆放 `0x41D6E`。
- `class14_entry.rs:18-35` decision 1 `0x41BE8`：speed 5、清 BUSY/BLOCK、`lib_distance_class`（`0x3293C`）→ DIST、`r = rand() & 0x1F`、`idx = (r<<3) + DIST + (variant<<7)` 查 `0x73214` 得 1..5 选 5 个状态入口。
- `class14_entry.rs:37-69` decision 2 `0x41CD0`：先 `c14_41c46`（同 facing 且随机命中 `0x73494`）→ 回 decision 1；否则 `r = rand() & 0xE8`、`idx = r + DIST + (variant<<7)`，按手里刀数选表（0 把 `0x73514` / 1 把 `0x73714` / 2 把 `0x73914`），查得 1..11 分派到 11 个入口（含 5 个 `c14_attack_start(0..4)`）。`:71-76` `c14_41c46` 判目标 facing 是否相同。
- `class14_states.rs:1-3` 文件头：`+$06` 状态表 `0x407F8`，30 项 0..0x3A（步长 2），handlers `0x40940..0x41154` 与 `0x40EBC`；每个 handler 是状态的一帧；状态入口负责写 `+$06` 与计时；原机 `bra 0x41BE8` 就是 decision。
- `class14_states.rs:10-42` `c14_state 0x407A2`：`act` 30 路 match（若干状态共用一个 handler，如 `0x1C|0x1E|0x20`、`0x28|0x2A`、`0x00|0x16`）；`:44-49` `c14_tick_timer`（`TIMER` 递减到 0 返回真）；`:51-56` 状态 0 / 0x16：走到目标旁 0x38 处、到点暂停，计时到 0 就 `c14_41be8` 重新决策。
- `class14_parts.rs:1-3` 文件头：class 60 两把刀 parts `0x580C6`、被击中且腾空时掉落的 class 34 刀 `0x5129E`、投掷刀 class 41 `0x55866`。
- `class14_parts.rs:13-66` `enemy_class60`：`mode 0` init（`box_table=0x103C00`、攻击 0x1E、`live=2`、`ATTACKING=0xFF`、`anim_table=0x6FB6A`、anim 0x22、`enemy_floor_collision`、转 mode 2）；`mode 2` `c60_alive` 读 `+$A0` 低 16 位解 `slot_of` 拿主体，**主体槽已不是 Enemy 或 mode>=4 就当帧自毁**；`knives == 0` 直接 return（不自毁、不显示）；第二把 part（var26 高字节非 0）在主体只剩 1 把刀时也 return；否则 `enemy_step` + `enemy_draw_check`。
- 上游并列：§50「地址即身份 / handle 是槽地址」、§43「`enemy_free_pool_a` 只清部分字段」、§66「独占写进双方对象头」、§13「census / target selection」、§6「表驱动 AI 决策共性」、§69 / §85 / §87「跟随对象反查宿主」同族但不同层。

**六条设计结论**：
① 一条脚本记录 = 三个池对象：`free_count() < 2` 就整组放弃，不是「能造几个造几个」；与 §76「池满丢弃 vs 下一帧重试」、§71 同族但这里是**原子三槽**。
② **真身由地址排序挑出**：三个 handle 三次比较取中位数，不是脚本指定、不是第一个 alloc 的槽。`PART_A / PART_B` 存的是另两个 handle，parts 的 `+$A0` 反查真身——三向互指。与 §50「地址即身份」正面呼应：这里连「谁是本体」都由地址决定。
③ 两阶段 init：`sub 0` 只做拆分与排序并写 `sub=2`，真身的 HP / box / 动画 / 目标要到下一帧 `sub 2` 才装；与 §42「生成帧不跑 AI」、§59「中间态是数据不是副作用」同族。
④ 三类生命周期分叉：真身跑 `+$06` 30 态状态机（每态一帧 handler，计时归零就回 decision）；parts 每帧读主体 mode 与 `KNIVES`，主体死 / 刀用完 / 只剩一把时第二把就隐去，主体 `mode>=4` 当帧自毁；掉落的刀（class 34）与投掷刀（class 41）另成对象。没有「parts 自己数帧」。
⑤ 决策是两张表 + 一个距离档：decision 1 用 `rng&0x1F`、decision 2 用 `rng&0xE8` 并按手里刀数换表，都要先 `lib_distance_class` 得 DIST、先判同 facing；`variant` 位移 7 把 BLADE / RAZOR 塞进同一张表的两半。共性已由 §6 登记，本节补「刀数参与选表」与「两个 decision 互为跳转」。
⑥ `BUSY` 字节把「已承诺本状态」写成显式门：进入状态后置位，decision 清位；与 §2 四层状态字节、§20 `Scene{state,sub}`、§39 连击锁同族，本节只登记 class 14 自己的用法，不串成等价。

**wof 侧按 §11.0 只登记不同语境并列事实**（四格都是既有注释 / 调用面复述）：`Cps1EnemySpawn.cs:1671-1676`（一次生成三个对象 `FFCCFC / FFCDDC / FFD07C`、ObjId `0x14 / 0x1E / 0x14`、FBA 与 CS 逐字节一致——**录像对拍语境**）/ `Cps1EnemyAI.cs:2973`（`0x11884` DmgReaction 0x08/0x10 → `0x11796`「分身替换族」入口）/ `Cps1EnemyAI.cs:3485-3503`（`0x121F4..0x12328` 受击「分身替换」主体、`0x1222C` 硬直递减 / 分身复制）/ `Cps1Actor2DRuntime.cs:26-28`（f=24 三个对象都进 state 0、`jsr 0xF98` 各 1 次）。**不串等价、不评优劣、不把未登记写成缺失、不据此断言原机缺机制**；wof 的「分身替换」是受击时复制，dino 的 class 14 是生成时拆分，语境不同；0 次 ROM 取证，§11.6 未触发；`_无对应ASM` 开关与 FBA 逐帧对拍按 §0 剥掉。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；临时片段用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s88_patch.txt` / `a52_patch.txt`。
- 大段中文 markdown 用 Write 落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → 按行号重建数组 → 逐项预校验 `cnt=1` 且 `new != old` → 一次 `WriteAllText`（`Join("`n")` + 末尾 LF，无 BOM）。
- **坑 1**：PowerShell 数组字面量里 `+$var+` 会解析错位；所有含 `+` 拼接的字符串先赋独立变量再进数组；写盘后核 L46 长度变化与 `EndsWith(' | 有效 |')`。
- **坑 2**：回执别写「`§N+` 引用 0」，改写「超出 §N 的章号引用 0」。
- **坑 3**：表格单元格禁止裸竖线（位或表达式改文字或 `\|`），精确表达式放非表格伪代码块。
- **坑 4**：`file:line` 全量校验必须**不去重**、不加 `(?<![\w/])` 后视、多根 basename 索引、扩展名正则用 `s[h]` / `p[y]` 字符类；去重 1245/1300、后视 1087/1135 都与历史 1774/1841+ 不可比，别相减。
- 导航固定 12 处：L16 七处（行数 / mermaid 数 / 表格行数 / `A.1–A.N` / A.N 条目 / A.N 位置 / `§0–§M 全部结论`）、L46 两处（章节列表 `/ §M |`、主题摘要 `；§M（…） | 有效 |`）、L47 两处、L50 / L54 / L63 / L65 各一处 `、**§M（…）**`、L70 一处 `、A.N`。回执追加时不改导航结构，只刷新 L16 行数与表格行数并补 A.N 正文定义。
- 校验固定项：片段逐行零缺失 / 表格块严格口径排除转义竖线 0 不一致 / 全量 `file:line` 双口径（不去重）零缺零越界且 HEAD 基线差等于新区引用数 / `CR=0 BOM=False` / `git diff -U0` 删除行逐条核为纯导航行 / 悬空章号 0。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；提交用 `git -c i18n.commitEncoding=UTF-8 commit -F`。
- 每块一提交：DRAFT 定题 → §88 正文 → A.52 回执 → DRAFT 收尾，四笔；顶部规模行、导航在 §88 提交时一次同步并预写 A.52。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
