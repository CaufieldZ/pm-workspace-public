#!/bin/bash
# UserPromptSubmit hook: session 健康度 + 需求质量提醒（三项检查合一进程）
#
# 三项原本各起一个进程、各自解析 stdin / 读 transcript，而这是每次用户发消息都走的
# 热路径。合并后一次 stdin 解析、一次读盘出全部数据。三项独立判断、独立埋点——
# gate 名 context-warn / cost-warn / pm-gate-reminder 是 dashboard 聚合键，不因合并改名。
#
# 两项输出通道，按「这段话说给谁听」严格分流（写反即静默失效）：
#   systemMessage                      → 用户可见，不进 context（检查 1 / 2）
#   hookSpecificOutput.additionalContext → 注入 Claude context（检查 3）
#   additionalContext 必须嵌在 hookSpecificOutput 内；放顶层会被静默忽略，不报错。
#
# 检查项 1 · context 压力
#   数据源：末条压缩边界之后、「有缓存读」的 assistant 消息的 cache_read_input_tokens
#     —— transcript 追加式写，压缩边界不删旧行；不切边界的话，边界已落地而压缩后首条
#        assistant 消息尚未写进来时，末条缓存读仍是压缩前的旧上下文 → 刚 /compact 完就催 compact。
#   档位：首档 PMWS_CONTEXT_STEP_START（默认 300000，约 1M 的 30%），之后每
#     PMWS_CONTEXT_STEP（默认 10000）一档；**跨档才算命中，同档内不重复报**——越过首档后
#     每轮都提醒会变成噪音，但你不管它的话每涨一档会再来一次。档位靠比对「边界后末两条
#     读数」算出，不落状态文件（代价：某轮没新增读数时同一次跨档可能再报一遍）。
#   增速：边界后最近 ≤6 条（去重）cache_read 的中位差分 → 告警带「近期均 +XK/条，距 500K 约 N 条」；
#     样本 <3 条或增速 ≤0 时省略该子句（不新增告警档，增速随现有阈值告警附带）。
#
# 检查项 2 · 累计消耗（多通道 · 分时段 / 分币种）
#   数据源：assistant 消息的 usage，按 message.id 去重取末行
#     —— 同一消息会重复落 2-3 行且 usage 逐字相同（VS Code 运行时实测），
#       不去重则金额虚高数倍；末行值 = 该消息真值。
#   通道解析（逐消息按 model 归通道，混 session 的历史段各归各的）：
#     · provider 归属：会话 env 的 ANTHROPIC_AUTH_TOKEN 与 cc-switch db 各条目的 token
#       做 sha256 比对（精确到条目）；未命中按 base_url 匹配（同 URL 多家取 is_current）；
#       仍未命中且 base_url = 配置里标记 legacy_base_url 的值 → 该通道；都不可解析 → 不计。
#     · claude* → USD 通道（价目读 cc-switch model_pricing = models.dev 同步表，含缓存写）；
#       deepseek 系 → CNY 通道（价目表按「模型前缀 → 价目」最长匹配，未列模型不计）。
#       缓存写按 cache_write_rate 计：数字 = 相对输入价的倍数，也认 'in' / 'cache_read'
#       两个别名，模型级优先于通道级；站点 deepseek 系价目行不给这个倍率，按站点全局默认
#       1.25——按输入价计会少算 20%。
#       高峰 ×2 要四个条件同时成立：peak.enabled、模型在 peak.models 前缀名单内（缺省 = 全体）、
#       消息时间落在 peak.hours × peak.weekdays 内、当天不在放假日表（peak.holidays_file）。
#       峰谷判的是「交易所日历」。两套日历交叉后**塌缩成一项**：交易所从不在调休补班的周末
#       开门，所以「交易所日历 ∩ 国务院日历」= weekday() ∈ 周一~周五 且 日期 ∉ 放假日表——
#       一张节假日表 + 一个 weekday 判断，没有第二份日历要维护。补班日靠 weekday 就被排除，
#       不必入表；表里只查「放假日」成员资格，绝不拿数据源的「工作日」标记（两者相反）。
#       提示里的「当前高峰时段」同样按本 session 实际计价的模型判定——纯 claude session
#       在高峰时段不会被标成 2 倍价。
#       节假日表读不到 / 未覆盖某年时不静默按无节假日判，出口自报口径缺口（见 NOTE_TAG）。
#   价目 / 通道映射 / 档位全部在 .claude/hooks/cost-config.json（PMWS_COST_CONFIG 覆盖；
#     配置缺失 → 本项静默跳过）——改价 / 加通道只改配置，不动本文件。
#   触发：分币种各按档位（默认 ¥5 / $5；PMWS_COST_STEP_MICRO / PMWS_COST_STEP_USD_MICRO
#     或配置 steps 覆盖）。金额本身即节流——同档内不重复报；跳档也只报一次。
#   附 · 账户真实余额：只在真要报金额时取一次（热路径多数时候不付这个成本），走
#     scripts/relay_balance.py --provider <计价通道指向的 provider>。取不到（没 .env /
#     网络失败 / 令牌失效）就整段省掉，金额照报；WARN_BALANCE=0 关掉本段。
#
# 检查项 3 · 模糊需求（走 additionalContext，注入模型）
#   触发：prompt 同时满足——含产出物关键词 / 含量化动词 / 剥掉非指标数字后仍无数字
#   节流：10 分钟一次（_dedup_if_fresh）
#   措辞：必须写成事实陈述。写成祈使的系统指令会触发 Claude 的 prompt-injection
#     防御，导致 Claude 把这段文字展示给用户而非当作 context 吸收——症状等同于失效。
#   只依赖 prompt，不依赖 transcript（transcript 缺失时本项照常工作）。

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/dedup.sh"

