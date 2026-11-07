# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**§91 开工版**：上一版是 `a80ed07` 收尾版（记 §90/A.54 完成状态与 §91 起步），开工读过后删掉重建为本版定题；旧版残差已消费。

## 30 秒版现状（开工当场核）

- HEAD `a80ed07`，`git status --short` 为空，工作区干净。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**。
- `DESIGN_DIFF_NOTES.md` 实测：**14459 行 / 106 张 mermaid / 3169 表格行 / 528 栅栏 / 表格块严格口径 405 块 0 不一致 / §0–§90 / A.1–A.54 正文定义 54 / 双口径不去重窄 1843 宽 1910 缺文件 0 越界 0 / 悬空 0 / CR=0 无 BOM**。顶部 L16 已是 `14459 行 ... 3169 表格行`，**不要引旧数**。
- `R:\Temp` 无残留。本轮开工按 `system-prompt.txt` 读了 `CODEBUDDY.md` → 旧 DRAFT → `git log -8` / `git status --short`。

## 本轮 §91 定题（先查重，不按零匹配排序）

**题目**：`enemy/class61*.rs` + `enemy/class52.rs` —— **刀掉在地上不是丢了一件东西**：Butcher 的两把刀是独立 pool A 对象（class 52），主体对象头同时存「现在持有」与「掉在地上要追的那一个」共四个 handle；掉落只是把同一个对象的 `sub` 写成 8，落地时刀**自己**变成 pool E 道具并把新句柄**回写主体**，主体 dash 每 32 帧朝那个句柄定向，捡到后**造一把全新的刀**、把旧的移除。

一句话结论：**身份从头到尾没有连续过，连续的只有那几个句柄字段**。一把刀在「手持 → 飞出去 → 地上道具 → 被捡回」四段里换了三次对象，主体只靠「写哪个字段、回写哪个字段」维持对它的追踪。

**排除链（本轮语义查重，A.50.3 双向化后两个方向都核）**：
- **§88 class14 三槽 / 刀数 decision / class34·class41**：`class14_parts.rs:68-140` 的掉刀是**新造 class34 对象** → 落地 `c34_make_knife_item` 造 pool E variant 4 道具；主体**不留 handle 副本、不追刀**；parts 只是显示。L13798 明写「各自类自己的状态机，本节不展开」。Butcher 是另一套代码：改同一个对象的 sub、回写句柄、dash 追回、造新刀。**同为「敌人武器落地变可拾取道具」，机制不同，只作并列、不串等价、不评优劣**；同时 L13823 的「刀数参与选表」是 class14 的 decision 2，Butcher 的 `c61_decide` 是另三张表（0/1/2 把），不重写、不合并。
- **§62 `item_drop_roll`（L8541–L8657）**：敌人死亡链把「位置 + 行号」交给 `item_drop_roll`，roll 表造掉落物、进 `$69EE` 拾取列表 → `find_pickup`。Butcher 的刀**不 roll、不进 `$69EE`**，是主体已有对象的状态迁移 + 定向回写。§21 的道具双向迁移也是玩家侧 `$69EE` 链，不同语境。
- **§66.4 认领地上道具（L9439–L9498）**：Bludge 按类别最低认领 / 8 格胃环 / 吐回，是「吃道具」；Butcher 是「追自己掉的武器」，不重写。
- **§77 `item_follow_hand` / 跟手**：pool E 物件读宿主 `+$60` attach 索引查表；Butcher 是 pool A 刀对象，主体读自己帧字节 `+$2D`（`param_b`）查 `0x57480` / `0x57558`（按刀 variant 高字节选）写坐标。同族不同池，不合并。
- **§89 舌头 / §88 parts / §87 火光 / §69 持械分体**：都是「跟随者读宿主」；本节多一层「跟随者落地后替宿主改字段（回写副本）」，是双向但不同形态。
- **主文件零匹配面**：`A52` / `c61_` / `class52.rs` / `0x57298` / `0x5A280` / `0x586D6` / `0x58752` / `0x5A1EA` / `0x584AC` / `KNIFE_A2` / `variant 0x12` 全部零匹配。主文件只在 L11036 / L11110 提过 `lib_face_target` 给 Butcher 决策 roll `0x5A1AC` 留 `frame_w1`，不是本节机制。

