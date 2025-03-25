from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils import timezone
import os
from django.conf import settings

class ReportsAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reports/', self.admin_view(self.reports_view), name='reports'),
        ]
        return custom_urls + urls
    
    def reports_view(self, request):
        # Get available report files
        reports_dir = os.path.join(settings.BASE_DIR, 'reports')
        available_reports = []
        
        if os.path.exists(reports_dir):
            for file in os.listdir(reports_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join('/reports', file)  # URL path, not file system path
                    if 'by_user' in file:
                        report_type = 'Farmers by User'
                    elif 'by_block' in file:
                        report_type = 'Farmers by Block'
                    else:
                        report_type = 'Other Report'
                    
                    # Extract date from filename
                    # Assuming format: farmers_by_user_YYYY_MM.csv
                    parts = file.split('_')
                    if len(parts) >= 4:
                        try:
                            year = parts[-2]
                            month = parts[-1].split('.')[0]
                            date_str = f"{year}-{month}"
                        except:
                            date_str = "Unknown date"
                    else:
                        date_str = "Unknown date"
                    
                    available_reports.append({
                        'name': report_type,
                        'date': date_str,
                        'url': file_path
                    })
        
        context = {
            'title': 'Farmer Reports',
            'reports': available_reports,
            **self.each_context(request),
        }
        return render(request, 'admin/reports.html', context)

# Register with the custom admin site
admin_site = ReportsAdminSite(name='customadmin') 