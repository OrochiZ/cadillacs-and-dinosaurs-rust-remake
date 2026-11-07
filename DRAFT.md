# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**§89 开工版**：上一版是 `258487f` 收尾版（记 §89 起步候选），开工读过后删掉重建为本版定题；旧版残差已消费。

## 30 秒版现状（开工当场核）

- HEAD `258487f`，`git status --short` 为空，工作区干净。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**；本轮提交只证明持续推进。
- 上一轮 7 笔（§87 / A.51 / DRAFT 收尾 / §88 定题 / §88 / A.52 / DRAFT 收尾）已全部落盘。
- 当前 `DESIGN_DIFF_NOTES.md` 实测：**13956 行 / 104 张 mermaid / 3037 表格行 / 518 栅栏 / 表格块 387 块严格口径 0 不一致 / §0–§88 / A.1–A.52 正文定义 52 / 双口径不去重窄 1793 宽 1860 缺文件 0 越界 0 / 悬空 0 / CR=0 无 BOM**。顶部 L16 已是 `13956 行 ... 3037 表格行`，**下一轮不要引 13892 / 3018 旧数**。
- `R:\Temp` 无残留。

## 本轮 §89 定题（先查重，不按零匹配排序）

**题目**：`enemy/class6*.rs` —— 舌头不是主体的一段动画，而是**另一个 pool A 对象**；主体用一个字节广播四态（伸 / 抓 / 收 / 收回），舌头按这个码**每帧拼一条长度随距离变化的 raw sprite list**，抓住英雄送回嘴边，主体同时按计时扣血。
一句话结论：这是「**主体不画自己会变长的身体部件，而是派一个独立对象出去；那个对象自己没有 AI，只在每帧读主体的一个状态码，按码决定伸多长、抓没抓到、什么时候回来**」。与 §88「三槽排序定真身」不同：这里两槽按 handle 大小分工（小的当舌头 class 0、大的当主体 class 0x18），且**主体与舌头互相写对方的状态字节**——主体写 `+$C3` 命令，舌头写回 `+$C2`（抓住）/ `+$C4`（送到嘴边），主体再据此推进自己的 step、每 0x1E 帧扣 1 HP。

**排除链（本轮语义查重，继续印证 A.50.3）**：
- 上一版 DRAFT 的 `class6_*` 候选里，**「认领地上道具 / 8 格胃环 / 吐回」已在 §66.4（L9439–L9498）完整展开**——`0x3AFFA` / `0x69EE` / 类别最低 / `+$AF` / `+$D0` / `0x3B086` 全有明写。**这是又一次「零匹配 ≠ 未展开」**：`class6_eat.rs` 不能写，本节只写舌头。
- **§24 通用投技**（双向互检联合状态机 / 挣扎计时 / 投掷多步 / `enemy_holder_tag`）已展开，但那是「两个活对象互检状态字节」的通用协议；本节是「一个可伸缩的**显示 + 判定**对象由主体广播状态码驱动」，不重写 §24、不把舌头写成投技变体。
- **§88 三槽转正**（`class14`）已展开，本节是**两槽按大小分工**（`min → class 0 舌头` / `max → class 0x18 主体`），且主体是被脚本记录造出来的那一个槽、自己 `alloc` 出第二个槽，不是一次造三槽取中位数。形态不同，不合并。
- **§50 pool D 借用** / **§81 pool C raw sprite 四态** 已展开：本节舌头也借 pool D special slot（`draw_special_alloc 0x48A8`）存**动态长度的精灵表**，但 §50 记的是「pool D 无独立 pass、被 pool B 借用」的总表结论，§81 是 pool C class 28 的定长四态；这里是「每 16 像素一段、按 `距离>>4 + 2` 改写 count word」的**可变长度拼接**。只作并列，不串等价。
- 上轮已排除：`player_weapon.rs`(§21)、`effect.rs` raw/pool D(§50/L6540)、`fxNN` 逐类、hit spark 五入口(§58)、`claim.rs`(§66)、`demo.rs`(§63)、`class14` 共性(§88)、表驱动决策(§6)、投技通用(§24)。