INPUT=$(cat)
hook_parse_all

# ── 检查项 3：模糊需求（只需要 prompt，放在 transcript 门之前）──────────
PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // ""' 2>/dev/null)
PM_HIT=0
PM_MSG=""

if [ -n "$PROMPT" ]; then
  # 条件 1：含产出物关键词（case 粗筛，用超集，宁 over 勿 under）
  case "$PROMPT" in
    *PRD*|*需求*|*场景清单*|*scene-list*|*scene.list*)
      # 条件 2：含量化动词
      case "$PROMPT" in
        *优化*|*提升*|*改善*|*增加*|*降低*|*完善*|*增强*|*调整*|*减少*|*提高*|*加速*|*缩短*)
          # 条件 3：剥掉非指标数字（季度 / 版本 / 场景号 / 优先级 / 排期）后仍无数字
          #   → 视为未给量化目标。「含任意数字」不足以证明已给目标。
          PROMPT_METRIC=$(printf '%s' "$PROMPT" | sed -E \
            -e 's/[0-9]{0,4}[Qq][1-4]//g' \
            -e 's/[vV][0-9]+(\.[0-9]+)*//g' \
            -e 's/[A-Z]-[0-9]+[a-z]?//g' \
            -e 's/[Pp][0-9]//g' \
            -e 's/[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}//g' \
            -e 's/[0-9]{1,2}月([0-9]{1,2}日?)?//g')
          case "$PROMPT_METRIC" in
            *[0-9]*) ;;                                        # 有真指标数字 → 不提醒
            *) _dedup_if_fresh pm-gate-reminder 600 "global" || PM_HIT=1 ;;
          esac
          ;;
      esac
      ;;
  esac
fi

if [ "$PM_HIT" = "1" ]; then
  # 事实陈述，非祈使指令——见文件头「措辞」条
  # gate 名保留为来源标注（测试锚点 + 让模型知道出处），但写成陈述句而非方括号指令标签
  PM_MSG="本条需求描述里出现了「优化 / 提升 / 增加」这类动词，但没有出现可验证的数字目标。按本工区的 PM-GATE 约定，Viability 一项需要「核心指标 + 具体数字 + 成功边界值」三件齐备；baseline 已含结论、改动 ≤1 场景、方案型项目这三种情形除外。（本条来自工区 pm-gate-reminder 检查）"
fi

# ── 检查项 1 / 2：需要 transcript ──────────────────────────────────────
CTX_HIT=0
COST_HIT=0
MSG=""