**dino 取证行号**（`dino-rs/crates/dino-game/src/game/enemy/`）：
- `class61.rs:1-6` 文件头：Butcher（class 61，handler `0x58498..0x5A47C`，8164 字节），Episode 2 Boss；`class5.rs` 把 class 字改写成 61 并清 state，init 在下一帧跑；文件分 init / alive / state bodies(`class61_states.rs`) / move blocks(`class61_moves.rs`) / hit `0x5A33A` / death `0x5A37A` / **knife follow tail `0x5A280`**；原机是一整段例程带「跳进别的状态中间」的分支，块保留地址当名字。
- `class61.rs:15-53` 自有字节：`ROLL +$A1`（30 帧攻击 roll 计时）、`GROUP +$AA`（向 controller 要 group 的计时）、`+$A2`/`+$A3`（走步跳过 / dash 32 帧方向）、`+$A4` 上次转向、`+$A5` 目标 X 距离类、**`KNIFE_A +$A6` / `KNIFE_B +$A8` 两把刀 A52（variant 0 / 0x100）与 `KNIFE_A2 +$B4` / `KNIFE_B2 +$B6` 它们的副本（掉落后道具，供 dash 追）**、`+$AB` 首跳标志、`+$AC` 本次受击已掉刀、`+$AE` 状态计时、`+$B0` 环形 hop 槽、`+$B8` aggression 翻转计时、`+$BA` 0 等英雄 / 1 压迫、`+$BB`/`+$BC` 连击剩余、`+$BE` 持有刀数 0..2、`+$BF` 剩余弹跳、`+$C8` 血条副本、`+$CC` 越过顶点；`TURN_TABLE 0x5986C` / `SLOT_DX 0x32EA4` / `SLOT_DZ 0x32EB2`。
- `class61.rs:75` mode 分派：0 init / 2 alive(`0x5861C`) / 4 death(`0x5A37A`) / 6 body that stays(`0x5A3CA`)。
- `class61.rs:85-130` `c61_init 0x584AC`：name 0xF、表 `0x6FDEC`、HP row 1、target、`ATTACKING=0xFF`、stun 0x0B、`KNIVES=0`、`FLAG_AC=0`、`ROLL=GROUP=0x1E`、`TIMER=0x14` → `c61_make_knives(e,h)` → `hud.boss=h`、`b4fc=0`（boss intro 结束）、贴地、`boss_spawn_controller(h)`、`BAR=hp_bar`、sound 0x0F（在决策 RNG 之前）、`c61_decide`。
- `class61.rs:132-153` `c61_make_knives 0x58562..0x585E6`：循环两次造 pool A 对象（`k20=0xD0` 即 class 52，variant 0 / 0x100，坐标取主体整数位置，`anim_table=0x6F8A6`，`+$A0 = ptr(h)` owner），把 handle 同时写 `knife`(持有) 与 `copy`(副本) 两个字段，`KNIVES=n+1`；**池满 `alloc()` 失败就 `return`，刀数停在 0 或 1**。
- `class61.rs:283-321` `c61_alive 0x5861C`：X 钳在相机窗口 `cam_x-0x50 .. +0x1D0`（HP=0 时收窄到 `-0x10..+0x190`）→ 按 `sub` 分 0 alive / 2 hit / 4 holding hero / 6 grabbed → **`GROUP` 每 30 帧归零时 `spawn.g.b502=1`（向 boss controller 要下一组）** → `c61_knife_drop` → `c61_tail_knives`。
- `class61.rs:323-329` `c61_sub0 0x5882A`：alive 第一件事是 `c61_knife_pickup`，之后 poise / floor / hitstop / 决策 / slot / state / leap roll / far check / slot refresh / timer toggle / draw check / 每帧重建 hostile(0x4C0A) 或 hurtable(0x4BEA) 列表。
- `class61.rs:419-427` 每 30 帧 `ROLL` 攻击 roll（HP 低时阈值不同）；`:490-491` `c61_decide 0x5A1EA`：随机行（32 行 × 8）与 X 距离类查三张表之一 —— **0 把 `0x73ED4` / 1 把 `0x73FD4` / 2 把 `0x740D4`** —— 1..4 连击(`0x59F0C`)、5 旋(`0x5A014`)、6/7 跳(`0x59B24`)、8 首跳(`0x59B1E`)、9 dash。
- `class61.rs:551-571` `c61_dying 0x5A37A`：step 0 音乐淡出 `hook_a5ea`、`flow.speed=1`、120 帧 `+$80`、记分(`0x325E6`)、step 2 倒数、末了 `enemy_boss_leader` → mode 6。**不碰任何刀字段**。
- `class61.rs:590-625` `c61_knife_drop 0x586D6`：`KNIVES<=0` 返回；**只在 `(mode,sub)==(2,2)` 且 `act==4 或 6`（击倒受击）**才继续；其它状态清 `FLAG_AC`；`rand() & 0xF >= 8` 或 `FLAG_AC!=0` 返回；`KNIVES -= 1`；**「第二把先掉」**：`left==0` 取 `KNIFE_A` 写 `KNIFE_A2`，否则取 `KNIFE_B` 写 `KNIFE_B2`；`FLAG_AC=1`；`slot_of(knife)` 解出 `Slot::Enemy(i)` 就把那个刀对象 `b.sub = 8`。
- `class61.rs:627-648` `c61_knife_pickup 0x58752`：`KNIVES>=2` 或 `act != 0x12`（dash）返回；按当前刀数取副本字段（0 把 → `+$B4`，1 把 → `+$B6`）；**`slot_of` 同时接受 `Slot::Item(i)` 与 `Slot::Enemy(i)`**；要求 `(mode,sub)==(2,0)`、X 在 `above(0x20,0x40)`、Z 在 `above(0x10,0x20)`、Y 相等；命中写 `+$A0=1`、`act=0x10`、`enemy_anim(5)`。
- `class61.rs:650-690` `c61_tail_knives 0x5A280` / `c61_knife_follow 0x5A2A4`：按 `KNIVES` 逐把跟手；读主体帧字节 `+$2D`（0x63 / 0x5A 归一成 0x15）当行号，按刀 `var26>>8` 选 `0x57480` / `0x57558`，每行 8 字节给 `dx/dy/dz/pic`；facing 镜像 dx；写刀对象坐标与 `+$A6=pic`；`pic==0x5A` 隐藏；帧字节变化才 `start_anim`（`0x120E`）。
- `class61_states.rs:521-560` `c61_s10 0x5959E`（act 0x10 抓刀）：动画播完且 `KNIVES<2` → `enemies.alloc()` 造**一把全新的 A52 刀**（`k20=0xD0`、variant 按 second、`+$A0=owner`、`anim_table=0x6F8A6`）；把旧的那一个（**Item 或 Enemy 槽都处理**）`var26=0; mode=4` 从地上移除；`KNIFE_x` 与 `KNIFE_x2` **都写新 handle**；`KNIVES+1`；末了 `c61_tail_knives` + `c61_59e08`。
- `class61_states.rs:562-599` `c61_s12 0x59678`（act 0x12 dash，速度 13）：`TIMER` 倒数；每 32 帧（`+$A3` 重装 0x20）在 `KNIVES<2` 时读副本 handle 的 `sub / X / Z`（同样接受 Item / Enemy 两池）；**`sub==8`（还在飞）就 `c61_5a186` 放弃这次 dash**；否则 `enemy_angle_to` 朝刀定向；然后 `lib_face_target` 面向英雄、`enemy_move_dir`、路上 `c61_knife_pickup`、`enemy_step`。
- `class52.rs:1-7` 文件头（最关键）：class 52（handler `0x57298`，920 字节 + 偏移表 `0x57480`/`0x57558`）；**手持时 sub 0 是「身体的一部分」**，主体每帧写坐标（`c61_knife_follow`）；击倒让主体设 `+$05=8` → 刀飞出去（sub 8 然后 4）→ 落地**变成 pool E item（class 0，variant `0x12`，英雄可捡的 Butcher 刀）并自毁**；**主体死（mode 4）时刀立即自毁**。
- `class52.rs:14-24` `enemy_class52 0x57298`：mode 0 init / 2 run / 4·6 `enemy_free_pool_a`（`0x5747A`）。
- `class52.rs:41-62` `c52_run 0x572F0`：先读 `+$A2` owner，`slot_of` 解出主体且 `mode>=4` 就**当帧 free**；再按 `sub` 分派 0 held(`0x5731C`) / 2 sliding(`0x5735A`, 加长速 `+$AA`) / 4 falling(`0x57368`) / 6·8 start-to-fall / 尾随 `enemy_clamp_to_playfield 0x193E`。
- `class52.rs:64-77` held：读 owner facing、`enemy_step`、`+$A6 == 0x5A` 时不画。
- `class52.rs:79-105` `c52_falling 0x57368`：`motion()`；落地（`yi()<0` 或不再 airborne）→ `items.alloc()` 造 pool E item（`k20=0`、`var26=0x12`、坐标取刀）→ **把 item handle 回写主体的 `+$B4` / `+$B6`（按刀 `var26>>8` 选字段）** → 刀 `mode=4` 自毁；未落地则 `enemy_step` + draw check。
- `class52.rs:107-123` `c52_6 0x573DE`：起始滑开（X±0x40、Y+0x40、`dir=8` 或 `0x18`、长速 `0x58000`、anim 8）。
- `class52.rs:125-138` `c52_8 0x5743C`：起始掉落（`sub=4`、airborne、`vx=0x100`、`vy=0x680`、`ay=0xFFBB`、anim 0x20）。
- `class14_parts.rs:68-140`（**只作并列边界**）：class34 掉刀是新造对象、落地 `c34_make_knife_item` 造 pool E **variant 4**，且有「两把枪在场就不转道具」的 `off` 门；Butcher 是 variant `0x12`、改同一个对象、回写句柄。§88 L13798 已登记但不展开。

