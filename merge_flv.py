# 主要是需要moviepy这个库
from moviepy.editor import *
import os

def merge_flv(movie_list, des):
    '''
        合并视频的方法
        @movie_list 按顺序排好的需要合并的视频
        @des 存储目标路径
    '''
    L = []
    for movie in movie_list:
        if os.path.splitext(movie)[1] == '.flv':
            video = VideoFileClip(movie)
            L.append(video)
        else:
            print('%s 不是.flv文件' %movie)
            return
    if len(L) == 0:
        return
    # 拼接视频
    final_clip = concatenate_videoclips(L)
    # 生成目标视频文件
    final_clip.to_videofile(des, fps=24, remove_temp=False)
    print('合并成功')
    
if __name__ == '__main__':
    # 要合并所有视频的根文件夹
    root_dir = '操作系统_清华大学(向勇、陈渝)_哔哩哔哩 (゜-゜)つロ 干杯~-bilibili'
    for dir in os.listdir(root_dir):
        dir_path = os.path.join(root_dir, dir)
        movie_list = []
        for flv_file in  os.listdir(dir_path):
            print(flv_file)
            if flv_file.endswith('.flv'):
                file_path = os.path.join(dir_path, flv_file)
            movie_list.append(file_path)
        #合并flv视频片段为mp4文件
        merge_flv(movie_list, os.path.join(dir_path, dir + '.mp4'))
    print("合并完成")
        