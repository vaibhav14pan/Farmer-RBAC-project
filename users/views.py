from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, FileResponse, Http404
from functools import wraps
from .models import Block, User, Farmer
from .forms import LoginForm, ProfileForm, UserForm, BlockForm, FarmerForm, DateRangeReportForm
import sys
import redis
from django.conf import settings
import datetime
import os
from django.utils import timezone

def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')  # Redirect to login if session expired

            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponseForbidden("You do not have permission to access this page.")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user:
            login(request, user)
              # 30 minutes session expiry
            return redirect('dashboard')
        else:
            print("login_view: Authentication failed", file=sys.stderr)
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# Connect to Redis
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

@login_required
def dashboard(request):
    user_role = getattr(request.user, 'role', None)
    if user_role == 'admin':
        return render(request, 'users/admin_dashboard.html')
    elif user_role == 'supervisor':
        return render(request, 'users/supervisor_dashboard.html')
    elif user_role == 'surveyor':
        return render(request, 'users/surveyor_dashboard.html')

    print("dashboard: No valid role found, logging out", file=sys.stderr)
    logout(request)
    return redirect('login')

@login_required
@role_required(['admin'])
def create_block(request):
    form = BlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'users/create_block.html', {'form': form})

@login_required
@role_required(['admin'])
def create_block(request):
    form = BlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'users/create_block.html', {'form': form})

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import User
from .forms import UserForm
from django.contrib.auth.decorators import login_required

@login_required
@role_required(['admin'])
def create_or_edit_user(request, user_id=None):
    user = get_object_or_404(User, id=user_id) if user_id else None
    is_editing = user is not None
    form = UserForm(request.POST or None, request.FILES or None, instance=user)

    if is_editing:
        form.fields['password'].required = False  # Make password optional when editing
        form.fields['block'].label = "Change Block"  # Update label for clarity

    if request.method == 'POST' and form.is_valid():
        assigned_block = form.cleaned_data.get('block')
        role = form.cleaned_data.get('role')

        # Prevent duplicate supervisor block assignment
        if role == 'supervisor':
            existing_supervisor = User.objects.filter(role='supervisor', block=assigned_block)
            if user:
                existing_supervisor = existing_supervisor.exclude(id=user.id)
            if existing_supervisor.exists():
                messages.error(request, f"Block '{assigned_block}' is already assigned to another supervisor. Please choose a different block.")
                return render(request, 'users/create_user.html', {'form': form, 'user': user, 'is_editing': is_editing})

        user = form.save(commit=False)

        # If editing, allow password and image updates
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)  # Update password only if provided

        if 'profile_image' in request.FILES:
            user.image = request.FILES['profile_image']  # Update profile image if uploaded

        user.save()
        messages.success(request, f"User '{user.username}' has been successfully {'updated' if is_editing else 'created'}.")
        return redirect('list_users')

    return render(request, 'users/create_user.html', {
        'form': form,
        'user': user,
        'is_editing': is_editing,
    })


@login_required
@role_required(['surveyor'])
def add_or_edit_farmer(request, farmer_id=None):
    if farmer_id:
        farmer = get_object_or_404(Farmer, id=farmer_id, added_by=request.user)
    else:
        farmer = None

    form = FarmerForm(request.POST or None, request.FILES or None, instance=farmer)  # Handle file uploads

    if request.method == 'POST' and form.is_valid():
        farmer = form.save(commit=False)

        # Ensure the farmer is assigned to the surveyor's block
        if request.user.block:
            farmer.block = request.user.block
        else:
            return render(request, 'users/add_farmer.html', {
                'form': form, 
                'error': 'No block assigned to your account.'
            })
        
        farmer.added_by = request.user

        # Save uploaded images (if provided)
        if 'image' in request.FILES:
            farmer.image = request.FILES['image']
        if 'aadhar_image' in request.FILES:
            farmer.aadhar_image = request.FILES['aadhar_image']

        farmer.save()
        return redirect('dashboard')

    return render(request, 'users/add_farmer.html', {'form': form, 'farmer': farmer})




