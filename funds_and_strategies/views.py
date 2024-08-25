from collections import defaultdict
from datetime import datetime, timedelta
import json
import os
from django.shortcuts import get_object_or_404, render, redirect
from django.http import FileResponse, Http404, JsonResponse
from django.contrib import messages
import requests
from services.update_assets import update_all_assets
from .models import Asset, Balance, ExchangeRate, Fund, PerformanceMetric, SavedReport, Strategy, Transaction
from .forms import AssetFormSet, ExchangeAccountForm, FundForm, StrategyForm, TransactionFormSet, WalletForm
from django.db.models import Sum, Max
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

# Create your views here.

def get_bitcoin_data():
    # Calcola le date per l'ultimo anno
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Convertili in timestamp UNIX
    end_date_unix = int(end_date.timestamp())
    start_date_unix = int(start_date.timestamp())

    # URL dell'API CoinGecko
    url = f'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=usd&from={start_date_unix}&to={end_date_unix}'
    
    response = requests.get(url)
    data = response.json()
    prices = data['prices']
    labels = [datetime.fromtimestamp(item[0] / 1000).strftime('%Y-%m-%d') for item in prices]
    prices = [item[1] for item in prices]
    
    return labels, prices

def dashboard_view(request):
    labels, data = get_bitcoin_data()
    context = {
        'labels': json.dumps(labels),
        'data': json.dumps(data)
    }
    return render(request, 'funds_and_strategies/dashboard.html', context)

def settings(request):
    return render(request, 'funds_and_strategies/settings.html')

def save_fund(request):
    if request.method == 'POST':
        form = FundForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "success", "message": "Fund saved successfully"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data"})
    else:
        form = FundForm()
    return render(request, 'funds_and_strategies/save_fund.html', {'form': form})

def save_strategy(request):
    if request.method == 'POST':
        form = StrategyForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "success", "message": "Strategy saved successfully"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data"})
    else:
        form = StrategyForm()
    return render(request, 'funds_and_strategies/save_strategy.html', {'form': form})

def save_api_keys(request):
    if request.method == 'POST':
        form = ExchangeAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "success", "message": "API keys saved successfully"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data"})
    else:
        form = ExchangeAccountForm()
    return render(request, 'funds_and_strategies/save_api_keys.html', {'form': form})

def save_wallet(request):
    if request.method == 'POST':
        form = WalletForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "success", "message": "Wallet saved successfully"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data"})
    else:
        form = WalletForm()
    return render(request, 'funds_and_strategies/save_wallet.html', {'form': form})

def update_assets(request):
    try:
        update_all_assets()  # La tua funzione per aggiornare gli asset

        # Recupera i dati aggiornati
        funds = Fund.objects.all()
        funds_data = []

        for fund in funds:
            balance_data = Balance.objects.filter(fund=fund).order_by('date')
            daily_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='daily_performance').order_by('date')
            monthly_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='monthly_performance').order_by('date')
            cumulative_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='cumulative_performance').order_by('date')
            asset_allocation_data = get_asset_allocation_fund(fund)

            fund_data = {
                'id': fund.id,
                'name': fund.name,
                'balance_labels': [item.date.strftime('%Y-%m-%d') for item in balance_data],
                'balance_values': [float(item.value_usd) for item in balance_data],
                'daily_labels': [item.date.strftime('%Y-%m-%d') for item in daily_performance_data],
                'daily_values': [float(item.value) for item in daily_performance_data],
                'monthly_labels': [item.date.strftime('%Y-%m') for item in monthly_performance_data],
                'monthly_values': [float(item.value) for item in monthly_performance_data],
                'cumulative_labels': [item.date.strftime('%Y-%m') for item in cumulative_performance_data],
                'cumulative_values': [float(item.value) for item in cumulative_performance_data],
                'asset_allocation': asset_allocation_data,
            }
            funds_data.append(fund_data)

        return JsonResponse({"status": "success", "funds_data": funds_data})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    
