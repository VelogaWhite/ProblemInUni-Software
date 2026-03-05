from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Issue
from .forms import RegisterForm

class IssueModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='s640101234567', password='password123')
        self.issue = Issue.objects.create(
            reporter=self.user,
            description='แอร์ไม่เย็น',
            location='อาคาร 78 ชั้น 3',
            status='pending'
        )

    def test_issue_creation(self):
        """ทดสอบว่าสร้าง Issue ได้ถูกต้อง"""
        self.assertEqual(self.issue.description, 'แอร์ไม่เย็น')
        self.assertEqual(self.issue.location, 'อาคาร 78 ชั้น 3')
        self.assertEqual(self.issue.reporter, self.user)
        self.assertEqual(self.issue.status, 'pending')

    def test_issue_str_representation(self):
        """ทดสอบ __str__ ของ Model ว่าแสดงผลถูกต้องตามรูปแบบ Location - Description"""
        expected_str = 'อาคาร 78 ชั้น 3 - แอร์ไม่เย็น'
        self.assertEqual(str(self.issue), expected_str)


class RegisterFormTest(TestCase):
    def test_valid_form(self):
        """ทดสอบฟอร์มสมัครสมาชิกด้วยข้อมูลที่ถูกต้อง"""
        data = {
            'username': 's640101234567',
            'email': 's640101234567@email.kmutnb.ac.th',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = RegisterForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email_pattern(self):
        """ทดสอบอีเมลผิดรูปแบบ (ไม่ใช่เมลมหาลัย)"""
        data = {
            'username': 's640101234567',
            'email': 'somchai@gmail.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_username_email_mismatch(self):
        """ทดสอบ Username ไม่ตรงกับรหัสนักศึกษาในอีเมล"""
        data = {
            'username': 's640101234567',
            'email': 's640109999999@email.kmutnb.ac.th',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        # Error จาก clean() จะอยู่ใน __all__
        self.assertIn('__all__', form.errors)


class IssueViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='s640101234567', password='password123')
        self.issue = Issue.objects.create(
            reporter=self.user,
            description='ลิฟต์ค้าง',
            location='อาคาร 81',
            status='pending'
        )

    def test_homepage_view(self):
        """ทดสอบหน้า Homepage แสดงผลถูกต้องและมีรายการปัญหา"""
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'issues/homepage.html')
        self.assertContains(response, 'ลิฟต์ค้าง')

    def test_report_issue_logged_in(self):
        """ทดสอบการแจ้งปัญหาเมื่อล็อกอินแล้ว"""
        self.client.login(username='s640101234567', password='password123')
        response = self.client.post(reverse('report_issue'), {
            'description': 'น้ำรั่ว',
            'location': 'ห้องน้ำชาย ชั้น 2'
        })
        # แจ้งเสร็จต้อง Redirect ไปหน้า Profile
        self.assertRedirects(response, reverse('profile'))
        
        # ตรวจสอบว่ามีปัญหาเพิ่มขึ้นมาในฐานข้อมูล
        self.assertEqual(Issue.objects.count(), 2)
        new_issue = Issue.objects.latest('created_at')
        self.assertEqual(new_issue.description, 'น้ำรั่ว')

    def test_report_issue_not_logged_in(self):
        """ทดสอบการแจ้งปัญหาเมื่อยังไม่ล็อกอิน (ต้องเด้งไปหน้า Login)"""
        response = self.client.post(reverse('report_issue'), {
            'description': 'ไฟดับ',
            'location': 'โรงอาหาร'
        })
        # ต้อง Redirect ไปหน้า Login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
        
        # ปัญหาต้องไม่ถูกสร้างเพิ่ม
        self.assertEqual(Issue.objects.count(), 1)
