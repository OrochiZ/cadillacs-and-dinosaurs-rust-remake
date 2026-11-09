# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：接着把「各种表」的数值抽象意义转进缓存

**用户本轮强调**：`我觉得所以才要转换缓存各种表数值的抽象意义啊` —— 承接上一轮倒推出的
「一个数字没有全局意思，只有谁在读它才有」，意思是**正因如此才更要把每一张表的数值
意义都转出来、缓存住**，否则「先确定谁在读」落不了地。这是推动继续扩表，不是要新哲学结论，
所以本轮不往设计笔记再堆段落，只补数据层。

开工核现场：`git status --short` 空、HEAD `c9d28ca1`、无临时提交信息。
回源读了 `re/specs/flow/SPEC.md` §4、`re/specs/enemy/SPEC.md` §3.2 / §7.1 / §7.4 / §13.2，
以及本会话前面已读的 `re/specs/player/SPEC.md` §3.2 状态表。

### 新增 6 个域、77 条（33 → 39 域，208 → 285 条）

- `game_mode`：顶层游戏模式 G.$4D0（投币加入 / 选人 / 过场 / 真正的游戏帧 / 续关 /
  game over 两入口 / 结局）。来源 `re/specs/flow/SPEC.md` §4、`ENDING.md`。
- `player_run_state` / `player_air_state`：补齐玩家状态字的另外两本手册。与已有
  `player_ground_state` 合成一套——**同一个状态字 $06 在地面 / 跑动 / 空中三张表里
  各讲一套**，空中表里还写进角色差异（同一个编号在 Hannah / Mustapha / Mess / Jack
  身上是不同的跳跃攻击）。三个域都标 `context_dependent` 并在 note 里互指。
  来源 `re/specs/player/SPEC.md` §3.2。
- `enemy_ai_state`：杂兵 class 2 的真实 AI 状态（拿主意 / 接近绕圈 / 亮相挑衅 /
  保持距离 / 攻击 / 冲刺 / 下坠 / 等待再攻击 / 跳下台阶）。来源 §7.4 各 State 小节。
- `pool_a_class`：池 A 类别编号 → 是哪一族敌人 / Boss，只登记 SPEC 点名的 ~28 个；
  未列出的编号多是布景 / 弹丸 / 辅助，classmap.txt 里名字为空，不猜。来源 §3.2。
- `container_variant`：容器变体 → 「可打 / 实心挡路 / 能举」的规则组合。变体不是换贴图，
  是换一组规则。来源 §13.2。

**本轮最关键的一条防误读登记**：`enemy_ai_state` 的 note 明写「别拿 §7.1 的 debug
词汇表当编号表」——SPEC 原文是「class 2 的 +$06 不按那张表走，那只是开发者的通用词汇，
每个 class 各用自己的子集和编号」。转缓存转得越多，越得连「哪张表不能当编号表用」一起记，
否则批量转换反而会批量制造错读。selftest 已固化这条断言。

### 验证

`--selftest` 从 25 条加到 **33 条，33/33 通过**；新增断言覆盖三张玩家状态表都在缓存、
`collide 4` 能同时列出三张、`game_mode 0x0C` / `pool_a_class 18` /
`container_variant 0xA` 的映射、以及上面那条 debug 警告。
`py_compile` exit=0；两个文件 `CR=0 BOM=False over2000=0`；JSON 合法。
抽查 `game_mode 0x0C` / `pool_a_class 18` / `container_variant 0xA` / `enemy_ai_state 0`
输出与源一致。0 次 ROM 取证。

### 长期口径（仍在生效）

- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。
  Stop hook 是客户端自动重发催办，**不直读 goal 状态**；按「继续合理授权工作」直接做，不询问是否继续。
- 不写「下一格 / 短期不再动笔」当收尾；提到方向就当轮把第一步做掉；不拿「你主动暂停」当收尾话头。
- 交付一律**说人话**：人类理解中的游戏设计，不报内部编号、证伪流水账、校验数字当主体。
- 产物层（`re/out/assets/`）无分析意义：不读日志、不铺分析、不修 `check_docs.py` 假红、
  不改 `CLAUDE.md` / `.gitignore` 产物状态描述。收尾用 `git status` / `git diff --check` / `CR/BOM`。
- 用户裁定：`dino载具是特殊关卡,没什么好看的` —— 载具换面已停；特殊关卡 / 专属演出 /
  单个 Boss 那一段编排不构成通则；不再回查 `notes/02-mid.md` §32 / `notes/06-method.md` §85。
- ROM 边界：ROM 主要为调查 data；仅在 `wof_cs` 写得非常可疑时才核实。本轮 0 次 ROM 取证。
  不恢复「以 ROM 审 repo」框架，不把 `[I]` 写成 `[O]`，不评优劣、不推断 wof 原机缺机制。
- 缓存纪律：每条带 `scope` / `source` / `tag`，不从字段名猜，不把 `[U]` 写成 `[O]`，
  上下文相关域要带对象 / 链；离散取值不连成范围；位域与字段偏移域不参与按取值反查。
- 环境硬限制：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`、`re/out/dino_68k.bin` /
  `gfx.npy` 本机查不到 ⇒ 编译、回归、MAME 对拍、ROM-dependent 脚本跑不了，不是缺口。
- 写盘 LF 无 BOM；提交信息用 `git commit -F` 临时文件随后清理。

## 开工与收尾

- 开工：核现场 → 回源读四份 SPEC 的成表段 → 追加 6 域 → 抽查 → 补 selftest → 全量自测。
- 本会话已提交：`60d32087`（缓存 + 脚本）、`39561bc0`（anim / box）、
  `c9d28ca1`（collide + 设计倒推），每次临时信息都已清理、工作区复核干净。
- 本轮收尾：校验 `DRAFT.md` / `re/specs/semantics.json` / `re/specs/lookup.py` 的
  `CR=0 BOM=False`（新增行 0 超 2000）、`git diff --check`、`--selftest` 33/33；
  提交信息走 `git commit -F`，随后 `Remove-Item`，再复核干净工作区。
