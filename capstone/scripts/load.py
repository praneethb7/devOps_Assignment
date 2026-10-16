"""Bounded HTTP load. Usage: python scripts/load.py URL [seconds] [workers]."""
import concurrent.futures
import sys
import os
import time
from urllib.request import Request, urlopen
url = (sys.argv[1] if len(sys.argv)>1 else "http://localhost:3000") + "/api/equipment"
seconds = min(int(sys.argv[2]) if len(sys.argv)>2 else 120, 600)
workers = min(int(sys.argv[3]) if len(sys.argv)>3 else 8, 32)
end = time.monotonic()+seconds

def worker():
    ok = errors = 0
    while time.monotonic() < end:
        try:
            with urlopen(Request(url, headers=({"Host": os.environ["HOST_HEADER"]} if "HOST_HEADER" in os.environ else {})), timeout=5) as response:
                response.read()
            ok += 1
        except Exception:
            errors += 1
    return ok, errors

with concurrent.futures.ThreadPoolExecutor(workers) as pool:
    results = list(pool.map(lambda _: worker(), range(workers)))
print({"requests": sum(r[0] for r in results), "errors": sum(r[1] for r in results), "duration_seconds": seconds})
