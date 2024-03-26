# zgyh福仔,每日抽奖,月中一次立减金。其他分区,暂时只做云游长白山,云游天府
# ck,分两种，大厅一个，其他分区通用一个
# bocfz.sinodoc.cn:8099 域名下authorization值 大厅填入main_auth
# branch-fz.sinodoc.cn:8787 域名下authorization值,分区通用填入fq_auth
# 日期：11.1
# 作者: 木兮
import time
from os import path

import requests

GLOBAL_DEBUG = False  # 全局除错
send_notify = True  # 发送通知
main_auth = 'boccb82045c86a5c1bc71ed8f5fe64a71f8'
fq_auth = 'boc4b9e2802881820ba56e8d5f12e375551'
send_msg = ''

headers = {
    'authorization': main_auth,
    'origin': 'https://bocfz.sinodoc.cn',
    'x-requested-with': 'com.chinamworld.bocmbci',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://bocfz.sinodoc.cn/',
    'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
}

'''
福仔设置区域,每日抽奖等级 draw_level,2-6,设置高，等级不够就不会抽奖
'''
draw_level = 4

'''
云游长白山设置区域  0 为88人参抽一次，  1为880人参，抽十次
'''
jilin_turn_type = '1'


# 发送通知
def load_send():
    cur_path = path.abspath(path.dirname(__file__))
    notify_file = cur_path + "/notify.py"

    if path.exists(notify_file):
        try:
            from notify import send  # 导入模块的send为notify_send
            print("加载通知服务成功！")
            return send  # 返回导入的函数
        except ImportError:
            print("加载通知服务失败~")
    else:
        print("加载通知服务失败~")

    return False  # 返回False表示未成功加载通知服务


# 捕获异常
def catch_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print("发生了错误:", str(e))
        return None

    return wrapper


def send_request(url, headers=None, params=None, data=None, cookies=None, method='GET', debug=None, retries=3):
    # 如果没有指定 debug 参数，就使用全局的 debug 设置
    debug = debug if debug is not None else GLOBAL_DEBUG

    with requests.Session() as session:
        for attempt in range(retries):
            try:
                # 更新请求头部信息
                session.headers.update(headers or {})

                if cookies is not None:
                    # 更新 cookies
                    session.cookies.update(cookies)

                # 根据传入的数据类型选择发送请求的方式（JSON 或者普通数据）
                if isinstance(data, dict):
                    response = session.request(method, url, params = params, json = data)
                else:
                    response = session.request(method, url, params = params, data = data)

                # 如果请求失败，抛出异常
                response.raise_for_status()

                # 如果启用了 debug 模式，打印响应内容
                if debug:
                    print(response.text)

                return response

            except (requests.RequestException, ConnectionError, TimeoutError) as e:
                # 捕获特定类型的异常，并打印错误信息
                print(f"请求失败: {e}")

                if attempt < retries - 1:
                    # 如果尝试次数未达到上限，重试请求
                    print(f"开始重发请求 {attempt + 1}/{retries}")
                    continue
                else:
                    # 达到重试次数上限，返回 None
                    print(f"重发次数达上限")
                    return None


# 主区域
# 福仔等级信息
@catch_errors
def fz_user_info():
    info_url = 'https://bocfz.sinodoc.cn:8099/api/UserInfo/detail'
    info_data = send_request(info_url, headers, method = "POST").json()
    global send_msg
    if info_data.get('code') != '200':
        print(info_data.get('msg'))
        send_msg += info_data.get('msg')
        return None
    user = info_data.get('data', {}).get('user', {})
    nickname = info_data.get('data', {}).get('nickname')
    level = user.get('level')
    score = user.get('score')
    print(f'【福仔云游记】: 用户【{nickname}】,等级【{level}】,福气值【{score}】')
    return level


@catch_errors
def fz_task_list():
    level = fz_user_info()
    if level is None:
        return None

    print('获取任务信息')
    tasklist_url = 'https://bocfz.sinodoc.cn:8099/api/Tasks/allTaskLists'
    tasklist_payload = {"channel": "boc"}
    tasklist_data = send_request(tasklist_url, headers, data = tasklist_payload, method = "POST").json()
    task5 = [value for value in tasklist_data.get('data').values() if
             isinstance(value.get('type'), int) and value.get('type') == 5]

    for value in task5:
        id = value.get('id')
        name = value.get('name')
        state = value.get('state')
        if state == 1:
            print(f'已完成: {name}')
            continue
        print(f'去完成: {name}')
        fz_do_task(id)

    print('每日福仔抽奖')
    fz_to_draw(level)
    print('查询奖品信息')
    fz_prize_list()


