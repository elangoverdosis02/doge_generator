import os
import json
import time
import random
import string
import threading
import requests

from urllib.parse import urljoin
from datetime import datetime, timedelta, timezone
from io import StringIO


m = '\033[1;36m'
p = '\033[1;37m'
h = '\033[1;32m'
k = '\033[1;33m'
b = '\033[1;35m'
c = '\033[1;31m'
x = '\033[1;36m'
q = '\033[1;30m'
z = '\033[101m'
o = '\033[0m'



BASE_URL = os.environ.get("BASE_URL", "https://claimdoge.net").rstrip("/")
API_URL = urljoin(BASE_URL + "/", "api")
UA = os.environ.get("UA", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.0.0 Mobile Safari/537.36")

DIFFICULTY = os.environ.get("DIFFICULTY", "expert")
TILE_ORDER = os.environ.get("TILE_ORDER", "seq").lower()

OPEN_DELAY_MIN = int(os.environ.get("OPEN_DELAY_MIN", "0"))
OPEN_DELAY_MAX = int(os.environ.get("OPEN_DELAY_MAX", "0"))
BACKOFF_ERR = int(os.environ.get("BACKOFF_ERR", "30"))
MAX_GAME_LIVES = int(os.environ.get("MAX_GAME_LIVES", "6"))
MAX_TRY_START = int(os.environ.get("MAX_TRY_START", "3"))
MAX_AD_TRIES_ENERGY = int(os.environ.get("MAX_AD_TRIES_ENERGY", "3"))
MAX_AD_TRIES_CONTINUE = int(os.environ.get("MAX_AD_TRIES_CONTINUE", "2"))
WAIT_REGEN_MAX_SEC = int(os.environ.get("WAIT_REGEN_MAX_SEC", "240"))
TRAILING_DELAY = int(os.environ.get("TRAILING_DELAY", "5"))

DIV = "━" * 58
WIB = timezone(timedelta(hours = 7))
ACCOUNTS_FILE = os.environ.get("ACCOUNTS_FILE", "accounts.json")

SHOW_TIME = int(os.environ.get("SHOW_TIME", "0"))
COUNTDOWN_STEP = int(os.environ.get("COUNTDOWN_STEP", "1"))

_tls = threading.local()
PRINT_LOCK = threading.Lock()

def log(msg: str):
    with PRINT_LOCK:
        print(msg, flush = True)

def set_alias(alias: str):
    _tls.alias = alias

def get_alias():
    return getattr(_tls, "alias", "")

def _tag():
    alias = get_alias()
    if SHOW_TIME:
        base = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
        return f"{base} | {alias}" if alias else base
    return alias or datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def _clear_current_line():
    print("\r\033[K", end = "", flush = True)

def mmss(sec: int):
    sec = max(0, int(sec))
    m, s = divmod(sec, 60)
    return f"{m:02d}m : {s:02d}s"

def countdown(total_sec: int, label = "[TIMER]", clear_on_done = True):
    total = max(0, int(total_sec))
    if total <= 0:
        return
    left = total
    step = max(1, COUNTDOWN_STEP)
    while left > 0:
        m, s = divmod(left, 60)
        print(f"\r[{z}{_tag()}{o}] {label} {b}{m:02d}m : {s:02d}s {o}", end = "", flush = True)
        sleep_d = min(step, left)
        time.sleep(sleep_d)
        left -= sleep_d
    if clear_on_done:
        _clear_current_line()
    else:
        print(f"\r[{z}{_tag()}{o}] {label} 00m : 00s ")

def rand_req_id(ts_ms: int):
    abc = string.ascii_lowercase + string.digits
    return f"{ts_ms}-{''.join(random.choice(abc) for _ in range(10))}"

def post_json(sess, url, body: dict, timeout = 60):
    return sess.post(url, data = json.dumps(body, separators = (",", ":")), timeout = timeout)

def make_session(proxy_url: str = None):
    s = requests.Session()
    s.headers.update({
        "User-Agent" : UA,
        "Accept" : "*/*",
        "Origin" : BASE_URL,
        "Referer" : BASE_URL + "/",
        "X-Requested-With" : "TelegramWebApp",
        "Content-Type" : "application/json",
    })
    if proxy_url:
        s.proxies.update({"http" : proxy_url, "https" : proxy_url})
    return s

def get_user_data(sess, init_data: str):
    ts = int(time.time() * 1000)
    body = {"action" : "get_user_data", "initData" : init_data, "timestamp" : ts, "requestId" : rand_req_id(ts)}
    r = post_json(sess, API_URL, body)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, None

def mines_get_stats(sess, init_data: str):
    ts = int(time.time() * 1000)
    body = {"action" : "mines_get_stats", "initData" : init_data, "timestamp" : ts, "requestId" : rand_req_id(ts)}
    r = post_json(sess, API_URL, body)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, None

def mines_start_game(sess, difficulty: str, init_data: str):
    ts = int(time.time() * 1000)
    body = {"action" : "mines_start_game", "initData" : init_data, "timestamp" : ts, "requestId" : rand_req_id(ts), "difficulty" : difficulty}
    r = post_json(sess, API_URL, body)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, None

def mines_open_tile(sess, tile_index: int, init_data: str):
    ts = int(time.time() * 1000)
    body = {"action" : "mines_open_tile", "initData" : init_data, "timestamp" : ts, "requestId" : rand_req_id(ts), "tile_index" : int(tile_index)}
    r = post_json(sess, API_URL, body)
    j = None
    raw = r.text or ""
    try:
        j = r.json()
    except:
        pass
    return r.status_code, j, raw

def mines_watch_ad_continues(sess, init_data: str):
    ts = int(time.time() * 1000)
    body = {"action" : "mines_watch_ad_continues", "initData" : init_data, "timestamp" : ts, "requestId" : rand_req_id(ts)}
    r = post_json(sess, API_URL, body)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, None

def mines_use_continue(sess, init_data: str):
    ts = int(time.time() * 1000)
    body = {"action" : "mines_use_continue", "initData" : init_data, "timestamp" : ts, "requestId" : rand_req_id(ts)}
    r = post_json(sess, API_URL, body)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, None

def mines_watch_ad_game_lives(sess, init_data: str):
    ts = int(time.time() * 1000)
    body = {"action" : "mines_watch_ad_game_lives", "initData" : init_data, "timestamp" : ts, "requestId" : rand_req_id(ts)}
    r = post_json(sess, API_URL, body)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, None

def tile_order_25():
    order = list(range(25))
    if TILE_ORDER == "random":
        random.shuffle(order)
    return order

def safe_get(d, *path, default = None):
    cur = d
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def print_stats(stats):
    if not isinstance(stats, dict):
        return
    s = stats.get("stats") if "stats" in stats else stats
    if not isinstance(s, dict):
        return
    lives = s.get("game_lives")
    conti = s.get("continue_lives")
    streak = s.get("current_streak")
    earned = s.get("total_earned_doge") or s.get("earned_doge")
    nxt = s.get("seconds_until_next_life") or 0
    log(f"[{z}{_tag()}{o}] 📊 STATS | Lives : {k}{lives}{o} | Continue : {k}{conti}{o} | Streak : {streak} | Earned : {k}{earned}{o} DOGE")
    if isinstance(lives, int):
        log(f"[{z}{_tag()}{o}] ⚡ ENERGY | {k}{lives}{o}/{k}{MAX_GAME_LIVES}{o} " + (f"+1 in {k}{mmss(nxt)}{o}" if nxt else ""))

def ensure_game_lives(sess, init_data: str, need = 1):
    tries = 0
    while True:
        sc, st = mines_get_stats(sess, init_data)
        if isinstance(st, dict):
            s = st.get("stats") or {}
            lives = int(s.get("game_lives", 0))
            nxt = int(s.get("seconds_until_next_life") or 0)
            print_stats(st)
        else:
            lives, nxt = 0, 0

        if lives >= need:
            return True

        if tries < MAX_AD_TRIES_ENERGY:
            log(f"[{z}{_tag()}{o}] 🔄 REFILL_ENERGY | Via {m}Ads{o}")
            sc_w, jw = mines_watch_ad_game_lives(sess, init_data)
            if sc_w == 200 and isinstance(jw, dict) and jw.get("status") == "success":
                log(f"[{z}{_tag()}{o}] ✅ REFILL_ENERGY | {m}Success{o}")
            else:
                log(f"[{z}{_tag()}{o}] ❌ REFILL_ENERGY | Failed")
            time.sleep(2)
            tries += 1
            continue

        if nxt > 0 and nxt <= WAIT_REGEN_MAX_SEC:
            log(f"[{z}{_tag()}{o}] ⏸️ WAIT_ENERGY | {mmss(nxt)}")
            countdown(nxt, label = "[ENERGY]", clear_on_done = True)
            tries = 0
            continue

        log(f"[{z}{_tag()}{o}] ❌ NO_ENERGY | Lives still 0")
        return False

def get_active_game(sess, init_data: str):
    sc, st = mines_get_stats(sess, init_data)
    s = st.get("stats") if isinstance(st, dict) else {}
    if s and s.get("has_active_game"):
        return s.get("active_game"), s
    return None, s

def continue_if_needed(sess, active_game, init_data: str):
    has_bomb = bool(active_game.get("has_active_bomb"))
    continues_remaining = int(active_game.get("continues_remaining", 0))
    if not has_bomb:
        return
    if continues_remaining <= 0:
        at = 0
        while at < MAX_AD_TRIES_CONTINUE:
            log(f"[{z}{_tag()}{o}] 🔄 REFILL_CONTINUE | Via {m}Ads{o}")
            sc_w, jw = mines_watch_ad_continues(sess, init_data)
            if sc_w == 200 and isinstance(jw, dict) and jw.get("status") == "success":
                log(f"[{z}{_tag()}{o}] ✅ REFILL_CONTINUE | {m}Success{o}")
            else:
                log(f"[{z}{_tag()}{o}] ❌ REFILL_CONTINUE | Failed")
            time.sleep(2)
            at += 1
            break
    sc_c, jc = mines_use_continue(sess, init_data)
    if sc_c == 200 and isinstance(jc, dict) and jc.get("status") == "success":
        log(f"[{z}{_tag()}{o}] ✅ USE_CONTINUE | {m}Success{o}")
    else:
        log(f"[{z}{_tag()}{o}] ❌ USE_CONTINUE | Failed")
    time.sleep(1)

def pick_unopened_indices(order, revealed_tiles):
    opened = {t.get("index") for t in (revealed_tiles or []) if isinstance(t, dict) and "index" in t}
    for i in order:
        if i not in opened:
            yield i

def resume_active_game(sess, active_game, init_data: str):
    diff = active_game.get("difficulty", DIFFICULTY)
    log(f"[{z}{_tag()}{o}] 🔄 RESUME_GAME | Difficulty : {k}{diff}{o}")
    continue_if_needed(sess, active_game, init_data)
    order = tile_order_25()
    for idx in pick_unopened_indices(order, active_game.get("revealed_tiles")):
        if OPEN_DELAY_MAX > 0 or OPEN_DELAY_MIN > 0:
            countdown(random.randint(OPEN_DELAY_MIN, max(OPEN_DELAY_MIN, OPEN_DELAY_MAX)), label = "[OPEN]", clear_on_done = True)
        else:
            countdown(5, label = "[OPEN]", clear_on_done = True)

        sc_o, jo, raw = mines_open_tile(sess, idx, init_data)
        result = safe_get(jo, "result", "result")
        tile_reward = safe_get(jo, "result", "tile_reward_doge")
        total_doge = safe_get(jo, "result", "earned_doge") or safe_get(jo, "result", "current_earnings_doge")
        tiles_opened = safe_get(jo, "result", "tiles_opened")
        continues_rem = safe_get(jo, "result", "continues_remaining")

        log(DIV)
        if result == "safe":
            log(f"[{z}{_tag()}{o}] ✅ TILE_SAFE | Tile : {k}{idx}{o} | Reward : {k}{tile_reward}{o} | Total : {k}{total_doge}{o} | Opened : {k}{tiles_opened}{o}")
        elif result == "bomb":
            log(f"[{z}{_tag()}{o}] 💣 TILE_BOMB | Tile : {k}{idx}{o} | Continues : {k}{continues_rem}{o}")
        elif result == "auto_continue":
            log(f"[{z}{_tag()}{o}] 🔄 AUTO_CONTINUE | Tile : {k}{idx}{o}")
        elif result == "all_bombs_auto_cashout":
            log(f"[{z}{_tag()}{o}] 🎯 AUTO_CASHOUT | Tile : {k}{idx}{o} | Total : {k}{total_doge}{o}")
        else:
            log(f"[{z}{_tag()}{o}] ❓ UNKNOWN_RESULT | Tile : {k}{idx}{o} | Result : {result}")

        if sc_o >= 400 or not isinstance(jo, dict):
            log(f"[{z}{_tag()}{o}] ❌ OPEN_ERROR | {str(raw)[:300]}")
            countdown(BACKOFF_ERR, label = "[BACKOFF]", clear_on_done = True)
            continue

        if result in ("safe", "auto_continue"):
            if TRAILING_DELAY > 0:
                countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)
            continue

        if result == "bomb":
            if isinstance(continues_rem, int) and continues_rem <= 0:
                log(f"[{z}{_tag()}{o}] 🔄 REFILL_CONTINUE | Via {m}Ads{o}")
                sc_w, jw = mines_watch_ad_continues(sess, init_data)
                if sc_w == 200 and isinstance(jw, dict) and jw.get("status") == "success":
                    log(f"[{z}{_tag()}{o}] ✅ REFILL_CONTINUE | {m}Success{o}")
                else:
                    log(f"[{z}{_tag()}{o}] ❌ REFILL_CONTINUE | Failed")
                time.sleep(2)
            sc_c, jc = mines_use_continue(sess, init_data)
            if sc_c == 200 and isinstance(jc, dict) and jc.get("status") == "success":
                log(f"[{z}{_tag()}{o}] ✅ USE_CONTINUE | {m}Success{o}")
            else:
                log(f"[{z}{_tag()}{o}] ❌ USE_CONTINUE | Failed")
            time.sleep(1)
            if TRAILING_DELAY > 0:
                countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)
            continue

        if result == "all_bombs_auto_cashout":
            log(f"[{z}{_tag()}{o}] 🎯 AUTO_CASHOUT | Total : {k}{total_doge}{o}")
            break

        log(f"[{z}{_tag()}{o}] ❓ UNKNOWN_RESULT | {json.dumps(jo, ensure_ascii = False)[:500]}")
        if TRAILING_DELAY > 0:
            countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)

    if TRAILING_DELAY > 0:
        countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)

