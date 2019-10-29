import time

import requests
import re

from math import floor

from zzk_crawl.zzk_prop import Properties


class HandlerZZK(object):
    def  __init__(self,host,file_name):
        # session用来保存服务器给我们的cookie
        self.session = requests.session()
        # properties文件工具
        self.prop = Properties(file_name)

        self.host = host
        self.page_count = self.prop.property['page_count']
        self.room_count = self.prop.property['room_count']
        # self.thumb_dics = {}
        # 筛选模板
        self.search_arr = re.compile('homestay_arr = \[(.*)\];')  # 基本信息
        self.search_thumb = re.compile('homestay_thumb = (.*);')  # 图片路径
        self.search_price = re.compile('homestay_min_price_arr = (.*);')  # 价格信息
        # 定义请求头
        self.header = {
            "Host": self.host,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer":"http://kr.zizaike.com/search//x5000-o1-p1",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.9"
        }

    # 开始爬取
    def start_crawl(self,url):
        # 爬取第一页
        response = self.handler_data_first_page(url=url)
        # 爬取其他页
        self.handler_data_other_page(url=url,response=response)

        # print(dics)

    # 爬取第一页的数据(第一页格式特殊)
    def handler_data_first_page(self,url):
        # 请求地址
        target_url = url
        # 发送GET请求
        response = self.handler_request(method="GET",url=target_url)
        # 从response中筛选我想要的数据
        homestay_arr_list = self.search_arr.findall(response.text)
        # 图片数据
        homestay_thumb_list = self.search_thumb.findall(response.text)
        # 格式化format 嵌套字典的列表
        # dics = self.format_homestay_arr(homestay_arr_list)
        dics = eval(homestay_arr_list[0])
        thumb_dic = eval(homestay_thumb_list[0])
        # 爬图片
        self.crawl_thumb(dics=dics,thumb_dic=thumb_dic)
        
        return response

    # 爬取其他页的数据
    def handler_data_other_page(self,url,response):
        # 数据模板
        search_room_num = re.compile('<span class=\'homeNum\' style="color:#F35758;font-size: 20px;">(.*)</span>')
        # 从response中筛选数据
        room_list = search_room_num.findall(response.text)
        thumb_dic = self.filter_format(search_pattern=self.search_thumb,response=response)
        # 筛选出的数据解析为页数
        page_num = self.get_page_num(room_list)
        for i in range(page_num):
            # 达到最后一页结束
            if i>=page_num:
                break
            # 其他页的url
            other_url = url + '-p' + str(i+1)
            # print("other_url:%s"%other_url)

            response = self.handler_request(method="GET",url=other_url)

            thumb_dic = self.filter_format(search_pattern=self.search_thumb,response=response)
            dics = self.filter_format(search_pattern=self.search_arr,response=response)
            self.crawl_thumb(dics,thumb_dic=thumb_dic)


    # 过滤并解析数据
    def filter_format(self,search_pattern,response):
        homestay_list = self.search_pattern.findall(response.text)
        dic = eval(homestay_list[0])


    def crawl_thumb(self,dics,thumb_dic):
        print("正在爬第【%s】页的图片"%str(self.page_count))
        self.page_count = int(self.page_count)+1
        # 每次变化都更新
        self.prop.update_properties(page_count=self.page_count,room_count=self.room_count)
        # 再次发送GET请求，请求图片
        for i in range(len(dics)):
            print('目前是第【%s】张'%self.room_count)
            self.room_count = int(self.room_count)+1
            # 变化之后及时更新到配置文件
            self.prop.update_properties(page_count=self.page_count,room_count=self.room_count)
            id = dics[i]['id']
            thumb_url = thumb_dic[str(id)]
            thumb_url = str(thumb_url).replace("\\", "")
            time_name = time.strftime('%Y%m%d %H%M%S',time.localtime(time.time()))
            response = self.handler_request(method='GET', url=thumb_url)
            data = response.content
            with open('D:\serverUploadTemp\crawl_repository\%s.jpg' % time_name, 'wb') as fb:
                fb.write(data)


    # 返回url对应的国家总共有多少页数据
    def get_page_num(self,room_list):
        # 列表转字符串
        page_room_str = "".join(room_list)
        # 对字符串格式再处理
        if len(page_room_str) > 3:
            page_room_str = page_room_str.replace(",", "")
        # 字符串转数值
        room_num = int(page_room_str)
        page_num = float(room_num/25) if room_num % 25 == 0 else floor(room_num / 25) + 1
        return page_num

    # 数据格式format
    def format_homestay_arr(self,homestay_arr_list):
        homestay_arr_str = "".join(homestay_arr_list)
        homestay_arr_str = homestay_arr_str.replace("},{", "}*{")
        fm_homestay_arr_list = homestay_arr_str.split("*")

        # 存储民宿元信息的列表，嵌套字典
        dics=[]
        for dicStr in fm_homestay_arr_list:
            try:
                dic = eval(dicStr)
                dics.append(dic)
            except:
                pass
        return dics


    # method：请求方式
    # url：请求地址
    # data：post请求的请求体
    def handler_request(self,method,url,data=None):
        if method=="GET":
            response = self.session.get(url=url,headers=self.header)
        elif method=="POST":
            response = self.session.post(url=url,headers=self.header,data=data)
        return response

if __name__ == '__main__':
    file_name = 'zzk_crawl.properties'

    jp_url = 'http://japan.zizaike.com/search//x5000-o1'
    jp_host = 'japan.zizaike.com'

    kr_url = 'http://kr.zizaike.com/search//x5000-o1'
    kr_host = 'kr.zizaike.com'
    crawl = HandlerZZK(jp_host,file_name)
    crawl.start_crawl(url=jp_url)