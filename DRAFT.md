# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 `DESIGN_DIFF_NOTES.md`（git 跟踪）。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是开工读旧版（记着「§85 尚未定题」）后删掉重建的新版：旧版残差已全部消费。

## 30 秒版现状（开工重建时）

- 当场核：HEAD `1503724`，`git status --short` 为空。开放目标 `长时间自主推进` active，主线 `DESIGN_DIFF_NOTES.md`，按「一节一提交」推进，仍开放、不收口。
- 已落盘：口径澄清（`9d8145f`）、DRAFT 机制（`21e6974`）、§84 背景流送（`96cdcc0`）、A.48 回执（`adf49ef`）、上一轮 DRAFT 重建（`1503724`）。
- 当前文件 13050 行 / 100 图 / 2786 表格行 / 496 栅栏 / §0–§84 / A.1–A.48 / 悬空 0 / 窄 1721 宽 1788 双口径全命中 / LF 无 BOM。写盘后按实测刷新顶部规模行，不引旧数。

## 本轮 §85 定题与取证（旧版写的「尚未定题」已作废）

- 选题：`car.rs` **mode 2 驾驶态的每帧数据流**。§32 只写 4 态骨架与字段协议，`§32.5` 的「未做（保留，不扩张）：`car.rs` 各 sub 步逐段、`0x8C886` 转向表 / `0x8C404` bump 表数值」按 `9d8145f` 口径澄清是**历史取材范围声明，不是闸门**。
- 查重：`prop_car_drive` / `prop_car_steer` / `prop_car_stick` / `prop_car_speed` / `prop_car_band` / `prop_car_bump` / `prop_car_smoke` / `prop_car_riders` / `prop_car_seats` / `STICK` / `PAIRS_B` / `BUMPS` / `WHEEL_ANIM` / `TVX` / `TVZ` / `NEW_SEAT` / `BUMP_T` / `car_riders` / `b119` / `bc0` 在笔记里几乎全零匹配；仅 `prop_car_wheel` 在 L4654 作 §32 伪代码一行、`car_on` 在 §15/§47 作门控、`0x8C886` 在 L2025/L4706 作地址与范围声明出现。
- 核心取证行号（`dino-rs/crates/dino-game/src/game/`）：`car.rs:14-38`（字段/表常量）、`:92-107`（mode 分派）、`:356-371`（`prop_car_seats`）、`:397-404`（`prop_car_carry`）、`:412-480`（`prop_car_drive` 每帧序列与帧尾）、`:483-492`（`prop_car_riders`）、`:495-519`（`prop_car_steer` 分档）、`:524-549`（`prop_car_stick` 三表）、`:553-564`（`prop_car_speed` 逼近）、`:567-585`（`prop_car_band` 窗口）、`:590-620`（`prop_car_bump`）、`:623-632`（`prop_car_smoke`）、`:638-690`（`prop_car_wheel`）、`:693-702`（`prop_car_dust`）、`:709-748`（`prop_car_end`）。
- 读方/下游：`spawn.rs:35-39,155`、`trace.rs:1439-1442`（`car_riders`/`car_on`/`car_obj` 逐帧存档字段）、`combat.rs:87`（`car_mode && car_on` 门）、`script.rs:156,305,386`（`bc0` 当过场输入门）、`boss_common.rs:563-575`（`b4db`/`bc0` 单测）、`player.rs:595-598`（`b516`）、`terrain.rs:658`、`hud.rs:498`（`b4d5`）。
- wof 侧按 §11.0 只登记不同语境并列事实：`Cps1HorseRuntime.cs:40-70`（马池每帧按 `ActStatA` 分派）、`:234-249`（上马门控写 `Mount`/`MountObj`）、`:263-304`（A=04 离场是「X-相机X+0x38 > 0x1F0」卷屏判定，B!=0 时 `X += VelX(±6)`）、`Cps1EnemyAI.cs:4812`（`解析Mount目标或玩家` 把 `MountObj` 当目标指针）。**不串等价、不评优劣、不把未登记写成缺失**；0 次 ROM 取证，§11.6 未触发。
- 六条设计结论：①乘员位图与三份座位每帧清零重建，`bc0` 是玩家侧副本；②没有驾驶员，N 个 rider 的方向按人数分档（0 默认 `0x800/0`、1 全量、2 减半、3 ×6/16）合成单一目标速度，`b119=0x3D` 新按下窗口选 `PAIRS_B` 或 `PAIRS`；③目标 ≠ 速度 ≠ 位置：`vz` 立即、`vx` 每帧 ±0x30 逼近、差值 -0x20..0x1F 才取到，位置再被相对镜头窗口（X cam+0x30..+0x140、Z cam+0x10..+0x50）拉回；④车身高度 `BUMPS` 表倒计时与 HP 门槛冒烟是不归输入管的第二条线；⑤轮子是独立对象，读车主体的 `vx/vz` 自算相位（`WHEEL_ANIM`）；⑥帧尾 `sub != 0` 是 hit flash，`sub == 0` 才有终局测试，且**终点由镜头 `cam_x >= 0xA000` 或全局 `car_mode == 2` 决定，不是车自己的位置**。

## 写盘工艺（沿用，勿再犯）

- 唯一交付文档是 git 跟踪的 `DESIGN_DIFF_NOTES.md`；`R:\Temp\*` 只是写盘脚手架，用**中性名 + 用完即删 + 落盘即入仓**，本轮用 `R:\Temp\s85_patch.txt` / `a49_patch.txt`（不再用 `.md` 后缀）。
- 大段中文 markdown 用 Write 工具落干净 UTF-8 片段 → .NET `ReadAllLines(...,UTF8)` 读回 → 按行号重建数组 → 逐项预校验 `new != old` 且 `cnt=1` → 一次 `WriteAllText` 写回主文件；`Join("`n")` 保持 LF 无 BOM。
- 导航同步用「按行号重建数组 + 整行末尾追加」，不要批量锚点 replace（§84 时两次 `same=True` / `cnt=0` 失败源于此）。§85 需同步 L16 规模行与 A.49 预写、L46 章节列表、L47 附录行、L50/L54/L63/L65 主题索引、L70 附录引用列表。
- `git diff` / `git log` 中文经 PowerShell 控制台是 GBK 乱码，文件本身 UTF-8；判断内容用 `Read` 或 .NET `ReadAllText(...,UTF8)`。
- 表格行统计用历史 `^\|` 口径；`file:line` 双口径沿用 `s[h]` / `p[y]` 字符类；不同正则口径 / 不同时点数字不相减。

## 每轮收尾

把本轮未闭合残差写回本文件（删旧建新，不是编辑）；跨轮结论进 `DESIGN_DIFF_NOTES.md`。目标仍开放，不宣称完成。
