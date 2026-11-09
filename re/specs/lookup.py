#!/usr/bin/env python3
"""取值 -> 抽象意义 的离线查询、ANI 帧解码、生成记录解码。

不读 ROM、不依赖第三方包；语义全部来自同目录 semantics.json（人工核对过的缓存），
原始数值仍回源各 SPEC / tables.txt。设计动机：看到一段 ANI / SPR / 生成记录，
就能直接知道「这一帧 / 这一条在干嘛」，而不必去翻散在各卷的文字。

用法（在任意目录）：
    python re/specs/lookup.py                          打印这份用法说明
    python re/specs/lookup.py list                     列出所有可查的域
    python re/specs/lookup.py frame_type              列出该域全部取值与意义
    python re/specs/lookup.py frame_type 4            查一个取值（支持 4 / 04 / 0x04 / 0xA）
    python re/specs/lookup.py drop_code 25            范围取值也能查（1-19 是武器 ...）
    python re/specs/lookup.py attr 0x3020              拆 SPR attr 字的各位
    python re/specs/lookup.py flags draw_flags 0x81    拆位域（域, 值）
    python re/specs/lookup.py frame 10 0A01 8000 0100 0405 1A02        解码 10 字节帧记录
    python re/specs/lookup.py frame 12 0A01 8000 0100 0405 1A02 0011    解码 12 字节帧记录
    python re/specs/lookup.py anim 10 0A01 8000 0100 0405 1A02 0A01 8000 0100 0085 1A02
                                                         把一串帧记录翻成一段动画时间线（kind 4 且开盒才算攻击生效；kind 6 特殊 / 必杀帧单列）
    python re/specs/lookup.py comp 0002 0002 0005 0003 0802 0803 FFF8 FFE0 0008 FFF0
                                                         把一串 SPR composition 翻成「几块图 / 贴在哪」
    python re/specs/lookup.py box -1 10 -68 59 29 42     六个 i16 判定盒 -> 打哪儿 / 够多远
    python re/specs/lookup.py spawn 04D0 0141 0008 0120 0040 0000 0000   解码 14 字节生成记录
    python re/specs/lookup.py spawn 16 04D0 0141 0008 0120 0040 0000 0000 0000
    python re/specs/lookup.py script 2C 00 05 01 000A   解码 6 字节过场脚本记录
    python re/specs/lookup.py attack 0A 01 00 09 03 14 00 00
                                                      8 字节攻击属性记录 -> 这一拳打完会怎样（反应门票两侧并排）
    python re/specs/lookup.py wof_attack ours 00 00 00 00 0A 00 03 00 56 00 00 00 06 0E 03 00
                                                      16 字节 wof 参数行 -> 这一招一行在说什么
    python re/specs/lookup.py wof_attack enemy ...   敌→玩家那张表布局不同，字段含义看命中链
    python re/specs/lookup.py chain                   ANI -> SPR -> 判定框 能推断什么（说明版）
    python re/specs/lookup.py moment 10 0A01 8000 0100 0405 1A02
                                                      把同一帧的几份数据合起来说「在干嘛」
    python re/specs/lookup.py moment 10 ... attack 0A 01 00 09 03 14 00 00
                                                      再挂上这一拳打完的后果
    python re/specs/lookup.py moment 10 ... comp 0002 0002 0005 0003 0802 0803
                                                      SPR 那一环也喂进来，画面与判定并排
    python re/specs/lookup.py find 攻击                按意义关键词反查
    python re/specs/lookup.py collide 4               只给一个取值，列出它在各域的所有意义
    python re/specs/lookup.py collide 0x1A            看同一编号在哪几张表里意思不同
    python re/specs/lookup.py attack_id 0x5A          查一个攻击编号是哪一招
    python re/specs/lookup.py anim_id 1 4             查这一招是哪段，并带出这一拳的后果
    python re/specs/lookup.py player_hurt_anim 2      挨打后会播受击动画的第几段、后面还有几拍
    python re/specs/lookup.py enemy_hurt_anim 3       敌人挨打分派到哪个受击姿态槽（按兵种翻表）
    python re/specs/lookup.py coverage                哪些表已转、哪些按纪律不转、为什么
    python re/specs/lookup.py unknown                  一次列出「还没弄明白」的取值与整类不转的表（每条带回源止于何处）
    python re/specs/lookup.py unknown player_ground_state   只看某一册里哪些编号还没登记
    python re/specs/lookup.py themes                  按玩法主题列出可查的域与证据成色
    python re/specs/lookup.py themes state_machine    只看状态机这一块
    python re/specs/lookup.py legacy                  外推文九条判断各自能查到什么、查不到什么
    python re/specs/lookup.py legacy difficulty      只看其中一条
    python re/specs/lookup.py --json frame_type 4     机器可读输出
    python re/specs/lookup.py --selftest              固化自测（不依赖 ROM）

边界：本工具只回答「这个取值在这份 rep 已登记的意义里是什么」，不推断未登记取值、
不把 [I] 说成 [O]、不做跨游戏等价；喂字节翻意义的解码输出也带上 [O] / [I] / [U] 标签，
别只挑其中一句读。未命中就直说未登记。
同一编号在玩家侧 / 敌人侧、dino / wof 侧含义可以相反，上下文相关的域会提示先确认对象。
"""
from __future__ import annotations

import contextlib
import io
import itertools
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).resolve().parent
DB = json.loads((HERE / "semantics.json").read_text(encoding="utf-8"))
DOMAINS = DB["domains"]

# 这些域的「数字」是字节偏移或位编号，不是游戏里读到的取值；
# 只给一个取值反查时必须排除，否则会把 "+4 字段" 当成 "取值 4"。
OFFSET_KEY_DOMAINS = ("attack_field", "box_field", "wof_atk_field", "comp_extra", "camera_event", "dino_script_record")

# SPEC §4.4 [O]：普通命中循环要求攻方 +$2E == 4，只有这类帧把 +$49
# 拿去和防守方 +$48 相交。6 是 [I] 推断的特殊 / 必杀帧，那张含 6 的表
# 是防守方类型分派，不是攻方；解码时单列，别把推断数成攻击生效帧。
# 0 / 2 的 +$49 是抓投探测，8 / 10 / 12 / 14 不发起攻击。
ATTACK_KINDS = (4,)
SPECIAL_KINDS = (6,)
GRAB_KINDS = (0, 2)

# 一次挥击的完整拍子样本：起势 / 普通生效 / 必杀 / 攻击帧关盒 / 收势末帧。
# 自测与全命令冒烟共用，确保时间线不把 kind=6 读成收招。
_ANIM_BEAT = ["10", "0A01", "8000", "0100", "0006", "1A00",
              "0A01", "8000", "0100", "0403", "1A02",
              "0A01", "8000", "0100", "0604", "0005",
              "0A01", "8000", "0100", "0402", "1A00",
              "0A01", "8000", "0100", "0085", "1A00", "0011"]

# SPEC §3.6 只逐段列了 Jack 的前三套；第 3/4/5 套只有套级用途。
SET_DOMAINS = {0: "jack_anim_set0", 1: "jack_anim_set1", 2: "jack_anim_set2"}

# dino 8 字节攻击记录里的反应编号是「门票」：挨打的是玩家还是敌人，
# 由两本不同的受击册子读。wof 那 16 字节行是另一套，不在这里串等价。
REACTION_DOMAINS = ("player_hurt_reaction", "enemy_hurt_reaction")
REACTION_LABELS = {"player_hurt_reaction": "玩家挨打", "enemy_hurt_reaction": "敌人挨打"}


# ---------- 取值解析 ----------
def parse_value(s: str):
    """返回 (整数值, 规范化键列表)。支持 4 / 04 / 0x04 / 0xA / 十进制字符串键。"""
    s = s.strip()
    cands = [s]
    try:
        if s.lower().startswith("0x"):
            n = int(s, 16)
        elif s.isdigit():
            n = int(s, 10)
        else:
            n = int(s, 16)          # 含 A-F 的裸十六进制，如 0A / 0E
        cands += [str(n), f"0x{n:X}", f"0x{n:02X}", f"0x{n:02x}"]
    except ValueError:
        return None, cands
    return n, list(dict.fromkeys(cands))


def match_value(dom: dict, token: str):
    """在域里找取值：精确键 -> 别名 -> 范围键 -> nonzero/other 兜底。"""
    vals = dom["values"]
    n, cands = parse_value(token)
    if n is not None:
        # 有些域的键写成 "+0" / "+10"（字段偏移），查纯数字时也该命中
        cands = list(dict.fromkeys(cands + ["+" + str(n)]))
    for c in cands:
        if c in vals:
            return c, vals[c]
    for k, v in vals.items():
        alias = str(v.get("alias", ""))
        if alias and any(c.lower() == alias.lower() for c in cands):
            return k, v
    if n is not None:
        for k, v in vals.items():
            m = re.fullmatch(r"(\d+)-(\d+)", k)
            if m and int(m.group(1)) <= n <= int(m.group(2)):
                return k, v
        for fallback in ("nonzero", "other", "negative", "low7=n"):
            if fallback not in vals:
                continue
            if fallback == "nonzero" and n == 0:
                continue
            if fallback == "negative" and n >= 0:
                continue
            return fallback, vals[fallback]
    return None, None


def fmt(tag: str) -> str:
    return {"O": "[O 观察]", "I": "[I 推断]", "U": "[U 未登记]"}.get(tag, f"[{tag}]")


def say(v: dict | None, fallback: str = "未登记") -> str:
    """解码命令里凡是直接引用缓存意义的，都连置信标签一起说。

    查单值 / 列域 / 反查都带 fmt；喂字节翻意义的那几条不该例外，
    否则「身份：特殊 / 必杀攻击帧」这种 [I] 会被读成观察事实。
    字段 / 位偏移说明（「+0..3 是伤害随机偏移」）讲的是这一格叫什么、
    不是某个取值的意义，按取值反查排除字段偏移域的同一纪律，不走这里。
    """
    return f"{v['meaning']} {fmt(v['tag'])}" if v else fallback


# ---------- 命令 ----------
def cmd_list():
    print(f"可查的域（{len(DOMAINS)} 个）  语义缓存：{HERE / 'semantics.json'}")
    print("=" * 78)
    for name, d in DOMAINS.items():
        flag = " 位域" if d.get("bitfield") else ""
        ctx = " 上下文相关" if d.get("context_dependent") else ""
        rng = " 含范围" if any(re.fullmatch(r"\d+-\d+", k) for k in d["values"]) else ""
        print(f"  {name:22s} {d['label']}{flag}{ctx}{rng}")
        print(f"  {'':22s} scope={d['scope']}  条目 {len(d['values'])}  src={d['source']}")
    print("\n用 `lookup.py <域> [取值]` 查单值；喂字节解码：`frame` / `anim` / `comp` / "
          "`box` / `spawn` / `script` / `attack` / `wof_attack`；"
          "串链：`chain`（说明）/ `moment`（喂同一帧的数据合成一句）/ `anim_id`。")
    print("三个索引：`coverage`（按回源分组）/ `themes`（按玩法问题）/ "
          "`legacy`（外推文九条判断各能查到什么、查不到什么）；"
          "`unknown` 一次列出还没弄明白的取值与整类不转的表（未登记 ≠ 不存在）。")
    return 0


def cmd_domain(name: str):
    d = DOMAINS.get(name)
    if not d:
        print(f"没有这个域：{name}。可用：{', '.join(DOMAINS)}")
        return 1
    print(f"{name} — {d['label']}")
    print(f"scope={d['scope']}  source={d['source']}")
    if d.get("note"):
        print(f"注意：{d['note']}")
    if d.get("bitfield"):
        print(f"（位域：数值按位拆，可用 `flags {name} <值>`）")
    print("-" * 78)
    for k, v in d["values"].items():
        alias = f"  (别名 {v['alias']})" if v.get("alias") else ""
        print(f"  {k:14s} {fmt(v['tag'])} {v['meaning']}{alias}")
        if v.get("note"):
            print(f"  {'':14s} └ {v['note']}")
    return 0


def emit(domain: str, key: str, v: dict, as_json: bool):
    if as_json:
        print(json.dumps({"domain": domain, "key": key, **v}, ensure_ascii=False))
    else:
        print(f"  {domain}.{key}  {fmt(v['tag'])} {v['meaning']}")
        if v.get("alias"):
            print(f"      别名 {v['alias']}")
        if v.get("note"):
            print(f"      {v['note']}")
        d = DOMAINS[domain]
        if d.get("context_dependent"):
            print(f"      注意（上下文相关）：{d.get('note', '查这个域要带 scope / 对象 / 链')}")
        print(f"      src={d['source']}")


def cmd_lookup(name: str, token: str, as_json: bool):
    d = DOMAINS.get(name)
    if not d:
        print(f"没有这个域：{name}")
        return 1
    # 描述性字符串键（如 ours:+0xC、dino/wof、negative、hi=f>>8）优先精确命中
    if token in d["values"]:
        emit(name, token, d["values"][token], as_json)
        return 0
    key, v = match_value(d, token)
    if v is None:
        print(f"  {name}.{token}：未登记。这个域已有的键：{', '.join(d['values'])}")
        print("  （不猜：没有出处的意义请标 [U] 并补 source 后再加进 semantics.json）")
        return 2
    emit(name, key, v, as_json)
    return 0


def cmd_flags(name: str, token: str):
    d = DOMAINS.get(name)
    if not d or not d.get("bitfield"):
        print(f"{name} 不是位域。位域有：{', '.join(k for k, v in DOMAINS.items() if v.get('bitfield'))}")
        return 1
    n, _ = parse_value(token)
    if n is None:
        print(f"读不出数值：{token}")
        return 1
    print(f"{name} = 0x{n:X} ({n}) — {d['label']}")
    for k, v in d["values"].items():
        if "-" in k:
            lo, hi = (int(x) for x in k.split("-"))
            field = (n >> lo) & ((1 << (hi - lo + 1)) - 1)
            hit = field != 0 or lo == 0
            print(f"  bits {k:6s} = {field:<6d} {fmt(v['tag'])} {v['meaning']}" + ("" if hit else "  (当前为 0)"))
        else:
            b = int(k)
            on = bool(n & (1 << b))
            print(f"  bit  {b:<6d} = {int(on):<6d} {'ON ' if on else 'off'} {fmt(v['tag'])} {v['meaning']}")
    print(f"  src={d['source']}")
    return 0


def u16(b: bytes, off: int) -> int:
    return (b[off] << 8) | b[off + 1]


def cmd_frame(tokens: list[str]):
    """解码一条帧记录：10 字节（敌人/多数对象）或 12 字节（玩家）。"""
    if not tokens:
        print("用法：frame [10|12] <hex bytes...>   例：frame 10 0A01 8000 0100 0405 1A02")
        return 1
    stride = None
    if tokens[0] in ("10", "12"):
        stride = int(tokens[0])
        tokens = tokens[1:]
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in tokens)
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"十六进制读不出：{e}")
        return 1
    if stride is None:
        stride = 12 if len(b) == 12 else 10
    if len(b) < 10 or (stride == 12 and len(b) < 12):
        print(f"字节不够：拿到 {len(b)}，{stride} 字节格式需要 {stride}")
        return 1
    b = b[:stride]
    w0, w1 = u16(b, 0), u16(b, 2)
    p_a, p_b, kind, timer, body, atk = b[4], b[5], b[6], b[7], b[8], b[9]
    dur = timer & 0x7F
    last = bool(timer & 0x80)

    print(f"帧记录 {stride} 字节：{' '.join(f'{x:02X}' for x in b)}")
    print("-" * 78)
    print(f"  +0..1 w0 = 0x{w0:04X}  主 composition 索引（字节偏移）", end="")
    print("  ← w0 bit15=1：复合帧，w1 是部件表自相对偏移" if w0 & 0x8000 else "")
    print(f"  +2..3 w1 = 0x{w1:04X}  ", end="")
    print("叠加层：无（bit15=1）" if w1 & 0x8000 else "叠加 composition 索引（画在主体之后/下方）")
    print(f"  +4    param_a = 0x{p_a:02X}  → obj+$2C：按状态而定，脱离处境无固定意义 [U]")
    if p_a == 1:
        print("         └ 在拳类动画里 = 连段取消窗口开放 [I]（re/specs/anim/SPEC.md §1）")
    print(f"  +5    param_b = 0x{p_b:02X}  → obj+$2D：相位索引；"
          "分身绘制时按它查 +$38 偏移表重同步 [O]")
    kv, vv = match_value(DOMAINS["frame_type"], str(kind))
    print(f"  +6    kind    = 0x{kind:02X}  → obj+$2E 帧类型：", end="")
    print(say(vv))
    if vv and vv.get("note"):
        print(f"         └ {vv['note']}")
    print(f"  +7    timer   = 0x{timer:02X}  → 时长 {256 if dur == 0 else dur} tick；"
          f"bit7={'1 末帧，后跟 i16 link word' if last else '0 顺序下一帧'}")
    print(f"  +8    body_box   = 0x{body:02X}  → " +
          ("没有身体盒（这一帧打不到它） [O]" if body == 0 else f"身体盒索引 {body}（查 +$44 表第 {body} 项）"))
    print(f"  +9    attack_box = 0x{atk:02X}  → " +
          ("没有攻击盒 / 关盒 [O]" if atk == 0 else f"攻击盒索引 {atk}（查 +$44 表第 {atk} 项）"))
    if stride == 12:
        print(f"  +10..11 attach = 0x{u16(b, 10):04X}  → obj+$60；高字节 = 附着点索引（持械 / 抓人）")
    print("-" * 78)
    print("这一帧在干嘛（只靠数值，不看 GFX）：")
    for line in infer(kind, body, atk, dur, last, w0):
        print(f"  · {line}")
    print("\n  看不到 GFX 仍能知道：打哪儿、打多久、这一帧算攻击还是受击、结束后往哪走。")
    print("  看不到 GFX 无法知道：这一帧画的是什么造型、素材好不好看 —— 那归 composition/code。")
    for label, idx in (("攻击盒", atk), ("身体盒", body)):
        if idx == 0:
            continue
        _, bv = match_value(DOMAINS["jack_box_example"], str(idx))
        if bv:
            print(f"  · {label} #{idx} 若属 Jack（盒表 0x100000）：{say(bv)}")
            print("    别的角色 / 敌人按自己的盒表取同一个索引，形状不同，别套。")
    return 0


def infer(kind, body, atk, dur, last, w0) -> list[str]:
    out = []
    fk, fv = match_value(DOMAINS["frame_type"], str(kind))
    if fv:
        out.append(f"身份：{say(fv)}")
    if kind == 4 and atk:
        out.append(f"攻击生效：+$49 有攻击盒 #{atk}，与防守方 +$48 身体盒相交才命中；"
                   "盒的 6 个 i16 决定前伸距离、打的高度、纵深容差")
    if kind == 4 and not atk:
        out.append("标了『攻击生效』却没有攻击盒 → 这一帧实际上打不到人（可能是收招或过渡）")
    if kind in (0, 2) and atk:
        out.append("非攻击帧却带攻击盒 → 抓投探测，目标限定在特定状态")
    if body == 0:
        out.append("没有身体盒 → 这一帧自己不可被命中（必杀 / 无敌 / 演出帧）")
    else:
        out.append(f"有身体盒 #{body} → 自己仍可被反击，攻防同时成立")
    if kind in (8, 10):
        out.append("受击 / 倒地身份 → 命中循环会跳过它，不会被连锁追打")
    out.append(f"这一拍占 {256 if dur == 0 else dur} tick（0 不是不显示，是 256）")
    out.append("末帧后的 link word 决定是回环还是跳到另一段（连段接哪一招写在这里）" if last
               else "顺序推进到下一帧，段落还没结束")
    if w0 & 0x8000:
        out.append("复合帧：多个 composition 各带独立 dx/dy，常用来做『身体 + 上下起伏部件』")
    return out


