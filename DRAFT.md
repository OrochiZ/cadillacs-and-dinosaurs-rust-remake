# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**§90 开工版**：上一版是 `2bc91da` 收尾版（记 §89/A.53 完成状态与 §90 起步），开工读过后删掉重建为本版定题；旧版残差已消费。

## 30 秒版现状（开工当场核）

- HEAD `2bc91da`，`git status --short` 为空，工作区干净。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**。
- `DESIGN_DIFF_NOTES.md` 实测：**14223 行 / 105 张 mermaid / 3104 表格行 / 524 栅栏 / 表格块严格口径 396 块 0 不一致 / §0–§89 / A.1–A.53 正文定义 53 / 双口径不去重窄 1819 宽 1886 缺文件 0 越界 0 / 悬空 0 / CR=0 无 BOM**。顶部 L16 已是 `14223 行 ... 3104 表格行`，**不要引旧数**。
- `R:\Temp` 无残留。本轮开工按 `system-prompt.txt` 读了 `CODEBUDDY.md` → 旧 DRAFT → `git log -8` / `git status --short`。

## 本轮 §90 定题（先查重，不按零匹配排序）

**题目**：`prop/drivers.rs` —— **共享服务层的「存在」已经在 §35 / §36 登记，但三条节拍内部怎么组织、差异压在哪没写**。本节写：pool B 机关把一次「等几帧 → 换一片格子 → 造一个火花 → 响一声 → 退场」拆成**一个公共节拍 + 类自带的表**；调色板循环器把「借位」当步进；四种等待形状把「什么时候触发」压成一个枚举。

一句话结论：这不是「每个机关各写一套破墙动画」，而是**时间由驱动器管、内容由类自带表管**；连「第一个运行帧就步进」都是 `subq.b` 从 0 借位这一个字节行为长出来的。

**排除链（本轮语义查重，继续印证 A.50.3）**：
- `boss_common.rs` / `BossAi` / `gate_table` / `action_table` / `form_index` —— **§16（L2097–L2130）+ §7 + §11 已完整展开**，还明写「不是统一 Boss 决策器」。排除。
- `class10_hold.rs` 的 `c10_claim` / `stomp` —— **§66.4（L9439–L9498）已展开**「认领倒地玩家 / enter_stomp / stomp_step4」，`0x3C8E8` 已在正文伪代码里；`c10_hold0` 抓投属 §24 通用投技。排除。
- `class13.rs` 守卫「chance table 全 0 仍抽一次 RNG 并丢掉」—— **§51 RNG 单流全景「取几次即帧契约·不取也被单测钉死」+ §20.6 已展开**。排除。
- `prop.rs:1-29` 可破坏物四段契约（hit_init / prop_register_hit / pass_10cd0 / mode 4 break）—— **§35（L4998–L5027）已完整展开**，`L5048` 还明写「共享层 = 契约（hit_init / register_hit / break）+ 服务（`drivers.rs` 四类）」。**共享层的存在不是新发现**，本节只展开三条节拍内部组织。
- `prop_tile_clock`（G.$7AE / G.$7AF 差一帧重画）—— **§36 实例表第 7 项 L5118 已登记**。本节只作并列，不重写。
- §73 三层 tilemap / §80 pool C class 34 与 sprite palette 0xB·0xC 闪烁 / §84 摄像机补边 / §70 三 pass 打箱子 / §87 池 E 生命史 / §88 三槽 / §89 舌头——都是既有面，不合并、不串等价。
- `prop/drivers.rs` 的 `PaletteCycler` / `prop_palette_copy` / `prop_palette_cycle` / `prop_burst_fire` / `prop_burst_step` / `BurstWait` / `BurstAction` / `BurstSpec` / `B60` / `B61` / `B63` / `0x94640` / `class 21` / `prop_burst_arm` / `prop_burst_wait` 在主文件 **Grep 全零匹配**：这是本节的差异面。
- **未接线边界（必须写进正文）**：`drivers.rs:28` 是 `#![allow(dead_code)]`，`:27` 明写「A service for the scenery prop tasks of M3: nothing calls it before the first of them is ported」；`prop.rs:29` 说共享服务「shared by the later classes」，`:45-47` 才 `pub mod drivers`。**repo 侧当前没有类调用链**。本节只登记注释钉死的原机节拍（按 §11.0 记按什么索引、起什么作用、何时结束），**不据此断言 rep 侧已生效、不写成「dino 有统一机关驱动」、不评价 rep 侧完成度**；按「不过度怀疑 rep 侧」也不反向怀疑注释。