def add_assets(request):
    if request.method == 'POST':
        formset = AssetFormSet(request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.value_usd = instance.amount * instance.price
                instance.save()
            messages.success(request, 'Assets added successfully!')
            return redirect('add_assets')
    else:
        formset = AssetFormSet(queryset=Asset.objects.none())

    strategies = Strategy.objects.all()

    return render(request, 'funds_and_strategies/add_assets.html', {
        'formset': formset,
        'strategies': strategies
    })

def add_transactions(request):
    if request.method == 'POST':
        formset = TransactionFormSet(request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.value_usd = instance.amount * instance.price
                
                exchange_rate = ExchangeRate.objects.filter(from_currency='EUR', to_currency='USD', date=instance.date).first()
                
                if exchange_rate:
                    instance.value_eur = instance.value_usd / exchange_rate.rate
                else:
                    latest_exchange_rate = ExchangeRate.objects.filter(from_currency='EUR', to_currency='USD').order_by('-date').first()
                    if latest_exchange_rate:
                        instance.value_eur = instance.value_usd / latest_exchange_rate.rate
                    else:
                        instance.value_eur = None

                instance.save()
                
            messages.success(request, 'Transactions added successfully!')
            return redirect('add_transactions')
    else:
        formset = TransactionFormSet(queryset=Transaction.objects.none())

    strategies = Strategy.objects.all()

    return render(request, 'funds_and_strategies/add_transactions.html', {
        'formset': formset,
        'strategies': strategies
    })

def get_asset_allocation_fund(fund):
    latest_date = Asset.objects.filter(strategy__fund=fund).aggregate(latest_date=Max('date'))['latest_date']
    assets = Asset.objects.filter(strategy__fund=fund, date=latest_date)
    asset_totals = defaultdict(lambda: {'value_usd': 0, 'amount':0, 'percentage': 0})
    total_value = assets.aggregate(total=Sum('value_usd'))['total'] or 1

    for asset in assets:
        asset_totals[asset.name]['value_usd'] += asset.value_usd
        asset_totals[asset.name]['amount'] += asset.amount

    asset_allocation = []
    for asset_name, data in asset_totals.items():
        percentage = (data['value_usd'] / total_value) * 100
        if percentage > 0.1:
            asset_allocation.append({
                'name': asset_name,
                'value_usd': float(data['value_usd']),
                'amount': float(data['amount']),
                'percentage': float(percentage),
            })
    
    # Ordina per percentuale decrescente
    asset_allocation = sorted(asset_allocation, key=lambda x: x['percentage'], reverse=True)
    return asset_allocation

def funds(request):
    funds = Fund.objects.all()
    funds_data = []

    for fund in funds:
        balance_data = Balance.objects.filter(fund=fund).order_by('date')
        daily_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='daily_performance').order_by('date')
        weekly_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='weekly_performance').order_by('date')
        monthly_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='monthly_performance').order_by('date')
        annual_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='annual_performance').order_by('date')
        cumulative_performance_data = PerformanceMetric.objects.filter(fund=fund, metric_name='cumulative_performance').order_by('date')
        asset_allocation_data = get_asset_allocation_fund(fund)
        
        fund_data = {
            'id': fund.id,
            'name': fund.name,
            'balance_labels': [item.date.strftime('%Y-%m-%d') for item in balance_data],
            'balance_values': [float(item.value_usd) for item in balance_data], 
            'balance_values_eur': [float(item.value_eur) for item in balance_data], 
            'daily_labels': [item.date.strftime('%Y-%m-%d') for item in daily_performance_data],
            'daily_values': [float(item.value) for item in daily_performance_data], 
            'daily_values_eur': [float(item.value_eur) for item in daily_performance_data], 
            'weekly_labels': [item.date.strftime('%Y-%m-%d') for item in weekly_performance_data],
            'weekly_values': [float(item.value) for item in weekly_performance_data],
            'weekly_values_eur': [float(item.value_eur) for item in weekly_performance_data], 
            'monthly_labels': [item.date.strftime('%Y-%m') for item in monthly_performance_data],
            'monthly_values': [float(item.value) for item in monthly_performance_data], 
            'monthly_values_eur': [float(item.value_eur) for item in monthly_performance_data],  
            'annual_labels': [item.date.strftime('%Y') for item in annual_performance_data],
            'annual_values': [float(item.value) for item in annual_performance_data],
            'annual_values_eur': [float(item.value_eur) for item in annual_performance_data], 
            'cumulative_labels': [item.date.strftime('%Y-%m-%d') for item in cumulative_performance_data],
            'cumulative_values': [float(item.value) for item in cumulative_performance_data],
            'cumulative_values_eur': [float(item.value_eur) for item in cumulative_performance_data], 
            'asset_allocation': asset_allocation_data,
        }

        funds_data.append(fund_data)

    context = {
        'funds': funds,
        'funds_data': json.dumps(funds_data),  
    }
    return render(request, 'funds_and_strategies/funds.html', context)

