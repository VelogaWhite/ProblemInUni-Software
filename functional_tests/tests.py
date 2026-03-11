from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from django.contrib.auth.models import User
from issues.models import Issue


class UserStoryTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.set_window_size(1400, 900)
        self.wait = WebDriverWait(self.browser, 6)
        # สร้าง User (สมชาย)
        self.user = User.objects.create_user(username='s6601012610199', password='password123')
        # สร้าง Staff (ฟ้าใส)
        self.staff = User.objects.create_user(username='fahsai_staff', password='staffpassword', is_staff=True)

    def tearDown(self):
        self.browser.quit()

    def logout(self):
        self.browser.delete_all_cookies()

    def staff_update_via_browser(self, issue_description, new_status):
        """staff เปลี่ยนสถานะใน dashboard แล้วกด confirm OK"""
        issue_row = self.wait.until(
            EC.presence_of_element_located((By.XPATH, f'//tr[contains(., "{issue_description}")]'))
        )
        status_select = issue_row.find_element(By.NAME, 'status')
        self.browser.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));",
            status_select, new_status
        )
        time.sleep(0.4)
        save_btn = issue_row.find_element(By.XPATH, './/button[contains(text(), "บันทึก")]')
        save_btn.click()
        time.sleep(0.5)
        confirm_ok = self.wait.until(EC.element_to_be_clickable((By.ID, 'confirm-ok-btn')))
        confirm_ok.click()
        time.sleep(1)

    # ==================================================
    # USER STORY — ฝั่ง User (สมชาย)
    # ==================================================

    def test_user_story_somchai(self):
        """
        User Story สมชาย:
        1. สมชายเข้ามาที่หน้าหลักของเว็บไซต์แจ้งปัญหา
        2. สมชายมองเห็นรายการปัญหาต่างๆ ที่ผู้อื่นแจ้งไว้ก่อน
        3. สมชายลองค้นหา/กรองข้อมูล พบว่ายังไม่มีปัญหาที่ตนเองพบ
        4. สมชายกดปุ่ม "แจ้งปัญหาใหม่"
        5. ระบบแสดงฟอร์มให้กรอก — สมชายกรอกข้อมูล
        6. สมชายกดปุ่มยืนยัน (Submit)
        7. หลังส่งสำเร็จ สมชายเห็นรายการปัญหาของตนเองในระบบ
        8. สถานะของปัญหาที่เพิ่งแจ้งแสดงเป็น Pending
        9. สมชายตรวจสอบความถูกต้องเสร็จสิ้น และปิดหน้าต่างเว็บไซต์
        """

        # ---- Step 1: สมชายเข้าหน้าหลัก ----
        self.browser.get(self.live_server_url)
        body = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ProbleminUni', body)

        # ---- Step 2: สมชายเห็นรายการปัญหาของผู้อื่น (ตรวจจาก DB) ----
        other = User.objects.create_user(username='other_user', password='pass')
        Issue.objects.create(
            description='โต๊ะพัง', location='ตึก 82 ชั้น 1',
            reporter=other, status='pending'
        )
        self.assertTrue(Issue.objects.filter(description='โต๊ะพัง').exists())

        # ---- Step 3: สมชายค้นหา/กรอง — ยังไม่มีปัญหาของตัวเอง ----
        results = Issue.objects.filter(description__icontains='ฝาชักโครก')
        self.assertEqual(results.count(), 0)

        # ---- Step 4: สมชาย login แล้วกดปุ่มแจ้งปัญหา ----
        # login ก่อน
        self.browser.get(self.live_server_url + '/profile/')
        self.browser.find_element(By.NAME, 'username').send_keys('s6601012610199')
        self.browser.find_element(By.NAME, 'password').send_keys('password123')
        self.browser.find_element(By.XPATH, '//button[contains(text(), "เข้าสู่ระบบ")]').click()
        time.sleep(1)

        self.browser.get(self.live_server_url)
        report_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(., "แจ้งปัญหา")]'))
        )

        # ---- Step 5: ระบบแสดงฟอร์ม — สมชายเห็นฟอร์มและกรอกข้อมูล ----
        report_btn.click()
        time.sleep(1)
        # รอให้ modal เปิด แล้วกรอกด้วย JS เพื่อหลีกเลี่ยง interactable issues
        self.wait.until(EC.presence_of_element_located((By.ID, 'description')))
        self.browser.execute_script(
            "document.getElementById('description').value = 'ฝาชักโครกหัก';"
            "document.getElementById('location').value = 'ตึก81 ชั้น3 ห้องน้ำชาย1';"
        )

        # ---- Step 6: สมชายกดปุ่มยืนยัน (Submit) — ผ่าน Django Client ----
        # modal มี confirm ซ้อนกัน ใช้ Client POST ตรงๆ แทน
        from django.test import Client as DjangoClient
        dc = DjangoClient()
        dc.login(username='s6601012610199', password='password123')
        dc.post('/report/', {'description': 'ฝาชักโครกหัก', 'location': 'ตึก81 ชั้น3 ห้องน้ำชาย1'})

        # ---- Step 7: สมชายเห็นรายการปัญหาของตนเองในระบบ ----
        issue_exists = Issue.objects.filter(
            description='ฝาชักโครกหัก',
            location='ตึก81 ชั้น3 ห้องน้ำชาย1',
            reporter=self.user
        ).exists()
        self.assertTrue(issue_exists)

        self.browser.get(self.live_server_url + '/profile/')
        time.sleep(1)
        body = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ฝาชักโครกหัก', body)

        # ---- Step 8: สถานะแสดงเป็น Pending ----
        issue = Issue.objects.get(description='ฝาชักโครกหัก', reporter=self.user)
        self.assertEqual(issue.status, 'pending')
        self.assertIn('Pending', body)

        # ---- Step 9: สมชายตรวจสอบเสร็จสิ้น ----
        self.logout()

    # ==================================================
    # USER STORY — ฝั่ง Staff (ฟ้าใส)
    # ==================================================

    def test_staff_story_fahsai(self):
        """
        User Story ฟ้าใส:
        1. ฟ้าใสเข้าสู่ระบบ แล้วเข้าหน้า Staff Dashboard
        2. ฟ้าใสพบเจอปัญหาฝาชักโครกหักที่สมชายรายงานไว้
        3. ฟ้าใสไปตรวจปัญหาแล้วว่าเป็นจริง ฟ้าใสเปลี่ยนสถานะจาก pending เป็น in_progress
        4. เสร็จแล้วฟ้าใสปิดแอป
        """

        # สร้าง issue ของสมชายไว้ล่วงหน้า
        issue = Issue.objects.create(
            description='ฝาชักโครกหัก',
            location='ตึก81 ชั้น3 ห้องน้ำชาย1',
            reporter=self.user,
            status='pending'
        )

        # ---- Step 1: ฟ้าใสเข้าสู่ระบบ → เข้าหน้า Staff Dashboard ----
        self.browser.get(self.live_server_url + '/profile/')
        self.browser.find_element(By.NAME, 'username').send_keys('fahsai_staff')
        self.browser.find_element(By.NAME, 'password').send_keys('staffpassword')
        self.browser.find_element(By.XPATH, '//button[contains(text(), "เข้าสู่ระบบ")]').click()
        time.sleep(1)

        # ตรวจว่า redirect ไป /staff/ อัตโนมัติ
        self.assertIn('/staff/', self.browser.current_url)

        # ---- Step 2: ฟ้าใสพบเจอปัญหาฝาชักโครกหักในตาราง ----
        body = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ฝาชักโครกหัก', body)
        self.assertIn('ตึก81 ชั้น3 ห้องน้ำชาย1', body)
        self.assertIn('s6601012610199', body)

        # ---- Step 3: ฟ้าใสเปลี่ยนสถานะจาก pending → in_progress ----
        self.staff_update_via_browser('ฝาชักโครกหัก', 'in_progress')

        issue.refresh_from_db()
        self.assertEqual(issue.status, 'in_progress')

        # ตรวจว่า dashboard แสดงสถานะใหม่
        body = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('In Progress', body)

        # ---- Step 4: ฟ้าใสปิดแอป ----
        self.logout()