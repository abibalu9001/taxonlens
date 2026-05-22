from django.db import models


class Identification(models.Model):

    image = models.ImageField(

        upload_to='organisms/',

        blank=True,

        null=True

    )

    organism_type = models.CharField(

        max_length=50,

        blank=True,

        null=True

    )

    common_name = models.CharField(

        max_length=200

    )

    scientific_name = models.CharField(

        max_length=200

    )

    family_name = models.CharField(

        max_length=200,

        blank=True,

        null=True

    )

    tamil_name = models.CharField(

        max_length=200,

        blank=True,

        null=True

    )

    confidence = models.CharField(

        max_length=50,

        blank=True,

        null=True

    )

    wikipedia_link = models.TextField(

        blank=True,

        null=True

    )

    description = models.TextField(

        blank=True,

        null=True

    )

    ai_cost = models.CharField(

        max_length=50,

        blank=True,

        null=True

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return self.common_name
