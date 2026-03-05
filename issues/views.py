from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Issue
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
    return render(request, 'issues/homepage.html', {'issues': issues, 'status_choices': Issue.STATUS_CHOICES})

def profile(request):
    # ตรวจสอบว่าผู้ใช้ล็อกอินหรือยัง
    if request.user.is_authenticated:
        # ถ้าล็อกอินแล้ว ดึงเฉพาะปัญหาที่ผู้ใช้คนนี้ (request.user) เป็นคนรายงาน
        user_issues = Issue.objects.filter(reporter=request.user).order_by('-created_at')
    else:
        # ถ้ายังไม่ล็อกอิน ส่งลิสต์ว่างๆ ไป (เดี๋ยวเราไปจัดการแสดงผลต่อใน HTML)
        user_issues = []
        
    return render(request, 'issues/profile.html', {'user_issues': user_issues})

def issue_detail(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    return render(request, 'issues/issue_detail.html', {'issue': issue})

@login_required(login_url='login')
def report_issue(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        location = request.POST.get('location')
        image = request.FILES.get('image')
        
        if description and location:
            Issue.objects.create(
                description=description,
                location=location,
                image=image,
                reporter=request.user,
                status='pending'
            )
            return redirect('profile')
    return redirect('homepage')

# ระบบเข้าสู่ระบบ
def login_view(request):
    if request.method == 'POST':
        # รับค่าจากฟอร์มในหน้า Profile
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        
        # ตรวจสอบความถูกต้อง
        user = authenticate(request, username=user_name, password=pass_word)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('/admin/')
            return redirect('homepage') # ล็อกอินสำเร็จให้กลับไปหน้า Dashboard
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!')
            return redirect('profile')
            
    return redirect('profile')

# ระบบออกจากระบบ
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login') # ออกจากระบบแล้วเด้งไปหน้าเข้าสู่ระบบ
    return render(request, 'issues/logout_confirm.html')

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
