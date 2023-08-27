
import requests
import hashlib
import base64
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto import Random

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
    
