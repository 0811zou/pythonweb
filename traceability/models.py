import hashlib
import json

from django.conf import settings
from django.db import models
from django.utils import timezone


class TraceEvent(models.Model):
    EVENT_TYPES = [
        ('planting', '种植'),
        ('fertilizing', '施肥'),
        ('pesticide', '农药'),
        ('harvest', '采收'),
        ('qc', '质检'),
        ('storage', '入库'),
        ('shipping', '发货'),
        ('other', '其他'),
    ]
    batch = models.ForeignKey('products.ProductBatch', on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, default='other')
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=200, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    data_hash = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_traceevent'
        ordering = ['occurred_at', 'created_at']

    def __str__(self):
        return f"{self.batch.batch_code} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.previous_hash:
            previous = (
                TraceEvent.objects
                .filter(batch=self.batch)
                .exclude(pk=self.pk)
                .order_by('-created_at', '-id')
                .first()
            )
            self.previous_hash = previous.data_hash if previous else ''
        self.data_hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def calculate_hash(self):
        payload = {
            'batch_code': self.batch.batch_code,
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'operator_id': self.operator_id,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else '',
            'location': self.location,
            'previous_hash': self.previous_hash,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()
