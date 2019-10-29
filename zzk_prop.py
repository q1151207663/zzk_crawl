class Properties:
    def __init__(self,name):
        self.file_name = name
        self.property = {}

        with open(self.file_name,'r') as fr:
            for f in fr:
                fsplit = f.split('=')
                self.property[fsplit[0]]=fsplit[1]


    def update_properties(self,page_count,room_count):
        with open(self.file_name,'w+') as fwr:
            fwr.write('page_count=%s\n'%page_count)
            fwr.write('room_count=%s'%room_count)



if __name__ == '__main__':
    file_name = 'zzk_crawl.properties'
    prop = Properties(file_name)

