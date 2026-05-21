from django.contrib import admin

from .models import Identification


@admin.register(Identification)

class IdentificationAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'common_name',

        'scientific_name',

        'family_name',

        'confidence',

        'ai_cost',

        'created_at'

    )

    search_fields = (

        'common_name',

        'scientific_name',

        'family_name'

    )

    list_filter = (

        'family_name',

        'created_at'

    )

    readonly_fields = (

        'created_at',

    )
