from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Issue, UserProfile, Comment
from .forms import IssueForm, CommentForm
from django.contrib.auth.models import User
from django.db.models import Q,Count

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Issue, Comment, UserProfile
from .forms import UserProfileForm, EditUserForm  # You'll need to create these forms


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get("next", "issues:dashboard"))
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "issues/login.html")

def user_logout(request):
    logout(request)
    return redirect('issues:login')

def home(request):
    return render(request, 'issues/home.html')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Issue

@login_required
def dashboard(request):
    """
    Displays the correct data and template based on the user's profile role.
    """
    # Get the user's role from their profile
    try:
        role = request.user.userprofile.role
    except AttributeError:
        # Fallback if a user has no profile or role
        messages.warning(request, 'Your account is not configured with a role. Please contact an administrator.')
        return redirect('profile')

    # --- Role-based logic ---
    if role == 'admin':
        issues = Issue.objects.all().order_by('-created_at')
        return render(request, 'issues/dashboard.html', {'issues': issues})

    elif role == 'manager':
        issues = Issue.objects.all().order_by('-created_at')
        return render(request, 'issues/dashboard.html', {'issues': issues})

    elif role == 'hardware':    
        issues = Issue.objects.filter(
        assigned_to=request.user,
        status__in=['pending', 'In Progress']
        ).order_by('-created_at')
        return render(request, 'issues/dashboard.html', {'issues': issues})

    elif role == 'employee':
        issues = Issue.objects.filter(
        raised_by=request.user
        ).exclude(
        status='resolved'
        ).order_by('-created_at')
        return render(request, 'issues/dashboard.html', {'issues': issues})
    
    else:
        # Fallback for an unknown role
        messages.error(request, f"Unknown role '{role}' assigned to your profile.")
        return redirect('profile')
    
