# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。

## 本轮收尾（开工重建，收尾写回）

- 开工核对：HEAD `0653c1a8`，`git status --short` 只有 ` M re/specs/lookup.py`（上一轮被压缩打断、已写盘但未验证的补丁），临时提交信息文件不存在；`CODEBUDDY.md` / `CLAUDE.md` / `DRAFT.md` 都读过。上一轮自测 314/314。
- **本轮一格：解码输出的证据标签只留一套**。
  - 起因：`say()` / `fmt()` 早就是 `[O 观察]` / `[I 推断]` / `[U 未登记]`，但后来逐格补上的多帧时间线、link word、身体盒关盒、抓姿势、受击跳过、script default 分支等说明手写成 `[O]` / `[I]` / `[U]`。同一份解码里混两种写法，读者会把短标签当成第三种证据成色，分不清哪句是代码观察、哪句是推断。这不是排版问题，是「看到数据就能不误读地知道它在干嘛」这条主线的可读性问题。
  - **边界先分清**：只改「挂在某句意义后面的短标签」。用法说明、注释、`unknown` 里的「标 [U]」、`legacy` 里的「[O] 级回源」、断言名里「frame_type 0 是 [I] 不是 [O]」——这些讲的是标签体系本身，**不是给具体句子打标签**，全部保留；否则会把概念引用一起误伤。
  - 落盘：约 20 处输出字符串统一到标准标签（`frame` 的 param_a / param_b / body_box / attack_box、`infer` 的两支、`cmd_script` default 分支、`cmd_attack` 三拳对照、`cmd_moment` 两个关盒、`cmd_anim` 的 marks / link word 三类去向 / SPEC §3.1 / 末尾统计）；用法说明改成直接列出三种标准标签长什么样。
  - 自测：一条旧断言 `"跳到本段之外 [I]"` 同步成 `[I 推断]`（否则 313/314）；新增一条防回退自测，**真跑十条解码命令**（`frame` / `anim` / `moment` / `comp` / `box` / `spawn` / `script` / `attack` / `wof_attack` / `chain`），扫实际输出里不再夹裸 `\[[OIU]\]`，同时统计标准标签至少 5 处，确认不是把标签删光了。扫描对象是命令输出，不是源码全文——这样概念引用天然不在范围内。314 → **315**。
  - **未新增域、未改语义**：只动输出字符串、docstring、自测；`semantics.json` 本轮未改，`coverage.registered` / `themes` / `legacy` / `not_registered` 都没动。
- 验证：`--selftest` 315/315 全过 exit 0；`py_compile` exit 0、`json.load` 通过、`git diff --check` exit 0；`lookup.py` `CR=0 BOM=False`、`over2000=[]`；四条 CLI（`anim` 拍子样本 / `frame` / `moment` kind=6 / `chain`）真跑 rc=0、`stderr` 全空。`anim` 输出里 `[O 观察]` / `[I 推断]` 逐行可见，不再有裸短标签；仍报「攻击生效帧 1 个 / 特殊必杀帧 1 个 [I 推断] / 其中 1 帧身体盒关着 / link word @+0032 i16 +17 / 跳到本段之外 [I 推断]」。
- 本轮 0 次 ROM 取证、没碰产物层、没改 `check_docs.py`、没动设计文档正文（`DESIGN_DIFF_NOTES.md` / `GAMEPLAY_LEGACY.md` / `notes/*`）、没回改早期卷、没回查载具 / 特殊关卡换面；`GAMEPLAY_LEGACY.md` 第 481 行停止条件仍有效。wt1 只读、未改。

## 长期口径（每轮沿用，不是本轮新增任务）

