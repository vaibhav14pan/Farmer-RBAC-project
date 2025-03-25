import csv
import os
import datetime
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.conf import settings
from django.utils import timezone
from users.models import Farmer, User, Block

class Command(BaseCommand):
    help = 'Generate farmer addition report for a specific date range'

    def add_arguments(self, parser):
        # Date range arguments
        parser.add_argument(
            '--start-date', 
            type=str,
            help='Start date in YYYY-MM-DD format'
        )
        parser.add_argument(
            '--end-date', 
            type=str,
            help='End date in YYYY-MM-DD format'
        )

    def handle(self, *args, **options):
        # Parse dates from arguments
        start_date_str = options.get('start_date')
        end_date_str = options.get('end_date')
        
        # Default to previous month if no dates provided
        if not start_date_str or not end_date_str:
            now = timezone.now()
            month = now.month - 1
            year = now.year
            if month == 0:
                month = 12
                year = year - 1
            
            start_date = datetime.date(year, month, 1)
            if month == 12:
                end_date = datetime.date(year + 1, 1, 1)
            else:
                end_date = datetime.date(year, month + 1, 1)
            
            self.stdout.write(f"No date range specified. Defaulting to {start_date.strftime('%B %Y')}...")
        else:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                # Add one day to end_date to make it inclusive
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() + datetime.timedelta(days=1)
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return
        
        self.stdout.write(f"Generating report from {start_date.strftime('%Y-%m-%d')} to {(end_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}...")
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(settings.BASE_DIR, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate report by user
        self._generate_user_report(start_date, end_date, reports_dir)
        
        # Generate report by block
        self._generate_block_report(start_date, end_date, reports_dir)
        
        # Generate detailed farmer report
        self._generate_detailed_farmer_report(start_date, end_date, reports_dir)
        
        self.stdout.write(self.style.SUCCESS('Reports generated successfully!'))

    def _generate_user_report(self, start_date, end_date, reports_dir):
        # Query farmers added in the given date range, grouped by user
        user_stats = (
            Farmer.objects
            .filter(date_added__gte=start_date, date_added__lt=end_date)
            .values('added_by')
            .annotate(farmer_count=Count('id'))
            .order_by('-farmer_count')
        )
        
        # Create a map of user IDs to usernames for reference
        users = {user.id: user.username for user in User.objects.all()}
        
        # Generate CSV file
        filename = os.path.join(
            reports_dir, 
            f"farmers_by_user_{start_date.strftime('%Y%m%d')}_to_{(end_date - datetime.timedelta(days=1)).strftime('%Y%m%d')}.csv"
        )
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Username', 'Role', 'Farmers Added'])
            
            for stat in user_stats:
                user_id = stat['added_by']
                user = User.objects.get(id=user_id)
                writer.writerow([
                    user.username,
                    user.role,
                    stat['farmer_count']
                ])
        
        self.stdout.write(f"User report saved to {filename}")

    def _generate_block_report(self, start_date, end_date, reports_dir):
        # Query farmers added in the given date range, grouped by block
        block_stats = (
            Farmer.objects
            .filter(date_added__gte=start_date, date_added__lt=end_date)
            .values('block')
            .annotate(farmer_count=Count('id'))
            .order_by('-farmer_count')
        )
        
        # Create a map of block IDs to names for reference
        blocks = {block.id: block.name for block in Block.objects.all()}
        
        # Generate CSV file
        filename = os.path.join(
            reports_dir, 
            f"farmers_by_block_{start_date.strftime('%Y%m%d')}_to_{(end_date - datetime.timedelta(days=1)).strftime('%Y%m%d')}.csv"
        )
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Block Name', 'Farmers Added'])
            
            for stat in block_stats:
                block_id = stat['block']
                block_name = blocks.get(block_id, 'Unknown')
                writer.writerow([
                    block_name,
                    stat['farmer_count']
                ])
        
        self.stdout.write(f"Block report saved to {filename}")
        
    def _generate_detailed_farmer_report(self, start_date, end_date, reports_dir):
        # Query all farmers added in the given date range
        farmers = (
            Farmer.objects
            .filter(date_added__gte=start_date, date_added__lt=end_date)
            .select_related('added_by', 'block')  # Optimize queries
            .order_by('date_added')
        )
        
        # Generate CSV file
        filename = os.path.join(
            reports_dir, 
            f"detailed_farmers_{start_date.strftime('%Y%m%d')}_to_{(end_date - datetime.timedelta(days=1)).strftime('%Y%m%d')}.csv"
        )
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Headers - adjust based on your Farmer model fields
            writer.writerow([
                'ID', 
                'Name', 
                'Phone', 
                'Village',
                'Block',
                'Date Added',
                'Added By',
                'Gender',
                'Age',
                # Add other relevant fields from your Farmer model
            ])
            
            for farmer in farmers:
                # Get the related block name
                block_name = farmer.block.name if farmer.block else 'Unknown'
                
                # Get the username of who added this farmer
                added_by_username = farmer.added_by.username if farmer.added_by else 'Unknown'
                
                # Write farmer details - adjust based on your model fields
                writer.writerow([
                    farmer.id,
                    farmer.name,
                    getattr(farmer, 'phone', 'N/A'),  # Using getattr to safely handle attributes that might not exist
                    getattr(farmer, 'village', 'N/A'),
                    block_name,
                    farmer.date_added.strftime('%Y-%m-%d'),
                    added_by_username,
                    getattr(farmer, 'gender', 'N/A'),
                    getattr(farmer, 'age', 'N/A'),
                    # Add other relevant fields from your Farmer model
                ])
        
        self.stdout.write(f"Detailed farmer report saved to {filename}") 