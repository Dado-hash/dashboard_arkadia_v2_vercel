from django.contrib import admin
from .models import ExchangeRate, Fund, SavedReport, Strategy, Asset, Balance, Transaction, PerformanceMetric, ExchangeAccount, Wallet

class FundAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class StrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'fund', 'manual', 'description')
    search_fields = ('name', 'fund__name')
    list_filter = ('fund',)
    ordering = ('name',)

class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'strategy', 'exchange_or_wallet', 'amount', 'value_usd', 'date')
    search_fields = ('name', 'strategy__name')
    list_filter = ('strategy', 'date')
    ordering = ('date',)

class BalanceAdmin(admin.ModelAdmin):
    list_display = ('strategy_or_fund', 'value_usd', 'value_eur', 'date')
    search_fields = ('strategy__name', 'fund__name')
    list_filter = ('strategy', 'fund', 'date')
    ordering = ('date',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('type', 'asset', 'amount', 'value_usd', 'value_eur', 'date', 'strategy_or_fund')
    search_fields = ('type', 'strategy__name')
    list_filter = ('type', 'strategy', 'date')
    ordering = ('date',)

class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ('strategy_or_fund', 'date', 'metric_name', 'value', 'value_eur')
    search_fields = ('strategy__name', 'fund__name', 'metric_name')
    list_filter = ('strategy', 'fund', 'date', 'metric_name')
    ordering = ('date',)

class ExchangeAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'strategy', 'exchange')
    search_fields = ('name', 'strategy__name')
    list_filter = ('strategy',)
    ordering = ('name',)

class WalletAdmin(admin.ModelAdmin):
    list_display = ('name', 'strategy', 'address', 'network', 'description', 'last_updated')
    search_fields = ('name', 'strategy__name')
    list_filter = ('strategy',)
    ordering = ('name',)

class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency', 'date', 'rate')
    search_fields = ('from_currency', 'to_currency')
    list_filter = ('date', 'from_currency', 'to_currency')
    ordering = ('date',)

class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'fund', 'currency')
    search_fields = ('name', 'date', 'fund', 'currency')
    list_filter = ('date', 'fund', 'currency')
    ordering = ('date',)

admin.site.register(Fund, FundAdmin)
admin.site.register(Strategy, StrategyAdmin)
admin.site.register(Asset, AssetAdmin)
admin.site.register(Balance, BalanceAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(PerformanceMetric, PerformanceMetricAdmin)
admin.site.register(ExchangeAccount, ExchangeAccountAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(SavedReport, ReportAdmin)