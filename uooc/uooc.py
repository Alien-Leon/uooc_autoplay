import sys
import requests
import json
import time
import os

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/56.0.2924.87 Safari/537.36',
    'accept-language': 'zh-CN,zh;q=0.9',  # 请求中文版网页
    'content-type': 'application/x-www-form-urlencoded',
    'accept': '*/*',
    'Referer': 'http://www.uooconline.com/home/learn/index',
    'Connection': 'keep-alive',
    'Cookie': '' # 手动填充登录后的Cookie字符串至此行即可使用
}

Data = {
    'chapter_id': '',
    'cid': '',
    'hidemsg_': 'true',
    'network': 4,
    'resource_id': '',
    'section_id': '',
    'source': '1',
    'subsection_id': 0,
    'video_length': 0,
    'video_pos': 0
}

POST_URL = "http://www.uooconline.com/home/learn/markVideoLearn"
LOGIN_URL = "http://www.uooconline.com/user/login"
LIST_URL = "http://www.uooconline.com/home/course/list?page=1&type=learn"
LOGIN_DATA = {
    'account': '',
    'password': '',
    'remember': 'true'
}


session = requests.Session()
session.headers = HEADERS

# 登录选项，由于uooc的登录模式更改暂时无法使用，可以直接更改header中cookie
#
# while True:
#     print("请输入邮箱账号")
#     account: str = input()
#     LOGIN_DATA['account'] = account
#     print("请输入密码")
#     password = input()
#     LOGIN_DATA['password'] = password
#
#     # 模拟登录
#     r = session.post(LOGIN_URL, LOGIN_DATA)
#     print('登录中。。。。')
#     login_js = json.loads(r.text)
#     if login_js['code'] == 600:
#         print("账号或密码不正确，请重新输入。")
#     else:
#         break
#
# # 清除命令行内容
# os.system('cls')

# # 调试使用：直接登录
# r = session.post(LOGIN_URL, LOGIN_DATA)

# 获取课程列表

r = session.get(LIST_URL)
list_js = json.loads(r.text)

print('请输入编号选择观看课程')

i = 0
for list in list_js['data']['data']:
    print(i, " ----> ", list['parent_name'])
    i += 1
num = int(input())
# cid 为课程id
cid = list_js['data']['data'][num]['id']

while True:

    # 获取当前课程目录
    CATALOGLIST_URL = "http://www.uooconline.com/home/learn/getCatalogList?cid=%s" % cid
    r = session.get(url=CATALOGLIST_URL)
    cata_js = json.loads(r.text)
    courses = cata_js['data']

    # 遍历课程目录获取当前进度
    find = 0
    second = 0  # 判断是否含二级目录
    cur = {}
    for i in courses:
        # print(i)
        children = i['children']
        for j in children:
            # print(j)

            # 判断是否有二级目录
            children = j.get('children', [])
            if len(children) != 0:
                # print("child----")
                # print(j)
                chapter_id = j['pid']
                # print("该目录含有子目录")
                for child in children:
                    if child['finished'] == 0:
                        j = child
                        second = 1
                        break
            if j['finished'] == 0:
                cur = j
                find = 1
                break
        if find == 1:
            break

    pid = cur['pid']
    id = cur['id']
    name = cur['name']
    test = 0
    print("\n")
    print("当前进度为：", cur['name'])
    # print(cur)
    if cur['task_id'] != 0:
        print("目前进度为测验，请自己动手吧!")
        test = 1
        break
    else:
        if second == 0:
            CUR_URL = "http://www.uooconline.com/home/learn/getUnitLearn?catalog_id=%s&chapter_id=%s&" \
                      "cid=%s&hidemsg_=true&section_id=%s&show=" % (id, pid, cid, id)
            r = session.get(CUR_URL)

        else:
            # catalog_id=subsection_id= id, chapter_id=chapter_id, sectionid=pid, cid=cid,
            # print(id, chapter_id, cid, pid, id)
            CUR_URL = "http://www.uooconline.com/home/learn/getUnitLearn?catalog_id=%s&chapter_id=%s&cid=%s&" \
                      "hidemsg_=true&section_id=%s&show=&subsection_id=%s" % (id, chapter_id, cid, pid, id)
            r = session.get(CUR_URL)

        cur_json = json.loads(r.text)
        data = cur_json['data']


        count = -1
        for d in data:
            if d['task_id'] != 0 and d['finished'] == 0:
                print("目前进度为测验，请自己动手吧!")
                test = 1
                break
            if d['finished'] == 0 and d['is_task'] == "1":
                count+=1
                break
            count += 1
        if test == 1:
            break

        data = data[count]
        # print("正在播放")
        # print("count %d",count)
        # print(data)

        finished = data['finished']
        if finished == 1:
            continue
        video_pos = float(data['video_pos'])
        reid = data['id']
        while True:

            Data['cid'] = cid
            if second == 0:
                Data['section_id'] = id
                Data['resource_id'] = reid
                Data['chapter_id'] = pid
                # print("1",Data)
            else:
                Data['chapter_id'] = chapter_id
                Data['subsection_id'] = id
                Data['section_id'] = pid
                Data['resource_id'] = reid
                # print("2",Data)
            Data['video_pos'] = video_pos
            r = session.post(url=POST_URL, data=Data)
            video_pos += 120

            # 不能提交过快，最好是按照视频时间提交
            js = json.loads(r.text)
            # print(js)
            if js['data']['finished'] == 1:
                break

            for i in range(120, 0, -2):
                print("\r正在观看: %s--> %s s" % (name, video_pos-i), end="")
                sys.stdout.flush()
                time.sleep(1)

if test == 1:
    os.system('echo msgbox "目前进度为测验，请自己动手吧 ：）",vbokonly+48,"消息" > a.vbs')
    os.system('wscript.exe /nologo a.vbs')
    os.system('del a.vbs')

print("程序结束")
os.system("pause")
