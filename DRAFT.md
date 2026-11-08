# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**「closeout 收口 + 上游工具化」版**：上一版是 `f386345`（必读层口径订正版），本轮开工读过消费完毕，并已按机制删除重建。

## 本轮做完的事

开工按流程复位必读层与本版 DRAFT 后，判定的关系是：前十几轮的「提现象→查重→收口」知识层自检不该靠换小现象续命，本轮继续落在**产品目标里可用工具当场验证的真实步骤**（M10-25 / M10-26 closeout），并把反复撞到的同一类漂移在**上游**固化成工具，而不是每轮重新 Grep。

**五个提交（工作区干净）**：

1. `ffed738` — `plan/PLAN.md` 里程碑表自 `e035775`（2026-10-13）后从未更新，仍写 M1 "Next"、M2–M10 "Pending"、Total「456 listed, about 600 expected」；按 `STATUS.md` 逐行同步到 M0–M9 Done / M10 23 of 26，并加「两者不一致以 STATUS.md 为准」。依据：`D5-final-plan.md:3712-3724`（"Edits the main session makes to other files" 明列 PLAN.md 表/status 列）、`NEW-PLAN.md:325`、M10-25 scope「update STATUS.md and plan/PLAN.md to "done"」。同提交删掉 `dino-rs/README.md` 的「Fessenden with three heroes」差异：该节与 `final.txt` 由 `1267e1b`（Task 17）同一次提交建立，随后 `d1ba4a4`（Task 75）明确「the debris ... gone」把 N1 标 GONE 却漏同步 README。
2. `96df4c5` — `STATUS.md` 开头行仍写「Work resumed 2026-10-21 after the M4 checkpoint (M1 to M4 and M6 done)」并挂 sweep 基线「379 of 418」，与同文件表格自相矛盾。改为对齐现行状态；**特意不把 379 改成 406**：`final.txt:9-11` 明说 results.jsonl / results_new.jsonl 不在盘上、re/out/sweep 已没，本环境无法复核 379 与 406 是否同一批刷新，硬改等于把无法验证的数字写成结论；改为删旧基线并指向 M10-26 权威清单。
3. `0b574b7` — 新增 `re/harness/check_docs.py`（零依赖、不读 ROM、不碰游戏代码），把 4 类反复出现的漂移固化成 6 项静态检查：里程碑状态、`--jump` 名（双向）、settings key（双向）、文档 CLI flag、git 泄漏、README 不得列 final.txt 标 GONE 的差异。自带 `--self-test`（同一套 `check()` 判据喂人为漂移样本）。`re/harness/README.md` 追加独立一节，写明只需 python + git。
4. `ca5f1a5` — 堵住假绿：`parse_milestones` 按固定列号取状态，若两表同时多一列会落到同一个 Hours 值而假通过。加状态词白名单；自检增第 7 个「列移位」样本。实测 shifted STATUS M1 = 24 / PLAN M1 = 24 / equal=True，naive 判据确实会假绿。
5. `1d1b8b2` — 补参数校验与 `--help`：原先敲 `--help` 静默跑检查、`--slft-test` 之类拼错会显示「6/6 passed」让人误以为自检跑过。未知参数 exit 2，`-h/--help` 打印用法 exit 0。

## 回源与校验

