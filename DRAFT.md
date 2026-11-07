# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**§94 开工版**：上一版是 `7b5f5e6` 收尾版（§94 起步原候选 `flow/system.rs`），开工读过后消费完毕。
> 中途曾误写成「跑步摇杆前置检测」定题版，用户明确 `跑步问题暂时不用研究了,只是考你` 后已 `git checkout -- DRAFT.md` 撤销，工作区干净；**跑步那道不写**。

## 30 秒版现状（开工当场核）

- HEAD `7b5f5e6`，`git status --short` 为空。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**。
- `DESIGN_DIFF_NOTES.md`：**15225 行 / 109 张 mermaid / 3354 表格行 / 558 栅栏 / §0–§93 / A.1–A.57 正文定义 57 / §94=0 / A.58=0 / L46_len=11141 endsTable=True / CR=0 无 BOM**。L16 已是 `15225 行 ... 3354 表格行`，**不要引旧数**。
- `R:\Temp` 无 `s9*` / `a5*` / `a6*` / `draft_*` 残留。
- 引用行数上限：`player.rs=3952`、`body.rs=238`、`player_combat.rs`（短）、`enemy_combat.rs`、`collide.rs`、`camera.rs`、`Cps1PlayerLogic.cs=14686`、`Cps1Collision.cs`、`Cps1PlayerMulti.cs=5188`。

## 本轮定题（用户当面出的第二道题）

用户原话：

> `感觉需要寻找下 wof 关羽普攻连拳 打杂兵 和 dino 穆斯塔法 普攻连拳打杂兵 的感觉为什么不同(CAPCOM每个游戏都有特色,就好像现实中打击不同材质),虽然你不能直接看到图片,但你看状态机和判定框 以及 抖动和临时无敌什么的 应该可以分析出来`

配套的前两条（同一条链，本轮只作背景、不写正文）：`4级状态机的数值风格,dino里跑步的摇杆前置检测,在wof中应该插入到哪(其实我知道,就是考考你)`、`dino似乎把四个角色的主体写成一套代码了,用ID小分支.而wof看起来是多开发者并行开发各写一种乱七八糟`、`我就是试图学dino的经验,未来优化wof.以及分析打击感差异,以及数据格式差异未来互相移植角色`。

**用户明确纠偏口径（必须遵守）**：`请说人话,不要只说自己的小编号`、`用户关心的不是你的内部分析步骤,而是人类理解中的游戏设计`。所以 §94 正文：
- 用「打在湿沙上 / 扫过一排空罐头」这类**人类可感的材质比喻**开场并贯穿；
- 讲**游戏设计本意**：续拳许可来自哪里、一次挥拳碰几个人、被打的杂兵让不让步、停顿/抖动/无敌是不是同一个东西、判定框形状、伤害随什么变；
- 不写「我先 Grep 了什么」、不堆 §/A 内部编号当叙述主体、不把取证流程写进正文；`file:line` 只在证据表里出现；
- 不评优劣、不把未登记写成缺失（§11.0）；按 §0 剥掉 FBA 实测 / CS 卡值 / 逐帧对读 / 置信度标记 / `_无对应ASM` 开关；0 次 ROM 取证（§11.6 未触发）。

## 语义查重（双向，刚做完）

- `打击感` 在主文件零匹配；`hitstop|poise|受击反应|命中停顿|抖动|无敌` 大量命中但**都在 §3 / §12 / §22 / §29 / §37 / §39 / §17 的机制对照里**，不是「两边普攻连拳打杂兵的手感」这一具体场景。
- 已展开、本轮**不重写**：§3 dino 固定 pass 管线 + 多因子伤害（L296 起）、§12 命中帧结算 / 后续帧处决（L1555 起）、§22 poise/dizzy/反击/hitstop 四套同帧写入（L3152 起）、§29 恢复链 14+ 反应 / `invuln[16]`、§37 `step_shake` 幅度递减方波 / `+0x62` 一字节三用、§39 连击 `combo_t` 时间窗与四段链（L5510 起）、§17 多因子伤害连乘（L760 起）。
- **本轮的新横切面**：把这些既有机制**收拢到「关羽 vs 穆斯塔法各打一套连拳同一个杂兵」这一个场景**，回答「玩家手上感觉为什么不同」。这是场景级综合，不是新机制；按 A.50.3 / A.54.2「有匹配 ≠ 已展开」取题。
- 用户上一轮口头答过的六点，是本节骨架：续拳许可、一拳碰几个、杂兵让步方式、停顿/抖动/无敌合一还是分家、判定框形状、伤害随什么变。加上第七点「角色差异落在哪」与「未来优化先动哪三处」。

## dino 侧取证（穆斯塔法 = character 1，全部当场读源码）

