# -*- coding: utf-8 -*-
from socket import *
from shutil import rmtree
import os, sys
import signal
import time
from pythonmysql import MysqlPython

# 文件库的路径
FILE_PATH = "/home/tarena/个人网盘云/"


# 实现功能模块
class TftpServ(object):
    # 设置和客户端连接的套接字
    def __init__(self, connfd):
        self.connfd = connfd

    @staticmethod
    def calculate(num):
        num1 = 0
        num2 = num
        if num > 262144:
            num1 = num // 20
            num2 = num // 20 + num % 20
        return num1, num2

    def get_file(self, file, num, way):
        try:

            num1, num2 = self.calculate(num)
            with open('{}'.format(file), way) as f:
                # 在接收大文件时 data拼接数据可能会非常巨大 于是可以分成几次接收拼接并写入
                # 创建一个变量 将接收到的信息连接起来 防止出现汉字被切割 出现解码错误
                for i in range(20):
                    data = b""
                    if i == 19:
                        num1 = num2
                    while num1:
                        num1 -= 1
                        line = self.connfd.recv(4096)
                        data += line
                    if way == "w":
                        f.write(data.decode())
                    else:
                        f.write(data)
                    # 发送提示信息到客户端 表示已经接收完毕 可以接受下一个文件
                self.connfd.send(b"OK")
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
                        line = self.connfd.recv(4096)
                        data += line
                    if way == "w":
                        f.write(data.decode())
                    else:
                        f.write(data)
                self.connfd.send(b"OK")
        except Exception as e:
            print("不可预知的错误发生了", e)

    def get_dirctory(self, file):
        # 如果 此文件夹不存在 则创建
        if not os.path.isdir(file):
            os.makedirs(file)
        while True:
            try:
                data = self.connfd.recv(1024)
                print(data)
                line = data.decode()
                if line == "over":
                    print(line)
                    break
                elif line[:6] == "wenben":
                    print(line)
                    # 获取 此文件的大小
                    size = self.connfd.recv(1024).decode()
                    # 计算出真正要接受的次数
                    num = (int(size)+4095) // 4096
                    self.get_file(FILE_PATH + line[27:], num, "w")
                elif line[:6] == "erjinz":
                    print(line)
                    # 获取 此文件的大小
                    size = self.connfd.recv(1024).decode()
                    num = (int(size) + 4095) // 4096
                    self.get_file(FILE_PATH + line[27:], num, "wb")
                elif line[:6] == "dictor":
                    print(line)
                    if os.path.isdir(FILE_PATH + line[27:]):
                        print("这是一个已存在的文件夹")
                        continue
                    os.makedirs(FILE_PATH + line[27:])
                else:
                    print(line)
            except UnicodeDecodeError as e:
                print("大哥 文件夹接收又出错了 快改改", e)

    # 接收 客户端上传的文件
    def get_upload(self, name):
        try:
            file = FILE_PATH + name
            # 以 x 方式打开客户端要上传的文件名 如果有会抛出一个错误
            if os.path.isdir(file) or os.path.isfile(file):
                raise FileExistsError("有文件了大哥")
            # 若创建该空文件成功 发送 Right 信号 表示可以上传
            self.connfd.send(b"Right")
            data = self.connfd.recv(1024).decode()
            # 接收到客户端发来的 wenben信号 以文本文件格式接收并写入
            if data[:6] == "wenben":
                num = (int(data[6:]) + 4095) // 4096
                self.get_file(file, num, "w")
            # 若接收到客户端发来的 erjinzhi 信号 , 以二进制格式接收并写入
            elif data[:6] == "erjinz":
                num = (int(data[6:]) + 4095) // 4096
                self.get_file(file, num, "wb")
            elif data[:6] == "dictor":
                self.get_dirctory(file)
        # 当服务端本地有此文件时 也即 以x 文件时创建新文件时和本地文件重名 抛出此错误
        except FileExistsError as e:
            # 通知 客户端 此文件已经存在
            self.connfd.send(b"Error")
            print("重名文件上传失败",e)
            return
        # 接收其他未预知的错误
        except Exception as e:
            print("不可预知的错误发生", e)

    def send_download(self,file):
        if os.path.isfile(FILE_PATH + file):
            # 判断 客户端请求的文件类型 并根据文件类型 发送对应信号给客户端
            try:
                # 尝试以文本文件打开文件 并读取一行内容
                with open(FILE_PATH + file) as f:
                    f.readline()
                    print("默认文本文件打开成功")
                self.send_download_file(file, True)
            # 以默认文本文件打开失败 作为二进制的文件处理
            except UnicodeDecodeError as e:
                print("发送二进制文件", e)
                self.send_download_file(file, False)
            except Exception as e:
                print(e)
                print("暂时不能识别的文件")
        elif os.path.isdir(FILE_PATH + file):
            self.connfd.send("dir".encode())
            self.send_dictory(FILE_PATH + file)
            time.sleep(0.1)
            self.connfd.send("over".encode())
        else:
            self.Nofile()
            print("没有此文件")

    # 发送服务端文件至客户端
    def send_download_file(self, name, boolean):
        if boolean:
            # 此方法 发送 wenben 信号到客户端  并以文本文件格式发
            self.connfd.send(b"wenben")
        else:
            self.connfd.send(b"erjinz")
        file = FILE_PATH + name
        # 睡眠0.1秒 以等待客户端创建文件 协调收发读写速度
        time.sleep(0.1)
        size = os.path.getsize(file)
        self.connfd.send(str(size).encode())
        time.sleep(0.1)
        try:
            with open("{}".format(file),"rb") as f:
                self.send_file(f)
                print("发送成功")
        except Exception as e:
            print(e)

    # 以文本方式发送
    def send_file(self, f):
        while True:
            # 从 文件中固定读取4096个字节
            data = f.read(4096)
            if not data:
                break
            self.connfd.sendall(data)
        # 在这里阻塞 当客户端接收完毕之后会发送 OK 到服务端  提醒服务端可以发送下一个文件
        data = self.connfd.recv(128).decode()
        if data == "OK":
            time.sleep(0.01)

    # 递归发送文件夹下的所有文件以及文件夹  发送顺序类似 深度优先
    def send_dictory(self, filename):
        # 将文件夹下的文件及文件夹名列表用list绑定
        list = os.listdir(filename)
        print(list)
        # 每个文件夹后加上一个斜杠 当递归打开子文件夹时 避免子文件夹名和子文件夹下的文件名粘连
        file = filename + "/"
        # 循环发送文件夹下的所有文件及文件夹
        try:
            for i in list:
                # 判断该路径名是否为文件
                if os.path.isfile(file + i):
                    try:
                        # 试着以普通文本文件打开此文件 若错误 则会跳到下面的二进制发送
                        with open(file + i) as f:
                            f.readline()
                        with open(file + i, "rb") as f:
                            # 发送"wenben"+文件名到客户端 提醒客户端 这是一个文本文件 以文本方式接收
                            self.connfd.send(("wenben" + file + i).encode())
                            time.sleep(0.1)
                            # 获取文件大小 发送给客户端 客户端则知道要循环接收多少次
                            size = os.path.getsize(file + i)
                            self.connfd.send(str(size).encode())
                            # 睡眠0.3秒 防止发送的文件信息和文件大小粘包
                            time.sleep(0.1)
                            # 调用发送文本方法
                            self.send_file(f)
                            print(i + "wenben发送完毕")
                    except UnicodeDecodeError:
                        with open(file + i, "rb") as f:
                            self.connfd.send(("erjinz" + file + i).encode())
                            time.sleep(0.1)
                            size = os.path.getsize(file + i)
                            self.connfd.send(str(size).encode())
                            time.sleep(0.1)
                            self.send_file(f)
                            print(i + "erjinzhi发送完毕")
                elif os.path.isdir(file + i):
                    time.sleep(0.1)
                    self.connfd.send(("dictor" + file + i).encode())
                    self.send_dictory(file + i)
        except ConnectionResetError as e:
            print(e)

    # 发送云端文件列表给客户端
    def check_list(self):
        self.connfd.send("\n".join(os.listdir(FILE_PATH)).encode())

    # 发送None 信号 告知客户端
    def Nofile(self):
        self.connfd.send(b"None")

    # 当接收到客户端的del 命令时 执行该方法
    def del_file(self, name):
        file = FILE_PATH + name
        if os.path.isfile(file):
            try:
                # 判断文件成功 删除该文件
                os.remove(file)
                print("删除文件:", file)
                self.connfd.send("删除成功".encode())
            # 权限不够 删除失败
            except PermissionError as e:
                print("没有权限访问", e)
                self.connfd.send("删除失败".encode())
            except Exception as e:
                print("删除文件时出错")
                self.connfd.send("删除失败".encode())
        elif os.path.isdir(file):
            try:
                # 调用rmtree 删除文件夹
                rmtree(file)
                self.connfd.send("删除成功".encode())
            except:
                print("删除失败")
                self.connfd.send("删除失败".encode())

    # @staticmethod
    # def do_sql(self, fn):
    #     def fx(data):
    #         mysql = MysqlPython("diskuser")
    #         data = data.split("##")
    #         fn(mysql,data)
    #     return fx

    # @do_sql
    def login_user(self, data):
        print("sql start")
        mysql = MysqlPython("diskuser")
        data = data.split("##")
        print(*data)
        sql = "select id from users where name={} and upwd={}".format(*data)
        result = mysql.select_all(sql)
        print(result)
        if result:
            self.connfd.send("YES".encode())
        else:
            self.connfd.send("NO".encode())
        print("sql over")

    # @do_sql
    def register_user(self,data):
        mysql = MysqlPython("diskuser")
        data = data.split("##")
        sql = "insert into users(name, upwd) values({},{})".format(*data)
        result = mysql.zhixing(sql)
        if result:
            self.connfd.send("YES".encode())
        else:
            self.connfd.send("NO".encode())



