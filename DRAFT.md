# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮做了什么：把 SPR composition 也翻成可查意义（第九格）

**背景**：开工核现场，`25ce65f8`（主题索引）已提交、工作区干净、
`R:\Temp\dino_commit_msg.txt` 已清理；上一份摘要担心的「截断丢提交」核清为
工具回显问题，不是真丢。复跑 `--selftest` 76/76、`themes` 六类、
`py_compile` OK、`coverage` 57 域 / 441 条 / 缺 0 多 0。

### 为什么补这一环

- 用户原话是「看到某个 ANI SPR 数据就能简单知道是什么抽象意义」、
  「ANI->SPR->判定框，虽然你看不见 GFX，但能猜出是在干嘛吧」。
- 既有工具：ANI 侧 `frame` / `anim`、判定框侧 `box`、SPR attr 位拆解
  `attr` / `flags`，中间 **composition 记录本身** 只有 `chain` 里一张文字图，
  没有「喂一串字节就翻成形状」的命令。补上它，三环才都能离线查。
- 扫 `re/specs/**/*.md` 时先划清边界：`flow/ENDING.md`（结局专属演出）、
  `enemy/B50-B76.md`（Boss 登场对白服务）按用户「特殊关卡 / 专属演出 /
  单个 Boss 编排不构成通则」**不转、不展开**；`CONTEXT.md` 的 `pool_tag`
  早已收进 `coverage` 第 8 组，硬件 / 宿主层其余按纪律不转。

### 落点

- `re/specs/semantics.json` 新增 `comp_extra` 域（回源 anim/SPEC.md §2.6）：
  `+$4C` / `+$4D` 涉水时从末尾藏掉几个 entry（脚 / 腿）、`+$4E` bit7
  不画影子 / 高半字节选影子与水花图集 / `0x70` 影子下移、`+$4F` 用途未明
  标 [U]；note 写明 entry 按头 → 脚排、字段键不是取值。
  `coverage.registered` 的 anim 组、`themes.data_format` 同步登记。
- `re/specs/lookup.py` 新增 `cmd_comp`：读 8 字节头（count / n / hattr /
  layout），按 normal（2 字节/entry、共用 attr）或 alt（4 字节/entry、
  逐块 attr）拆 code 与 attr，后面若接 `n×4` 字节就当 layout 的 (dx,dy)
  一起解；输出调色板 / X·Y 翻转 / 块尺寸 / 摆位，并说清「第一块优先级
  最高」「头→脚」「换一组摆位就是另一帧」「朝右整体镜像」。
  加了 `s16` 与 `describe_attr`（位含义复用 `sprite_attr` 域登记）。
  `comp_extra` 加进 `OFFSET_KEY_DOMAINS`，不参与 `collide` 按取值反查。
  doc 用法、main dispatch、自测同步；自测 76 → **82/82**。
- `DESIGN_DIFF_NOTES.md` 数值索引节补「三环现在都能离线查了」指引；
  并在「册子之间怎么交接」之后补一段设计倒推：一帧人不是一整张图，
  是零件编号 + 共用摆位表，薄的不只是玩法规则、连「一帧摆成什么样」
  也薄，厚的是零件与摆位两本册子；接回外推文编舞那一段，标 **dino 侧**
  登记、不写成两款共同架构、不推断作者意图。

### 实跑验证

- `--selftest` → **82/82 通过**（新增 6 条：normal / alt 解码、count 与
  GFX 边界、块精灵尺寸、`comp_extra` 入缓存、字段偏移域不参与反查）。
- `comp` 两条实例：normal（共用调色板 5、两块 1×1、dx=-8/8）与
  alt（逐 entry attr、调色板 13/14、X·Y 翻转、块 2×2）都能翻成人话；
  顺手修掉 `describe_attr` 把「调色板 13X 翻转」黏在一起的显示。
- `coverage` → **58 个域 / 445 条；索引缺 0 个域、多 0 个域**；
  `themes` 一致性断言照旧通过；`py_compile` OK。
- 四份改动文件 `CR=0 BOM=False`；`DESIGN_DIFF_NOTES.md` 超 2000 字节的
  仍是既存第 57 / 89 / 154 行，本轮新增行 0 超长；`git diff --check` exit=0。

### 边界

- **0 次 ROM**；只读 rep 内 SPEC / 缓存与离线脚本，未碰 `g:/wof/wt1` 源码。
- 不碰 `re/out/assets/` 产物层，不修 `check_docs.py` 假红，
  不改 `CLAUDE.md` / `.gitignore`。
- 不恢复「以 ROM 审 repo」框架；不把 `[I]` 写成 `[O]`；不从字段名 / 常量名猜意义；
  `code` 只是图块编号，看不到 GFX 不猜造型。
- 环境硬限制照旧（无 Rust 工具链 / `dino.zip` / `re/rom` / `target`），新脚本 ROM-free。

### 长期口径（细则在耐久层，不在本文件展开）

- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。
  Stop hook 是客户端自动重发催办，**不直读 goal 状态**；按「继续合理授权工作」直接做。
- 不写「下一格 / 短期不再动笔」当收尾；提到方向就当轮把第一步做掉。
- 交付一律**说人话**：人类理解中的游戏设计，不报内部编号、校验数字当主体。
- `dino载具是特殊关卡,没什么好看的` ⇒ 载具 / 特殊关卡 / 单个 Boss 那一段编排不构成通则。
- 产物层无分析意义；ROM 主要服务于 data 调查，仅在 `wof_cs` 非常可疑时才核实。
- 写盘 LF 无 BOM；提交信息走 `git commit -F` 临时文件随后清理。
- 新增语义域必须带 source / scope / tag；`coverage.registered` 与
  `themes.list[*].domains` 都必须覆盖所有域且每域只归一处；
  离散编号不连成范围；位域 / 字段偏移域继续被 `collide` 排除。

## 收尾

- 校验四份文件 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、
  `git status --short`；`git commit -F` 后 `Remove-Item` 临时信息，再复核干净工作区。
