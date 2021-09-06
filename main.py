import asyncio
import os
import bs4
import lxml
import json
import aiohttp

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # 加上这一行

file_dir = r"D:\Game\setu\pixiv\datasets"
file_dirs = r"E:\pythonProject\work\pics"

url = ""

async def fetch(session, url, proxy = None, headers=None):
    async with session.get(url, proxy=proxy,headers=headers) as response:
        return await response.text()

async def fetch2(session, url, proxy = None, headers=None):
    async with session.get(url,proxy=proxy,headers=headers) as response:
        return await response.read()

def analyze(text: str) -> str:
    soup = bs4.BeautifulSoup(text, "lxml")
    mylist = soup.find_all('meta')
    for i in mylist:
        if i.get("content"):
            try:
                data1 = json.loads(i.get("content"))
                for j in data1['illust']:
                    data2 = data1['illust'][j]
                    data3 = {}
                    data3['id'] = data2['id']
                    data3['title'] = data2['title']
                    data3['uploadDate'] = data2['uploadDate']
                    data3['urls'] = data2['urls']
                    data3['author'] = data2['userName']
                    data3['author_id'] = data2['userId']
                    data3['restrict'] = data2['restrict']
                    data3['xRestrict'] = data2['xRestrict'] #0无限制 1R-18
                    data3['pages'] = data2['pageCount']
                    data3['type'] =  data2['illustType'] #0普通 2动图
                    data3['sl'] = data2['sl']
                    data3['tags'] = []
                    #myreturn = data3['urls']['original']
                    for k in data2['tags']['tags']:
                        # print(k)
                        if 'translation' in k:
                            data3['tags'].append({'tag': k['tag'], 'translation': k['translation']})
                        else:
                            data3['tags'].append({"tag": k["tag"]})
                    break
            except:
                pass
    return data3

# def operate(file_name: str):
#     global url
#     with open(file_name, "r", encoding="utf-8") as f:
#         analyze(f.read())

# def get_all(cwd: str) -> list:
#     result = []
#     get_dir = os.listdir(cwd)
#     for i in get_dir:
#         sub_dir = os.path.join(cwd,i)
#         if os.path.isdir(sub_dir):
#             get_all(sub_dir)
#         else:
#             result.append(i)
#     return result
#
# def get_html(mode: int= -1):
#     html_list = get_all(os.path.join(file_dir, 'html'))
#     for i in range(len(html_list)):
#         if i == mode:
#             break
#         operate(os.path.join(file_dir, 'html', html_list[i]))
#         os.remove(os.path.join(file_dir, 'html', html_list[i]))
#     print(html_list)

