from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Issue
from django.utils import timezone

# ปรับแต่งหน้า Admin
admin.site.site_header = "ProblemInUni Admin"     # ข้อความในแถบ Header
admin.site.index_title = "การจัดการระบบ"          # ข้อความในหน้าแรกของ Admin
admin.site.site_url = "/"                         # ลิงก์ "View site" จะพากลับไปหน้า Dashboard

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

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'confirmed' and not obj.confirmed_at:
                obj.confirmed_at = timezone.now()
            elif obj.status == 'resolved' and not obj.resolved_at:
                obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if obj.status == 'confirmed' and not obj.confirmed_at:
                obj.confirmed_at = timezone.now()
            elif obj.status == 'resolved' and not obj.resolved_at:
                obj.resolved_at = timezone.now()
            obj.save()
        formset.save_m2m()