if [ -f "$HOOK_TRANSCRIPT" ]; then
  # 输出一行（空格分隔，30 字段）：
  #   <末条缓存读> <¥微元> <$微元> <¥输入> <¥输出> <¥缓存读> <$输入> <$输出> <$缓存读> <$缓存写>
  #   <¥输入tok> <¥输出tok> <¥缓存读tok> <$输入tok> <$输出tok> <$缓存读tok> <$缓存写tok>
  #   <命中率%> <当前高峰 0/1> <cost可用 0/1> <¥档位> <$档位>
  #   <context增速tok/条> <距下一档条数（-1=不可估算）> <context跨档 0/1> <下一档线tok>
  #   <余额 provider，无 = -> <推定档通道，无 = -> <未计价条数>
  #   <节假日口径缺口：- 无 / unreadable 表读不到 / 年份列表 未覆盖（该年峰谷按周一~周五判）>
  STATS=$(HOOK_TRANSCRIPT="$HOOK_TRANSCRIPT" PMWS_COST_CONFIG="${PMWS_COST_CONFIG:-${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/cost-config.json}" python3 <<'PY' 2>/dev/null
import json, os, datetime, hashlib, sqlite3

# Asia/Shanghai 无夏令时（1991 年起），固定 UTC+8，免依赖 tzdata
SH = datetime.timezone(datetime.timedelta(hours=8))
DEFAULT_PEAK_HOURS = {9, 10, 11, 14, 15, 16, 17}
DEFAULT_PEAK_DAYS = {0, 1, 2, 3, 4}   # 周一…周五（Python weekday）；站点那侧写 1=周一…7=周日

# 价目 / 通道 / 档位全部来自配置文件；缺失 → 本项静默跳过（改价改配置，不动本代码）
try:
    CFG = json.load(open(os.environ.get("PMWS_COST_CONFIG") or "", encoding="utf-8"))
    if not isinstance(CFG, dict):
        CFG = {}
except Exception:
    CFG = {}
CHANNELS = [c for c in (CFG.get("channels") or []) if isinstance(c, dict)]

PCFG = CFG.get("peak") or {}
try:
    PEAK_HOURS = set(int(h) for h in (PCFG.get("hours") or DEFAULT_PEAK_HOURS))
except Exception:
    PEAK_HOURS = set(DEFAULT_PEAK_HOURS)
try:
    PEAK_DAYS = set(int(d) for d in (PCFG.get("weekdays") or DEFAULT_PEAK_DAYS))
except Exception:
    PEAK_DAYS = set(DEFAULT_PEAK_DAYS)
try:
    PEAK_MULT = float(PCFG.get("multiplier") or 2)
except Exception:
    PEAK_MULT = 2.0
PEAK_ENABLED = PCFG.get("enabled", True)
PEAK_MODELS = [str(p) for p in PCFG["models"]] if "models" in PCFG else None  # None = 全体适用

# ── 放假日表（「交易所日历」判定的前提）──
# 只认「放假日」成员资格；数据源的「工作日」标记语义相反（调休补班的周六日在那里是工作日，
# 但在峰谷口径下仍算低谷），拿错标记等于把补班日错判成高峰。表声明了却读不到 → 出声，
# 不静默按「没有节假日」判（那是把错判藏起来）。
HOL_FILE = PCFG.get("holidays_file") or ""
HOL_MODE = str(PCFG.get("holidays_mode") or "")
HOL_ON = bool(HOL_FILE) and HOL_MODE != "ignore"
HOLIDAYS = set()
HOL_YEARS = set()
HOL_BAD = False          # 表声明了但读不出 / 空表
HOL_UNCAL = set()        # 有计价消息落在表未覆盖的年份
if HOL_ON:
    _cfgp = os.environ.get("PMWS_COST_CONFIG") or ""
    _holp = HOL_FILE if os.path.isabs(HOL_FILE) else os.path.join(os.path.dirname(_cfgp), HOL_FILE)
    try:
        _hd = json.load(open(_holp, encoding="utf-8"))
        for _y, _days in (_hd.get("off_days") or {}).items():
            HOL_YEARS.add(str(_y))
            for _d in _days:
                HOLIDAYS.add(str(_d))
        HOL_BAD = not HOLIDAYS
    except Exception:
        HOL_BAD = True

# ── 会话 provider 解析：token 哈希 → base_url（legacy 兜底在 channel_for 里）──
DB = os.path.expanduser(os.environ.get("PMWS_CCSWITCH_DB") or CFG.get("ccswitch_db") or "~/.cc-switch/cc-switch.db")
TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN") or ""
BASE = os.environ.get("ANTHROPIC_BASE_URL") or ""

PROV = None       # cc-switch provider 名；解析失败为 None
USD_PRICING = {}  # model_id → (输入, 输出, 缓存读, 缓存写) 每 1M USD
try:
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    rows = con.execute(
        "SELECT name, is_current, json_extract(settings_config,'$.env.ANTHROPIC_AUTH_TOKEN'),"
        " json_extract(settings_config,'$.env.ANTHROPIC_BASE_URL')"
        " FROM providers WHERE app_type='claude'").fetchall()
    if TOKEN:
        th = hashlib.sha256(TOKEN.encode()).hexdigest()
        for nm, cur, tk, bu in rows:
            if tk and hashlib.sha256(str(tk).encode()).hexdigest() == th:
                PROV = nm
                break
    if PROV is None and BASE:
        same = [(nm, cur) for nm, cur, tk, bu in rows if bu == BASE]
        if len(same) == 1:
            PROV = same[0][0]
        elif len(same) > 1:
            on = [nm for nm, c in same if c]
            if len(on) == 1:
                PROV = on[0]
    for mid, i, o, cr, cw in con.execute(
            "SELECT model_id, input_cost_per_million, output_cost_per_million,"
            " cache_read_cost_per_million, cache_creation_cost_per_million FROM model_pricing"):
        try:
            USD_PRICING[mid] = (float(i), float(o), float(cr), float(cw or 0))
        except Exception:
            pass
    con.close()
except Exception:
    pass

def _models_match(ch, model):
    if any(model.startswith(p) for p in (ch.get("models") or [])):
        return True
    rates = ch.get("rates_off_peak")
    return isinstance(rates, dict) and any(model.startswith(p) for p in rates)


def _cny_rate(ch, model):
    """通道内按「模型前缀 → 价目」最长匹配；未列模型返回 None（不计）。"""
    rates = ch.get("rates_off_peak") or {}
    best = None
    for prefix, r in rates.items():
        if isinstance(r, dict) and model.startswith(prefix) and (best is None or len(prefix) > len(best)):
            best = prefix
    return rates[best] if best else None

def channel_for(model):
    """模型 → (通道, 是否推定档)。推定 = token 没登记，靠 base_url 兜的档——提示里要标注，
    否则一个猜出来的价会以事实的口吻报出去。"""
    # 1) 模型可计的通道里 provider 名吻合者优先（token 命中即实际在打的通道）
    cands = [c for c in CHANNELS if _models_match(c, model)]
    if PROV:
        for c in cands:
            if PROV in (c.get("provider_names") or []):
                return c, False
    # 2) USD 通道兜底（claude 家族：混 session 里的历史段）
    for c in cands:
        if c.get("currency") == "USD":
            return c, False
    # 3) 落到 legacy_base_url 与当前 env 相符的通道（deepseek 家族默认档；支持多值——端点随地区切）
    for c in cands:
        lb = c.get("legacy_base_url")
        if lb and BASE in (lb if isinstance(lb, list) else [lb]):
            return c, True
    return None, False

def usd_rate(model):
    if model in USD_PRICING:
        return USD_PRICING[model]
    best = None
    for mid, r in USD_PRICING.items():
        if model.startswith(mid) or mid.startswith(model):
            if best is None or len(mid) > len(best[0]):
                best = (mid, r)
    return best[1] if best else None

def _holiday_blocks(dt):
    """该日是否因放假日而全天低谷；顺带记下「表没覆盖的年份」供出口自报。

    表读不到（HOL_BAD）时返回 False——判定退回「只按周几」，缺口由 HOL_BAD 自报，
    不在这里装成「查过了没问题」。
    """
    if not HOL_ON or HOL_BAD:
        return False
    if dt.date().isoformat() in HOLIDAYS:
        return True
    if str(dt.year) not in HOL_YEARS:
        HOL_UNCAL.add(dt.year)
    return False


def _in_peak(dt, model):
    """高峰四件套缺一不可：总开关、模型名单、时段（小时 × 周几）、非放假日。"""
    if not PEAK_ENABLED:
        return False
    if PEAK_MODELS is not None and not any(model.startswith(p) for p in PEAK_MODELS):
        return False
    if not (dt.weekday() in PEAK_DAYS and dt.hour in PEAK_HOURS):
        return False
    return not _holiday_blocks(dt)


def _is_peak(ts, model):
    if not ts:
        return False
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(SH)
    except Exception:
        return False
    return _in_peak(dt, model)


def _cache_write_mult(chan, rate):
    """缓存写倍率：模型级 → 通道级 → 按输入价（返回 None）。

    数字 = 相对输入价的倍数（站点 1.25）；'cache_read' 单列；'in' / 缺省 = 按输入价。
    数字不认的话，配置里写 1.25 会被静默当成 1.0（少算 20%），静默分叉比算错更难查。
    """
    v = rate.get("cache_write_rate")
    if v is None:
        v = chan.get("cache_write_rate")
    if v == "cache_read":
        return "cache_read"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return None

try:
    lines = open(os.environ["HOOK_TRANSCRIPT"], encoding="utf-8", errors="replace").readlines()
except Exception:
    raise SystemExit(0)

# ── 采集：压缩边界切 context 读数；usage 行按 message.id 去重（末行覆盖取真值）──
last_cr = 0
boundary_idx = 0        # 最后压缩边界时的消息数——边界后的消息用于 context 增速
msgs = {}
order = []
for line in lines:
    # 压缩边界：边界之前记的是压缩前的上下文大小，不能拿来判当前压力。
    # 粗筛命中才解析——工具结果里提到 compact_boundary 的行 subtype 为空，不会误清。
    if '"compact_boundary"' in line:
        try:
            if json.loads(line).get("subtype") == "compact_boundary":
                last_cr = 0
                boundary_idx = len(order)
        except Exception:
            pass
    # 热路径粗筛：绝大多数 entry（attachment / queue-operation / snapshot）不含 usage，先跳过再解析
    if '"usage"' not in line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("type") != "assistant":
        continue
    m = d.get("message") or {}
    u = m.get("usage")
    if not isinstance(u, dict):
        continue
    cr = u.get("cache_read_input_tokens") or 0
    if cr > 0:
        last_cr = cr          # 最后一次赋值 = 最近一条有缓存读的消息
    mid = m.get("id") or "__n%d" % len(order)
    if mid not in msgs:
        order.append(mid)
    msgs[mid] = (m.get("model") or "", d.get("timestamp"),
                 u.get("input_tokens") or 0, u.get("output_tokens") or 0,
                 cr, u.get("cache_creation_input_tokens") or 0)

# ── 逐消息计价（去重后）──
cny = [0.0, 0.0, 0.0]        # ¥ 输入 / 输出 / 缓存读（缓存写按 cache_write_rate 并入输入）
usd = [0.0, 0.0, 0.0, 0.0]   # $ 输入 / 输出 / 缓存读 / 缓存写
tin_c = tout_c = tcr_c = 0
tin_u = tout_u = tcr_u = tcw_u = 0
cost_ok = False
bal_prov = "-"               # 计价通道指向的 provider（余额查询用）；无 = 取不到余额
peak_used = False            # 本 session 有计价消息落在高峰名单内——「当前高峰时段」提示成立的前提
assumed_chan = ""            # 推定档的通道名（token 未登记时靠 base_url 兜的那个）
skipped = 0                  # 占着 token 却没进合计的条数——如实报出来，别让金额冒充全量

for mid in order:
    model, ts, i, o, cr, cw = msgs[mid]
    ch, is_assumed = channel_for(model)
    if ch is None:
        if i or o or cr or cw:
            skipped += 1
        continue
    if ch.get("currency") == "CNY":
        r = _cny_rate(ch, model)
        if r is None:
            if i or o or cr or cw:
                skipped += 1
            continue
        # 只有真计上价的条目才代表「这场会按高峰价花钱」/「这个站取得到余额」
        peak_used = peak_used or PEAK_MODELS is None or any(
            model.startswith(p) for p in PEAK_MODELS)
        if ch.get("provider"):
            bal_prov = str(ch["provider"])
        if is_assumed and not assumed_chan:
            assumed_chan = str(ch.get("id") or "")
        mult = PEAK_MULT if _is_peak(ts, model) else 1.0
        pin = float(r.get("in") or 0) * mult
        pout = float(r.get("out") or 0) * mult
        rate_cr = float(r.get("cache_read") or 0) * mult
        cwr = _cache_write_mult(ch, r)
        pcw = rate_cr if cwr == "cache_read" else (pin * cwr if cwr is not None else pin)
        cny[0] += (i * pin + cw * pcw) / 1000000.0
        cny[1] += o * pout / 1000000.0
        cny[2] += cr * rate_cr / 1000000.0
        tin_c += i + cw; tout_c += o; tcr_c += cr
        cost_ok = True
    elif ch.get("currency") == "USD":
        rate = usd_rate(model)
        if rate is None:
            if i or o or cr or cw:
                skipped += 1
            continue
        peak_used = peak_used or PEAK_MODELS is None or any(
            model.startswith(p) for p in PEAK_MODELS)
        if ch.get("provider"):
            bal_prov = str(ch["provider"])
        if is_assumed and not assumed_chan:
            assumed_chan = str(ch.get("id") or "")
        pin, pout, pcr, pcw = rate
        usd[0] += i * pin / 1000000.0
        usd[1] += o * pout / 1000000.0
        usd[2] += cr * pcr / 1000000.0
        usd[3] += cw * pcw / 1000000.0
        tin_u += i; tout_u += o; tcr_u += cr; tcw_u += cw
        cost_ok = True

if not order:
    raise SystemExit(0)

# ── context 档位 + 增速 ──
# 档位：首档起每 step 一档，跨档才算命中（同档不重复报，防越线后每轮刷屏）。
# 「下一档」同时充当增速子句的终点——指着下一档比指某个固定值可行动。
try:
    CTX_START = int(float(os.environ.get("PMWS_CONTEXT_STEP_START") or 300000))
except Exception:
    CTX_START = 300000
try:
    CTX_STEP = int(float(os.environ.get("PMWS_CONTEXT_STEP") or 10000))
except Exception:
    CTX_STEP = 10000
if CTX_STEP <= 0:
    CTX_STEP = 10000


def _rung(n):
    """n 落在第几档：不到首档 = 0。"""
    return 0 if n < CTX_START else 1 + (n - CTX_START) // CTX_STEP


ctx_seq = [x for x in (msgs[mid][4] for mid in order[boundary_idx:]) if x > 0]
ctx_prev = ctx_seq[-2] if len(ctx_seq) >= 2 else 0
ctx_hit = 1 if _rung(last_cr) > _rung(ctx_prev) else 0
ctx_next = (CTX_START if last_cr < CTX_START
            else CTX_START + ((last_cr - CTX_START) // CTX_STEP + 1) * CTX_STEP)

# 增速：边界后最近 ≤6 条（去重）cache_read 的中位差分 → 距下一档的估计条数
win = ctx_seq[-6:]
dcr = 0
eta = -1
if len(win) >= 3:
    diffs = sorted(win[i] - win[i - 1] for i in range(1, len(win)))
    dcr = max(0, diffs[len(diffs) // 2])
    if dcr > 0 and last_cr < ctx_next:
        eta = max(1, (ctx_next - last_cr) // dcr)

micro = round(sum(cny) * 1000000)
usd_micro = round(sum(usd) * 1000000)
if not cost_ok:
    micro = 0
    usd_micro = 0

def _step(env_name, cfg_key, dflt):
    raw = os.environ.get(env_name) or (CFG.get("steps") or {}).get(cfg_key) or dflt
    try:
        v = int(float(raw))
        return v if v > 0 else dflt
    except Exception:
        return dflt

step_c = _step("PMWS_COST_STEP_MICRO", "cny_micro", 5000000)
step_u = _step("PMWS_COST_STEP_USD_MICRO", "usd_micro", 5000000)
cny_step = micro // step_c
usd_step = usd_micro // step_u

def _tok(x):
    if x < 1000:
        return str(x)
    if x < 1000000:
        return f"{x / 1000:.0f}K"
    return f"{x / 1000000:.1f}M"

# 缓存命中率 = 缓存读 / 全部输入（输入 + 缓存读，两通道合计）；与成本无关，纯 token 比例
in_side = tin_c + tcr_c + tin_u + tcr_u
hit = round((tcr_c + tcr_u) * 100 / in_side) if in_side > 0 else 0

now = datetime.datetime.now(SH)
# 「当前高峰时段（2 倍价）」只在本 session 真按高峰价计过费时才成立——纯 claude session
# 落在高峰时段也是原价，标 2 倍价会把人往错误的方向推（改时段 / 改模型都是白改）。
# 今天若是放假日同样不成立——放假日在峰谷口径下全天低谷，此时劝人「避开高峰」是白劝。
now_peak = 1 if (PEAK_ENABLED and peak_used
                 and now.weekday() in PEAK_DAYS and now.hour in PEAK_HOURS
                 and not _holiday_blocks(now)) else 0
if HOL_BAD:
    hol_field = "unreadable"
elif HOL_UNCAL:
    hol_field = ",".join(str(y) for y in sorted(HOL_UNCAL))
else:
    hol_field = "-"

print(f"{last_cr} {micro} {usd_micro} {round(cny[0] * 1e6)} {round(cny[1] * 1e6)} {round(cny[2] * 1e6)}"
      f" {round(usd[0] * 1e6)} {round(usd[1] * 1e6)} {round(usd[2] * 1e6)} {round(usd[3] * 1e6)}"
      f" {_tok(tin_c)} {_tok(tout_c)} {_tok(tcr_c)} {_tok(tin_u)} {_tok(tout_u)} {_tok(tcr_u)} {_tok(tcw_u)}"
      f" {hit} {now_peak} {1 if cost_ok else 0} {cny_step} {usd_step} {dcr} {eta} {ctx_hit} {ctx_next}"
      f" {bal_prov} {assumed_chan or '-'} {skipped} {hol_field}")
PY
)

  if [ -n "$STATS" ]; then
    read -r LAST_CR MICRO USD_MICRO C_IN C_OUT C_CACHE U_IN U_OUT U_CR U_CW TI TO TC TIU TOU TCRU TCWU HIT NOW_PEAK COST_OK CNY_STEP USD_STEP DCR ETA CTX_RUNG_HIT CTX_NEXT BAL_PROV ASSUMED_CHAN SKIPPED HOL_FIELD <<<"$STATS"

    # 检查项 1：context 压力（档位制——跨档才算命中，同档不重复报）
    if [ "${CTX_RUNG_HIT:-0}" = "1" ]; then
      CTX_HIT=1
      CTX_K=$(( LAST_CR / 1000 ))
      CTX_PCT=$(( LAST_CR * 100 / 1000000 ))
    fi

    # 检查项 2：累计消耗（¥ / $ 两档独立记步；金额本身即节流）
    if [ "$COST_OK" = "1" ]; then
      if [ "${CNY_STEP:-0}" -ge 1 ] || [ "${USD_STEP:-0}" -ge 1 ]; then
        # 档位状态：每 session 一个文件，记已报过的最高档（「¥档 $档」两个数）
        STATE_DIR="${TMPDIR:-/tmp}/pmws_cost_step"
        if mkdir -p "$STATE_DIR" 2>/dev/null; then
          STATE="$STATE_DIR/$(printf '%s' "${CLAUDE_CODE_SESSION_ID:-global}" | cksum | cut -d' ' -f1)"
          LAST=$(cat "$STATE" 2>/dev/null)
          LAST_CNY=0; LAST_USD=0
          case "$LAST" in
            *" "*) LAST_CNY="${LAST%% *}"; LAST_USD="${LAST##* }" ;;
            *[!0-9]*|"") ;;               # 空 / 脏值 → 归零
            *) LAST_CNY="$LAST" ;;        # 旧单值格式（历史残留）：按 ¥ 档恢复
          esac
          case "$LAST_CNY" in ''|*[!0-9]*) LAST_CNY=0 ;; esac
          case "$LAST_USD" in ''|*[!0-9]*) LAST_USD=0 ;; esac
          if [ "$CNY_STEP" -gt "$LAST_CNY" ] || [ "$USD_STEP" -gt "$LAST_USD" ]; then
            printf '%s %s' "$CNY_STEP" "$USD_STEP" > "$STATE"
            COST_HIT=1
          fi
        fi
      fi
    fi

    # 检查项 2 附 · 账户真实余额。只在这次真要报金额时才取——热路径上多数时候不付这个
    # 成本。按本 session 计价通道指向的 provider 取（config 里没写 provider 的通道取不到，
    # 直接省掉）。取不到（没 .env / 网络失败 / 令牌失效）同样整段省掉，金额照报。
    if [ "$COST_HIT" = "1" ] && [ "${WARN_BALANCE:-1}" != "0" ] && [ -n "${BAL_PROV:-}" ] && [ "$BAL_PROV" != "-" ]; then
      if [ -n "${WARN_BALANCE_CMD:-}" ]; then
        # 交给 bash -c 执行而不是未加引号展开：后者会把命令里的引号/空格原样落进字段
        # （'echo "28.10 1"' 的 BAL 会变成 `"28.10`），把结果弄脏。测试用这个入口注入桩。
        read -r BAL BAL_LOW <<<"$(bash -c "$WARN_BALANCE_CMD" 2>/dev/null | head -1)"
      else
        read -r BAL BAL_LOW <<<"$(RELAY_HTTP_TIMEOUT="${RELAY_HTTP_TIMEOUT:-2}" \
          python3 "${CLAUDE_PROJECT_DIR:-$(pwd)}/scripts/relay_balance.py" --provider "$BAL_PROV" 2>/dev/null \
          | head -1)"
      fi
      # 余额必须形如 12 / 12.34（可带负号，欠费时余额就是负的）——用 bash 原生正则而不是
      # case 模式：case 的 `*..*` 挡得住 ".."，挡不住 "1.2.3"。不合规就整段丢弃，
      # 「stdout 只有一行 JSON」的契约不能被余额内容破坏。BAL_LOW 只认字面 1。
      [[ "$BAL" =~ ^-?[0-9]+(\.[0-9]{1,2})?$ ]] || { BAL=""; BAL_LOW=0; }
      case "$BAL_LOW" in 1) BAL_LOW=1 ;; *) BAL_LOW=0 ;; esac
    fi
  fi
