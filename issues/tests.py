from django.test import TestCase, Client
from django.contrib.auth.models import User
from issues.models import Issue, IssueStatusLog, Notification


class IssueModelTest(TestCase):
    """ทดสอบ Issue Model"""

    def setUp(self):
        self.user = User.objects.create_user(username='s6601012610199', password='password123')

    def test_issue_default_status_is_pending(self):
        """Issue ที่สร้างใหม่ต้องมีสถานะ pending เป็น default"""
        issue = Issue.objects.create(
            description='ไฟไม่ติด', location='ตึก 89 ชั้น 2', reporter=self.user
        )
        self.assertEqual(issue.status, 'pending')

    def test_issue_str_representation(self):
        """__str__ ต้องคืน location - description"""
        issue = Issue.objects.create(
            description='ไฟไม่ติด', location='ตึก 89 ชั้น 2', reporter=self.user
        )
        self.assertIn('ตึก 89 ชั้น 2', str(issue))

    def test_issue_can_store_rejection_reason(self):
        """Issue ที่ถูก reject ต้องเก็บ rejection_reason ได้"""
        issue = Issue.objects.create(
            description='ปัญหาไม่ชัดเจน', location='ตึก 1',
            reporter=self.user, status='rejected',
            rejection_reason='ไม่พบปัญหาที่แจ้งมา'
        )
        self.assertEqual(issue.rejection_reason, 'ไม่พบปัญหาที่แจ้งมา')


class IssueStatusLogTest(TestCase):
    """ทดสอบ IssueStatusLog Model"""

    def setUp(self):
        self.user = User.objects.create_user(username='s6601012610199', password='password123')
        self.staff = User.objects.create_user(username='fahsai_staff', password='staffpassword', is_staff=True)
        self.issue = Issue.objects.create(
            description='ไฟไม่ติด', location='ตึก 89', reporter=self.user
        )

    def test_log_created_on_report(self):
        """เมื่อ report_issue ต้องสร้าง log สถานะ pending"""
        IssueStatusLog.objects.create(issue=self.issue, status='pending', changed_by=self.user)
        self.assertEqual(IssueStatusLog.objects.filter(issue=self.issue).count(), 1)
        log = IssueStatusLog.objects.get(issue=self.issue)
        self.assertEqual(log.status, 'pending')

    def test_log_created_on_status_update(self):
        """เมื่อ staff เปลี่ยนสถานะต้องสร้าง log ใหม่"""
        IssueStatusLog.objects.create(issue=self.issue, status='pending', changed_by=self.user)
        IssueStatusLog.objects.create(issue=self.issue, status='in_progress', changed_by=self.staff)
        logs = IssueStatusLog.objects.filter(issue=self.issue)
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs.last().status, 'in_progress')
        self.assertEqual(logs.last().changed_by, self.staff)

    def test_logs_ordered_by_changed_at(self):
        """logs ต้องเรียงตาม changed_at จากเก่าไปใหม่"""
        IssueStatusLog.objects.create(issue=self.issue, status='pending', changed_by=self.user)
        IssueStatusLog.objects.create(issue=self.issue, status='in_progress', changed_by=self.staff)
        IssueStatusLog.objects.create(issue=self.issue, status='resolved', changed_by=self.staff)
        logs = list(IssueStatusLog.objects.filter(issue=self.issue))
        self.assertEqual(logs[0].status, 'pending')
        self.assertEqual(logs[1].status, 'in_progress')
        self.assertEqual(logs[2].status, 'resolved')


