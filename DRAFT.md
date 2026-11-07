# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是开工读旧版（收尾版，记着 §87 候选）后删掉重建的新版：旧版残差已全部消费。

## 30 秒版现状（开工重建时）

- 当场核：HEAD `b7d73ae`，`git status --short` 为空。开放目标 `长时间自主推进` 仍 active，**未收口、不宣称完成**。
- 当前 `DESIGN_DIFF_NOTES.md`：13500 行 / 102 图 / 2918 表格行 / 506 栅栏 / 表格块严格口径 370 块 0 不一致 / §0–§86 / A.1–A.50 / 附录定义 50 / 双口径窄 1760 宽 1827 全命中 / LF 无 BOM。**写盘后按实测刷新顶部规模行，不引旧数。**
- 上一轮 6 笔提交：`6cd48a6` DRAFT 开工 → `aace74c` §85 → `18da0d4` A.49 → `504d66b` §86 → `35e2331` A.50 → `b7d73ae` DRAFT 收尾。

## 本轮 §87 定题（先查重，不按扫描排序）

**题目**：`item/blast.rs` —— 同一个「攻击者」身份下，池 E 六类对象各自的生命史。
一句话结论：攻击者不是一类对象，而是池 E 里若干类对象**在某一帧共同声明的一种身份**；身份由「这一帧有没有进 `$671A`」决定，而每类对象自己决定「我这一生有几帧、第几帧登记、什么时候转成别的对象」。

**排除链（本轮两次印证 A.50.3「函数名零匹配 ≠ 机制未展开」）**：
- `item/weapon.rs`（63 函数 50 零匹配）**排除**：§21 已记 `KINDS` 三元组与 15 类型、`item/weapon.rs:1-26` / `:36-52`；§76 / L11614 已明写「设施共用，差异压在一个变体 / 分支里，不另起一套状态机」；L11564 `item_land_check`、L11560 `LIFE = 0x258`、§82 / §83 的 15 类型保留清单都已登记。想写的结论与既有正文重复。
- `item/blast.rs` 的**共性**也已登记：§61 / L8378 引 `blast.rs:6-8`「explosions and projectiles are attackers」、L8388「`item_register_attacker`（`item.rs:248`）每帧登记」、L10244 三张注册列表、§70 命中下游。**因此 §87 只写差异面，不重写共性**：`item_blast` 的 5 个 kind 分支、4 族弹道、一帧攻击盒、火把 overlay 的各自生命史全零匹配。
- `effect.rs`（`raw_load` / `raw_tick` / `fx_tick_sprite_frame`）与 `player_weapon.rs` 留作后续候选，本轮未用。
- 已排除（沿用旧版）：`script.rs` / `flow/*` / `enemy/scenery.rs` / `car.rs` / `camera.rs` / `terrain.rs` / `hud.rs` / `snd.rs` / `trace.rs` / `flow/mame_check.rs` / `enemy_combat.rs` / `player.rs` / `enemy.rs`。

**dino 取证行号**（`dino-rs/crates/dino-game/src/game/item/blast.rs`）：`:1-8` 文件头六类清单与攻击者语义 / `:12-25` 七张表常量 / `:28-48` `item_explosion_body` 造爆炸（复制 who/id/坐标/airborne/`+$70` 为源，池满丢弃）/ `:50-58` 音效与 `item_d7 = 23 - slot` / `:60-65` `blast_setup` / `:67-77` `item_blast` 按 `var26` 五分派 / `:79-94` `blast_run` 与 `draw_list_add_visible_item` / `:96-129` kind0 / `:131-159` kind1 与撞墙停 / `:161-168` `blast_attack` 取一次 serial / `:170-189` kind2 / `:190-221` kind3 / `:222-247` kind4+ 小火焰闪烁 / `:248-268` `item_bullet` / `:269-337` `bullet_init` / `:338-376` `bullet_run` 隔帧碰撞 / `:377-437` `item_overlay` 跟随火把 / `:438-466` `item_shell` / `:467-497` `shell_run` / `:498-526` 尘土与 `shell_end` / `:527-553` `item_projectile` / `:554-585` `projectile_run` / `:586-615` `item_gun_shot` / `:616-633` `pellet_run` / `:634-649` `item_attack_box_spawn` / `:650-680` `item_attack_box` 只活一帧 / `:681-710` 单测。
上游并列：`item.rs:248` `item_register_attacker`（§61 已登记）、`item.rs:367` `item_despawn_near`、`combat_lists_reset`（§48）。

