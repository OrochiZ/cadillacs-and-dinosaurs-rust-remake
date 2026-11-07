# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**§93 开工版**：上一版是 `b2eba96` 收尾版（记 §91/A.55 与 §92/A.56 完成状态、方法残差、§93 起步），开工读过后消费完毕，旧版残差不再保留。

## 30 秒版现状（开工当场核）

- HEAD `b2eba96`，`git status --short` 为空，工作区干净。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**。
- `DESIGN_DIFF_NOTES.md` 实测：**14945 行 / 108 张 mermaid / 3284 表格行 / 546 栅栏 / §0–§92 / A.1–A.56 正文定义 56 / 表格块严格口径 420 块 0 不一致 / 双口径不去重窄 1923 宽 1990 缺文件 0 越界 0 / 悬空 >92 为 0 / CR=0 无 BOM**。顶部 L16 已是 `14945 行 ... 3284 表格行`，**不要引旧数**。
- `R:\Temp` 无残留。本轮开工按 `system-prompt.txt` 读了 `CODEBUDDY.md` → 旧 DRAFT → `git log -8` / `git status --short`，未回读 transcript。

## 本轮 §93 定题（先查重，不按零匹配排序）

**题目**：`flow/name_entry.rs` —— **三个玩家各有一份 32 字节块，却共用一个帧戳：高分名字输入把四套计时、两套按键判据和一次结算演出压进同一个状态通道**。

一句话结论：`name_frame(i)` 对三个玩家各调用一次，但「这一帧是不是同一帧」由一个全局 word 帧戳判定；全局的排名文字闪烁只在第一份调用里减一次，其余两份只读不减。每个玩家私有块里同时跑着 20 秒表、420 空闲帧、方向重复、按键锁、光标与完成闪烁，**三条结束路径都汇到同一个 `done` 字节**，之后才做脏话过滤 / 插入 / 排序 / 4 次闪烁——**结算先于演出，写完表与演完是两个阶段**。

**排除链（A.50.3 / A.54.2 / A.56.2 双向化，两个方向都核）**：
- **§41.7 / §60.6 / A.24 保留清单**：`name_entry` 与其余 12 个 flow 子模块一起被列为「逐类展开」保留（L5801、L8285、L8298、L9573、L9586、L9638、L9772），`name_qualify` 只在 §55 L7372 / L7415 / L7433 作为续关交接被提过一句。按 `9d8145f` 口径，保留是**取材范围声明不是闸门**；本节按 A.26「紧邻保留边界取横切面」先例，只取一条跨帧契约，**不逐状态抄 679 行、不把保留清单当禁令、也不把「零匹配」当定题依据**。
- **§55 续关 / §30 整局流程**：`seconds < 0 → name_qualify` 是交接点；`flow_continue_*` 的四态 sub 层、`flow.mode` 8 态已展开。本节从 `name_qualify` 之后开始，不重写。
- **§57 三类计时器**：全局时间门 / 事件补偿 / 每帧递减；本节是**每玩家私有块加一个全局帧戳**，没有全局暂停门，只有「同帧共享」一层。同族不同层，不合并。
- **§14 输入边沿 / §81 打字机 fast / §92 快进**：三种按键判据（边沿一次打完 / 电平持续三倍 / 边沿加锁 + 方向电平），本节同一屏里两种并存，只作并列、不串等价。
- **§40 结算 / §26 HUD 分数 / §60 ranking_cut**：名次与分数归属、2000 格写入被边界切断已展开；本节只写「按 rank 插入再按分数排序」两步契约与 `done` 之后的结算序，不重写结算与 CUTS。
- **§86 影片时间线 / §60 长任务跨帧**：计数撞表只跑一个 handler / 长任务被切断；本节是「`done` 之后先结算再演出」，不合并。
- **§0 边界**：单测 `name_entry_a17_matches_mame`（`name_entry.rs:584-654`）逐帧对拍 `flow_k-name-entry`、sound queue、GFXRAM，属宿主 / 工程层，只登记存在不展开；`_无对应ASM` 开关与 FBA 逐帧对拍按 §0 剥掉。
- **主文件零匹配面**：`name_same_frame` / `seen_frame` / `same_frame` / `IDLE_FRAMES` / `name_dirs` / `name_profanity` / `name_insert` / `0x1616C` / `0x161DA` / `0x16260` / `GLYPH_RUB` / `finish` / `flashes` 全部零匹配；但定题依据是上面七条语义查重，不是零匹配排序。