fi

[ "$CTX_HIT" = "0" ] && [ "$COST_HIT" = "0" ] && [ "$PM_HIT" = "0" ] && exit 0

# ── 组装提示文案 ──────────────────────────────────────────────────────
# 微元 → ¥X.YY / $X.XXXX（整数运算，避免浮点）
_yuan() { printf '%d.%02d' $(( $1 / 1000000 )) $(( $1 % 1000000 / 10000 )); }
_usd()  { printf '%d.%04d' $(( $1 / 1000000 )) $(( $1 % 1000000 / 100 )); }

CNY_TXT=""
USD_TXT=""
[ "${MICRO:-0}" -gt 0 ] && CNY_TXT="¥$(_yuan "$MICRO")"
[ "${USD_MICRO:-0}" -gt 0 ] && USD_TXT="\$$(_usd "$USD_MICRO")"

CTX_PACE=""
if [ "${DCR:-0}" -ge 1000 ] && [ "${ETA:-0}" -gt 0 ]; then
  CTX_PACE=" · 近期均 +$(( DCR / 1000 ))K/条，距 $(( ${CTX_NEXT:-0} / 1000 ))K 约 ${ETA} 条"
fi

# 余额段（取不到就整段没有——空 BAL 即省略）
BAL_TAG=""
if [ -n "${BAL:-}" ]; then
  if [ "${BAL_LOW:-0}" = "1" ]; then
    BAL_TAG=" · 余额 ¥$BAL ⚠️ 偏低"
  else
    BAL_TAG=" · 余额 ¥$BAL"
  fi