**六条设计结论**：① `item_blast` 五 kind 共用 `mode 0 init → 2 run → 4/6 free`，`blast_run` 统一「动画步 → 播完 free → 每帧登记攻击者 → 按 `visible` 进绘制表」；② kind 差异全压在 init 的一次性写入（kind0 按 `airborne` 选 attack 0x54/0x56 与动画 0/1、落地 `cam.shake_req=3`；kind1 滚动要 `item_terrain`+`motion` 且撞墙 `sub+=2` 停；kind2 shake+0x6E；kind3 敌人炸弹 `who=0xFF` 不记分；kind4+ 小火焰**没有自己的攻击**）；③ `item_d7 = 23 - slot` 让**池槽号参与小火焰闪烁相位**（`(frame + d7)` 奇偶），与 §45 `(depth,handle)` 排序、§50 对象池同族；④ 四族弹道各自决定生命史：bullet 按 8 字节记录取 vx/anim/atk/aim、玩家枪按 `+$EA` 锁定目标、其余随机 vz、`bullet_run` **按槽号奇偶隔帧碰撞**、撞地/墙/水转 mode 4 火花；shell 抛物线+尘土+接触生成 class 1 kind 1 小爆炸；projectile 水平速度由距离 32 位除以 `0x39`、弧线 `vy=-0x500`、低于目标高度 `+$A2` 爆炸、非零 variant 还留 class 11 攻击盒；pellet 飞 `0xC0` 像素内、命中即 free；⑤ `item_attack_box`（class 11）**只活一帧**，把「一次攻击」做成池对象而不是玩家状态机里的 flag；⑥ `item_overlay`（class 6）跟随火把，靠宿主 `+$2C` 帧标志决定装载 swing / idle flame 列表，Z +2/-1 由帧奇偶决定前后，火把消失或不再是同一把武器就结束。

**wof 侧按 §11.0 只登记不同语境并列事实**（四格都是既有注释 / 调用面复述）：`Cps1EffectActorRuntime.cs:363` `效果对象_爆炸特效环_对应ASM_630E` / `:4007` `ObjId 9（落地爆炸体：0x6E0 动画 + 受击帧翻转）` / `:4315` `4E390..4E3B4：落地爆炸` / `Cps1PlayerLogic.cs:5417` `1C09E move.w #$A,(0x94,A0) ; 攻击盒 ID`（wof 攻击盒是玩家对象字段）。不串等价、不评优劣、不把未登记写成缺失；0 次 ROM 取证，§11.6 未触发。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；临时片段用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s87_patch.txt` / `a51_patch.txt`。
- 大段中文 markdown 用 Write 落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → 按行号重建数组 → 逐项预校验 `cnt=1` 且 `new != old` → 一次 `WriteAllText`（`Join` + 末尾 LF，无 BOM）。
- **坑 1**：PowerShell 数组字面量里 `+$var+` 会解析错位（§85 的 L46 丢摘要与表格结尾，长度恰好抵消）。所有含 `+` 拼接的字符串**先赋独立变量**再进数组；写盘后核 L46 长度变化与 `EndsWith(' | 有效 |')`。
- **坑 2**：回执里别写「`§N+` 引用 0」这种会被简单悬空正则误报的措辞，改写「超出 §N 的章号引用 0」。
- 导航固定 12 处：L16 七处（行数 / mermaid 数 / 表格行数 / `A.1–A.N` / A.N 条目 / A.N 位置 / `§0–§M 全部结论`）、L46 两处（章节列表 `/ §M |`、主题摘要 `；§M（…） | 有效 |`）、L47 两处、L50 / L54 / L63 / L65 各一处 `、**§M（…）**`、L70 一处 `、A.N`。回执追加时不改导航结构，只刷新 L16 行数与表格行数两个数字并补 A.N 正文定义。
- 校验固定项：片段逐行零缺失 / 表格块严格口径排除转义竖线 0 不一致 / 全量 `file:line` 双口径（`s[h]` / `p[y]` 字符类 + 多根索引）零缺零越界且差额等于新区引用数 / `CR=0 BOM=False` / `git diff -U0` 删除行逐条核为纯导航行。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；提交用 `git -c i18n.commitEncoding=UTF-8 commit -F`。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