@catch_errors
def fz_do_task(id):
    click_task_url = 'https://bocfz.sinodoc.cn:8099/api/Tasks/clickTaskBotm'
    click_task_payload = {"taskid": id, "state": 0}
    send_request(click_task_url, headers, data = click_task_payload, method = "POST")
    task_detail_url = 'https://bocfz.sinodoc.cn:8099/api/Tasks/taskDetail'
    task_detail_payload = {"tid": id, "channel": "boc"}
    task_detail_data = send_request(task_detail_url, headers, data = task_detail_payload, method = "POST").json()
    score = task_detail_data.get('data', {}).get('score')
    print(f'任务完成获得: {score}福气值')
    time.sleep(3.5)


@catch_errors
def fz_to_draw(level):
    if level < draw_level:
        print('当前福仔等级,小于预设等级,不做抽奖')
        return

    num_url = 'https://bocfz.sinodoc.cn:8099/promotion/ZhTtcj/initData'
    num_payload = {"level": draw_level}
    num_data = send_request(num_url, headers, data = num_payload, method = "POST").json()
    cj_num = num_data.get('data', {}).get('cj_num')
    if cj_num <= 0:
        print('今日抽奖次数已用完')
        return

    award_url = 'https://bocfz.sinodoc.cn:8099/promotion/ZhTtcj/asyncAward'
    award_data = send_request(award_url, headers, data = num_payload, method = "POST").json()
    order_id = award_data.get('data', {}).get('order_id')
    time.sleep(3)

    award_result_url = 'https://bocfz.sinodoc.cn:8099/promotion/ZhTtcj/asyncAwardResult'
    award_result_payload = {"order_id": order_id}
    award_result_data = send_request(award_result_url, headers, data = award_result_payload, method = "POST").json()
    prize = award_result_data.get('data', {}).get('prize')
    print(f'抽奖获得: {prize}')


@catch_errors
def fz_prize_list():
    url = 'https://bocfz.sinodoc.cn:8099/api/Prizes/prizesLists'
    response = send_request(url, headers, method = "POST").json()
    # rlist = response.get('data').get('rlist') # 卡券
    alist = response.get('data').get('alist')  # 礼品
    global send_msg
    for value in alist:
        type = value.get('type')
        state = value.get('state')
        prize = value.get('prize')
        if int(type) == 30:
            if state == 10:
                print(f'【福仔奖品信息】已领取:{prize}')
                send_msg += f'\n【福仔奖品信息】已领取:{prize}'
            else:
                print(f'【福仔奖品信息】待领取: {prize}')
                send_msg += f'\n【福仔奖品信息】待领取: {prize}'


# 云游长白山
@catch_errors
def jilin_detail():
    detail_url = 'https://branch-fz.sinodoc.cn:8787/jilin/user/detail'
    detail_data = send_request(detail_url, headers).json()
    if detail_data.get('code') != '200':
        print(detail_data.get('msg'))
        return None, None, None
    quantity_num = detail_data.get('data').get('quantity_num')  # 人参数量
    award_num = detail_data.get('data').get('award_num')  # 剩余甩子
    turntable_num = detail_data.get('data').get('turntable_num')  # 本月剩余转盘次数
    print(f'\n【云游长白山】:  人参数量 【{quantity_num}】,剩余骰子 【{award_num}】,剩余转盘次数 【{turntable_num}】')

    return quantity_num, award_num, turntable_num


@catch_errors
def jinlin_tasklists():
    quantity_num, award_num, turntable_num = jilin_detail()
    if quantity_num is None:
        return

    print('获取任务信息')

    lists_url = 'https://branch-fz.sinodoc.cn:8787/jilin/task/lists'
    lists_data = send_request(lists_url, headers).json()

    games = lists_data.get('data').get('games')  # 游戏任务
    views = lists_data.get('data').get('views')  # 浏览任务
    standard = lists_data.get('data').get('standard')  # 达标任务

    for game, view, standard_task in zip(games, views, standard):
        for task in [game, view, standard_task]:
            name = task.get('name')
            id = task.get('id')
            state = task.get('state')
            type = task.get('type')
            if type == 3:
                if id == 14:
                    if state in [1, 2]:
                        action = '去领取' if state == 2 else '去完成'
                        print(f'{action}: {name}奖励')
                        award_num = jilin_finish(id)
                    else:
                        print(f'已完成: {name}')
            elif type in [1, 2]:
                if state in [3, 4]:
                    print(f'已完成: {name}')
                elif state in [1, 2]:
                    action = '去领取' if state == 2 else '去完成'
                    print(f'{action}: {name}奖励')
                    award_num = jilin_finish(id)

    if award_num <= 0:
        print('当前骰子数量不足,去抽奖')
        jilin_turn(quantity_num, turntable_num)
        print('查询奖品信息')
        jilin_prize()
        return

    # 掷骰子,人参数量
    print(f'骰子数量:{award_num},去掷骰子')
    quantity_num = jilin_toaward(award_num)
    # 抽奖,剩余次数
    print('去抽奖')
    jilin_turn(quantity_num, turntable_num)
    print('查询奖品信息')
    jilin_prize()