def get_asset_allocation_strategy(strategy):
    latest_date = Asset.objects.filter(strategy=strategy).aggregate(latest_date=Max('date'))['latest_date']
    assets = Asset.objects.filter(strategy=strategy, date=latest_date)
    asset_totals = defaultdict(lambda: {'value_usd': 0, 'amount':0, 'percentage': 0})
    total_value = assets.aggregate(total=Sum('value_usd'))['total'] or 1

    for asset in assets:
        asset_totals[asset.name]['value_usd'] += asset.value_usd
        asset_totals[asset.name]['amount'] += asset.amount

    asset_allocation = []
    for asset_name, data in asset_totals.items():
        percentage = (data['value_usd'] / total_value) * 100
        if percentage > 0.1:
            asset_allocation.append({
                'name': asset_name,
                'value_usd': float(data['value_usd']),
                'amount': float(data['amount']),
                'percentage': float(percentage),
            })
    
    asset_allocation = sorted(asset_allocation, key=lambda x: x['percentage'], reverse=True)
    return asset_allocation

def strategies(request, fund_id):
    fund = get_object_or_404(Fund, id=fund_id)
    strategies = Strategy.objects.filter(fund=fund)

    # Prepara i dati per tutte le strategie
    strategies_data = []
    for strategy in strategies:
        balance_data = Balance.objects.filter(strategy=strategy).order_by('date')
        daily_performance_data = PerformanceMetric.objects.filter(strategy=strategy, metric_name='daily_performance').order_by('date')
        weekly_performance_data = PerformanceMetric.objects.filter(strategy=strategy, metric_name='weekly_performance').order_by('date')
        monthly_performance_data = PerformanceMetric.objects.filter(strategy=strategy, metric_name='monthly_performance').order_by('date')
        annual_performance_data = PerformanceMetric.objects.filter(strategy=strategy, metric_name='annual_performance').order_by('date')
        cumulative_performance_data = PerformanceMetric.objects.filter(strategy=strategy, metric_name='cumulative_performance').order_by('date')
        asset_allocation_data = get_asset_allocation_strategy(strategy)

        strategy_data = {
            'id': strategy.id,
            'name': strategy.name,
            'balance_labels': [item.date.strftime('%Y-%m-%d') for item in balance_data],
            'balance_values': [float(item.value_usd) for item in balance_data], 
            'balance_values_eur': [float(item.value_eur) for item in balance_data],
            'daily_labels': [item.date.strftime('%Y-%m-%d') for item in daily_performance_data],
            'daily_values': [float(item.value) for item in daily_performance_data], 
            'daily_values_eur': [float(item.value_eur) for item in daily_performance_data],
            'weekly_labels': [item.date.strftime('%Y-%m-%d') for item in weekly_performance_data],
            'weekly_values': [float(item.value) for item in weekly_performance_data],
            'weekly_values_eur': [float(item.value_eur) for item in weekly_performance_data],
            'monthly_labels': [item.date.strftime('%Y-%m') for item in monthly_performance_data],
            'monthly_values': [float(item.value) for item in monthly_performance_data], 
            'monthly_values_eur': [float(item.value_eur) for item in monthly_performance_data],
            'annual_labels': [item.date.strftime('%Y') for item in annual_performance_data],
            'annual_values': [float(item.value) for item in annual_performance_data],
            'annual_values_eur': [float(item.value_eur) for item in annual_performance_data],
            'cumulative_labels': [item.date.strftime('%Y-%m-%d') for item in cumulative_performance_data],
            'cumulative_values': [float(item.value) for item in cumulative_performance_data],
            'cumulative_values_eur': [float(item.value_eur) for item in cumulative_performance_data],
            'asset_allocation': asset_allocation_data,
        }

        strategies_data.append(strategy_data)

    context = {
        'strategies': strategies,
        'strategies_data': json.dumps(strategies_data), 
    }
    return render(request, 'funds_and_strategies/strategies.html', context)