class NotificationTest(TestCase):
    """ทดสอบ Notification Model"""

    def setUp(self):
        self.user = User.objects.create_user(username='s6601012610199', password='password123')
        self.staff = User.objects.create_user(username='fahsai_staff', password='staffpassword', is_staff=True)
        self.issue = Issue.objects.create(
            description='ก้อกน้ำรั่ว', location='ตึก 82', reporter=self.user
        )

    def test_notification_created_on_status_update(self):
        """เมื่อ staff เปลี่ยนสถานะต้องสร้าง notification ให้ผู้แจ้ง"""
        Notification.objects.create(
            user=self.user, issue=self.issue,
            message='ปัญหา "ก้อกน้ำรั่ว" ถูกอัปเดตเป็น: กำลังดำเนินการแล้ว'
        )
        notif = Notification.objects.get(user=self.user)
        self.assertFalse(notif.is_read)
        self.assertIn('ก้อกน้ำรั่ว', notif.message)

    def test_notification_marked_read(self):
        """notification ต้องถูก mark as read ได้"""
        Notification.objects.create(user=self.user, issue=self.issue, message='test')
        Notification.objects.filter(user=self.user).update(is_read=True)
        self.assertTrue(Notification.objects.get(user=self.user).is_read)

    def test_unread_count(self):
        """นับ unread notification ได้ถูกต้อง"""
        Notification.objects.create(user=self.user, issue=self.issue, message='แจ้งเตือน 1')
        Notification.objects.create(user=self.user, issue=self.issue, message='แจ้งเตือน 2')
        count = Notification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(count, 2)


class HomepageViewTest(TestCase):
    """ทดสอบ homepage view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='s6601012610199', password='password123')

    def test_homepage_returns_200(self):
        """homepage ต้องคืน status 200"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_homepage_shows_all_issues(self):
        """homepage ต้องส่ง issues ทั้งหมดใน context"""
        Issue.objects.create(description='ไฟไม่ติด', location='ตึก 89', reporter=self.user, status='pending')
        Issue.objects.create(description='แก้วแตก', location='ตึก 78', reporter=self.user, status='resolved')
        response = self.client.get('/')
        self.assertEqual(response.context['issues'].count(), 2)

    def test_homepage_filter_by_status(self):
        """homepage กรองด้วย ?status= ได้ถูกต้อง"""
        Issue.objects.create(description='ไฟไม่ติด', location='ตึก 89', reporter=self.user, status='pending')
        Issue.objects.create(description='แก้วแตก', location='ตึก 78', reporter=self.user, status='resolved')
        response = self.client.get('/?status=resolved')
        issues = list(response.context['issues'])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].description, 'แก้วแตก')

    def test_homepage_search_by_keyword(self):
        """homepage ค้นหาด้วย ?search= ได้ถูกต้อง"""
        Issue.objects.create(description='ฝาชักโครกหัก', location='ตึก 81', reporter=self.user, status='pending')
        Issue.objects.create(description='แก้วแตก', location='ตึก 78', reporter=self.user, status='resolved')
        response = self.client.get('/?search=ฝาชักโครก')
        issues = list(response.context['issues'])
        descs = [i.description for i in issues]
        self.assertIn('ฝาชักโครกหัก', descs)
        self.assertNotIn('แก้วแตก', descs)


