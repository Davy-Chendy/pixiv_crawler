"""
增量式爬虫
爬取pixiv
by FengLiu
"""

import os
import time
import aiohttp
import asyncio
import requests
from math import ceil

def print_l(msg):
    """
    自定义打印 可以随便删改
    :param msg:信息
    """
    print("[%s] %s"%(time.strftime("%H:%M:%S", time.localtime()),msg) )

GET_AUTHOR_ID_LIST_API = "https://www.pixiv.net/ajax/user"
GET_LIST_API = "https://www.pixiv.net/ajax/tags/frequent/illust"
VILIPIX_GET_LIST_API = "https://www.vilipix.com/api/illust"
GET_ORIGINAI_JPG_API = "https://i.pximg.net/img-original/img/"
VILIPIX_GET_ORIGINAI_JPG_API = "http://img3.vilipix.com/picture/pages/original/"

class pixiv:

    def __init__(self,download_path ,pixiv_db,headers):
        """
        初始化pixiv模块

        :param download_path:下载目录
        :param pixiv_db:一个db对象 用于读存储图片id
        :param headers:请求头
        """

        if not os.path.exists(download_path):
            os.makedirs(download_path)

        self.__pixiv_db = pixiv_db
        self.__download_path = download_path
        self.__headers = headers

        self.__all_jpg_list = {
            "len":0,
            "all_jpg_list": [],
        }

    def __save_jpg_id(self,id,get_in):
        """
        将该图片id存入db文件

        :param id:图片id
        :param get_in:来源
        """
        spl = "INSERT INTO save_pixiv_jpg (id,get_in,time) VALUES ('%s','%s',%s);"%(id,get_in,
                                                                                    time.strftime("%Y%m%d", time.localtime()))
        self.__pixiv_db.execute(spl)
        self.__pixiv_db.commit()

    def __search_jpg_id(self,id):
        """
        从db文件中查找该图片id

        :param id:图片id
        :return:存在返回 False 不存在返回True
        """
        spl = "select * FROM save_pixiv_jpg WHERE id = %s;"%id
        data = self.__pixiv_db.execute(spl)
        if not data.fetchall():
            return True

        return False

    def __link_api(self,url,data=None):
        """
        请求接口返回json
        """
        res = requests.get(url=url,data=data,headers=self.__headers)
        return res.json()

    def __pixiv_get_id_list(self,mode,date,get_len):
        """
        获取图片id 计算请求图片详细数据接口

        :return:返回图片详细数据接口列表
        """
        url,jpg_list,jpg_id_yi_list,http_ = "",[],[],""
        if mode == "author":
            url = GET_AUTHOR_ID_LIST_API +"/%s/profile/all?lang=zh"%date
            http_ = "https://www.pixiv.net/ajax/user/%s/profile/illusts?"%date
        data = self.__link_api(url)
        jpg_id_list = data['body']['illusts'].keys()

        for jpg_id in jpg_id_list:
            if self.__search_jpg_id(jpg_id):
                jpg_list.append(jpg_id)

        jpg_id_len = len(jpg_list)
        yi = ceil(jpg_id_len / get_len)
        for i in range(0, yi):
            http = http_
            if not jpg_id_len < 0:
                for jpg_id in jpg_list[get_len * i:get_len * (i + 1)]:
                    http += "ids%5B%5D=" + jpg_id + "&"
                jpg_id_yi_list.append(http + "work_category=illustManga&is_first_page=0&lang=zh")
                jpg_id_len -= get_len
            else:
                jpg_id_len = -jpg_id_len
                for jpg_id in jpg_list[get_len * i:get_len * i + jpg_id_len]:
                    http += "ids%5B%5D=" + jpg_id + "&"
                jpg_id_yi_list.append(http + "work_category=illustManga&is_first_page=0&lang=zh")

        return jpg_id_yi_list

    def pixiv_get_list(self,mode,date,get_len=20):
        """
        需要科学上网 获取pixiv指定作者所有作品
        获取到的图片url列表存储于self.__all_jpg_list

        :param mode:author
        :param date:作者id
        :param get_len:图片详细数据接口一次获取多少图片 默认20
        """
        jpg_list = []
        jpg_id_yi_list = self.__pixiv_get_id_list(mode,date,get_len)
        for jpg_id_yi in jpg_id_yi_list:
            get_len_ = 0
            data = self.__link_api(jpg_id_yi)['body']['works']
            for jpg in data:
                get_len_ += 1
                jpg_list.append(
                    GET_ORIGINAI_JPG_API + data[jpg]["url"].split("/", 7)[-1].replace("_custom1200", "").replace("_square1200",""))

            print_l("成功获取%s张图片url!!!" % get_len_)

        self.__all_jpg_list["len"] += len(jpg_list)
        self.__all_jpg_list["all_jpg_list"].append(["%s_%s" % (mode, date), jpg_list])

    def vilipix_get_list(self,mode,date):
        """
        基于国内pixiv 不用代理不用会员获取日周月榜单
        获取到的图片url列表存储于self.__all_jpg_list

        :param mode:日daily 周weekly 月monthly
        :param date:更新日期
        """
        jpg_list,end,get_len = [],0,0
        while True:
            data = self.__link_api(VILIPIX_GET_LIST_API+"?mode=%s&date=%s&limit=%s&offset=%s"%(
                mode,date,30,end
            ))

            for jpg in data['rows']:
                if self.__search_jpg_id(jpg['id']):
                    get_len += 1
                    jpg_list.append(VILIPIX_GET_ORIGINAI_JPG_API+jpg["regular_url"].split("/",6)[-1].replace("_master1200",""))

            print_l("成功获取%s张图片url!!!"%get_len)
            if not len(data['rows']) == 30:
                break

            end += 30
        self.__all_jpg_list["len"] += len(jpg_list)
        self.__all_jpg_list["all_jpg_list"].append(["%s_%s"%(mode,date),jpg_list])

    def __download_jpg(self,jpg_list,download_path):
        """
        下载图片url列表

        :param jpg_list:图片url列表
        :param download_path:下载路径
        """
        for jpg in jpg_list[1]:
            res = requests.get(url=jpg, headers=self.__headers)
            jpg_name = jpg.split("/")[-1]

            if res.status_code == 404:
                print_l("%s 404 尝试png..." % jpg_name)
                jpg_name = jpg_name.replace('.jpg', '.png')
                res = requests.get(url=jpg.replace('.jpg', '.png'), headers=self.__headers)

            with open(download_path + "/" + jpg_name, "wb") as jpg:
                jpg.write(res.content)

            self.__all_jpg_list["len"] -= 1
            self.__save_jpg_id(jpg_name.split("_",1)[0],jpg_list[0])
            print_l("%s 下载完成! 剩余目标数%s" % (jpg_name, self.__all_jpg_list["len"]))

    async def __async_download_jpg(self,jpg_list,download_path,limit):
        """
        基于asyncio的异步下载图片
        半成品 加上代理ip才能正常使用 直接用爬到一半会请求空图片

        :param jpg_list:图片url列表
        :param download_path:下载路径
        :param limit:最多任务数 默认10
        """
        url_list = []
        conn = aiohttp.TCPConnector(limit=limit)

        async def download_jpg(session, url):
            async with session.get(url,headers=self.__headers,verify_ssl=False) as res:
                jpg_name = str(res.url).split("/")[-1]
                if not res.status == 404:
                    content = await res.content.read()
                    with open(download_path + "/" + jpg_name, "wb") as jpg:
                        jpg.write(content)
                    self.__all_jpg_list["len"] -= 1
                    self.__save_jpg_id(jpg_name.split("_")[0],jpg_list[0])
                    print_l("%s 下载完成! 剩余目标数%s" % (jpg_name, self.__all_jpg_list["len"]))
                elif res.status == 404:
                    print_l("%s 404 尝试png..." % jpg_name)
                    url_list.append(str(res.url).replace("jpg", "png"))

        async with aiohttp.ClientSession(connector=conn) as session:
            tasks = [asyncio.create_task(download_jpg(session, jpg)) for jpg in jpg_list[1]]
            await asyncio.wait(tasks)

            if not url_list == []:
                await self.__async_download_jpg([jpg_list[0],url_list], download_path, limit=limit)

    def download(self,async_http = False,limit=10):
        """
        下载self.__all_jpg_list中图片url列表

        :param async_http:True开启异步请求
        :param limit:异步最多任务数 默认10
        """
        print_l("开始下载... 目标数%s"%self.__all_jpg_list["len"])
        for jpg_list in self.__all_jpg_list["all_jpg_list"]:
            download_path = self.__download_path + "/" + jpg_list[0]
            if not os.path.exists(download_path):
                os.makedirs(download_path)

            if not jpg_list[1] == []:
                if async_http:
                    try:
                        asyncio.run(self.__async_download_jpg(jpg_list, download_path, limit=limit))
                    except RuntimeError:
                        pass
                else:
                    self.__download_jpg(jpg_list, download_path)
        print_l("全部下载完成 下载任务结束!!!")
        #
        self.__all_jpg_list = {
            "len": 0,
            "all_jpg_list": [],
        }

    def delete_all_jpg_list(self):
        """
        清空self.__all_jpg_list 生成一个空的
        """
        self.__all_jpg_list = {
            "len": 0,
            "all_jpg_list": [],
        }

    def set_headers(self,headers):
        """
        设置请求头
        :param headers:请求头
        """
        self.__headers = headers

