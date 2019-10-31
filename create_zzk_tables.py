from sqlalchemy import create_engine, Integer, String, Float, DECIMAL, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column




engine = create_engine("mysql+pymysql://root:ranhongxia@127.0.0.1:3306/zzk?charset=utf8")
Session = sessionmaker(engine)

# 创建一个基类
Base = declarative_base()
# 创建一个关联数据库的实体类，继承自那个基类
class ZZKtables(Base):
    # 表名
    __tablename__ = 'zzk_room_table'

    # 字段
    room_id = Column(Integer,primary_key=True,autoincrement=True)
    room_name = Column(String(length=500))
    # 民宿地址，非空字段
    room_address = Column(String(length=500),nullable=False)
    # 速订
    is_speed = Column(Integer,default=0)
    # 促销
    is_promotion = Column(Integer,default=0)
    # 精品
    is_boutique = Column(Integer,default=0)
    # 包车服务
    baoche_service = Column(Integer,default=0)

    jiesong_service = Column(Integer,default=0)
    daiding_service = Column(Integer,default=0)
    dingcan_service = Column(Integer,default=0)
    huwai_service = Column(Integer,default=0)
    other_service = Column(Integer,default=0)

    comment_num = Column(Integer,nullable=False)
    jingdu = Column(Float,nullable=False)
    weidu = Column(Float,nullable=False)
    price = Column(DECIMAL,nullable=False)
    is_chinese_landlord = Column(Integer,default=0)
    latest_success_time = Column(String(length=100),default='1998-02-18 00:00:00')
    # 房东照片
    landlord_pic = Column(String(length=500))
    # 民宿房间数量
    room_num = Column(Integer,nullable=False)
    # 民宿当前房间数量
    current_room_num = Column(Integer,nullable=False)
    # 是否有故事~
    has_story = Column(Integer,default=0)
    is_wifi = Column(Integer,default=0)
    # 位于那个国家
    address_type = Column(String(length=50),nullable=False)

if __name__ == '__main__':
    # 创建表
    ZZKtables.metadata.create_all(engine)