**dino 取证行号**（`dino-rs/crates/dino-game/src/game/enemy/`）：
- `class6.rs:1-6` 文件头：pool A class 6 = Bludge（`0x39272`，7826 字节）与 class 0 Part 0（`0x33334`）；Bludge 是蜥蜴人恐龙突变体，mode 0 init 与槽配对 `0x3929C`、四入口 `0x393BA`、hop AI `0x39656`、受击 `0x3A1C8`、死亡 `0x3A1E2`；**Part 0 是配对的舌头控制器**。
- `class6.rs:17-24` `enemy_class0_part 0x33334`：舌头三态 `mode 0 init / 2 run / _ free`；`:26-73` `enemy_part0_init 0x3334A` 先读 `+$A0` 父 handle、查父 `k20 >> 8 == 0x18` 则自毁；`draw_special_alloc 0x48A8` 失败则**把父对象 mode 写 6 连带 free**（`:41-47`）；成功则清 special slot 128 字节、拷 `0x3375C` 模板（`:76-85` `enemy_part0_copy_template`）、`+$A4 = special_handle + 12` 指向 list 的 count word、`frame = slot_frame`、`box_table = 0x337EA`、`draw_flags = 0x70`、可见。
- `class6.rs:87-91` `enemy_part0_free`：先 `draw_special_free 0x498C` 归还 pool D 槽，再 `enemy_free_pool_a 0x48FC`。
- `class6.rs:97-116` `enemy_class6 0x39272`：mode 2 按 `sub` 分 `0 alive / 2 hit / 4 grab_state(0x3A0B4) / 6 grabbed(0x2B35A)`，尾随 `enemy_clamp_to_playfield 0x193E`；mode 4 dying / mode 6 free。
- `class6.rs:118-127` `enemy_c6_mode0 0x39286` 按 `sub` 四阶段：`0 alloc_pair / 2 init / 4 entrance / 6 entrance_end`。
- `class6.rs:129-189` `enemy_c6_alloc_pair 0x3929C`：**一次 `enemies.alloc()` 再取一槽**，注释 `:138-139`「a0 恒为 max(h,new_h)、a1 恒为 min」；`h <= new_h` 时当前槽变小 handle 当 Part 0（class 0 / sub 0 / `+$A0 = bludge_h`）、新槽当主体（class 0x18 / sub 2 / `+$C0 = part0_h`，继承 variant/dir/XYZ/drop）；反之当前槽当主体、新槽当 Part 0。**两向互指**：舌头 `+$A0` → 主体，主体 `+$C0` → 舌头。
- `class6.rs:191-241` `enemy_c6_init 0x392FE`：主体也 `draw_special_alloc`，清 16 字节、`+$D2/+$D4 = spec_handle+16`（胃环写指针 / 结束）、`+$D6/+$D8 = 0`；`id=0x10`、anim `0x3A234`、box `0x103000`、按等级设速度与 HP、`stun=10`、选目标 `+$76`、贴地、`sub += 2`。
- `class6.rs:243-254` `enemy_c6_entrance 0x393BA` 按 variant 低字节四入口；`:256-287` 入口 2 后方弧线跳（vy 0x400 / ay -0x48 / vz -0x100 / 20 帧）。
- `class6_tongue.rs:1-4` 文件头（最关键）：Part 0 舌头由主体字节驱动——`+$C3` = 1 伸出 / 2 抓住英雄 / 3 收回 / 0 在内；`+$C2` = 1 有英雄被抓；`+$C4` = 1 已送到嘴边。舌头是 **pool D block（`+$98`）里的一条 raw sprite list，`+$A4` 指向 count word，每 16 像素一段**；速度 0x600、回收 0xA00，最长 `0xC8` 像素，box 1（`0x337EA`）碰到英雄就抓。
- `class6_tongue.rs:9-13` 常量：`TIP 0x337DA` 一段 8 字节、`HELD 0x337E2` 抓住英雄后覆写第一段 8 字节、`BOX_TABLE 0x337EA`。
- `class6_tongue.rs:16-54` `enemy_part0_run 0x333D0`：读父 `+$A0` 解 `slot_of`，父 HP=0 或 mode>=4 即自毁；父 `kind==0xE` 或 `(mode,sub)==(2,2)` 时清 `+$C3`；`c3 = 父.+$C3`，与本地 `+$A6` 不同就 `act=0` 重开；按 `c3` 分派 `1 part0_out / 2 part0_hold / 3 part0_back`；可见则进 draw list、进 hurtable 列表。
- `class6_tongue.rs:60-97` `part0_out 0x33444`：act 0 时从主体 facing ±0x50 / Y+0x30 起步、vx ±0x600、重置 list 为 1 段；之后 `motion` + `part0_limit`（`:145-151` 距离 ≥0xC8 就写父 `+$C3=3`）+ `part0_count`（`:172-176` `count = |距离|>>4 + 2`）+ `part0_touch`；碰到英雄且 `part0_can_grab` 成立则 `part0_grab`、写父 `+$C2=1 / +$C3=2`、本地 `+$80=0x64`（100 帧）、list 首段换 `HELD`；不成立就 `+$C3=3` 收回。
- `class6_tongue.rs:99-110` `part0_hold 0x334E4`：目标 `action != 0x40` 就 `part0_release`；100 帧倒计时到 0 写父 `+$C3=3`。`:112-135` `part0_back 0x33500`：act 0 时按 facing ±0x58 定位、vx ±0xA00；有英雄仍查 action；`motion` + `part0_arrive` + `part0_count`。
- `class6_tongue.rs:137-143` `part0_action`：从 target handle 解 `Slot::Player` 读 `players[p].action`。`:153-170` `part0_arrive 0x335B2`：带英雄到 0x60 像素时写父 `+$C4=1` 并释放；空手回锚点写父 `+$C3=0`。`:178-187` `part0_list_reset / part0_list_held` 改 count 与首段 8 字节。
- `class6_attack.rs:1-6` 文件头：act 6 攻击脚本（`0x39C38..0x3A0B2`）是 `+$B4` 索引的字节串（`SCRIPTS 0x39CAC`，每脚本 4 字节，`+$B2` 读位置）：0 走到英雄旁 / 2 跳 / 4 扑（attack 0x24）/ 6 冲（0x25）/ 8 长舌跳（0x26）/ 0xA 吐酸球（class 7）/ 0xC 与 sub 4 用舌头抓英雄；`>=0x80` 结束脚本。每步读 `+$AD` 作自己的相位计数。
- `class6_attack.rs:23-42` `enemy_c6_state_attack 0x39C38`：hitstop 门后按 `step` 分派（0 下一条脚本 / 2 走 / 4 跳 / 6 扑 / 8 冲 / 0xA 舌 / 0xC 吐）。`:49-61` `c6_script_next`：目标 dead 或 sub 2 就结束；`:61` 命令 0xC 写 `state 0x0204_0000`（转 sub 4 抓取态）。
- `class6_attack.rs:477-491` `enemy_c6_grab_state 0x3A0B4`：act 0 清 `+$C2/+$C3`、anim 0xA；act 2 走 `c6_grab_body`。`:493-537` `c6_grab_body 0x3A0EC`：`+$C2 != 0` 时 `+$C5` 每帧减 1，借位则重装 `0x1E` 并给目标玩家 `hp -= 1` + 刷血条；`step 0` 走完写 `+$C3=1`（**主体启动舌头**）；`step 2` 若 `+$C2` 已置位转 step 4 `c6_grab_wait`，若 `+$C3==3` 则 `c6_grab_back`；`step 6` 等 `+$C3` 回 0 才推进。注释 `:493` 明写「part 0 设置 `+$C3`：1 伸出 / 2 抓住 / 3 收回」。
- `class6_eat.rs:1-11`（**只作边界，不写正文**）：吃道具 / 胃环 / 吐回已在 §66.4 展开，本节不重复。

