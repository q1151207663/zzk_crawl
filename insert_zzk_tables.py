from zzk_crawl.create_zzk_tables import ZZKtables
from zzk_crawl.create_zzk_tables import Session
from zzk_crawl.zzk_log import HandlerLog
from zzk_crawl.zzk_prop import Properties


class HandlerZZKData(object):
    def __init__(self):
        self.mysql_session = Session()
        self.prop = Properties()
        self.handlerLog = HandlerLog()
        dics_data = {}

    # 数据的存储方法
    def insert_item(self,data):
        try:
            dics_data = ZZKtables(
                room_id = data['roomInfoList'][0]['roomId'],
                room_name = data['roomInfoList'][0]['title'],
                room_address = data['address'],
                is_speed = data['isSpeed'],
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
                price = data['minPrice'],
                is_chinese_landlord = data['isChineseLandlord'],
                latest_success_time = data['latestSuccessTimeS'],
                landlord_pic = data['userPhoto'],
                room_num = data['room_num'],
                current_room_num = data['room_num'],
                has_story = data['hasStoryI'],
                is_wifi = data['roomInfoList'][0]['wifiI'],
                address_type = 'thailand'
            )
        except:
            print("【%s】此数据格式有误，无法插入")
            self.handlerLog.write_log(log_str='\n数据异常：\n%s'%str(data))
            self.handlerLog.write_log('\n%s页，%s号'%(str(self.prop.property['page_count']),str(self.prop.property['room_count'])))
            return
        # 在存储数据之前，判断一下room表中是否此记录是否已经存在
        check_result = self.mysql_session.query(ZZKtables).filter(ZZKtables.room_id == data['roomInfoList'][0]['roomId']).first()
        if not check_result:
            # 不存在才插入
            self.mysql_session.add(dics_data)
            # 要手动提交
            self.mysql_session.commit()
            print("id:【%s】,room_name:【%s】已插入数据库"%(data['roomInfoList'][0]['roomId'],data['roomInfoList'][0]['title']))
        else:
            print("此数据已存在")

handler_zzk_data = HandlerZZKData()