- 四段连拳状态字：`player.rs:1296-1305` jab `set_state(0x0200_0004)` + `combo=0` + `dtap=0` + `player_new_attack(i,0)`；`:1308-1325` jab 每帧先判 `hitstop != 0` → `player_hit_confirm_entry`，否则 `player_pstep` 动画走完 → `lock=5 / combo_t=0 / combo=0` → idle（**打空整串散掉**）；`:1328-1336` hit_confirm 里 `combo += 1`、`action=0x10`、`set_state(0x0200_0006)`；`:1339-1364` hitstop 逐帧 -1、减到 0 才 `pstep`，期间 `pressed & ATK` 存 `atk_buf`，动画走完给 `combo_t=0x28`（40 帧窗口），`combo==4` 清空；`:1367-1384` `player_chain_continue` 按 combo 1/2/3 接 `punch2 / punch3 / finisher`；`:1387-1403` punch2 `0x0200_0008`；`:1416-1433` punch3 `0x0200_000A` 且 `hitstop += 1`（第三拳故意加长）；`:1437-1473` finisher `0x0200_000C` + `player_new_attack(i,4)`，且 `p.b.id == 1 && param_a == 0` 时 anim=7（**穆斯塔法专属收招 pose，按 id 小分支**），combo 第 4 段可抓 partner 转投技。
- **许可来自打中**：`player_jab`/`punch2`/`punch3`/`finisher` 每帧第一句都是 `if hitstop != 0 { return player_hit_confirm_entry(i) }`。hitstop 由命中写入，所以「打中」才是续拳的门票。
- 命中写入 `enemy_combat.rs:120-180` `enemy_monster_hit`：`boxes_hit` 三轴几何判定 → `e.b.serial = ab.serial`、`e.b.live = 2`（受击态，本列表免打）、`set_state(0x0202_0000)`、扣 `stun`（`saturating_sub(rec.stun)`）、写 `reaction` / `act=mapped` / `step=0`、`e.b.hitstop = rec.hit_stop` 且 `body_mut(a).hitstop = rec.hit_stop`（**双方同写**）、队伍技连 partner 也写、`spawn_hit_spark(..., rec.spark)`；`rec = assets.sprites.player_attacks[ch][(ab.atk/2)]`，8 字节记录 `damage / stun / reaction / hit_stop / sound / score / spark / b7`（`prop.rs:702` 实例）。
- 一拳碰几个：`enemy_combat.rs:105-117` `pass_11a9e` 同帧遍历 `0x6718 × 0x6B64` 全部敌人，`db.live & 2 == 0 && db.serial != ab.serial` 才打（serial 防同一拳重复打同一人，`player_new_attack` `:251-258` 每拳 `G.$67BE++` 发新流水号）；`:32` 同类判据。**同帧一次结算一片**。
- 伤害 `player_combat.rs:19-89` `player_damage`：counter hit（敌人 kind==4 正在出招）、弱点对（`weakness` 表）、`power`、等级缩放、敌人 HP 百位 `hp_hundreds_scale`、HP band `hp_band_scale`、**两次 RNG**（r1/r2）连乘，保底 1。
- 受击后 `L818` poise 起始 10、每次命中减 `rec.stun`、到 0 下一拳必击倒、击倒重置；`:953-957` 受击态 `mode 2 → hit_reaction(0x2A606)` 按 `act` 分派 10+ 种；击倒物理 4 组初速（L820）。**攒够了才飞**。
- 判定框 `collide.rs:8-48`：`box_table & 0xFF_FFFF` + `multi_box` 决定单/多框；`overlap` 三轴 `(z,x,y)`，`axis` 用 `<=` 所以**边缘接触算命中**；`left()` 按 `facing` 镜像 xoff；`boxes_hit` 返回第一对重叠框，直接喂火花定位。玩家框表 `player_box_tables[ch]`（`player.rs:645`），按动画帧记录带出。
- 屏幕抖动 `camera.rs:208-250` `step_shake`：`shake_sign` 每 2 帧翻转、幅度 `shake_amp -= 1` 递减到 0、按关卡选 scroll1/scroll2 的 Y 偏移；`cam_shake(strength)` `:1733` 只写请求。**普攻连拳命中不触发 cam_shake**——本轮 grep 全库，`cam_shake` 只在硬落地（`player.rs:1818` strength 3）、Boss（`boss_common.rs:356`）、机关（`prop/b82_85.rs:206,439`、`class22_foot.rs:234`、`class30.rs:70`、`class38.rs:328`、`class84.rs` 多处、`class61_states.rs:393,463`）、script（`:1126`）、car/cont 里出现，**没有普攻命中**。所以轻拳是「手上的黏滞」不是「屏幕在抖」。

## wof 侧取证（关羽，按 §11.0 只登记不同语境并列事实）