**六条设计结论**：
① **两槽按 handle 大小分工**：主体自己 alloc 出第二槽，`min` 恒为舌头（class 0）、`max` 恒为主体（class 0x18）——与 §88「三槽取中位数」是同族（地址决定身份）但不同形态（两槽、大小而非中位数、主体先被脚本造出来）。
② **舌头没有 AI，只有一个从主体读来的状态码**：`+$C3` 四值（0 内 / 1 伸 / 2 抓 / 3 收）由主体与舌头**双向写**——主体写 1 启动，舌头自己写 2/3/0 回报；`+$C2`（有英雄）、`+$C4`（送到嘴边）是舌头→主体的另两条回报线。与 §71 master 用 `sub` 广播给 N 个演员、§77 同一帧字节读成三态同族，但这里是**两个独立 pool A 对象跨槽写字节**，不是同一个任务机。
③ **画出「会变长的身体部件」不靠动画帧，靠每帧改写一条 raw sprite list 的段数**：`count = |距离|>>4 + 2`（每 16 像素一段），首段在普通态是 `TIP`、抓住后覆写成 `HELD` 8 字节；长度上限 `0xC8` 触发收回。与 §45 固定排序键、§81 定长 raw sprite 四态不同：这里**列表长度本身就是玩法状态**（伸到多远 / 有没有抓到人）。
④ **抓住不是一次命中事件，是一段有独立计时的托管**：舌头本地 100 帧 `+$80`、主体 `+$C5` 每 `0x1E` 帧扣 1 HP，两边各自跑；英雄 `action != 0x40`（不在被抓态）任一边都能提前释放。与 §24 通用投技的「双向互检」一致，但这里多了一层「显示对象也参与释放判据」。
⑤ **「送回嘴边」是一个显式里程碑**：`part0_arrive` 在距锚点 0x60 像素时写 `+$C4=1` 并释放，主体据此进入后续；空手回锚点则 `+$C3=0` 收工。不是「舌头消失 = 抓取结束」，而是**位置阈值触发一个状态字节**。
⑥ **生命周期耦合但不合并**：父 HP=0 / mode>=4 / 槽已不是 Enemy → 舌头当帧自毁并归还 pool D；`draw_special_alloc` 失败则主体 mode=6 连带放弃（原子耦合）；与 §87 parts 读宿主、§88 parts 读主体同族，但这里舌头还**持有自己的 pool D 数据槽**，自毁要先 `draw_special_free`。