def reports(request):
    funds = Fund.objects.all()
    selected_fund_id = request.GET.get('fund', None)
    selected_currency = request.GET.get('currency', 'USD')
    selected_fund = Fund.objects.get(id=selected_fund_id) if selected_fund_id else None

    fund_performance = {}
    strategy_performance = []
    strategy_weights = []

    if selected_fund:
        ytd = PerformanceMetric.objects.filter(fund=selected_fund, metric_name="annual_performance").last()
        mtd = PerformanceMetric.objects.filter(fund=selected_fund, metric_name="monthly_performance").last()
        wtd = PerformanceMetric.objects.filter(fund=selected_fund, metric_name="weekly_performance").last()
        latest_balance = Balance.objects.filter(fund=selected_fund).order_by('-date').first()

        fund_performance = {
            'ytd': ytd,
            'mtd': mtd,
            'wtd': wtd,
            'latest_balance': latest_balance,
            'ytd_class': get_css_class_for_metric(ytd, selected_currency),
            'mtd_class': get_css_class_for_metric(mtd, selected_currency),
            'wtd_class': get_css_class_for_metric(wtd, selected_currency),
        }

        strategies = Strategy.objects.filter(fund=selected_fund)
        total_balance = latest_balance.value_usd if selected_currency == 'USD' else latest_balance.value_eur

        for strategy in strategies:
            ytd = PerformanceMetric.objects.filter(strategy=strategy, metric_name="annual_performance").last()
            mtd = PerformanceMetric.objects.filter(strategy=strategy, metric_name="monthly_performance").last()
            wtd = PerformanceMetric.objects.filter(strategy=strategy, metric_name="weekly_performance").last()
            latest_strategy_balance = Balance.objects.filter(strategy=strategy).order_by('-date').first()

            strategy_performance.append({
                'strategy': strategy,
                'ytd': ytd,
                'mtd': mtd,
                'wtd': wtd,
                'latest_balance': latest_strategy_balance,
                'ytd_class': get_css_class_for_metric(ytd, selected_currency),
                'mtd_class': get_css_class_for_metric(mtd, selected_currency),
                'wtd_class': get_css_class_for_metric(wtd, selected_currency),
            })

            if latest_strategy_balance:
                strategy_balance = latest_strategy_balance.value_usd if selected_currency == 'USD' else latest_strategy_balance.value_eur
                strategy_weight = (strategy_balance / total_balance) * 100 if total_balance > 0 else 0
                strategy_weights.append({
                    'strategy': strategy.name,
                    'balance': strategy_balance,
                    'weight': strategy_weight,
                })

    context = {
        'funds': funds,
        'selected_fund': selected_fund,
        'selected_currency': selected_currency,
        'fund_performance': fund_performance,
        'strategy_performance': strategy_performance,
        'strategy_weights': strategy_weights,
    }

    return render(request, 'funds_and_strategies/reports.html', context)

def get_css_class_for_metric(metric, currency):
    if metric:
        value = metric.value if currency == 'USD' else metric.value_eur
        return 'text-success' if value >= 0 else 'text-danger'
    return ''

def all_reports(request):
    reports = SavedReport.objects.all().order_by('date')
    context = {
        'reports': reports,
    }
    return render(request, 'funds_and_strategies/all_reports.html', context)

def save_report(request):
    if request.method == 'POST':
        fund_id = request.POST.get('fund_id')
        selected_currency = request.POST.get('currency')
        selected_fund = Fund.objects.get(id=fund_id)

        # Raccogliere i dati di performance del fondo e delle strategie
        fund_performance = {
            'ytd': PerformanceMetric.objects.filter(fund=selected_fund, metric_name="annual_performance").last(),
            'mtd': PerformanceMetric.objects.filter(fund=selected_fund, metric_name="monthly_performance").last(),
            'wtd': PerformanceMetric.objects.filter(fund=selected_fund, metric_name="weekly_performance").last(),
            'latest_balance': Balance.objects.filter(fund=selected_fund).order_by('-date').first(),
        }

        strategies = Strategy.objects.filter(fund=selected_fund)
        strategy_performance = []
        for strategy in strategies:
            strategy_performance.append({
                'strategy': strategy,
                'ytd': PerformanceMetric.objects.filter(strategy=strategy, metric_name="annual_performance").last(),
                'mtd': PerformanceMetric.objects.filter(strategy=strategy, metric_name="monthly_performance").last(),
                'wtd': PerformanceMetric.objects.filter(strategy=strategy, metric_name="weekly_performance").last(),
                'latest_balance': Balance.objects.filter(strategy=strategy).order_by('-date').first(),
            })

        report_name = f"{selected_fund.name} Report {datetime.now().strftime('%B %Y')} ({selected_currency})"

        existing_report = SavedReport.objects.filter(name=report_name).first()
        if existing_report:
            if os.path.exists(existing_report.file_path):
                os.remove(existing_report.file_path)
            existing_report.delete()

        file_name = create_pdf_report(selected_fund, selected_currency, fund_performance, strategy_performance)

        saved_report = SavedReport.objects.create(
            name=f"{selected_fund.name} Report {datetime.now().strftime('%B %Y')} ({selected_currency})",
            file_path=file_name,
            date=datetime.now(),
            fund=selected_fund,
            currency=selected_currency
        )

        return redirect('reports')

