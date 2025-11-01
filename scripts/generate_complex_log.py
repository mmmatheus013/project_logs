import argparse
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "curl/7.85.0",
    "PostmanRuntime/7.32.3",
    "python-requests/2.32.5",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 Safari/605.1.15",
]

METHODS = ["GET", "POST", "PUT", "DELETE"]
PATHS = [
    "/", "/login", "/logout", "/status", "/api/v1/items", "/api/v1/items/123",
    "/search?q=test", "/static/js/app.js", "/health", "/metrics"
]
REFERERS = [
    "-", "https://google.com", "https://bing.com", "https://example.com/page"
]


def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def gen_line(ts):
    ip = random_ip()
    method = random.choice(METHODS)
    path = random.choice(PATHS)
    status = random.choice([200, 201, 204, 301, 302, 400, 401, 403, 404, 500])
    size = random.randint(64, 50000)
    uid = uuid.uuid4()
    ua = random.choice(USER_AGENTS)
    ref = random.choice(REFERERS)
    # formato estilo combined log + extra fields
    return f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S %z")}] "{method} {path} HTTP/1.1" {status} {size} "{ref}" "{ua}" uid={uid}\n'


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", "-n", type=int,
                   default=100000, help="Número de linhas")
    p.add_argument(
        "--output", "-o", default="test-files/complex_log.txt", help="Arquivo de saída")
    p.add_argument(
        "--start", "-s", help="Timestamp ISO inicial (ex: 2025-10-31T12:00:00)", default=None)
    args = p.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.start:
        start = datetime.fromisoformat(args.start)
    else:
        start = datetime.utcnow()

    with out.open("w", encoding="utf-8") as fh:
        ts = start
        for i in range(args.count):
            # incrementa timestamp alguns segundos aleatórios
            ts += timedelta(seconds=random.randint(0, 3))
            fh.write(gen_line(ts))

    print(f"Gerado {args.count} linhas em {out}")


if __name__ == "__main__":
    main()
