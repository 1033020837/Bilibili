"""
    使用多进程
    下载B站指定视频
"""

from contextlib import closing
import requests
import sys,os
import re
import json
import shutil
import re
import threading
from multiprocessing import Pool
from pprint import pprint

# 下载地址的镜像格式部分的可能替换值
video_mode = [ 'mirrorcos.', 'mirrorkodo.', 'mirrorks3.', 'mirrorbos.', 'mirrorks3u.',  ]

# 主线程
main_thread = threading.current_thread()

def make_path(p):  
    """
        判断文件夹是否存在
        存在则清空
        不存在则创建
    """
    #if os.path.exists(p):       # 判断文件夹是否存在  
    #    shutil.rmtree(p)        # 删除文件夹  
    if not os.path.exists(p):
        os.mkdir(p)                 # 创建文件夹  


        
headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
			'Accept': '*/*',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.bilibili.com'
          }

sess = requests.Session()  
#下载的根目录
root_dir = '.'          

def download_video(video_url, dir_, video_name, index, count):   
    '''
        下载一个视频片段
    '''
    size = 0
    session = requests.Session()    
    mirror = re.findall('mirror.*?\.', video_url)
    # 链接中是否带mirror字符
    isMirror = len(mirror) > 0   
    chunk_size = 1024 #每次1KB
    video_path = os.path.join(dir_, video_name, str(index) + '.flv')
    for i,mode in enumerate(video_mode):  
        video_url = re.sub('mirror.*?\.', mode, video_url)
        response = session.get(video_url, headers=headers, stream=True, verify=False)
            
        if response.status_code == 200:
            content_size = int(response.headers['content-length'])
            print("进程ID%d: %s 第%d/%d个片段, [文件大小]:%0.2f MB"% (os.getpid(), video_name, index, count, content_size / 1024 / 1024))
            with open(video_path, 'wb') as file:
                j = 0
                for data in response.iter_content(chunk_size = chunk_size):
                    file.write(data)
                    size += len(data)
                    file.flush()
                    if j > 0 and j % 1000 == 0:
                        print("进程ID%d: %s 第%d/%d个片段, [下载进度]:%.2f%%"% (os.getpid(), video_name, index, count, float(size / content_size * 100)))
                    j += 1
            return
        
        else:
           
            print('进程ID%d：链接异常，尝试更换链接' %os.getpid())    
            
            if not isMirror or i == len(video_mode) - 1:
                print('进程ID%d：%s 第%d/%d个片段无法下载' %(os.getpid(), video_name, index, count)) 
                return                    

def download_videos(dir_, video_urls, video_name):
    """
        下载一个完整视频的所有视频片段
    """
    make_path(os.path.join(dir_, video_name))
    print('进程ID%d: %s 开始下载' %(os.getpid(), video_name))
    for i, video_url in enumerate(video_urls):      
        download_video(video_url, dir_, video_name, i+1, len(video_urls))
    print('进程ID%d: %s 下载完成' %(os.getpid(), video_name))
                
def get_download_urls(arcurl):
    req = sess.get(url=arcurl, headers = headers, verify=False)
    pattern = '.__playinfo__=(.*)</script><script>window.__INITIAL_STATE__='
    try:
        infos = re.findall(pattern, req.text)[0]
    except:
        return []
    json_ = json.loads(infos)
    durl = json_['durl']
    
    #urls = [re.sub('mirror.*?\.', 'mirrorcos.', url['url']) for url in durl]
    urls = [url['url'] for url in durl]
    
    return urls

def get_page_count(url):
    """
        获取一个视频的页数
    """
    req=sess.get(url, headers=headers)
    pattern = '\"pages\":(\[.*}}\]),'
    try:
        infos = re.findall(pattern, req.text)[0]
        json_ = json.loads(infos)
        title_pages = dict([(page['part'],page['page']) for page in json_])
        title = re.findall('<title .*>(.*)</title>', req.text)[0]
        return title_pages, title
    except  Exception as e:
        print("Error when get page count.")
        print(e)
        return

def one_process(dir_, urls_and_titles):
    """
        修改为多进程下载
        此函数为一个进程所执行的部分下载任务
    """
    for urls,title in urls_and_titles:
        download_videos(dir_, urls, '%s' %title)
    
if __name__ == '__main__':   
    # 视频编号，替换为自己需要下载的视频编号
    aid = '31300709'
    
    # 一个视频可能分很多，定义从第几页开始下载
    start_page = 1
    
    url = 'https://www.bilibili.com/video/av%s'%aid
    title_pages, title = get_page_count(url)
    dir_ = os.path.join(root_dir, title)
    make_path(dir_)
    print('创建文件夹 %s 成功' %dir_)
    urls_and_titles = []
    for title,page in title_pages.items():
        if page < start_page:
            continue
        video_url = url + '/?p=%d' %page
        urls = get_download_urls(video_url)
        urls_and_titles.append([urls, title])
    
    # 需要下载的视频总数
    count = len(urls_and_titles)
    # 进程数目,需要下载的视频总数超过30才会开启多进程
    process_count = 5
    # 每个进程需要下载的视频数目
    each_count = count // process_count
    indexs = []
    for i in range(process_count):
        if each_count != 0:
            indexs.append(urls_and_titles[i*each_count:(i+1)*each_count])
        if i == (process_count - 1) and (i+1)*each_count != count:
            indexs.append(urls_and_titles[(i+1)*each_count:count])
    print(indexs)
    print('Parent process %s.' % os.getpid())
    p = Pool(process_count)
    for i in range(len(indexs)):
        p.apply_async(one_process, args=(dir_, indexs[i]))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')