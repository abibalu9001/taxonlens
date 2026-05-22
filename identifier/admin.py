from django.contrib import admin

from .models import Identification


@admin.register(Identification)

class IdentificationAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'organism_type',

        'common_name',

        'scientific_name',

        'family_name',

        'confidence',

        'created_at'

    )

    search_fields = (

        'common_name',

        'scientific_name',

        'family_name'

    )

    list_filter = (

        'organism_type',

        'family_name',

        'created_at'

    )