fi

# 口径不完整的三个标注：推定档（价是猜的）+ 未计价条数（有 token 没进合计）+
# 节假日缺口（峰谷是只按周几猜的）。金额本身即事实，但不完整的口径必须自己说出来——
# 否则数字会被当成全量。
NOTE_TAG=""
[ -n "${ASSUMED_CHAN:-}" ] && [ "$ASSUMED_CHAN" != "-" ] && \
  NOTE_TAG=" · 按 ${ASSUMED_CHAN} 价（key 未登记）"
[ "${SKIPPED:-0}" -ge 1 ] && NOTE_TAG="$NOTE_TAG · 另有 ${SKIPPED} 条未计价"
case "${HOL_FIELD:-}" in
  ""|"-") ;;
  unreadable) NOTE_TAG="$NOTE_TAG · 节假日表读不到（峰谷按周一~周五判）" ;;
  *) NOTE_TAG="$NOTE_TAG · 节假日表未覆盖 ${HOL_FIELD}（该年峰谷按周一~周五判）" ;;
esac

if [ "$CTX_HIT" = "1" ] && [ "$COST_HIT" = "1" ]; then
  # 两项都命中：合成一句，数字 → 数字 → 数字 → 动作
  PEAK_TAG=""
  [ "$NOW_PEAK" = "1" ] && PEAK_TAG=" · 高峰价"
  AMT="$CNY_TXT"
  if [ -n "$USD_TXT" ]; then
    if [ -n "$AMT" ]; then AMT="$AMT + $USD_TXT"; else AMT="$USD_TXT"; fi
  fi
  MSG="⚠️💰 context ${CTX_K}K（${CTX_PCT}%）${CTX_PACE} · 已花 ${AMT}${BAL_TAG} · 命中率 ${HIT}%${PEAK_TAG}${NOTE_TAG} ｜ 建议 /compact"