def cmd_spawn(tokens: list[str]):
    """解码一条生成记录：14 字节（list 1，布景 / 脚本命令）或 16 字节（list 2，敌人 / 波次）。"""
    if not tokens:
        print("用法：spawn [14|16] <hex bytes...>   例：spawn 04D0 0100 0008 0120 0040 0000 0000")
        return 1
    stride = None
    if tokens[0] in ("14", "16"):
        stride = int(tokens[0])
        tokens = tokens[1:]
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in tokens)
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"十六进制读不出：{e}")
        return 1
    if stride is None:
        stride = 16 if len(b) == 16 else 14
    if len(b) < stride:
        print(f"字节不够：拿到 {len(b)}，{stride} 字节格式需要 {stride}")
        return 1
    b = b[:stride]
    trig, flags, cls = u16(b, 0), u16(b, 2), u16(b, 4)
    x, z, var = u16(b, 6), u16(b, 8), u16(b, 10)
    hi = flags >> 8
    sf = DOMAINS["spawn_flags"]["values"]

    print(f"生成记录 {stride} 字节：{' '.join(f'{v:02X}' for v in b)}")
    print("-" * 78)
    print(f"  +0   trig  = 0x{trig:04X}  触发镜头位置；波次记录里这一格换成 delay 帧数")
    print(f"  +2   flags = 0x{flags:04X}  低字节装命令位 / 人数门 / 难度门 / 池选择，"
          f"高字节 0x{hi:02X} 只在难度门打开时当阈值读")
    print(f"  +4   class = 0x{cls:04X}  → 对象 +$20 派发偏移；若是命令则这一格是命令字")
    print(f"  +6   x     = 0x{x:04X}    +8 z = 0x{z:04X}    +A var = 0x{var:04X}")
    if stride == 14:
        print(f"  +C   y     = 0x{u16(b, 12):04X}")
    else:
        print(f"  +C   w5c   = 0x{u16(b, 12):04X}    +E b5b = 0x{b[14]:02X}（入场方式等）"
              f"   +F b96 = 0x{b[15]:02X}（掉落表行）")
    print("-" * 78)

    if flags & 0x80:
        ck, cv = match_value(DOMAINS["spawn_command"], str(cls))
        print("这条不是生成对象，是脚本命令（flags 低字节 bit7 置位）")
        print(f"  命令字 0x{cls:04X} → " + (f"{cv['meaning']} {fmt(cv['tag'])}" if cv else "未登记，代码里是空操作"))
        return 0

    pk, pv = match_value(DOMAINS["spawn_pool"], str(flags & 7))
    print(f"生成目标：" + (f"flags&7 = {flags & 7} → {pv['meaning']} {fmt(pv['tag'])}" if pv else "池未登记"))
    print(f"  把 +$20 设成 0x{cls:04X}，落在 (X, Z) = (0x{x:04X}, 0x{z:04X})，var = 0x{var:04X}")

    cond = []
    c60 = flags & 0x60
    if c60 == 0x40:
        cond.append(sf["&0x60=0x40"]["meaning"])
    elif c60 == 0x60:
        cond.append(sf["&0x60=0x60"]["meaning"])
    c18 = flags & 0x18
    if c18 & 0x10:
        cond.append(sf["&0x18=0x10"]["meaning"].replace("高字节 hi", f"hi={hi}"))
    elif c18 & 0x08:
        cond.append(sf["&0x18=0x08"]["meaning"].replace("高字节 hi", f"hi={hi}"))
    if cond:
        print("放行条件：" + "；".join(cond))
    else:
        print("放行条件：无人数 / 难度门，镜头一到就生成")
    print("池满时：" + ("这一条被丢弃，本帧停止处理 list 1" if stride == 14
                     else "这一条被跳过（指针已前进），本帧停止处理 list 2"))
    if stride == 16 and b[14]:
        ek, ev = match_value(DOMAINS["entrance"], str(b[14]))
        if ev:
            print(f"入场方式 b5b=0x{b[14]:02X} → {ev['meaning']} {fmt(ev['tag'])}")
    return 0


def cmd_script(tokens: list[str]):
    """解码一条 dino 英雄过场脚本记录（6 字节）：翻成『这一条在等什么 / 覆写什么 / 放行什么』。"""
    if not tokens:
        print("用法：script <6 bytes...>   例：script 2C 00 05 01 000A")
        print("      6 字节 = action, floor_only(G.$4F0), argument(G.$4FD), "
              "no_clamp(G.$506), timer:word(BE)")
        return 1
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in tokens)
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"十六进制读不出：{e}")
        return 1
    if len(b) < 6:
        print(f"字节不够：拿到 {len(b)}，一条过场脚本记录要 6 字节")
        return 1
    b = b[:6]
    action, floor_only, argument, no_clamp = b[0], b[1], b[2], b[3]
    timer = u16(b, 4)
    act_dom = DOMAINS["dino_script_action"]
    rec = DOMAINS["dino_script_record"]["values"]

    print(f"过场脚本记录 6 字节：{' '.join(f'{x:02X}' for x in b)}   "
          "（dino 英雄过场，script.rs 0x1DB5E 每帧读一条）")
    print(f"  src={DOMAINS['dino_script_record']['source']}")
    print("-" * 78)
    _, av = match_value(act_dom, f"0x{action:02X}")
    print(f"  +0 action = 0x{action:02X}  → " +
          (f"{av['meaning']} {fmt(av['tag'])}" if av
           else "不在 41 项里，走 script_action 的 default 空分支 [O]"))
    print("        └ 这是跳表 0x1DBD6 的字节偏移，不是动作序号；"
          "全部 41 项查 `lookup.py dino_script_action`")
    # +1/+3 是布尔档位字（player.rs 按 ==0 / !=0 读）；文案取自缓存，开/关按本条取值实时判
    f1 = rec["+1"]["meaning"].split("：", 1)[-1]
    f3 = rec["+3"]["meaning"].split("：", 1)[-1]
    print(f"  +1 floor_only (G.$4F0) = 0x{floor_only:02X}  "
          f"[{'开' if floor_only else '关'}] 置位时：{f1}"
          + ("" if floor_only else "；这一位是 0，墙照常挡人（默认地形判定）"))
    print(f"  +2 argument   (G.$4FD) = 0x{argument:02X}  "
          f"{rec['+2']['meaning'].split('：', 1)[-1]}")
    print(f"  +3 no_clamp   (G.$506) = 0x{no_clamp:02X}  "
          f"[{'开' if no_clamp else '关'}] 置位时：{f3}"
          + ("" if no_clamp else "；这一位是 0，留在屏幕钳制范围内、路过照常捡东西"))
    if timer == 0xFFFF:
        print("  +4 timer:word = 0xFFFF  → wait-until：条件没达就每帧重跑本条，"
              "绝不推进到下一条")
    else:
        print(f"  +4 timer:word = 0x{timer:04X}  → 本条动作跑 {timer} 帧，"
              "逐帧递减到 0 才读下一条")
    print("-" * 78)
    print("这一条在干嘛（只靠六个字节，不看画面）：")
    if av:
        head = av["meaning"].split("：")[0]
        print(f"  · 动作是「{head}」——41 个 action 里多数不是播动画："
              "要么在等一个条件，要么覆写输入让角色走自己完整的玩家状态机，少数才直接改世界")
        if "G.$7A9" in av["meaning"]:
            print("  · 它直接改世界：把镜头锁的放行字 G.$7A9 置 1 —— "
                  "和波次收尾 `wave_end` 写的是同一个 GO，查 `lookup.py wave_end` 对得上")
    else:
        print("  · action 不在 41 项里，这条什么都不做（default 空分支），输入原样通过")
    print(f"  · 两个规则档位现在是 floor_only {'开' if floor_only else '关'} / "
          f"no_clamp {'开' if no_clamp else '关'}；它们不是本条专属，"
          "会保留到后续每一条记录（含 END），直到下一个脚本首记录才重置")
    print("  · 状态字 +$04 != 0x0200（受击 / 死亡 / 复活）时整条脚本挂起，本条不执行")
    print("  · 下一条何时读：" +
          ("条件满足那一刻才推进（0xFFFF wait-until，条件没达就每帧重跑本条）"
           if timer == 0xFFFF else
           f"本条跑满 {timer} 帧、timer 减到 0 时翻到下一条 6 字节记录"))
    print("\n  看不到画面也能知道：这条在等什么 / 覆写什么 / 放行什么、跑几帧、"
          "下一拍什么时候翻页。")
    print("  看不到画面不能知道：字幕写了什么字、声音长什么样、姿势具体造型 "
          "—— 那在文本 / 声音表 / GFX 里。")
    print("  单看一条不够：档位会跨记录延续，连着上一条一起读才知道这一帧按什么规则跑。")
    return 0


def hurt_anim_for(react: int) -> list[str]:
    """反应门票后面那一环：受击代码会去播 set2 的第几段。

    用 player_hurt_anim.reactions 反查，不在别处再抄一份映射。一个反应
    可以命中多段（正面 / 背后分岔），此时明说不是同时播。只接玩家侧：
    敌人侧的 anim 编号还要按兵种翻一张表，见 enemy_hurt_reaction。
    """
    dom = DOMAINS.get("player_hurt_anim")
    if not dom:
        return []
    hits = [(k, v) for k, v in dom["values"].items()
            if react in v.get("reactions", [])]
    if not hits:
        return []
    out = [f"    → 接着播 set2 #{k}：{say(v)}" for k, v in hits]
    if len(hits) > 1:
        out.append("    （上面几段按正面 / 背后等条件分岔，不是同时播）")
    return out


def enemy_hurt_anim_for(react: int) -> list[str]:
    """敌人册子后面那一环：受击代码分派到哪个姿态槽。

    和玩家侧分开反查：同一个反应编号两侧不是同一个意思，下游自然
    各走各的。只列直接分派；改判击倒那种条件分支不在这里冒充同时播。
    """
    dom = DOMAINS.get("enemy_hurt_anim")
    if not dom:
        return []
    hits = [(k, v) for k, v in dom["values"].items()
            if react in v.get("reactions", [])]
    return [f"    → 敌人姿态槽 #{k}：{say(v)}" for k, v in hits]


def reaction_brief(react: int) -> list[str]:
    """把攻击记录里的反应门票在 dino 两本受击册子里的读法并排列出来。

    只列 dino 两侧、不自动串 wof：这条记录本来就是 dino 的 8 字节结构，
    把 wof 反应表并排进来会被读成「同一个编号两边等价」。
    """
    out = []
    for name in REACTION_DOMAINS:
        k, v = match_value(DOMAINS[name], str(react))
        if v:
            generic = "（兜底键，不是这个编号的专门登记）" \
                if k in ("nonzero", "other", "negative", "low7=n") else ""
            out.append(f"  {name:24s} → {say(v)}{generic}   [{REACTION_LABELS[name]}]")
            # 各自的下游紧跟自己那本册子：同一编号两侧各走各的链，别串
            if name == "player_hurt_reaction":
                out.extend(hurt_anim_for(react))
            elif name == "enemy_hurt_reaction":
                out.extend(enemy_hurt_anim_for(react))
    if not out:
        out.append("  这个编号两本册子都没登记：不硬答，回源各自的 source")
    return out


def cmd_attack(tokens: list[str]):
    """解码一条 8 字节攻击属性记录：把 +0..+7 合成「这一拳打完会怎样」。"""
    if not tokens:
        print("用法：attack <8 bytes...>   例：attack 0A 01 00 09 03 14 00 00")
        print("      8 字节 = damage, stun, reaction, hit-stop, sound, score, spark, +$9A")
        return 1
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in tokens)
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"十六进制读不出：{e}")
        return 1
    if len(b) < 8:
        print(f"字节不够：拿到 {len(b)}，一条攻击属性记录要 8 字节")
        return 1
    b = b[:8]
    fields = DOMAINS["attack_field"]["values"]
    print(f"攻击属性记录 8 字节：{' '.join(f'{x:02X}' for x in b)}  "
          "（AttackRecord，obj+$58 指向；re/specs/anim/SPEC.md §4.5）")
    print("-" * 78)
    names = ["damage", "stun", "reaction", "hit-stop", "sound", "score", "spark", "+$9A"]
    for key, name in zip(fields, names):
        i = int(key.lstrip("+"))
        print(f"  {key:>4} {name:<9} = {b[i]:3d} (0x{b[i]:02X})  → {fields[key]['meaning']}")
    print("-" * 78)
    print("这一拳打完会怎样（合起来看，不看 GFX）：")
    dmg, stun, react, stop, snd, score, spark = b[0], b[1], b[2], b[3], b[4], b[5], b[6]
    print(f"  · 扣 {dmg} 血、削 {stun} 点韧性；攻守双方一起顿 {stop} 帧，"
          f"攻击方记 {score} 分（作为 score_bcd 的字节偏移）")
    print(f"  · 受击反应 {react} 只是第一张门票：写进挨打者 +$7B / +$06，"
          "后面还隔着受击状态机、状态档位、按 ObjId 的动画链")
    print("    同一个编号两本册子各讲各的，先确定挨打的是谁：")
    for line in reaction_brief(react):
        print("    " + line)
    print("    两本都是 dino 侧；wof 那 16 字节行是另一套，别把编号直接对上（见 `wof_attack`）。")
    print(f"  · 音效 {snd}（0 = 无）、火花类型 {spark}（交给特效对象）；"
          "帧记录本身不带伤害，是状态代码把 +$58 设成偶数才指到这条记录")
    hit = None
    for k, v in DOMAINS["jack_attack_record"]["values"].items():
        if v.get("bytes", "").lower() == b.hex():
            hit = (k, v)
            break
    if hit:
        k, v = hit
        print(f"\n  对照 Jack 连段：这条记录的 $58 = {k}。{say(v)}")
        print("  三拳并排（10/15/29 伤害、9/9/13 顿帧、反应 0/2/6）：")
        print("  伤害与削韧逐拳跳档；顿帧前两拳都是 9，只在收束那拳拉到 13；")
        print("  反应 0 → 2 → 6（SPEC 把 6 标成击倒 [I]），火花也只在最后一拳给。")
        print("  「连段是打出来的」不是手感形容词，是三行逐招数据里写好的代价递进；")
        print("  按 input_buffer 的读法，前两拳不加重自己的停顿，续拳窗口照旧，")
        print("  重的时间成本留给收尾那一下。")
    else:
        print("\n  这条不在 Jack 三条示例里：逐招数值表里还有别的招，本机不登记，"
              "不替它猜名字（回源 re/specs/anim/SPEC.md §4.5）。")
    print("\n  wof 半边不是这 8 字节结构：那边一招一行 16 字节、按攻防方向分两张表，"
          "用 `lookup.py wof_attack <ours|enemy> <16 bytes>` 翻。")
    return 0


def cmd_wof_attack(tokens: list[str]):
    """解码 wof 一招一行 16 字节参数行：按我方 / 敌方布局翻出这一行在说什么。"""
    usage = (
        "用法：wof_attack <ours|enemy> <16 bytes...>\n"
        "      例：wof_attack ours 00 00 00 00 0A 00 03 00 56 00 00 00 06 0E 03 00\n"
        "      ours = 我方表 0x6DB44（玩家→敌），enemy = 敌方表 0x6E754（敌→玩家）"
    )
    if not tokens or tokens[0] not in ("ours", "enemy"):
        print(usage)
        return 1
    side = tokens[0]
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in tokens[1:])
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"十六进制读不出：{e}")
        return 1
    if len(b) < 16:
        print(f"字节不够：拿到 {len(b)}，一招一行要 16 字节")
        return 1
    b = b[:16]
    fields = DOMAINS["wof_atk_field"]["values"]
    table = "0x6DB44（我方）" if side == "ours" else "0x6E754（敌方）"
    print(f"wof 一招一行 16 字节参数行  [{side} / {table}]")
    print(f"  {' '.join(f'{x:02X}' for x in b)}")
    print("  两张表都是 16 字节但行内布局不同；同一字节在不同命中链里还会被读成别的东西。")
    print("-" * 78)
    if side == "ours":
        layout = [(0, 4, "ours:+0..3"), (4, 2, "ours:+4..5"),
                  (6, 2, "ours:+6..7"), (8, 2, "ours:+8..9"),
                  (11, 1, "ours:+0xB"), (12, 1, "ours:+0xC"),
                  (13, 1, "ours:+0xD"), (14, 1, "ours:+0xE")]
        reaction_at, lethal_at, shake_at = 12, 13, 14
        reaction_dom, reaction_label = "wof_reaction", "敌人侧受击入口 0x11878"
        gaps = ["+0xA 这一格回源没给消费端，不硬答",
                "+0xF 民间资料标『呆』，按 §11.0 未串等价，不登记意义"]
    else:
        layout = [(0, 4, "enemy:+0..3"), (4, 2, "enemy:+4..5"),
                  (6, 2, "enemy:+6..7"), (8, 2, "enemy:+8..9"),
                  (10, 1, "enemy:+0xA"), (11, 1, "enemy:+0xB"),
                  (12, 1, "enemy:+0xC")]
        reaction_at, lethal_at, shake_at = 10, 11, 12
        reaction_dom, reaction_label = "wof_player_reaction", "玩家侧受击入口 0x11720"
        gaps = ["+0xD..0xF 这三格回源没给消费端，不硬答"]
    for start, size, key in layout:
        chunk = " ".join(f"{x:02X}" for x in b[start:start + size])
        print(f"  {key.split(':', 1)[1]:>8}  {chunk:<12} → {fields[key]['meaning']}")
    for g in gaps:
        print(f"  {'':>8}  {g}")
    print("-" * 78)

    def describe(dom_name: str, val: int) -> str:
        _, v = match_value(DOMAINS[dom_name], str(val))
        return say(v, "这个编号缓存里没登记，不硬答（回源 §94.14）")

    print("这一行合起来在说什么（不看 GFX）：")
    print("  · dino 的一招是一张填好格子的 8 字节行、每格有固定名字；"
          "wof 这一行是一串没有名字的位置，取第几格算什么靠命中链决定")
    if side == "ours":
        print("  · 伤害不是一格定值：随机 long + 攻击力基值两段拼出来；"
              "具体加多少是量，按 §94.3 回源 tables.txt，不在这里评大小")
    else:
        print("  · 这一行不写伤害：+4..5 是难度索引增量，伤害另从 0x6EE84+d6 查表；"
              "所以敌→玩家这一侧的『疼不疼』不在这 16 字节里")
    print("  · 击退 / 特效写目标 +0x72，事件音效 word 投进事件记录；"
          "这些是逐招挑的量，不是规则")
    react, lethal, shake = b[reaction_at], b[lethal_at], b[shake_at]
    print(f"  · 平时反应 0x{react:02X} → {reaction_label}：{describe(reaction_dom, react)}")
    print(f"  · 致死时改用 0x{lethal:02X} → {describe(reaction_dom, lethal)}")
    print("    两个都是第一张门票，后面还隔着按入口选受击手册、状态档位、按 ObjId 的动画 / 碎尸链；")
    print("    民间资料把这一列直接读成『烧死 / 全碎』这类死法名，"
          "按 §94.14 三方对账只核到两角，未验命名不固化")
    _, sv = match_value(DOMAINS["wof_shake_left"], str(shake))
    print(f"  · shake 0x{shake:02X} → "
          f"{say(sv, '取值未登记，按非零态每帧 -1 跳过本帧')}")
    print("-" * 78)
    print("边界：同一行在 0x7FF2（我方→敌）/ 0x8228·0x8726（敌→玩家）/ 0x8D00（敌→场地对象）")
    print("      三条命中链里取第几格、算什么各不相同；这里只按所选布局读，")
    print("      0x8D00 还会跳过整段反应分派、直接绝对寻址取 +0xB 当双方 +0x62 的生命周期。")
    print("      按 §11.0 不串等价、不评优劣、不推断原机缺什么；看不到 GFX 就不猜造型。")
    return 0


