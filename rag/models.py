# Create your models here.
from django.db import models
from django.db.models import UniqueConstraint

    
class PdfTopicMap(models.Model):
    document_id = models.UUIDField(primary_key=True, null=False, blank=True, editable=False)  # 先允許為空
    pdf_name = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pdf_topic_map"
        indexes = [
            models.Index(fields=["pdf_name"]),
            models.Index(fields=["topic"]),
        ]
        constraints = [
            UniqueConstraint(fields=["pdf_name", "topic"], name="uq_pdf_topic")
        ]
        permissions = (
            ("access_pdf", "Can access this document"),  # 自訂物件層級權限
            ("edit_pdf", "Can edit this document")
        )

    def __str__(self):
        return f"{self.pdf_name} → {self.topic}"

class QARecord(models.Model):
    question = models.TextField()             # 問
    answer = models.TextField()               # 答
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "qa_record"
        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"QA record"