**dino 取证行号**（`dino-rs/crates/dino-game/src/game/`）：
- `prop.rs:1-2` pool B = 波次控制器（class 15 `0x7B336`）+ Boss 增援控制器（class 22 `0x7BEF6`）；`:4-29` 可破坏物四段契约；`:28-29`「mode 4 (the break) is the prop's own: tiles, sound, effect, then free. The palette cycler, the tile clock and the door burst shared by the later classes are in `drivers.rs`」；`:45-47` `#[path="prop/drivers.rs"] pub mod drivers`。
- `prop/drivers.rs:1-3` 文件头：共享服务层，类自带表（nothing is extracted here）；`:5-10` ① Palette cycler：B60 `0x863AC` / B61 `0x864DA` / B63 `0x869E6` 共用一个 `subq.b #1,+$A4` 借位步进，重装 `+$A5`；reload 8 = 每 9 帧（B60 四套 36 帧循环）、16 = 每 17 帧（B61/B63）；每条 lane 一次 `and.w #$F000 ; or.w (a0)+`（`0x86438`）；B71 `0x89746` 与闪电 `0x77FF6` / `0x78170` 各用自己的计时器但直调 `prop_palette_copy`。
- `:11-15` ② Tile clock：`0x7862A` 读 `G.$7AE` 与 `G.$7AF`，相等就跳过重写；Episode 8 area 1 相位 `((gf+60)/24 mod 4)*4`，`G.$7AF` 是前一帧的值；两字节也是 scroll2 `+$72` / `+$73`，由 `tile_anim_tick`（stage 4 每 8 帧 `0x20956`、stage 7 每 24 帧 `0x2097C`）推进；0/4/8/12 是图片表 `0x78646` 的字节索引。
- `:16-21` ③ Burst：B4 `0x767D8` / B42 `0x83A0A` / B52 `0x85178` / B11 `0x789EE` / B14 `0x7B0BE` 共用「wait → 写 tile block → 造 pool C class 21 `0x94640` → 放音 → 下一 mode free(`0x4938`)」；B12 var 0 是 block table `0x78B86`（`tile_block.rs`）**不是 burst**；B12 var 4 `0x7900E` 自己写 tiles + 六个属性格 + pool C class 0x28 碎片 `0x93362` + 音 0x37，**不走驱动**；B11 的 `0x78A38` 在 tiles 前放 break 音，`prop_burst_fire` 在 tiles 后放；两者都不取 `rand`。
- `:22-23` ④ Hero reach：`pass_10cd0` `0x128F8` 的盒测试，`Z+8` 只是 jab 摘要，无第二条规则（§35 已展开）。
- `:25-28` 类把 countdown 留在自己对象头（`+$A4` / `+$B0` / `+$A0`），每次 update 调一步，与 `BlockTable` 同构；`:27-28` dead_code 说明。
- `:34-49` `prop_tile_clock` / `_prev` / `_edge` 三函数（闭式、上一帧、是否重画）；`:51-71` `PaletteLane{dest,count,list}` 与 `PaletteCycler{reload,steps,lanes,counter,index}`；`:74-87` `PaletteCycler::start` mode 0 清 `+$A4` 与步字，注释明写「第一个运行帧就步进，因为 0 的 countdown 会借位」。
- `:89-105` `BurstWait` 四形状：`Open`（B4/B52，word `+$A0`，fall-through 吃掉 wait 1，第一次 update 就开门）、`Hold`（B14 var 0，零计数只进 mode 4，swap 在下次调用；wait 8 在第 9 次调用写）、`Armed`（B11，byte `+$80`；wait 3 在第 5 次调用 swap）、`Now`（B42，mode 0 直接 swap，无计数器）。
- `:107-160` `BurstBlock{at,cols,rows,src,mode}` / `BurstAttr{at,cols,rows,keep,or_bits}` / `BurstEffect{var,facing}`（pool C class 21，`var` 由类给）/ `BurstSound{Break,Request,Quiet}` / `BurstAction{tiles,attrs,effect,sound}` / `BurstSpec{wait,action}`；**:146-147「The class owns the tables」**。
- `:162-165` `WAIT = +$A0`（B4/B14/B52 word）、`ARMED = +$80`（B11 byte）。
- `:167-172` `prop_tile_phase` 读 `cam.s2.phase72` / `prev73`；`:174-190` `prop_palette_copy`：`(old & 0xF000) | source`，写 `pal.dirty = true`，带 palette RAM 边界断言。
- `:192-212` `prop_palette_cycle`：`subq.b` 后 `n == 0xFF` 才步进 → 重装 `reload` → 步字 `+1` 到 `steps` 归零 → 逐 lane 从 `lane.list` 取第 `step` 个 long 当 set 去 copy；返回「这一帧有没有写」；注释明写**类自己先做 stage/area 门，门不满足就 free**。
- `:214-233` `prop_burst_fire` 固定顺序：`tiles` → `attrs` → `effect`（若有）→ `sound`；`BurstSound::Break` → `snd_break(x)`，`Request` → `snd_request(code,d1,d2)`，`Quiet` 无声；注释明写池 C 空时 `0x94646 bcs` 静默返回。
- `:235-268` `prop_c21_spawn`（class word 0x54 / class 21）/ `prop_c24_spawn`（0x60 / class 24）/ `prop_burst_effect` 用 prop 自身 XYZ。
- `:270-287` `prop_burst_step`：mode 0 arm / 2 wait / 4 fire 后置 mode 6 / ≥6 当帧 `prop_free`；注释「B4/B42/B52 在 mode 0 设自己 Y=0x60，effect 拷它」。
- `:289-309` `prop_burst_arm`：`Now` 当帧 fire + mode 6；`Open`/`Hold` 进 mode 2 写 word 并 **fall-through 到 wait**；`Armed` 进 mode 2 写 byte 后 `rts`（不 fall-through）。
- `:311-336` `prop_burst_wait`：`Armed` 用 byte `+$80`、`Open`/`Hold` 用 word `+$A0` 各减 1；归零进 mode 4；**只有 `Open` 立刻 fire 并置 mode 6**，`Hold` 要等下一次 mode 4 调用。