def cmd_chain():
    print("ANI → SPR → 判定框：不靠 GFX 能推断到哪一步")
    print("=" * 78)
    print("""
ANI（帧记录 / 动画表）        SPR（composition）              判定框（HitBoxBank）
  帧记录 10 或 12 字节      w0/w1 指向 comp 指针表         +$48 身体盒 / +$49 攻击盒
  ├ w0/w1  composition idx   ├ header: count/n/hattr/layout  └ 12 字节 = 6 × i16
  ├ +4 param_a (按状态)      ├ layout: 每块 (dx,dy)             zoff,zsize,xoff,xsize,yoff,ysize
  ├ +5 param_b (相位)        ├ 每块 code -> 图块编号
  ├ +6 kind   ← 帧类型       └ attr: 调色板 / 翻转 / 块尺寸
  ├ +7 时长 + 末帧标志
  └ +8/+9 盒索引 ──────────────────────────────────────────────┘

【能推断，且不需要看到图】
  1. 这一帧是什么身份      kind：攻击生效 / 受击 / 倒地 / 抓 / 被抓 / 中立
  2. 这一拍多长            +7 低 7 位；0 = 256 tick
  3. 打完往哪走            +7 bit7 后的 link word：回环还是接下一招
  4. 打哪儿、够多远        xoff/xsize = 前伸量与宽度；yoff/ysize = 打的高度段
  5. 纵深容差              zoff/zsize = 攻击者与防守者 Z 差多少还能连上
  6. 自己会不会被打        body_box == 0 即这一帧不可被命中
  7. 是否多部件、有位移     w0 bit15 复合帧 + 各部件独立 dx/dy

【实测例子（re/specs/anim/SPEC.md §4.1，Jack）】
  身体盒 0x1A = (1, 6, -12, 23, 0, 75)
  刺拳盒 0x02 = (-1, 10, -68, 59, 29, 42)
  → X 从 -68 到 -9：向面朝方向前伸约 59 像素，是一记探身短拳而非贴身撞
  → Y 从 29 到 71：打的是站立对手的中上段，够不到贴地的倒地目标
  → Z 从 -1 到 9：纵深容差很小（SPEC 明写 Z 差在 -8..+8 才连得上）
  → 身体盒 Y 0..75 覆盖全身：出拳的同时自己整个可被打，攻防同帧成立
  这四条全是数字能说出来的，GFX 一个像素都不用看。
  现在也不必手算：`lookup.py box -1 10 -68 59 29 42` 会直接吐出三个区间与判定条件。
  也不必手敲那六个 i16：帧记录读出 attack_box = 0x02 后，
  `lookup.py jack_box_example 2` 直接给出「前伸 59 像素、打中上段、纵深 -8..+8」。
  前提写清楚：这是 SPEC 明写的 Jack 示例盒，别的角色盒表不同，不能套。

【打中之后会怎样，也在这层数据里】
  帧记录不带伤害。状态代码把 obj+$58 设成偶数，指向一条 8 字节 AttackRecord：
  `lookup.py attack 0A 01 00 09 03 14 00 00` 把八个字段合成一句人话，
  并认出这是 Jack 连段的第几拳。三拳 10/15/29 伤害、9/9/13 顿帧、反应 0/2/6 ——
  「连段是打出来的」不是手感形容词，是三行逐招数据写好的代价递进。
  `lookup.py attack` 还会把反应门票在玩家侧 / 敌人侧两本册子里并排翻出来，
  不用另跑命令，也不会把两边读混。
  再往下一环也接上了：门票翻完之后，`attack` 自己就会说出「接着播受击动画的
  第几段」，以及倒地后躺多久、搓招能不能提前起来、什么时候进眩晕；
  `lookup.py player_hurt_anim <段号>` 可以按段号反查哪些反应会播它。
  段编号是代码调用号、四个角色通用；那一段长什么样仍是 Jack 的美术推断，不混。
  两侧都能再往下一环，但走的不是同一套：玩家侧是通用的 set2 段号，
  敌人侧是「按兵种 e.w84 查 L[0x2E68C + e.w84] 之后」的姿态槽
  （`lookup.py enemy_hurt_anim`），所以解码输出把两条下游各自紧跟
  自己那本册子，别串成一条链。
  所以 ANI -> SPR -> 判定框 -> 这一拳的后果 -> 挨打的人怎么演，
  五个环节都能不靠 GFX 读出来，但最后一环两侧各讲各的。

【看不到 GFX 就不能说的】
  code 只是图块编号；没有 gfx.npy 就不知道画的是拳头、刀光还是衣服褶皱，
  也不知道色板实际长相。造型、美观、动画流畅度不属于这层数据。
  但 layout 的 dx/dy 分布与帧间 code 变化，仍能粗略读出『身体在移动 / 肢体在伸展』。

【为什么这层要缓存】
  上面每个数字单独看都只是数；串成链才回答『这一帧在干嘛』。
  而这些数字的意义散在 SPEC §1/§2/§3/§4、notes/03-frame.md §49 等多处，
  且「0」在 dino 是关盒、在 wof 是合法表项 —— 不先查语义就会把打击判读反。
  同理，受击编号 0x1A 在玩家侧是『背后轻击』、在敌人侧是『起身 / 眩晕』，
  编号本身不说话，先得知道是谁在读。

上面是说明版。真拿到一段帧记录时不必自己拼几条命令：
  `lookup.py moment 10 0A01 8000 0100 0405 1A02 attack 0A 01 00 09 03 14 00 00`
把身份 / 空间 / 后果合起来说，还会拦住「把攻击记录挂到非攻击帧上」这种错配；
再接一段 `comp <bytes...>`，SPR 那一环的零件数与摆位也并排进来，
画面和判定是两层数据就看得见了。
""")
    return 0


def cmd_moment(tokens: list[str]):
    """把同一帧的帧记录 + 可选攻击记录一次喂进来，合出「这一帧在干嘛」。

    chain 是串链的说明版，这里是可跑版；还多一层 chain 讲不了的判断：
    攻击记录不是任何时候都能往这一帧上挂，得先看帧类型与攻击盒。
    """
    usage = (
        "用法：moment [10|12] <帧记录 hex...> [attack <8 bytes...>] [comp <bytes...>]\n"
        "      例：moment 10 0A01 8000 0100 0405 1A02\n"
        "          moment 10 0A01 8000 0100 0405 1A02 attack 0A 01 00 09 03 14 00 00\n"
        "          moment 10 0A01 8000 0100 0405 1A02 comp 0002 0002 0005 0003 0802 0803\n"
        "      attack 与 comp 可按任意顺序接在帧记录后面；不带就不解那一环。\n"
        "      帧记录给身份 / 一拍多长 / 盒索引；comp 给这一帧由几块图拼成、贴在哪；\n"
        "      attack 给打中之后的后果。"
    )
    if not tokens:
        print(usage)
        return 1
    sections: dict[str, list[str]] = {"frame": []}
    cur = "frame"
    for t in tokens:
        if t in ("attack", "comp"):
            cur = t
            sections.setdefault(cur, [])
        else:
            sections.setdefault(cur, []).append(t)
    frame_tokens = sections.get("frame", [])
    atk_tokens = sections.get("attack", [])
    comp_tokens = sections.get("comp", [])
    stride = None
    if frame_tokens and frame_tokens[0] in ("10", "12"):
        stride = int(frame_tokens[0])
        frame_tokens = frame_tokens[1:]
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in frame_tokens)
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"帧记录十六进制读不出：{e}")
        return 1
    if stride is None:
        stride = 12 if len(b) == 12 else 10
    if len(b) < 10 or (stride == 12 and len(b) < 12):
        print(f"帧记录字节不够：拿到 {len(b)}，{stride} 字节格式需要 {stride}")
        return 1
    b = b[:stride]
    rec = None
    if atk_tokens:
        araw = "".join(t.replace("0x", "").replace(" ", "") for t in atk_tokens)
        try:
            ab = bytes.fromhex(araw)
        except ValueError as e:
            print(f"攻击记录十六进制读不出：{e}")
            return 1
        if len(ab) < 8:
            print(f"攻击记录字节不够：拿到 {len(ab)}，需要 8")
            return 1
        rec = ab[:8]
    comp_bytes = None
    if comp_tokens:
        craw = "".join(t.replace("0x", "").replace(" ", "") for t in comp_tokens)
        try:
            cb = bytes.fromhex(craw)
        except ValueError as e:
            print(f"composition 十六进制读不出：{e}")
            return 1
        if len(cb) < 8:
            print(f"composition 字节不够：拿到 {len(cb)}，光头就要 8 字节")
            return 1
        comp_bytes = cb

    w0, w1 = u16(b, 0), u16(b, 2)
    kind, timer, body, atk = b[6], b[7], b[8], b[9]
    dur, last = timer & 0x7F, bool(timer & 0x80)
    _, fv = match_value(DOMAINS["frame_type"], str(kind))
    # 按 frame_type 域：4 攻击生效、6 特殊 / 必杀，只有这两类自带伤害攻击盒。
    # 0 / 2 的 +$49 是抓投探测，8 / 10 / 12 / 14 根本不发起攻击。
    attack_kinds, grab_kinds = ATTACK_KINDS, GRAB_KINDS
    live = kind in attack_kinds and atk != 0

    print("这一帧合起来在干嘛（帧记录 + SPR 指向 + 判定框 + 后果，一次喂进去）")
    print("=" * 78)
    print(f"帧记录 {stride} 字节：{' '.join(f'{x:02X}' for x in b)}")
    print("-" * 78)
    print(f"1) 身份 / 这一拍：{say(fv, '帧类型未登记，不猜')}；"
          f"时长 {256 if dur == 0 else dur} tick，"
          + ("末帧，后面接一记 link word 决定回环还是接下一招" if last else "顺序走到下一帧"))
    print("2) SPR 环：composition 只管画成什么样，不参与打不打得中")
    if comp_bytes is not None:
        for line in comp_brief(comp_bytes):
            print("   " + line)
        print(f"   w0=0x{w0:04X} 指向它；下面第 3 环的盒区间跟这些零件 / 摆位不是一层数据")
    else:
        print(f"   w0=0x{w0:04X} 指向 composition（几块图、各自贴哪、翻转与调色板）")
        print("   想把这一环也喂进来：在帧记录后接 `comp <bytes...>`")
    if w0 & 0x8000:
        print("   w0 bit15=1：复合帧，w1 是部件表的自相对偏移，不是叠加层")
    elif w1 & 0x8000:
        print("   w1 bit15=1：这一帧没有叠加层")
    else:
        print(f"   w1=0x{w1:04X} 是第二组 composition 索引，画在主体之后 / 下方")
    print("3) 判定框环：能不能打中由 +$49 攻击盒与 +$48 身体盒决定，跟画面不是一层数据")
    for label, idx in (("攻击盒", atk), ("身体盒", body)):
        if idx == 0:
            print(f"   {label} 关盒（dino 里 0 就是关；wof 里 0 是合法表项，别串）")
            continue
        _, bv = match_value(DOMAINS["jack_box_example"], str(idx))
        if bv:
            print(f"   {label} #0x{idx:02X} 若属 Jack：{say(bv)}")
        else:
            print(f"   {label} #0x{idx:02X}：索引有效，但本机只登记 Jack 示例盒；"
                  "别的角色 / 敌人按自己的盒表取同一索引，形状不同，不套")
    print("   前提：Jack 示例盒只见于 re/specs/anim/SPEC.md §4.1，不是通用规则")
    print("4) 后果 / 合起来才看得出的那条：")
    if rec is not None and not live:
        if kind in grab_kinds:
            why = ("这一帧的 +$49 是抓投探测盒，命中后双方进的是『抓住 / 被抓』，"
                   "不走扣血那条链")
        elif kind in (8, 10, 12, 14):
            why = "这一帧是受击 / 倒地 / 抓姿势，命中循环本就跳过它，没有发起攻击这一说"
        elif kind in SPECIAL_KINDS:
            why = ("这一帧登记为特殊 / 必杀帧 [I 推断]；SPEC §4.4 的普通命中循环"
                   "只认攻方 +$2E == 4，是否另有必杀结算路径缓存没登记，"
                   "别当成已证实的第二次普通命中")
        elif kind in attack_kinds and atk == 0:
            why = "帧类型是攻击帧，但攻击盒关着，打不着人"
        else:
            why = "帧类型没登记成攻击生效帧"
        if kind in SPECIAL_KINDS:
            print(f"   注意：这一帧是特殊 / 必杀帧（kind=6，[I 推断]），不按普通命中循环结算：{why}")
            print("   AttackRecord 别在这一拍按普通命中结算，别把两份数据硬接成同一帧。")
        else:
            print(f"   注意：喂了攻击记录，但这一帧不是能结算伤害的攻击帧（kind={kind}）：{why}")
            print("   AttackRecord 不该在这一拍结算，别把两份数据硬接成同一帧。")
        print("   帧记录不写伤害；+$58 指到哪条 AttackRecord，是状态代码按招式挂上去的，"
              "什么时候挂、挂给谁，不归这 10/12 字节管")
    elif rec is not None and live:
        dmg, stun, react, stop = rec[0], rec[1], rec[2], rec[3]
        print(f"   这一帧能打人，攻击记录也挂上了：扣 {dmg} 血、削 {stun} 点韧性、"
              f"双方顿 {stop} 帧、反应 {react} 只是挨打者的第一张门票")
        print("   同一个反应编号，玩家挨打 / 敌人挨打各读一本册子：")
        for line in reaction_brief(react):
            print("   " + line)
        print("   两本都是 dino 侧，别把 wof 的反应编号直接对上。")
        print("   「够得着谁」写在盒表里，「打中之后多疼」写在另一条 8 字节里；"
              "两本册子要同一拍才对上，没有哪个数自己说出整拳")
        for k, v in DOMAINS["jack_attack_record"]["values"].items():
            if v.get("bytes", "").lower() == rec.hex():
                print(f"   对照 Jack 连段：这条是 $58 = {k}，{say(v)}")
                break
    elif rec is None and live:
        print("   这一帧能打人，但打中之后扣多少血不在这 10/12 字节里；"
              "帧记录不带伤害，+$58 指到 AttackRecord 才补上后果")
        print("   要接后果再喂 `attack <8 bytes>`（或 `anim_id 1 4` 按编号带出）")
    elif kind in SPECIAL_KINDS:
        print("   这一帧是特殊 / 必杀帧 [I 推断]：普通命中循环只认攻方 4，"
              "是否另走必杀结算路径缓存没登记，`attack` 别按普通命中往这一帧套")
    else:
        print("   这一帧关盒 / 不是攻击生效帧，谈不上打中；"
              "`box` 与 `attack` 都不该往这一帧上套")
    if live and body != 0 and atk != 0:
        print("   还有一条只有并排看才成立：两个盒同时非空，能打人的这一帧自己仍可被反击——"
              "攻防同帧，不另起一个无敌开关")
    if comp_bytes is not None:
        print("   三环并排才看得出的那条：零件怎么摆归 composition，够得着谁归判定框，"
              "打中多疼归攻击记录 —— 判定不跟着画面走，也没有谁替全场把整拳写死")
    print("-" * 78)
    print("看不到 GFX 仍能知道：身份、这一拍多长、打哪儿够多远、这一拳多疼、"
          "自己会不会被打、打完往哪走")
    print("看不到 GFX 无法知道：这一帧画的是拳头还是刀光、色板长相 —— 那归 composition/code")
    print("chain 是这一串的说明版，moment 是喂数据的可跑版。"
          "wof 半边不是 8 字节 AttackRecord，用 `wof_attack <ours|enemy> <16 bytes>`")
    return 0


def comp_brief(b: bytes) -> list[str]:
    """只挑 composition 里跟「这一帧怎么摆」有关的几个数，供 moment 合成用。

    逐 entry 的完整解码是 cmd_comp 的活；这里不复述图块编号，
    因为 code 没有 GFX 就说不出画的是什么。
    """
    hattr, n, layout_idx = u16(b, 4), u16(b, 2), u16(b, 6)
    alt = bool(hattr & 0x8000)
    need = 8 + n * (4 if alt else 2)
    out = [f"喂进来的 composition：{n} 块零件、"
           + ("alt 格式（每块自带 attr、允许块精灵）"
              if alt else f"normal 格式（全帧共用 attr、都是 1×1 图块、调色板 low5={hattr & 0x1F}）")
           + f"、layout 索引 0x{layout_idx:04X}"]
    if n == 0 or len(b) < need:
        out.append("entry 没读全，编号与摆位都别硬猜（完整口径见 `comp <bytes...>`）")
        return out
    if len(b) >= need + 4 * n:
        dx, dy = s16(b, need), s16(b, need + 2)
        out.append(f"接了 layout：第一块摆在 dx={dx}、dy={dy}，其余按 n×4 顺排；"
                   "同一批零件换一组摆位就是另一帧，不用重画人")
    else:
        out.append("没接 layout：知道有几块、各自什么编号，但不知道每块贴在哪")
    out.append("entry 按头 → 脚排，涉水时从末尾藏掉脚 / 腿；"
               "code 只是图块编号，没有 GFX 就不知道画的是拳头还是刀光")
    return out


def parse_i16(t: str) -> int:
    """判定盒字段是有符号 16 位：支持 -12 / 0xFFF4 / 1A 这类写法。"""
    t = t.strip()
    neg = t.startswith("-")
    if neg:
        t = t[1:]
    if t.lower().startswith("0x") or any(c in "abcdefABCDEF" for c in t):
        n = int(t, 16)
    else:
        n = int(t, 10)
    return -n if neg else n