**dino 取证行号**（`dino-rs/crates/dino-game/src/game/flow/name_entry.rs`，679 行）：
- `:1-11` 文件头：一局结束后 qualifying score 的名字输入（join state 0xA / 高分表）；原机例程 `0x154EE` 资格、`0x15AE2` setup、`0x15BE4` 每帧、`0x15C7A` 同帧标志、`0x15CB2` 输入、`0x15D1A` rank blink、`0x15D3C` / `0x15D74` rank 文字、`0x15DC2` / `0x15DE4` 空行、`0x15E3A` 键、`0x15EE8` 输入字形、`0x15F86` 方向重复、`0x15FB4` 字母、`0x160FC` 光标、`0x1616C` 脏话过滤、`0x161DA` 插入、`0x16230` 存储、`0x16260` 排序、`0x74A4` state 0xA。块布局 32 字节 / 玩家 `G.-$711C + 0x20 * player`；共享全局 `G.$7013` 同帧标志、`G.$701A` 帧戳、`G.$7017` rank blink 计数；`G.$5E4 = Flow::b5e4`。
- `:15-23` 三个常数：`IDLE_FRAMES=0x1A4`（420）、`SECONDS=0x14`（20）、`FRAMES_PER_SECOND=0x3C`（60）、`GLYPH_RUB=0x1C`（28）、`GLYPH_END=0x1D`（29）。
- `:25-59` `Block` 32 字节字段，`+$19` 之后不建模；`:62-115` `peek` / `poke` 按原机偏移读写字节。
- `:117-127` `NameEntry{blocks:[Block;3], seen_frame:u16, same_frame:bool, blink:u8}` —— **三个私有块 + 三个全局字节**。
- `:129-144` `name_qualify`：`p.b10a <= 10 && tenth < p.score` 才 `join[i].state=0xA`、`b5e4=1`、`name_setup(i)`；否则 `state=0xC`、`b5e4=0`。
- `:146-162` `name_setup`：`idle=420`、`secs=20`、`fps=60`、`rank` 取玩家 `b10a`、`name=四个空格`、`shown=[0x20;4]`、`glyph=0`、`done=0`、`finish=0`、`blink=w.frame`；注释明写**原机不清 `count` 与键字节，port 也不清**。
- `:164-179` `name_state`：`flow.mode == 0x1C && b507 != 0`（结局在跑）时 **return 整段 parked**；否则 `name_frame(i)` 返回 true 才 `state=0xC`、`b5e4=0`、`started &= !(1<<i)`、`flow_join_clear`。
- `:181-190` `name_same_frame`：`w.frame == seen_frame` → `same_frame=true`，否则把 `seen_frame` 更新为当前帧。
- `:192-229` `name_frame`：先 `name_same_frame()` → 写 `cur=w.input[i]` / `prev=front.prev_input[i]` → `done != 0` 就转 `name_finish` → `fps--`，到 0 重装 60 并 `secs--`，`secs==0` 写 `done=1` → `name_blink` / `name_keys` / `name_draw_letters` / `name_draw_cursor` → `idle--`，小于 0 写 `done=1`。
- `:231-261` `name_finish`：`finish==0` 时 `finish+=2`（一次性门）→ `name_profanity` → `name_insert` → `blink=0x1E`、`flashes=4`；之后每帧 `blink--`，**`old==0` 借位才 `flashes--`**，借位溢出返回 true；`blink < 5` 画空行否则画 rank 文字 + 字母。
- `:263-278` `name_blink`：**只有 `!same_frame` 才递减全局 `flow.name.blink`**，借位重装 `0x14`；`blink > 5` 画 rank 文字，否则画 6 列空行。
- `:280-327` `name_keys`：`lock` 每帧饱和减 1；`name_dirs` 给方向位；左右改 `glyph` 并重置 `idle=420`；`count==0` 跳过 RUB、`count>=3` 左移封顶、`glyph` 越界回绕到 RUB / END；攻击判据 `(cur & !prev) & 0x10` 且 `lock==0` 才 `lock=4`、`idle=420`、`name_enter`。
- `:329-344` `name_dirs`：`cur & 0xF == 0` 或 `(cur & 0xF) ^ b.prev != 0` → `rep=0x18`（24 帧）并**立即返回**当前方向；否则 `rep--`，到 0 重装 4 再返回。**新方向立即生效，之后先等 24 帧再每 4 帧重复**。
- `:346-374` `name_enter`：`END` 写 `done=1`；`RUB` 擦最后一个字母并把 `glyph` 回退到它的字形；其它按 `0x15F34` 表取字母写入 `+6+count` 与 `+$10+count`，`count++`，满 3 把 `glyph` 设 `END`。注释与单测明写**第 4 个及以后字母继续写进块**（`+$A` 是 fps 高字节、`+$10` 起是 shown 字形），`peek` 超出 `+$19` 返回 0。
- `:376-397` `name_draw_letters` / `name_draw_cursor`：四张 2x2 字形画在 `name_base(i)+0x400`，光标画在 `count` 之后那个槽；**(frame - b.blink) < 6 显示光标，否则画空并把 b.blink = frame**——`blink` 在输入阶段是「光标上次翻转的帧戳」。
- `:400-463` `name_glyph` / `name_blank` / `name_cells2x2` / `name_base`（按 `b4cf` 选 2 / 3 人布局的 scroll1 基址）/ `name_rank_text`（1ST..10TH 三张 2x2）/ `name_tile2x2` / `name_blank_rows`（6 或 16 列）。
- `:465-481` `name_profanity`：`0x161B2` 表 5 条三字母名字，命中则把名字替换成对应替换串、第 4 字节设空格。
- `:483-513` `name_insert`：`rank` 1..10 → `idx=rank-1`；从 `idx+1..=49` 倒序把每条往下挪一格（**第 50 条丢失**）；写 `score / name / chr / stage+1`（`+$A` 保留旧值）；再 `name_sort`。
- `:515-528` `name_sort`：50 条选择排序，有符号比较、平局早者在前。
- `:531-679` 单测：`block_bytes` / `table_bytes` 按原机布局重建字节；`name_entry_a17_matches_mame` 逐帧对拍（宿主层，按 §0 剥掉）；`letters_past_the_third_are_stored_on_into_the_block` 钉死第 4 个字母起写进块内其它字段、`count=40` 仍不越界。

