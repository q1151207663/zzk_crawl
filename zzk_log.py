
class HandlerLog(object):
    def __init__(self):
        self.log_path = 'zzk_crawl_log.txt'

    def write_log(self,log_str):
        with open(self.log_path,'a',encoding='utf8') as fw:
            fw.write(log_str)


if __name__ == '__main__':
    handlerLog = HandlerLog()