def cmd_box(tokens: list[str]):
    """把判定盒的 6 个 i16 翻成『这一下打哪儿、够多远、纵深容差多大』。"""
    if len(tokens) != 6:
        print("用法：box <zoff> <zsize> <xoff> <xsize> <yoff> <ysize>   "
              "例：box -1 10 -68 59 29 42")
        return 1
    try:
        zoff, zsize, xoff, xsize, yoff, ysize = (parse_i16(t) for t in tokens)
    except ValueError as e:
        print(f"读不出数值：{e}")
        return 1
    bf = DOMAINS["box_field"]["values"]
    pairs = [("+0", zoff), ("+2", zsize), ("+4", xoff),
             ("+6", xsize), ("+8", yoff), ("+10", ysize)]
    print(f"判定盒 6 × i16：({', '.join(str(v) for _, v in pairs)})")
    print(f"  src={DOMAINS['box_field']['source']}")
    print("-" * 78)
    for k, v in pairs:
        print(f"  {k:4s} = {v:7d}  {bf[k]['meaning']} {fmt(bf[k]['tag'])}")
    print("-" * 78)
    print("这一下的形状（只靠六个数，不看 GFX）：")
    print(f"  X 区间 [{xoff}, {xoff + xsize}]：宽度 {xsize}；"
          f"xoff={xoff} 表示盒子相对身体原点探出多远（朝右时整体镜像）")
    print(f"  Y 区间 [{yoff}, {yoff + ysize}]：高度段 {ysize}；"
          "对照防守方身体盒的 Y 区间，才知道够不够得着倒地 / 腾空目标")
    print(f"  Z 区间 [{zoff}, {zoff + zsize}]：纵深容差 {zsize}；"
          "攻守双方 Z 差落不进这个区间就打不着")
    print("  成立条件：+$49 攻击盒与 +$48 身体盒都非空，且两个矩形相交；"
          "有身体盒的一帧自己仍可被反击，攻防同帧成立")
    return 0


def cmd_anim(tokens: list[str]):
    """把一串连续帧记录翻成一段动画时间线（ANI 通常不止一帧）。"""
    stride = 10
    if tokens and tokens[0] in ("10", "12"):
        stride = int(tokens[0])
        tokens = tokens[1:]
    if not tokens:
        print("用法：anim [10|12] <hex bytes...>   例：anim 10 0A01 8000 0100 0405 1A02 ...")
        return 1
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in tokens)
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"十六进制读不出：{e}")
        return 1
    if len(b) < stride:
        print(f"字节不够：拿到 {len(b)}，一帧需要 {stride}")
        return 1
    print(f"ANI 段：{len(b)} 字节，按 {stride} 字节/帧切分")
    print("=" * 78)
    total, seen_last, identities = 0, False, []
    live_normal = special_frames = closed_attack = 0
    for i, off in enumerate(range(0, len(b) - stride + 1, stride)):
        rec = b[off:off + stride]
        kind, timer = rec[6], rec[7]
        dur, last = (timer & 0x7F) or 256, bool(timer & 0x80)
        body, atk = rec[8], rec[9]
        _, fv = match_value(DOMAINS["frame_type"], str(kind))
        label = fv["meaning"] if fv else "未登记"
        identities.append(label.split("：")[0].split("；")[0])
        total += dur
        mark = ""
        if kind in ATTACK_KINDS:
            if not atk:
                closed_attack += 1
                mark = "   → 攻击帧但攻击盒关着，这一帧打不着人"
            else:
                live_normal += 1
                mark = "   → 攻击生效"
        elif kind in SPECIAL_KINDS:
            special_frames += 1
            mark = ("   → 特殊 / 必杀帧 [I 推断]：普通命中循环只认攻方 4，"
                    "不并入生效帧")
        print(f"  帧 {i:02d} @+{off:04X}  kind=0x{kind:02X}  {label} {fmt(fv['tag']) if fv else ''}")
        print(f"       {dur:3d} tick   body_box={body:#04x}  attack_box={atk:#04x}"
              + ("   [末帧]" if last else "") + mark)
        if last:
            seen_last = True
            print("       末帧后紧跟的 i16 是 link word（不是帧记录），切分到此为止")
            break
    print("=" * 78)
    print(f"  这一段共 {total} tick；身份序列：{' → '.join(identities)}")
    print(f"  攻击生效帧 {live_normal} 个（kind 4 且攻击盒非 0）——"
          "只有这些帧让 +$49 与对方 +$48 相交结算命中")
    if special_frames:
        print(f"  另有 {special_frames} 个特殊 / 必杀帧 [I 推断]："
              "SPEC §4.4 的命中循环只认攻方 +$2E == 4，这些帧单列、"
              "不算普通攻击生效；是否另走必杀结算路径缓存没登记")
    if closed_attack:
        print(f"  另有 {closed_attack} 个攻击帧把攻击盒关着：打不着人，"
              "属于收势 / 过渡，不算生效帧")
    print("  其余帧是起势、受击、倒地、抓投姿势或被抓，不发起攻击结算")
    print("  段落" + ("在末帧结束，去向写在 link word 里（回环 / 接下一招）" if seen_last
                   else "还没读到末帧，后面还有帧记录"))
    return 0


def s16(b: bytes, off: int) -> int:
    """layout 里的 dx/dy 是有符号 16 位。"""
    v = u16(b, off)
    return v - 0x10000 if v & 0x8000 else v


def describe_attr(n: int) -> str:
    """把 CPS1 OBJ attr 字翻成人话；位含义取自 sprite_attr 域的登记。"""
    p = n & 0x1F
    w = ((n >> 8) & 0xF) + 1
    h = ((n >> 12) & 0xF) + 1
    parts = [f"调色板 {p}"]
    if n & 0x20:
        parts.append("X 翻转")
    if n & 0x40:
        parts.append("Y 翻转")
    parts.append(f"块 {w}×{h} 个 16×16")
    return "；".join(parts)


def cmd_comp(tokens: list[str]):
    """把一串 SPR composition 字节翻成『这帧由几块零件拼成、贴在哪、什么形状』。"""
    if not tokens:
        print("用法：comp <hex bytes...>   composition 记录（8 字节头 + entries）")
        print("      后面若还接了 n×4 字节，就当 layout 的 (dx,dy) 摆位一起解")
        return 1
    raw = "".join(t.replace("0x", "").replace(" ", "") for t in tokens)
    try:
        b = bytes.fromhex(raw)
    except ValueError as e:
        print(f"十六进制读不出：{e}")
        return 1
    if len(b) < 8:
        print(f"字节不够：拿到 {len(b)}，composition 头就要 8 字节")
        return 1
    count, n, hattr, layout_idx = u16(b, 0), u16(b, 2), u16(b, 4), u16(b, 6)
    alt = bool(hattr & 0x8000)
    esize = 4 if alt else 2
    need = 8 + n * esize
    if n == 0 or len(b) < need:
        print(f"entry 读不全：n={n}、{'alt' if alt else 'normal'} 格式要 {need} 字节，实际 {len(b)}")
        return 1

    print(f"SPR composition：{len(b)} 字节，{n} 个 entry")
    print("=" * 78)
    print(f"  +0 count  = 0x{count:04X}  总 16×16 硬件图块数（各 entry 的 块宽×块高 之和）；"
          "只喂调试用的 sprite-usage 计数，不参与绘制")
    print(f"  +2 n      = {n}      这一帧由几块零件拼成（SPEC 里 1..55）")
    _, cv = match_value(DOMAINS["comp_format"], "1" if alt else "0")
    print(f"  +4 hattr  = 0x{hattr:04X}  → {cv['meaning']} {fmt(cv['tag'])}")
    print(f"            low5 = {hattr & 0x1F}  " +
          ("（alt 格式这一格只占位，调色板逐 entry 自带）" if alt
           else "（normal 格式：这一格就是全帧共用的调色板）"))
    print(f"  +6 layout = 0x{layout_idx:04X}  layout 索引（不是字节偏移），指向 n×(dx,dy) 摆位表；"
          "同一组摆位可被多帧共享")
    print("-" * 78)

    entries = []
    for i in range(n):
        off = 8 + i * esize
        code = u16(b, off)
        attr = u16(b, off + 2) if alt else hattr
        entries.append((code, attr))
        print(f"  entry #{i:02d}  code=0x{code:04X}  attr=0x{attr:04X}  → {describe_attr(attr)}")

    has_layout = len(b) >= need + 4 * n
    print("-" * 78)
    if has_layout:
        for i in range(n):
            off = need + i * 4
            dx, dy = s16(b, off), s16(b, off + 2)
            print(f"  entry #{i:02d}  dx={dx:6d}  dy={dy:6d}  "
                  "→ 相对对象原点（X、脚底）的左上偏移；朝右时整体镜像")
    else:
        print(f"  （没接 layout 字节：还差 {4 * n} 字节才能知道每块贴在哪；"
              "把 layout 的 n×4 字节接在 composition 后面一起喂）")

    print("=" * 78)
    print("这一帧的形状（只靠数字，不看 GFX）：")
    print(f"  · 由 {n} 块零件拼成；数据里第一块最先发出 = 优先级最高，画在最上层")
    print("  · entry 按头 → 脚排：涉水时按 +$4C / +$4D 从末尾藏掉脚 / 腿，"
          "附带的 4 字节查 `lookup.py comp_extra`")
    print("  · " + ("alt 格式：每块自带 attr，允许块精灵（一块占多个 16×16 图块）"
                    if alt else "normal 格式：全帧共用同一个 attr，且都是 1×1 图块"))
    print("  · layout 与 composition 分开存：同一批零件换一组摆位就是另一帧，"
          "不用重画人 —— 动作改的是摆位和编号，不是整张图")
    print("  · 朝右（facing != 0）时整体镜像，盒的 X 区间也跟着翻")
    print("\n  看不到 GFX 不能说：code 只是图块编号，不知道这块是拳头、刀光还是衣褶，"
          "也不知道色板实际长相")
    print("  衔接：`frame` 的 +0/+2 指到这里；判定形状交给 `box`；"
          "整段身份用 `anim`；三层串起来就是 `chain` 讲的那条线")
    return 0


def cmd_anim_id(tokens: list[str]):
    """按「套号 + 段号」查 Jack 的动画编号是哪一招（ANI 表 u16 offset[id] 的 id）。"""
    if len(tokens) != 2:
        print("用法：anim_id <set 0..5> <id>   例：anim_id 1 4")
        return 1
    set_n, _ = parse_value(tokens[0])
    if set_n is None or set_n not in range(6):
        print(f"套号读不出或超出 0..5：{tokens[0]}")
        return 1
    set_v = DOMAINS["anim_set"]["values"].get(str(set_n))
    print(f"Jack 动画 set {set_n} / id {tokens[1]}")
    if set_v:
        print(f"  这一套：{set_v['meaning']} {fmt(set_v['tag'])}")
    dname = SET_DOMAINS.get(set_n)
    if not dname:
        print("  这一套 SPEC 只给了套级用途，没有逐段编号表 —— 不猜。")
        return 0
    d = DOMAINS[dname]
    if tokens[1] in d["values"]:
        k, v = tokens[1], d["values"][tokens[1]]
    else:
        k, v = match_value(d, tokens[1])
    if v is None:
        print(f"  {dname}.{tokens[1]}：未登记。这套已有的编号：{', '.join(d['values'])}")
        print("  （不猜：没有出处的意义请标 U 并补 source 后再加进 semantics.json）")
        return 2
    emit(dname, k, v, False)
    if set_n == 1:
        print("  对齐查：attack_id（$58）/ player_ground_state（状态字）/ combo_counter（+$B2）")
        m = re.search(r"\$58\s*=\s*(\d+)", v["meaning"])
        if m:
            a = m.group(1)
            _, av = match_value(DOMAINS["attack_id"], a)
            _, rv = match_value(DOMAINS["jack_attack_record"], a)
            print(f"  ── 这一拳的后果（$58 = {a}，不用再拼命令）──")
            if av:
                print(f"  攻击编号表里 $58 = {a} 是：{say(av)}")
            if rv:
                hx = " ".join(rv["bytes"][i:i + 2] for i in range(0, 16, 2))
                print(f"  攻击属性记录 8 字节：{hx}")
                print(f"  {say(rv)}")
                print(f"  逐字段看后果：lookup.py attack {rv['bytes']}")
            else:
                print(f"  $58 = {a} 的逐字节攻击属性记录在 ROM 表里，本机不登记，"
                      "不替它猜数值（招名仍查 attack_id）。")
        else:
            print("  这一段没写 $58，是同一招的伸臂 / 命中变体；攻击记录随主招，"
                  "别把变体当成新的一招另配一份数值。")
    return 0


def cmd_find(word: str):
    print(f"在意义 / 备注里搜「{word}」：")
    hit = 0
    for name, d in DOMAINS.items():
        for k, v in d["values"].items():
            blob = v["meaning"] + " " + v.get("note", "") + " " + v.get("alias", "")
            if word in blob or word in d.get("label", "") + d.get("note", ""):
                print(f"  {name}.{k:14s} {fmt(v['tag'])} {v['meaning']}")
                hit += 1
    print(f"（{hit} 条；src 见各自域）" if hit else "（无命中）")
    return 0


def cmd_coverage():
    """列出哪些成表已转成可查语义，以及哪些按纪律不转、为什么。"""
    cov = DB.get("coverage", {})
    print("表数值 → 抽象意义：覆盖索引")
    print("=" * 78)
    print(cov.get("note", ""))
    print("\n已登记（按回源分组）：")
    for grp in cov.get("registered", []):
        print(f"  {grp['source']}")
        print(f"    {', '.join(grp['domains'])}")
    print("\n按纪律没转的：")
    for item in cov.get("not_registered", []):
        print(f"  · {item['what']}")
        print(f"    └ {item['why']}")
    listed = {x for g in cov.get("registered", []) for x in g["domains"]}
    missing = sorted(set(DOMAINS) - listed)
    stale = sorted(listed - set(DOMAINS))
    total = sum(len(d["values"]) for d in DOMAINS.values())
    print(f"\n合计 {len(DOMAINS)} 个域 / {total} 条；"
          f"索引缺 {len(missing)} 个域、多 {len(stale)} 个域。")
    if missing:
        print("  缺（新增域忘了登记来源）：" + ", ".join(missing))
    if stale:
        print("  多（缓存里已删）：" + ", ".join(stale))
    sides = {"dino": 0, "wof": 0, "both": 0}
    for d in DOMAINS.values():
        s = d.get("scope", "dino")
        key = "both" if s == "both" else ("wof" if s.startswith("wof") else "dino")
        sides[key] += 1
    print(f"\n按游戏侧：dino {sides['dino']} / wof {sides['wof']} / "
          f"两侧共用 {sides['both']} 个域。")
    print("  这是证据边界，不是「哪边设计更简单」：wof 侧 C# 移植欠账见 notes/08，"
          "原机多张表按上面 not_registered 的理由不转；别据此评优劣，"
          "也别推断 wof 原机缺机制。")
    return 0


def unknown_rows() -> dict:
    """把标 [U] 的取值按域收起来，供 unknown 命令与自测共用。"""
    out = {}
    for name, d in DOMAINS.items():
        us = [(k, v) for k, v in d["values"].items() if v["tag"] == "U"]
        if us:
            out[name] = (d, us)
    return out


def cmd_unknown(tokens: list[str]):
    """一次列出「这份缓存还答不了什么」：域内 [U] 取值 + 按纪律整类不转的表。

    两者都只是「没写意义」，不是「不存在」。给一个域名就只看那一册，
    方便分析某张状态表时先看清哪些编号还没弄明白。
    """
    cov = DB.get("coverage", {})
    groups = unknown_rows()
    if tokens:
        key = tokens[0]
        if key not in DOMAINS:
            print(f"没有这个域：{key}。用 `lookup.py list` 看全部可查的域，"
                  "或用 `lookup.py unknown` 看整体缺口视图。")
            return 1
        print(f"{key} 里还没弄明白的取值（{len(groups.get(key, (None, []))[1])} 条）")
        print("=" * 78)
        print(f"出处：{DOMAINS[key]['source']}")
        if DOMAINS[key].get("context_dependent"):
            print(f"注意（上下文相关）：{DOMAINS[key].get('note', '')}")
        for k, v in groups.get(key, (None, []))[1]:
            print(f"  {k:14s} {fmt(v['tag'])} {v['meaning']}")
            if v.get("note"):
                print(f"  {'':14s} 备注：{v['note']}")
            if v.get("blocked_at"):
                print(f"  {'':14s} 回源止于：{v['blocked_at']}")
        if key not in groups:
            print("  这个域没有 [U] 取值；但不代表整类都清楚了，")
            print("  整类按纪律不转的理由看 `lookup.py coverage`。")
        print("\n未登记 ≠ 不存在：查不到的取值只是没写意义，不代表游戏里没有；")
        print("别顺着字段名猜，也别把它当成关掉 / 空值。")
        print("『回源止于』写的是取证走到哪一行、为什么停，不是漏查，也不是猜测。")
        return 0

    total = sum(len(us) for _, us in groups.values())
    print("这份缓存还答不了什么（未登记 ≠ 不存在）")
    print("=" * 78)
    print(cov.get("unknown_note", ""))
    print(f"\n一、取值在册、但具体意义没弄明白（标 [U]，共 {total} 条 / {len(groups)} 个域）")
    for name, (d, us) in groups.items():
        print(f"  {name}   （{d['source']}）")
        for k, v in us:
            print(f"    {k:14s} {fmt(v['tag'])} {v['meaning']}")
            if v.get("blocked_at"):
                print(f"    {'':14s} 回源止于：{v['blocked_at']}")
    print("\n  这些编号确实存在、游戏确实在读，只是我们只知道它大概属于哪一类。")
    print("  别顺着字段名猜，也别把它当成关掉 / 空值；")
    print("  每条后面的『回源止于』是取证走到哪一行、为什么停，上游 SPEC 自己就标了 [U]。")
    nr = cov.get("not_registered", [])
    print(f"\n二、整类按纪律不转成域（{len(nr)} 类）")
    for item in nr:
        print(f"  · {item['what']}")
        print(f"    └ {item['why']}")
    print("\n  这不是漏查清单：理由逐条写在上面，完整回源分组见 `lookup.py coverage`。")
    print("\n查一个具体取值：先 `lookup.py <域> <取值>` 看是不是 [U]；")
    print("再 `lookup.py collide <取值>` 看它在别的册子里是不是已经有意义；")
    print("都没命中才回源 source。`lookup.py unknown <域>` 只看某一册还没弄明白的编号。")
    return 0


def tag_counts(dom: dict) -> dict:
    """一个域里观察 / 推断 / 未登记各几条，供主题索引按设计问题报成色。"""
    c = {"O": 0, "I": 0, "U": 0}
    for v in dom["values"].values():
        c[v["tag"]] = c.get(v["tag"], 0) + 1
    return c


def theme_agg(names: list[str]) -> dict:
    agg = {"O": 0, "I": 0, "U": 0}
    for n in names:
        c = tag_counts(DOMAINS[n])
        for k in agg:
            agg[k] += c[k]
    return agg


