import datetime
import json
import multiprocessing
import os
import time

import requests
import re

from math import floor

from create_zzk_tables import ZZKRoomTable, ZZKtables
from insert_zzk_tables import handler_zzk_data
from zzk_log import HandlerLog
from zzk_prop import Properties


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
        self.crawl_thumb(dics,thumb_dic,city,data_dic)

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
        for i in range(int(page_num)):

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
            self.crawl_thumb(dics,thumb_dic=thumb_dic,city=city,data_dic=data_dic)



    def pool_handler_test(self,page_num,i,url,city):
        # 判断是否进入上次一爬的范围
        if not self.check_page_scope():
            return
        if i >= page_num - 1:
            print('爬取完成')
            return
        # 其他页的url
        other_url = url + '-p' + str(i + 1)
        print("other_url:" + other_url)
        # 对新拼接的url发出请求
        response = self.handler_request(method="GET", url=other_url)
        # 对新页的响应进行解析
        thumb_dic, dics, price_dic, data_dic = self.format_all_data(response)

        # print("data_dic:%s\ndics:%s\nthumb_dic:%s\nprice_dic:%s" % (data_dic, dics, thumb_dic, price_dic))
        self.crawl_thumb(dics, thumb_dic=thumb_dic, city=city, data_dic=data_dic)


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
    def crawl_thumb(self,dics,thumb_dic,city,data_dic):
        # 获取当前页
        temp_page = self.page_count
        # 存储本地图片路径
        room_pic_paths = []
        land_pic_paths = []

        print("正在爬第【%s】页的民宿首映图" % temp_page)
        # 循环发送GET请求，请求图片
        for i in range(len(dics)):
            id = dics[i]['id']
            thumb_url = thumb_dic[str(id)]
            thumb_url = str(thumb_url).replace("\\", "")
            # 请求图片
            response = self.session.get(url=thumb_url)
            data = response.content
            # 爬取的房间图片在本地存放的路径
            room_pic_path = 'D:\serverUploadTemp\crawl_repository\%s'%city
            # 路径不存在则创建
            if not os.path.exists(room_pic_path):
                os.makedirs(room_pic_path)
            room_pic_name = room_pic_path+'\%s_page_%s_nums.jpg'%(self.page_count,self.room_count)
            room_pic_paths.append(room_pic_name)
            # 防止重复爬取  房间数
            if os.path.exists(room_pic_name):
                self.room_check = int(self.room_check) + 1
                print("检测重复民宿首映图，跳过...index:%d"%i)
            else:
                with open(room_pic_name, 'wb') as fb:
                    fb.write(data)
                print('第【%s】张民宿首映图爬取成功！' % self.room_count)
            # 在配置文件中更新图片序号
            self.room_count_update()


        print("第【%s】页民宿首映图爬取完毕，开始爬第【%s】页的房东照片" % (temp_page,temp_page))
        for i in range(len(data_dic)):
            land_pic_url = data_dic[i]['user_photo']
            response = self.session.get(land_pic_url)
            land_pic_data = response.content
            land_pic_path = 'D:\serverUploadTemp\crawl_repository\%s'%city
            # 路径不存在则创建
            if not os.path.exists(land_pic_path):
                os.makedirs(land_pic_path)
            land_pic_name = land_pic_path+'\%s_page_%s_pic.jpg' % (self.page_count, self.land_count)
            land_pic_paths.append(land_pic_name)

            # 防止重复爬取
            if os.path.exists(land_pic_name):
                self.land_check = int(self.land_check) + 1
                print("检测改民房东照片已存在，跳过...")
            else:
                with open(land_pic_name,'wb') as fb:
                    fb.write(land_pic_data)
                print('第【%s】个房东照片爬取成功！' % self.land_count)
            # 在配置文件中更新照片序号
            self.land_count_update()


        # 爬取每个民宿的民宿简介等信息  http://%city%.zizaike.com/h/%homestay_id%
        for i in range(len(dics)):
            url = 'http://%s/h/%s' % (self.host, str(dics[i]['id']))
            response = self.session.get(url=url)
            mydata = self.format_mydata(response, city,dics[i]['id'],i)
            # 将数据插入 homestay_table
            handler_zzk_data.insert_homestay_table(data_dic[i],room_pic_paths[i],land_pic_paths[i],dics[i],mydata,city)

            # 爬取该民宿的所有展示图和滚动图并保存在本地，返回本地url
            show_url_list, slider_url_list = self.format_homestary_pic(response, city, dics[i])
            min_length = min(len(show_url_list),len(slider_url_list))
            for j in range(min_length):
                # 将保存在本地的民宿展示图的url插入homestay_pic_table
                handler_zzk_data.insert_homestay_pic_table(dics[i],show_url_list[j],slider_url_list[j])


            # 爬取该民宿下所有的房间信息  这里可能有问题
            room_info_list = data_dic[i]['roomInfoList']
            # 遍历房间列表
            for r in range(len(room_info_list)):
                # 爬取并解析该房间包含的数据
                room_pic_url_list,room_data = self.crawl_roominfo(city,room_info_list[r])
                # 将解析好的数据插入数据库
                handler_zzk_data.insert_room_table(room_info_list[r],dics[i]['id'],room_data)
                # 将保存在本地的图片路径插入数据库
                for p in range(len(room_pic_url_list)):
                    handler_zzk_data.insert_room_pic_table(room_info_list[r]['roomId'],room_pic_url_list[p],room_info_list[r]['title'])


        # 图片序号=25 则页数更新+1 图片数重置为1
        if str(self.room_count)=='25' and str(self.land_count)=='25':
            print(" *********************跳页******************* ")
            # 页数+1
            self.page_count_update()
            # 图片数重置
            self .room_count_reset()
            self.land_count_reset()


    # 爬取民宿下的房间信息
    def crawl_roominfo(self,city,room_info):
        room_data = {}
        room_url = 'http://'+self.host+'/r/'+str(room_info['roomId'])
        room_response = self.session.get(room_url)
        # 房间展示图 https://zh.zizaike.com/r/208642
        room_pic_pattern = re.compile('//img1.zzkcdn.com/(.*)/2000x1500.jpg-homepic800x600.jpg')
        room_pic_urls = room_pic_pattern.findall(room_response.text)
        print("room_pic_urls length:%s"%str(len(room_pic_urls)))
        # 用于保存爬取的房间图片的本地地址
        room_pic_url_list = []
        for i in range(len(room_pic_urls)):
            room_pic_target = 'http://img1.zzkcdn.com/'+room_pic_urls[i]+'/2000x1500.jpg-homepic800x600.jpg'
            room_pic_response = self.session.get(room_pic_target)
            room_pic_data = room_pic_response.content
            room_pic_url = 'D:\serverUploadTemp\crawl_repository\%s\\room'%city
            # 路径不存在则创建
            if not os.path.exists(room_pic_url):
                os.makedirs(room_pic_url)
            room_pic_name = room_pic_url+'\\room_%s_%s.jpg'%(str(room_info['roomId']),str(i+1))
            # 判断该文件是否存在 存在：True  否则False
            if os.path.exists(room_pic_name):
                print('尝试爬取的图片：%s已存在，终止爬取,%s'%(room_pic_url,self.get_now_time()))
                self.handlerLog.write_log('尝试爬取的图片：%s已存在，终止爬取,%s\n'%(room_pic_url,self.get_now_time()))
            else:
                with open(room_pic_name,'wb') as fw:
                    fw.write(room_pic_data)
                # 爬取图片的本地路径保存到列表
                room_pic_url_list.append(room_pic_name)
                print("【%s】的第【%s】张尝试爬取的图片房间展示图爬取成功"%(str(room_info['title']),str(i+1)))

        # 房间首映图
        if room_pic_url_list!=None and len(room_pic_url_list)>0:
            room_data['room_index_pic'] = room_pic_url_list[0]
        else:
            room_data['room_index_pic'] = ''

        print('【%s】的房间展示图爬取完成，开始解析房间面积'%str(room_info['title']))
        room_area_pattern = re.compile('<span>房间面积:(.+?)<')
        room_area = room_area_pattern.findall(room_response.text)
        # 房间面积
        if room_area!=None and len(room_area)>0:
            room_data['room_area'] = room_area[0]
        else:
            room_data['room_area'] = ''

        print('【%s】的房间面积解析完成，开始解析楼层信息'%str(room_info['title']))
        room_floor_pattern = re.compile('<span>楼层:(.+?)<')
        room_floor = room_floor_pattern.findall(room_response.text)
        if room_floor!=None and len(room_floor)>0:
            room_floor_str = str(room_floor[0]).replace(' ','')
            room_floor_str = room_floor_str.replace('\t','')
            room_data['room_floor'] = room_floor_str
        else:
            room_data['room_floor'] = ''

        print('【%s】的房间楼层信息解析完成，开始解析窗户信息'%str(room_info['title']))
        is_window_pattern = re.compile('<span>是否有窗(.*)<')
        is_window = is_window_pattern.findall(room_response.text)
        if is_window!=None and len(is_window)>0:
            is_window_str = str(is_window[0])[1:]
            room_data['is_window'] = is_window_str
        else:
            room_data['is_window'] = ''

        print('【%s】的房间窗户信息解析完成，开始解析电梯信息' % str(room_info['title']))
        is_elevator_pattern = re.compile('<span>电梯:(.+?)</span>')
        is_elevator = is_elevator_pattern.findall(room_response.text)
        if is_elevator!=None and len(is_elevator)>0:
            room_data['room_elevator'] = is_elevator[0]
        else:
            room_data['room_elevator'] = ''

        print('【%s】的房间电梯信息解析完成，开始解析床型信息' % str(room_info['title']))
        chuangxing_pattern = re.compile('<span>房型:(.*)</span>')
        chuangxing = chuangxing_pattern.findall(room_response.text)
        if chuangxing!=None and len(chuangxing)>0:
            room_data['chuangxing'] = chuangxing[0]
        else:
            room_data['chuangxing'] = ''

        print('【%s】的房间床型信息解析完成，开始解析最大入住人数' % str(room_info['title']))
        max_stay_pattern = re.compile('最多入住:([\s\d]*)人')
        max_stay = max_stay_pattern.findall(room_response.text)
        if max_stay!=None and len(max_stay)>0:
            room_data['max_stay'] = max_stay
        else:
            room_data['max_stay'] = ''


        print('开始解析【%s】房间的基础设施信息'%room_info['title'])
        # python没有switch
        switch = {'电视机':'is_tv','电冰箱':'is_refrigerator','24小时热水':'is_hot_water_24',
                  '免费停车位':'is_free_parking','可以吸烟':'is_smoking','空调':'is_air',
                  '热水壶':'is_hot_kettle','厨房':'is_kitchen','淋浴':'is_shower','热水浴缸':'is_bathtub',
                  '可以携带宠物':'is_carrypet','毛巾':'is_towel','拖鞋':'is_slipper','一次性盥洗用品':'is_disposable',
                  '洗衣机':'is_washer','代订门票':'is_hlep_ticket','代订包车':'is_hlep_car','可接待家庭/孩子':'is_reception_child'}
        yes_service_pattern = re.compile('<li class="setting_yes">(.*)<')
        yes_service = yes_service_pattern.findall(room_response.text)
        for i in range(len(yes_service)):
            key = switch[str(yes_service[i])]
            room_data[key] = '1'

        no_service_pattern = re.compile('<li class="setting_no">(.*)<')
        no_service = no_service_pattern.findall(room_response.text)
        for i in range(len(no_service)):
            key = switch[str(no_service[i])]
            room_data[key] = '0'
        print("【%s】的全部信息爬取、解析完成"%room_info['title'])
        return room_pic_url_list,room_data


    def get_now_time(self):
        return time.strftime('%Y.%m.%d %H:%M:%S ', time.localtime(time.time()))


    # 解析homestay_pic网络地址，发出请求写入本地，并返回在本地路径
    def format_homestary_pic(self,response,city,homestays):
        # 展示图
        show_pic_url_pattern = re.compile('https://img1.zzkcdn.com/(.*)/2000x1500.jpg-homepic800x600.jpg')
        show_pic_url = show_pic_url_pattern.findall(response.text)
        show_url_list = []
        # 循环获取各个展示图的url
        for i in range(len(show_pic_url)):
            show_temp_url = 'https://img1.zzkcdn.com/'+show_pic_url[i]+'/2000x1500.jpg-homepic800x600.jpg'
            print(show_temp_url)
            requests.packages.urllib3.disable_warnings()
            show_response = self.session.get(show_temp_url,verify=False)
            show_data = show_response.content
            show_url = 'D:\serverUploadTemp\crawl_repository\%s\show'%city
            if not os.path.exists(show_url):
                os.makedirs(show_url)
            show_name = show_url+'\show_%s_%s.jpg'%(str(homestays['id']),str(i+1))
            if os.path.exists(show_name):
                print('尝试爬取的图片：%s已存在，终止爬取,%s' % (show_name, self.get_now_time()))
                self.handlerLog.write_log('尝试爬取的图片：%s已存在，终止爬取,%s\n' % (show_name, self.get_now_time()))
            else:
                with open(show_name,'wb') as fw:
                    fw.write(show_data)
                print("【%s】民宿的第【%s】张展示图爬取成功" % (homestays['name'], str(i + 1)))
            # 将url存入列表
            show_url_list.append(show_name)
        print('【%s】民宿的展示图全部爬取完成'%homestays['name'])

        # 下方滚动图
        slider_pic_url_pattern = re.compile('https://img1.zzkcdn.com/(.*)/2000x1500.jpg-roomthumb.jpg')
        slider_pic_url = slider_pic_url_pattern.findall(response.text)
        slider_url_list = []
        # 循环获取各个滚动图的url
        for i in range(len(slider_pic_url)):
            slider_temp_url = 'https://img1.zzkcdn.com/'+slider_pic_url[i]+'/2000x1500.jpg-roomthumb.jpg'
            requests.packages.urllib3.disable_warnings()
            slider_response = self.session.get(slider_temp_url,verify=False)
            slider_data = slider_response.content
            slider_url = 'D:\serverUploadTemp\crawl_repository\%s\slider'%city
            if not os.path.exists(slider_url):
                os.makedirs(slider_url)
            slider_name = slider_url+'\slider_%s_%s.jpg'%(str(homestays['id']),str(i+1))
            if os.path.exists(slider_name):
                print('尝试爬取的图片：%s已存在，终止爬取,%s' % (slider_name, self.get_now_time()))
                self.handlerLog.write_log('尝试爬取的图片：%s已存在，终止爬取,%s\n' % (slider_name, self.get_now_time()))
            else:
                with open(slider_name,'wb') as fw:
                    fw.write(slider_data)
                print("【%s】的第【%s】张滚动图爬取成功" % (homestays['name'], str(i + 1)))
            slider_url_list.append(slider_name)
        print('【%s】民宿的滚动图全部爬取完成'%homestays['name'])

        return show_url_list,slider_url_list




    # 从响应中解析homestay_table表需要的剩下几个字段数据
    def format_mydata(self,response,city,homestay_id,i):
        mydata = {}
        txt_target = response.text
        # 注册时间
        reg_time_pattern = re.compile('float-right">注册时间 (.+?)</p>')
        reg_time = reg_time_pattern.findall(txt_target)
        if reg_time!=None and len(reg_time)>0:
            mydata['reg_time']=reg_time[0]
        else:
            mydata['reg_time'] = ''

        # 取消预订天数 匹配到了2个元素
        refund_days_pattern = re.compile('>前(.+?)天<')
        refund_days = refund_days_pattern.findall(txt_target)
        if refund_days!=None and len(refund_days)>0:
            full_refund_days = refund_days[0]
            mydata['full_refund_days'] = full_refund_days
            # 人算不如天算。。
            if len(refund_days)>1:
                not_refund_days = refund_days[1]
                mydata['not_refund_days'] = not_refund_days
            else:
                mydata['not_refund_days'] = ''
        else:
            mydata['full_refund_days'] = ''
            mydata['not_refund_days'] = ''

        # 取消预订扣款百分比
        refund_cut_pattern = re.compile('refund-view-label">退款 (.+?)%</label>')
        refund_cut = refund_cut_pattern.findall(txt_target)
        if refund_cut!=None and len(refund_cut)>0:
            mydata['refund_cut'] = refund_cut[0]
        else:
            mydata['refund_cut'] = ''

        # 注意事项
        terms_pattern = re.compile('<span class="origin">(.*)</span>')
        terms = terms_pattern.findall(txt_target)
        if terms!=None and len(terms)>0:
            mydata['terms'] = terms[0]
        else:
            mydata['terms'] = ''

        # 交通路线文字描述
        tfc_txt_pattern = re.compile('<p class="origin">(.*)</p>')
        tfc_txt = tfc_txt_pattern.findall(txt_target)
        if tfc_txt!=None and len(tfc_txt)>0:
            mydata['tfc_txt'] = tfc_txt[0]
        else:
            mydata['tfc_txt'] = ''

        # 民宿简介
        homestay_desc_pattern = re.compile('<div class="origin">(.*)<br/></div>')
        homestay_desc = homestay_desc_pattern.findall(txt_target)
        if homestay_desc!=None and len(homestay_desc)>0:
            mydata['homestay_desc'] = homestay_desc[0]
        else:
            mydata['homestay_desc'] = ''

        # 交通路线图url
        tfc_pic_pattern = re.compile('<img src="(.*)original.jpg"/>')
        tfc_pic_url = tfc_pic_pattern.findall(txt_target)
        if tfc_pic_url!=None and len(tfc_pic_url)>0:
            temp_url = str(tfc_pic_url[0])+'original.jpg'
            requests.packages.urllib3.disable_warnings()
            temp_response = self.session.get(temp_url,verify=False)
            traffic_path = 'D:\serverUploadTemp\crawl_repository\%s\\traffic'%city
            if not os.path.exists(traffic_path):
                os.makedirs(traffic_path)
            traffic_name = traffic_path+'\logo_%s_%s.jpg'% (homestay_id, str(i + 1))
            with open(traffic_name,'wb') as fw:
                fw.write(temp_response.content)
            mydata['tfc_pic_url'] = traffic_name
        else:
            mydata['tfc_pic_url'] = ''


        # 民宿logo图url
        if city=='china' or city=='thailand':
            homestay_logo_pattern = re.compile('<img src="https://pages.zizaike.com/a/newavatar/(.*)"/>')
            homestay_logo_url = homestay_logo_pattern.findall(txt_target)
            mydata['homestay_logo_url'] = ''
            if homestay_logo_url!=None and len(homestay_logo_url)>0:
                homestay_logo_url = 'https://pages.zizaike.com/a/newavatar/'+homestay_logo_url[0]
                # 爬取图片保存到本地并返回本地url
                logo_path = self.imreallynotword(homestay_logo_url,city,homestay_id,i)
                mydata['homestay_logo_url'] = logo_path
            else:
                homestay_logo_pattern = re.compile('https://img1.zzkcdn.com/(.*)/2000x1500.jpg-userphoto.jpg')
                homestay_logo_url = homestay_logo_pattern.findall(txt_target)
                if homestay_logo_url != None and len(homestay_logo_url) > 0:
                    homestay_logo_url = 'https://img1.zzkcdn.com/' + homestay_logo_url[0] + '/2000x1500.jpg-userphoto.jpg'
                    logo_path = self.imreallynotword(homestay_logo_url, city, homestay_id, i)
                    mydata['homestay_logo_url'] = logo_path
                else:
                    mydata['homestay_logo_url'] = ''
        else:
            homestay_logo_pattern = re.compile('https://img1.zzkcdn.com/(.*)/2000x1500.jpg-userphoto.jpg')
            homestay_logo_url = homestay_logo_pattern.findall(txt_target)
            if homestay_logo_url!=None and len(homestay_logo_url)>0:
                homestay_logo_url = 'https://img1.zzkcdn.com/'+homestay_logo_url[0]+'/2000x1500.jpg-userphoto.jpg'
                logo_path = self.imreallynotword(homestay_logo_url, city, homestay_id, i)
                mydata['homestay_logo_url'] = logo_path
            else:
                mydata['homestay_logo_url'] = ''


        return mydata



    # 帮助mydata爬取logo的方法
    def imreallynotword(self,logo_url,city,homestay_id,i):
        requests.packages.urllib3.disable_warnings()
        logo_response = self.session.get(logo_url,verify=False)
        logo_path = 'D:\serverUploadTemp\crawl_repository\%s\logo'%city
        if not os.path.exists(logo_path):
            os.makedirs(logo_path)

        logo_name = logo_path+'\logo_%s_%s.jpg' % ( homestay_id, str(i + 1))
        # 爬取文件存在则输出到日志，文件不存在则输出到本地
        self.imgexist_out_pic(logo_name, logo_response)
        return logo_name


    # 检查图片是否存在，如果存在则输出到日志，不存在则序列化到本地
    def imgexist_out_pic(self,pic_path,pic_response):
        if os.path.exists(pic_path):
            print('尝试爬取的图片：%s已存在，终止爬取,%s' % (pic_path, self.get_now_time()))
            self.handlerLog.write_log('尝试爬取的图片：%s已存在，终止爬取,%s\n' % (pic_path, self.get_now_time()))
        else:
            with open(pic_path, 'wb') as fw:
                fw.write(pic_response.content)

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
        if int(self.land_count)==25 or int(self.land_check)==25:
            return
        self.land_check = int(self.land_check) +1
        self.land_count = int(self.land_count) +1
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
            print('当前页：【%s】数据已经爬取，跳过...'%str(self.page_check))
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
        self.room_count = 1

    # 照片数重置
    def land_count_reset(self):
        self.land_check = 1
        self.prop.reset(self.page_count)
        self.land_count = 1



if __name__ == '__main__':
    file_name = ''

    prop = Properties()

    myswitch = {
        'japan': {'url': 'http://japan.zizaike.com/search//x5000-o1', 'host': 'japan.zizaike.com'},
        'taiwan': {'url': 'http://taiwan.zizaike.com/search//x5000-o1', 'host': 'taiwan.zizaike.com'},
        'china': {'url': 'http://zh.zizaike.com/search//x5000-o1', 'host': 'zh.zizaike.com'},
        'thailand': {'url': 'http://thailand.zizaike.com/search//x5000-o1', 'host': 'thailand.zizaike.com'},
        'korea': {'url': 'http://kr.zizaike.com/search//x5000-o1', 'host': 'kr.zizaike.com'}
    }
    country = prop.property['country']
    url = myswitch[country]['url']
    host = myswitch[country]['host']


    crawl = HandlerZZK(host)
    crawl.start_crawl(url,country)


