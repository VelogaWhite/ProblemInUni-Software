from django.shortcuts import render
from .models import Issue

def homepage(request):
    # ดึงข้อมูลปัญหาทั้งหมดมาแสดงที่หน้าแรก (ให้คนอื่นเห็นปัญหาที่ถูกรายงานไว้)
    issues = Issue.objects.all().order_by('-created_at')
    return render(request, 'issues/homepage.html', {'issues': issues})

def profile(request):
    # ตรวจสอบว่าผู้ใช้ล็อกอินหรือยัง
    if request.user.is_authenticated:
        # ถ้าล็อกอินแล้ว ดึงเฉพาะปัญหาที่ผู้ใช้คนนี้ (request.user) เป็นคนรายงาน
        user_issues = Issue.objects.filter(reporter=request.user).order_by('-created_at')
    else:
        # ถ้ายังไม่ล็อกอิน ส่งลิสต์ว่างๆ ไป (เดี๋ยวเราไปจัดการแสดงผลต่อใน HTML)
        user_issues = []
        
    return render(request, 'issues/profile.html', {'user_issues': user_issues})

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
            return redirect('profile') # ล็อกอินสำเร็จให้กลับไปหน้า Profile
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!')
            return redirect('profile')
            
    return redirect('profile')

# ระบบออกจากระบบ
def logout_view(request):
    logout(request)
    return redirect('homepage') # ออกจากระบบแล้วเด้งกลับหน้าแรก

# ระบบสมัครสมาชิก
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # สมัครเสร็จให้ล็อกอินอัตโนมัติเลย
            return redirect('profile')
    else:
        form = UserCreationForm()
        
    return render(request, 'issues/register.html', {'form': form})