class ReportIssueViewTest(TestCase):
    """ทดสอบ report_issue view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='s6601012610199', password='password123')

    def test_report_requires_login(self):
        """ยังไม่ login → POST /report/ ต้อง redirect ไป login"""
        response = self.client.post('/report/', {'description': 'ทดสอบ', 'location': 'ตึก A'})
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(Issue.objects.filter(description='ทดสอบ').exists())

    def test_report_creates_issue(self):
        """login แล้ว POST → ต้องสร้าง Issue ใน DB"""
        self.client.login(username='s6601012610199', password='password123')
        self.client.post('/report/', {'description': 'ก๊อกน้ำรั่ว', 'location': 'ตึก 82 ชั้น 2'})
        self.assertTrue(Issue.objects.filter(description='ก๊อกน้ำรั่ว').exists())

    def test_report_sets_pending_status(self):
        """Issue ที่สร้างจาก report ต้องมีสถานะ pending"""
        self.client.login(username='s6601012610199', password='password123')
        self.client.post('/report/', {'description': 'ก๊อกน้ำรั่ว', 'location': 'ตึก 82'})
        issue = Issue.objects.get(description='ก๊อกน้ำรั่ว')
        self.assertEqual(issue.status, 'pending')

    def test_report_sets_reporter(self):
        """Issue ที่สร้างต้องบันทึก reporter เป็น user ที่ login"""
        self.client.login(username='s6601012610199', password='password123')
        self.client.post('/report/', {'description': 'ก๊อกน้ำรั่ว', 'location': 'ตึก 82'})
        issue = Issue.objects.get(description='ก๊อกน้ำรั่ว')
        self.assertEqual(issue.reporter, self.user)

    def test_report_creates_status_log(self):
        """report_issue ต้องสร้าง IssueStatusLog ด้วย"""
        self.client.login(username='s6601012610199', password='password123')
        self.client.post('/report/', {'description': 'ก๊อกน้ำรั่ว', 'location': 'ตึก 82'})
        issue = Issue.objects.get(description='ก๊อกน้ำรั่ว')
        self.assertTrue(IssueStatusLog.objects.filter(issue=issue, status='pending').exists())


class ProfileViewTest(TestCase):
    """ทดสอบ profile view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='s6601012610199', password='password123')

    def test_profile_authenticated_returns_200(self):
        """user ที่ login เข้า profile ได้"""
        self.client.login(username='s6601012610199', password='password123')
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)

    def test_profile_shows_only_own_issues(self):
        """profile แสดงเฉพาะ issue ของตัวเอง"""
        other = User.objects.create_user(username='other', password='pass')
        Issue.objects.create(description='ปัญหาของฉัน', location='A', reporter=self.user, status='pending')
        Issue.objects.create(description='ปัญหาของคนอื่น', location='B', reporter=other, status='pending')
        self.client.login(username='s6601012610199', password='password123')
        response = self.client.get('/profile/')
        descs = [i.description for i in response.context['user_issues']]
        self.assertIn('ปัญหาของฉัน', descs)
        self.assertNotIn('ปัญหาของคนอื่น', descs)

    def test_profile_marks_notifications_as_read(self):
        """เข้า profile แล้ว notifications ต้องถูก mark as read"""
        issue = Issue.objects.create(description='ทดสอบ', location='A', reporter=self.user, status='pending')
        Notification.objects.create(user=self.user, issue=issue, message='test', is_read=False)
        self.client.login(username='s6601012610199', password='password123')
        self.client.get('/profile/')
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)