@login_required
@role_required(['admin', 'supervisor'])
def list_users(request):
    role_filter = request.GET.get('role', None)  # Get role filter from URL params
    block_filter = request.GET.get('block', None)  # Get block filter from URL params
    search_query = request.GET.get('search', '').strip().lower()
    
    users = User.objects.all().select_related('block')

    if role_filter:
        users = users.filter(role=role_filter)
    if block_filter:
        users = users.filter(block__id=block_filter)
    if search_query:
        users = users.filter(username__icontains=search_query)
    
    blocks = Block.objects.all()  # Fetch all blocks for dropdown filter
    
    return render(request, 'users/list_users.html', {
        'users': users,
        'blocks': blocks,
        'selected_role': role_filter,
        'selected_block': block_filter,
        'search_query': search_query,
    })



@login_required
@role_required(['admin'])
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    if user.role != 'admin':  # Prevent deleting other admins
        user.delete()
    return redirect('list_users')

@login_required
@role_required(['supervisor'])
def list_surveyors(request):
    """Allow a supervisor to see only surveyors assigned to their block."""
    if not request.user.block:
        return HttpResponseForbidden("No block assigned to your account.")
    
    surveyors = User.objects.filter(role='surveyor', block=request.user.block)
    
    return render(request, 'users/surveyors_list.html', {
        'surveyors': surveyors
    })


@login_required
@role_required(['surveyor'])
def delete_farmer(request, farmer_id):
    """Allow a surveyor to delete a farmer only if the farmer belongs to their assigned block."""
    farmer = get_object_or_404(Farmer, id=farmer_id, block=request.user.block)
    farmer.delete()
    return redirect('list_farmers')

@login_required
@role_required(['surveyor'])
def list_farmers(request):
    farmers = Farmer.objects.filter(block=request.user.block)  # Only show farmers in the surveyor's block
    return render(request, 'users/list_farmers.html', {'farmers': farmers})


@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Handle password update
            new_password = form.cleaned_data.get('password')
            if new_password:
                user.set_password(new_password)
            
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=user)
    
    return render(request, 'users/profile.html', {'form': form, 'user': user})

@login_required
def list_blocks(request):
    """
    View function to list all blocks.
    Admin can see all blocks.
    Supervisors and Surveyors can only see their assigned block.
    """
    if request.user.role == 'admin':
        blocks = Block.objects.all()
    else:
        # For supervisors and surveyors, only show their assigned block
        blocks = Block.objects.filter(id=request.user.block.id)
    
    context = {
        'blocks': blocks,
        'user': request.user,
    }
    return render(request, 'users/list_blocks.html', context)

@login_required
@role_required(['admin'])
def edit_block(request, block_id):
    block = get_object_or_404(Block, id=block_id)
    form = BlockForm(request.POST or None, instance=block)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('list_blocks')  # Redirect to the blocks list after successful update
    
    return render(request, 'users/edit_block.html', {'form': form, 'block': block})

@login_required
@role_required(['admin'])
def delete_block(request, block_id):
    block = get_object_or_404(Block, id=block_id)
    block.delete()
    return redirect('list_blocks')

@login_required
def profile(request):
    # If the user is a farmer, restrict profile view
    if request.user.role == 'farmer':
        return HttpResponseForbidden("You cannot view this section.")
    
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def statistics(request):
    """
    Statistics view showing metrics based on user role.
    Displays Redis-based statistics about farmer counts.
    """
    user = request.user
    context = {'user': user}
    
    if user.is_superuser or user.role == 'admin':
        # Add admin-specific statistics
        blocks = Block.objects.all()
        block_stats = []
        
        for block in blocks:
            block_key = f"block:{block.id}:farmers:count"
            count = int(redis_client.get(block_key) or 0)
            block_stats.append({
                'name': block.name,
                'count': count,
                'id': block.id
            })
        
        # Get all users except superusers
        users = User.objects.exclude(is_superuser=True)
        user_stats = []
        
        for u in users:
            today = datetime.date.today().isoformat()
            today_key = f"user:{u.id}:farmers:added:{today}"
            today_count = int(redis_client.get(today_key) or 0)
            
            user_stats.append({
                'username': u.username,
                'role': u.role,
                'block': u.block.name if u.block else 'Not Assigned',
                'today_count': today_count,
                'total_farmers': Farmer.objects.filter(added_by=u).count()
            })
        
        context.update({
            'block_stats': block_stats,
            'user_stats': user_stats,
            'total_farmers': Farmer.objects.count(),
            'is_admin_view': True
        })
    
    # Keep your existing surveyor logic here...
    
    return render(request, 'users/statistics.html', context)

