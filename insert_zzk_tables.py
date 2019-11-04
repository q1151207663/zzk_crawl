import time

from zzk_crawl.create_zzk_tables import ZZKtables, ZZKHomestayPicTable, ZZKRoomTable, ZZKRoomPicTable
from zzk_crawl.create_zzk_tables import Session
from zzk_crawl.zzk_log import HandlerLog
from zzk_crawl.zzk_prop import Properties


class HandlerZZKData(object):
    def __init__(self):
        self.mysql_session = Session()
        self.prop = Properties()
        self.handlerLog = HandlerLog()


    # 民宿房间图片表插入一条数据
    def insert_room_pic_table(self,room_id,room_pic_url,room_name):
        format_item = ZZKRoomPicTable(
            room_id = room_id,
            room_show_pic = room_pic_url
        )
        check_result = self.mysql_session.query(ZZKRoomPicTable).filter(ZZKRoomPicTable.room_show_pic==room_pic_url).first()
        if not check_result:
            self.mysql_session.add(format_item)
            self.mysql_session.commit()
            print("id:【%s】,room_name:【%s】房间的图片已插入数据库" % (room_id, room_name))
        else:
            message_tip = "%s，房间图片url：%s图片在room_pic_table表中已存在，终止插入" % (self.get_now_time(),room_pic_url)
            print(message_tip)
            self.handlerLog.write_log(message_tip+'\n')



    # 民宿的房间表插入一条数据
    def insert_room_table(self,room_info,homestay_id,room_data):

        try:
            format_item = ZZKRoomTable(
                room_id=room_info['roomId'],
                room_title=room_info['title'],
                homestay_id=homestay_id,
                breakfast=room_info['breakfast'],
                support_speed=room_info['isSpeed'],
                room_price=room_info['price'],
                room_model=room_info['roomModel'],
                room_wifi=room_info['wifiI'],

                room_elevator=room_data['room_elevator'],
                max_stay=room_data['max_stay'],
                chuangxing=room_data['chuangxing'],
                room_index_pic=room_data['room_index_pic'],
                room_area=room_data['room_area'],
                room_floor=room_data['room_floor'],
                is_window=room_data['is_window'],

                is_tv=room_data['is_tv'],
                is_refrigerator=room_data['is_refrigerator'],
                is_hot_water_24=room_data['is_hot_water_24'],
                is_free_parking=room_data['is_free_parking'],
                is_smoking=room_data['is_smoking'],
                is_air=room_data['is_air'],
                is_hot_kettle=room_data['is_hot_kettle'],
                is_kitchen=room_data['is_kitchen'],
                is_shower=room_data['is_shower'],
                is_bathtub=room_data['is_bathtub'],
                is_carrypet=room_data['is_carrypet'],
                is_towel=room_data['is_towel'],
                is_slipper=room_data['is_slipper'],
                is_disposable=room_data['is_disposable'],
                is_washer=room_data['is_washer'],
                is_hlep_ticket=room_data['is_hlep_ticket'],
                is_hlep_car=room_data['is_hlep_car'],
                is_reception_child=room_data['is_reception_child']
            )
        except:
            print("民宿id：【%s】,房间id：【%s】此数据格式有误，无法插入" % (str(homestay_id),room_info['title']))
            self.handlerLog.write_log("民宿id：【%s】,房间id：【%s】此数据格式有误，无法插入\n" % (str(homestay_id),room_info['title']))
            return

        # 在存储数据之前，判断一下room_table表中是否此记录是否已经存在
        check_result = self.mysql_session.query(ZZKRoomTable).filter(ZZKRoomTable.room_id == room_info['roomId']).first()
        if not check_result:
            # 不存在
            self.mysql_session.add(format_item)
            self.mysql_session.commit()
            print("id:【%s】,room_name:【%s】已插入数据库" % (room_info['roomId'], room_info['title']))
        else:
            print("【%s】此数据已存在" % str(room_info['title']))



    # 民宿图片表插入一条记录
    def insert_homestay_pic_table(self,homestays,show_url,slider_url):
        format_item = ZZKHomestayPicTable(
            homestay_id = homestays['id'],
            homestay_show_pic = show_url,
            homestay_slider_pic = slider_url
        )
        check_result = self.mysql_session.query(ZZKHomestayPicTable).filter(ZZKHomestayPicTable.homestay_show_pic==show_url,
                                                             ZZKHomestayPicTable.homestay_slider_pic==slider_url).first()
        if not check_result:
            self.mysql_session.add(format_item)
            self.mysql_session.commit()
            print("id:【%s】,homestay_name:【%s】民宿的图片已插入数据库" % (homestays['id'], homestays['name']))
        else:
            message_tip = "%s民宿图片url：%s------%s在homestay_pic_table表中已存在，终止插入" % (self.get_now_time(),show_url,slider_url)
            print(message_tip)
            self.handlerLog.write_log(message_tip+'\n')


    # 民宿表插入一条记录
    def  insert_homestay_table(self,data,room_pic_path,land_pic_path,homestay,mydata,city):
        try:
            fotmat_item = ZZKtables(
                homestay_id = homestay['id'],
                homestay_name = homestay['name'],
                homestay_address = homestay['address'],
                is_speed = homestay['speed_room'],
                is_promotion = data['isPromotion'],
                is_boutique = data['isBoutiqueBnb'],
                baoche_service = data['baocheServiceI'],
                jiesong_service = data['jiesongServiceI'],
                daiding_service = data['daidingServiceI'],
                huwai_service = data['huwaiServiceI'],
                other_service = data['otherServiceI'],
                comment_num = data['commentNum'],
                jingdu = data['slng'],
                weidu = data['slat'],
                min_price = data['minPrice'],
                is_chinese_landlord = data['isChineseLandlord'],
                latest_success_time = data['latestSuccessTimeS'],
                room_num = data['room_num'],
                has_story = data['hasStoryI'],

                address_type=city,
                homestay_index_pic=room_pic_path,
                landlord_pic=land_pic_path,

                # 民宿简介
                homestay_desc = mydata['homestay_desc'],
                # 取消预订全额退款天数(前多少天)
                full_refund_days = mydata['full_refund_days'],
                # 不可取消预订天数(前多少天)
                not_refund_days = mydata['not_refund_days'],
                # 取消预订扣款比例
                cut_pay = mydata['refund_cut'],
                # 注意事项
                terms_txt = mydata['terms'],
                # 交通路线文字描述
                traffic_txt = mydata['tfc_txt'],
                # 交通路线图
                homestay_traffic_pic = mydata['tfc_pic_url'],
                # 民宿logo图
                homestay_logo_pic = mydata['homestay_logo_url'],
                # 注册时间
                homestay_registry = mydata['reg_time'],
                # 服务语言
                service_language = data['followLanguageS'],

            )
        except:
            print("【%s】此数据格式有误，无法插入"%str(homestay['name']))
            self.handlerLog.write_log('%s，数据异常：%s\n'%(self.get_now_time(),homestay['name']))
            return
        # 在存储数据之前，判断一下homestay表中是否此记录是否已经存在
        check_result = self.mysql_session.query(ZZKtables).filter(ZZKtables.homestay_id == homestay['id']).first()
        if not check_result:
            # 不存在才插入
            self.mysql_session.add(fotmat_item)
            # 手动提交
            self.mysql_session.commit()
            print("id:【%s】,homestay_name:【%s】已插入数据库"%(homestay['id'],homestay['name']))
        else:
            print("【%s】此数据已存在"%str(homestay['name']))



    def get_now_time(self):
        return time.strftime('%Y.%m.%d %H:%M:%S ', time.localtime(time.time()))





handler_zzk_data = HandlerZZKData()