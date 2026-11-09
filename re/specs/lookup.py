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
    python re/specs/lookup.py box -1 10 -68 59 29 42     六个 i16 判定盒 -> 打哪儿 / 够多远
    python re/specs/lookup.py spawn 04D0 0141 0008 0120 0040 0000 0000   解码 14 字节生成记录
    python re/specs/lookup.py spawn 16 04D0 0141 0008 0120 0040 0000 0000 0000
    python re/specs/lookup.py chain                   ANI -> SPR -> 判定框 能推断什么
    python re/specs/lookup.py find 攻击                按意义关键词反查
    python re/specs/lookup.py collide 4               只给一个取值，列出它在各域的所有意义
    python re/specs/lookup.py collide 0x1A            看同一编号在哪几张表里意思不同
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
OFFSET_KEY_DOMAINS = ("attack_field", "box_field", "wof_atk_field")


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
    ck("域数量 >= 30（ANI/SPR 之外确有扩展）", len(DOMAINS) >= 30, str(len(DOMAINS)))

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
    if cmd == "flags":
        return cmd_flags(rest[0], rest[1]) if len(rest) >= 2 else (print("用法：flags <位域> <值>") or 1)
    if cmd == "attr":
        return cmd_flags("sprite_attr", rest[0]) if rest else (print("用法：attr <hex>") or 1)
    if cmd == "frame":
        return cmd_frame(rest)
    if cmd == "anim":
        return cmd_anim(rest)
    if cmd == "box":
        return cmd_box(rest)
    if cmd == "spawn":
        return cmd_spawn(rest)
    if len(rest) == 0:
        return cmd_domain(cmd)
    return cmd_lookup(cmd, rest[0], as_json)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
