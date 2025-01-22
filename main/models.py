from django.db import models

# Create your models here.



class StockData(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    current_price = models.FloatField()
    high_52_week = models.FloatField()
    low_52_week = models.FloatField()
    market_cap = models.FloatField(null=True, blank=True)
    volume = models.IntegerField(null=True, blank=True)
    average_volume_52_week = models.IntegerField(null=True, blank=True)
    cagr_5y = models.FloatField(null=True, blank=True)
    cagr_3y = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    
    # New fields for MACD, RSI
    macd = models.FloatField(null=True, blank=True)
    rsi = models.FloatField(null=True, blank=True)

    # Bollinger Bands stored as a TextField (e.g., JSON or CSV format)
    bollinger_bands = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.symbol



class VolumeTraderData(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    current_volume = models.BigIntegerField()
    average_volume_52_week = models.BigIntegerField()
    percentage_difference = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.symbol


class PumpDumpStatus(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=50)  # Example field for status
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.status}"
