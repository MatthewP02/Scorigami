from django.contrib import admin
from .models import FootballGame

class FootballAdmin(admin.ModelAdmin):
	list_filter = ['date']
	search_fields = ['winner__icontains', 'loser__icontains']
	ordering =  ['date']

admin.site.register(FootballGame, FootballAdmin)