- 连拳三级：`Cps1PlayerLogic.cs:7053-7057` `关羽_A02B00C08_出拳连击检查_1B400`（`ComboLeft==0` 就 `ComboLev=0`）；`:7059-7091` `出拳开始_1B412`：`combolev>2` 归零、`AtkType = combolev*0x10`、动画表 `0x70A2A[combolev]`、音效/特效记录 `5+combolev`、`ActStatD=2`、`AtkAnimId=0x0A`；`:7093-7200` `出拳执行_1B45E`：`SUB_2470` 推进动画 → `AniStatCD < 0`（动画播完）→ `ComboLeft` 门（`:7108` 逐指令 listing：==0 就清 C 收招）→ `clr ComboLeft` → `NewBtnA != 0` 才 `ComboLev++` 回 `出拳开始`；`ComboLev==1 && HitObj1!=0` 且方向键 0x08/0x04 时转连拳收尾抓（写 `0x02040200` / 敌人 `0x02060000`、预备伤害 `1BCA` / `1684`）。**全程不检查「有没有打中」**。
- `ComboLeft` 递减在 `关羽_A02B00_待机_1ADE4`（`:6175`），`ShakeLeft` 递减在 `:6169-6173`（非零就减一并 `return`）；`:705` / `:7925` 同族。
- 三级攻击力表 `Cps1PlayerLogic.cs:5417-5420` `角色1_C08攻击力表_1C0C8 = {0x01E0, 0x01F0, 0x0200}`，`combo & 3` 索引写 `+0x7A`（`:5468`）；`:5438-5439` 三套动画 `0x75E70/0x75E92/0x75EB4`。
- 群体伤害机制注释 `Cps1Collision.cs:333-342`：**命中敌人 A → A 与 attacker 各写 3 帧硬直 → 3 帧后 attacker 归零、攻击动画仍活跃 → 可命中敌人 B → 同一套动画依次命中 3–5 个目标，每次 combo_level++ / 伤害递增**。
- 临时无敌 / 免打：`Cps1Collision.cs:368-392` `玩家普通攻击对敌人碰撞_可能对应ASM_94EA` 早退门 `target.Exist==0 || Hp<0`、`target.ShakeLeft != 0`（`:381`，**被碰过的杂兵 3 帧内直接 return**）、`+0x78` 无敌字节（`:388`）；`:1390` `tst.b (0x78,A1) / bne 下一个`。
- 硬直合一 `Cps1Collision.cs:5143-5176` `命中双方硬直_可能对应ASM_7EA2`：`attacker.ShakeLeft == 0` 时**双方同写 `shake=3`**；已有则取 min。`:2059`/`:2109-2110`/`:2395-2409`/`:2782-2783`/`:3309-3310`/`:3469-3470`/`:3866-3867`/`:4363-4364` 各路径都写 `+0x62`（值 1/2/3 不等）。**`+0x62 ShakeLeft` 一个字节同时是：被击者硬直帧数、攻击者再命中门、命中定格长度**（§37 已登记「一字节三用」，本轮只把它放进场景，不重写）。
- 受击反应 `Cps1Collision.cs:4882-4901` `受击反应分发_可能对应ASM_7E4A`：9 项跳表 `0x7E68`（字节偏移 00/02/…/10），`reaction = rb(a3)`，**`target.Hp < 0 && ObjId > 4` 当帧改读「死亡备用字节」**（`:4888-4890`）；`:4921-4946` `StunLeft/StunVal` 清零 + `DmgReaction` + `命中双方硬直`；`:5129-5141` `7E7A` 轻硬直或累计击飞；`:5178-5219` `累计击飞硬直_可能对应ASM_17B2`：`StunVal` 按 `+0x72&6` 分档 + RNG 表 `0x17E4+rng` **字节 wrap 累加**（非饱和），`StunLeft` 窗口。
- 伤害 `L857`（既有结论）：随机伤害 → 难度索引 → `0x6EE84` 修正 → 防御衰减 `damage *= (0x20 - max(hpBand, defense)) >> 5`（`hpBand` 由目标 HP 查 `0x1BF0`）。**按剩余血量分档**。
- 判定框 `Cps1Collision.cs:21` `HITBOX_ROM_BASE = 0xE4F02`；`:55-76` `HitboxGet(id)` 取 `[valX, radX, valY, radY]`，`HitboxBoxWidthX` 从 `id-2` 取框宽，表项布局 `[X框宽, valX, radX, valY, radY]` 10 字节（`:59-61`）；`:1084`/`:1116` 全程按 `A6 = 0xE4F02` 相对偏移。X/Y 二维区间，Z 另算（`:907` valY/radY 注释）。`AtkBoxId` / `HurtBoxId` 是相对基址的字节偏移。**不是逐帧从动画记录带出，是一张全局表按 id 查**。
- `检测下上搓招_1F7C` / `按键历史_2008` 等属上一道跑步题范畴，本轮不写。

