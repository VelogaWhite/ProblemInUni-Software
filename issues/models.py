from django.db import models
from django.contrib.auth.models import User

class Issue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    CATEGORY_CHOICES = [
        ('electrical',   '⚡ Electrical'),
        ('plumbing',     '🔧 Plumbing / Water'),
        ('internet',     '🌐 Internet / Network'),
        ('ac',           '❄️ Air Conditioning'),
        ('furniture',    '🪑 Furniture / Equipment'),
        ('security',     '🔒 Security'),
        ('cleanliness',  '🧹 Cleanliness'),
        ('other',        '📌 Other'),
    ]
    ZONE_CHOICES = [
        ('archif1', 'คณะสถาปัตยกรรม ชั้น 1'),
        ('archif2', 'คณะสถาปัตยกรรม ชั้น 2'),
        ('archif3', 'คณะสถาปัตยกรรม ชั้น 3'),
        ('archif4', 'คณะสถาปัตยกรรม ชั้น 4'),
        ('archif5', 'คณะสถาปัตยกรรม ชั้น 5'),
        ('archif6', 'คณะสถาปัตยกรรม ชั้น 6'),
        ('outdoor81', 'ลานหน้าตึก 81'),
    ]

    description = models.TextField()
    location = models.CharField(max_length=200)
    zone = models.CharField(max_length=20, choices=ZONE_CHOICES, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    image = models.ImageField(upload_to='issue_images/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_issues')
    
    # เวลา
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # เหตุผลปฏิเสธ
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.location} - {self.description[:30]}"

class IssueStatusLog(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(max_length=20, choices=Issue.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Log: {self.issue.location} changed to {self.status}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To {self.user.username}: {self.message}"

# --- เพิ่มตารางสำหรับเก็บพิกัด 3D Hotspot ---
class HotspotCoordinate(models.Model):
    zone = models.CharField(max_length=20, choices=Issue.ZONE_CHOICES, help_text="โซนหรือชั้นที่จุดนี้อยู่")
    keyword = models.CharField(max_length=100, help_text="คำสำคัญ เช่น 'ห้องน้ำชาย', 'ลิฟต์', 'บันไดหนีไฟ'")
    position = models.CharField(max_length=100, help_text="พิกัด position (x y z) ที่ได้จากเครื่องมือ")
    normal = models.CharField(max_length=100, help_text="พิกัด normal (x y z) ที่ได้จากเครื่องมือ", default="0.0000 1.0000 0.0000")

    def __str__(self):
        return f"[{self.get_zone_display()}] - {self.keyword}"