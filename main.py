import time

import requests
import urllib3
import logging


urllib3.disable_warnings()

logging.basicConfig(filename="/timing/yufuguanjia.log", level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


total_account_password = {
    "phone": "password"
}


class ClockIn(object):
    def __init__(self, phone, password):
        self.card_id = ""
        self.name = ""
        self.nexttime = ""
        self.phone = phone
        self.password = password
        self.cs_num = "派出所给的二维码数据"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
                          "MicroMessenger/8.0.38(0x1800262b) NetType/WIFI Language/zh_CN",

            "Referer": "https://servicewechat.com/wx2b66be5e3196fc46/134/page-frame.html"
        }
        # 登录
        token = self.login()
        if token is None:
            self.error("登录失败")
            raise Exception("登录失败")
        else:
            self.info(f"登录成功{token}")
            self.token = token
        # 获取用户信息
        self.request_user_info()

    def info(self, message, func_name=""):
        logging.info(f"{func_name}----{self.name}:{message}")

    def error(self, message, func_name=""):
        logging.error(f"{func_name}----{self.name}:{message}")

    def headers_token(self):
        return {
            **self.headers,
            "Authorization": self.token
        }

    def login(self):
        url = "https://shyly.autosec.cn/app/login"
        params = {
            "username": self.phone,
            "password": self.password
        }
        res = requests.post(url=url, params=params, verify=False).json()
        code = res.get("code")
        if code == 200:
            self.info("登录成功", "login")
            return res.get("token")
        else:
            self.error("登录失败", "login")
            return None

    def request_user_info(self):

        # {
        #     "msg": "操作成功",
        #     "employ": {
        #         "empId": 227684,
        #         "empPhone": "13913918492",
        #         "empCardid": "342201199606265926",
        #         "empPasw": "",
        #         "empName": "李欠男",
        #         "empCardidType": "A",
        #         "empHuji": "安徽省-宿州市-埇桥区",
        #         "empRegionCode": "1484",
        #         "empNation": "01",
        #         "empDuty": "50",
        #         "empGender": "0",
        #         "empArea": "1172",
        #         "empStreet": "27031",
        #         "empAddress": "浦东新区迎春路809号",
        #         "empPicture": null,
        #         "empPicturecode": "649d8507180f534d0792e030",
        #         "empStatus": "0",
        #         "empActivate": "0",
        #         "empCreateTime": "2023-06-29 21:19:35",
        #         "empUpdateTime": null,
        #         "empMark": null,
        #         "activateCode": "649d8507180f534d0792e030",
        #         "activateTime": "2023-06-29 21:20:08",
        #         "empZzid": null,
        #         "empAcflag": "1",
        #         "isdown": null,
        #         "iscompare": null,
        #         "isadult": null,
        #         "empBirth": null,
        #         "empCountry": null,
        #         "empCoin": null,
        #         "isfzr": "0",
        #         "compareRes": null,
        #         "compareScore": null,
        #         "papersTypeName": "居民身份证",
        #         "nationms": "汉族",
        #         "regionName": "浦东新区",
        #         "addressName": "迎春路",
        #         "duty": null
        #     },
        #     "isadult": "yes",
        #     "ischeck": "yes",
        #     "code": 200,
        #     "nexttime": "2023-07-01 08:00:00",
        #     "iszjbx": "0",
        #     "isexist": true
        # }
        res = requests.post(
            url="https://shyly.autosec.cn/app/getInfo", headers=self.headers_token()).json()
        self.card_id = res['employ']['empCardid']
        self.name = res['employ']['empName']
        self.nexttime = res['nexttime']
        self.info(
            f"获取用户信息成功:{self.name}{self.card_id}{self.nexttime}", "request_user_info")

    def check_active_time(self):
        return time.strptime(self.nexttime, "%Y-%m-%d %H:%M:%S") > time.localtime(time.time())

    def base_work(self, url):
        for k in range(3):
            res = requests.post(url=url, headers=self.headers_token(),
                                data={
                                    "cardid": self.card_id,
                                    "ylcsNum": self.cs_num
            }).json()

            code = res.get("code")
            if code == 200:
                self.info("打卡成功", "base_work")
                return True
            elif code == 601:
                self.info("不能重复打卡", "base_work")
                return True
            else:
                self.error(f"打卡失败:{res}", "base_work")
                pass

    def in_work(self):
        # 检查激活状态
        self.check_active()
        # 检查是否已打卡
        if not self.check_in_options():
            self.base_work(
                "https://shyly.autosec.cn/ylinter/empaction/checkIn")
        else:
            self.info("已打卡", "in_work")

    def out_work(self):
        # 检查激活状态
        self.check_active()
        self.base_work("https://shyly.autosec.cn/ylinter/empaction/checkOut")

    def check_in_options(self):
        res = requests.post(url="https://shyly.autosec.cn/ylinter/empaction/judgeCheckIn", headers=self.headers_token(),
                            data={
                                "cardid": self.card_id
        }).json()
        if res.get("ylcs") == "":
            self.info("未打卡", "check_in_options")
            return False
        else:
            self.info("已打卡", "check_in_options")
            return True

    def check_active(self):
        if not self.check_active_time():
            self.info("未激活", "check_active")
            files = [
                ("file", ("tmp_876asdjhf7876s6f66.jpg",
                 open("./1.jpg", "rb"), "image/jpeg")),
            ]

            upload_image_res = requests.post(url="https://shyly.autosec.cn/ylinter/file/uploadImage",
                                             headers=self.headers,
                                             files=files).json()

            res = requests.post(url="https://shyly.autosec.cn/ylinter/empaction/employActive",
                                headers=self.headers_token(),
                                data={
                                    "cardid": self.card_id,
                                    "picture": upload_image_res['imageid']
                                }).json()
            self.info(f"激活结果:{res}", "check_active")
            return res['code']


def in_work():
    for phone, password in total_account_password.items():
        driver = ClockIn(phone=phone, password=password)
        driver.in_work()


def out_work():
    for phone, password in total_account_password.items():
        driver = ClockIn(phone=phone, password=password)
        driver.out_work()


if __name__ == '__main__':
    in_work()
    # out_work()
