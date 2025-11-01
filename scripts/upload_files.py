import os
import sys
import time
import logging
from pathlib import Path
from typing import List
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# carrega .env explicitamente a partir da raiz do projeto 
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/logs/upload/")
DIRECTORIES_RAW = os.getenv("DIRECTORIES", "")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "").strip() or None
SKIP_EXTENSIONS = os.getenv("SKIP_EXTENSIONS", "")  
DELAY = float(os.getenv("DELAY_SECONDS", "0.2"))

if not DIRECTORIES_RAW:
    logging.error("DIRECTORIES vazio. Preencha .env")
    sys.exit(1)


def _clean_path(s: str) -> str:
    return s.strip().strip('"').strip("'")


def parse_directories(raw: str) -> List[Path]:
    if "," in raw:
        parts = [p for p in (p.strip() for p in raw.split(",")) if p]
    else:
        parts = [p for p in (p.strip() for p in raw.splitlines()) if p]
    return [Path(_clean_path(p)).expanduser() for p in parts]


def should_skip(p: Path) -> bool:
    if not SKIP_EXTENSIONS:
        return False
    exts = [e.strip().lower() for e in SKIP_EXTENSIONS.split(",") if e.strip()]
    return p.suffix.lower() in exts


def find_files(dirs: List[Path]) -> List[Path]:
    files = []
    for d in dirs:
        if not d.exists():
            logging.warning("Diretório não existe: %s", d)
            continue
        if d.is_file():
            if not should_skip(d):
                files.append(d)
            continue
        for p in d.rglob("*"):
            if p.is_file() and not should_skip(p):
                files.append(p)
    return sorted(files)


# usa session para reaproveitar conexões
SESSION = requests.Session()
if AUTH_TOKEN:
    SESSION.headers.update({"Authorization": f"Bearer {AUTH_TOKEN}"})


def send_file(file_path: Path) -> bool:
    try:
        with file_path.open("rb") as f:
            files = {"file": (file_path.name, f)}
            resp = SESSION.post(API_URL, files=files, timeout=60)
        if resp.status_code in (200, 201):
            logging.info("Enviado: %s (status=%s)",
                         file_path, resp.status_code)
            return True
        logging.error("Falha enviando %s: %s - %s",
                      file_path, resp.status_code, resp.text)
        return False
    except Exception as e:
        logging.exception("Erro enviando %s: %s", file_path, e)
        return False


def main():
    dirs = parse_directories(DIRECTORIES_RAW)
    files = find_files(dirs)
    logging.info("Arquivos encontrados: %d", len(files))
    success = 0
    for i, f in enumerate(files, start=1):
        logging.info("[%d/%d] %s", i, len(files), f)
        if send_file(f):
            success += 1
        time.sleep(DELAY)
    logging.info("Concluído. Sucesso: %d / %d", success, len(files))


if __name__ == "__main__":
    main()