**wof 侧按 §11.0 只登记不同语境并列事实**（四格都是既有注释 / 调用面复述）：`Cps1PlayerLogic.cs:3989`（`1C1F8 cmpa.w $6a(a1),a0` 被抓者 `+$6A` 反查持有者）/ `Cps1PlayerLogic.cs:4755`（`1C81A tst.w $82(a1)` 抓取段读被抓者 HP）/ `Cps1EnemyAI.cs:3485-3503`（`0x121F4..0x12328` 受击「分身替换」主体与 `0x1222C` 复制）/ `Cps1EnemySpawn.cs:1671-1676`（三对象 `ObjId 0x14/0x1E/0x14` 录像对拍）。**不串等价、不评优劣、不把未登记写成缺失、不据此断言原机缺机制**；wof 侧无舌头机制的直接注释，不臆断；0 次 ROM 取证，§11.6 未触发；`_无对应ASM` 开关与 FBA 逐帧对拍按 §0 剥掉。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；临时片段用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s89_patch.txt` / `a53_patch.txt`。
- 大段中文 markdown 用 Write 落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → **按行号直接对数组元素就地赋值**（坑 5）→ 逐项预校验 `cnt=1` 且 `new != old` → 一次 `WriteAllText`（`Join("`n")` + 末尾 LF，无 BOM）。
- **坑 1**：PowerShell 数组字面量里 `+$var+` 会解析错位；含 `+` 的字符串先赋独立变量；写盘后核 L46 长度变化与 `EndsWith(' | 有效 |')`。
- **坑 2**：回执别写「`§N+` 引用 0」，改写「超出 §N 的章号引用 0」。
- **坑 3**：表格单元格禁止裸竖线（位或表达式改文字或 `\|`），精确表达式放非表格伪代码块。
- **坑 4**：`file:line` 全量校验必须**不去重**、不加 `(?<![\w/])` 后视、多根 basename 索引、扩展名正则用 `s[h]` / `p[y]` 字符类。
- **坑 5**：导航替换别用 `[ordered]@{ 16=... }` 存数字行号再 `ContainsKey($i+1)`（int）查——key 会变字符串、查询恒 false，导致整组替换**静默丢弃**而 `PRECHECK_FAIL=0` 照样过。改 `$LA[$ln-1]=$line` 就地赋值。写盘后必须核 L16 新数字、L46 长度与 `EndsWith(' | 有效 |')`、四处主题索引 `§N` 命中、L70 `A.N` 命中、diff 删除恰为 8 条导航行。
- 导航固定 12 处：L16 七处（行数 / mermaid 数 / 表格行数 / `A.1–A.N` / A.N 条目 / A.N 位置 / `§0–§M 全部结论`）、L46 两处（章节列表 `/ §M |`、主题摘要 `；§M（…） | 有效 |`）、L47 两处、L50 / L54 / L63 / L65 各一处 `、**§M（…）**`、L70 一处 `、A.N`。回执追加时不改导航结构，只刷新 L16 行数与表格行数并补 A.N 正文定义。
- 校验固定项：片段逐行零缺失 / 表格块严格口径排除转义竖线 0 不一致 / 全量 `file:line` 双口径（不去重）零缺零越界且 HEAD 基线差等于新区引用数 / `CR=0 BOM=False` / `git diff -U0` 删除行逐条核为纯导航行 / 悬空章号 0 / **写盘后导航命中复核**。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；提交用 `git -c i18n.commitEncoding=UTF-8 commit -F`。
- 每块一提交：DRAFT 定题 → §89 正文 → A.53 回执 → DRAFT 收尾，四笔；顶部规模行、导航在 §89 提交时一次同步并预写 A.53。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
