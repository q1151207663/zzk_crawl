import json

import requests
import re

from math import floor

from zzk_crawl.insert_zzk_tables import handler_zzk_data
from zzk_crawl.zzk_log import HandlerLog
from zzk_crawl.zzk_prop import Properties


class HandlerZZK(object):
    def  __init__(self,host):
        # session用来保存服务器给我们的cookie
        self.handlerLog = HandlerLog()
        self.session = requests.session()
        # properties文件工具
        self.prop = Properties()

        self.host = host
        self.page_count = self.prop.property['page_count']
        self.room_count = self.prop.property['room_count']
        self.land_count = self.prop.property['land_count']

        self.page_check = 1
        self.room_check = 1
        self.land_check = 1

        # 筛选模板
        self.search_arr = re.compile('homestay_arr = \[(.*)\];')  # 基本信息
        self.search_thumb = re.compile('homestay_thumb = (.*);')  # 图片路径
        self.search_price = re.compile('homestay_min_price_arr = (.*);')  # 价格信息
        self.search_data = re.compile('search_data = \[(.*)\];')  # 详细信息
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
    def start_crawl(self,url,city):
        # 爬取第一页
        response = self.handler_data_first_page(url=url,city=city)
        # 爬取其他页
        self.handler_data_other_page(url=url,response=response,city=city)


    # 爬取第一页的数据(第一页格式特殊)
    def handler_data_first_page(self,url,city):
        # 请求地址
        target_url = url
        # 发送GET请求
        response = self.handler_request(method="GET",url=target_url)

        # 判断是否进入上次爬取的范围
        if not self.check_page_scope():
            # 如果已在范围内则直接return
            return response

        # 从response中筛选我想要的数据
        thumb_dic, dics, price_dic, data_dic = self.format_all_data(response)
        # print("data_dic:%s\ndics:%s\nthumb_dic:%s\nprice_dic:%s"%(data_dic,dics,thumb_dic,price_dic))

        # 爬图片,同时将元信息连同图片一起插入数据库
        self.crawl_thumb(dics=dics,thumb_dic=thumb_dic,city=city,data_dic=data_dic,room_num=0)

        return response


    # 爬取其他页的数据
    def handler_data_other_page(self,url,response,city):
        print("handler_data_other_page")
        # 数据模板
        search_room_num = re.compile('<span class=\'homeNum\' style="color:#F35758;font-size: 20px;">(.*)</span>')
        # 从response中筛选数据 总共有多少家民宿
        room_list = search_room_num.findall(response.text)
        # 将筛选出的数据解析为页数
        page_num,room_num = self.get_page_num(room_list)
        # 根据页数循环请求爬取
        for i in range(page_num):
            # 判断是否进入上次一爬的范围
            if not self.check_page_scope():
                continue
            if i>=page_num-1:
                print('爬取完成')
                return
            # 其他页的url
            other_url = url + '-p' + str(i+1)
            print("other_url:"+other_url)
            # 对新拼接的url发出请求
            response = self.handler_request(method="GET",url=other_url)
            # 对新页的响应进行解析
            thumb_dic,dics,price_dic,data_dic = self.format_all_data(response)

            # print("data_dic:%s\ndics:%s\nthumb_dic:%s\nprice_dic:%s" % (data_dic, dics, thumb_dic, price_dic))
            self.crawl_thumb(dics,thumb_dic=thumb_dic,city=city,data_dic=data_dic,room_num=room_num)


    # 过滤并解析数据
    def filter_format(self,search_pattern,response,isdics):
        homestay_list = search_pattern.findall(response.text)
        # 数据是列表嵌套字典
        if isdics:
            dics = self.format_homestay_arr(homestay_list,search_pattern)
            return dics

        # eval无法解析 null, true, false之类的数据
        temp_str = str(homestay_list[0])
        clean_str = temp_str.replace('false', '0').replace('true', '1').replace('null','')
        dics = json.loads(clean_str)
        return dics


    # 爬取房间展示图
    def crawl_thumb(self,dics,thumb_dic,city,data_dic,room_num):
        # 计算当前页
        temp_page = self.page_count
        # 存储本地图片路径
        room_pic_paths = []
        land_pic_paths = []
        print("正在爬第【%s】页的房间展示图" % temp_page)
        # 再次发送GET请求，请求图片
        for i in range(len(dics)):
            id = dics[i]['id']
            thumb_url = thumb_dic[str(id)]
            thumb_url = str(thumb_url).replace("\\", "")
            response = self.session.get(url=thumb_url)
            data = response.content
            # 爬取的房间图片在本地存放的路径
            room_pic_path = 'D:\serverUploadTemp\crawl_repository\%s_%s_page_%s_nums.jpg'%(city,self.page_count,self.room_count)
            room_pic_paths.append(room_pic_path)
            # 防止重复爬取  房间数
            if int(self.room_check) < int(self.room_count):
                self.room_check = int(self.room_check) + 1
                print("检测重复展示图，跳过...index:%d"%i)
                continue
            with open(room_pic_path, 'wb') as fb:
                fb.write(data)
            if str(room_num) != '0':
                percentage = str(( (int(self.page_count)-1)*50 + int(self.room_count)+int(self.land_count))/ int(room_num)*2)
            else:
                percentage = '未知...'
            print('第【%s】张展示图爬取成功！爬取进度【%s】' % (self.room_count,percentage))
            # 在配置文件中更新图片序号
            self.room_count_update()


        print("第【%s】页房间展示图爬取完毕，开始爬第【%s】页的房东照片" % (temp_page,temp_page))
        for i in range(len(data_dic)):
            land_pic_url = data_dic[i]['user_photo']
            response = self.session.get(land_pic_url)
            land_pic_data = response.content
            land_pic_path = 'D:\serverUploadTemp\crawl_repository\%s_%s_page_%s_pic.jpg' % (city,self.page_count, self.land_count)
            land_pic_paths.append(land_pic_path)
            # 防止重复爬取  房间数
            if int(self.land_check) < int(self.land_count):
                self.land_check = int(self.land_check) + 1
                print("检测重复照片，跳过...index:%d"%i)
                continue
            with open(land_pic_path,'wb') as fb:
                fb.write(land_pic_data)
            if str(room_num) != '0':
                percentage = str(( (int(self.page_count)-1) * 25 + int(self.room_count)+int(self.land_count)) / int(room_num)*2)
            else:
                percentage = '未知...'
            print('第【%s】张照片爬取成功！爬取进度【%s】' % (self.land_count,percentage))
            # 在配置文件中更新照片序号
            self.land_count_update()

            # 将数据插入表
            handler_zzk_data.insert_item(data_dic[i],room_pic_paths[i],land_pic_paths[i])

            # 图片序号=25 则页数更新+1 图片数重置为1
            if str(self.room_count)=='26' or str(self.land_count)=='26':
                print(" *********************跳页******************* ")
                # 页数+1
                self.page_count_update()
                # 图片数重置
                self.room_count_reset()
                self.land_count_reset()


    # 页面更新
    def page_count_update(self):
        self.page_check = int(self.page_check) + 1
        self.page_count = int(self.page_count) + 1
        # 每次变化都更新
        self.prop.update_properties(page_count=self.page_count, room_count=self.room_count,land_count=self.land_count)


    # room更新
    def room_count_update(self):
        if int(self.room_check)==25 or int(self.room_count)==25:
            return
        self.room_check = int(self.room_check) + 1
        self.room_count = int(self.room_count) + 1
        # 变化之后及时更新到配置文件
        self.prop.update_properties(page_count=self.page_count, room_count=self.room_count,land_count=self.land_count)


    # land更新
    def land_count_update(self):
        self.land_check = int(self.land_check) +1
        self.land_count = int(self.land_count) +1
        if int(self.land_count)==25 or int(self.land_check)==25:
            return
        self.prop.update_properties(page_count=self.page_count, room_count=self.room_count,land_count=self.land_count)



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
        return page_num,room_num

    # 数据格式format
    def format_homestay_arr(self,homestay_arr_list,search_pattern):
        # 存储民宿元信息的列表，嵌套字典
        dics = []
        homestay_arr_str = "".join(homestay_arr_list)
        if str(search_pattern)==str(self.search_data):
            homestay_arr_str = re.sub('},{"address"', '}**{"address"', homestay_arr_str)
            # 剔除脏数据
            homestay_arr_str = self.delete_dirty_data(homestay_arr_str)
            fm_homestay_arr_list = homestay_arr_str.split('**')
            for dicStr in fm_homestay_arr_list:
                # dic = eval(dicStr)
                try:
                    dic = json.loads(dicStr)
                    dics.append(dic)
                except:
                    self.handlerLog.write_log('%s页，%s号' % (str(self.prop.property['page_count']), str(self.prop.property['room_count'])))
                    self.handlerLog.write_log(log_str='数据异常：\n%s' % str(dicStr))
                    continue
        else:
            # 分割之后少了一个{
            fm_homestay_arr_list = homestay_arr_str.split(",{")
            for dicStr in fm_homestay_arr_list:
                if str.find(dicStr,"{")==-1:
                    dicStr = "{"+dicStr
                try:
                    dic = json.loads(dicStr)
                    dics.append(dic)
                except:
                    print("爬取完成")
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


    # 解析响应中的全部数据
    def format_all_data(self,response):
        thumb_dic = self.filter_format(self.search_thumb, response, isdics=False)
        dics = self.filter_format(self.search_arr, response, isdics=True)
        price_dic = self.filter_format(self.search_price, response, isdics=False)
        data_dic = self.filter_format(self.search_data, response, isdics=True)
        return thumb_dic,dics,price_dic,data_dic


    # 防止重复爬取 页数
    # 页数没有进入范围则返回false
    def check_page_scope(self):
        # 防止重复爬取
        if int(self.page_check) < int(self.page_count):
            # 页数+1
            self.page_check = int(self.page_check) + 1
            return False
        else:
            return True


    # 清除脏数据
    def delete_dirty_data(self,str):
        try:
            str = re.sub(',"min_price_str":"(.+?)","origin_price"',',"min_price_str":"","origin_price"',str)
        except:
            pass
        return str


    # 图片数重置
    def room_count_reset(self):
        self.room_check = 1
        self.prop.reset(self.page_count)
        self.room_count = self.prop.property['room_count']

    # 照片数重置
    def land_count_reset(self):
        self.land_check = 1
        self.prop.reset(self.page_count)
        self.land_count = self.prop.property['land_count']



if __name__ == '__main__':
    file_name = ''

    taiwan = 'taiwan'
    thailand = 'thailand'
    japan = 'japan'
    korea = 'korea'
    china = 'china'


    jp_url = 'http://japan.zizaike.com/search//x5000-o1'
    kr_url = 'http://kr.zizaike.com/search//x5000-o1'
    tl_url = 'http://thailand.zizaike.com/search//x5000-o1'
    zh_url = 'http://zh.zizaike.com/search//x5000-o1'
    tw_url = 'http://taiwan.zizaike.com/search//x5000-o1'

    jp_host = 'japan.zizaike.com'
    kr_host = 'kr.zizaike.com'
    tl_host = 'thailand.zizaike.com'
    zh_host = 'zh.zizaike.com'
    tw_host = 'taiwan.zizaike.com'


    crawl = HandlerZZK(zh_host)
    crawl.start_crawl(url=zh_url,city=china)