def get_latest_csv_file(prefix):
    """Helper function to get the most recent CSV file with a specific prefix"""
    reports_dir = os.path.join(settings.BASE_DIR, 'reports')
    if not os.path.exists(reports_dir):
        return None
    
    # Filter files by the prefix
    matching_files = [f for f in os.listdir(reports_dir) if f.startswith(prefix) and f.endswith('.csv')]
    
    if not matching_files:
        return None
        
    # Sort by modification time (newest first)
    matching_files.sort(key=lambda f: os.path.getmtime(os.path.join(reports_dir, f)), reverse=True)
    
    return os.path.join(reports_dir, matching_files[0])

def download_csv_by_user(request):
    """View to download the latest farmers by user CSV"""
    if not request.user.is_authenticated or request.user.role != 'admin':
        raise Http404("Not found")
        
    file_path = get_latest_csv_file('farmers_by_user')
    
    if not file_path or not os.path.exists(file_path):
        # If no file exists, generate one for current month
        from django.core.management import call_command
        now = timezone.now()
        call_command('generate_monthly_report', month=now.month, year=now.year)
        
        # Try getting the file again
        file_path = get_latest_csv_file('farmers_by_user')
        if not file_path or not os.path.exists(file_path):
            raise Http404("Report not found. Please generate reports first.")
    
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response

def download_csv_by_block(request):
    """View to download the latest farmers by block CSV"""
    if not request.user.is_authenticated or request.user.role != 'admin':
        raise Http404("Not found")
        
    file_path = get_latest_csv_file('farmers_by_block')
    
    if not file_path or not os.path.exists(file_path):
        # If no file exists, generate one for current month
        from django.core.management import call_command
        now = timezone.now()
        call_command('generate_monthly_report', month=now.month, year=now.year)
        
        # Try getting the file again
        file_path = get_latest_csv_file('farmers_by_block')
        if not file_path or not os.path.exists(file_path):
            raise Http404("Report not found. Please generate reports first.")
    
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response

def farmer_report(request):
    if request.method == 'POST':
        form = DateRangeReportForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Query using date range
            farmers = Farmer.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Process data for report...
    else:
        form = DateRangeReportForm()
    
    return render(request, 'users/farmer_report.html', {'form': form, 'data': data})

@login_required
@role_required(['admin'])
def date_range_report(request):
    if request.method == 'POST':
        form = DateRangeReportForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Generate report using management command
            from django.core.management import call_command
            
            # Format dates for command
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Call command to generate report
            call_command('generate_monthly_report', 
                         start_date=start_date_str,
                         end_date=end_date_str)
            
            # Get the generated report filenames
            start_date_fmt = start_date.strftime('%Y%m%d')
            end_date_fmt = end_date.strftime('%Y%m%d')
            
            # Prepare report links
            reports = [
                {
                    'type': 'user',
                    'name': 'Farmers by User Report',
                    'filename': f"farmers_by_user_{start_date_fmt}_to_{end_date_fmt}.csv"
                },
                {
                    'type': 'block',
                    'name': 'Farmers by Block Report',
                    'filename': f"farmers_by_block_{start_date_fmt}_to_{end_date_fmt}.csv"
                },
                {
                    'type': 'farmer',
                    'name': 'Detailed Farmer Report',
                    'filename': f"detailed_farmers_{start_date_fmt}_to_{end_date_fmt}.csv"
                }
            ]
            
            return render(request, 'users/date_range_report.html', {
                'form': form,
                'message': f"Reports generated for {start_date_str} to {end_date_str}",
                'reports': reports
            })
    else:
        form = DateRangeReportForm()
    
    return render(request, 'users/date_range_report.html', {'form': form})


@login_required
@role_required(['admin'])
def download_generated_report(request, report_type, filename):
    """Download a specific generated report file"""
    if not request.user.is_authenticated or request.user.role != 'admin':
        raise Http404("Not found")
    
    reports_dir = os.path.join(settings.BASE_DIR, 'reports')
    file_path = os.path.join(reports_dir, filename)
    
    if not os.path.exists(file_path):
        raise Http404(f"Report file not found. Please generate the report first.")
    
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response