**七条设计结论**：
① **三个私有块 + 一个全局帧戳**：`NameEntry` 里 `blocks[3]` 各管自己的输入与字母，但 `seen_frame / same_frame / blink` 是全局一份；`name_same_frame` 用 `w.frame == seen_frame` 判「这一帧是否已被别的玩家跑过」，**不是每玩家一个计时器**。与 §92「按轮 / 按 vblank」分层同族但不同层：这里是「按帧 / 按调用次数」，不合并。
② **一个 32 字节块压四套计时加三条状态通道**：`secs/fps`（20 秒由 60 帧换算）、`idle`（420 帧、任何有效输入重置）、`rep`（方向 24 帧首发 / 4 帧重复）、`lock`（攻击后 4 帧）、`blink`（光标 6 帧 / 完成时 30 帧倒计时）、`flashes`（4 次）、`done`（结束）、`finish`（表已写门）、`count/glyph/shown`（字母与图片）。与 §57 三类计时器同族但**没有全局暂停门**，只有「同帧共享」一层；不抄 32 字节字段表，只写它们怎么互相借用。
③ **同一字段跨阶段复用**：`blink` 在输入阶段是「光标上次翻转的帧戳」（`frame - blink < 6`），`name_finish` 里被重装 `0x1E` 当「4 次 ×30 帧」倒计时；`old == 0` 借位才减 `flashes`——**借位当步进**，与 §90 `prop_palette_cycle` 的 `subq.b` 借位同族，不串等价。
④ **两套按键判据并存**：方向用「低 4 位电平是否变化」立即响应 + 私有 `rep`（新方向等 24 帧、按住每 4 帧）；攻击用 `cur & !prev & 0x10` **边沿** + 4 帧 `lock`。与 §92 电平持续快进、§81 边沿一次打完、§14 输入边沿只作并列：这里同一屏里两种并存，且 `b.prev` 是上一帧输入字节。
⑤ **三条结束路径汇到一个 `done`**：20 秒到、420 帧空闲、选中 `END` 按攻击，都只写 `done=1`；下一帧起 `name_finish`，`finish` 从 0 加 2 当一次性门，先脏话过滤 → 按 rank 插入（表下移一格、第 50 条丢失）→ 50 条排序 → 4 次 ×30 帧排名行闪烁才返回 true。**结算先于演出，且「写完表」与「演完」是两个阶段**；与 §86「计数撞表只跑一个 handler」不同路，不合并。
⑥ **资格门与 parked 交接**：`rank <= 10` 且 `tenth < score`（无符号 long）才进 join state 0xA 并 `b5e4=1`；否则直接 0xC。`name_state` 在 `flow.mode == 0x1C && b507 != 0`（结局在跑）时**整段 return**，等结局结束才逐帧推进输入。与 §55 交接、§30 `flow.mode` 只作并列，不重写。
⑦ **块即内存的边界按 repo 侧如实登记**：第 4 个及以后字母会继续写进块内其它字段，`peek` 在 `+$19` 之外返回 0，绘制不读 ROM 之外；`name_setup` 不清 `count` / 键字节（注释明写原机不清）。按 repo 侧如实登记为块布局副作用，**不评优劣、不臆断原机另有保护、不写成缺陷、不据此断言 rep 侧完成度**。

