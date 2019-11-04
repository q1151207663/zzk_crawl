class Properties:
    def __init__(self):
        self.file_name = 'zzk_crawl.properties'
        self.property = {}

        with open(self.file_name,'r') as fr:
            for f in fr:
                f = f.strip()
                fsplit = f.split('=')
                self.property[fsplit[0]] = fsplit[1]


    def update_properties(self, page_count, room_count, land_count):
        with open(self.file_name,'w+') as fwr:
            fwr.write('page_count=%s\n' % page_count)
            fwr.write('room_count=%s\n' % room_count)
            fwr.write('land_count=%s\n' % land_count)
            fwr.write('country=%s' % self.property['country'])



    def reset(self,page_count):
        with open(self.file_name,'w+') as fwr:
            fwr.write('page_count=%s\n' % page_count)
            fwr.write('room_count=%s\n' % '1')
            fwr.write('land_count=%s\n'%'1')
            fwr.write('country=%s' % self.property['country'])


if __name__ == '__main__':
    prop = Properties()