async def Gethttp(url,cookie,download):
    proxy = 'http://127.0.0.1:7890'
    headers = {
        ':authority': 'i.pximg.net',
        ':method': 'GET',
        ':path': '/img-original/img/2021/08/05/11/54/01/91739274_p0.jpg',
        ':scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://www.pixiv.net/',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67'
    }
    headers2={
        ':authority': 'www.pixiv.net',
        ':method': 'GET',
        ':path': '/ajax/user/17591461/profile/all?lang=zh',
        ':scheme': 'https',
        'accept': 'application/json',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'cookie': cookie,
        'pragma': 'no-cache',
        'referer': 'https://www.pixiv.net/users/17591461/illustrations',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
        'x-user-id': '70504062'
    }
    data_all = {"normal":{},"r18":{}}
    author = ""
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url, proxy=proxy, headers=headers2)
        dic = json.loads(html)
        works = dic['body']["illusts"]
        for pid in works:
            print('检测到作品pid：%s' % pid)
            url = 'https://www.pixiv.net/artworks/%s' % pid
            #对单部作品分析
            html = await fetch(session, url, proxy=proxy, headers=headers)
            data = analyze(html)
            author = data['author_id']
            if data['xRestrict']:
                data_all['r18'][pid] = data
            else:
                data_all['normal'][pid] = data
            urls = data['urls']['original']
            url2, _= os.path.split(urls)
            #print(url2)
            q, fullname = os.path.split(urls[19:])
            #下载这个pid作品的所有pages
            if not download:
                continue
            if data['type'] ==2:
                continue
            for i in range(data['pages']):
                name = "%s_p%d.%s" % (data['id'], i, fullname.split('.')[1])
                headers[':path'] = q + '/' + name
                if not os.path.exists(os.path.join(file_dirs, 'image', 'normal', data['author'])):
                    os.makedirs(os.path.join(file_dirs, 'image', 'normal', data['author']))
                if not os.path.exists(os.path.join(file_dirs, 'image', 'R-18', data['author'])):
                    os.makedirs(os.path.join(file_dirs, 'image', 'R-18', data['author']))

                if data['xRestrict']:
                    if not os.path.exists(os.path.join(file_dirs, 'image', 'R-18', data['author'], name)):
                        with open(os.path.join(file_dirs, 'image', 'R-18', data['author'], name), "wb") as qq:
                            print("——————图片%s开始下载——————" % name)
                            image = await fetch2(session, url2 + '/' + name, proxy=proxy, headers=headers)
                            print("——————图片%s下载完成——————" % name)
                            qq.write(image)
                    else:
                        print("图片%s已存在" % name)
                else:
                    if not os.path.exists(os.path.join(file_dirs, 'image', 'normal', data['author'], name)):
                        with open(os.path.join(file_dirs, 'image', 'normal', data["author"], name), "wb") as f:
                            print("——————图片%s开始下载——————" % name)
                            image = await fetch2(session, url2 + '/' + name, proxy=proxy, headers=headers)
                            print("——————图片%s下载完成——————" % name)
                            f.write(image)
                    else:
                        print("图片%s已存在" % name)
    with open(os.path.join(file_dirs, 'works', author + ".txt"), "w", encoding='utf-8') as f:
        f.write(json.dumps(data_all))


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    #
    user_id = '9472577'
    user_id = user_id.strip()
    #user_name = 'pudding'
    api = 'https://www.pixiv.net/ajax/user/%s/profile/all?lang=zh' % user_id
    download = True
    cookie = ''
    cookie = ''
    cookie = ''
    cookie = ''
    cookie = ''
    cookie = ''
    cookie = ''
    cookie = 'first_visit_datetime_pc=2021-08-31+17%3A41%3A59; p_ab_id=4; p_ab_id_2=3; p_ab_d_id=34402486; yuid_b=JFcIEDc; _ga=GA1.2.941841170.1630399323; PHPSESSID=58756695_j3g2IaSymOAljtkbqWpYm9s2Wpp8WlFG; device_token=9ce1dcea8066414b03e501900c052f70; c_type=26; privacy_policy_agreement=0; privacy_policy_notification=0; a_type=0; b_type=1; _im_vid=01FEDNZ17X1YYV3F2DKZ24RY9M; _im_uid.3929=b.e768ad1129a56b98; adr_id=uIxaYBQiFDRzAhDw9bx2fUyw8zPvme9MSHuWDIMUpf0jTzTj; ki_s=; ki_r=; __cf_bm=N72FOLP8CNHkRn1LqMTJ_kAB0A3dAeiWrB0R0QcTiQI-1630756030-0-AUG1vrARj+ORV7WgAUSG607k9AIiW5PV8lLL3qZbDspDJDOjzArCZDnwhEwHvA4zPy/u2SPLuEBvf1F/01vP2bKREMrCQn4Jc5HeVpl5duz6k14r0GsgqWT+ErPiuyZ3GN3DTyOOKC0fi3tGl/xkKKqouNUuklK+QWj3aLraw6c3vXcE8ZLx1294QtqtIiILRg==; login_ever=yes; _gcl_au=1.1.733999351.1630756321; tag_view_ranking=Lt-oEicbBr~jH0uD88V6F~RTJMXD26Ak~tgP8r-gOe_~1m8UkUR-IC~HHAvWENeAu~HnJ0MouDn0~zyKU3Q5L4C~L58xyNakWW~30YRghWWsb~_pwIgrV8TB~rsb55I7upx; ki_t=1630399331798%3B1630756030493%3B1630756884701%3B2%3B15'





    asyncio.run(Gethttp(api, cookie, download))
    #get_html(-1)
    #print(url)

#从all?zhang=zh中获取headers的cookies