def create_pdf_report(fund, currency, fund_performance, strategy_performance):
    # Definisci il nome del file
    file_name = f"{fund.name}_{currency}_Report_{datetime.now().strftime('%Y_%m_%d')}.pdf"

    # Crea il documento PDF
    pdf = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []

    # Aggiungi il titolo
    styles = getSampleStyleSheet()
    title = Paragraph(f"Performance Report for {fund.name}", styles['Title'])
    elements.append(title)

    # Aggiungi una tabella con le performance del fondo
    data = [
        ['Performance Type', f'Value ({currency})'],
        ['YTD', f"{fund_performance['ytd'].value if fund_performance['ytd'] else 0 if currency == 'USD' else fund_performance['ytd'].value_eur if fund_performance['ytd'] else 0}%"],
        ['MTD', f"{fund_performance['mtd'].value if fund_performance['mtd'] else 0 if currency == 'USD' else fund_performance['mtd'].value_eur if fund_performance['mtd'] else 0}%"],
        ['WTD', f"{fund_performance['wtd'].value if fund_performance['wtd'] else 0 if currency == 'USD' else fund_performance['wtd'].value_eur if fund_performance['wtd'] else 0}%"],
        ['Latest Balance', f"{fund_performance['latest_balance'].value_usd if fund_performance['latest_balance'] else 0 if currency == 'USD' else fund_performance['latest_balance'].value_eur if fund_performance['latest_balance'] else 0}"]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    # Aggiungi spazio tra le tabelle
    elements.append(Spacer(1, 12))

    # Aggiungi una tabella con le performance delle strategie
    strategy_data = [['Strategy', 'YTD', 'MTD', 'WTD', f'Latest Balance ({currency})']]
    for sp in strategy_performance:
        ytd_value = sp['ytd'].value if sp['ytd'] else 0 if currency == 'USD' else sp['ytd'].value_eur if sp['ytd'] else 0
        mtd_value = sp['mtd'].value if sp['mtd'] else 0 if currency == 'USD' else sp['mtd'].value_eur if sp['mtd'] else 0
        wtd_value = sp['wtd'].value if sp['wtd'] else 0 if currency == 'USD' else sp['wtd'].value_eur if sp['wtd'] else 0
        latest_balance_value = sp['latest_balance'].value_usd if sp['latest_balance'] else 0 if currency == 'USD' else sp['latest_balance'].value_eur if sp['latest_balance'] else 0

        strategy_data.append([
            sp['strategy'].name,
            f"{ytd_value}%",
            f"{mtd_value}%",
            f"{wtd_value}%",
            f"{latest_balance_value}"
        ])

    strategy_table = Table(strategy_data)
    strategy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(strategy_table)

    # Aggiungi spazio tra le tabelle
    elements.append(Spacer(1, 12))

    # Calcola i pesi percentuali delle strategie
    total_balance = sum(sp['latest_balance'].value_usd if sp['latest_balance'] else 0 if currency == 'USD' else sp['latest_balance'].value_eur if sp['latest_balance'] else 0 for sp in strategy_performance)
    weight_data = [['Strategy', f'Weight (%)']]
    for sp in strategy_performance:
        latest_balance_value = sp['latest_balance'].value_usd if sp['latest_balance'] else 0 if currency == 'USD' else sp['latest_balance'].value_eur if sp['latest_balance'] else 0
        weight_percentage = (latest_balance_value / total_balance * 100) if total_balance != 0 else 0
        weight_data.append([sp['strategy'].name, f"{weight_percentage:.2f}%"])

    weight_table = Table(weight_data)
    weight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(weight_table)

    # Costruisci il PDF
    pdf.build(elements)

    return file_name

def download_report(request, report_id):
    try:
        report = SavedReport.objects.get(id=report_id)
        file_path = report.file_path
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.name}.pdf"'
        return response
    except SavedReport.DoesNotExist:
        raise Http404("Report not found")