def cmd_themes(tokens: list[str]):
    """按玩法主题列出可查的域；与 coverage 的「按回源文件分组」正交。"""
    items = DB.get("themes", {}).get("list", [])
    if not items:
        print("缓存里没有主题索引")
        return 1
    if not tokens:
        print("按设计问题查缓存（与 coverage 的回源分组正交）")
        print("=" * 78)
        print(DB["themes"].get("note", ""))
        for t in items:
            agg = theme_agg(t["domains"])
            print(f"  {t['key']:20s} {t['label']}  ({len(t['domains'])} 个域；"
                  f"观察 {agg['O']} / 推断 {agg['I']} / 未登记 {agg['U']})")
            print(f"  {'':20s} {t['question']}")
        print("\n用 `lookup.py themes <主题>` 看这一块有哪些域、哪些还没弄明白；"
              "`lookup.py <域> [取值]` 查具体意义。")
        print("括号里的成色别跳过：标 [I 推断] 的不是观察事实，[U 未登记] 也不是「游戏里没有」。")
        return 0
    key = tokens[0]
    t = next((x for x in items if x["key"] == key), None)
    if not t:
        print(f"没有这个主题：{key}。可用：{', '.join(x['key'] for x in items)}")
        return 1
    print(f"{t['label']} — {t['question']}")
    print("-" * 78)
    for name in t["domains"]:
        d = DOMAINS.get(name)
        c = tag_counts(d) if d else {"O": 0, "I": 0, "U": 0}
        print(f"  {name:24s} {d['label'] if d else '（域不存在）'}")
        print(f"  {'':24s} 观察 {c['O']} / 推断 {c['I']} / 未登记 {c['U']}")
    agg = theme_agg(t["domains"])
    print(f"\n（{len(t['domains'])} 个域；合计 观察 {agg['O']} / 推断 {agg['I']} / 未登记 {agg['U']}）")
    unknowns = [n for n in t["domains"] if tag_counts(DOMAINS[n])["U"]]
    if unknowns:
        print("这一块还有没弄明白的编号（未登记 ≠ 不存在，别当成关掉 / 空值）：")
        for n in unknowns:
            print(f"  lookup.py unknown {n}")
    print("具体取值用 `lookup.py <域> [取值]` 查；标 [I 推断] 的不是观察事实。")
    return 0


def legacy_probes(item: dict) -> list[dict]:
    """probe 可以是单个样本，也可以挂多条；统一成列表，老数据不用改。"""
    p = item.get("probe")
    if isinstance(p, list):
        return p
    return [p] if p else []


def cmd_legacy(tokens: list[str]):
    """外推文九条判断 → 缓存里哪些域是它的数据底座，以及查不到什么。"""
    items = DB.get("legacy", {}).get("list", [])
    if not items:
        print("缓存里没有 legacy 索引")
        return 1
    if tokens:
        key = tokens[0]
        hit = [x for x in items if x["key"] == key]
        if not hit:
            print(f"没有这一条：{key}。可用的 key：{', '.join(x['key'] for x in items)}")
            return 2
        items = hit
    print("外推文九条判断 → 可查的数据底座")
    print("=" * 78)
    print(DB["legacy"]["note"])
    print("=" * 78)
    for x in items:
        print(f"\n{x['title']}   [{x['key']}]")
        print(f"  问的是：{x['question']}")
        print(f"  能查：{x['can_check']}")
        print(f"  查不到（别当证据）：{x['cannot_check']}")
        if x.get("source"):
            print(f"  另有 [O] 回源（结构观察与边界看这里）：{x['source']}")
        print(f"  可查域（{len(x['domains'])}）：{', '.join(x['domains'])}")
        print("    直接翻：" + " / ".join(f"lookup.py {d}" for d in x["domains"][:3]))
        for pr in legacy_probes(x):
            print(f"    可跑样本：lookup.py {' '.join(pr['argv'])}"
                  f"  → 输出里应有「{pr['expect']}」（--selftest 会真跑一次）")
    print("\n  这是证据底座盘点，不是又九条设计判断；"
          "右栏「当代同类常见做法」是外推观察，不占域。")
    used = {x for it in DB["legacy"]["list"] for x in it["domains"]}
    print(f"  {len(DOMAINS)} 个域里 {len(used)} 个挂了判断；未挂的不是漏查——"
          "覆盖全部域是 `lookup.py themes` 的事，这里只挂能回答该判断的域。")
    return 0


def cmd_collide(token: str):
    """只给一个取值，列出它在各域的所有意义 —— 确认「这个数得先知道谁在读」。"""
    print(f"取值「{token}」在已登记域里的所有意义：")
    print("=" * 78)
    hits, skipped = [], []
    for name, d in DOMAINS.items():
        if d.get("bitfield") or name in OFFSET_KEY_DOMAINS:
            skipped.append(name)
            continue
        k, v = match_value(d, token)
        if v:
            hits.append((name, k, v, d))
    for name, k, v, d in hits:
        ctx = " [上下文相关]" if d.get("context_dependent") else ""
        generic = "  (兜底/参数化键，不是这个值的专门登记)" \
            if k in ("nonzero", "other", "negative", "low7=n") else ""
        print(f"  {name:24s} -> {v['meaning']} {fmt(v['tag'])}{ctx}{generic}")
    if not hits:
        print("  （没有域登记这个取值）")
    print("=" * 78)
    ctx_n = sum(1 for _, _, _, d in hits if d.get("context_dependent"))
    exact_n = sum(1 for _, k, _, _ in hits
                  if k not in ("nonzero", "other", "negative", "low7=n"))
    print(f"命中 {len(hits)} 个域，其中 {exact_n} 个是这个值的专门登记、"
          f"{ctx_n} 个标注上下文相关。")
    print("这个数没有全局意义：先确定是哪张表 / 哪个对象在读，再谈它是什么。"
          "只带数字不带域，等于让工具替你猜。")
    if skipped:
        print(f"（已跳过 {len(skipped)} 个位域 / 字段偏移域：它们的数字是位号或字节偏移，"
              f"不是取值：{', '.join(skipped)}）")
    return 0


# ---------- 固化自测 ----------
def capture(fn, *args) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args)
    return buf.getvalue()


