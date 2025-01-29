# from django.contrib import admin

# # Register your models here.
# # admin.py

# from .models import StockData

# admin.site.register(StockData)

# from .models import VolumeTraderData, PumpDumpStatus

# admin.site.register(VolumeTraderData)
# admin.site.register(PumpDumpStatus)

from django.contrib import admin
from .models import StockData

@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'symbol')
