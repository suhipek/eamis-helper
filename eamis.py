
import requests
import hashlib
import base64
import time
import json
import re
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto import Random
from bs4 import BeautifulSoup

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh,en-US;q=0.7,en;q=0.3',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

sso_public_key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCfy7Co/zbDUegHFoAxuEzAyllnf6dxt50iipCVVns8Vzx6BCJmYEYa6/OlLrhJSB7yW4igfyotKkwsd8lA1d3nP6HWb7s4t2HWTKo/Tcb/LVzUGX9Juz8ifF1tHduAAubJNVlArr21uu1atk9y4K6Um3MKwWw5tQ/bMP4NdYMaRQIDAQAB"

class eamis:
    default_headers = default_headers
    sso_public_key = base64.b64decode(sso_public_key)
    verify = False
    
    def __init__(self):
        self.cookie_eamis = self.prepare_eamis_cookie()
        JSESSIONID = self.cookie_eamis['JSESSIONID']
        self.cookie_sso = self.prepare_sso_cookie(JSESSIONID)
        self.course_list_cache = {}
        
    def prepare_eamis_cookie(self):
        homeExt = requests.get(
            'https://eamis.nankai.edu.cn/eams/homeExt.action', 
            headers=self.default_headers, allow_redirects=False, verify=self.verify)
        return homeExt.cookies
    
    def prepare_sso_cookie(self, JSESSIONID):
        login = requests.get(
            f'https://sso.nankai.edu.cn/sso/login?service=https://eamis.nankai.edu.cn/eams/login.action;jsessionid={JSESSIONID}', 
            headers=self.default_headers, allow_redirects=False, verify=self.verify)
        return login.cookies
    
    def login(self, username, password):
        rand = self.get_rand()
        password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        password_rsa = self.jsencrypt_rsa(password)
        timestamp = str(int(time.time() * 1000))
        service = f"https://eamis.nankai.edu.cn/eams/login.action;jsessionid={self.cookie_eamis['JSESSIONID']}"
        
        data = {
            'ajax': '1',
            'username': username,
            'password': password_md5,
            'lt': timestamp,
            'rand': rand,
            't': password_rsa,
            'roleType': '',
            'service': service,
            'loginType': '0',
        }
        headers = {
            'User-Agent': self.default_headers['User-Agent'],
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://sso.nankai.edu.cn',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': f"https://sso.nankai.edu.cn/sso/login?service=https%3A%2F%2Feamis.nankai.edu.cn%2Feams%2Flogin.action%3Bjsessionid%3D{self.cookie_eamis['JSESSIONID']}",
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        login = requests.post('https://sso.nankai.edu.cn/sso/login', 
                              cookies=self.cookie_sso, 
                              headers=headers, 
                              data=data, 
                              verify=self.verify)
        
        return login
        
    def jsencrypt_rsa(self, password):
        public_key = RSA.importKey(self.sso_public_key)
        cipher = PKCS1_v1_5.new(public_key)
        return base64.b64encode(cipher.encrypt(password.encode('utf-8'))).decode('utf-8')
        
    def get_rand(self):
        rand = requests.get(
            'https://sso.nankai.edu.cn/sso/loadcode', 
            headers=self.default_headers, 
            cookies=self.cookie_sso,
            allow_redirects=False, 
            verify=self.verify)
        return rand.json()['rand']        
    
    def check_login(self):
        home = requests.get(
            'https://eamis.nankai.edu.cn/eams/home.action',
            headers=self.default_headers, 
            cookies=self.cookie_sso,
            allow_redirects=False,
            verify=self.verify
        )
        if home.status_code == 200:
            return True
        return False
    
    def get_all_semesters(self):
        all_semesters = requests.get(
            'https://eamis.nankai.edu.cn/eams/dataQuery.action?dataType=semesterCalendar', 
            headers=self.default_headers, 
            cookies=self.cookie_eamis, 
            verify=self.verify)
        corrected_json = re.sub(r'(\w+):', r'"\1":', 
                                all_semesters.text)
        return json.loads(corrected_json)
    
    def switch_to_current_semester(self):
        timestamp = str(int(time.time() * 1000))
        courseTableForStd = requests.get(
            f'https://eamis.nankai.edu.cn/eams/courseTableForStd!innerIndex.action?projectId=1&_={timestamp}', 
            headers=self.default_headers, 
            cookies=self.cookie_eamis, 
            verify=self.verify)
        self.cookie_eamis.update(courseTableForStd.cookies)

    def get_course_table(self, project_id):
        timestamp = str(int(time.time() * 1000))
        courseTableForStd = requests.get(
            f'https://eamis.nankai.edu.cn/eams/courseTableForStd!innerIndex.action?projectId=1&_={timestamp}', 
            headers=self.default_headers, 
            cookies=self.cookie_eamis, 
            verify=self.verify)
        pattern = r'if\(jQuery\("#courseTableType"\)\.val\(\)=="std"\){\s*bg\.form\.addInput\(form,"ids","(\d+)"\);'
        match = re.search(pattern, courseTableForStd.text)
        ids = match.group(1)
        
        # TODO: prase the course table
        return courseTableForStd
            
    def get_course_list(self, profile_id):
        params = {
            'profileId': profile_id,
        }
        headers = self.default_headers.copy()
        headers['Referer'] = f'https://eamis.nankai.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id={profile_id}'
        stdElectCourse = requests.get(
            'https://eamis.nankai.edu.cn/eams/stdElectCourse!data.action',
            params=params,
            cookies=self.cookie_eamis,
            headers=headers,
            verify=self.verify
        )
        pattern = r'var lessonJSONs = (.*?);'
        match = re.search(pattern, stdElectCourse.text)
        corrected_json = re.sub(r'(\w+):', r'"\1":', 
                        match.group(1)).replace('\'', '"')
        return json.loads(corrected_json)
    
    def get_profile_list(self):
        params = {
            'projectId': '1',
        }

        stdElectCourse = requests.get(
            'https://eamis.nankai.edu.cn/eams/stdElectCourse!innerIndex.action',
            params=params,
            cookies=self.cookie_eamis,
            headers=self.default_headers,
            verify=self.verify
        )
        soup = BeautifulSoup(stdElectCourse.text, 'html.parser')

        profile_info = {}

        divs = soup.find_all('div', class_='ajax_container')
        for div in divs:
            header = div.find('h3')
            link = div.find('a', href=True)

            if header and link:
                title = header.get_text(strip=True)
                url = link['href']
                profile_id = url.split('=')[-1]
                profile_info[profile_id] = title
                
        return profile_info
    
    def refresh_course_list(self, profile_id):
        self.course_list_cache[profile_id] = self.get_course_list(profile_id)
        
    def get_student_count(self, semesterId):
        """get student count of each course

        Args:
            semesterId (int): semester id, can use cookie_eamis['semester.id'] to get current semester id

        Returns:
            dict: /*sc 当前人数, lc 人数上限,upsc 计划外实际人数  ,uplc 计划外上限*/
        """
        params = {
            'projectId': '1',
            'semesterId': semesterId,
        }

        queryStdCount = requests.get(
            'https://eamis.nankai.edu.cn/eams/stdElectCourse!queryStdCount.action',
            params=params,
            cookies=self.cookie_eamis,
            headers=self.default_headers,
            verify=self.verify
        )
        
        pattern = r'window.lessonId2Counts=(.*?)'
        match = re.search(pattern, queryStdCount.text)
        corrected_json = re.sub(r'(\w+):', r'"\1":', 
                        match.group(1)).replace('\'', '"')
        return json.loads(corrected_json)
    
    def batch_operator(self, profile_id: int, course_id: int, operator: bool):
        headers = self.default_headers.copy()
        headers['Referer'] = 'https://eamis.nankai.edu.cn/eams/stdElectCourse!defaultPage.action'
        params = {
            'profileId': str(profile_id),
        }
        operator = 'true' if operator else 'false'
        data = {
            'optype': operator,
            'operator0': f'{course_id}:{operator}:0',
            'lesson0': f'{course_id}',
            f'expLessonGroup_{course_id}': 'undefined',
        }

        response = requests.post(
            'https://eamis.nankai.edu.cn/eams/stdElectCourse!batchOperator.action',
            params=params,
            cookies=self.cookie_eamis,
            headers=headers,
            data=data,
        )
        
        return response