# 流程控制, 创建套接字, 创建开发, 方法调用
def main():

    HOST = "0.0.0.0"
    PORT = 8888
    ADDR = (HOST, PORT)
    # 创建套接字 设置端口可立即重用 设置超时检测 绑定地址
    sockfd = socket()
    sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # sockfd.settimeout(3)
    sockfd.bind(ADDR)
    sockfd.listen(10)
    # 忽略子进程发来的信号 让系统进程处理子进程的退出 防止僵尸进程的发生
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    print("Parent process wait connect")
    # 创建类对象
    while True:
        # 接收 客户端连接 无客户端连接时 阻塞在此处
        try:
            connfd, addr = sockfd.accept()
        # ctrl + c 主动退出程序时
        except KeyboardInterrupt:
            sockfd.close()
            sys.exit("服务器退出")
        except Exception as e:
            print(e)
            continue
        print("客户端登录", addr)
        #　创建父子进程
        pid = os.fork()
        if pid == 0:
            sockfd.close()
            # 创建和客户端连接的套接字对象
            tftp = TftpServ(connfd)
            while True:
                # 开始等待接收 客户端命令
                data = connfd.recv(1024)
                print(data)
                data = data.decode()
                if data == "list":
                    tftp.check_list()
                # 接收到下载命令 调用下载方法
                elif data[:3] == "get":
                    tftp.send_download(data[3:])
                # 接收到上传命令 调用上传方法
                elif data[:3] == "put":
                    tftp.get_upload(data[3:])
                elif data[:3] == "del":
                    tftp.del_file(data[3:])
                elif data[:3] == "log":
                    tftp.login_user(data[3:])
                    print("log")
                elif data[:3] =="reg":
                    tftp.register_user(data[3:])
                # 客户端断开连接 退出子进程
                elif not data:
                    print("客户端退出")
                    sys.exit(0)
                else:
                    print("客户端发送错误指令")
        # 在父进程里关闭该客户端的套接字 并进行下一次循环 创建子进程失败时也关闭套接字
        else:
            connfd.close()
            continue

if __name__ == '__main__':
    main()

