# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**「必读层口径订正」版**：上一版是 `d042dad`（检索范围漏目录订正版），本轮开工读过消费完毕，并已按机制删除重建。

## 本轮做完的事

开工按流程复位必读层（`CLAUDE.md`、`DRAFT.md`、`git log -8` / 干净工作区），并抬头读了 `STATUS.md`、`dino-rs/ARCHITECTURE.md`、`re/README.md`、`run.md`、`re/harness/allow/final.txt`。答「我现在做的事和当前目标是什么关系」时判定：前十几轮走的是「提现象→查重→收口」的**知识层自检**，DRAFT 自己已反复判定不该再靠换一个小现象凑 diff；本轮换到**产品目标里可用工具当场验证的真实步骤**（M10-26 明列的 git 泄漏扫描面），撞出并订正了一个真实的、每轮开工必读的过期口径。

**订正内容（提交 `1228179`，2 files / +12 -5）**：`CLAUDE.md` 第 6–8 行与 `.gitignore` 抬头仍写「asset dump IS committed / Exception」，与仓库事实相反。真值是用户本人 2026-11-05 两个连贯提交：`4c5c8b4`（07:35，"del out"，删 7406 个文件）→ `55160d3`（10:20，把 `!re/out/assets/` 两条例外注释掉）。`CLAUDE.md` 自 `caafad3`（2026-10-12）后从未同步（后续改动只动 sub-agent 规则），属**纯遗漏**，不是待裁定问题。A51（`re/notes/session-01a1a8e4.md:1609`）曾把它当「意外状态、先报告」，已被用户后续连贯动作证伪；`re/notes/DECISIONS.md:140` 仍沿用旧口径，说明这句过期陈述已实际误导。

按「上游优先」在源头修：只订正描述、**不改行为** —— 两条例外保持注释，不擅自恢复提交，也不推翻 2026-10-12「允许提交」的裁定（写明恢复路径：取消注释 + 重跑 dump + 提交）。`AGENTS.md`/`CODEBUDDY.md` 是指向 `CLAUDE.md` 的符号链接（git 索引模式 120000，blob 内容就是 `CLAUDE.md`），改一处三份自动同步，`git status` 只报两个文件。

## 回源与校验

- 必读层：`CLAUDE.md` 全文、`STATUS.md`、`dino-rs/ARCHITECTURE.md`、`re/README.md`、`run.md`、`re/harness/allow/final.txt`（M10-26 已知差异清单，已存在且完整）。
- M10-26 泄漏扫描：`git ls-files` 共 1982 个文件，全扩展名（含 `.gif`/`.png`/`.bin`/`.npy`/`.elf`/`.zip`/`.json` 等）命中 **0**；`git ls-files re/out` = **0**；`git ls-files re/ghidra` 只有 3 个脚本/entries（合规）；`git check-ignore -v re/out/assets/index.html` 由 `.gitignore:6:re/out/*` 命中。**这项检查实质通过**。
- 时序：`git show --format=fuller --stat 4c5c8b4`（7406 files / 14660 deletions，未动 `.gitignore`/`CLAUDE.md`）、`git show 55160d3 -- .gitignore`（两条例外由 `!` 改 `#!`）、`git log -- CLAUDE.md`（末次 `413777d` 2026-10-21，asset dump 行自 `caafad3` 未动）、`git log --all -- re/out/assets`（只有 `caafad3` 与 `4c5c8b4`）。
- 格式：`BOM=False / CR=False / maxlen 144 与 112 / git diff --check` 全过。提交后干净工作区。
- ROM：本轮 **0 次读 ROM 字节**，只查 git 元数据与文档；`dino.zip`/`re/rom` 均不存在，也没有拿任何 wof ROM 来读 dino。
- 环境限制（已核死，下轮别重复试）：`cargo`/`rustc`/`rustup` 全 absent（PATH 无 rust 项、`$env:USERPROFILE\.cargo\bin` 等常见位都没有），`dino.zip`、`re/rom`、`dino-rs/target` 都不存在 ⇒ 本环境做不了 `cargo build/test`、`regress.sh`、运行时回归。这是限制，不是未闭合缺口，别为它凑动作。

## 本轮口径（下轮开工以必读层与工具当场输出为准复核，本文件不是律法源）

- **别把历史文档里的「committed」抬成新缺口去刷**：`plan/game/design/D5-final-plan.md:108 / 3721`、`re/specs/sound/SPEC.md:23`、`re/specs/sound/HANDOFF.md:5`、`STATUS.md:44`、`re/notes/DECISIONS.md:140` 仍沿用旧口径。它们是当时的设计/计划记录或另一个项目（wt1）的笔记，不是每轮必读的现行约束；`re/README.md:14`、`plan/game/design/asset-catalog.md:5`、`plan/game/NEW-PLAN.md:34` 本来就写「git-ignored」，与现状一致。本轮有意**不扩散改**，避免「顺着自造文档一路推到无关动作」。
- **别重演收尾套路**：不写「下一轮换一个现象」「等用户经验或新疑点」（前几版被 Stop hook 点名）；开放目标下继续合理工作 ≠ 每轮必须挤出笔记 diff。本轮有实质产物（必读层订正 + 一次真实的 M10-26 检查结论），不是「查了一圈没改」。
- **别重查已核层**：四块主题地图、自检清册全表、§94.11 全文、`0x11CC4` 三条链、§94.15 / §70.3 / `EnemyData.t` 清册行前几轮已核；本轮新核的是 `STATUS.md` / `run.md` / `final.txt` / git 泄漏扫描，下轮也不必重复。
- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。Stop hook 是客户端自动重发催办，不直读 goal 状态。