- 工具验证：正例 `6/6 passed`、`--self-test` clean baseline + `7/7` 漂移捕获、`py_compile` OK、从 `R:\Temp` 与 `C:\` 异地运行正常、`--help` exit 0、`--slft-test` exit 2 且无 passed、`git diff --check` OK、`BOM=False / CR=0 / over2000=0`。
- **真实旧版负例**（临时脚本在 `R:\Temp`，跑完即删）：`ffed738^` 的 PLAN.md 抓到 10 个里程碑漂移（M1 Done vs Next、M2 Done vs Pending …）、`ffed738^` 的 README 命中 GONE marker、`96df4c5^` 的 STATUS.md 过期开头在场而当前已消失。工具不是摆设。
- 按 §94.11 第四种漏法做查重时走的是**仓库根全 `*.md`**，不是只查 `notes/`；两处过期断言各只在现行文档出现一份，其它 `N1`/`379` 命中是资产目录编号或无关现象，逐条核过「是不是同一件事」。
- 环境限制（已核死，别重复试）：注册表卸载项、常见安装位、`G:\Users` 全无 Rust（cargo/rustc/rustup 全 absent，PATH 无 rust 项）；`G:\wof` 深度 4、各用户目录都无 `dino.zip`；`re/rom`、`re/mame/roms`、`.worktrees`、`dino-rs/target` 都不存在；`re/out` 全树只剩 1 个文件。⇒ 本环境做不了 `cargo build/test`、`regress.sh` 与运行时回归。这是限制，不是未闭合缺口，别为它凑动作。

## 查证通过、判定「不用改」的层（下轮别重复查）

- **M10-26 git 泄漏扫描实质通过**：`git ls-files` 1982 个文件，全扩展名（含 .gif/.png/.bin/.npy/.elf/.zip）命中 0；`git ls-files re/out` = 0；`git check-ignore -v re/out/assets/index.html` 由 `re/out/*` 命中；`re/ghidra` 只跟踪 3 个脚本/entries。
- **M10-25 debug-gating 断言成立**：`main.rs:203` 的 `debug::Debug::new` 只在 `--debug-keys`/`--test` 时为真，`autoplay`/`test`/`trace` 默认全关，与 `run.md:196/211` 一致。
- 源码里 30+ 处 `not ported` 是防御性兜底与有意不移植的 debug/anti-tamper 分支，与「no placeholder class is left」不矛盾（`run.md:211` 明写兜底消息只在真有未移植 class 时才出现）。个别注释仍留 M3 时期的将来时措辞，纯注释、无工具链可编译验证，属边际，不扩散。
- CLI flag 集合：文档 42 个 vs `main.rs` 字符串 38 个，差集仅 `--release`/`--nocapture`/`--ignored`（cargo/libtest 自己的）与 `--rom`（由 `dino-extract/src/rom.rs:70` 的 `Rom::find` 自己扫 args，设计分工）。反向差集为空。
- `run.md` 的 22 个 `--jump` 名与 `jumps.rs` 的 `JUMPS` 双向差集都空（`final.txt` N4 断言复核通过）；README 的 11 个 settings key 与 `config.rs` 的 `OPTIONS` 一一对应，默认值逐项与 `Config::default()` 一致；6 步配置查找顺序与 `config.rs:18-19`、`main.rs:299-301` 一致。
- `regress.sh` 是纯 MAME step-mode 回归（要 ROM 与 traces）。**没有**把静态检查挂进去：那会让不需要 ROM 的轻量检查依赖重环境，是倒退。独立入口更可用，已登记在 `re/harness/README.md`。
- 历史文档里的「committed」措辞（`D5-final-plan.md:108/3721`、`re/specs/sound/SPEC.md:23`、`HANDOFF.md:5`、`STATUS.md:44`、`re/notes/DECISIONS.md:140`）仍是旧口径，本轮有意**不扩散改**：它们是当时的设计/计划记录或另一个项目的笔记，不是每轮必读的现行约束；`re/README.md:14`、`asset-catalog.md:5`、`NEW-PLAN.md:34` 本来就写「git-ignored」，与现状一致。

## 本轮口径

- 本轮有实质产物（5 个提交，其中一个是带自检的上游工具），不是「查了一圈没改」，也不是靠换小现象凑 diff。改文档后直接跑 `python re/harness/check_docs.py` 与 `--self-test` 即可复核这 6 类一致性，不必重新人工 Grep。
- 别重演收尾套路：不写「下一轮换一个现象」「等用户经验或新疑点」；开放目标下继续合理工作 ≠ 每轮必须挤出笔记 diff。也别把 379/406 之类无法当场复核的数字抬成结论。
- 别重查已核层：四块主题地图、自检清册全表、§94.11 全文、`0x11CC4` 三条链、§94.15 / §70.3 / `EnemyData.t` 清册行前几轮已核；本轮新核的是 closeout 文档、CLI/config/jump 一致性、git 泄漏面与工具链/ROM 环境。
- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。Stop hook 是客户端自动重发催办，不直读 goal 状态。