**七条设计结论**：
① **刀不是主体的部件，是独立 pool A 对象**（class 52，`k20=0xD0`）；主体对象头用**四个 handle 字段**同时记「现在持有」`+$A6`/`+$A8` 与「掉在地上要追的那一个」`+$B4`/`+$B6`，初始两份指向同一个对象。与 §88「三槽排序定真身」、§89「两槽按大小分工」同族（地址即身份），但这里是**一个主体 + 两件武器 + 两份副本字段**，不是造槽定身份。
② **「掉落」不是销毁也不是生成，是把同一个对象的 `sub` 写成 8**，主体把 handle 从持有字段**迁到副本字段**；刀自己接着跑 `8 → 4` 抛物线。`FLAG_AC +$AC` 保证一次受击只掉一把，且「第二把先掉」（`left==0` 取 A，否则取 B）。与 §87「攻击者身份是每帧声明」同族（状态字改身份），不串等价。
③ **落地时刀自己换池，并把新句柄回写主体**：`c52_falling` 造 pool E item（class 0 variant `0x12`），按刀 variant 高字节选 `+$B4` / `+$B6` 把 **item handle 写进主体对象头**，然后刀自毁。**身份在落地这一刻从 pool A 换到 pool E，连续的是主体那几个字段**。这解释了拾取与 dash 里 `slot_of` 为何同时接受 `Slot::Item` 与 `Slot::Enemy`。
④ **拾取判据只认句柄解出的槽 + `(mode,sub)` + 距离，不认池类属**：`c61_knife_pickup` 要求 `(2,0)` idle、X/Z/Y 三轴窗口，且只在 dash 中、刀数 < 2 才查；命中转 act 0x10。与 §66 认领（每帧重建候选表、读上一帧）不同路：**这里不扫列表，只查一个已知句柄**。
⑤ **捡回是「造新刀 + 移除旧物」，与掉落不对称**：`c61_s10` 动画播完造一把全新 class 52，把旧道具 `var26=0; mode=4` 移走，持有字段与副本字段**都写新 handle**。所以「同一把刀被捡回来」在对象层面并不成立——**从头到尾换过三次对象**。
⑥ **dash 是「追刀」不是「追英雄」**：`c61_s12` 每 32 帧朝副本句柄的坐标重新定向，途中顺带拾取；`sub==8`（还在飞）就放弃这次 dash。刀数同时改写**出招分布**（三张 decision 表 0/1/2 把）与**导航目标**，是「装备状态直接改 AI 两条线」的一处实例；与 §88 L13823 的 class14「刀数选表」只作并列，不重写。
⑦ **生命周期耦合由刀侧反查完成**：刀每帧读 `+$A2` owner，主体 `mode>=4` 当帧 free；主体死亡路径 `c61_dying` 自己**不碰任何刀字段**。资源门：`c61_make_knives` 池满提前结束使刀数停在 0/1；落地 `items.alloc()` 失败时刀只把自己 mode=4、副本字段仍指向旧 handle（按 repo 侧如实登记，不臆断后续）。跟手是主体读自己帧字节查两张偏移表写刀坐标，与 §77 pool E 跟手同族不同池。

