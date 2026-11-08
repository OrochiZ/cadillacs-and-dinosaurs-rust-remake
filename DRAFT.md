# DRAFT — 一次性过桥笔记（读完删除重建）

> 只放本轮、压缩后捡不回的残差。跨轮结论一律进 git 跟踪的耐久层。
> 规矩：新会话 / 压缩后开工先读本文件 → 读完删除重建（不是编辑）。每轮收尾把本轮残差写回。
> 本文件是**「closeout 收口 + 上游工具化（完整版）」**：上一版是 `01a7e9e`（同轮中途版，只记到 5 个提交），本轮后续又推进了工具验证与第 7 项检查，故按机制删除重建写回完整残差。

## 本轮做完的事

开工复位必读层后的关系判定：前十几轮「提现象→查重→收口」的知识层自检不该靠换小现象续命，本轮落在**产品目标里可用工具当场验证的真实步骤**（M10-25 / M10-26 closeout），并把反复撞到的同一类漂移在**上游**固化成工具，而不是每轮重新 Grep。

**七个实质提交 + DRAFT 提交（工作区干净）**：

1. `ffed738` — `plan/PLAN.md` 里程碑表自 `e035775`（2026-10-13）后从未更新（M1 "Next"、M2–M10 "Pending"、Total「456 listed, about 600 expected」），按 `STATUS.md` 同步到 M0–M9 Done / M10 23 of 26，并写明「两者不一致以 STATUS.md 为准」。依据 `D5-final-plan.md:3712-3724`、`NEW-PLAN.md:325`、M10-25 scope。同提交删 `dino-rs/README.md` 的「Fessenden with three heroes」：该节与 `final.txt` 由 `1267e1b`（Task 17）同次建立，`d1ba4a4`（Task 75）把 N1 标 GONE 却漏同步 README。
2. `96df4c5` — `STATUS.md` 开头行仍写「after the M4 checkpoint」并挂 sweep 基线「379 of 418」，与同文件表格矛盾。**特意不把 379 改成 406**：`final.txt:9-11` 明说 results.jsonl 不在盘上、re/out/sweep 已没，本环境无法复核两数是否同批刷新；改为删旧基线并指向 M10-26 权威清单。
3. `0b574b7` — 新增 `re/harness/check_docs.py`（零依赖、不读 ROM、不碰游戏代码），6 项静态检查 + `--self-test`；`re/harness/README.md` 追加独立一节。
4. `ca5f1a5` — 堵假绿：`parse_milestones` 固定列号取状态，两表同时多一列会落到同一个 Hours 值而假通过。加状态词白名单 + 第 7 个「列移位」自检样本。实测 shifted STATUS M1 = 24 / PLAN M1 = 24 / equal=True，naive 判据确实会假绿。
5. `1d1b8b2` — 补参数校验与 `--help`：原先 `--help` 静默跑检查、`--slft-test` 之类拼错会显示「6/6 passed」让人误以为自检跑过。未知参数 exit 2。
6. `41aaa94` — fresh clone 实证（README 的「runs on a fresh clone with no ROM」此前只是推断）：浅克隆到内存盘，无 ROM/target/re/out/rom/venv，正例与自检均过，人为把 M1 改回 `Pending` 后如期 exit 1。
7. `3440900` — 增第 7 项检查：文档命令不得组合 `main.rs` 显式互斥的 flag（`--jump` vs `--episode/--stage/--area/--camx`、`--episode` vs `--stage`、`--headless` vs `--viewer/--view/--windowed`、`--trace` vs `--ally`）。24 条真命令行零违规。过程中第一版判据把散文里列举的 flag 混成一个集合，误报 2 条（那行正是讲互斥规则本身），收紧为只解析真命令行并把理由写进 docstring/README。自检加到 8 样本。**改文档里的「six checks → seven checks」之前，先用 7 项版重跑 fresh clone 实测**，不把结论写得比来源更实。

工具最终状态：7 项检查（里程碑状态、jump 名双向、settings key 双向、CLI flag、命令互斥、GONE 差异、git 泄漏）、`--self-test` 干净基线 + 8 个人为漂移样本、`--help`、未知参数 exit 2。

## 回源与校验

