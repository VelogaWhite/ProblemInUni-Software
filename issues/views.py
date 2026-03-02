from django.shortcuts import render
from .models import Issue

def homepage(request):
    # ดึงข้อมูลปัญหาทั้งหมดมาแสดงที่หน้าแรก (ให้คนอื่นเห็นปัญหาที่ถูกรายงานไว้)
    issues = Issue.objects.all().order_by('-created_at')
    return render(request, 'issues/homepage.html', {'issues': issues})