def play_one_round(sess, init_data: str):
    sc_u, ju = get_user_data(sess, init_data)
    if sc_u == 200 and isinstance(ju, dict):
        safe_user = {k : ju.get(k) for k in ("id", "username", "balance", "referral_balance")}
        log(f"[{z}{_tag()}{o}] 👤 USER_DATA | {x}{json.dumps(safe_user, ensure_ascii = False)}{o}")
    else:
        log(f"[{z}{_tag()}{o}] ❌ USER_DATA | HTTP {sc_u}")

    ag, stats_obj = get_active_game(sess, init_data)
    if stats_obj:
        log(f"[{z}{_tag()}{o}] 📊 GAME_STATS")
        print_stats(stats_obj)

    if ag:
        resume_active_game(sess, ag, init_data)
    else:
        if not ensure_game_lives(sess, init_data, need = 1):
            log(f"[{z}{_tag()}{o}] ⏸️ SKIP_ROUND | No energy")
            if TRAILING_DELAY > 0:
                countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)
            return

        start_ok = False
        for _ in range(MAX_TRY_START):
            sc_g, jg = mines_start_game(sess, DIFFICULTY, init_data)
            if sc_g == 200 and isinstance(jg, dict) and jg.get("status") == "success":
                log(f"[{z}{_tag()}{o}] ✅ START_GAME | Difficulty : {k}{DIFFICULTY}{o}")
                start_ok = True
                break
            if isinstance(jg, dict):
                msg = (jg.get("message", "") or "").lower()
                log(f"[{z}{_tag()}{o}] ❌ START_GAME | {json.dumps(jg, ensure_ascii = False)}")
                if "already have an active game" in msg:
                    ag2, _ = get_active_game(sess, init_data)
                    if ag2:
                        resume_active_game(sess, ag2, init_data)
                        start_ok = True
                        break
                if "mines_no_game_lives" in msg:
                    if not ensure_game_lives(sess, init_data, need = 1):
                        break
                    continue
            time.sleep(2)

        if not start_ok:
            log(f"[{z}{_tag()}{o}] ❌ START_FAILED | Cannot start or resume game")
            if TRAILING_DELAY > 0:
                countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)
            return

        order = tile_order_25()
        for idx in order:
            if OPEN_DELAY_MAX > 0 or OPEN_DELAY_MIN > 0:
                countdown(random.randint(OPEN_DELAY_MIN, max(OPEN_DELAY_MIN, OPEN_DELAY_MAX)), label = "[OPEN]", clear_on_done = True)
            else:
                countdown(5, label = "[OPEN]", clear_on_done = True)

            sc_o, jo, raw = mines_open_tile(sess, idx, init_data)
            result = safe_get(jo, "result", "result")
            tile_reward = safe_get(jo, "result", "tile_reward_doge")
            total_doge = safe_get(jo, "result", "earned_doge") or safe_get(jo, "result", "current_earnings_doge")
            tiles_opened = safe_get(jo, "result", "tiles_opened")
            continues_rem = safe_get(jo, "result", "continues_remaining")

            log(DIV)
            if result == "safe":
                log(f"[{z}{_tag()}{o}] ✅ TILE_SAFE | Tile : {k}{idx}{o} | Reward : {k}{tile_reward}{o} | Total : {k}{total_doge}{o} | Opened : {k}{tiles_opened}{o}")
            elif result == "bomb":
                log(f"[{z}{_tag()}{o}] 💣 TILE_BOMB | Tile : {k}{idx}{o} | Continues : {k}{continues_rem}{o}")
            elif result == "auto_continue":
                log(f"[{z}{_tag()}{o}] 🔄 AUTO_CONTINUE | Tile : {k}{idx}{o}")
            elif result == "all_bombs_auto_cashout":
                log(f"[{z}{_tag()}{o}] 🎯 AUTO_CASHOUT | Tile : {k}{idx}{o} | Total : {k}{total_doge}{o}")
            else:
                log(f"[{z}{_tag()}{o}] ❓ UNKNOWN_RESULT | Tile : {k}{idx}{o} | Result : {result}")

            if sc_o >= 400 or not isinstance(jo, dict):
                log(f"[{z}{_tag()}{o}] ❌ OPEN_ERROR | {str(raw)[:300]}")
                countdown(BACKOFF_ERR, label = "[BACKOFF]", clear_on_done = True)
                continue

            if result in ("safe", "auto_continue"):
                if TRAILING_DELAY > 0:
                    countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)
                continue

            if result == "bomb":
                if isinstance(continues_rem, int) and continues_rem <= 0:
                    log(f"[{z}{_tag()}{o}] 🔄 REFILL_CONTINUE | Via {m}Ads{o}")
                    sc_w, jw = mines_watch_ad_continues(sess, init_data)
                    if sc_w == 200 and isinstance(jw, dict) and jw.get("status") == "success":
                        log(f"[{z}{_tag()}{o}] ✅ REFILL_CONTINUE | {m}Success{o}")
                    else:
                        log(f"[{z}{_tag()}{o}] ❌ REFILL_CONTINUE | Failed")
                    time.sleep(2)
                sc_c, jc = mines_use_continue(sess, init_data)
                if sc_c == 200 and isinstance(jc, dict) and jc.get("status") == "success":
                    log(f"[{z}{_tag()}{o}] ✅ USE_CONTINUE | {m}Success{o}")
                else:
                    log(f"[{z}{_tag()}{o}] ❌ USE_CONTINUE | Failed")
                time.sleep(1)
                if TRAILING_DELAY > 0:
                    countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)
                continue

            if result == "all_bombs_auto_cashout":
                log(f"[{z}{_tag()}{o}] 🎯 AUTO_CASHOUT | Total : {k}{total_doge}{o}")
                break

            log(f"[{z}{_tag()}{o}] ❓ UNKNOWN_RESULT | {json.dumps(jo, ensure_ascii = False)[:500]}")
            if TRAILING_DELAY > 0:
                countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)

    sc_s2, js2 = mines_get_stats(sess, init_data)
    if sc_s2 == 200 and isinstance(js2, dict):
        log(f"[{z}{_tag()}{o}] 📊 POST_ROUND_STATS")
        print_stats(js2)
    else:
        log(f"[{z}{_tag()}{o}] ❌ POST_ROUND_STATS | HTTP {sc_s2}")
    
    log(DIV)
    if TRAILING_DELAY > 0:
        countdown(TRAILING_DELAY, label = "[DELAY]", clear_on_done = True)

