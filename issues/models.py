from django.db import models
from django.contrib.auth.models import User

class Issue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending (รอการตรวจสอบ)'),
        ('in_progress', 'In Progress (กำลังดำเนินการ)'),
        ('resolved', 'Resolved (แก้ไขแล้ว)'),
        ('rejected', 'Rejected (ปฏิเสธ/ยกเลิก)'),
    ]

    # ผู้ที่รายงานปัญหา (สมชาย)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE) 
    
    # รายละเอียดปัญหา 
    description = models.TextField() 
    
    # สถานที่ 
    location = models.CharField(max_length=255) 
    
    # รูปภาพประกอบ (ถ้ามี)
    image = models.ImageField(upload_to='issue_images/', blank=True, null=True)

    # สถานะของปัญหา 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending') 
    
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location} - {self.description[:20]}"