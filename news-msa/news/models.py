from django.db import models
from datetime import date

class News(models.Model):
    title = models.CharField(max_length=300)
    keyword = models.CharField(max_length=100, blank=True, null=True)
    link = models.URLField(max_length=700, unique=True)  # unique 다시 추가
    crawl_date = models.DateField(db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.title
