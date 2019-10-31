import requests

session = requests.session()
url = 'http://img1.zzkcdn.com/jp27de64367dcc3def79e0513f56cd3e/2000x1500.jpg-homepic800x600.jpg'
file_path = 'D:\\serverUploadTemp\\crawl_repository\\a.jpg'
response = session.get(url=url)
data = response.content
print(data)
with open(file_path,'wb') as fw:
    fw.write(data)

