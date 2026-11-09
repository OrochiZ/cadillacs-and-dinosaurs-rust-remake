#!/usr/bin/env python3
"""取值 -> 抽象意义 的离线查询、ANI 帧解码、生成记录解码。

不读 ROM、不依赖第三方包；语义全部来自同目录 semantics.json（人工核对过的缓存），
原始数值仍回源各 SPEC / tables.txt。设计动机：看到一段 ANI / SPR / 生成记录，
就能直接知道「这一帧 / 这一条在干嘛」，而不必去翻散在各卷的文字。

用法（在任意目录）：
    python re/specs/lookup.py                          列出所有可查的域
    python re/specs/lookup.py frame_type              列出该域全部取值与意义
    python re/specs/lookup.py frame_type 4            查一个取值（支持 4 / 04 / 0x04 / 0xA）
    python re/specs/lookup.py drop_code 25            范围取值也能查（1-19 是武器 ...）
    python re/specs/lookup.py attr 0x3020              拆 SPR attr 字的各位
    python re/specs/lookup.py flags draw_flags 0x81    拆位域（域, 值）
    python re/specs/lookup.py frame 10 0A01 8000 0100 0405 1A02        解码 10 字节帧记录
    python re/specs/lookup.py frame 12 0A01 8000 0100 0405 1A02 0011    解码 12 字节帧记录
    python re/specs/lookup.py anim 10 0A01 8000 0100 0405 1A02 0A01 8000 0100 0085 1A02
                                                         把一串帧记录翻成一段动画时间线
    python re/specs/lookup.py comp 0002 0002 0005 0003 0802 0803 FFF8 FFE0 0008 FFF0
                                                         把一串 SPR composition 翻成「几块图 / 贴在哪」
    python re/specs/lookup.py box -1 10 -68 59 29 42     六个 i16 判定盒 -> 打哪儿 / 够多远
    python re/specs/lookup.py spawn 04D0 0141 0008 0120 0040 0000 0000   解码 14 字节生成记录
    python re/specs/lookup.py spawn 16 04D0 0141 0008 0120 0040 0000 0000 0000
    python re/specs/lookup.py script 2C 00 05 01 000A   解码 6 字节过场脚本记录
    python re/specs/lookup.py chain                   ANI -> SPR -> 判定框 能推断什么
    python re/specs/lookup.py find 攻击                按意义关键词反查
    python re/specs/lookup.py collide 4               只给一个取值，列出它在各域的所有意义
    python re/specs/lookup.py collide 0x1A            看同一编号在哪几张表里意思不同
    python re/specs/lookup.py attack_id 0x5A          查一个攻击编号是哪一招
    python re/specs/lookup.py anim_id 1 4             查 Jack 第 1 套第 4 段是哪一招
    python re/specs/lookup.py coverage                哪些表已转、哪些按纪律不转、为什么
    python re/specs/lookup.py themes                  按玩法主题列出可查的域
    python re/specs/lookup.py themes state_machine    只看状态机这一块
    python re/specs/lookup.py --json frame_type 4     机器可读输出
    python re/specs/lookup.py --selftest              固化自测（不依赖 ROM）

边界：本工具只回答「这个取值在这份 rep 已登记的意义里是什么」，不推断未登记取值、
不把 [I] 说成 [O]、不做跨游戏等价。未命中就直说未登记。
同一编号在玩家侧 / 敌人侧、dino / wof 侧含义可以相反，上下文相关的域会提示先确认对象。
"""
from __future__ import annotations

import contextlib
import io
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

# SPEC §3.6 只逐段列了 Jack 的前三套；第 3/4/5 套只有套级用途。
SET_DOMAINS = {0: "jack_anim_set0", 1: "jack_anim_set1", 2: "jack_anim_set2"}


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
    print("\n用 `lookup.py <域> [取值]` 查；`lookup.py chain` 看 ANI->SPR->判定框；"
          "`lookup.py spawn <记录>` 看一条生成脚本说什么。")


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
    print(f"{vv['meaning']} {fmt(vv['tag'])}" if vv else "未登记")
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
    return 0


def infer(kind, body, atk, dur, last, w0) -> list[str]:
    out = []
    fk, fv = match_value(DOMAINS["frame_type"], str(kind))
    if fv:
        out.append(f"身份：{fv['meaning']}")
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
""")
    return 0


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
    total, actives, seen_last, identities = 0, 0, False, []
    for i, off in enumerate(range(0, len(b) - stride + 1, stride)):
        rec = b[off:off + stride]
        kind, timer = rec[6], rec[7]
        dur, last = (timer & 0x7F) or 256, bool(timer & 0x80)
        body, atk = rec[8], rec[9]
        _, fv = match_value(DOMAINS["frame_type"], str(kind))
        label = fv["meaning"] if fv else "未登记"
        identities.append(label.split("：")[0].split("；")[0])
        total += dur
        if kind == 4 and atk:
            actives += 1
        print(f"  帧 {i:02d} @+{off:04X}  kind=0x{kind:02X}  {label} {fmt(fv['tag']) if fv else ''}")
        print(f"       {dur:3d} tick   body_box={body:#04x}  attack_box={atk:#04x}"
              + ("   [末帧]" if last else ""))
        if last:
            seen_last = True
            print("       末帧后紧跟的 i16 是 link word（不是帧记录），切分到此为止")
            break
    print("=" * 78)
    print(f"  这一段共 {total} tick；身份序列：{' → '.join(identities)}")
    print(f"  攻击生效帧 {actives} 个 —— 这些帧才有 +$49 与对方 +$48 相交；"
          "其余帧是起势、过渡或收招")
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
    return 0


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
            print(f"  {t['key']:20s} {t['label']}  ({len(t['domains'])} 个域)")
            print(f"  {'':20s} {t['question']}")
        print("\n用 `lookup.py themes <主题>` 看这一块有哪些域；"
              "`lookup.py <域> [取值]` 查具体意义。")
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
        print(f"  {name:24s} {d['label'] if d else '（域不存在）'}")
    print(f"\n（{len(t['domains'])} 个域；具体取值用 `lookup.py <域> [取值]` 查）")
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
    _, v = match_value(DOMAINS["combo_counter"], "3")
    ck("连段计数 3 → 终结拳", bool(v) and "终结拳" in v["meaning"])
    ck("Jack 专属表标了作用域，没写成四角色通用",
       all("Jack only" in DOMAINS[x]["scope"]
           for x in ("jack_anim_set0", "jack_anim_set1", "jack_anim_set2")))
    out = capture(cmd_collide, "3")
    ck("collide 3 现在也列出连段计数与 Jack 动画表",
       all(x in out for x in ("combo_counter", "jack_anim_set0", "jack_anim_set1")))

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

    ok = sum(1 for _, good, _ in checks if good)
    for label, good, detail in checks:
        print(f"  {'PASS' if good else 'FAIL'}  {label}" + (f"   [{detail}]" if not good and detail else ""))
    print(f"\n{ok}/{len(checks)} 通过")
    return 0 if ok == len(checks) else 1


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
    if cmd == "find":
        return cmd_find(" ".join(rest)) if rest else (print("用法：find <词>") or 1)
    if cmd == "collide":
        return cmd_collide(rest[0]) if rest else (print("用法：collide <取值>") or 1)
    if cmd == "coverage":
        return cmd_coverage()
    if cmd == "themes":
        return cmd_themes(rest)
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
    if len(rest) == 0:
        return cmd_domain(cmd)
    return cmd_lookup(cmd, rest[0], as_json)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
