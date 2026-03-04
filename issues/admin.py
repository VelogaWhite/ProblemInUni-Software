from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Issue

# ปรับแต่งหน้า Admin
admin.site.site_header = "ProblemInUni Admin"     # ข้อความในแถบ Header
admin.site.index_title = "การจัดการระบบ"          # ข้อความในหน้าแรกของ Admin
admin.site.site_url = "/login/"                   # ลิงก์ "View site" จะพากลับไปหน้า Login

# ซ่อนตาราง Groups (กลุ่มผู้ใช้งาน) เนื่องจากไม่ได้ใช้งานในโปรเจกต์นี้
admin.site.unregister(Group)

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    # แสดงคอลัมน์อะไรบ้างในหน้ารายการ
    list_display = ('description', 'location', 'reporter', 'status', 'created_at')
    # เพิ่มตัวกรองด้านขวา (กรองตามสถานะ และ วันที่)
    list_filter = ('status', 'created_at')
    # เพิ่มช่องค้นหา (ค้นหาจาก รายละเอียด, สถานที่, และชื่อผู้แจ้ง)
    search_fields = ('description', 'location', 'reporter__username')
    # ให้แก้ไขสถานะได้เลยจากหน้ารายการ
    list_editable = ('status',)