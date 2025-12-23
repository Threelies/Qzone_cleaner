import time
import requests
import re
import pymongo
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from urllib import parse
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class Spider:
    def __init__(self, qq, password, host, port, db):
        self.__username = qq
        self.__password = password
        self.ids = ""
        self.uins = ""

        chrome_options = Options()
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.req = requests.Session()

        self.client = pymongo.MongoClient(host=host, port=port)
        self.db = self.client[db]

    def login(self):
        self.driver.get('https://qzone.qq.com/')
        self.driver.set_window_position(20, 40)
        self.driver.set_window_size(1100, 700)
        self.driver.switch_to.frame('login_frame')

        self.driver.execute_script(
            "var a = document.getElementById('qlogin_list');"
            "if(a && a.firstElementChild){a.removeChild(a.firstElementChild);}"
        )

        self.driver.find_element(By.ID, 'switcher_plogin').click()
        self.driver.find_element(By.ID, 'u').clear()
        self.driver.find_element(By.ID, 'u').send_keys(self.__username)
        
        #由于现在登录时经常有图片验证导致代码卡死，所以在这直接改成手动操作
        #在弹出的浏览器输入password或扫码、完成图片验证后进入空间主页，代码终端按两次enter键开始运行。
        print("请手动输入密码，然后按 Enter 键继续...")
        input("按 Enter 键继续...")

        print("登录成功后请手动完成图片验证码验证，完成后按 Enter 键继续...")
        input("按 Enter 键继续...")

        time.sleep(3)
        self.driver.get('http://user.qzone.qq.com/{}'.format(self.__username))

        cookies_dict = {item['name']: item['value'] for item in self.driver.get_cookies()}
        self.cookies = cookies_dict

        self.get_g_tk()

        cookie_str = "; ".join([f"{name}={value}" for name, value in self.cookies.items()])
        self.headers = {'Cookie': cookie_str}

    def get_g_tk(self):
        p_skey = self.cookies.get('p_skey', '')
        h = 5381
        for i in p_skey:
            h += (h << 5) + ord(i)
        self.g_tk = h & 2147483647

    def _parse_jsonp(self, text: str):
        text = (text or "").strip()
        m = re.search(r'\(\s*(\{.*\})\s*\)', text, flags=re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except Exception:
            return None

    def get_ids_batch(self, num=10):
        base = 'https://user.qzone.qq.com/proxy/domain/m.qzone.qq.com/cgi-bin/new/get_msgb?'
        params = {
            'uin': self.__username,
            'hostUin': self.__username,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'sort': 0,
            'num': num,
            'start': 0,
            'format': 'jsonp',
            'g_tk': self.g_tk,
            '_': int(time.time() * 1000)
        }
        url = base + parse.urlencode(params)

        board = self.req.get(url, headers=self.headers, timeout=20)
        time.sleep(1)

        obj = self._parse_jsonp(board.text)
        if not obj:
            # 兜底兼容极端情况
            if '\"commentList\":[]' in board.text:
                return [], []
            # 解析失败时直接返回空，避免死循环
            print("get_msgb 返回无法解析，可能登录态异常/风控。")
            print(board.text[:300])
            return [], []

        comment_list = (obj.get("data") or {}).get("commentList") or []
        if not comment_list:
            return [], []

        ids, uins = [], []
        for item in comment_list[:num]:
            _id = str(item.get("id", "")).strip()
            _uin = str(item.get("uin", "")).strip()
            if _id and _uin:
                ids.append(_id)
                uins.append(_uin)

        return ids, uins

    def del_board(self):
        print("本轮删除：", self.ids, self.uins)
        url = 'https://h5.qzone.qq.com/proxy/domain/m.qzone.qq.com/cgi-bin/new/del_msgb?' + '&g_tk=' + str(self.g_tk)
        data = {
            'hostUin': self.__username,
            'idList': self.ids,
            'uinList': self.uins,
            'iNotice': 1,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'ref': 'qzone',
            'json': 1,
            'g_tk': self.g_tk,
            'format': 'fs',
            'qzreferrer': 'https://qzs.qq.com/qzone/msgboard/msgbcanvas.html'
        }
        response = self.req.post(url, data=data, headers=self.headers, timeout=20).text
        print(response)

    def del_all(self, batch_size=10, max_rounds=10000):
        last_ids = None
        stuck = 0

        for r in range(1, max_rounds + 1):
            ids, uins = self.get_ids_batch(num=batch_size)
            if not ids:
                print("commentList 为空，删除结束。")
                return

            print(f"[Round {r}] 读取到 {len(ids)} 条，开始删除...")

            if last_ids == ids:
                stuck += 1
            else:
                stuck = 0
            last_ids = ids

            if stuck >= 3:
                print("连续 3 轮读到同一批 ID，可能存在无法删除/风控限制，停止以避免死循环。")
                print("卡住的 IDs:", ids)
                return

            self.ids = ",".join(ids) + ","
            self.uins = ",".join(uins) + ","

            self.del_board()
            time.sleep(1.2)


if __name__ == '__main__':
    qq = 'your_qq_number'
    password = 'your_password'
    host = 'localhost'
    port = 27017
    db = 'QQ'

    sp = Spider(qq, password, host, port, db)
    sp.login()
    sp.del_all(batch_size=10)