def _is_valid_account(a):
    return isinstance(a, dict) and a.get("alias") and a.get("init_data")

def load_accounts_from_file(path = ACCOUNTS_FILE):
    try:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding = "utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [a for a in data if _is_valid_account(a)]
        if isinstance(data, dict):
            out = []
            for alias, obj in data.items():
                if isinstance(obj, dict):
                    obj = {"alias" : alias, **obj}
                    if _is_valid_account(obj):
                        out.append(obj)
            return out
        return []
    except Exception:
        return []

def save_accounts_to_file(accounts, path = ACCOUNTS_FILE):
    seen = {}
    for a in accounts:
        if _is_valid_account(a):
            seen[a["alias"]] = {"alias" : a["alias"], "init_data" : a["init_data"], "proxy" : a.get("proxy")}
    serial = list(seen.values())
    with open(path, "w", encoding = "utf-8") as f:
        json.dump(serial, f, ensure_ascii = False, indent = 2)
    return serial

def upsert_account(accounts, acc):
    for i, a in enumerate(accounts):
        if a.get("alias") == acc.get("alias"):
            accounts[i] = acc
            return accounts
    accounts.append(acc)
    return accounts

def collect_accounts_interactive(existing = None):
    accounts = list(existing or [])
    while True:
        clear_screen()
        print(DIV)
        print("CORE DRILL".center(58))
        print(DIV)
        print("Saved accounts :")
        if accounts:
            for i, a in enumerate(accounts, 1):
                p = " (proxy)" if a.get("proxy") else ""
                print(f" {i}. {z}{a['alias']}{o}{p}")
        else:
            print(" (none)")
        print(DIV)
        print("ADD ACCOUNT".center(58))
        print(DIV)

        alias = input("Alias : ").strip()
        while not alias:
            print("Alias cannot be empty.")
            alias = input("Alias : ").strip()

        init_data = input("Init Data : ").strip()
        while not init_data:
            print("Init Data cannot be empty.")
            init_data = input("Init Data : ").strip()

        use_proxy = input("Use Proxy (y/n) : ").strip().lower()
        proxy_url = None
        if use_proxy == "y":
            proxy_url = input("Proxy (http://user:pass@host:port or socks5://host:port) : ").strip() or None

        accounts = upsert_account(accounts, {"alias" : alias, "init_data" : init_data, "proxy" : proxy_url})
        
        more = input("Add another account? (y/n) : ").strip().lower()

        if more != "y":
            break
    return accounts