**六条设计结论**：
① 共享层的存在已登记（§35 L5048 / §36 L5118），本节补的是「时间 / 内容分离」：三条节拍都把**什么时候做**放在驱动器（一个 countdown、两个全局字节、一个 mode 链），把**做什么**放在类自带的表（`PaletteLane.list` / `BurstAction.tiles` / 图片表），驱动器不读表内容、只按索引取。
② 调色板循环器把「借位」当步进：`subq.b #1,+$A4` 从 0 减到 0xFF 才有 borrow，`mode 0` 清 0 意味着**第一个运行帧就写一套颜色**；重装 8/16 得到每 9 / 17 帧一步（B60 四套 36 帧、B61/B63 每 17 帧）。与 §80 的「按帧号每 4 帧切 0xB」不同：那里是 flow/tally 驱动两格 sprite palette，这里是场景机关共用一条 lane 链并**保留亮度 nibble**。
③ `prop_palette_copy` 用 `(old & 0xF000) | source` 保住地图亮度；每条 lane 独立 dest / count / list；B71 与闪电不共用 countdown、只共用这一条 copy —— **「共用节拍」与「共用写入原语」是两级**，不混为一谈。类自己先做 stage/area 门，门不满足当帧 free：退出条件在类里，节拍在驱动器里。
④ tile clock 用**两个全局字节差一帧**表示「该重画了」：`G.$7AE` 当前、`G.$7AF` 上一帧，相等就跳过；相位 `((gf+60)/24 mod 4)*4` 是 0/4/8/12 的图片表索引。§36 已登记这一条，本节只作并列，不重写。
⑤ burst 是**一条四步流水线 + 四种等待形状**：`mode 0 arm → 2 wait → 4 fire → 6 free`；fire 内固定 `tiles → attrs → effect → sound`；`Open` 的 wait 1 被 fall-through 吃掉，所以「生成后未更新的那一帧」本身就是设计里的等 1 帧；`Hold` 的零计数只进 mode 4、swap 要下一次调用；`Armed` 用 byte 计数器且 arm 后直接 `rts`；`Now` 无计数器当帧完成。差异全压在一个枚举与类自带表，驱动器只有一份。
⑥ 生命周期与边界：`prop_burst_step` 的 mode ≥6 当帧 free；全程**不取 RNG**（与 §51 帧契约不同层）；池 C 满时 `prop_c21_spawn` 静默返回但仍推进 mode（与 §76「池满少一个就算了」同族）；B12 var 0 / var 4 是明确不走驱动的例外。**`drivers.rs` 当前 `dead_code`、repo 侧无类调用链**：本节只登记注释钉死的原机节拍，不据此断言 rep 侧已生效，也不写成「dino 有统一机关驱动」；按 §11.0 不抄表内容、不评价 rep 侧完成度。