## 七条设计结论（正文用材质比喻展开，不照抄清单）

1. **续拳许可**：dino 打中才续（hitstop≠0 是门票，缓冲键在定格帧里攒着），打空整套散；wof 动画播完 + 时间窗内有新按键沿就续，不看命中。→ 湿沙被顶回来一下 vs 空罐头按自己节拍倒。
2. **一拳碰几个**：dino 同帧遍历一片、serial 防同一人重复；wof 同一套动画跨帧扫 3–5 个、3 帧硬直锁错开。→ 一拳闷一片 vs 一刀划一串。
3. **让步方式**：dino poise 累积到 0 才击倒 + 10 多种受击反应 + 抛物线，伤害看「是不是趁它出招/克不克它/剩多少血」连乘；wof 9 档反应、当帧按 HP<0 换死亡备用字节、伤害按剩余血量 band 防御衰减、StunVal 带 RNG 累加。→ 会疲劳的实体 vs 按血量分档的靶子。
4. **停顿/抖动/无敌**：dino 拆三份（hitstop 逐招可变且双方同写、poise 独立、受击态 + serial 免打、屏幕方波留给硬落地/重击/机关）；wof 压进 `+0x62` 一字节（双方同写 3 帧、被击者免打门、攻击者再命中门），另有 `+0x78` 无敌字节。→ 可变长度的黏滞 vs 固定三帧的清脆叩击。**这是「不同材质」最直接的来源**。
5. **判定框**：dino 三轴盒 + 边缘算命中 + 按帧记录带出 + 四角色各自框表 + 命中框对喂火花定位；wof 全局 `0xE4F02` 表按 id 偏移取二维区间。→ 贴着动作形状 vs 固定矩形扫过去。
6. **角色差异落在哪**：dino 四角色共用连拳骨架，只 finisher 一帧按 `b.id==1` 换 pose（穆斯塔法专属）；wof 关羽连拳的动画/`AtkType`/音效编号全按 `ComboLev` 递增查表。呼应 §31「数值 vs 结构」，不重写。
7. **未来优化 wof 先动三处**（用户真实目的，只写设计层、不写实施方案）：命中停顿从固定三帧改成每招一列、给杂兵独立韧性累积、把续拳许可从「动画播完+按键」挪到「命中确认」。三处都在数据/状态层，判定管线不用动；移植角色时最贵的也是这层手感参数，不是招式表。

## 写盘工艺（沿用，不改）

- 片段 `R:\Temp\s94_patch.txt`（中性名、首行空、末行 `---`），写盘 `R:\Temp\s94_write.ps1` 按坑 5 **直接对数组元素就地赋值 `$LA[$ln-1]=$line`**，逐项预校验 `cnt=1` 且 `new != old`，一次 `WriteAllText`（`Join("`n")` + 末尾 LF、无 BOM）。
- 导航 12 处：L16 七处、L46 两处、L47 两处、L50 / L54 / L63 / L65 各一处、L70 一处；同步并预写 A.58 在 §94 提交时一次完成。L16 数字用**写盘后实测**，不引旧数；含 `+` 拼接先赋独立变量；写盘后核 L16、L46 长度变化与 `EndsWith(' | 有效 |')`、四处主题索引 `§94`、L70 `A.58`、片段逐行零缺失、diff 删除纯导航行。
- 表格单元格禁裸竖线；**表格块严格口径先剥离转义竖线 `\|`**（A.54.5 / A.55.3）；校验脚本 `R:\Temp\s94_verify.ps1` 一次性重建，双口径 `file:line` 不去重 / 无后视 / 多根 basename 索引 / OOB 任一候选覆盖 / `s[h]` `p[y]` 字符类 / 悬空阈值 `> 94` / HEAD 基线差等于新区引用数。
- 每块一提交：`DRAFT 定题 → §94 正文 → A.58 回执 → DRAFT 收尾`；提交信息用 `git -c i18n.commitEncoding=UTF-8 commit -F`。`R:\Temp` 脚手架用完即删。
- 硬约束：只谈游戏逻辑本意；repo 侧为主、不过度怀疑；ROM 主要为 data 且仅 `wof_cs` 非常可疑时才查（§11.6 未触发就 0 次 ROM）；wof 侧按 §11.0 只登记不同语境并列事实，不串等价、不评优劣、不把未登记写成缺失、不推断多开发者并行开发的历史成因；宿主对拍 / FBA 实测 / CS 卡值 / 置信度标记 / `_无对应ASM` 开关按 §0 剥掉；不评价移植完成度。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
