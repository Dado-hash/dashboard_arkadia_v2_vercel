from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('save-fund/', views.save_fund, name='save_fund'),
    path('save-strategy/', views.save_strategy, name='save_strategy'),
    path('save-api-keys/', views.save_api_keys, name='save_api_keys'),
    path('update-assets/', views.update_assets, name='update_assets'),
    path('save-wallet/', views.save_wallet, name='save_wallet'),
    path('add-assets/', views.add_assets, name='add_assets'),
    path('add-transactions/', views.add_transactions, name='add_transactions'),
    path('settings/', views.settings, name='settings'),
    path('funds/', views.funds, name='funds'),
    path('funds/<int:fund_id>/strategies/', views.strategies, name='strategies'),
    path('reports/', views.reports, name='reports'),
    path('save_report/', views.save_report, name='save_report'),
    path('all_reports/', views.all_reports, name='all_reports'),
    path('download_report/<int:report_id>/', views.download_report, name='download_report'),
]