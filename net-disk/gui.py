from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from threading import Thread
from multiprocessing import Process,Queue
from setting import ADDR


class connect_sever(Tk):

    def __init__(self, conn):
        super(connect_sever, self).__init__()
        self.geometry("375x200+750+400")
        label1 = Label(self, text="守得云开见月明", font=('Helvetica', '14', 'bold'))
        label1.place(x=110, y=15)
        label2 = Label(self, text="登录名", font=('Helvetica', '14', 'bold'))
        label2.place(x=20, y=50)
        label3 = Label(self, text="密码", font=('Helvetica', '14', 'bold'))
        label3.place(x=25, y=100)
        entry1 = Entry(self, highlightcolor='red', width=30)
        entry1.place(x=90, y=50)
        entry2 = Entry(self, highlightcolor='red', width=30, show='*')
        entry2.place(x=90, y=100)
        button1 = Button(self, text="登录", width=8, height=1,
                         font=('Helvetica', '14', 'bold'),
                         command=lambda : conn.login(self, entry1.get(),entry2.get()))
        button1.place(x=220, y=130)
        button1 = Button(self, text="注册", width=8, height=1,
                         font=('Helvetica', '14', 'bold'),
                         command=lambda : conn.register(self, entry1.get(), entry2.get()))
        button1.place(x=70, y=130)


class net_disk(Tk):
    def __init__(self, TftpClient):
        super(net_disk, self).__init__()
        self.geometry("600x350+700+200")
        self.TftpClient = TftpClient
        self.tftp = TftpClient(ADDR)
        self.check_list()
        self.left_up()
        self.right_download()

    def check_list(self):
        self.label = Label(self, text="云上的日子你我共享", font=('Helvetica', '14', 'bold'),
                      width=25,height=1, fg="purple")
        self.label.place(x=170,y=10)
        self.tftp.sockfd.send(b"list")
        data = self.tftp.sockfd.recv(4096)
        print(data.decode())
        l = data.decode().split("\n")
        # 将接受到的文本使用listbox放置在窗口上
        self.listbox1 = Listbox(self, selectmode="multiple", width=25, height=9,
                           font=24)
        try:
            self.sb.destroy()
        except Exception as e:
            pass
        self.sb = Scrollbar(self, orient='vertical',activebackground="#ff0000")
        self.listbox1['yscrollcommand'] = self.sb.set
        for i in range(len(l)):
            self.listbox1.insert(i, l[i])
            self.listbox1.place(x=185, y=50)
        self.sb.config(command=self.listbox1.yview)
        self.sb.pack(side=RIGHT, fill=Y)
        # sb.place(x=405, y=50)
        #  绑定函数
        self.button = Button(self,text="刷新文件列表", width=20, height=1,
                        font=('Helvetica', '14', 'bold'), command=self.check_list)
        self.button.place(x=185, y=300)

    def left_up(self):

        label = Label(self, text="上传文件", font=('Helvetica', '14', 'bold'),
                      width=15, fg="brown")
        label.place(x=15, y=20)
        entry1 = Entry(self, width=20)
        entry1.place(x=20, y=60)
        label = Label(self, text="上传进度", font=('Helvetica', '14', 'bold'),
                      width=15, fg="brown")
        label.place(x=15, y=90)
        prb = ttk.Progressbar(self, length=145)
        prb.place(x=20, y=130)

        # todo command 绑定
        button = Button(self, text="确认上传", width=12, height=1,
                        font=('Helvetica', '14', 'bold'),
                        command=lambda: self.up_file(entry1.get()))
        button.place(x=20, y=160)
        label = Label(self, text="删除文件", font=('Helvetica', '14', 'bold'),
                      width=15, fg="brown")
        label.place(x=15, y=210)
        entry1 = Entry(self, width=20)
        entry1.place(x=20, y=240)

        # todo command 绑定
        button = Button(self, text="确认删除", width=12, height=1,
                        font=('Helvetica', '14', 'bold'),
                        command=lambda: self.del_file(entry1.get()))
        button.place(x=20, y=290)

    def right_download(self):
        label = Label(self, text="下载文件", font=('Helvetica', '14', 'bold'),
                      width=15, fg="brown")
        label.place(x=430, y=20)
        entry1 = Entry(self, width=20)
        entry1.place(x=430, y=60)
        label = Label(self, text="下载进度", font=('Helvetica', '14', 'bold'),
                      width=14, fg="brown")
        label.place(x=435, y=90)
        prb = ttk.Progressbar(self, length=145)
        prb.place(x=430, y=130)
        # todo command 绑定
        button = Button(self, text="确认下载", width=12, height=1,
                        font=('Helvetica', '14', 'bold'),
                        command=lambda: self.down_file(entry1.get()))
        button.place(x=430, y=160)
        label = Label(self, text="本地文件目录\n桌面下网盘文件",
                      font=('Helvetica', '14', 'bold'),
                      width=14, fg="brown")
        label.place(x=435, y=220)
        # todo command 绑定
        button = Button(self, text="打开目录", width=12, height=1,
                        font=('Helvetica', '14', 'bold'),
                        command=self.second_gui)
        button.place(x=435, y=290)

    def second_gui(self):
        t = Thread(target=open_file)
        t.start()
        t.join()

    def open_file(self):
        root0 = Tk()
        root0.geometry("0x0+0+0")
        fd = filedialog.LoadFileDialog(root0)
        # 创建打开文件对话框
        filename = fd.go("/home/tarena/桌面/网盘文件")
        print(filename)
        root0.mainloop()


    def up_file(self, name):
        if "tftpclient1" in dir(self):
            print(dir(self))
            return
        elif not name:
            return
        self.tftpclient1 = self.TftpClient(ADDR)
        pro1 = Process(target=self.tftpclient1.upload,args=(name,))
        pro1.start()
        pro1.join()
        del self.tftpclient1

    def down_file(self, name):
        if "tftpclient2" in dir(self):
            return
        elif not name:
            return
        self.tftpclient2 = self.TftpClient(ADDR)
        pro2 = Process(target=self.tftpclient2.download, args=(name,))
        pro2.start()
        pro2.join()
        del self.tftpclient2

    def del_file(self, name):
        self.tftp.delete(name)


def open_file():
    root0 = Tk()
    root0.geometry("0x0+20+20")
    fd = filedialog.LoadFileDialog(root0)
    # 创建打开文件对话框
    filename = fd.go("/home/tarena/桌面/网盘文件")
    print(filename)
    root0.mainloop()