@catch_errors
def jilin_finish(id):
    finish_url = f'https://branch-fz.sinodoc.cn:8787/jilin/task/finish?tid={id}'
    finish_data = send_request(finish_url, headers).json()

    msg = finish_data.get("msg")
    new_award_num = finish_data.get("data", {}).get("award_num")
    print(f'{msg},当前剩余骰子数量: {new_award_num}')
    time.sleep(2)
    return new_award_num


@catch_errors
def jilin_toaward(award_num):
    num = None
    for _ in range(award_num):
        toaward_url = 'https://branch-fz.sinodoc.cn:8787/jilin/draw/toaward'
        toaward_data = send_request(toaward_url, headers).json()
        award_num = toaward_data.get('data').get('list').get('award_num')  # 获得人参
        quantity_num = toaward_data.get('data').get('info').get('quantity_num')  # 当前人参
        num = quantity_num
        print(f'掷骰子获得人参: {award_num}, 总数: {quantity_num}')
        time.sleep(3)
    return num


@catch_errors
def jilin_turn(quantity_num, turntable_num):
    result = None
    if jilin_turn_type == '0':
        result = quantity_num // 88
    elif jilin_turn_type == '1':
        result = quantity_num // 880

    if result <= 0:
        return print('当前人参数量不足，无法抽奖')
    if turntable_num < result:
        result = turntable_num
    for _ in range(result):
        turn_url = f'https://branch-fz.sinodoc.cn:8787/jilin/turntable/finish?type={jilin_turn_type}'
        turn_data = send_request(turn_url, headers).json()
        name = turn_data.get('data').get('list')[0].get('name')
        print(name)
        time.sleep(3)


@catch_errors
def jilin_prize():
    url = 'https://branch-fz.sinodoc.cn:8787/jilin/prize/lists'
    response = send_request(url, headers).json()
    data = response.get('data')
    global send_msg
    if not data:
        print('【云游长白山】暂未获得奖品')
        send_msg += '\n【云游长白山】暂未获得奖品'
        return
    for value in data:
        name = value.get('name')
        state_desc = value.get('state_desc')
        print(f'【云游长白山】{name}: {state_desc}')
        send_msg += f'\n【云游长白山】{name}: {state_desc}'


# 云游天府
@catch_errors
def sichun_user_detail():
    user_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/user/detail'
    user_data = send_request(user_url, headers).json()
    if user_data.get('code') != '200':
        print(user_data.get('msg'))
        return None
    is_sign = user_data.get('data').get('is_sign')
    level = user_data.get('data').get('level')
    score = user_data.get('data').get('score')  # 福竹数量
    # eattime = user_data.get('data').get('eattime')  # 吃饭时间
    # drilltime = user_data.get('data').get('drilltime')  # 训练时间
    # drill_num = user_data.get('data').get('drill_num')  # 训练数量
    # cleantime = user_data.get('data').get('cleantime')  # 清洁时间
    # clean_num = user_data.get('data').get('clean_num')  # 清洁数量
    # washtime = user_data.get('data').get('washtime')  # 洗涤时间
    # wash_num = user_data.get('data').get('wash_num')  # 洗涤数量
    print(f'\n【云游天府】 等级 【{level}】,福竹数量 【{score}】')
    if is_sign == 0:
        print('去签到')
        sichun_signin()
    elif is_sign == 1:
        print('今日已签到')
    return score


