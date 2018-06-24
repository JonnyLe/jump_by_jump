__author__ = 'Jonny'
__time__ ='2018.01.22'
__site__='济南'

import os
import sys
import re
import time
import random
import json
import subprocess
import math
import debug
from PIL import Image


#是否循环游戏，标志参数
LOOP = False
#截图参数
SCREENSHOT_WAY = 2
#调试参数
DEBUG = True


def _get_screen_size():
    #获取手机得分辨率
    size_str = os.popen('adb shell wm size').read()
    print(size_str)
    if not size_str:
        print('请安装ABD模块及相关驱动')
        sys.exit()
    m = re.search(r'(\d+)x(\d+)',size_str)
    if m :
        return "{height}x{width}".format(height = m.group(2),width = m.group(1))
    else:
        exit('无法获取屏幕数据')


def init():
    # 初始化手机屏幕参数和棋子棋盘的各种参数
    #获取手机的分辨率
    size_str =_get_screen_size()
    # 避免出现空值，提高系统的容错性
    if size_str:
        #print(size_str)
        # 获取配置文件路径
        config_file_path = 'config/%s/config.json'%size_str
        if os.path.exists(config_file_path):
            with open(config_file_path,'r') as f:
                print('Load config file from %s'%config_file_path)
                return json.load(f)#返回字典类型
        else:
            with open('config/default.json','r') as f:
                print('Load default file')
                return json.load(f)
    # else:
    #     exit('无法获取屏幕数据')


def get_screenShot():
    process = subprocess.Popen('adb shell screencap -p',shell = True,stdout=subprocess.PIPE)
    #适用于Windows
    screenshot = process.stdout.read()
    #由于Windows环境下的图片和Android下的图片格式有一定的区别和格式差异
    #个人认为主要是由于两个操作系统windo和Linux操作系统造成的（Android系统事基于linu系统的）
    bytes_screenshot = screenshot.replace(b'\r\r\n',b'\n')
    #保存截屏图片
    with open('autojump.png','wb') as f:
        f.write(bytes_screenshot)
    #print(screenshot)  #用于测试代码使用，非程序打码
    #exit()   #程序测试代码


