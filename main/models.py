from django.db import models

# Create your models here.

class StockData(models.Model):
    company_name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now=True)

    # class Meta:
    #     db_table = 'ListOfCompanies'

    def __str__(self):
        return f"{self.company_name} ({self.symbol})"

# class StockData1(models.Model):
#     symbol = models.CharField(max_length=20, unique=True)
#     company_name = models.CharField(max_length=255, null=True, blank=True)

#     # Allow NULL values
#     high_52_week = models.FloatField(null=True, blank=True)
#     low_52_week = models.FloatField(null=True, blank=True)

#     current_price = models.FloatField(null=True, blank=True)
#     market_cap = models.FloatField(null=True, blank=True)
#     volume = models.IntegerField(null=True, blank=True)
#     average_volume_52_week = models.IntegerField(null=True, blank=True)
#     cagr_5y = models.FloatField(null=True, blank=True)
#     cagr_3y = models.FloatField(null=True, blank=True)
#     timestamp = models.DateTimeField(auto_now=True)

#     # New fields for MACD, RSI
#     macd = models.FloatField(null=True, blank=True)
#     rsi = models.FloatField(null=True, blank=True)

#     # Bollinger Bands stored as a TextField (e.g., JSON or CSV format)
#     bollinger_bands = models.TextField(null=True, blank=True)

#     ## New tickets
#     volatility = models.FloatField(null=True, blank=True)
#     dividend_yield = models.FloatField(null=True, blank=True)
#     dividend_per_share = models.FloatField(null=True, blank=True)
#     pe_ratio = models.FloatField(null=True, blank=True)
#     moving_average_50 = models.FloatField(null=True, blank=True)
#     moving_average_200 = models.FloatField(null=True, blank=True)
#     historical_data = models.JSONField(null=True, blank=True)
#     historical_data_last_30_days = models.JSONField(null=True, blank=True)

#     def __str__(self):
#         return self.symbol


# class VolumeTraderData(models.Model):
#     symbol = models.CharField(max_length=20, unique=True)
#     current_volume = models.BigIntegerField()
#     average_volume_52_week = models.BigIntegerField()
#     percentage_difference = models.FloatField()
#     timestamp = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.symbol


# class PumpDumpStatus(models.Model):
#     symbol = models.CharField(max_length=20, unique=True)
#     status = models.CharField(max_length=50)  # Example field for status
#     timestamp = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.symbol} - {self.status}"

#         # return f"NSE Data (Updated at {self.updated_at})"


