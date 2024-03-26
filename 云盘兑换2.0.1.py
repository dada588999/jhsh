# 脚本名称: [中国移动云盘]
# 功能描述: 云盘兑换奖品
# 使用说明:
#   - [抓包 Cookie：任意Authorization]
#   - [注意事项: 简易方法，开抓包进App，搜refresh，找到authTokenRefresh.do ，请求头中的Authorization，响应体<token> xxx</token> 中xxx值（新版加密抓这个）]
# 环境变量设置:
#   - 名称：[ydypdh]   格式：[Authorization值#手机号#token值]
#   - 多账号处理方式：[换行或者@分割]
# 定时设置: [59 59 11,15 * * *]
# 更新日志:
#   - [1.30]: [同一环境变量获取]
# 注: 本脚本仅用于个人学习和交流，请勿用于非法用途。作者不承担由于滥用此脚本所引起的任何责任，请在下载后24小时内删除。
# 作者: 木兮
import os
import random
import re
import time

import requests

ua = 'Mozilla/5.0 (Linux; Android 11; M2012K10C Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.210 Mobile Safari/537.36 MCloudApp/10.0.1'
rewardName = ''  # 兑换奖品名称


class YP:
    token = None
    jwtToken = None
    num = 30  # 请求次数
    timestamp = str(int(round(time.time() * 1000)))
    cookies = {'sensors_stay_time': timestamp}

    def __init__(self, cookie):
        self.Authorization = cookie.split("#")[0]
        self.account = cookie.split("#")[1]
        self.total_amount = None
        self.jwtHeaders = {
            'User-Agent': ua,
            'Accept': '*/*',
            'Host': 'caiyun.feixin.10086.cn:7071',
        }

    def run(self):
        self.sso()
        self.jwt()
        self.receive()
        self.exchange(rewardName)

    def send_request(self, url, headers, data=None, method='GET', cookies=None):
        with requests.Session() as session:
            session.headers.update(headers)
            if cookies is not None:
                session.cookies.update(cookies)

            try:
                if method == 'GET':
                    response = session.get(url)
                elif method == 'POST':
                    response = session.post(url, json = data)
                else:
                    raise ValueError('Invalid HTTP method.')

                response.raise_for_status()
                return response.json()

            except requests.Timeout as e:
                print("请求超时:", str(e))

            except requests.RequestException as e:
                print("请求错误:", str(e))

            except Exception as e:
                print("其他错误:", str(e))

    # 刷新令牌
    def sso(self):
        url = 'https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken'
        headers = {
            'Authorization': self.Authorization,
            'User-Agent': ua,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Host': 'orches.yun.139.com'
        }
        data = {"account": self.account, "toSourceId": "001005"}
        return_data = self.send_request(url, headers = headers, data = data, method = 'POST')
        if 'success' in return_data:
            if return_data['success']:
                self.token = return_data['data']['token']
            else:
                print(return_data['message'])
        else:
            print("出现未知错误")

    # 获取jwttoken
    def jwt(self):
        url = f"https://caiyun.feixin.10086.cn:7071/portal/auth/tyrzLogin.action?ssoToken={self.token}"
        return_data = self.send_request(url = url, headers = self.jwtHeaders, method = 'POST')
        if return_data['code'] != 0:
            return print(return_data['msg'])
        self.jwtToken = return_data['result']['token']
        self.jwtHeaders['jwtToken'] = self.jwtToken
        self.cookies['jwtToken'] = self.jwtToken

    # 云朵数量
    def receive(self):
        url = "https://caiyun.feixin.10086.cn/market/signin/page/receive"
        return_data = self.send_request(url, headers = self.jwtHeaders, cookies = self.cookies)
        if return_data['msg'] == 'success':
            self.total_amount = return_data["result"].get("total", "")
            print(f'当前云朵数量:{self.total_amount}云朵')
        else:
            print(return_data['msg'])

    # 兑换奖品
    def find_prize(self, name, exchange_lists):
        for key, value in exchange_lists.items():
            for prize in value:
                prize_name = prize.get('prizeName')
                if prize_name == name:
                    prize_id = prize.get('prizeId')
                    pOrder = prize.get('pOrder')  # 消耗数量
                    return prize_id, pOrder
        return None, None

    def exchange(self, name):
        list_url = 'https://caiyun.feixin.10086.cn/market/signin/page/exchangeList'
        list_data = self.send_request(list_url, headers = self.jwtHeaders, cookies = self.cookies)
        exchange_lists = list_data.get('result', {})

        prize_id, pOrder = self.find_prize(name, exchange_lists)

        if prize_id is None:
            print(f'未找到{name}，请检查是否有该类型的会员卡。')
            return

        if self.total_amount < pOrder:
            print('当前云朵数量不足，无法兑换~~')
            return

        print(f'开始兑换奖品: {name}')
        reward_url = f'https://caiyun.feixin.10086.cn/market/signin/page/exchange?prizeId={prize_id}&client=app&clientVersion=10.2.1'

        for _ in range(self.num):
            reward_data = self.send_request(reward_url, headers = self.jwtHeaders, cookies = self.cookies)
            if reward_data.get('code') == 0:
                print('兑换成功')
                break
            else:
                print(reward_data.get('msg'))
                time.sleep(0.02)


if __name__ == "__main__":
    env_name = 'ydypdh'
    token = os.getenv(env_name)
    if not token:
        print(f'⛔️未获取到ck变量：请检查变量 {env_name} 是否填写')
        exit(0)
    cookies = re.split(r'[@\n]', token)
    print(f"共获取到{len(cookies)}个账号")

    for i, cookie in enumerate(cookies, start = 1):
        print(f"\n======== ▷ 第 {i} 个账号 ◁ ========")
        YP(cookie).run()
        print("\n随机等待5-10s进行下一个账号")
        time.sleep(random.randint(5, 10))
