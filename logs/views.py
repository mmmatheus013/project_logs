import io
import logging
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Log

logger = logging.getLogger('logs')

# define arquivo de logs
LOG_FILE = Path(settings.BASE_DIR) / "raw_logs.txt"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


@csrf_exempt
def upload_file(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST"}, status=405)

    uploaded = request.FILES.get("file")
    if not uploaded:
        logger.warning("Upload falhou — 'file' ausente em request.FILES")
        return HttpResponseBadRequest('Campo "file" ausente')

    created = 0
    file_batch = []
    db_batch = []
    FILE_BATCH = 1000
    DB_BATCH = 1000

    try:
        text_stream = io.TextIOWrapper(
            uploaded.file, encoding="utf-8", errors="replace")
        with LOG_FILE.open("a", encoding="utf-8") as out_f:
            for raw_line in text_stream:
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue

                # preparar escrita em arquivo
                file_batch.append(line + "\n")
                if len(file_batch) >= FILE_BATCH:
                    out_f.writelines(file_batch)
                    file_batch = []

                # preparar objetos para DB
                db_batch.append(Log(content=line))
                if len(db_batch) >= DB_BATCH:
                    with transaction.atomic():
                        Log.objects.bulk_create(db_batch, batch_size=DB_BATCH)
                    created += len(db_batch)
                    db_batch = []

            # grava o arquivo
            if file_batch:
                out_f.writelines(file_batch)

            # grava no DB
            if db_batch:
                with transaction.atomic():
                    Log.objects.bulk_create(db_batch, batch_size=DB_BATCH)
                created += len(db_batch)

    except Exception as exc:
        logger.exception(
            "Erro processando upload e gravando raw_logs.txt/DB: %s", exc)
        return JsonResponse({"error": "erro ao processar arquivo"}, status=500)

    logger.info("Upload processed: created=%d raw_file=%s client=%s",
                created, str(LOG_FILE), request.META.get('REMOTE_ADDR'))
    return JsonResponse({"created": created}, status=201)