elif [ "$CTX_HIT" = "1" ]; then
  MSG="⚠️ context 缓存读取 ${CTX_K}K token（~${CTX_PCT}% of 1M）${CTX_PACE}，建议 /compact 一次（手动 compact 质量优于自动）"
elif [ "$COST_HIT" = "1" ]; then
  # 分列顺序 = 账单列顺序（输入 / 输出 / 缓存读 / 缓存写），便于对账
  PEAK_TAG=""
  [ "$NOW_PEAK" = "1" ] && PEAK_TAG=" · 当前高峰时段（2 倍价）"
  if [ -n "$USD_TXT" ] && [ -z "$CNY_TXT" ]; then
    MSG="💰 本 session 累计 \$$(_usd "$USD_MICRO")（输入 \$$(_usd "$U_IN")/${TIU} · 输出 \$$(_usd "$U_OUT")/${TOU} · 缓存读 \$$(_usd "$U_CR")/${TCRU} · 缓存写 \$$(_usd "$U_CW")/${TCWU} · 命中率 ${HIT}%）${PEAK_TAG}${BAL_TAG}${NOTE_TAG}"
  elif [ -n "$USD_TXT" ]; then
    MSG="💰 本 session 累计 ¥$(_yuan "$MICRO") + \$$(_usd "$USD_MICRO")（¥ 输入 ¥$(_yuan "$C_IN")/${TI} · 输出 ¥$(_yuan "$C_OUT")/${TO} · 缓存读 ¥$(_yuan "$C_CACHE")/${TC} ｜ \$ 输入 \$$(_usd "$U_IN")/${TIU} · 输出 \$$(_usd "$U_OUT")/${TOU} · 缓存读 \$$(_usd "$U_CR")/${TCRU} · 缓存写 \$$(_usd "$U_CW")/${TCWU} · 命中率 ${HIT}%）${PEAK_TAG}${BAL_TAG}${NOTE_TAG}"
  else
    MSG="💰 本 session 累计 ¥$(_yuan "$MICRO")（输入 ¥$(_yuan "$C_IN")/${TI} · 输出 ¥$(_yuan "$C_OUT")/${TO} · 缓存读 ¥$(_yuan "$C_CACHE")/${TC} · 命中率 ${HIT}%）${PEAK_TAG}${BAL_TAG}${NOTE_TAG}"
  fi