- 工具：正例 `7/7`、自检 `8/8`、`py_compile` OK、从 `R:\Temp` 与 `C:\` 异地运行正常、`--help` exit 0、`--slft-test` exit 2 且无 passed、`git diff --check` OK、`BOM=False / CR=0 / over2000=0`。
- **真实旧版负例**（临时脚本在内存盘，跑完即删）：`ffed738^` 的 PLAN.md 抓到 10 个里程碑漂移、`ffed738^` 的 README 命中 GONE marker、`96df4c5^` 的 STATUS.md 过期开头在场而当前已消失。
- **干净克隆实测两轮**：6 项版（`01a7e9e` HEAD）与 7 项版（覆盖未提交文件到克隆）都通过；后者还在克隆里人为漂移 M1 得到 exit 1。内存盘克隆与临时脚本均已清理。
- 按 §94.11 第四种漏法查重走的是**仓库根全 `*.md`**；核「是不是同一件事」逐条做过（N1 的 190 frames/three heroes/quake debris 与 README 那条逐项对应）。
- 环境限制（已核死，别重复试）：注册表卸载项、常见安装位、`G:\Users` 全无 Rust（cargo/rustc/rustup 全 absent）；`G:\wof` 深度 4、各用户目录无 `dino.zip`；`re/rom`、`re/mame/roms`、`.worktrees`、`dino-rs/target` 不存在；`re/out` 全树只剩 1 个文件 ⇒ `cargo build/test`、`regress.sh`、MAME 对拍与运行时回归做不了。这是硬限制，不是未闭合缺口。

## 查证通过、判定「不用改」的层（下轮别重复查）

- M10-26 git 泄漏扫描：`git ls-files` 1982 个文件全扩展名命中 0；`git ls-files re/out` = 0；`git check-ignore -v re/out/assets/index.html` 由 `re/out/*` 命中；`re/ghidra` 只跟踪 3 个脚本/entries。
- M10-25 debug-gating：`main.rs:203` 只在 `--debug-keys`/`--test` 时启用，`autoplay`/`test`/`trace` 默认全关，与 `run.md:196/211` 一致。
- 源码 30+ 处 `not ported` 是防御性兜底与有意不移植的 debug/anti-tamper 分支，与「no placeholder class is left」不矛盾；个别 M3 时期将来时注释纯属措辞，不扩散。
- CLI flag 集合：文档 42 vs `main.rs` 38，差集仅 cargo/libtest 的 3 个与 `--rom`（由 `dino-extract/src/rom.rs:70` 的 `Rom::find` 自己扫 args）。反向空。
- 22 个 `--jump` 名与 `jumps.rs` 双向差集空；README 11 个 settings key 与 `config.rs` `OPTIONS` 一一对应且默认值逐项一致；6 步配置查找顺序与 `config.rs:18-19`、`main.rs:299-301` 一致。
- `dino-rs/ARCHITECTURE.md` ownership 表 72 个显式 `.rs` 路径按 basename 在 `dino-rs/` 全树（303 个 .rs）**零悬空**。第一版按固定根解析报 40 个 missing 是判据错（表里写的是相对不同根的路径），已纠正。
- Cargo workspace（M10-25「fresh clone builds」的静态前提）：4 个 members 都有目录、4 个 package 名与 `Cargo.lock` 及 `ARCHITECTURE.md` 一致、`edition = "2024"` 与 README 一致、`main.rs` 的 15 个 `mod` 声明零缺失。
- 文档里 23 个 `re/harness/*.sh|py` 脚本引用按 `git ls-files` 全部存在、零悬空（这次用 Python 做，避开前两次 PowerShell 反引号/子表达式被安全策略拦的写法）。
- `regress.sh` 是纯 MAME step-mode 回归（要 ROM 与 traces），**没有**把静态检查挂进去：会让轻量检查依赖重环境，是倒退。
- 历史文档里的「committed」旧措辞（`D5-final-plan.md:108/3721`、`re/specs/sound/SPEC.md:23`、`HANDOFF.md:5`、`re/notes/DECISIONS.md:140`）有意不扩散改；`re/README.md:14`、`asset-catalog.md:5`、`NEW-PLAN.md:34` 本来就写「git-ignored」，与现状一致。
- `final.txt` 有 10+ 处 GONE，但绝大多数是 `Player sees: no` 的 trace/harness 差异，README 的 Known Differences 只列玩家可见的 6 条；工具用显式哨兵表（`GONE_MARKERS`）而非强制每个 GONE 都有 marker，避免噪音。**不再给工具加第 8、9 项检查**：继续加会变成「为不停制造边际活」。

## 本轮口径

- 本轮有实质产物（7 个提交，核心是带自检的上游工具），不是「查了一圈没改」，也不是换小现象凑 diff。改文档后直接跑 `python re/harness/check_docs.py` 与 `--self-test` 即可复核这 7 类一致性。
- 别重演收尾套路：不写「下一轮换一个现象」「等用户经验或新疑点」；开放目标下继续合理工作 ≠ 每轮必须挤出笔记 diff。也别把 379/406 之类无法当场复核的数字抬成结论。
- 别重查已核层：四块主题地图、自检清册全表、§94.11 全文、`0x11CC4` 三条链、§94.15 / §70.3 / `EnemyData.t` 清册行前几轮已核。
- `长时间自主推进` 仍是开放目标；局部提交、干净工作区、本轮收尾都**不算完成或缩小**。Stop hook 是客户端自动重发催办，不直读 goal 状态。