@catch_errors
def sichun_tasklist():
    score = sichun_user_detail()
    if score is None:
        return
    print('获取任务信息')
    list_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/task/lists'
    list_data = send_request(list_url, headers).json()
    games = list_data.get('data').get('games')  # 游戏任务
    views = list_data.get('data').get('views')  # 浏览任务
    standard = list_data.get('data').get('standard')  # 达标任务

    for game, view, standard_task in zip(games, views, standard):
        for task in [game, view, standard_task]:
            name = task.get('name')
            id = task.get('id')
            state = task.get('state')
            type = task.get('type')
            num = task.get('n_max') - task.get('num')
            if type == 3:
                if id == 14:
                    if state in [1, 2]:
                        action = '去领取' if state == 2 else '去完成'
                        print(f'{action}: {name}奖励')
                        score = sichun_finish(id)
                    else:
                        print(f'已完成: {name}')
            elif type == 2:
                if state in [3, 4]:
                    print(f'已完成: {name}')
                elif state in [1, 2]:
                    action = '去领取' if state == 2 else '去完成'
                    print(f'{action}: {name}奖励')
                    score = sichun_finish(id)
            elif type == 1:
                if id == 4:
                    if state == 3:
                        print(f'已完成: {name}')
                    else:
                        prop_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/userProps/getRandProps'  # 园子
                        prop_data = send_request(prop_url, headers).json()
                        data = prop_data.get('data')
                        if not data:
                            print('暂无每日道具，或已领取')
                        else:
                            for i in data:
                                id = i.get('id')
                                name = i.get('name')
                                print(f'去领取: {name}')
                                sendprop_url = f'https://branch-fz.sinodoc.cn:8787/sichuan/userProps/sendProps?pid={id}'
                                sendprop_data = send_request(sendprop_url, headers).json()
                                if sendprop_data.get('code') == '200':
                                    print('领取成功')
                                    time.sleep(2)
                else:
                    if state in [3, 4]:
                        print(f'已完成: {name}')
                    elif state in [1, 2]:
                        action = '去领取' if state == 2 else '去完成'
                        print(f'{action}: {name}奖励')
                        for _ in range(num):
                            score = sichun_finish(id)
    print('去抽奖')
    sichun_draw(score)
    print('查询奖品信息')
    sichun_prize()


@catch_errors
def sichun_finish(id):
    finish_url = f'https://branch-fz.sinodoc.cn:8787/sichuan/task/finish?tid={id}'
    finish_data = send_request(finish_url, headers).json()
    msg = finish_data.get('msg')
    prize = finish_data.get('data').get('prize')
    score = finish_data.get('data').get('info').get('score')  # 福竹数量
    for value in prize:
        name = value.get('name')
        print(f'{msg}获得: {name}')
    time.sleep(2)
    return score


@catch_errors
def sichun_signin():
    signin_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/sign/sign'
    signin_data = send_request(signin_url, headers).json()
    if signin_data.get('code') == '200':
        print('签到成功')
    else:
        print(signin_data.get('msg'))


@catch_errors
def sichun_draw(score):
    if score < 10:
        print('福竹数量不足，无法抽奖')
        return
    num_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/ttcj/init'
    num_data = send_request(num_url, headers).json()
    num = num_data.get('data').get('num')
    if num <= 0:
        print('今日已抽奖')
        return
    draw_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/ttcj/asyncAward'
    draw_data = send_request(draw_url, headers).json()
    msg = draw_data.get('msg')
    name = draw_data.get('data').get('prize')[0].get('name')
    print(f'{msg}获得:{name}')


@catch_errors
def sichun_prize():
    url = 'https://branch-fz.sinodoc.cn:8787/sichuan/prize/lists'
    response = send_request(url, headers).json()
    list = response.get('data').get('list')
    global send_msg
    if not list:
        print('【云游天府】暂未获得奖品')
        send_msg += '\n【云游天府】暂未获得奖品'
    for value in list:
        name = value.get('name')
        state_desc = value.get('state_desc')
        print(f'【云游天府】{name}: {state_desc}')
        send_msg += f'\n【云游天府】{name}: {state_desc}'


# 云游云南
@catch_errors
def yunnan_user_detail():
    user_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/user/detail'
    user_data = send_request(user_url, headers).json()
    if user_data.get('code') != '200':
        print(user_data.get('msg'))
        return None
    cloud_val = user_data.get('data').get('cloud_val')  # 七彩祥云
    flower_val = user_data.get('data').get('flower_val')  # 繁花值
    water_val = user_data.get('data').get('water_val')  # 水滴数量

    print(f'\n【云游云南】 水滴数量 【{water_val}】,七彩祥云数量 【{cloud_val}】')
    return cloud_val


