程序说明：
1、本程序可爬取自在客网站民宿，房间的相关数据
2、本程序仅用于学习，不用于商业，若因学习之外的任何行为造成违法，作者概不负责

运行环境：
win10 64位，mysql5.7以上最好，最好使用ip代理(不用也行)，python3

三方库：
requests，sqlalchemy，pymysql

使用说明：
在zzk_crawl.properties文件中配置爬取的国家(英文小写)，初次爬取另外三个参数都设置为1
这三个参数是防止重复爬取的
只需要在换另一个国家时将它们重置为1即可
再创建数据库zzk    create database zzk;
先安装三方库，dos界面pip install requests 依次安装需要的三方库
运行create_zzk_table.py创建数据表
最后运行handler_crawl_zzk.py即可开始爬取
