from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from django.contrib.auth.models import User

class SomchaiReportsIssueTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()
        # 1. อัปเดต: จำลอง User เป็นรหัสนักศึกษาเพื่อให้ตรงกับเงื่อนไขใหม่ของระบบ
        self.user = User.objects.create_user(username='s640101234567', password='password123')

    def tearDown(self):
        self.browser.quit()

    def test_somchai_user_story(self):
        # ล็อกอินเข้าสู่ระบบก่อน
        self.browser.get(self.live_server_url + '/profile/')
        self.browser.find_element(By.NAME, 'username').send_keys('s640101234567')
        self.browser.find_element(By.NAME, 'password').send_keys('password123')
        self.browser.find_element(By.XPATH, '//button[contains(text(), "เข้าสู่ระบบ")]').click()

        # สมชายเข้าหน้าเว็บ Problem in Uni
        self.browser.get(self.live_server_url)

        # 1. ตรวจสอบว่าอยู่หน้า homepage และมีกล่องแสดงปัญหา
        self.assertIn('Problem in Uni', self.browser.title)
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ปัญหาในมหาลัยที่รายงานล่าสุด', page_text)

        # 2. ปุ่ม Filter ปัญหา (อัปเดต: โค้ดใหม่ใช้แท็ก <summary> ในการทำ Dropdown)
        filter_button = self.browser.find_element(By.XPATH, '//summary[contains(., "Filter")]')
        self.assertTrue(filter_button.is_displayed())

        # 3. ปุ่มขวาบน กดเพื่อไปดู Profile (อัปเดต: โค้ดใหม่แสดงชื่อ Username เป็นปุ่มกดแทนคำว่า Profile)
        profile_button = self.browser.find_element(By.LINK_TEXT, 's640101234567')
        self.assertTrue(profile_button.is_displayed())

        # 4. ปุ่มซ้ายบนที่จะกดแล้วกลับไปที่หน้า homepage
        home_button = self.browser.find_element(By.LINK_TEXT, 'ProbleminUni')
        self.assertTrue(home_button.is_displayed())

        # สมชายไม่เจอปัญหาของตัวเอง จึงกดปุ่มรายงานปัญหา 
        # (อัปเดต: ปุ่มย้ายมาอยู่ข้างช่องค้นหา และใช้คำว่า "แจ้งปัญหา")
        report_button = self.browser.find_element(By.XPATH, '//button[contains(., "แจ้งปัญหา")]')
        report_button.click()

        # รอให้ Modal เด้งขึ้นมา
        time.sleep(1) 

        # ตรวจสอบหัวข้อ Modal “รายงานปัญหา”
        modal_title = self.browser.find_element(By.XPATH, '//h2[text()="รายงานปัญหา"]')
        self.assertTrue(modal_title.is_displayed())

        # สมชายพิมพ์ปัญหา “ฝาชักโครกในหองน้ำชำรุด” ลงไปในกล่อง inputbox
        desc_input = self.browser.find_element(By.ID, 'description')
        desc_input.send_keys('ฝาชักโครกในหองน้ำชำรุด')

        # สมชายระบุสถานที่ “ตึก 81 ชั้น 4 ห้อง 412"
        loc_input = self.browser.find_element(By.ID, 'location')
        loc_input.send_keys('ตึก 81 ชั้น 4 ห้อง 412')

        # พอกรอกข้อมูลครบถ้วนสมชายจึงกด submit
        submit_button = self.browser.find_element(By.XPATH, '//button[text()="Submit"]')
        submit_button.click()

        # เมื่อสมชายกด submit สมชายเจอหน้าที่รวมปัญหาที่สมชายได้รายงานเอาไว้
        time.sleep(1) # รอระบบบันทึกและ Redirect ไปหน้า Profile
        self.assertIn('/profile/', self.browser.current_url)

        # และจะเห็น Status ว่าปัญหาของสมชายกำลังรอการถูกยืนยัน
        profile_page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ฝาชักโครกในหองน้ำชำรุด', profile_page_text)
        self.assertIn('ตึก 81 ชั้น 4 ห้อง 412', profile_page_text)
        self.assertIn('รอการถูกยืนยัน', profile_page_text)