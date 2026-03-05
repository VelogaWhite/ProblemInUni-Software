from django.db import models
from django.contrib.auth.models import User

class Issue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอการถูกยืนยัน'),
        ('confirmed', 'รับเรื่องแล้ว'),
        ('resolved', 'แก้ไขเสร็จสิ้น'),
    ]

    description = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='issue_images/', null=True, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # --- เพิ่ม 2 บรรทัดนี้ ---
    confirmed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    # -----------------------

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status)

    def __str__(self):
        return self.description
