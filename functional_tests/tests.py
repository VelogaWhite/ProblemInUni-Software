from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
from django.contrib.auth.models import User

class IssueReportingAndManagementTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.user = User.objects.create_user(username='s640101234567', password='password123')
        # สร้าง Staff Account
        self.staff = User.objects.create_user(username='fahsai_staff', password='staffpassword', is_staff=True)

    def tearDown(self):
        self.browser.quit()

    def test_somchai_and_fahsai_user_story(self):
        # ==========================================
        # สมชาย (User)
        # ==========================================
        self.browser.get(self.live_server_url + '/profile/')
        self.browser.find_element(By.NAME, 'username').send_keys('s640101234567')
        self.browser.find_element(By.NAME, 'password').send_keys('password123')
        self.browser.find_element(By.XPATH, '//button[contains(text(), "เข้าสู่ระบบ")]').click()

        self.browser.get(self.live_server_url)
        report_button = self.browser.find_element(By.XPATH, '//button[contains(., "แจ้งปัญหา")]')
        report_button.click()
        time.sleep(1)

        desc_input = self.browser.find_element(By.ID, 'description')
        desc_input.send_keys('ฝาชักโครกหัก')
        loc_input = self.browser.find_element(By.ID, 'location')
        loc_input.send_keys('ตึก81 ชั้น3 ห้องน้ำชาย1')

        submit_button = self.browser.find_element(By.XPATH, '//button[text()="Submit"]')
        submit_button.click()
        time.sleep(1) 

        self.assertIn('/profile/', self.browser.current_url)
        profile_page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ฝาชักโครกหัก', profile_page_text)
        self.assertIn('Pending', profile_page_text) 

        self.browser.delete_all_cookies() # สมชายปิดหน้าจอ

        # ==========================================
        # ฟ้าใส (Staff)
        # ==========================================
        self.browser.get(self.live_server_url + '/profile/') # ฟ้าใสเข้าหน้า Login
        self.browser.find_element(By.NAME, 'username').send_keys('fahsai_staff')
        self.browser.find_element(By.NAME, 'password').send_keys('staffpassword')
        self.browser.find_element(By.XPATH, '//button[contains(text(), "เข้าสู่ระบบ")]').click()
        time.sleep(1)

        # เนื่องจากล็อกอินเป็น Staff ระบบจะ Redirect มาที่ /staff/ อัตโนมัติ (ตามที่เราเขียนโค้ดไว้ใน Login View)
        self.assertIn('/staff/', self.browser.current_url)

        staff_page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ฝาชักโครกหัก', staff_page_text)
        self.assertIn('s640101234567', staff_page_text)

        # ฟ้าใสเปลี่ยนสถานะปัญหาจาก pending เป็น in progress
        issue_row = self.browser.find_element(By.XPATH, '//tr[contains(., "ฝาชักโครกหัก")]')
        status_dropdown = Select(issue_row.find_element(By.NAME, 'status'))
        status_dropdown.select_by_value('in_progress')

        # กดปุ่มบันทึก
        save_button = issue_row.find_element(By.XPATH, './/button[text()="บันทึก"]')
        save_button.click()
        time.sleep(1)

        # รีเฟรชและตรวจสอบว่าสถานะเปลี่ยนเป็น In Progress สำเร็จ
        updated_page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('In Progress', updated_page_text)