def find_piece_and_board(img, config):
    #分析棋子棋盘
    w,h = img.size
    #扫描y轴起点
    scan_start_y = 0
    #扫描棋子的左右边界，减少开销
    scan_x_side = int(w//8)
    #棋子的底坐标
    pixel_y_max = 0
    #获取图片的像素矩阵(返回一个对象)
    img_pixel = img.load()

    if not LOOP:
        if sum(img_pixel[5,5][:-1])<150:
            exit('Game Over!')
    #检测scan_start_y的初值(去掉干扰部分，减少检测开销,截取图片的中间的1/3的图片，扫描的步长是50)
    for i in range(h//3,h*2//3,50):
        first_pixel = img_pixel[0,i]
        for j in range(1,w):
            #如果是非纯色的，说明遇到跳块
            pixel = img_pixel[j,i]
            if pixel[:-1] != first_pixel[:-1]:
                scan_start_y = i-50
                break
        if scan_start_y != 0:
            break
        #从上往下开始扫描棋子，棋子一般位于屏幕的上半部分
    left = 0
    right = 0
    for i in range(scan_start_y,h*2//3):
        flag = True
        for j in range(scan_x_side,w-scan_x_side):
            pixel  = img_pixel[j,i]
            #根据棋子为紫色，可以通过ps和RGB 测算出紫色的像素范围值
            if (50 < pixel[0] <60) and (53 < pixel[1]< 63) and (95 < pixel[2]<110):
                if flag == True:
                    left = j;
                    flag = False;
                right = j
                pixel_y_max =max(i,pixel_y_max)
    if not all((left,right)):
        return 0,0,0,0
    piece_x = (left + right) // 2
    piece_y = pixel_y_max - config['piece_base_height_1_2']  #上调坐标，找到中心点
          #  print('***********',piece_x,piece_y,'************')  #测试代码
            #限制棋盘的扫描高度
    if piece_x < w/2:
        board_x_start = piece_x + config['piece_body_width']//2
        board_x_end = w
    else:
        board_x_start = 0
        board_x_end = piece_x - config['piece_body_width']//2

    #从上往下扫描找到棋盘的横坐标
    left = 0
    right = 0
    num = 0
    for i in range((h//3),h*2//3):
        flag = True
        first_pixel = img_pixel[0, i]
        for j in range(board_x_start,board_x_end):
            pixel = img_pixel[j,i]
            #20是色差阈值可以调节
            if (abs(pixel[0] - first_pixel[0])+abs(pixel[1]-first_pixel[1])+abs(pixel[2]-first_pixel[2]))>10:
                if flag:
                    left = j
                    right = j
                    flag = False
                else:
                    right = j
                num = num + 1
                print(left,right)  #测试代码
        if not flag:
            break
    board_x = (left + right) // 2
    top_point = img_pixel[board_x,i+1] #i+1去掉上面一条白线的BUG
    # 从上顶点往下 + con['height']的位置开始向上找颜色与上顶点一样的点，为下顶点
    # if num < 5:
    #     # 说明是方形
    #     if abs(top_point[0] - 255) + abs(top_point[1] - 228) + abs(top_point[2] - 226) < 5:
    #         print('唱片图案')
    #         top = 0
    #         bottom = 0
    #         for k in range(i, i + con["height"]):
    #             pixel = img_pixel[board_x, k]
    #             # 根据唱片中的红色部分判断
    #             # if (155 < pixel[0] < 180) and (141 < pixel[1] < 165) and (113 < pixel[2] < 116):
    #             # print(pixel[0], pixel[1], pixel[2])
    #             if (abs(pixel[0] - 239) < 3) and (abs(pixel[1] - 118) < 3) and (abs(pixel[2] - 119) < 3):
    #
    #                 if not top:
    #                     top = k
    #                 else:
    #                     bottom = k
    #                 # print(top, bottom)
    #         board_y = (top + bottom) // 2
    #         return piece_x, piece_y, board_x, board_y


    # 该方法对所有纯色平面和部分非纯色平面有效
    # print(top_point)
    for k in range(i+config['height'],i,-1):
        pixel = img_pixel[board_x,k]
        print(pixel)  #测试代码
        if (abs(pixel[0]-top_point[0])+abs(pixel[1]-top_point[0])+abs(pixel[2]-top_point[2]))<10:
            break
    board_y = (i+k)//2
    if num <5:
        #去掉有些颜色比较多的误差
        if k-i <30:
            print('深红色433---->>>')
            board_y += (k-i)
    #去掉药瓶
    if num == 3:
        if top_point[:-1] ==(219,221,229):
            print('唱片！')
            top = 0
            bottom = 0
            for k in range(i,i+config['height']):
                pixel = img_pixel[board_x,k]
                #根据唱片中的红色部分判断
                # #if (155 < pixel[0] < 180) and (141 < pixel[1] < 165) and (113 < pixel[2] < 116):
                # print(pixel[0], pixel[1], pixel[2])
                if pixel[:-1] ==(118,118,118):
                    if not top:
                        top = k
                    else:
                        bottom = k
                        print(top,bottom)   #测试代码
            board_y = (top+bottom)//2
            return piece_x,piece_y,board_x,board_y
    if not all((board_x,board_y)):
        return 0,0,0,0
    return piece_x,piece_y,board_x,board_y


def jump(distance, point,ratio):
    #跳跃
    press_time = distance *  ratio
    press_time = max(press_time,200)
    press_time = int(press_time)
    cmd = 'adb shell input swipe {x1} {y1} {x2} {y2} {duration}'.format(
        x1 = point[0],
        y1 = point[1],
        x2 = point[0]+random.randint(0,3),
        y2 = point[1]+random.randint(0,3),
        duration = press_time
    )
    print(cmd)
    os.system(cmd)
    return press_time


def check_screenshot():
    global SCREENSHOT_WAY
    if os.path.isfile('autojump.png'):
        os.remove('autojump.png')
    if SCREENSHOT_WAY<0:
        print('暂不支持该设备！')
        sys.exit()
    get_screenShot()
    try:
        Image.open('autojump.png').load()
    except Exception as e:
        print(e)
        SCREENSHOT_WAY = SCREENSHOT_WAY-1
        check_screenshot()



def run():
    """主要函数，完成程序的主要任务"""
    open_game = input('请确保手机打开了 ADB 并连接了电脑，然后打开跳一跳并【开始游戏】后再用本程序，确定开始？y/n>>:')
    # if (open_game != 'y')or(open_game != 'Y'):
    #    exit('退出！')
    # 初始化：
    config = init()
    #检查截图方式：
    check_screenshot()
    print('通过第%s种方式获取截图'%SCREENSHOT_WAY)
    while True:
        #截图autojump.png
        get_screenShot()
        #读取截取的图片
        img = Image.open('autojump.png')
        piece_x,piece_y,board_x,board_y = find_piece_and_board(img,config)
        #计算棋子棋盘的距离
        ntime = time.time()
        print(piece_x,piece_y,board_x,board_y,'------->')
        distance = math.sqrt((piece_x - board_x)**2 + (piece_y - board_y)**2)
        #生成一个随机按压点，防止被Ban
        if DEBUG:
            debug.save_debug_screenshot(ntime,img,piece_x,piece_y,board_x,board_y)
            debug.backup_screenshot(ntime)
        press_point = (random.randint(*config['swipe']['x']),
                           random.randint(*config['swipe']['y']))
        #跳跃
        jump(distance,press_point,config['press_ratio'])
        #休息，停留（注意应该理论上是可以休息1~2秒的挣个连续区间，而不是离散区间）
        time.sleep(random.randrange(1,3))

#测试代码
# def test_screenshot():
#     img = Image.open('autojump.png')
#     con = init()
#     res = find_piece_and_board(img,con)
#     print(res)


if __name__=='__main__':
    run()
    #_get_screen_size()