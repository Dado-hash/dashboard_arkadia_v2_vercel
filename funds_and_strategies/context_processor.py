from .models import SavedReport

def recent_reports_processor(request):
    recent_reports = SavedReport.objects.order_by('date')[:3]
    return {'recent_reports': recent_reports}