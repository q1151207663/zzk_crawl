class Properties:
    def __init__(self):
        self.file_name = 'zzk_crawl.properties'
        self.property = {}

        with open(self.file_name,'r') as fr:
            for f in fr:
                f = f.strip()
                fsplit = f.split('=')
                self.property[fsplit[0]]=fsplit[1]


    def update_properties(self,page_count,room_count):
        with open(self.file_name,'w+') as fwr:
            fwr.write('page_count=%s\n'%page_count)
            fwr.write('room_count=%s'%room_count)


    def reset_room(self,page_count):
        with open(self.file_name,'w+') as fwr:
            fwr.write('page_count=%s\n' % page_count)
            fwr.write('room_count=%s' % '1')


if __name__ == '__main__':
    prop = Properties()

