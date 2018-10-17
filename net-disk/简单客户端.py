# -*- coding: utf-8 -*-
import tkinter
from socket import *
import sys, os
from time import sleep
from setting import *


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


class tkinter_disk(object):

    def __init__(self, tftp, root):
        self.root = root
        # 设置窗口标题
        root.title("个人云空间")
        img1 = tkinter.PhotoImage(file="./timg1.gif")
        img2 = tkinter.PhotoImage(file="./timg2.gif")
        img3 = tkinter.PhotoImage(file="./timg3.gif")
        img4 = tkinter.PhotoImage(file="./timg4.gif")
        # 设置 标签属性
        label = tkinter.Label(root, text="个人云-秘密空间\n云上的日子 你我共享", bg="#e080e9",
                              width=74, height=5)
        # 在主界面放置标签
        label.place(x=0,y=0)
        # 设置按钮属性 绑定按钮调用的方法
        btn1 = tkinter.Button(root, image=img1, command=self.check)
        # 放置按钮
        btn1.place(x=0, y=100)
        btn2 = tkinter.Button(root, image=img2, command=self.button_downlo)
        btn2.place(x=0, y=200)
        btn3 = tkinter.Button(root, image=img3, command=self.button_uplo)
        btn3.place(x=0, y=300)
        btn4 = tkinter.Button(root, image=img4, command=self.button_delete)
        btn4.place(x=0, y=400)

        self.tftp = tftp
        tkinter.mainloop()

    # todo
    def check(self):
        # 发送 查看文件列表信号到服务端 服务端返回用\n作为分隔符的字符串
        self.tftp.sockfd.send(b"list")
        data = self.tftp.sockfd.recv(4096)
        print(data.decode())
        l = data.decode().split("\n")
        # 将接受到的文本使用listbox放置在窗口上
        listbox1 = tkinter.Listbox(self.root, selectmode="multiple", width=50, height=10,
                                   font=24)
        sb = tkinter.Scrollbar(self.root, orient='vertical',activebackground="#ff0000")
        listbox1['yscrollcommand'] = sb.set
        for i in range(len(l)):
            listbox1.insert(i, l[i])
        listbox1.place(x=525, y=0)
        sb.config(command=listbox1.yview)
        sb.place(x=655, y=0)

    # 当按下 下载功能键后 调用此方法
    def button_downlo(self):
        label = tkinter.Label(self.root, text="请输入要下载的文件名", fg="#0033ff")
        label.pack()
        # 设置接收用户输入的输入框
        self.entry_down = tkinter.Entry(self.root)
        self.entry_down.pack()
        btn = tkinter.Button(self.root, text="确认下载",
                             command=lambda: self.tftp.download(self.entry_down.get()))
        btn.pack()

    # 当按下主页面的上传键时 执行此方法
    def button_uplo(self):
        label = tkinter.Label(self.root, text="请输入要上传的文件名", fg="#0033ff")
        label.pack()
        self.entry_up = tkinter.Entry(self.root)
        self.entry_up.pack()
        # 当确认上传该文件时 调用函数
        btn = tkinter.Button(self.root, text="确认上传",
                             command=lambda: self.tftp.upload(self.entry_up.get()))
        btn.pack()

    # 按下删除功能键后
    def button_delete(self):
        label = tkinter.Label(self.root, text="请输入要删除的文件名", fg="#0033ff")
        label.pack()
        self.entry_del = tkinter.Entry(self.root)
        self.entry_del.pack()
        # 确认删除 调用删除方法
        btn = tkinter.Button(self.root, text="确认删除",
                             command=lambda:self.tftp.delete(self.entry_del.get()))
        btn.pack()


def main():
    # 如果无法连接服务器 则显示无法连接窗口
    try:
        tftp = TftpClient(ADDR)
    except ConnectionRefusedError:
        root0 = tkinter.Tk()
        root0.geometry("125x100+750+400")
        label = tkinter.Label(root0, text="服务器拒绝连接")
        label.pack()
        root0.mainloop()
        return

    root= tkinter.Tk()
    root.geometry("800x500")
    tk = tkinter_disk(tftp, root)
    root.mainloop()


if __name__ == "__main__":
    main()