fi

# ── 输出：两条通道分别走自己的字段 ─────────────────────────────────────
# stdout 必须只有这一行 JSON（多余一行 → JSON 校验失败整条被丢）
if [ -n "$MSG" ] && [ "$PM_HIT" = "1" ]; then
  jq -nc --arg msg "$MSG" --arg ctx "$PM_MSG" \
    '{systemMessage: $msg, hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $ctx}}'
elif [ "$PM_HIT" = "1" ]; then
  jq -nc --arg ctx "$PM_MSG" \
    '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $ctx}}'
else
  jq -nc --arg msg "$MSG" '{systemMessage: $msg}'
fi

# 埋点分开写：各 gate 名独立聚合，dashboard 不受合并影响
[ "$CTX_HIT" = "1" ] && log_event hook context-warn triggered "cache_read=${LAST_CR}"
[ "$COST_HIT" = "1" ] && log_event hook cost-warn triggered "micro=${MICRO} usd_micro=${USD_MICRO} cny_step=${CNY_STEP} usd_step=${USD_STEP} hit=${HIT} peak=${NOW_PEAK} bal=${BAL:-miss} bal_low=${BAL_LOW:-0} assumed=${ASSUMED_CHAN:-none} skipped=${SKIPPED:-0}"
[ "$PM_HIT" = "1" ] && log_event hook pm-gate-reminder triggered "prompt_len=${#PROMPT}"

exit 0