@catch_errors
def sichun_tasklist():
    score = sichun_user_detail()
    if score is None:
        return
    print('获取任务信息')
    list_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/task/lists'
    list_data = send_request(list_url, headers).json()
    games = list_data.get('data').get('games')  # 游戏任务
    views = list_data.get('data').get('views')  # 浏览任务
    standard = list_data.get('data').get('standard')  # 达标任务

    for game, view, standard_task in zip(games, views, standard):
        for task in [game, view, standard_task]:
            name = task.get('name')
            id = task.get('id')
            state = task.get('state')
            type = task.get('type')
            num = task.get('n_max') - task.get('num')
            if type == 3:
                if id == 14:
                    if state in [1, 2]:
                        action = '去领取' if state == 2 else '去完成'
                        print(f'{action}: {name}奖励')
                        score = sichun_finish(id)
                    else:
                        print(f'已完成: {name}')
            elif type == 2:
                if state in [3, 4]:
                    print(f'已完成: {name}')
                elif state in [1, 2]:
                    action = '去领取' if state == 2 else '去完成'
                    print(f'{action}: {name}奖励')
                    score = sichun_finish(id)
            elif type == 1:
                if id == 4:
                    if state == 3:
                        print(f'已完成: {name}')
                    else:
                        prop_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/userProps/getRandProps'  # 园子
                        prop_data = send_request(prop_url, headers).json()
                        data = prop_data.get('data')
                        if not data:
                            print('暂无每日道具，或已领取')
                        else:
                            for i in data:
                                id = i.get('id')
                                name = i.get('name')
                                print(f'去领取: {name}')
                                sendprop_url = f'https://branch-fz.sinodoc.cn:8787/sichuan/userProps/sendProps?pid={id}'
                                sendprop_data = send_request(sendprop_url, headers).json()
                                if sendprop_data.get('code') == '200':
                                    print('领取成功')
                                    time.sleep(2)
                else:
                    if state in [3, 4]:
                        print(f'已完成: {name}')
                    elif state in [1, 2]:
                        action = '去领取' if state == 2 else '去完成'
                        print(f'{action}: {name}奖励')
                        for _ in range(num):
                            score = sichun_finish(id)
    print('去抽奖')
    sichun_draw(score)
    print('查询奖品信息')
    sichun_prize()


@catch_errors
def sichun_finish(id):
    finish_url = f'https://branch-fz.sinodoc.cn:8787/sichuan/task/finish?tid={id}'
    finish_data = send_request(finish_url, headers).json()
    msg = finish_data.get('msg')
    prize = finish_data.get('data').get('prize')
    score = finish_data.get('data').get('info').get('score')  # 福竹数量
    for value in prize:
        name = value.get('name')
        print(f'{msg}获得: {name}')
    time.sleep(2)
    return score


@catch_errors
def sichun_signin():
    signin_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/sign/sign'
    signin_data = send_request(signin_url, headers).json()
    if signin_data.get('code') == '200':
        print('签到成功')
    else:
        print(signin_data.get('msg'))


@catch_errors
def sichun_draw(score):
    if score < 10:
        print('福竹数量不足，无法抽奖')
        return
    num_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/ttcj/init'
    num_data = send_request(num_url, headers).json()
    num = num_data.get('data').get('num')
    if num <= 0:
        print('今日已抽奖')
        return
    draw_url = 'https://branch-fz.sinodoc.cn:8787/sichuan/ttcj/asyncAward'
    draw_data = send_request(draw_url, headers).json()
    msg = draw_data.get('msg')
    name = draw_data.get('data').get('prize')[0].get('name')
    print(f'{msg}获得:{name}')


@catch_errors
def sichun_prize():
    url = 'https://branch-fz.sinodoc.cn:8787/sichuan/prize/lists'
    response = send_request(url, headers).json()
    list = response.get('data').get('list')
    global send_msg
    if not list:
        print('【云游天府】暂未获得奖品')
        send_msg += '\n【云游天府】暂未获得奖品'
    for value in list:
        name = value.get('name')
        state_desc = value.get('state_desc')
        print(f'【云游天府】{name}: {state_desc}')
        send_msg += f'\n【云游天府】{name}: {state_desc}'


# 云游黄山
@catch_errors
def run():
    fz_task_list()
    time.sleep(2)
    headers['authorization'] = fq_auth
    jinlin_tasklists()
    time.sleep(2)
    sichun_tasklist()


if __name__ == "__main__":
    run()
    # 在load_send中获取导入的send函数
    send = load_send()

    # 判断send是否可用再进行调用
    if send:
        send('福仔云游记', send_msg)
    else:
        print('通知服务不可用')