class LoginViewTest(TestCase):
    """ทดสอบ login view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='s6601012610199', password='password123')
        self.staff = User.objects.create_user(username='fahsai_staff', password='staffpassword', is_staff=True)

    def test_login_correct_redirects_homepage(self):
        """login ถูกต้อง → redirect homepage"""
        response = self.client.post('/login/', {'username': 's6601012610199', 'password': 'password123'})
        self.assertRedirects(response, '/')

    def test_login_staff_redirects_dashboard(self):
        """staff login → redirect /staff/"""
        response = self.client.post('/login/', {'username': 'fahsai_staff', 'password': 'staffpassword'})
        self.assertRedirects(response, '/staff/')

    def test_login_wrong_password_shows_error(self):
        """password ผิด → messages มี error"""
        from django.contrib.messages import get_messages
        self.client.post('/login/', {'username': 's6601012610199', 'password': 'wrong'})
        response = self.client.get('/profile/')
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('ไม่ถูกต้อง' in m for m in msgs))


class StaffDashboardViewTest(TestCase):
    """ทดสอบ staff dashboard view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='s6601012610199', password='password123')
        self.staff = User.objects.create_user(username='fahsai_staff', password='staffpassword', is_staff=True)

    def test_normal_user_cannot_access(self):
        """user ธรรมดาเข้า /staff/ ไม่ได้"""
        self.client.login(username='s6601012610199', password='password123')
        response = self.client.get('/staff/')
        self.assertNotEqual(response.status_code, 200)

    def test_staff_can_access(self):
        """staff เข้า /staff/ ได้"""
        self.client.login(username='fahsai_staff', password='staffpassword')
        response = self.client.get('/staff/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_all_issues(self):
        """dashboard แสดงทุก issue ใน context"""
        Issue.objects.create(description='หน้าต่างแตก', location='ตึก 81', reporter=self.user, status='pending')
        Issue.objects.create(description='ลิฟต์เสีย', location='ตึก 89', reporter=self.user, status='in_progress')
        self.client.login(username='fahsai_staff', password='staffpassword')
        response = self.client.get('/staff/')
        self.assertEqual(response.context['issues'].count(), 2)

    def test_dashboard_count_context(self):
        """dashboard ต้องส่ง count แต่ละสถานะใน context"""
        Issue.objects.create(description='A', location='X', reporter=self.user, status='pending')
        Issue.objects.create(description='B', location='X', reporter=self.user, status='resolved')
        self.client.login(username='fahsai_staff', password='staffpassword')
        response = self.client.get('/staff/')
        self.assertEqual(response.context['count_pending'], 1)
        self.assertEqual(response.context['count_resolved'], 1)


class UpdateIssueStatusViewTest(TestCase):
    """ทดสอบ update_issue_status view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='s6601012610199', password='password123')
        self.staff = User.objects.create_user(username='fahsai_staff', password='staffpassword', is_staff=True)
        self.issue = Issue.objects.create(
            description='ก้อกน้ำรั่ว', location='ตึก 82', reporter=self.user, status='pending'
        )

    def test_staff_can_update_status(self):
        """staff เปลี่ยนสถานะได้"""
        self.client.login(username='fahsai_staff', password='staffpassword')
        self.client.post(f'/staff/update/{self.issue.id}/', {'status': 'in_progress'})
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, 'in_progress')

    def test_normal_user_cannot_update(self):
        """user ธรรมดาเปลี่ยนสถานะไม่ได้"""
        self.client.login(username='s6601012610199', password='password123')
        self.client.post(f'/staff/update/{self.issue.id}/', {'status': 'resolved'})
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, 'pending')

    def test_update_creates_status_log(self):
        """เปลี่ยนสถานะต้องสร้าง IssueStatusLog"""
        self.client.login(username='fahsai_staff', password='staffpassword')
        self.client.post(f'/staff/update/{self.issue.id}/', {'status': 'in_progress'})
        self.assertTrue(IssueStatusLog.objects.filter(issue=self.issue, status='in_progress').exists())

    def test_update_creates_notification(self):
        """เปลี่ยนสถานะต้องสร้าง Notification ให้ผู้แจ้ง"""
        self.client.login(username='fahsai_staff', password='staffpassword')
        self.client.post(f'/staff/update/{self.issue.id}/', {'status': 'resolved'})
        self.assertTrue(Notification.objects.filter(user=self.user, issue=self.issue).exists())

    def test_reject_saves_rejection_reason(self):
        """reject พร้อมเหตุผล → ต้องเซฟ rejection_reason"""
        self.client.login(username='fahsai_staff', password='staffpassword')
        self.client.post(f'/staff/update/{self.issue.id}/', {
            'status': 'rejected',
            'rejection_reason': 'ไม่พบปัญหาที่แจ้งมา'
        })
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, 'rejected')
        self.assertEqual(self.issue.rejection_reason, 'ไม่พบปัญหาที่แจ้งมา')

    def test_change_from_rejected_clears_reason(self):
        """เปลี่ยนจาก rejected ไปสถานะอื่น → rejection_reason ต้องถูกล้าง"""
        self.issue.status = 'rejected'
        self.issue.rejection_reason = 'เหตุผลเดิม'
        self.issue.save()
        self.client.login(username='fahsai_staff', password='staffpassword')
        self.client.post(f'/staff/update/{self.issue.id}/', {'status': 'in_progress'})
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.rejection_reason, '')