**wof 侧按 §11.0 只登记不同语境并列事实**（四格都是既有注释 / 调用面复述）：`Cps1EnemyAI.cs:29724`（`弓箭手_取武器槽_部分对应ASM_13EE(out uint weapon)`，语境 = Actor 从武器槽取武器）/ `Cps1PlayerLogic.cs:6323-6326`（`关羽_站立拾取近接_可能对应ASM_1E9D8` 地面物近接扫描、池 1 命中进公共拾取，语境 = 玩家按键触发的拾取扫描）/ `Cps1PlayerLogic.cs:6555`（拾取后玩家 `+0x8C = BC9C` 记武器对象，语境 = 玩家对象头单个武器指针，无「掉落副本」）/ `Cps1MiscObjRuntime.cs:36-44`（`A5+0x32C` / `A5+0x320` 拾取缓冲队列指针与数量，语境 = 宿主侧缓冲队列）。**不串等价、不评优劣、不把未登记写成缺失、不据此断言原机缺机制**；wof 侧未见「Boss 掉刀后留句柄追回」的直接注释，不臆断；0 次 ROM 取证，§11.6 未触发；`_无对应ASM` 开关与 FBA 逐帧对拍按 §0 剥掉。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；临时片段用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s91_patch.txt` / `a55_patch.txt`。
- 大段中文 markdown 用 Write 落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → **按行号直接对数组元素就地赋值**（坑 5）→ 逐项预校验 `cnt=1` 且 `new != old` → 一次 `WriteAllText`（`Join("`n")` + 末尾 LF，无 BOM）。**写盘 / 校验都落 `.ps1` 再执行**，不用长命令行 here-string。片段首行空 + 末行 `---`。
- 坑 1：数组字面量里 `+$var+` 解析错位，含 `+` 的字符串先赋独立变量；写盘后核 L46 长度变化与 `EndsWith(' | 有效 |')`。
- 坑 2：回执别写「`§N+` 引用 0」，改写「超出 §N 的章号引用 0」。
- 坑 3：表格单元格禁止裸竖线（位或、绝对值符号都算），精确表达式放非表格伪代码块。
- 坑 4：`file:line` 全量校验**不去重**、无 `(?<![\w/])` 后视、多根 basename 索引、`s[h]` / `p[y]` 字符类；OOB 用「任一同名候选文件行数覆盖即通过」；悬空阈值随最大章号调为 > 91。**校验脚本属一次性脚手架，用完即删，需要就重建，不假设它还在**。
- 坑 5：导航替换别用 `[ordered]@{}` 存数字行号再 `ContainsKey($i+1)`（int）查；改 `$LA[$ln-1]=$line`。写盘后核 L16 新数字、L46 长度与 `EndsWith(' | 有效 |')`、四处主题索引 `§N` 命中、L70 `A.N` 命中、diff 删除恰为 8 条导航行。
- 导航固定 12 处：L16 七处、L46 两处、L47 两处、L50 / L54 / L63 / L65 各一处、L70 一处。回执追加时不改导航结构，只刷新 L16 行数与表格行数并补 A.N 正文定义。
- 校验固定项：片段逐行零缺失 / 表格块严格口径 0 不一致 / 全量 `file:line` 双口径零缺零越界且 HEAD 基线差等于新区引用数 / `CR=0 BOM=False` / `git diff -U0` 删除行逐条核为纯导航行 / 悬空章号 0 / 写盘后导航命中复核。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；提交用 `git -c i18n.commitEncoding=UTF-8 commit -F`。
- 每块一提交：DRAFT 定题 → §91 正文 → A.55 回执 → DRAFT 收尾，四笔；顶部规模行、导航在 §91 提交时一次同步并预写 A.55。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
