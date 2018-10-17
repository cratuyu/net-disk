# -*- coding: utf-8 -*-
import tkinter
from socket import *
import sys, os
from time import sleep
from setting import *
from gui import *

# 创建 与服务端通信的类
class TftpClient(object):
    def __init__(self, ADDR):
        sockfd = socket()
        sockfd.connect(ADDR)
        self.sockfd = sockfd

    # 当用户确认下载后 执行该函数与服务端进行通信
    def download(self, filename):
        # 获取tkinter的输入框输入的信息
        self.entry_down1 = filename
        # 如果用户误操作 则不会执行后边的代码
        if self.entry_down1 == "":
            print("未输入要下载的文件名")
            return
        file = FILE_PATH + self.entry_down1
        # get 下载命令与文件名一起发给服务端
        cmd = "get" + self.entry_down1
        self.sockfd.send(("{}".format(cmd)).encode())
        data = self.sockfd.recv(1024).decode()
        # 如果接受到服务端发送来的None 表示服务端无此文件
        if data == "None":
            print("服务器未找到此文件")
        # 如果 接受到 wenben 表示服务器上 该文件为文本格式 则以文本格式接收并写入
        elif data == "wenben":
            size = self.sockfd.recv(1024).decode()
            num = (int(size) + 4095) // 4096
            self.get_file(file, num, "w")
        # 如果接收到服务端发来的erjinzhi 表示该文件为二进制文件 则以 二进制文件接收并写入
        elif data == "erjinz":
            size = self.sockfd.recv(1024).decode()
            num = (int(size) + 4095) // 4096
            self.get_file(file, num, "wb")
        # 如果接收到服务端发来的dir 表示该文件为文件夹, 则创建文件夹并开始接收所有内容
        elif data == "dir":
            self.get_dir(file)

    @staticmethod
    def calculate(num):
        num1 = 0
        num2 = num
        if num > 262144:
            num1 = num // 20
            num2 = num // 20 + num % 20
        return (num1, num2)

    # 以普通文本方式接收
    def get_file(self, file, num, way):
        try:
            num1, num2 = self.calculate(num)
            with open('{}'.format(file), way) as f:
                # 在接收大文件时 data拼接数据可能会非常巨大 于是可以分成几次接收拼接并写入
                for i in range(20):
                    # 创建一个变量 将接收到的信息连接起来 防止出现汉字被切割 出现解码错误
                    data = b""
                    if i == 19:
                        num1 = num2
                    while num1:
                        num1 -= 1
                        line = self.sockfd.recv(4096)
                        data += line
                    if way == "w":
                        f.write(data.decode())
                    else:
                        f.write(data)
                # 发送提示信息到客户端 表示已经接收完毕 可以接受下一个文件
                self.sockfd.send(b"OK")
        # 如果 该文件和存入文件路径下某文件夹同名 则将文件名加"1" 并写入
        except IsADirectoryError as e:
            num1, num2 = self.calculate(num)
            with open('{}'.format(file + "1"), way) as f:
                for i in range(20):
                    data = b""
                    if i == 19:
                        num1 = num2
                    while num1:
                        num1 -= 1
                        line = self.sockfd.recv(4096)
                        data += line
                    if way == "w":
                        f.write(data.decode())
                    else:
                        f.write(data)
                self.sockfd.send(b"OK")
        except Exception as e:
            print("不可预知的错误发生了", e)

    # 以文件夹方式接收
    def get_dir(self, file):
        # 如果 此文件夹不存在 则创建
        if not os.path.isdir(file):
            os.makedirs(file)
        while True:
            try:
                data = self.sockfd.recv(1024)
                print(data)
                line = data.decode()
                if line == "over":
                    print(line)
                    break
                elif line[:6] == "wenben":
                    print(line)
                    # 获取 此文件的大小
                    size = self.sockfd.recv(1024).decode()
                    #
                    num = (int(size) + 4095) // 4096
                    self.get_file(FILE_PATH+line[25:], num, "w")
                elif line[:6] == "erjinz":
                    print(line)
                    # 获取 此文件的大小
                    size = self.sockfd.recv(1024).decode()
                    num = (int(size) + 4095) // 4096
                    self.get_file(FILE_PATH+line[25:], num, "wb")
                elif line[:6] == "dictor":
                    print(line)
                    if os.path.isdir(FILE_PATH+line[25:]):
                        print("这是一个已存在的文件夹")
                        continue
                    os.makedirs(FILE_PATH+line[25:])
                else:
                    print(line)
            except UnicodeDecodeError as e:
                print("大哥 文件夹接收又出错了 快改改",e)

    # 上传文件
    def upload(self,filename):
        self.entry_up1 = filename
        print(self.entry_up1)
        # 用户误操作时不执行
        if not self.entry_up1:
            print("未输入要下载的文件名")
            return
        file = FILE_PATH + self.entry_up1
        if os.path.isfile(file):
            cmd = "put" + self.entry_up1
            self.sockfd.send(cmd.encode())
            msg = self.sockfd.recv(1024).decode()
            if msg == "Error":
                print("服务器已有文件名,请重试")
            # 如果 接收到 Right 表示服务端已准备就绪 准备接收文件
            elif msg == "Right":
                try:
                    with open(file) as f:
                        f.readline()
                    size = os.path.getsize(file)
                    # 发送 wenben 和 文件大小 信号 提醒服务端接收的是文本文件
                    self.sockfd.send(("wenben"+str(size)).encode())
                    # 睡眠0.2秒 等待服务端创建好文件 协调双方收发读写速度
                    sleep(0.1)
                    # 以文本文件格式打开 并发送
                    with open("{}".format(file), "rb") as f:
                        self.send_file(f)
                    print("上传成功")
                # 如果 在以文本文件打开并读取一行数据时出错 则表示该文件为二进制文件 以二进制文件发送
                except UnicodeDecodeError:
                    # 提醒服务端 以二进制文件接收 并写入
                    size = os.path.getsize(file)
                    self.sockfd.send(("erjinz"+str(size)).encode())
                    sleep(0.1)
                    with open("{}".format(file), "rb") as f:
                        self.send_file(f)
                    print("上传成功")
                except Exception as e:
                    print("不知道咋回事", e)
        elif os.path.isdir(file):
            cmd = "put" + self.entry_up1
            self.sockfd.send(cmd.encode())
            msg = self.sockfd.recv(1024).decode()
            if msg == "Error":
                print("服务器已有文件名,请重试")
            # 如果 接收到 Right 表示服务端已准备就绪 准备接收文件
            elif msg == "Right":
                self.sockfd.send(b"dictor")
                self.send_dictory(file)
                self.sockfd.send(b"over")

    def send_file(self, f):
        while True:
            # 从 文件中固定读取4096个字节
            data = f.read(4096)
            if not data:
                break
            self.sockfd.sendall(data)
        # 在这里阻塞 当客户端接收完毕之后会发送 OK 到服务端  提醒服务端可以发送下一个文件
        data = self.sockfd.recv(128).decode()
        if data == "OK":
            sleep(0.01)

    def send_dictory(self,filename):
        # 将文件夹下的文件及文件夹名列表用list绑定
        list = os.listdir(filename)
        print(list)
        # 每个文件夹后加上一个斜杠 当递归打开子文件夹时 避免子文件夹名和子文件夹下的文件名粘连
        file = filename + "/"
        # 循环发送文件夹下的所有文件及文件夹
        for i in list:
            # 判断该路径名是否为文件
            if os.path.isfile(file + i):
                try:
                    # 试着以普通文本文件打开此文件 若错误 则会跳到下面的二进制发送
                    with open(file + i) as f:
                        f.readline()
                    with open(file + i, "rb") as f:
                        # 发送"wenben"+文件名到客户端 提醒客户端 这是一个文本文件 以文本方式接收
                        self.sockfd.send(("wenben" + file + i).encode())
                        sleep(0.1)
                        # 获取文件大小 发送给客户端 客户端则知道要循环接收多少次
                        size = os.path.getsize(file + i)
                        self.sockfd.send(str(size).encode())
                        # 睡眠0.3秒 防止发送的文件信息和文件大小粘包
                        sleep(0.1)
                        self.send_file(f)
                        print(i + "wenben发送完毕")
                except UnicodeDecodeError:
                    with open(file + i, "rb") as f:
                        self.sockfd.send(("erjinz" + file + i).encode())
                        sleep(0.1)
                        size = os.path.getsize(file + i)
                        self.sockfd.send(str(size).encode())
                        sleep(0.1)
                        self.send_file(f)
                        print(i + "erjinzhi发送完毕")
            elif os.path.isdir(file + i):
                sleep(0.1)
                self.sockfd.send(("dictor" + file + i).encode())
                self.send_dictory(file + i)

    # 将要删除的云端文件名 发送到服务器
    def delete(self, filename):
        self.entry_del1 = filename
        if not self.entry_del1:
            return
        # del 命令 + 文件名
        cmd = "del" + self.entry_del1
        self.sockfd.send(cmd.encode())
        data = self.sockfd.recv(1024).decode()
        print(data)


class login_server:

    def __init__(self, ADDR):
        sockfd = socket()
        sockfd.connect(ADDR)
        self.sockfd = sockfd

    def login(self,gui1, name, upwd):
        print(name,upwd)
        if name and upwd:
            data = "log" + name + "##" + upwd
            self.do_send(gui1, data)

    def register(self,gui1, name, upwd):
        if name and upwd:
            data = "reg" + name + "##" + upwd
            self.do_send(gui1, data)

    def do_send(self,gui1, data):
        self.sockfd.send(data.encode())
        line = self.sockfd.recv(1024).decode()
        print(line)
        if line == "YES":
            # 关闭一级界面
            gui1.destroy()
            gui2 = net_disk(TftpClient)
        else:
            # todo
            gui1.label = Label(gui1, text="用户名或者密码错误")
            gui1.label.pack(side='bottom')