- `长时间自主推进` 是开放目标：局部提交、干净工作区、阶段总结、压缩 / 总结请求都不算完成或缩小；不询问是否继续，不直读 goal 状态，不写「下一格 / 短期不再动笔」当收尾，提到方向就当轮把第一步做掉。
- 用户要的是「游戏设计本意」，交付一律说人话；不把内部编号、提交号、校验数字当主体；忽略 Rust / C#、typed struct / WRAM、端序、逐帧补偿等实现表相。
- 用户的真实任务是把各类变量取值转成可查的「抽象意义」并缓存，ANI / SPR 只是举例；要能顺着 ANI → SPR → 判定框 → 后果 → 受击反应 → 挨打的人怎么演 → 这一招打完往哪走，在看不到 GFX 时推断这一帧在干嘛；**细节之后要倒推回设计架构和意图**（`legacy` 索引就是这条回路）。**缓存与脚本的落点：`re/specs/semantics.json`（机器可读语义）/`re/specs/lookup.py`（离线查询，不带参数打印全部用法）**；入口有三处：`CLAUDE.md` 指向的 `re/README.md` / `re/specs/CONTEXT.md` 路径清册、`DESIGN_DIFF_NOTES.md`「阅读顺序」第 7 条、以及 `lookup.py` 不带参数的用法说明。`unknown` 一次列出哪些还没弄明白（两类未登记分开说，未登记 ≠ 不存在，每条带 blocked_at）；`themes` 按玩法问题查数时带观察 / 推断 / 未登记的成色并指向 `unknown`。**解码输出统一带 `[O 观察]` / `[I 推断]` / `[U 未登记]`，只有这一套**；用法说明、注释、`unknown`「标 [U]」、`legacy`「[O] 级回源」是概念引用，不算短标签、不要去「统一」；字段 / 位偏移说明讲的是格子名，不挂标签。后果环把反应门票并排翻到 dino 两本受击册子、**各自的下游紧跟自己那本册子**（玩家 set2 段号 / 敌人姿态槽），不串 wof、也不串两侧。新增域必须带 source / scope / tag，不从字段名猜；`coverage.registered` 与 `themes` 必须覆盖所有域且每域只归一处；`not_registered` 写清「为什么不转」；`legacy` 每条带 `can_check` / `cannot_check` / `probe`（probe 可单条或多条）；上下文相关域必须带 `note`，且要讲清「查之前先确认哪一侧 / 哪个对象 / 哪一层档位」——状态机四层（mode / 地面 / 跑动 / 空中）都在内。**多个键写同一句意义不算错**（武器段被特例切两段、多变体同规则、多段同标签），但要在 note 里讲清为什么，别让人当成抄重去「修正」。**新增或改动解码命令后，`SMOKE_CASES` 要跟着加**（现在 40 条）；每条命令必须 `return 0`，别让 `main() -> int` 拿到 `None`。
- **`[U]` 不是漏查清单**：每条 `[U]` 必须带 `blocked_at`，写清回源走到哪一行 / 哪一段、为什么停（SPEC 自己标 [U]、上游 Open gaps 明列、只给 handler 没给逐项意义、编号合并成一类）。`blocked_at` 里的路径从仓库根写全、行号不越界，自测会扫。有充分证据的 `[U]` 要真升级成 `[O]` / `[I]` 并补条目级 `source`——升级时别忘 `unknown` 的条数与「该域是否还在 unknown 里」会跟着变；没证据的别硬答，也别反复回源翻同一批。当前 17 条 `[U]` 已逐条回源核过，别再从头翻。
- **八类帧身份只有一份分组**：`re/specs/anim/SPEC.md §4.4` 的 `0/2/4/6/8/0xA/0xC/0xE` 在 `lookup.py` 里收成五组常量，`frame` / `anim` / `moment` 共用——`GRAB_KINDS(0,2)` / `ATTACK_KINDS(4,)` / `SPECIAL_KINDS(6,) [I]` / `SKIP_DEFEND_KINDS(8,10)` / `GRAB_POSE_KINDS(12,14)`。自测扫源码拦硬编码，别再在下游各写一份判据。攻方生效只认 4；6 是 [I] 推断、单列不算生效；被跳过的防守方只有 8/0xA；0xC/0xE 仍在防守方命中分派表里、自己可能挨打。`frame_type.note` 也写了五组。
- **身体盒取 0 ≠ 攻击盒取 0**：`box_index_zero` 登记的是攻击盒（+$49）取 0 =「这一帧不打人」（dino）/「合法表项」（wof）；`body_box_zero` 登记的是防守方身体盒（+$48）取 0 =「这一帧自己不可被命中」，依据 `re/specs/anim/SPEC.md §4.4` 的 [O] 前置条件 `defender +$48 != 0`，只有 dino 侧证据。查数前先分清哪个字段、哪一侧；能不能打人和会不会挨打是两件事，也别从帧类型推「哪帧无敌」（逐帧看这个字节）。`body_box_zero` 已进 `coverage.registered` 与 `themes.hit_logic`。
- **Jack 示例盒的 meaning 讲的是盒表项，不是当前帧**：`cmd_frame` 末尾打印盒表项意义前已先声明这一点；别把那句「出拳同时自己整个可被打，攻防同帧」读成当前这一帧的身份判断。
- **link word 是量，不是编号域**：`re/specs/anim/SPEC.md:185-187` [O] 写明末帧后紧跟 `i16 link`，下一帧 = `addr_of_link + link`，可回环或跳到另一段；tick 例程跟随 link 时 `carry=1` 表示「这一段演完了」。`anim` 已能解出有符号值、目标相对段首偏移、以及回环 / 跳段 / 段内非帧起点三类去向（后两类是 [I] 推断，因为离线没有 ANI 表绝对基址）。**别把它转成「取值 → 意义」的域**：连续相对偏移按纪律不转，`frame_timer.bit7=1` 已登记其存在与用途。
- **`legacy` 索引的挂法**：新查明白的取值要挂回它支撑的判断，但先核正文——正文已立住的判断只补可查落点，不改正文、不加节号。**`legacy` 不要求覆盖所有域**：覆盖全部域是 `themes` 的职责，这里按「能否回答这条判断」挂域，别为凑覆盖率硬挂；字段偏移域可以作为「把一拍拆开读」的解码入口挂（swing 已挂 attack_field / box_field / wof_atk_field），但别把不回答问题的域塞进去（continuity 要的是 camera_lock，不是 camera_event）。`legacy.beat` 三条 probe（帧记录 link word / wof `+0x62` 解锁 / 挨打那一侧躺地），`legacy.difficulty` 两条（波次 / 贴脸按档停顿）；`can_check` 只写缓存里真有取值或真有命令能翻出来的东西。
- **按游戏侧的分布是证据边界**：70 域里 dino 63 / wof 6 / 两侧共用 1，`coverage` 命令当场打印并写明「不是哪边设计更简单」。别据此评优劣，也别从 `wof_cs` 移植侧推断 wof 原机缺机制；理由见 `notes/08` 与 `not_registered`。「wof 半边薄」不是补域的理由。
- **动画编号有三层，别混**：`player_hurt_anim` 是 [O]「玩家受击代码播 set2 第几段」、四个角色通用；`enemy_hurt_anim` 是 [O]「敌人受击代码分派到哪个姿态槽」、跨兵种一致的槽位语义；`jack_anim_set2` 是 [I]「Jack 那一段长什么样」。敌人每槽具体图集要按 `e.w84` 查 `L[0x2E68C + e.w84]`，逐兵种内容按 `not_registered` 第 14 条不转；§3.6 只列到 #7，#8 / #9 只在 §5 受击代码里出现，#5 无调用点。两侧反应编号集合本就不同，别互套、别跨对象推全表。**两张 anim 域的 `reactions` 都只列直接分派**，运行时改判不挂进去，免得读成同一拍同时播两段。**note 里引用 `coverage.not_registered` 之前先确认真有对应条目**。
- 回源路径一律从仓库根写全（如 `dino-rs/crates/dino-assets/...`），不留裸前缀、也不留纯文件名；`§N` 要指向真能翻到的标题（早期卷若只分 `N.1`–`N.k` 子节，就写子节范围）。`legacy.list[*].title` 与 `GAMEPLAY_LEGACY.md` 九节标题逐字对应、顺序一致。自测会查文件真实存在、行号范围与 `§号` 标题，白名单只放命令示例 `lookup.py` 与通配符 `/HANDOFF.md`。
- **停止条件**：`GAMEPLAY_LEGACY.md` 第 481 行「不改总入口、不加新节号、不回文档自洽循环」；415–481 补层已闭合、`legacy` 九条索引只对应前九节，不补后半部底座。伪代码 / 流程图各卷已很多；总入口 153–157 行三个实际问题落点、`themes` 已是按玩法问题那条索引 —— 都核过，别再翻。`not_registered` 现在 14 条理由，逐条都有回源，别再从头翻。`notes/08` 是移植侧欠账清单、非原机缺机制。
- 「缓存没转成域」与「没有证据」是两种缺口；不把 [I] 写成 [O]，也不把 [O] 代码观察降成叙事；不从概括硬编假编号域；[O] 回源但形态是量 / 条件分支 / 随机漂移 / 未给逐项意义的查表，写进 `not_registered` + `source`。
- 「讲两侧」按外推文正文与它自己写下的边界判定，不按 `can_check` 措辞。要求两侧各挂样本的是 `beat / swing / death / feel / values`；`combo / crowd / continuity` 不算，`difficulty` 正文没提 wof。
- ROM 主要服务于 data 调查，只在 `wof_cs` 写得非常可疑时才触发核实；不恢复「以 ROM 审 repo」框架。
- 特殊关卡、专属演出、单个 Boss 那一段的编排不构成通则；载具换面停止。
- 环境限制（不是缺口）：无 Rust 工具链、无 `dino.zip`、无 `re/rom` / `target`，做不了 `cargo build/test`、`regress.sh`、MAME 对拍；`lookup.py` 是 ROM-free 的离线脚本。
- 写盘 LF 无 BOM；收尾校验 `CR=0 BOM=False`、新增行 `over2000=0`、`git diff --check`、`git status --short`；提交信息用 `git commit -F R:\Temp\dino_commit_msg.txt` 后清理临时文件。
- 用补丁脚本改 `lookup.py` 时，短锚点可能是更长行的子串（4 空格 vs 8 空格缩进），断言 `count==1` 会挡住；用带前后换行符的完整行锚点。生成脚本里的正则要用单引号 here-string 原样传，避免外层字符串把 `\s` 当转义。PowerShell 里没有 `py` 别名，用 `python`；ripgrep 不支持前瞻 `(?!...)`，扫裸短标签用 Python `re` 或在输出层做。