**wof 侧按 §11.0 只登记不同语境并列事实**（四格都是既有注释 / 调用面复述）：`Cps1CameraRuntime.cs:702` / `:725`（相机跨列 / 跨行更新 Scroll2，语境 = 卷屏补边，§84 已用）/ `Cps1CoroutineScheduler.cs:1113-1117`（`includePaletteStep: false`、FBA 实测 f=9918 的任务体，语境 = 协程让出帧时是否带 palette 步）/ `Cps1Actor20Runtime.cs:229-231` 与 `Cps1Actor25Runtime.cs:155-157`（`ProfilePaletteTable + +0x17` 逐对象查表写 `+0x5F`，语境 = 对象级 palette profile）/ `Cps1Actor21Runtime.cs:37`（palette 表读并写 `+0x9A/+0x9C`，语境 = 对象头 palette 字段）。**不串等价、不评优劣、不把未登记写成缺失、不据此断言原机缺机制**；wof 侧未见「机关破墙共享节拍」的直接注释，不臆断；0 次 ROM 取证，§11.6 未触发；`_无对应ASM` 开关与 FBA 逐帧对拍按 §0 剥掉。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；临时片段用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s90_patch.txt` / `a54_patch.txt`。
- 大段中文 markdown 用 Write 落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → **按行号直接对数组元素就地赋值**（坑 5）→ 逐项预校验 `cnt=1` 且 `new != old` → 一次 `WriteAllText`（`Join("`n")` + 末尾 LF，无 BOM）。**写盘命令落 `.ps1` 再执行**，不用长命令行 here-string（上一轮被打断过）。
- 坑 1：数组字面量里 `+$var+` 解析错位，含 `+` 的字符串先赋独立变量；写盘后核 L46 长度变化与 `EndsWith(' | 有效 |')`。
- 坑 2：回执别写「`§N+` 引用 0」，改写「超出 §N 的章号引用 0」。
- 坑 3：表格单元格禁止裸竖线（位或、绝对值符号都算），精确表达式放非表格伪代码块。
- 坑 4：`file:line` 全量校验**不去重**、无 `(?<![\w/])` 后视、多根 basename 索引、`s[h]` / `p[y]` 字符类；OOB 判定用「任一同名候选文件行数覆盖即通过」。
- 坑 5：导航替换别用 `[ordered]@{}` 存数字行号再 `ContainsKey($i+1)`（int）查；改 `$LA[$ln-1]=$line`。写盘后核 L16 新数字、L46 长度与 `EndsWith(' | 有效 |')`、四处主题索引 `§N` 命中、L70 `A.N` 命中、diff 删除恰为 8 条导航行。
- 导航固定 12 处：L16 七处、L46 两处、L47 两处、L50 / L54 / L63 / L65 各一处、L70 一处。回执追加时不改导航结构，只刷新 L16 行数与表格行数并补 A.N 正文定义。
- 校验固定项：片段逐行零缺失 / 表格块严格口径 0 不一致 / 全量 `file:line` 双口径零缺零越界且 HEAD 基线差等于新区引用数 / `CR=0 BOM=False` / `git diff -U0` 删除行逐条核为纯导航行 / 悬空章号 0 / 写盘后导航命中复核。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；提交用 `git -c i18n.commitEncoding=UTF-8 commit -F`。
- 每块一提交：DRAFT 定题 → §90 正文 → A.54 回执 → DRAFT 收尾，四笔；顶部规模行、导航在 §90 提交时一次同步并预写 A.54。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
