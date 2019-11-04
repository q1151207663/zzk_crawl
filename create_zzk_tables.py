from sqlalchemy import create_engine, Integer, String, Float, DECIMAL, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column




engine = create_engine("mysql+pymysql://root:ranhongxia@127.0.0.1:3306/zzk?charset=utf8")
Session = sessionmaker(engine)

# 创建一个基类
Base = declarative_base()

# 民宿表
class ZZKtables(Base):
    # 表名
    __tablename__ = 'homestay_table'
    # 主键
    homestay_id = Column(String(length=50),primary_key=True)
    # 民宿名
    homestay_name = Column(String(length=500),nullable=False)
    # 民宿地址，非空字段
    homestay_address = Column(String(length=500),nullable=False)
    # 支持速订
    is_speed = Column(Integer,default=0)
    # 促销优惠
    is_promotion = Column(Integer,default=0)
    # 精品
    is_boutique = Column(Integer,default=0)
    # 服务
    baoche_service = Column(Integer,default=0)
    jiesong_service = Column(Integer,default=0)
    daiding_service = Column(Integer,default=0)
    dingcan_service = Column(Integer,default=0)
    huwai_service = Column(Integer,default=0)
    other_service = Column(Integer,default=0)
    comment_num = Column(Integer,nullable=False)
    jingdu = Column(Float,nullable=False)
    weidu = Column(Float,nullable=False)
    # 最低价
    min_price = Column(DECIMAL,nullable=False)
    is_chinese_landlord = Column(Integer,default=0)
    latest_success_time = Column(String(length=100),default='1998-02-18 00:00:00')
    # 房东照片
    landlord_pic = Column(String(length=500))
    # 首页展示图
    homestay_index_pic = Column(String(length=500))
    # 房间数量
    room_num = Column(Integer,nullable=False)
    # 是否有故事~
    has_story = Column(Integer,default=0)
    # 位于那个国家
    address_type = Column(String(length=50),nullable=False)
    # 民宿简介
    homestay_desc = Column(Text)

    # 下面3个为null则具体的取消政策按房型不同而异。详细政策请事先咨询。
    # 取消订单全额退款天数(前多少天)
    full_refund_days = Column(String(length=10))
    # 拒绝取消预订天数
    not_refund_days = Column(String(length=10))
    # 取消预订扣款比例
    cut_pay = Column(String(length=10))

    # 注意事项
    terms_txt = Column(Text)
    # 交通路线文字描述
    traffic_txt = Column(Text)
    # 民宿logo图片
    homestay_logo_pic = Column(String(length=500),nullable=False)
    # 民宿交通图片
    homestay_traffic_pic = Column(String(length=500),nullable=False)
    # 注册时间
    homestay_registry = Column(String(length=50),nullable=False)
    # 服务语言
    service_language = Column(String(length=100),nullable=False)
    # 收到私信数量
    get_mail_num = Column(Integer,default=0)
    # 回复私信数量
    to_mail_num = Column(Integer,default=0)
    # 回信时间间隔
    to_mail_time = Column(String(length=50))



# 民宿图片表
class ZZKHomestayPicTable(Base):
    __tablename__ = 'homestay_pic_table'
    # 主键
    homestay_pic_id = Column(Integer,primary_key=True,autoincrement=True)
    # 外键
    homestay_id = Column(String(length=50))
    # 民宿展示图片
    homestay_show_pic = Column(String(length=500))
    # 民宿幻灯片下的小图片
    homestay_slider_pic = Column(String(length=500))


# 房间图片表
class ZZKRoomPicTable(Base):
    __tablename__ = 'room_pic_table'
    # 主键
    room_pic_id = Column(Integer,primary_key=True,autoincrement=True)
    # 外键
    room_id = Column(String(length=50))
    # 房间图片
    room_show_pic = Column(String(length=500))



# 民宿房间表
class ZZKRoomTable(Base):
    __tablename__ = 'room_table'

    room_id = Column(String(length=50),primary_key=True)
    # 房间标题
    room_title = Column(String(length=500),nullable=False)
    # 外键...手动添加
    homestay_id = Column(String(length=50))
    # 早餐
    breakfast = Column(Integer,default=0)
    # 床型
    chuangxing = Column(String(length=50))
    # 该房间支持速订
    support_speed = Column(Integer,default=0)
    # 房间价格
    room_price = Column(DECIMAL,nullable=False)
    # 房型
    room_model = Column(String(length=5))
    # WiFi
    room_wifi = Column(Integer,default=0)
    # 房间首映图
    room_index_pic = Column(String(length=500))
    # 房间面积
    room_area = Column(String(length=50))
    # 楼层
    room_floor = Column(String(length=50))
    # 电梯
    room_elevator = Column(String(length=50))
    is_window = Column(String(length=20))
    # 最多入住
    max_stay = Column(String(length=20))

    # 相关设施
    is_tv = Column(Integer,default=0)
    # 电冰箱
    is_refrigerator = Column(Integer,default=0)
    is_hot_water_24 = Column(Integer,default=0)
    is_free_parking = Column(Integer,default=0)
    is_smoking = Column(Integer,default=0)
    # 空调
    is_air = Column(Integer,default=0)
    # 热水壶
    is_hot_kettle = Column(Integer,default=0)
    # 厨房
    is_kitchen = Column(Integer,default=0)
    # 淋浴
    is_shower = Column(Integer,default=0)
    is_bathtub = Column(Integer,default=0)
    is_carrypet = Column(Integer,default=0)
    # 毛巾
    is_towel = Column(Integer,default=0)
    # 拖鞋
    is_slipper = Column(Integer,default=0)
    # 一次性物品
    is_disposable = Column(Integer,default=0)
    # 洗衣机
    is_washer = Column(Integer,default=0)
    # 代订门票
    is_hlep_ticket = Column(Integer,default=0)
    # 代叫车
    is_hlep_car = Column(Integer,default=0)
    # 接待儿童
    is_reception_child = Column(Integer,default=0)
    # 限时优惠
    discounts = Column(String(length=20),default='0%')


if __name__ == '__main__':
    # 创建表
    ZZKtables.metadata.create_all(engine)
    ZZKRoomTable.metadata.create_all(engine)
    ZZKHomestayPicTable.metadata.create_all(engine)
    ZZKRoomPicTable.metadata.create_all(engine)
