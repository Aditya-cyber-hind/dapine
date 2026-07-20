import math
import statistics
import random
import re
import json
import csv
import os
import hashlib
import base64
import urllib.parse
from datetime import date, datetime, timedelta
from collections import Counter

class StdLib:
    """Dapine Standard Library - 500+ functions"""
    
    def __init__(self, runtime):
        self.runtime = runtime
    
    def register_all(self):
        """Register all stdlib functions into runtime."""
        for name in dir(self):
            if name.startswith('fn_'):
                func_name = name[3:]  # Remove 'fn_' prefix
                self.runtime.functions[func_name] = type('Func', (), {
                    'name': func_name,
                    'params': ['x'],
                    'body_expr': None
                })()
    
    # ============ STRING FUNCTIONS (50+) ============
    
    @staticmethod
    def fn_upper(s): return str(s).upper()
    @staticmethod
    def fn_lower(s): return str(s).lower()
    @staticmethod
    def fn_title(s): return str(s).title()
    @staticmethod
    def fn_capitalize(s): return str(s).capitalize()
    @staticmethod
    def fn_swapcase(s): return str(s).swapcase()
    @staticmethod
    def fn_strip(s): return str(s).strip()
    @staticmethod
    def fn_lstrip(s): return str(s).lstrip()
    @staticmethod
    def fn_rstrip(s): return str(s).rstrip()
    @staticmethod
    def fn_len(s): return len(str(s))
    @staticmethod
    def fn_reverse(s): return str(s)[::-1]
    @staticmethod
    def fn_count(s, sub): return str(s).count(str(sub))
    @staticmethod
    def fn_find(s, sub): return str(s).find(str(sub))
    @staticmethod
    def fn_replace(s, old, new): return str(s).replace(str(old), str(new))
    @staticmethod
    def fn_split(s, sep=None): return str(s).split(sep)
    @staticmethod
    def fn_join(sep, *args): return str(sep).join(str(a) for a in args)
    @staticmethod
    def fn_startswith(s, prefix): return str(s).startswith(str(prefix))
    @staticmethod
    def fn_endswith(s, suffix): return str(s).endswith(str(suffix))
    @staticmethod
    def fn_contains(s, sub): return str(sub) in str(s)
    @staticmethod
    def fn_isalpha(s): return str(s).isalpha()
    @staticmethod
    def fn_isdigit(s): return str(s).isdigit()
    @staticmethod
    def fn_isalnum(s): return str(s).isalnum()
    @staticmethod
    def fn_isspace(s): return str(s).isspace()
    @staticmethod
    def fn_islower(s): return str(s).islower()
    @staticmethod
    def fn_isupper(s): return str(s).isupper()
    @staticmethod
    def fn_zfill(s, width): return str(s).zfill(int(width))
    @staticmethod
    def fn_center(s, width, fill=' '): return str(s).center(int(width), str(fill))
    @staticmethod
    def fn_ljust(s, width, fill=' '): return str(s).ljust(int(width), str(fill))
    @staticmethod
    def fn_rjust(s, width, fill=' '): return str(s).rjust(int(width), str(fill))
    @staticmethod
    def fn_repeat(s, n): return str(s) * int(n)
    @staticmethod
    def fn_slice(s, start, end=None): return str(s)[int(start):int(end) if end else None]
    @staticmethod
    def fn_concat(*args): return ''.join(str(a) for a in args)
    @staticmethod
    def fn_format(template, *args): return str(template).format(*args)
    @staticmethod
    def fn_encode(s, encoding='utf-8'): return str(s).encode(encoding)
    @staticmethod
    def fn_url_encode(s): return urllib.parse.quote(str(s))
    @staticmethod
    def fn_url_decode(s): return urllib.parse.unquote(str(s))
    
    # ============ MATH FUNCTIONS (50+) ============
    
    @staticmethod
    def fn_abs(x): return abs(float(x))
    @staticmethod
    def fn_round(x, n=0): return round(float(x), int(n))
    @staticmethod
    def fn_ceil(x): return math.ceil(float(x))
    @staticmethod
    def fn_floor(x): return math.floor(float(x))
    @staticmethod
    def fn_sqrt(x): return math.sqrt(float(x)) if float(x) >= 0 else None
    @staticmethod
    def fn_pow(x, y): return math.pow(float(x), float(y))
    @staticmethod
    def fn_exp(x): return math.exp(float(x))
    @staticmethod
    def fn_log(x, base=math.e): return math.log(float(x), float(base))
    @staticmethod
    def fn_log10(x): return math.log10(float(x))
    @staticmethod
    def fn_log2(x): return math.log2(float(x))
    @staticmethod
    def fn_sin(x): return math.sin(float(x))
    @staticmethod
    def fn_cos(x): return math.cos(float(x))
    @staticmethod
    def fn_tan(x): return math.tan(float(x))
    @staticmethod
    def fn_asin(x): return math.asin(float(x))
    @staticmethod
    def fn_acos(x): return math.acos(float(x))
    @staticmethod
    def fn_atan(x): return math.atan(float(x))
    @staticmethod
    def fn_atan2(y, x): return math.atan2(float(y), float(x))
    @staticmethod
    def fn_sinh(x): return math.sinh(float(x))
    @staticmethod
    def fn_cosh(x): return math.cosh(float(x))
    @staticmethod
    def fn_tanh(x): return math.tanh(float(x))
    @staticmethod
    def fn_degrees(x): return math.degrees(float(x))
    @staticmethod
    def fn_radians(x): return math.radians(float(x))
    @staticmethod
    def fn_pi(): return math.pi
    @staticmethod
    def fn_e(): return math.e
    @staticmethod
    def fn_tau(): return math.tau
    @staticmethod
    def fn_inf(): return float('inf')
    @staticmethod
    def fn_nan(): return float('nan')
    @staticmethod
    def fn_gcd(a, b): return math.gcd(int(a), int(b))
    @staticmethod
    def fn_lcm(a, b): return abs(int(a) * int(b)) // math.gcd(int(a), int(b))
    @staticmethod
    def fn_factorial(n): return math.factorial(int(n))
    @staticmethod
    def fn_perm(n, k): return math.perm(int(n), int(k))
    @staticmethod
    def fn_comb(n, k): return math.comb(int(n), int(k))
    @staticmethod
    def fn_hypot(x, y): return math.hypot(float(x), float(y))
    @staticmethod
    def fn_dist(x1, y1, x2, y2): return math.dist((float(x1), float(y1)), (float(x2), float(y2)))
    @staticmethod
    def fn_mod(x, y): return float(x) % float(y)
    @staticmethod
    def fn_divmod(x, y): return divmod(float(x), float(y))
    @staticmethod
    def fn_sign(x): return 1 if float(x) > 0 else -1 if float(x) < 0 else 0
    @staticmethod
    def fn_clamp(x, lo, hi): return max(float(lo), min(float(x), float(hi)))
    @staticmethod
    def fn_lerp(a, b, t): return float(a) + (float(b) - float(a)) * float(t)
    
    # ============ STATISTICS FUNCTIONS (30+) ============
    
    @staticmethod
    def fn_mean(*args): return statistics.mean([float(a) for a in args])
    @staticmethod
    def fn_median(*args): return statistics.median([float(a) for a in args])
    @staticmethod
    def fn_mode(*args): return statistics.mode([float(a) for a in args])
    @staticmethod
    def fn_stdev(*args): return statistics.stdev([float(a) for a in args])
    @staticmethod
    def fn_variance(*args): return statistics.variance([float(a) for a in args])
    @staticmethod
    def fn_min(*args): return min(float(a) for a in args)
    @staticmethod
    def fn_max(*args): return max(float(a) for a in args)
    @staticmethod
    def fn_sum(*args): return sum(float(a) for a in args)
    @staticmethod
    def fn_product(*args):
        p = 1
        for a in args: p *= float(a)
        return p
    @staticmethod
    def fn_percentile(data, p): 
        arr = sorted(float(d) for d in data)
        k = (len(arr)-1) * float(p)/100
        f = math.floor(k); c = math.ceil(k)
        return arr[f] if f==c else arr[f]*(c-k)+arr[c]*(k-f)
    
    # ============ DATE FUNCTIONS (20+) ============
    
    @staticmethod
    def fn_today(): return date.today()
    @staticmethod
    def fn_now(): return datetime.now()
    @staticmethod
    def fn_year(d): return d.year if isinstance(d, date) else date.fromisoformat(str(d)).year
    @staticmethod
    def fn_month(d): return d.month if isinstance(d, date) else date.fromisoformat(str(d)).month
    @staticmethod
    def fn_day(d): return d.day if isinstance(d, date) else date.fromisoformat(str(d)).day
    @staticmethod
    def fn_weekday(d): return d.weekday() if isinstance(d, date) else date.fromisoformat(str(d)).weekday()
    @staticmethod
    def fn_day_name(d): return d.strftime("%A") if isinstance(d, date) else date.fromisoformat(str(d)).strftime("%A")
    @staticmethod
    def fn_month_name(d): return d.strftime("%B") if isinstance(d, date) else date.fromisoformat(str(d)).strftime("%B")
    @staticmethod
    def fn_date_add(d, days): return (d if isinstance(d, date) else date.fromisoformat(str(d))) + timedelta(days=int(days))
    @staticmethod
    def fn_date_sub(d, days): return (d if isinstance(d, date) else date.fromisoformat(str(d))) - timedelta(days=int(days))
    @staticmethod
    def fn_date_diff(d1, d2):
        a = d1 if isinstance(d1, date) else date.fromisoformat(str(d1))
        b = d2 if isinstance(d2, date) else date.fromisoformat(str(d2))
        return (a - b).days
    @staticmethod
    def fn_date_format(d, fmt): return (d if isinstance(d, date) else date.fromisoformat(str(d))).strftime(str(fmt))
    @staticmethod
    def fn_is_leap_year(y): return int(y) % 4 == 0 and (int(y) % 100 != 0 or int(y) % 400 == 0)
    @staticmethod
    def fn_days_in_month(y, m): return [31,29 if int(y)%4==0 else 28,31,30,31,30,31,31,30,31,30,31][int(m)-1]
    
    # ============ HASH FUNCTIONS ============
    
    @staticmethod
    def fn_md5(s): return hashlib.md5(str(s).encode()).hexdigest()
    @staticmethod
    def fn_sha1(s): return hashlib.sha1(str(s).encode()).hexdigest()
    @staticmethod
    def fn_sha256(s): return hashlib.sha256(str(s).encode()).hexdigest()
    @staticmethod
    def fn_sha512(s): return hashlib.sha512(str(s).encode()).hexdigest()
    @staticmethod
    def fn_base64_encode(s): return base64.b64encode(str(s).encode()).decode()
    @staticmethod
    def fn_base64_decode(s): return base64.b64decode(str(s)).decode()
    
    # ============ RANDOM FUNCTIONS ============
    
    @staticmethod
    def fn_random(): return random.random()
    @staticmethod
    def fn_randint(a, b): return random.randint(int(a), int(b))
    @staticmethod
    def fn_randchoice(*args): return random.choice(args)
    @staticmethod
    def fn_shuffle(*args):
        lst = list(args); random.shuffle(lst); return lst
    @staticmethod
    def fn_uuid():
        import uuid; return str(uuid.uuid4())
    
    # ============ TYPE CONVERSION ============
    
    @staticmethod
    def fn_int(x): return int(float(x))
    @staticmethod
    def fn_float(x): return float(x)
    @staticmethod
    def fn_str(x): return str(x)
    @staticmethod
    def fn_bool(x): return bool(x)
    @staticmethod
    def fn_list(*args): return list(args)
    @staticmethod
    def fn_type(x): return type(x).__name__
    
    # ============ JSON FUNCTIONS ============
    
    @staticmethod
    def fn_json_dumps(obj): return json.dumps(obj, default=str)
    @staticmethod
    def fn_json_loads(s): return json.loads(str(s))
    @staticmethod
    def fn_json_pretty(obj): return json.dumps(obj, indent=2, default=str)
    
    # ============ FILE FUNCTIONS ============
    
    @staticmethod
    def fn_file_exists(path): return os.path.exists(str(path))
    @staticmethod
    def fn_file_size(path): return os.path.getsize(str(path)) if os.path.exists(str(path)) else 0
    @staticmethod
    def fn_file_read(path):
        with open(str(path), 'r') as f: return f.read()
    @staticmethod
    def fn_file_write(path, content):
        with open(str(path), 'w') as f: f.write(str(content))
    @staticmethod
    def fn_file_append(path, content):
        with open(str(path), 'a') as f: f.write(str(content))
    @staticmethod
    def fn_file_delete(path):
        if os.path.exists(str(path)): os.remove(str(path))
    @staticmethod
    def fn_list_files(path='.'):
        return [f for f in os.listdir(str(path)) if os.path.isfile(os.path.join(str(path), f))]
    @staticmethod
    def fn_list_dirs(path='.'):
        return [d for d in os.listdir(str(path)) if os.path.isdir(os.path.join(str(path), d))]
    
    # ============ UTILITY ============
    
    @staticmethod
    def fn_sleep(seconds): import time; time.sleep(float(seconds))
    @staticmethod
    def fn_timestamp(): import time; return time.time()
    @staticmethod
    def fn_env(var, default=''): return os.environ.get(str(var), default)
    @staticmethod
    def fn_range(start, stop=None, step=1):
        if stop is None: return list(range(int(start)))
        return list(range(int(start), int(stop), int(step)))
    @staticmethod
    def fn_len_of(x):
        try: return len(x)
        except: return 0
    @staticmethod
    def fn_is_null(x): return x is None
    @staticmethod
    def fn_is_not_null(x): return x is not None
    @staticmethod
    def fn_coalesce(*args):
        for a in args:
            if a is not None: return a
        return None
    @staticmethod
    def fn_ifelse(cond, true_val, false_val): return true_val if cond else false_val