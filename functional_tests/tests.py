from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth.models import User
import time

class SomchaiReportsIssueTest(StaticLiveServerTestCase):

    def setUp(self):
        # เปิดเบราว์เซอร์ (เราใช้ Chrome เป็นค่าเริ่มต้น)
        self.browser = webdriver.Chrome()
        # สร้าง User "สมชาย" รอไว้ในฐานข้อมูลเพื่อให้เขาสามารถเข้าสู่ระบบได้
        self.user = User.objects.create_user(username='somchai', password='password123')

    def tearDown(self):
        # และสมชายก็ได้ปิดแอปลง
        self.browser.quit()

    def test_somchai_user_story(self):
        # เนื่องจากระบบเราบังคับให้ต้องมี User ถึงจะดู Profile และรายงานปัญหาแล้วผูกชื่อได้
        # เราจึงจำลองให้สมชาย Login ก่อนเริ่มกระบวนการ
        self.browser.get(self.live_server_url + '/profile/')
        self.browser.find_element(By.NAME, 'username').send_keys('somchai')
        self.browser.find_element(By.NAME, 'password').send_keys('password123')
        self.browser.find_element(By.XPATH, '//button[contains(text(), "เข้าสู่ระบบ")]').click()

        # สมชายเข้าหน้าเว็บ ProbleminUni จากนั้น
        self.browser.get(self.live_server_url)

        # สมชายจะเห็นหน้า homepage ที่มี...
        # 1. กล่องข้อความที่แสดงปัญหาที่ผู้อื่นได้รายงานไว้
        self.assertIn('ProbleminUni', self.browser.title)
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ปัญหาในมหาลัยที่รายงานล่าสุด', page_text)

        # 2. ปุ่ม Filter ปัญหา
        filter_button = self.browser.find_element(By.XPATH, '//button[contains(text(), "Filter")]')
        self.assertTrue(filter_button.is_displayed())

        # 3. ปุ่มขวาบน กดเพื่อไปดู Profile 
        profile_button = self.browser.find_element(By.LINK_TEXT, 'โปรไฟล์ (Profile)')
        self.assertTrue(profile_button.is_displayed())

        # 4. ปุ่มซ้ายบนที่จะกดแล้วกลับไปที่หน้า homepage
        home_button = self.browser.find_element(By.LINK_TEXT, 'ProbleminUni')
        self.assertTrue(home_button.is_displayed())

        # สมชายได้มองไปที่กล่องข้อความที่แสดงปัญหาที่ผู้อื่นได้รายงานไว้
        # แต่สมชายไม่เจอปัญหาที่สมชายพบเจอในมหาลัย
        # สมชายจึงกดปุ่มรายงานปัญหา (ที่อยู่ขวาล่าง)
        report_button = self.browser.find_element(By.XPATH, '//button[contains(@class, "fixed bottom-8")]')
        report_button.click()

        # รอให้ Modal เด้งขึ้นมา
        time.sleep(1) 

        # แล้วก็เห็นกล่องขึ้นมาตรงกลางโดยทีหัวข้อคือ “รายงานปัญหา”
        modal_title = self.browser.find_element(By.XPATH, '//h2[text()="รายงานปัญหา"]')
        self.assertTrue(modal_title.is_displayed())

        # สมชายเห็น inputbox ให้กรอกปัญหาที่เจอ
        # สมชายจึงพิมพ์ปัญหา “ฝาชักโครกในหองน้ำชำรุด” ลงไปในกล่อง inputbox
        desc_input = self.browser.find_element(By.ID, 'description')
        desc_input.send_keys('ฝาชักโครกในหองน้ำชำรุด')

        # จากนั้นสมชายก็เห็น inputbox ให้กรอกสถานที่ที่เจอปัญหา
        # สมชายก็ระบุสถานที่ “ตึก 81 ชั้น 4 ห้อง 412"
        loc_input = self.browser.find_element(By.ID, 'location')
        loc_input.send_keys('ตึก 81 ชั้น 4 ห้อง 412')

        # พอกรอกข้อมูลครบถ้วนสมชายจึงกด submit
        submit_button = self.browser.find_element(By.XPATH, '//button[text()="Submit"]')
        submit_button.click()

        # เมื่อสมชายกด submit สมชายเจอหน้าที่รวมปัญหาที่สมชายได้รายงานเอาไว้ (หน้า Profile)
        time.sleep(1) # รอระบบโหลดไปหน้า Profile
        self.assertIn('/profile/', self.browser.current_url)

        # และจะเห็น Status ว่าปัญหาของสมชายกำลังรอการถูกยืนยัน
        profile_page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('ฝาชักโครกในหองน้ำชำรุด', profile_page_text)
        self.assertIn('ตึก 81 ชั้น 4 ห้อง 412', profile_page_text)
        self.assertIn('รอการถูกยืนยัน', profile_page_text)