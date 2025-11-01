from django.db import models
import uuid


def generate_uid():
    return str(uuid.uuid4())


class Log(models.Model):
    uid = models.CharField(max_length=36, unique=True,
                           default=generate_uid, editable=False)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:50]
