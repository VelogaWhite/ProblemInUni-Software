from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Issue, IssueStatusLog, Notification
from .forms import RegisterForm

def homepage(request):
    # ดึง query parameters สำหรับการกรองข้อมูล
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    # เริ่มต้นด้วย queryset ทั้งหมด
    issues_query = Issue.objects.all()

    # กรองตามสถานะ (ถ้ามีการเลือก)
    if status_filter and status_filter != 'all':
        issues_query = issues_query.filter(status=status_filter)

    # ค้นหาจากหัวข้อปัญหา (description) หรือ สถานที่ (location)
    if search_query:
        issues_query = issues_query.filter(
            Q(description__icontains=search_query) | 
            Q(location__icontains=search_query)
        )

    issues = issues_query.order_by('-created_at')
    notif_count = request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0
    return render(request, 'issues/homepage.html', {
        'issues': issues,
        'status_choices': Issue.STATUS_CHOICES,
        'notif_count': notif_count,
    })

def profile(request):
    # ตรวจสอบว่าผู้ใช้ล็อกอินหรือยัง
    if request.user.is_authenticated:
        # ถ้าล็อกอินแล้ว ดึงเฉพาะปัญหาที่ผู้ใช้คนนี้ (request.user) เป็นคนรายงาน
        user_issues = Issue.objects.filter(reporter=request.user).order_by('-created_at')
    else:
        # ถ้ายังไม่ล็อกอิน ส่งลิสต์ว่างๆ ไป (เดี๋ยวเราไปจัดการแสดงผลต่อใน HTML)
        user_issues = []
        
    notif_count = request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0
    notifications = request.user.notifications.all()[:10] if request.user.is_authenticated else []
    # mark all as read when user visits profile
    if request.user.is_authenticated:
        request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'issues/profile.html', {
        'user_issues': user_issues,
        'notif_count': notif_count,
        'notifications': notifications,
    })

def issue_detail(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    logs  = issue.status_logs.all()
    notif_count = request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0
    return render(request, 'issues/issue_detail.html', {'issue': issue, 'logs': logs, 'notif_count': notif_count})

@login_required(login_url='login')
def report_issue(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        location = request.POST.get('location')
        image = request.FILES.get('image')
        
        if description and location:
            issue = Issue.objects.create(
                description=description,
                location=location,
                image=image,
                reporter=request.user,
                status='pending'
            )
            IssueStatusLog.objects.create(
                issue=issue,
                status='pending',
                changed_by=request.user,
                note='รายงานปัญหาเข้าระบบ'
            )
            return redirect('profile')
    return redirect('homepage')

# ระบบเข้าสู่ระบบ
def login_view(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        
        user = authenticate(request, username=user_name, password=pass_word)
        if user is not None:
            login(request, user)
            # ถ้าเป็น Staff ให้วิ่งไปหน้า Staff Dashboard
            if user.is_staff or user.is_superuser:
                return redirect('staff_dashboard')
            return redirect('homepage') 
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!')
            return redirect('profile')
            
    return redirect('profile')

# ระบบออกจากระบบ
def logout_view(request):
    logout(request)
    return redirect('login') # ออกจากระบบแล้วเด้งไปหน้าเข้าสู่ระบบ

# ระบบสมัครสมาชิก
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # สมัครเสร็จให้ล็อกอินอัตโนมัติเลย
            return redirect('profile')
    else:
        form = RegisterForm()
        
    return render(request, 'issues/register.html', {'form': form})

# ==========================================
# ส่วนของ Staff
# ==========================================
@login_required(login_url='login')
def staff_dashboard(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('homepage')

    all_issues = Issue.objects.all()
    status_filter = request.GET.get('status_filter', '')
    if status_filter:
        issues = all_issues.filter(status=status_filter).order_by('-created_at')
    else:
        issues = all_issues.order_by('-created_at')

    return render(request, 'issues/staff_dashboard.html', {
        'issues': issues,
        'status_choices': Issue.STATUS_CHOICES,
        'count_total':       all_issues.count(),
        'count_pending':     all_issues.filter(status='pending').count(),
        'count_in_progress': all_issues.filter(status='in_progress').count(),
        'count_resolved':    all_issues.filter(status='resolved').count(),
        'count_rejected':    all_issues.filter(status='rejected').count(),
    })

@login_required(login_url='login')
def update_issue_status(request, issue_id):
    if request.method == 'POST' and (request.user.is_staff or request.user.is_superuser):
        issue = get_object_or_404(Issue, pk=issue_id)
        new_status = request.POST.get('status')
        # รับค่าเหตุผลจากฟอร์ม
        rejection_reason = request.POST.get('rejection_reason', '') 
        
        if new_status in dict(Issue.STATUS_CHOICES).keys():
            issue.status = new_status
            
            # ถ้าสถานะเป็น rejected ให้เซฟเหตุผลลงไปด้วย
            if new_status == 'rejected':
                issue.rejection_reason = rejection_reason
            else:
                issue.rejection_reason = '' # ล้างค่าทิ้งถ้าเปลี่ยนเป็นสถานะอื่น
                
            issue.save()

            # บันทึก log การเปลี่ยนสถานะ
            IssueStatusLog.objects.create(
                issue=issue,
                status=new_status,
                changed_by=request.user,
                note=rejection_reason if new_status == 'rejected' else ''
            )

            # สร้าง notification ให้ผู้แจ้งปัญหา
            status_labels = {
                'pending':     'รอการตรวจสอบ',
                'in_progress': 'กำลังดำเนินการแล้ว',
                'resolved':    'แก้ไขเสร็จแล้ว ✓',
                'rejected':    'ถูกปฏิเสธ',
            }
            label = status_labels.get(new_status, new_status)
            Notification.objects.create(
                user=issue.reporter,
                issue=issue,
                message=f'ปัญหา "{issue.description[:30]}" ถูกอัปเดตเป็น: {label}'
            )
            
    return redirect('staff_dashboard')