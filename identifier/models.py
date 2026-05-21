from django.db import models

class Identification(models.Model):

    image = models.ImageField(
        upload_to='organisms/'
    )

    common_name = models.CharField(
        max_length=200
    )

    scientific_name = models.CharField(
        max_length=200
    )

    confidence = models.CharField(
        max_length=50
    )

    ai_cost = models.FloatField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.common_name