**wof 侧按 §11.0 只登记不同语境并列事实**（四格都是既有注释 / 调用面复述；FBA 实测 / CS 卡值 / 逐帧对读 / 置信度标记 / `_无对应ASM` 开关按 §0 剥掉）：
- `Cps1ObjectRuntime.cs:3718-3725`：ROM `0x113A6` 高分榜重绘协程的跨帧推进，让出点 `0x11400 jsr 0x866`，且必须放在 `0xD000` 消费者之前，语境 = **逐行重绘的协程位置**。
- `Cps1StaticInitialSnapshot_无对应ASM.cs:91`：`Cps1HudRuntime` 的「高分榜重绘进度」，语境 = **宿主静态快照的进度字段**。
- `Cps1Collision.cs:184-190`：`0x0DE8` 刷新最高分并挪动最高分标记，语境 = **分数结算时的最高分标记刷新**。
- `Cps1Memory.cs:580`：`C22C` 排名文字 / 字形写 `0x90A08C`，语境 = **排名字形的 GFXRAM 写入**。
- 四格**不串成等价、不评优劣、不把未登记写成缺失**；wof 侧未见「三玩家私有块 + 全局帧戳」的直接注释，不臆断、不据此断言原机缺机制；0 次 ROM 取证，§11.6 未触发。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；临时片段用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s93_patch.txt` / `a57_patch.txt`。
- 大段中文 markdown 用 Write 落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → **按行号直接对数组元素就地赋值**（坑 5）→ 逐项预校验 `cnt=1` 且 `new != old` → 一次 `WriteAllText`（`Join("`n")` + 末尾 LF，无 BOM）。**写盘 / 校验都落 `.ps1` 再执行**，不用长命令行 here-string。片段首行空 + 末行 `---`。
- 坑 1：数组字面量里 `+` 拼接解析错位，含 `+` 的字符串先赋独立变量；写盘后核 L46 长度变化与 `EndsWith(' | 有效 |')`。
- 坑 2：回执别写「`§N+` 引用 0」，改写「超出 §N 的章号引用 0」。
- 坑 3：表格单元格禁止裸竖线；精确表达式放非表格伪代码块。**表格块严格口径必须先剥离转义竖线 `\|`**（A.55.3）。
- 坑 4：`file:line` 全量校验**不去重**、无 `(?<![\w/])` 后视、多根 basename 索引、`s[h]` / `p[y]` 字符类；OOB 用「任一同名候选文件行数覆盖即通过」；悬空阈值随最大章号调为 > 93。**校验脚本属一次性脚手架，用完即删，需要就重建**；重建按修正后口径，别再漏剥 `\|`。
- 坑 5：导航替换别用 `[ordered]@{}` 存数字行号再 `ContainsKey($i+1)`（int）查；改 `$LA[$ln-1]=$line`。写盘后核 L16 新数字、L46 长度与 `EndsWith(' | 有效 |')`、四处主题索引 `§N` 命中、L70 `A.N` 命中、diff 删除恰为 8 条导航行。
- 导航固定 12 处：L16 七处、L46 两处、L47 两处、L50 / L54 / L63 / L65 各一处、L70 一处。回执追加时不改导航结构，只刷新 L16 行数与表格行数并补 A.N 正文定义。
- §93 摘要（L46 与四行主题索引共用，禁裸竖线）：`§93（三个玩家各一份 32 字节块却共用一个帧戳 / name_same_frame 用 w.frame 判同帧 全局排名文字闪烁只减一次 / 私有块压 20 秒表·420 空闲帧·方向重复 24 首发 4 重复·攻击锁 4 帧 / blink 在输入阶段是光标帧戳 完成时重装 0x1E 当 4 次 30 帧倒计时 借位才减 flashes / 方向读低 4 位电平变化 攻击读边沿加锁 两种判据并存 / done 汇聚 20 秒·空闲·END 三条结束路径 finish 门先脏话过滤·按 rank 插入·50 条排序·4 次闪烁 / name_qualify 要 rank 小于等于 10 且第十名分数更低 结局在跑时整段 parked / 第 4 个字母起写进块内其它字段按 repo 侧如实登记 / wof 按 §11.0 只登记高分榜重绘协程·快照进度·最高分标记·排名字形 GFXRAM 写入不同语境）`
- 校验固定项：片段逐行零缺失 / 表格块严格口径 0 不一致 / 全量 `file:line` 双口径零缺零越界且 HEAD 基线差等于新区引用数 / `CR=0 BOM=False` / `git diff -U0` 删除行逐条核为纯导航行 / 悬空章号 0 / 写盘后导航命中复核。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；提交用 `git -c i18n.commitEncoding=UTF-8 commit -F`。
- 每块一提交：DRAFT 定题 → §93 正文 → A.57 回执 → DRAFT 收尾，四笔；顶部规模行、导航在 §93 提交时一次同步并预写 A.57。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
