# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：把「关卡什么时候放行」的数据底座补进缓存（第十二格）

**背景**：`9fbb9ece` 收口漏扫的 HANDOFF 目录后，工作区干净、
`R:\Temp\dino_commit_msg.txt` 已清理。Stop hook 催办后继续。
上一格收的是「哪些目录不用再翻」，这一格正面核六份 SPEC 本身，
看 58 个域是不是把成表都转完了。

### 正面回源，先划边界

- `anim/SPEC.md §4.5` 攻击属性 8 字节字段布局 → 已在 `attack_field`。
- `sound/SPEC.md §12/§14` 音高 / 音量 / 包络 / 乘法表 / 样本与乐器表 →
  全是量与表内容，按 `coverage.not_registered` 既有两条不转；
  §14 的 twin voices 属声音实现层，也不进玩法判断。
- `stage/SPEC.md §6.6` 模式表已在 `camera_mode`；`§5.2` 事件记录是
  字段布局。真缺口是 **`§5.1` 的 `$7b4` 相机锁三档**——笔记里反复讲
  「门闩锁相机、阈值达标放行」，却没有可查的取值意义。

### 落点

- `semantics.json` 新增 `camera_lock`（0 自由 / 1 这一波打完前锁 /
  2 锁到关卡结束），note 写清「锁着不等于暂停世界：mode 4 每帧仍把
  camX 钉在事件给的 X 上，等 $6D go flag 才放行」，并标明这是共享
  事实、不是替所有人定拍子的裁决。
- 新增 `camera_event`（16 字节事件记录的字段键 `+0..+F`），note 写明
  `X = 0xFFFF` 是表终止符、加载时记下 camY 并让事件序号 +1。
- `coverage.registered` 的 stage 组、`themes.event_script` 同步登记；
  `OFFSET_KEY_DOMAINS` 加 `camera_event`，不参与 `collide` 反查。
- 自测 83 → **88/88**（相机锁、事件字段、终止符、`collide 1` 两义、
  字段偏移域排除）。
- `DESIGN_DIFF_NOTES.md`「拿这份缓存真跑一次」那段补一个真例证：
  同样是 `1`，在镜头模式表里是「区域结束、淡出换调色板」，在锁状态
  表里是「这一波还没打完、先别往前走」——一个说翻页、一个说放行，
  接回「一个数字没有全局意思」。

### 实跑验证

- `--selftest` 88/88；`py_compile` OK。
- JSON 侧核对：60 域 / 459 条，`coverage` 缺 0 个域，
  `themes` 列出 60 个、去重后 60 个。
- `collide 1` 实跑同时列出 `camera_mode` 与 `camera_lock` 两种不同
  意义；`camera_event.+B` 可查；被排除的 7 个字段偏移域在尾部列明。
- 四份改动文件 `CR=0 BOM=False`；`DESIGN_DIFF_NOTES.md` 超 2000 字节的
  仍是既存第 57 / 89 / 154 行，本轮新增行 0 超长；
  `git diff --check` exit=0。
- PowerShell `Select-Object -Last` 造成的中文乱码是已知管道显示问题，
  完整输出与 Python 断言已核对，不是数据错。

### 边界

- **0 次 ROM**；只读 rep 内 SPEC / 缓存与离线脚本，未碰 `g:/wof/wt1` 源码。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 假红，
  不改 `CLAUDE.md` / `.gitignore`。
- 不恢复「以 ROM 审 repo」框架；不把 `[I]` 写成 `[O]`；不从字段名猜意义；
  量 / 表内容 / 硬件实现层按纪律不转。
- 载具 / 特殊关卡 / 单个 Boss 专属演出不构成通则，不往那里钻。

### 长期口径（细则在耐久层，不在本文件展开）

- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。
  Stop hook 是客户端自动重发催办，**不直读 goal 状态**；按「继续合理授权工作」直接做。
- 不写「下一格 / 短期不再动笔」当收尾；提到方向就当轮把第一步做掉。
- 交付一律**说人话**：人类理解中的游戏设计，不报内部编号、校验数字当主体。
- 产物层无分析意义；ROM 主要服务于 data 调查，仅在 `wof_cs` 非常可疑时才核实。
- 写盘 LF 无 BOM；提交信息走 `git commit -F` 临时文件随后清理。
- 新增语义域必须带 source / scope / tag；`coverage.registered` 与
  `themes.list[*].domains` 都必须覆盖所有域且每域只归一处；
  离散编号不连成范围；位域 / 字段偏移域继续被 `collide` 排除。

## 收尾

- 校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、
  `git status --short`；`git commit -F` 后 `Remove-Item` 临时信息，再复核干净工作区。