def create_issue(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.created_by = request.user  # if you track who creates the issue
            issue.save()
            return redirect('issues:my_issues')  # Redirect after creation
    else:
        form = IssueForm()
    
    return render(request, 'issues/create_issue.html', {'form': form})
    
@login_required
def issue_create(request):
    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.raised_by = request.user
            issue.save()
            messages.success(request, 'Issue raised successfully.')
            return redirect('issues:dashboard')
    else:
        form = IssueForm()
    return render(request, 'issues/issue_form.html', {'form': form})

@login_required
def issue_detail(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    comment_form = CommentForm()
    return render(request, 'issues/issue_detail.html', {'issue': issue, 'comment_form': comment_form})

@login_required
def post_comment(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.issue = issue
            comment.author = request.user
            comment.save()
    return redirect('issues:issue_detail', pk=pk)

@login_required
def issue_update_status(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    profile = getattr(request.user, 'userprofile', None)
    role = profile.role if profile else 'employee'
    # Only hardware team and manager can update status / assign
    if role not in ['hardware', 'manager', 'admin']:
        return redirect('issues:dashboard')

    if request.method == 'POST':
        status = request.POST.get('status')
        assigned_id = request.POST.get('assigned_to')
        if status in dict(Issue.STATUS_CHOICES):
            issue.status = status
        if assigned_id:
            try:
                assigned_user = User.objects.get(pk=int(assigned_id))
                issue.assigned_to = assigned_user
            except User.DoesNotExist:
                pass
        issue.save()
        return redirect('issues:issue_detail', pk=pk)

    users = User.objects.filter(is_active=True)
    return render(request, 'issues/issue_update.html', {'issue': issue, 'users': users})

@login_required
def claim_issue(request, pk):
    # Hardware team member claims a pending issue
    issue = get_object_or_404(Issue, pk=pk)
    profile = getattr(request.user, 'userprofile', None)
    role = profile.role if profile else 'employee'
    if role != 'hardware':
        return redirect('issues:dashboard')
    if issue.status == 'pending':
        issue.assigned_to = request.user
        issue.status = 'claimed'
        issue.claimed = True
        issue.save()
    return redirect('issues:dashboard')

@login_required
def resolve_issue(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    profile = getattr(request.user, 'userprofile', None)
    role = profile.role if profile else 'employee'
    # Only assigned hardware or manager can resolve
    if role == 'hardware' and issue.assigned_to != request.user:
        return redirect('issues:dashboard')
    issue.status = 'resolved'
    issue.save()
    return redirect('issues:issue_detail', pk=pk)

@login_required
def issue_list(request):
    issues = Issue.objects.all().order_by('-created_at')  # fetch all issues
    return render(request, 'issues/issue_list.html', {'issues': issues})

@login_required
def reports(request):
    # Count totals
    total_issues = Issue.objects.count()
    open_issues = Issue.objects.filter(status__iexact="open").count()
    resolved_issues = Issue.objects.filter(status__iexact="resolved").count()
    high_priority = Issue.objects.filter(priority__iexact="high").count()

    # Issues grouped by assigned user's role/team via UserProfile
    team_data = (
        Issue.objects
        .values("assigned_to__userprofile__role")   # <-- changed here
        .annotate(count=Count("id"))
    )

    teams = [t["assigned_to__userprofile__role"] or "Unassigned" for t in team_data]
    team_issues = [t["count"] for t in team_data]

    context = {
        "total_issues": total_issues,
        "open_issues": open_issues,
        "resolved_issues": resolved_issues,
        "high_priority": high_priority,
        "teams": teams,
        "team_issues": team_issues,
    }
    return render(request, "issues/reports.html", context)

# Add these views to your issues/views.py file

@login_required
def profile(request):
    """Display user profile page"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user statistics
    issues_raised = Issue.objects.filter(raised_by=request.user)
    assigned_issues = Issue.objects.filter(assigned_to=request.user)
    resolved_issues = Issue.objects.filter(assigned_to=request.user, status='resolved')
    user_comments = Comment.objects.filter(author=request.user)
    
    # Get recent activities (last 10)
    recent_activities = []
    
    # Recent issues created
    for issue in issues_raised.order_by('-created_at')[:5]:
        recent_activities.append({
            'type': 'created',
            'description': f'Created issue: {issue.title}',
            'timestamp': issue.created_at,
        })
    
    # Recent comments
    for comment in user_comments.order_by('-created_at')[:5]:
        recent_activities.append({
            'type': 'commented',
            'description': f'Commented on: {comment.issue.title}',
            'timestamp': comment.created_at,
        })
    
    # Sort by timestamp and get latest 10
    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    context = {
        'issues_raised_count': issues_raised.count(),
        'assigned_issues_count': assigned_issues.count(),
        'resolved_issues_count': resolved_issues.count(),
        'comments_count': user_comments.count(),
        'recent_activities': recent_activities,
    }
    
    return render(request, 'issues/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile information"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = EditUserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('issues:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'issues/edit_profile.html', context)

@login_required
def update_profile_picture(request):
    """Update user profile picture via AJAX or form submission"""
    if request.method == 'POST':
        if 'profile_picture' in request.FILES:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Delete old profile picture if exists
            if profile.profile_picture:
                profile.profile_picture.delete()
            
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            messages.success(request, 'Profile picture updated successfully!')
        else:
            messages.error(request, 'No image file was uploaded.')
    
    return redirect('issues:profile')

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important for keeping user logged in
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('issues:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {'form': form}
    return render(request, 'issues/change_password.html', context)

@login_required
def my_issues(request):
    """Display user's issues (both created and assigned)"""
    # Get issues created by user
    created_issues = Issue.objects.filter(raised_by=request.user)
    
    # Get issues assigned to user
    assigned_issues = Issue.objects.filter(assigned_to=request.user)
    
    # Combine and remove duplicates
    all_user_issues = (created_issues | assigned_issues).distinct().order_by('-created_at')
    
    # Add filter functionality
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    if status_filter:
        all_user_issues = all_user_issues.filter(status=status_filter)
    
    if priority_filter:
        all_user_issues = all_user_issues.filter(priority=priority_filter)
    
    context = {
        'issues': all_user_issues,
        'created_count': created_issues.count(),
        'assigned_count': assigned_issues.count(),
        'status_filter': status_filter,
        'priority_filter': priority_filter,
    }
    
    return render(request, 'issues/my_issues.html', context)

# CSV Download view
import csv
import io
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from .models import Issue


def download_csv(request):
    """
    Enhanced CSV export with filtering, statistics, and better formatting
    """
    # Get filter parameters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Filter issues based on parameters
    issues = Issue.objects.all()
    
    if status_filter:
        issues = issues.filter(status=status_filter)
    if priority_filter:
        issues = issues.filter(priority=priority_filter)
    if date_from:
        issues = issues.filter(created_at__gte=date_from)
    if date_to:
        issues = issues.filter(created_at__lte=date_to)
    
    # Order by creation date (newest first)
    issues = issues.order_by('-created_at')
    
    # Generate filename with timestamp
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"issues_report_{timestamp}.csv"
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Add UTF-8 BOM for Excel compatibility
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # Write metadata header
    writer.writerow(['# Issues Export Report'])
    writer.writerow([f'# Generated on: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([f'# Total Records: {issues.count()}'])
    
    # Add filters info if any
    if status_filter or priority_filter or date_from or date_to:
        writer.writerow(['# Filters Applied:'])
        if status_filter:
            writer.writerow([f'# - Status: {status_filter}'])
        if priority_filter:
            writer.writerow([f'# - Priority: {priority_filter}'])
        if date_from:
            writer.writerow([f'# - Date From: {date_from}'])
        if date_to:
            writer.writerow([f'# - Date To: {date_to}'])
    
    writer.writerow([])  # Empty row for separation
    
    # Enhanced header row
    writer.writerow([
        'Issue ID',
        'Title',
        'Description',
        'Status',
        'Priority',
        'Category',
        'Assigned To',
        'Reporter',
        'Created Date',
        'Updated Date',
        'Due Date',
        'Resolution',
        'Tags',
        'Time Spent (Hours)',
        'Estimated Hours'
    ])
    
    # Write data rows with enhanced formatting
    for issue in issues:
        writer.writerow([
            issue.id,
            issue.title,
            (issue.description[:100] + '...') if len(str(issue.description or '')) > 100 else (issue.description or ''),
            issue.get_status_display() if hasattr(issue, 'get_status_display') else issue.status,
            issue.get_priority_display() if hasattr(issue, 'get_priority_display') else issue.priority,
            getattr(issue, 'category', 'N/A'),
            issue.assigned_to.get_full_name() if issue.assigned_to else 'Unassigned',
            getattr(issue.reporter, 'get_full_name', lambda: 'Unknown')() if hasattr(issue, 'reporter') and issue.reporter else 'System',
            issue.created_at.strftime('%Y-%m-%d %H:%M:%S') if issue.created_at else '',
            issue.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(issue, 'updated_at') and issue.updated_at else '',
            getattr(issue, 'due_date', ''),
            getattr(issue, 'resolution', ''),
            ', '.join([tag.name for tag in getattr(issue, 'tags', [])]) if hasattr(issue, 'tags') else '',
            getattr(issue, 'time_spent', 0),
            getattr(issue, 'estimated_hours', 0)
        ])
    
    # Add summary statistics at the end
    writer.writerow([])
    writer.writerow(['# SUMMARY STATISTICS'])
    
    # Calculate statistics
    total_issues = issues.count()
    status_counts = {}
    priority_counts = {}
    
    for issue in issues:
        status = issue.status
        priority = issue.priority
        
        status_counts[status] = status_counts.get(status, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    writer.writerow(['Total Issues:', total_issues])
    writer.writerow(['Status Breakdown:'])
    for status, count in status_counts.items():
        writer.writerow([f'- {status}:', count])
    
    writer.writerow(['Priority Breakdown:'])
    for priority, count in priority_counts.items():
        writer.writerow([f'- {priority}:', count])
    
    return response


def download_pdf(request):
    """
    Enhanced PDF export with professional formatting, charts, and statistics
    """
    # Get filter parameters (same as CSV)
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Filter issues
    issues = Issue.objects.all()
    
    if status_filter:
        issues = issues.filter(status=status_filter)
    if priority_filter:
        issues = issues.filter(priority=priority_filter)
    if date_from:
        issues = issues.filter(created_at__gte=date_from)
    if date_to:
        issues = issues.filter(created_at__lte=date_to)
    
    issues = issues.order_by('-created_at')
    
    # Generate filename with timestamp
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"issues_report_{timestamp}.pdf"
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create PDF document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2563eb')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=HexColor('#374151')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Build PDF content
    story = []
    
    # Title and header
    story.append(Paragraph("📊 Issues Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report metadata
    metadata_data = [
        ['Generated on:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['Total records:', str(issues.count())],
        ['Report type:', 'Complete Issues Export']
    ]
    
    # Add filter information if any
    if status_filter or priority_filter or date_from or date_to:
        metadata_data.append(['Filters applied:', ''])
        if status_filter:
            metadata_data.append(['- Status:', status_filter])
        if priority_filter:
            metadata_data.append(['- Priority:', priority_filter])
        if date_from:
            metadata_data.append(['- Date from:', date_from])
        if date_to:
            metadata_data.append(['- Date to:', date_to])
    
    metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
    ]))
    
    story.append(metadata_table)
    story.append(Spacer(1, 30))
    
    # Summary statistics
    story.append(Paragraph("📈 Summary Statistics", heading_style))
    
    # Calculate statistics
    total_issues = issues.count()
    status_counts = {}
    priority_counts = {}
    
    for issue in issues:
        status = issue.status
        priority = issue.priority
        
        status_counts[status] = status_counts.get(status, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # Create statistics tables
    stats_data = [['Metric', 'Count', 'Percentage']]
    
    # Add status breakdown
    for status, count in status_counts.items():
        percentage = (count / total_issues * 100) if total_issues > 0 else 0
        stats_data.append([f'Status: {status}', str(count), f'{percentage:.1f}%'])
    
    # Add priority breakdown
    for priority, count in priority_counts.items():
        percentage = (count / total_issues * 100) if total_issues > 0 else 0
        stats_data.append([f'Priority: {priority}', str(count), f'{percentage:.1f}%'])
    
    stats_table = Table(stats_data, colWidths=[3*inch, 1*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8fafc'), HexColor('#ffffff')])
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 30))
    
    # Issues list
    story.append(Paragraph("📋 Issues Details", heading_style))
    
    # Create issues table with pagination
    issues_per_page = 15
    issues_list = list(issues[:50])  # Limit to first 50 for PDF readability
    
    if issues_list:
        # Table headers
        table_data = [['ID', 'Title', 'Status', 'Priority', 'Assigned', 'Created']]
        
        for issue in issues_list:
            title = (issue.title[:30] + '...') if len(issue.title) > 30 else issue.title
            if issue.assigned_to:
                assigned = issue.assigned_to.get_full_name() or issue.assigned_to.username
                assigned = assigned[:15] + '...' if len(assigned) > 15 else assigned
            else:
                assigned = 'Unassigned'
            table_data.append([
                str(issue.id),
                title,
                issue.status,
                issue.priority,
                assigned,
                issue.created_at.strftime('%m/%d/%Y') if issue.created_at else 'N/A'
            ])
        
        issues_table = Table(table_data, colWidths=[0.7*inch, 2.5*inch, 1*inch, 1*inch, 1.3*inch, 1*inch])
        issues_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8fafc'), HexColor('#ffffff')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(issues_table)
        
        # Add note if there are more issues
        if issues.count() > 50:
            story.append(Spacer(1, 20))
            note_text = f"Note: Showing first 50 issues out of {issues.count()} total. Download CSV for complete data."
            story.append(Paragraph(note_text, normal_style))
    
    else:
        story.append(Paragraph("No issues found matching the specified criteria.", normal_style))
    
    # Add footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=HexColor('#6b7280')
    )
    story.append(Paragraph("Generated by Issues Management System", footer_style))
    
    # Build PDF
    doc.build(story)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


# Optional: Combined export view
def download_report(request, format_type):
    """
    Universal download view that handles both CSV and PDF
    """
    if format_type.lower() == 'csv':
        return download_csv(request)
    elif format_type.lower() == 'pdf':
        return download_pdf(request)
    else:
        return HttpResponse("Invalid format type", status=400)


