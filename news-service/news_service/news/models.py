from django.db import models

class News(models.Model):
    title = models.CharField(max_length=300)
    keyword = models.CharField(max_length=100, blank=True, null=True)
    link = models.URLField()

    def __str__(self):
        return self.title
