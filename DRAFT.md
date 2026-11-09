# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：补核 enemy SPEC，订正相机两域回源并闭合检索范围（第十三格）

**背景**：`66155da6` 补 `camera_lock` / `camera_event` 后，工作区干净。
上一格说「正面核六份 SPEC」，但 `enemy/SPEC.md` 的章节标题被输出上限
截断、只看到 §0，留了个尾巴；这一格补齐核完并订正回源口径。

### 补核 enemy SPEC 的结论

- `§6.4 Rank events` 全是量的增减（rank ±3 / speed ±1、查表值），
  `§8.5 Other flags` 是计数与载具专属标志（`$518`，按用户边界不转），
  `§3.1` 名字表、`§9` 逐关脚本都不是「取值 → 抽象意义」成表。
- `§8.2 / §8.3 / §8.5` 已有的口径对得上缓存：`wave_end`（0 GO /
  2 自动走下一区域 / 4 关卡结束）、`kill_all`（1 记分 / 2 超时不记分）
  都完整，**没有新缺口**。
- `§8.3` 给了比 stage SPEC 更直接的一句：**镜头恰好停在波次开始处，
  一直锁到波次收尾字把 `$7A9` GO 置起来**；segment table 0x21B2A
  的 16 字节记录字段名与 stage `§5.2` 对齐。

### 落点

- `camera_mode` 的 source 把含糊的「§8.3 wave lock」订正为
  `re/specs/enemy/SPEC.md §8.3`（stage 的 §8 是 tilemap streaming，
  没有 §8.3，原写法会指错文件）。
- `camera_lock` 的 source 补 `enemy/SPEC.md §8.3`，note 补
  「镜头恰好停在波次开始处」。
- `camera_event` 的 source 补 `enemy/SPEC.md §8.3（segment table 0x21B2A）`。
- `coverage.note` 补一句：六份 `re/specs/*/SPEC.md` 的成表已正面核过
  一轮，`not_registered` 写的是按纪律不转的理由、不是漏查，别再从头翻。
  与上一格 HANDOFF 收口合起来，`re/specs` 的检索范围彻底闭合。
- 自测 88 → **90/90**：新增「镜头锁与波次收尾能串成一条放行链」
  （`camera_lock` 回源 §8.3 + `wave_end 0` 的 GO / `$7A9`）与
  「六份 SPEC 已正面核过的口径写进覆盖索引」两条。

### 实跑验证

- `--selftest` 90/90；`py_compile` OK；60 域 / 459 条、
  `coverage` 缺 0 个域、`themes` 列出 60 个且去重 60 个。
- 四份文件 `CR=0 BOM=False`；`DESIGN_DIFF_NOTES.md` 超 2000 字节的
  仍是既存第 57 / 89 / 154 行，本轮新增行 0 超长；
  `git diff --check` exit=0。

### 边界

- **0 次 ROM**；只读 rep 内 SPEC / 缓存与离线脚本，未碰 `g:/wof/wt1` 源码。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 假红，
  不改 `CLAUDE.md` / `.gitignore`。
- 不恢复「以 ROM 审 repo」框架；不把 `[I]` 写成 `[O]`；不从字段名猜意义；
  量 / 表内容 / 硬件实现层 / 载具专属标志按纪律不转。
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