def capture_rc(fn, *args):
    """同 capture，但把命令的返回码也带回来，供全命令冒烟用。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*args)
    return buf.getvalue(), rc


def cmd_selftest():
    checks = []

    def ck(label, cond, detail=""):
        checks.append((label, bool(cond), detail))

    # 缓存自身的完整性：每条都得有出处与置信标签
    bad = []
    for name, d in DOMAINS.items():
        if not d.get("scope") or not d.get("source"):
            bad.append(f"{name} 缺 scope/source")
        for k, v in d["values"].items():
            if not v.get("meaning") or not v.get("tag") or v["tag"] not in ("O", "I", "U"):
                bad.append(f"{name}.{k} 缺 meaning/tag")
    ck("每个域都有 scope/source，每条都有 meaning/tag", not bad, "; ".join(bad))
    bad = [n for n, d in DOMAINS.items() if not d.get("label")]
    ck("每个域都有给人读的 label", not bad, ", ".join(bad))
    bad = [n for n, d in DOMAINS.items()
           if d.get("context_dependent") and not d.get("note")]
    ck("上下文相关域都带 note，讲清查之前要确认什么", not bad, ", ".join(bad))
    state_layers = ("player_mode", "player_ground_state",
                    "player_run_state", "player_air_state")
    ck("状态机四层都标了上下文相关，note 讲清先确认哪三层",
       all(DOMAINS[n].get("context_dependent") for n in state_layers)
       and all("查之前" in DOMAINS[n]["note"]
               for n in ("player_mode", "player_ground_state"))
       and "$06=0" in DOMAINS["player_ground_state"]["note"])
    out_pg = capture(cmd_lookup, "player_ground_state", "4", False)
    ck("查地面状态表会先提示确认档位，不让人把编号读成全局值",
       "注意（上下文相关）" in out_pg and "$06=0" in out_pg)
    out_c4 = capture(cmd_collide, "4")
    ck("反查同一个 4 时，地面状态表那行也标了上下文相关",
       any("player_ground_state" in l and "上下文相关" in l
           for l in out_c4.splitlines()))
    ck("unknown <上下文域> 也带上那条「先确认什么」",
       "注意（上下文相关）" in capture(cmd_unknown, ["player_ground_state"]))
    refs = []
    for src, group in (("legacy", DB["legacy"]["list"]),
                       ("themes", DB["themes"]["list"]),
                       ("coverage", DB["coverage"]["registered"])):
        for x in group:
            refs += [(src, n) for n in x.get("domains", [])]
    bad = [f"{s}:{n}" for s, n in refs if n not in DOMAINS]
    ck(f"三条索引引用的 {len(refs)} 处域名都真实存在", not bad, ", ".join(bad))
    bad = [str(i) for i, x in enumerate(DB["coverage"]["not_registered"])
           if not x.get("what") or not x.get("why")]
    ck("按纪律不转的每条都写了 what/why", not bad, ", ".join(bad))
    path_re = r"[A-Za-z0-9_./-]+\.(?:md|rs|py|txt)"
    repo_root = HERE.parent.parent
    src_strings = [(name, dom.get("source", "")) for name, dom in DOMAINS.items()]
    src_strings += [(f"coverage{i}", g.get("source", ""))
                    for i, g in enumerate(DB["coverage"]["registered"])]
    src_strings += [(f"not_registered{i}", x.get("source", ""))
                    for i, x in enumerate(DB["coverage"]["not_registered"])]
    src_strings += [("legacy." + x["key"], x.get("source", ""))
                    for x in DB["legacy"]["list"]]
    bad = [f"{tag}:{p}" for tag, s in src_strings
           for p in re.findall(path_re, s) if not (repo_root / p).exists()]
    ck("回源路径都从仓库根写全、且文件真实存在（不留裸文件名或裸前缀）",
       not bad, ", ".join(bad))
    bad_line = []
    for tag, s in src_strings:
        for m in re.finditer(path_re, s):
            f = repo_root / m.group(0)
            if not f.exists():
                continue
            lm = re.match(r":(\d+)(?:-(\d+))?", s[m.end():m.end() + 24])
            if not lm:
                continue
            nlines = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            hi = int(lm.group(2) or lm.group(1))
            if int(lm.group(1)) > nlines or hi > nlines:
                bad_line.append(f"{tag}:{m.group(0)}{lm.group(0)}(文件 {nlines} 行)")
    ck("带行号的回源引用没超出文件实际行数", not bad_line, ", ".join(bad_line))
    prose = [(f"notreg{i}.what", x.get("what", ""))
             for i, x in enumerate(DB["coverage"]["not_registered"])]
    prose += [(f"notreg{i}.why", x.get("why", ""))
              for i, x in enumerate(DB["coverage"]["not_registered"])]
    prose += [("legacy." + x["key"] + "." + field, x.get(field, ""))
              for x in DB["legacy"]["list"]
              for field in ("can_check", "cannot_check")]
    # 命令示例（lookup.py collide 4）与通配符（re/specs/*/HANDOFF.md）不是回源路径
    prose_skip = {"lookup.py", "/HANDOFF.md"}
    bad_prose = [f"{tag}:{p}" for tag, s in prose
                 for p in re.findall(path_re, s)
                 if p not in prose_skip and not (repo_root / p).exists()]
    ck("边界说明里提到的回源文件也写全（命令示例与通配符除外）",
       not bad_prose, ", ".join(bad_prose))
    sect_titles = set()
    for md in repo_root.rglob("*.md"):
        if ".git" in md.parts or "out" in md.parts:
            continue
        for line in md.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^#{1,6}\s+§?(\d+(?:\.\d+)?)\b", line.strip())
            if m:
                sect_titles.add(m.group(1))

    def all_strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from all_strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from all_strings(v)

    sect_refs = {m.group(1) for s in all_strings(DB)
                 for m in re.finditer(r"§(\d+(?:\.\d+)?)", s)}
    bad_sect = sorted(n for n in sect_refs if n not in sect_titles)
    ck("缓存引用的章节号也能在全库 md 里翻到对应标题",
       not bad_sect, ", ".join(bad_sect))
    ck("域数量 >= 57（wof 受击手册选择、玩家输入契约也进了缓存）",
       len(DOMAINS) >= 57, str(len(DOMAINS)))
    for dn in ("player_ground_state", "player_run_state", "player_air_state"):
        ck(f"状态表 {dn} 已登记", dn in DOMAINS)

    # 关键取值映射
    _, v = match_value(DOMAINS["wof_reaction"], "0x0E")
    ck("wof 0x0E → 碎尸族", bool(v) and "碎尸" in v["meaning"], v["meaning"] if v else "miss")
    ck("box_index_zero 两侧相反",
       "没有盒" in DOMAINS["box_index_zero"]["values"]["dino"]["meaning"]
       and "合法" in DOMAINS["box_index_zero"]["values"]["wof"]["meaning"])
    ck("frame_type 0 是 [I] 不是 [O]", DOMAINS["frame_type"]["values"]["0"]["tag"] == "I")

    # 裸十六进制与范围取值
    n, _ = parse_value("0A")
    ck("裸十六进制 0A 解析成 10", n == 10, str(n))
    _, v = match_value(DOMAINS["drop_code"], "25")
    ck("范围取值 drop_code 25 → 食物", bool(v) and "食物" in v["meaning"], v["meaning"] if v else "miss")
    _, v = match_value(DOMAINS["camera_mode"], "4")
    ck("camera_mode 4 → 战斗锁镜头", bool(v) and "锁镜头" in v["meaning"], v["meaning"] if v else "miss")
    _, v = match_value(DOMAINS["camera_lock"], "1")
    ck("相机锁 1 → 这一波打完前别往前走", bool(v) and "锁住" in v["meaning"])
    _, v = match_value(DOMAINS["camera_event"], "+B")
    ck("相机事件 +B → 切到哪种镜头模式", bool(v) and "camera mode" in v["meaning"])
    ck("相机事件记录标明 X=0xFFFF 是终止符", "0xFFFF" in DOMAINS["camera_event"]["note"])
    out = capture(cmd_collide, "1")
    ck("同一个 1 在镜头模式表与镜头锁表里意义不同",
       "camera_mode" in out and "camera_lock" in out
       and "区域结束" in out and "锁住" in out)
    ck("字段偏移域 camera_event 不参与按取值反查", "camera_event ->" not in out)
    ck("镜头锁与波次收尾能串成一条放行链",
       "enemy/SPEC.md §8.3" in DOMAINS["camera_lock"]["source"]
       and "GO" in DOMAINS["wave_end"]["values"]["0"]["meaning"]
       and "$7A9" in DOMAINS["wave_end"]["values"]["0"]["meaning"])
    ck("六份 SPEC 已正面核过的口径写进覆盖索引",
       "正面核过" in DB["coverage"]["note"] and "不是漏查" in DB["coverage"]["note"])
    ck("地面状态表的杂项编号拆成精确键，不再连成范围",
       "38-44" not in DOMAINS["player_ground_state"]["values"]
       and all(str(k) in DOMAINS["player_ground_state"]["values"] for k in (38, 40, 42, 44)))
    out = capture(cmd_collide, "39")
    ck("不存在的奇数状态编号不再被范围键误答", "player_ground_state ->" not in out)
    _, v = match_value(DOMAINS["dino_cmd_state"], "4")
    ck("dino 指令技 4 → t2 窗里等按住上+攻击", bool(v) and "t2" in v["meaning"])
    _, v = match_value(DOMAINS["wof_rkey1"], "0xFF")
    ck("wof RKey1 0xFF → 已确认倒计时", bool(v) and "倒计时" in v["meaning"])
    ck("指令技两域写明检测与执行分离 / 合一",
       "检测与执行分离" in DOMAINS["dino_cmd_state"]["note"]
       and "检测与执行合一" in DOMAINS["wof_rkey1"]["note"])
    ck("wof 脚本轨道按边界不转，理由已进索引",
       any("关卡脚本" in x["what"] and "空桩" in x["why"]
           for x in DB["coverage"]["not_registered"]))
    out = capture(cmd_collide, "2")
    ck("同一个 2 现在也列出两边指令技状态",
       "dino_cmd_state" in out and "wof_rkey1" in out)

    # 过场脚本：事件脚本主题里一直缺的那张成表
    ck("过场脚本 41 个 action 全部登记",
       len(DOMAINS["dino_script_action"]["values"]) == 41)
    _, v = match_value(DOMAINS["dino_script_action"], "0x2C")
    ck("过场脚本 0x2C → 置 GO 放行镜头", bool(v) and "GO" in v["meaning"])
    _, v = match_value(DOMAINS["dino_script_action"], "44")
    ck("十进制 44 也能查到 0x2C（hex 别名命中）", bool(v) and "GO" in v["meaning"])
    ck("两个 END 的差别写进语义",
       "全体" in DOMAINS["dino_script_action"]["values"]["0x0A"]["meaning"]
       and "自己" in DOMAINS["dino_script_action"]["values"]["0x26"]["meaning"])
    ck("过场脚本记录字段 +3 → no_clamp",
       "no_clamp" in DOMAINS["dino_script_record"]["values"]["+3"]["meaning"])
    out = capture(cmd_collide, "4")
    ck("同一个 4 现在也列出过场脚本的亮相动作",
       "dino_script_action" in out and "亮相" in out)
    ck("字段偏移域 dino_script_record 不参与按取值反查",
       "dino_script_record ->" not in out)
    ck("过场脚本置 GO 与镜头放行链能对上",
       "G.$7A9" in DOMAINS["dino_script_action"]["values"]["0x2C"]["meaning"]
       and "$7A9" in DOMAINS["wave_end"]["values"]["0"]["meaning"])

    # 喂一条 6 字节记录就翻成人话（frame / comp / box / spawn 同款解码器）
    out = capture(cmd_script, ["2C", "00", "05", "01", "000A"])
    ck("script 6 字节能解码出 action 意义",
       "过场脚本记录 6 字节" in out and "置 GO" in out and "G.$7A9" in out)
    ck("script 说清 action 是字节偏移不是序号", "字节偏移，不是动作序号" in out)
    ck("script 两个规则档位按取值说开还是关",
       "[关] 置位时" in out and "[开] 置位时" in out and "0x0200" in out)
    ck("script timer 说清几帧与何时翻下一条",
       "本条动作跑 10 帧" in out and "timer 减到 0 时翻到下一条" in out)
    ck("script 说清档位跨记录保留、action 多数不是播动画",
       "会保留到后续每一条记录" in out and "多数不是播动画" in out)
    out = capture(cmd_script, ["20", "00", "00", "00", "FFFF"])
    ck("script 0xFFFF 认成 wait-until 而不是 65535 帧",
       "wait-until" in out and "每帧重跑本条" in out and "65535" not in out)
    ck("script 把置 GO 与波次收尾的同一个 GO 对上",
       "G.$7A9" in capture(cmd_script, ["2C", "00", "05", "01", "000A"])
       and "wave_end" in capture(cmd_script, ["2C", "00", "05", "01", "000A"]))
    out = capture(cmd_script, ["2D", "00", "00", "00", "0001"])
    ck("script 对未登记的奇数 action 不硬答、说走 default 空分支",
       "default 空分支" in out and "不在 41 项里" in out)
    out = capture(cmd_script, ["2C", "00"])
    ck("script 字节不够时报清楚要 6 字节", "字节不够" in out and "要 6 字节" in out)
    nr = DB["coverage"]["not_registered"]
    ck("五套脚本里 #3 Boss 攻击脚本按『单个 Boss 专属』边界不转、理由已进索引",
       any("Boss 攻击脚本" in x["what"] and "专属" in x["why"] for x in nr))

    _, v = match_value(DOMAINS["spawn_pool"], "3")
    ck("spawn_pool 3 → 池 E", bool(v) and "池 E" in v["meaning"], v["meaning"] if v else "miss")
    _, v = match_value(DOMAINS["box_field"], "10")
    ck("带 + 前缀的字段键用纯数字也能查", bool(v) and "ysize" in v["meaning"], v["meaning"] if v else "miss")

    # 最容易读反的一处：同一编号两侧不同
    _, pv = match_value(DOMAINS["player_hurt_reaction"], "0x1A")
    _, ev = match_value(DOMAINS["enemy_hurt_reaction"], "0x1A")
    ck("0x1A 玩家侧 = 背后轻击", bool(pv) and "背后" in pv["meaning"], pv["meaning"] if pv else "miss")
    ck("0x1A 敌人侧 = 起身/眩晕", bool(ev) and "起身" in ev["meaning"], ev["meaning"] if ev else "miss")
    ck("两侧意义确实不同", bool(pv and ev) and pv["meaning"] != ev["meaning"])
    _, v = match_value(DOMAINS["player_hurt_reaction"], "15")
    ck("离散编号 0xF 没有被范围键误答", v is None, v["meaning"] if v else "")
    _, v = match_value(DOMAINS["wave_terminator"], "4")
    ck("正数不误答成负值 terminator", v is None, v["meaning"] if v else "")

    # 帧解码不把 +$49 格式化成 +$31，且 10/12 字节都能跑
    out = capture(cmd_frame, ["10", "0A01", "8000", "0100", "0405", "1A02"])
    ck("frame 10 字节能解码", "帧记录 10 字节" in out)
    ck("输出是 +$49 不是 +$31", "+$49" in out and "+$31" not in out)
    ck("param_b 限定在分身绘制", "分身绘制时" in out)
    out12 = capture(cmd_frame, ["12", "0A01", "8000", "0100", "0405", "1A02", "0011"])
    ck("frame 12 字节能解码并读 attach", "attach" in out12)

    # 一串帧记录（ANI 不止一帧）与六个 i16 判定盒
    out = capture(cmd_anim, ["10", "0A01", "8000", "0100", "0405", "1A02",
                             "0A01", "8000", "0100", "0085", "1A02"])
    ck("anim 一串帧记录能翻成时间线", "帧 00" in out and "link word" in out and "身份序列" in out)
    out = capture(cmd_anim, _ANIM_BEAT)
    ck("ANI 时间线只把 kind=4 且开盒数成攻击生效，不把 6 的 [I] 推断当 [O]",
       "攻击生效帧 1 个" in out and "特殊 / 必杀帧 [I 推断]" in out
       and "不算普通攻击生效" in out)
    ck("ANI 时间线把「攻击帧但关盒」单列，不混进起势 / 收招",
       "另有 1 个攻击帧把攻击盒关着" in out and "打不着人" in out)
    mo = capture(main, ["moment", "10", "0A01", "8000", "0100", "0604", "0005",
                        "attack", "0A", "01", "00", "09", "03", "14", "00", "00"])
    ck("moment 也不把 kind=6 按普通命中结算，并说清 SPEC 边界",
       "普通命中循环只认攻方 +$2E == 4" in mo and "正面轻击" not in mo)
    ck("攻击判据收紧回 SPEC §4.4 的攻方类型 4，6 单列不混",
       ATTACK_KINDS == (4,) and SPECIAL_KINDS == (6,))
    out = capture(cmd_box, ["-1", "10", "-68", "59", "29", "42"])
    ck("box 六个数能复算出打击形状",
       "X 区间 [-68, -9]" in out and "Y 区间 [29, 71]" in out and "Z 区间 [-1, 9]" in out)

    # SPR composition：ANI -> SPR -> 判定框 中间那一环也能离线查
    out = capture(cmd_comp, ["0002", "0002", "0005", "0003", "0802", "0803",
                             "FFF8", "FFE0", "0008", "FFF0"])
    ck("comp normal 格式能解出共用调色板与摆位",
       "normal 格式" in out and "调色板 5" in out and "2 个 entry" in out and "dx=" in out)
    ck("comp 明说 count 不参与绘制、entry 按头到脚、GFX 边界",
       "不参与绘制" in out and "头 → 脚" in out and "看不到 GFX 不能说" in out)
    out = capture(cmd_comp, ["0005", "0002", "800D", "0010", "1000", "112D",
                             "1010", "006E", "FFF8", "FFE0", "0008", "FFF0"])
    ck("comp alt 格式逐 entry 拆 attr",
       "alt 格式" in out and "逐 entry 自带" in out and "调色板 14" in out and "Y 翻转" in out)
    ck("comp alt 能读出块精灵尺寸", "块 2×2 个 16×16" in out)
    ck("composition 附带 4 字节已进缓存",
       "comp_extra" in DOMAINS and "+$4C" in DOMAINS["comp_extra"]["values"])
    out = capture(cmd_collide, "4")
    ck("字段偏移域 comp_extra 不参与按取值反查", "comp_extra ->" not in out)

    # 生成记录解码：命令字（flags 低字节 bit7 = 0x0080）/ 池 / 人数条件
    out = capture(cmd_spawn, ["04D0", "0084", "0004", "0000", "0000", "0000", "0000"])
    ck("spawn 命令记录识别成脚本命令", "脚本命令" in out and "重掷" in out)
    out = capture(cmd_spawn, ["04D0", "0141", "0008", "0120", "0040", "0000", "0000"])
    ck("spawn 生成记录识别池与人数条件", "池 B" in out and "2 人以上" in out)

    # 只给一个取值反查：不知道域名也能看出「得先确定谁在读」
    out = capture(cmd_collide, "0x1A")
    ck("collide 0x1A 同时列出两侧不同意义",
       "背后" in out and "起身" in out and "没有全局意义" in out)
    out = capture(cmd_collide, "4")
    ck("collide 4 命中多个域且显式排除位域/字段偏移",
       out.count(" -> ") >= 5 and "已跳过" in out)
    ck("collide 4 同时列出三张玩家状态表",
       all(x in out for x in ("player_ground_state", "player_run_state", "player_air_state")))

    # 本轮新补的成表数值
    _, v = match_value(DOMAINS["game_mode"], "0x0C")
    ck("game_mode 0x0C → 真正的游戏帧", bool(v) and "游戏帧" in v["meaning"])
    _, v = match_value(DOMAINS["pool_a_class"], "18")
    ck("pool_a_class 18 → 第一关 Boss", bool(v) and "VICE T." in v["meaning"])
    _, v = match_value(DOMAINS["container_variant"], "0xA")
    ck("容器变体 0xA → 举不起来", bool(v) and "举不起来" in v["meaning"])
    ck("debug 词汇表不能当编号表的警告已进缓存",
       "不按那张表" in DOMAINS["enemy_ai_state"]["note"])

    # 覆盖索引：每个域都必须登记回源分组，索引既不漏也不多
    cov = DB.get("coverage", {})
    listed = [x for g in cov.get("registered", []) for x in g["domains"]]
    absent = sorted(set(DOMAINS) - set(listed))
    stale = sorted(set(listed) - set(DOMAINS))
    ck("coverage.registered 覆盖所有域", not absent, ", ".join(absent))
    ck("coverage 没有指向已删除的域", not stale, ", ".join(stale))
    ck("coverage 没有重复登记同一个域", len(listed) == len(set(listed)))
    out = capture(cmd_coverage)
    ck("coverage 命令给出合计与一致性",
       "表数值 → 抽象意义：覆盖索引" in out
       and f"合计 {len(DOMAINS)} 个域" in out
       and "缺 0 个域、多 0 个域" in out)
    ck("coverage 按游戏侧报出分布，并写明这是证据边界不是设计结论",
       "按游戏侧" in out and "两侧共用" in out and "证据边界" in out
       and "别据此评优劣" in out and "wof 原机缺机制" in out)
    ck("coverage.note 也写了按游戏侧的证据边界",
       "证据边界" in DB["coverage"]["note"]
       and "别据此评优劣" in DB["coverage"]["note"])

    # 本轮转进来的四张表：抽查「取值 → 抽象意义」
    _, v = match_value(DOMAINS["sound_command"], "0xFF06")
    ck("声音命令 0xFF06 → 音乐淡出", bool(v) and "淡出" in v["meaning"])
    _, v = match_value(DOMAINS["sound_code"], "48")
    ck("声音编号 0x30 落在音效段", bool(v) and "音效" in v["meaning"])
    _, v = match_value(DOMAINS["sound_header_type"], "5")
    ck("声音头 5 → 音效且 h 即优先级", bool(v) and "优先级" in v["meaning"])
    _, v = match_value(DOMAINS["game_phase"], "4")
    ck("关内阶段 4 → 等清场", bool(v) and "清场" in v["meaning"])
    ck("0xFFxx 命令字没有混进普通编号段",
       match_value(DOMAINS["sound_code"], "0xFF06")[1] is None)

    # 再补的七张表：招式 / 武器 / 波次 / 音序 / 声像
    _, v = match_value(DOMAINS["attack_id"], "0x04")
    ck("攻击编号 0x04 → 终结拳", bool(v) and "终结拳" in v["meaning"])
    _, v = match_value(DOMAINS["attack_id"], "0x5A")
    ck("攻击编号 0x5A → 冲刺攻击第 2 拍（hex 别名命中十进制键）",
       bool(v) and "第 2 个命中拍" in v["meaning"])
    _, v = match_value(DOMAINS["weapon_kind"], "0x209")
    ck("手持物 0x209 → 火箭筒", bool(v) and "火箭筒" in v["meaning"])
    _, v = match_value(DOMAINS["weapon_attack_state"], "0x22")
    ck("持械状态 0x22 → 后坐力", bool(v) and "后坐力" in v["meaning"])
    _, v = match_value(DOMAINS["wave_ctrl_r5"], "4")
    ck("波次子状态 4 → 收尾", bool(v) and "收尾" in v["meaning"])
    _, v = match_value(DOMAINS["seq_command"], "0x18")
    ck("音序命令 0x18 → 设声像", bool(v) and "声像" in v["meaning"])
    _, v = match_value(DOMAINS["seq_command"], "0x0E")
    ck("音序循环命令族用连续范围键，不是离散编号",
       bool(v) and "循环" in v["meaning"])
    _, v = match_value(DOMAINS["pan_mode"], "7")
    ck("声像模式 7 → 双胞胎轨", bool(v) and "双胞胎" in v["meaning"])
    ck("同一个 4 在招式表和帧类型表里不是一回事",
       DOMAINS["attack_id"]["values"]["4"]["meaning"]
       != DOMAINS["frame_type"]["values"]["4"]["meaning"])
    out = capture(cmd_collide, "4")
    ck("collide 4 现在也列出招式 / 波次 / 音序几张表",
       all(x in out for x in ("attack_id", "wave_ctrl_r4", "seq_command")))

    # wof 侧第三张表：同一个编号在玩家侧 / 敌人侧不同
    _, pv = match_value(DOMAINS["wof_player_reaction"], "0x0E")
    _, ev = match_value(DOMAINS["wof_reaction"], "0x0E")
    ck("wof 玩家侧 0x0E → 击飞", bool(pv) and "击飞" in pv["meaning"])
    ck("wof 敌人侧 0x0E → 碎尸族", bool(ev) and "碎尸" in ev["meaning"])
    ck("wof 同一个 0x0E 两侧确实不同",
       bool(pv and ev) and pv["meaning"] != ev["meaning"])
    out = capture(cmd_collide, "0x0E")
    ck("collide 0x0E 同时列出 wof 两侧",
       "wof_player_reaction" in out and "wof_reaction" in out)
    out = capture(cmd_collide, "4")
    ck("collide 4 在 wof 半边也分叉：敌人侧 / 玩家侧 / 硬直字节各讲各的",
       all(x in out for x in ("wof_reaction", "wof_player_reaction", "wof_shake_left"))
       and "抓投弹飞族" in out and "DMGREACT_BURN" in out
       and "较长生命周期" in out)
    ck("同一个 4 在 wof 两侧不是同一个回答",
       match_value(DOMAINS["wof_reaction"], "4")[1]["meaning"]
       != match_value(DOMAINS["wof_player_reaction"], "4")[1]["meaning"])
    ck("wof 玩家侧未点名的 0x0A 不硬答",
       match_value(DOMAINS["wof_player_reaction"], "0x0A")[1] is None)
    nr = DB["coverage"]["not_registered"]
    ck("民间资料四列按纪律不转的理由已写进覆盖索引",
       any("民间资料" in x["what"] and "未验" in x["why"] for x in nr))

    # ANI 段编号：看到「套 + 段」就能知道这一招，并和另外三张表对齐
    out = capture(cmd_anim_id, ["1", "4"])
    ck("anim_id 1 4 → 终结拳", "jack_anim_set1.4" in out and "终结拳" in out)
    ck("anim_id 1 4 提示连段四表对齐", "combo_counter" in out and "attack_id" in out)
    out = capture(cmd_anim_id, ["0", "21"])
    ck("anim_id 0 21 → 跳跃踢", "跳跃踢" in out)
    out = capture(cmd_anim_id, ["3", "0"])
    ck("anim_id 3 0 → 只给套级用途、不猜逐段", "没有逐段编号表" in out)
    out = capture(cmd_anim_id, ["1", "12"])
    ck("set1 的 10-13 是连续跳跃攻击族", "跳跃攻击" in out)
    out = capture(cmd_anim_id, ["1", "4"])
    ck("anim_id 直接带出这一拳的攻击记录与后果",
       "攻击属性记录 8 字节" in out and "1D 0B 06 0D 09 20 18 00" in out
       and "终结拳" in out and "lookup.py attack" in out)
    out = capture(cmd_anim_id, ["1", "0"])
    ck("anim_id 1 0 带出刺拳记录", "0A 01 00 09 03 14 00 00" in out)
    out = capture(cmd_anim_id, ["1", "2"])
    ck("没写 $58 的变体段不另配数值", "别把变体当成新的一招" in out)
    _, v = match_value(DOMAINS["combo_counter"], "3")
    ck("连段计数 3 → 终结拳", bool(v) and "终结拳" in v["meaning"])
    ck("Jack 专属表标了作用域，没写成四角色通用",
       all("Jack only" in DOMAINS[x]["scope"]
           for x in ("jack_anim_set0", "jack_anim_set1", "jack_anim_set2")))
    out = capture(cmd_collide, "3")
    ck("collide 3 现在也列出连段计数与 Jack 动画表",
       all(x in out for x in ("combo_counter", "jack_anim_set0", "jack_anim_set1")))

    # 一招的完整后果：8 字节 AttackRecord + 可查的示例判定盒
    out = capture(cmd_attack, ["0A", "01", "00", "09", "03", "14", "00", "00"])
    ck("attack 喂 8 字节能翻出八个字段与这一拳的后果",
       "攻击属性记录 8 字节" in out and "扣 10 血" in out and "顿 9 帧" in out)
    ck("attack 认出这是 Jack 连段第几拳",
       "k0" in out and "$58 = 0" in out and "刺拳" in out)
    ck("attack 说清帧记录不带伤害、反应编号只是门票",
       "帧记录本身不带伤害" in out and "第一张门票" in out)
    ck("attack 把三拳代价递进倒推成设计判断",
       "代价递进" in out and "10/15/29" in out and "续拳窗口" in out)
    out = capture(cmd_attack, ["1D", "0B", "06", "0D", "09", "20", "18", "00"])
    ck("attack 终结拳认成 k2 并说出击倒",
       "k2" in out and "29 血" in out and "击倒" in out)
    out = capture(cmd_attack, ["00", "00", "00", "00", "00", "00", "00", "00"])
    ck("未登记的招不替它猜名字", "不替它猜名字" in out)
    out = capture(cmd_attack, ["0A", "01"])
    ck("attack 字节不够会直说", "字节不够" in out)
    _, v = match_value(DOMAINS["jack_attack_record"], "k2")
    ck("jack_attack_record 的 k2 别名能查", bool(v) and "终结拳" in v["meaning"])
    _, v = match_value(DOMAINS["jack_attack_record"], "4")
    ck("$58 = 4 查到终结拳", bool(v) and "29 血" in v["meaning"])
    _, v = match_value(DOMAINS["jack_box_example"], "2")
    ck("示例盒索引 2 翻出前伸与高度",
       bool(v) and "59 像素" in v["meaning"] and "中上段" in v["meaning"])
    _, v = match_value(DOMAINS["jack_box_example"], "0x1A")
    ck("示例盒 0x1A 翻出攻防同帧",
       bool(v) and "攻防在同一帧" in v["meaning"])
    ck("两个新域都标了 Jack only 且带 source",
       all("Jack only" in DOMAINS[x]["scope"] and DOMAINS[x]["source"]
           for x in ("jack_attack_record", "jack_box_example")))
    out = capture(cmd_frame, ["10", "0A01", "8000", "0100", "0405", "1A02"])
    ck("喂帧记录时盒索引能接到可查示例盒",
       "攻击盒 #2 若属 Jack" in out and "59 像素" in out)
    out = capture(cmd_chain)
    ck("chain 把四个环节串起来并指向新命令",
       "attack 0A 01 00 09 03 14 00 00" in out and "这一拳的后果" in out)
    ck("chain 的说明版指向可跑的 moment",
       "lookup.py moment" in out and "错配" in out)

    # moment：同一帧的几份数据合成一句，且拦住「攻击记录挂到非攻击帧」
    frame = ["10", "0A01", "8000", "0100", "0405", "1A02"]
    rec = ["0A", "01", "00", "09", "03", "14", "00", "00"]
    ck("moment 不给参数会给用法", "用法：moment" in capture(cmd_moment, []))
    out = capture(cmd_moment, frame)
    ck("只喂帧记录：说清后果不在帧里、指出怎么补",
       "帧记录不带伤害" in out and "attack <8 bytes>" in out
       and "身份" in out and "判定框环" in out)
    ck("SPR 环与判定框环分开：画面不决定打不打得中",
       "不参与打不打得中" in out and "跟画面不是一层数据" in out)
    out = capture(cmd_moment, frame + ["attack"] + rec)
    ck("挂上攻击记录：身份 / 空间 / 后果合起来，接得到 Jack 连段",
       "扣 10 血" in out and "两本册子" in out and "$58 = 0" in out
       and "攻防同帧" in out)
    dead = ["10", "0A01", "8000", "0100", "0005", "1A02"]
    out = capture(cmd_moment, dead + ["attack"] + rec)
    ck("抓投探测帧挂攻击记录会被拦住，并说清走的是抓住 / 被抓那条链",
       "不该在这一拍结算" in out and "不归这 10/12 字节管" in out
       and "抓投探测盒" in out and "扣 10 血" not in out)
    special = ["10", "0A01", "8000", "0100", "0605", "1A02"]
    out = capture(cmd_moment, special + ["attack"] + rec)
    ck("特殊 / 必杀帧（kind 6）不按普通命中结算，并说清是 [I] 推断",
       "普通命中循环只认攻方 +$2E == 4" in out and "[I 推断]" in out
       and "这一帧能打人" not in out and "扣 10 血" not in out)
    ck("frame_type 6 仍登记为特殊 / 必杀，但 note 写明不通过普通命中循环",
       "攻击" in DOMAINS["frame_type"]["values"]["6"]["meaning"]
       and "命中循环只认攻方" in DOMAINS["frame_type"]["values"]["6"]["note"]
       and "防守方类型分派" in DOMAINS["frame_type"]["values"]["6"]["note"])
    ck("frame_type 域级 note 也写明 6 是推断、别数成攻击生效帧",
       "别数成攻击生效帧" in DOMAINS["frame_type"]["note"])
    ck("盒索引按 SPEC 写成十六进制，对得上 0x1A",
       "身体盒 #0x1A" in capture(cmd_moment, frame))
    ck("攻击记录字节不够会直说",
       "攻击记录字节不够" in capture(cmd_moment, frame + ["attack", "0A", "01"]))
    comp = ["0002", "0002", "0005", "0003", "0802", "0803",
            "FFF8", "FFE0", "0008", "FFF0"]
    out = capture(cmd_moment, frame + ["comp"] + comp)
    ck("SPR 环能真喂进来：零件数与摆位和盒区间并排",
       "2 块零件" in out and "接了 layout" in out
       and "不是一层数据" in out and "判定不跟着画面走" in out)
    out = capture(cmd_moment, frame + ["comp"] + comp + ["attack"] + rec)
    ck("attack 与 comp 顺序任意都能合成，三环都在",
       "2 块零件" in out and "扣 10 血" in out and "三环并排" in out)
    ck("不喂 comp 时会提示怎么补这一环",
       "想把这一环也喂进来" in capture(cmd_moment, frame))
    ck("composition 字节不够会直说",
       "composition 字节不够" in capture(cmd_moment, frame + ["comp", "00", "02"]))
    ck("doc 与 list 都跟上 moment",
       "lookup.py moment" in __doc__ and "moment" in capture(cmd_list))

    # wof 16 字节参数行：与 dino attack 对称的「喂字节」入口
    ours = ["00", "00", "00", "00", "0A", "00", "03", "00",
            "56", "00", "00", "00", "06", "0E", "03", "00"]
    enemy = ["00", "00", "00", "00", "02", "00", "03", "00",
             "56", "00", "04", "06", "03", "00", "00", "00"]
    out = capture(cmd_wof_attack, [])
    ck("wof_attack 不给攻防方向会直说用法", "ours|enemy" in out and "用法" in out)
    out = capture(cmd_wof_attack, ["ours", "0A", "00"])
    ck("wof_attack 字节不够会直说", "字节不够" in out)
    out = capture(cmd_wof_attack, ["ours"] + ours)
    ck("wof_attack ours 翻出我方表与逐格字段",
       "0x6DB44" in out and "攻击力基值" in out and "两张表" in out)
    ck("wof_attack ours 的反应编号接到敌人侧受击入口",
       "敌人侧受击入口" in out and "击倒飞行" in out and "碎尸族" in out)
    ck("wof_attack ours 明说死法名未验、不固化",
       "未验命名" in out and "不固化" in out)
    ck("wof_attack ours 把 shake 接到 +0x62 的生命周期",
       "群体命中锁" in out and "解锁" in out)
    out = capture(cmd_wof_attack, ["enemy"] + enemy)
    ck("wof_attack enemy 换敌方布局、反应字节在 +0xA",
       "0x6E754" in out and "难度索引增量" in out and "玩家侧受击入口" in out)
    ck("wof_attack enemy 明说伤害不写在这一行",
       "伤害另从" in out and "不在这 16 字节里" in out)
    ck("wof_attack 边界写清三条命中链按不同偏移读同一行",
       "0x8D00" in out and "不串等价" in out)
    ck("wof_attack 对没给消费端的格不硬答", "不硬答" in out)
    ck("attack 命令指到 wof 半边的对称入口",
       "wof_attack" in capture(cmd_attack, ["0A", "01", "00", "09", "03", "14", "00", "00"]))
    ck("doc 与 list 都列出 wof_attack",
       "lookup.py wof_attack" in __doc__ and "wof_attack" in capture(cmd_list))
    new_keys = ("ours:+0xB", "ours:+0xE", "enemy:+0..3",
                "enemy:+6..7", "enemy:+8..9", "enemy:+0xC")
    fv = DOMAINS["wof_atk_field"]["values"]
    ck("补进 wof_atk_field 的几格都带 meaning / tag",
       all(k in fv and fv[k]["meaning"] and fv[k]["tag"] == "O" for k in new_keys))

    # wof 受击手册选择 + 玩家输入契约
    _, v = match_value(DOMAINS["wof_hurt_book"], "0x11878")
    ck("入口地址 0x11878 → 绝大多数敌人共用的受击手册",
       bool(v) and "共用" in v["meaning"])
    _, v = match_value(DOMAINS["wof_hurt_book"], "0x11720")
    ck("入口地址 0x11720 → 玩家本体手册",
       bool(v) and "玩家本体" in v["meaning"])
    ck("按角色分的是动画不是受击逻辑，note 已写明",
       "动画数据" in DOMAINS["wof_hurt_book"]["note"])
    out = capture(cmd_lookup, "input_buffer", "$C9", False)
    ck("输入缓冲 $C9 → 受击中必杀攒 10 帧", "10 帧" in out)
    ck("输入契约明写没有输入队列",
       "没有输入队列" in DOMAINS["input_buffer"]["label"])
    nr = DB["coverage"]["not_registered"]
    ck("街机前端硬件位按用户边界不转，理由已进索引",
       any("街机前端" in x["what"] and "硬件" in x["why"] and "游戏性" in x["why"]
           for x in nr))
    ck("HANDOFF 工程交接按边界不转、理由已进索引",
       any("HANDOFF.md" in x["what"] and "工程台账" in x["why"] for x in nr))

    # 主题索引：与 coverage 正交，每个域恰好归一处
    items = DB.get("themes", {}).get("list", [])
    listed = [x for t in items for x in t["domains"]]
    ck("主题索引覆盖所有域，且每个域只归一处",
       sorted(listed) == sorted(DOMAINS) and len(listed) == len(set(listed)),
       f"listed={len(listed)} domains={len(DOMAINS)}")
    ck("主题里的域名都真实存在", all(x in DOMAINS for x in listed))
    out = capture(cmd_themes, [])
    ck("themes 无参数能列出四块主题",
       all(x in out for x in ("state_machine", "hit_logic", "event_script", "enemy_strategy")))
    out = capture(cmd_themes, ["state_machine"])
    ck("themes state_machine 能列出该块域名",
       "combo_counter" in out and "input_buffer" in out)

    # 外推文九条判断的证据底座：能查什么、查不到什么
    items = DB.get("legacy", {}).get("list", [])
    ck("外推文九条判断都有证据底座", len(items) == 9)
    ck("legacy 每条域名都真实存在",
       all(x in DOMAINS for it in items for x in it["domains"]))
    ck("legacy 每条都写清能查与查不到",
       all(it["can_check"] and it["cannot_check"] for it in items))
    used_legacy = {x for it in items for x in it["domains"]}
    ck("legacy 不要求覆盖所有域：themes 才覆盖全部域，未挂判断的域不是漏查",
       len(used_legacy) < len(DOMAINS)
       and "不要求覆盖所有域" in DB["legacy"]["note"])
    ck("legacy note 写清挂域标准是能否回答判断、不是凑覆盖率",
       "凑覆盖率" in DB["legacy"]["note"]
       and "字段偏移域" in DB["legacy"]["note"])
    cont = next(x for x in items if x["key"] == "continuity")
    ck("continuity 不把 camera_event（记录里第几格）当镜头证据硬挂",
       "camera_event" not in cont["domains"] and "camera_lock" in cont["domains"])
    ck("legacy 总览把「未挂不是漏查」直接打印出来",
       "未挂的不是漏查" in capture(cmd_legacy, []))
    ck("难度条明写 rank 数值按纪律不转",
       any("rank / aggression" in it["cannot_check"] for it in items))
    out = capture(cmd_legacy, [])
    ck("legacy 无参数列出九条", all(it["title"] in out for it in items))
    out = capture(cmd_legacy, ["difficulty"])
    ck("legacy difficulty 只展开一条并列出域名",
       "六、同一套打法" in out and "wave_ctrl_r4" in out
       and "rank / aggression" in out and "五、一群敌人" not in out)
    out = capture(cmd_legacy, ["nope"])
    ck("legacy 未知 key 直说并给出可用列表", "没有这一条" in out and "beat" in out)
    ck("九条 probe 都带 argv 与 expect（挂多条的逐条都要有）",
       all(pr["argv"] and pr["expect"]
           for it in items for pr in legacy_probes(it)))
    diff = next(x for x in items if x["key"] == "difficulty")
    ck("难度条除了波次，还挂上「贴脸后按档停顿」这条 AI 证据",
       any(pr["argv"] == ["enemy_ai_state", "14"] for pr in legacy_probes(diff))
       and "aggression" in diff["can_check"]
       and "逐帧实证" in diff["cannot_check"])
    beat = next(x for x in items if x["key"] == "beat")
    ck("拍子那条判断也挂上「被打倒那一侧的时间」，且边界没写宽",
       "player_hurt_anim" in beat["domains"]
       and "enemy_hurt_anim" in beat["domains"]
       and "躺地" in beat["can_check"] and "搓招" in beat["can_check"]
       and any(pr["argv"] == ["player_hurt_anim", "2"] for pr in legacy_probes(beat))
       and "没有逐帧 trace" in beat["cannot_check"]
       and "不逐档登记" in beat["cannot_check"])
    ck("玩家段表写明改判不挂进 reactions，免得读成同一拍同时播",
       "改写成反应 0x1A" in DOMAINS["player_hurt_anim"]["note"]
       and "同时播" in DOMAINS["player_hurt_anim"]["note"])
    for it in items:
        for pr in legacy_probes(it):
            out = capture(main, pr["argv"])
            ck(f"legacy {it['key']} 的样本 {' '.join(pr['argv'])} 跑得通",
               pr["expect"] in out)
    both_sides = ("beat", "swing", "death", "feel", "values")
    ck("讲两侧的判断各自两侧都有真跑样本（第二节按正文边界不算）",
       all(len(legacy_probes(next(x for x in items if x["key"] == k))) >= 2
           for k in both_sides))
    cb = next(x for x in items if x["key"] == "combo")
    ck("combo 不硬凑 wof 样本：正文自己写了不并成同一套因果",
       "不并成同一套因果" in cb["cannot_check"]
       and all(pr["argv"][0] != "wof_rkey1" for pr in legacy_probes(cb)))
    ck("不算讲两侧的三条都写清了理由，没留半边悬念",
       all("不按" in next(x for x in items if x["key"] == k)["cannot_check"]
           for k in ("combo", "crowd", "continuity")))
    _, d14 = match_value(DOMAINS["enemy_hurt_reaction"], "14")
    _, w14 = match_value(DOMAINS["wof_reaction"], "14")
    ck("death 两侧样本是同一个编号的不同回答，不是凑数",
       d14 is not None and w14 is not None
       and d14["meaning"] != w14["meaning"])
    vs = legacy_probes(next(x for x in items if x["key"] == "values"))
    ck("values 的 0 在两侧各有一条样本",
       any(pr["argv"][:2] == ["box_index_zero", "dino"] for pr in vs)
       and any(pr["argv"][:2] == ["box_index_zero", "wof"] for pr in vs))
    sw = next(x for x in items if x["key"] == "swing")
    ck("swing 的底座接上「一拍也不是一条数据」的合成样本",
       "合成一句" in sw["can_check"]
       and any(pr["argv"][0] == "moment" for pr in legacy_probes(sw)))
    ck("swing 另有一条把 composition 也喂进去的三环样本",
       "画面零件与摆位" in sw["can_check"]
       and any(pr["argv"][0] == "moment" and "comp" in pr["argv"]
               for pr in legacy_probes(sw)))
    ck("swing 的合成样本真跑出「两本册子要同一拍才对上」",
       "两本册子" in capture(main, ["moment", "10", "0A01", "8000", "0100",
                                    "0405", "1A02", "attack", "0A", "01",
                                    "00", "09", "03", "14", "00", "00"]))
    ck("crowd 说清缺的是可查域、不是缺证据",
       any(it["key"] == "crowd" and "[O] 级回源" in it["cannot_check"]
           and "不是叙事" in it["cannot_check"] and "不硬编" in it["cannot_check"]
           for it in items))
    ck("feel 说清一字节三职有 [O] 回源、不是叙事",
       any(it["key"] == "feel" and "[O] 级回源" in it["cannot_check"]
           and "不是叙事" in it["cannot_check"] for it in items))
    ck("cannot_check 不再把 [O] 观察笼统叫叙事",
       all("叙事结论" not in it["cannot_check"] and "叙事概括" not in it["cannot_check"]
           for it in items))
    for key, marker in (("crowd", "enemy.rs"), ("feel", "Cps1Collision.cs"),
                        ("combo", "notes/02-mid.md")):
        it = next(x for x in items if x["key"] == key)
        ck(f"legacy {key} 的 source 指到具体回源",
           marker in it.get("source", "") and "[O] 级回源" in it["cannot_check"])
    ck("combo 说清连打阈值门有 [O] 回源但按纪律不转",
       any(it["key"] == "combo" and "不是叙事" in it["cannot_check"]
           and "不硬编" in it["cannot_check"] and "条件分支" in it["cannot_check"]
           for it in items))
    ck("覆盖索引写明连打累计四层为什么不转",
       any("StunVal" in x["what"] and "不硬编" in x["why"]
           and "未验" in x["why"]
           for x in DB["coverage"]["not_registered"]))
    out = capture(cmd_legacy, ["combo"])
    ck("legacy combo 单条视图能打印新挂的回源",
       "另有 [O] 回源" in out and "0x7E86" in out)
    out = capture(cmd_legacy, ["crowd"])
    ck("legacy 单条视图打印 [O] 回源去哪看",
       "另有 [O] 回源" in out and "enemy.rs" in out)

    # wof +0x62 一字节三职：从「有 [O] 回源但没转成域」变成真能喂值查
    d62 = DOMAINS["wof_shake_left"]
    ck("wof +0x62 域带齐 source / scope 与三职、同名分辨说明",
       d62["source"] and "wof" in d62["scope"]
       and all(x in d62["note"] for x in ("硬直门", "闪白", "群体命中锁", "A5-0x62")))
    out = capture(cmd_lookup, "wof_shake_left", "3", False)
    ck("查 +0x62 = 3 能翻出生命周期与群体命中解锁",
       "3 帧" in out and "群体命中锁" in out and "解锁" in out)
    _, v = match_value(d62, "0")
    ck("+0x62 = 0 是门关上、不是『没有硬直』", bool(v) and "解锁" in v["meaning"])
    _, v = match_value(d62, "nonzero")
    ck("+0x62 非零态每帧 -1 跳过本帧，数值只是还剩几帧",
       bool(v) and "每帧" in v["meaning"] and "rts" in v["meaning"])
    ck("+0x62 的 3 明说『能打几个』是注释读法、不是逐帧实测",
       "不是逐帧实测" in d62["values"]["3"]["meaning"])
    out = capture(cmd_collide, "3")
    ck("collide 3 能列出 wof_shake_left 且不误答字段偏移",
       "wof_shake_left" in out
       and not any(l.strip().startswith(n + " ")
                   for l in out.splitlines() if "->" in l
                   for n in OFFSET_KEY_DOMAINS))
    ck("legacy feel 现在把 +0x62 写进可查域与能查说明",
       any(it["key"] == "feel" and "wof_shake_left" in it["domains"]
           and "+0x62" in it["can_check"] for it in items))
    out = capture(cmd_lookup, "attack_field", "+3", False)
    ck("换掉 feel 的 probe 后，八字段攻击记录仍查得到命中定格", "命中定格" in out)

    # 判断讲两侧的，证据底座也得跟到两侧
    ck("swing 的底座不再只有 dino 半边",
       any(it["key"] == "swing"
           and all(d in it["domains"] for d in
                   ("wof_shake_left", "wof_atk_field", "wof_reaction"))
           and "+0x62" in it["can_check"] and "逐帧实测" in it["cannot_check"]
           for it in items))
    ck("beat 的底座也接上 wof 双方同写那一拍",
       any(it["key"] == "beat" and "wof_shake_left" in it["domains"]
           and "双方同写" in it["can_check"] for it in items))
    out = capture(main, ["wof_attack", "ours", "00", "00", "00", "00", "0A", "00",
                         "03", "00", "56", "00", "00", "00", "06", "0E", "03", "00"])
    ck("swing 新增的 wof 半边能真跑出群体命中解锁",
       "群体命中锁" in out and "解锁" in out)
    ck("按 wof 边界不转的那几条没有硬塞 wof 域",
       all(not any(d.startswith("wof_") for d in it["domains"])
           for it in items if it["key"] in ("crowd", "continuity", "difficulty")))

    # 取值反查的排除纪律：位域靠 bitfield 标志、字段偏移靠列表，两者合起来才算齐
    should_skip = {n for n, d in DOMAINS.items()
                   if d.get("bitfield") or n in OFFSET_KEY_DOMAINS}
    out = capture(cmd_collide, "4")
    hit_lines = [l for l in out.splitlines() if "->" in l]
    ck("collide 尾部列全被跳过的位域 / 字段偏移域",
       all(n in out for n in should_skip))
    ck("被跳过的域没有一个出现在命中行里",
       all(not any(l.strip().startswith(n + " ") for l in hit_lines)
           for n in should_skip))
    ck("所有登记键都能被自己反查命中",
       all(match_value(d, k)[0] == k for d in DOMAINS.values() for k in d["values"]))
    parse_bad = []
    for name, dom in DOMAINS.items():
        vals = dom["values"]
        ranges = [(int(m.group(1)), int(m.group(2)), k)
                  for k in vals
                  for m in [re.fullmatch(r"(\d+)-(\d+)", k)] if m]
        exact = [int(k) for k in vals if k.isdigit()]
        for a, b in itertools.combinations(ranges, 2):
            if a[0] <= b[1] and b[0] <= a[1]:
                parse_bad.append(f"{name}:范围重叠 {a[2]}/{b[2]}")
        for n in exact:
            if any(lo <= n <= hi for lo, hi, _ in ranges):
                parse_bad.append(f"{name}:精确键 {n} 落在范围内")
        aliases = [str(v.get("alias", "")) for v in vals.values()]
        aliases = [a for a in aliases if a]
        if len(aliases) != len(set(aliases)):
            parse_bad.append(f"{name}:别名撞车")
    ck("范围键不重叠、精确键不掉进范围、别名不撞车",
       not parse_bad, ", ".join(parse_bad))
    ck("同义不是抄重：三个域的 note 讲清了为什么多个键一句话",
       all(w in DOMAINS[n]["note"] for n, w in
           (("drop_code", "不是登记重复"),
            ("container_variant", "编号不同不等于规则不同"),
            ("jack_anim_set0", "不是把意义抄重了"))))
    ck("字段偏移域里没有纯数字键，两个位域都标了 bitfield",
       all(not any(re.fullmatch(r"\d+", k) for k in DOMAINS[n]["values"])
           for n in OFFSET_KEY_DOMAINS)
       and all(DOMAINS[n].get("bitfield") for n in ("draw_flags", "sprite_attr")))

    # 「还没弄明白」入口：把两类未登记并排说清，别读成「不存在」
    u_groups = unknown_rows()
    u_total = sum(len(us) for _, us in u_groups.values())
    ck("unknown_note 把两类未登记分开、明写不等于不存在",
       all(x in DB["coverage"].get("unknown_note", "")
           for x in ("两类", "[U]", "不等于", "不存在")))
    ck("所有 [U] 条目都只写部分意义、没有硬给具体意义",
       all(v["tag"] == "U" and any(
           w in v["meaning"] for w in
           ("未登记", "未明", "未逐项", "未单列", "用途未", "不从字段名猜"))
           for _, us in u_groups.values() for _, v in us))
    out = capture(cmd_unknown, [])
    ck("unknown 全览逐条打出了 [U] 的意义，且按域分组带出处",
       all(v["meaning"] in out for _, us in u_groups.values() for _, v in us)
       and all(n in out and DOMAINS[n]["source"] in out for n in u_groups)
       and f"共 {u_total} 条" in out)
    ck("unknown 全览同时给出按纪律不转的类数与边界句",
       f"{len(DB['coverage']['not_registered'])} 类" in out
       and "未登记 ≠ 不存在" in out and "不是漏查" in out
       and "collide" in out)
    one = "player_ground_state" if "player_ground_state" in u_groups else next(iter(u_groups))
    out_one = capture(cmd_unknown, [one])
    ck("unknown <域> 只看那一册、带出处、不退化成全览",
       f"{one} 里还没弄明白" in out_one
       and DOMAINS[one]["source"] in out_one
       and "这份缓存还答不了什么" not in out_one)
    clean = next(n for n in DOMAINS if n not in u_groups)
    out_clean = capture(cmd_unknown, [clean])
    ck("没有 [U] 的域会明说不代表整类都清楚",
       "没有 [U] 取值" in out_clean and "不代表整类都清楚" in out_clean)

    # 每条 [U] 都要写清「回源走到哪、为什么停」，且里面的路径与行号真能点开
    blocked = [(n, k, v["blocked_at"]) for n, (_, us) in u_groups.items()
               for k, v in us if v.get("blocked_at")]
    ck("每条 [U] 都带 blocked_at，说明回源止于何处、为什么不硬答",
       len(blocked) == u_total and all(
           any(w in s for w in ("回源到此为止", "不硬编", "不从概括固化",
                                "不把美术推测升级"))
           for _, _, s in blocked))
    check_paths = blocked + [("coverage.unknown_note", "-",
                              DB["coverage"].get("unknown_note", ""))]
    bad_blocked = []
    for n, k, s in check_paths:
        for m in re.finditer(
                r"([A-Za-z0-9_./-]+\.(?:md|rs|py|txt)):(\d+)(?:-(\d+))?", s):
            f = repo_root / m.group(1)
            if not f.exists():
                bad_blocked.append(f"{n}.{k}:{m.group(1)} 不存在")
                continue
            nl = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            hi = int(m.group(3) or m.group(2))
            if int(m.group(2)) > nl or hi > nl:
                bad_blocked.append(f"{n}.{k}:{m.group(0)}(文件 {nl} 行)")
    ck("blocked_at 里的回源路径与行号都真能点开、不越界",
       not bad_blocked, ", ".join(bad_blocked))
    ck("unknown 全览与单域都把 blocked_at 摆出来",
       all(s in out for _, _, s in blocked)
       and "回源止于" in out and "回源止于" in out_one)
    ck("证据够的一条已从 [U] 升为 [O]：撞到玩家后的等待再攻击",
       DOMAINS["enemy_ai_state"]["values"]["14"]["tag"] == "O"
       and "0x34204" in DOMAINS["enemy_ai_state"]["values"]["14"]["meaning"]
       and "enemy_ai_state" not in u_groups)
    ck("unknown_note 明写 [U] 是照抄上游、不是漏查",
       "照抄上游" in DB["coverage"].get("unknown_note", ""))
    ck("unknown 给不存在的域会明确报错，不静默当空",
       "没有这个域" in capture(cmd_unknown, ["no_such_domain"]))

    # 按玩法主题走进缓存时，成色要跟着走：别把推断当观察、把未登记当不存在
    out_t = capture(cmd_themes, ["state_machine"])
    ck("themes 单主题视图说清证据成色，并直接指到未登记的那些域",
       "观察" in out_t and "推断" in out_t and "未登记" in out_t
       and "unknown player_ground_state" in out_t
       and "未登记 ≠ 不存在" in out_t)
    df = next(x for x in DB["themes"]["list"] if x["key"] == "data_format")
    out_tt = capture(cmd_themes, [])
    ck("themes 总览也按主题给出观察 / 推断 / 未登记分布",
       f"推断 {theme_agg(df['domains'])['I']}" in out_tt
       and "data_format" in out_tt and "[I 推断]" in out_tt
       and "[U 未登记]" in out_tt)
    ck("六个主题的未登记条数合计等于全库 [U]，没漏报也没重复归",
       sum(theme_agg(t["domains"])["U"] for t in DB["themes"]["list"])
       == sum(1 for dom in DOMAINS.values()
              for v in dom["values"].values() if v["tag"] == "U"))

    # 解码输出也带证据标签：别让 [I] 在「这一帧在干嘛」里被读成观察
    ck("say() 把 meaning 与置信标签一起带出，缺省也不冒充登记",
       "[I 推断]" in say(DOMAINS["frame_type"]["values"]["6"])
       and "[U 未登记]" in say(DOMAINS["jack_anim_set1"]["values"]["15"])
       and say(None) == "未登记")
    out_i6 = capture(main, ["moment", "10", "0A01", "8000", "0100", "0605", "1A02"])
    ck("moment 喂必杀帧时，身份那行明说 [I 推断]",
       "1) 身份 / 这一拍：特殊 / 必杀攻击帧 [I 推断]" in out_i6)
    out_i0 = capture(main, ["frame", "10", "0A01", "8000", "0100", "0005", "1A00"])
    ck("frame 的「这一帧在干嘛」也带标签，不与逐字段行口径打架",
       "身份：中立帧" in out_i0 and out_i0.count("[I 推断]") >= 2)
    out_w = capture(main, ["wof_attack", "ours", "00", "00", "00", "00", "0A", "00",
                           "03", "00", "56", "00", "00", "00", "06", "0E", "03", "00"])
    ck("wof 参数行翻反应 / shake 取值时带标签，字段布局不冒充取值",
       "平时反应" in out_w and "· shake" in out_w
       and "[O 观察]" in out_w and "→ 伤害随机偏移 long" in out_w
       and "伤害随机偏移 long [O 观察]" not in out_w)
    out_a = capture(main, ["anim_id", "1", "4"])
    ck("anim_id 带出的攻击后果不丢标签",
       "攻击编号表里 $58" in out_a and "[O 观察]" in out_a)

    # 后果环别停在「第一张门票」：反应编号要能直接翻到两本受击册子
    out_atk = capture(main, ["attack", "1D", "0B", "06", "0D", "09", "20", "18", "00"])
    ck("attack 把反应门票在玩家侧 / 敌人侧并排翻出来，且不串 wof",
       "player_hurt_reaction" in out_atk and "enemy_hurt_reaction" in out_atk
       and "重击倒 B" in out_atk and "击倒 B（anim 3）" in out_atk
       and "[O 观察]" in out_atk and "别把编号直接对上" in out_atk
       and "wof_reaction" not in out_atk)
    ck("attack 对照 Jack 连段那行也带证据标签",
       any("对照 Jack 连段" in l and "[O 观察]" in l for l in out_atk.splitlines()))
    ck("反应门票后面还接了一环：代码会去播 set2 的第几段",
       "接着播 set2 #8" in out_atk and "[O 观察]" in out_atk
       and "重击倒" in out_atk)
    ck("一个反应按正面 / 背后分岔时，明说不是同时播",
       "set2 #0" in "\n".join(hurt_anim_for(14))
       and "set2 #6" in "\n".join(hurt_anim_for(14))
       and "分岔" in "\n".join(reaction_brief(14)))
    ck("受击动画段域写清两层边界：代码调用号 vs Jack 美术标签",
       all(w in DOMAINS["player_hurt_anim"]["note"]
           for w in ("四个角色通用", "Jack", "美术推断", "not_registered"))
       and DOMAINS["player_hurt_anim"]["context_dependent"])
    ck("每个 reactions 编号都能在玩家受击手册里查到",
       all(str(r) in DOMAINS["player_hurt_reaction"]["values"]
           for v in DOMAINS["player_hurt_anim"]["values"].values()
           for r in v["reactions"]))
    ck("moment 挂上攻击记录时也能带出接着播哪一段",
       "接着播 set2 #0" in capture(main, ["moment", "10", "0A01", "8000", "0100",
                                          "0405", "1A02", "attack", "0A", "01",
                                          "00", "09", "03", "14", "00", "00"]))
    ck("没给 anim2 调用的反应不硬答：0x22 停在手册那一层",
       "接着播 set2" not in "\n".join(reaction_brief(34)))
    ck("敌人侧 anim 编号要按兵种再翻表，玩家侧段表不套过去",
       all(w in DOMAINS["enemy_hurt_reaction"]["note"]
           for w in ("set_hit_anim", "e.w84", "别套过来"))
       and "敌人侧不适用" in DOMAINS["player_hurt_anim"]["note"]
       and "玩家侧" in DOMAINS["player_hurt_anim"]["scope"])
    hurt_notes = [(n, DOMAINS[n]["note"])
                  for n in ("enemy_hurt_reaction", "player_hurt_anim")]
    bad_note = []
    for n, s in hurt_notes:
        for m in re.finditer(
                r"([A-Za-z0-9_./-]+\.(?:md|rs|py|txt)):(\d+)(?:-(\d+))?", s):
            f = repo_root / m.group(1)
            if not f.exists():
                bad_note.append(f"{n}:{m.group(1)} 不存在")
                continue
            nl = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            if int(m.group(3) or m.group(2)) > nl:
                bad_note.append(f"{n}:{m.group(0)}({nl} 行)")
    ck("两侧边界 note 里新写的回源路径与行号真能点开",
       not bad_note, ", ".join(bad_note))
    ck("chain 说明版点明两侧下游各走各的、不串成一条链",
       "两侧都能再往下一环" in capture(cmd_chain)
       and "别串成一条链" in capture(cmd_chain))
    ck("敌人册子也接上下一环：分派到哪个受击姿态槽",
       "敌人姿态槽 #3" in out_atk and "击倒 B 的姿态" in out_atk)
    ck("两侧下游各自紧跟自己那本册子，不串成同一条链",
       out_atk.index("player_hurt_reaction") < out_atk.index("接着播 set2 #8")
       < out_atk.index("enemy_hurt_reaction") < out_atk.index("敌人姿态槽 #3"))
    ck("上一轮悬空的 not_registered 引用已落实为第 14 条",
       len(DB["coverage"]["not_registered"]) == 14
       and any("e.w84" in x["what"] and "enemy_hurt_anim" in x["why"]
               for x in DB["coverage"]["not_registered"])
       and "coverage.not_registered" in DOMAINS["enemy_hurt_reaction"]["note"]
       and "enemy_hurt_anim" in DOMAINS["enemy_hurt_reaction"]["note"])
    ck("敌人姿态槽的 reactions 都能在敌人受击手册里查到",
       all(str(r) in DOMAINS["enemy_hurt_reaction"]["values"]
           for v in DOMAINS["enemy_hurt_anim"]["values"].values()
           for r in v["reactions"]))
    ck("敌人姿态槽域写清「槽位语义 vs 按兵种图集」与两侧编号不通用",
       all(w in DOMAINS["enemy_hurt_anim"]["note"]
           for w in ("e.w84", "not_registered", "player_hurt_anim", "别互套"))
       and DOMAINS["enemy_hurt_anim"]["context_dependent"])
    ck("没登记的反应编号不硬答",
       "两本册子都没登记" in capture(main, ["attack", "0A", "01", "05", "09",
                                            "03", "14", "00", "00"]))
    ck("chain 说明版与可跑版对齐：点明反应门票两侧并排",
       "反应门票在玩家侧 / 敌人侧两本册子里并排翻出来" in capture(cmd_chain))
    out_mom = capture(main, ["moment", "10", "0A01", "8000", "0100", "0405", "1A02",
                             "attack", "1D", "0B", "06", "0D", "09", "20", "18", "00"])
    ck("moment 挂上攻击记录时，后果环也把反应门票翻到两本册子",
       "player_hurt_reaction" in out_mom and "enemy_hurt_reaction" in out_mom
       and "重击倒 B" in out_mom and "对照 Jack 连段" in out_mom
       and "[O 观察]" in out_mom)

    # 入口一致性：doc 与 list 都得跟上后来加的命令
    ck("doc 不再把无参数误写成列域",
       "打印这份用法说明" in __doc__ and "lookup.py list" in __doc__)
    out = capture(cmd_list)
    ck("list 末尾给出解码命令与三个索引、以及 unknown 入口",
       all(x in out for x in ("attack", "script", "coverage", "themes", "legacy", "unknown")))
    readme = (repo_root / "re/README.md").read_text(encoding="utf-8")
    context = (repo_root / "re/specs/CONTEXT.md").read_text(encoding="utf-8")
    ck("re/ 工作区两个入口也指得到语义缓存与查询脚本",
       all(x in readme for x in ("semantics.json", "lookup.py", "unknown", "themes"))
       and all(x in context for x in ("semantics.json", "lookup.py")))
    nav_cmds = ("frame", "anim", "comp", "box", "spawn", "script", "attack",
                "wof_attack", "moment", "chain", "collide", "coverage",
                "unknown", "themes", "legacy")
    nav_out = {n: capture(main, [n]) for n in nav_cmds}
    ck("总入口阅读顺序第 7 条列的查数入口都还在、没退化成未知域",
       all("没有这个域" not in o for o in nav_out.values())
       and "用法：moment" in nav_out["moment"]
       and "ANI → SPR → 判定框" in nav_out["chain"])
    smoke_bad = []
    for name, argv in SMOKE_CASES:
        try:
            s_out, rc = capture_rc(main, argv)
        except Exception as exc:
            smoke_bad.append(f"{name}:抛异常 {type(exc).__name__}")
            continue
        if rc != 0 or not s_out.strip() or "Traceback" in s_out \
                or "没有这个域" in s_out \
                or (argv and s_out.lstrip().startswith("用法：")):
            smoke_bad.append(f"{name}:rc={rc}")
    ck(f"用法里列的 {len(SMOKE_CASES)} 条命令都还跑得完，没退化成空输出 / 用法 / 未知域",
       not smoke_bad, ", ".join(smoke_bad))

    ok = sum(1 for _, good, _ in checks if good)
    for label, good, detail in checks:
        print(f"  {'PASS' if good else 'FAIL'}  {label}" + (f"   [{detail}]" if not good and detail else ""))
    print(f"\n{ok}/{len(checks)} 通过")
    return 0 if ok == len(checks) else 1


# 用法说明里列的每条命令：改动解码逻辑后逐条冒烟一次。
# 这里只管「能不能完整跑完、有没有退化成空输出 / 用法 / 未知域」，
# 具体语义由 --selftest 里那些断言管，两者不重复。
_WOF = ["00", "00", "00", "00", "0A", "00", "03", "00",
        "56", "00", "00", "00", "06", "0E", "03", "00"]
_FRAME = ["10", "0A01", "8000", "0100", "0405", "1A02"]
_ATK = ["attack", "0A", "01", "00", "09", "03", "14", "00", "00"]
_COMP = ["comp", "0002", "0002", "0005", "0003", "0802", "0803"]
SMOKE_CASES = [
    ("list", ["list"]),
    ("domain-all", ["frame_type"]),
    ("domain-one", ["frame_type", "4"]),
    ("range", ["drop_code", "25"]),
    ("attr", ["attr", "0x3020"]),
    ("flags", ["flags", "draw_flags", "0x81"]),
    ("frame10", ["frame"] + _FRAME),
    ("frame12", ["frame", "12", "0A01", "8000", "0100", "0405", "1A02", "0011"]),
    ("anim", ["anim", "10", "0A01", "8000", "0100", "0405", "1A02",
              "0A01", "8000", "0100", "0085", "1A02"]),
    ("anim_beat", ["anim"] + _ANIM_BEAT),
    ("comp", ["comp", "0002", "0002", "0005", "0003", "0802", "0803",
              "FFF8", "FFE0", "0008", "FFF0"]),
    ("box", ["box", "-1", "10", "-68", "59", "29", "42"]),
    ("spawn", ["spawn", "04D0", "0141", "0008", "0120", "0040", "0000", "0000"]),
    ("spawn16", ["spawn", "16", "04D0", "0141", "0008", "0120", "0040",
                 "0000", "0000", "0000"]),
    ("script", ["script", "2C", "00", "05", "01", "000A"]),
    ("attack", _ATK),
    ("wof_ours", ["wof_attack", "ours"] + _WOF),
    ("wof_enemy", ["wof_attack", "enemy"] + _WOF),
    ("chain", ["chain"]),
    ("moment", ["moment"] + _FRAME),
    ("moment_atk", ["moment"] + _FRAME + _ATK),
    ("moment_comp", ["moment"] + _FRAME + _COMP),
    ("moment_all", ["moment"] + _FRAME + _ATK + _COMP),
    ("find", ["find", "攻击"]),
    ("collide4", ["collide", "4"]),
    ("collide1A", ["collide", "0x1A"]),
    ("attack_id", ["attack_id", "0x5A"]),
    ("anim_id", ["anim_id", "1", "4"]),
    ("hurt_anim", ["player_hurt_anim", "2"]),
    ("enemy_hurt_anim", ["enemy_hurt_anim", "3"]),
    ("coverage", ["coverage"]),
    ("unknown", ["unknown"]),
    ("unknown_dom", ["unknown", "player_ground_state"]),
    ("themes", ["themes"]),
    ("themes_one", ["themes", "state_machine"]),
    ("legacy", ["legacy"]),
    ("legacy_one", ["legacy", "difficulty"]),
    ("json", ["--json", "frame_type", "4"]),
    ("help", ["-h"]),
    ("noargs", []),
]


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if "--selftest" in argv:
        return cmd_selftest()
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "list":
        return cmd_list()
    if cmd == "chain":
        return cmd_chain()
    if cmd == "moment":
        return cmd_moment(rest)
    if cmd == "find":
        return cmd_find(" ".join(rest)) if rest else (print("用法：find <词>") or 1)
    if cmd == "collide":
        return cmd_collide(rest[0]) if rest else (print("用法：collide <取值>") or 1)
    if cmd == "coverage":
        return cmd_coverage()
    if cmd == "unknown":
        return cmd_unknown(rest)
    if cmd == "themes":
        return cmd_themes(rest)
    if cmd == "legacy":
        return cmd_legacy(rest)
    if cmd == "anim_id":
        return cmd_anim_id(rest)
    if cmd == "flags":
        return cmd_flags(rest[0], rest[1]) if len(rest) >= 2 else (print("用法：flags <位域> <值>") or 1)
    if cmd == "attr":
        return cmd_flags("sprite_attr", rest[0]) if rest else (print("用法：attr <hex>") or 1)
    if cmd == "frame":
        return cmd_frame(rest)
    if cmd == "anim":
        return cmd_anim(rest)
    if cmd == "comp":
        return cmd_comp(rest)
    if cmd == "box":
        return cmd_box(rest)
    if cmd == "spawn":
        return cmd_spawn(rest)
    if cmd == "script":
        return cmd_script(rest)
    if cmd == "attack":
        return cmd_attack(rest)
    if cmd == "wof_attack":
        return cmd_wof_attack(rest)
    if len(rest) == 0:
        return cmd_domain(cmd)
    return cmd_lookup(cmd, rest[0], as_json)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