def worker(alias: str, init_data: str, proxy_url: str = None):
    set_alias(alias)
    sess = make_session(proxy_url = proxy_url)
    log(f"[{z}{_tag()}{o}] 🚀 STARTING | URL : {BASE_URL}")
    log(f"[{z}{_tag()}{o}] ⚙️ SETTINGS | Difficulty : {k}{DIFFICULTY}{o} | Tile Order : {k}{TILE_ORDER}{o}")
    if proxy_url:
        log(f"[{z}{_tag()}{o}] 🔌 PROXY | {k}{proxy_url}{o}")

    round_count = 0
    while True:
        try:
            round_count += 1
            log(f"[{z}{_tag()}{o}] 🔄 ROUND {round_count}")
            play_one_round(sess, init_data)
            log(f"[{z}{_tag()}{o}] ✅ ROUND {round_count} COMPLETED")
            print(DIV)
        except KeyboardInterrupt:
            log(f"[{z}{_tag()}{o}] 🛑 STOPPED by user")
            break
        except Exception as e:
            log(f"[{z}{_tag()}{o}] ❌ ERROR : {e}")
            countdown(BACKOFF_ERR, label = "[BACKOFF]", clear_on_done = True)

def main():
    clear_screen()
    accounts = load_accounts_from_file()

    if accounts:
        print(DIV)
        print("CORE DRILL".center(58))
        print(DIV)
        print("Loaded accounts :")
        for i, a in enumerate(accounts, 1):
            p = " (proxy)" if a.get("proxy") else ""
            print(f" {i}. {z}{a['alias']}{o}{p}")
        print(DIV)
        choice = input("Add another account? (y/n) : ").strip().lower()
        if choice == "y":
            accounts = collect_accounts_interactive(existing = accounts)
            accounts = save_accounts_to_file(accounts)
    else:
        print(DIV)
        print("CORE DRILL".center(58))
        print(DIV)
        print("No saved accounts. Let's add at least one.")
        accounts = collect_accounts_interactive(existing = [])
        accounts = save_accounts_to_file(accounts)

    if not accounts:
        print("No account. Exit.")
        return

    print(DIV)
    print("Run mode :")
    print("1. All accounts")
    print("2. Single account")
    print(DIV)
    mode = input("Choose (1/2) : ").strip()
    print(DIV)
    selected_accounts = accounts
    if mode == "2":
        print("Select an account to run :")
        for i, a in enumerate(accounts, 1):
            p = " (proxy)" if a.get("proxy") else ""
            print(f" {i}. {z}{a['alias']}{o}{p}")
        while True:
            print(DIV)
            sel = input("Enter number : ").strip()
            if sel.isdigit():
                idx = int(sel)
                if 1 <= idx <= len(accounts):
                    selected_accounts = [accounts[idx - 1]]
                    break
            print("Invalid selection. Try again.")

    clear_screen()
    print(DIV)
    print(f"TOTAL {len(selected_accounts)} ACCOUNTS")
    print(DIV)

    threads = []
    for acc in selected_accounts:
        t = threading.Thread(
            target = worker,
            args = (acc["alias"], acc["init_data"], acc.get("proxy")),
            daemon = True
        )
        t.start()
        threads.append(t)

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        print("[EXIT] Stopped by user.")

if __name__ == "__main__":
    main()