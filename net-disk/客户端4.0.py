import tkinter
from socket import *
import sys, os
from time import sleep
from setting import *
from gui import *
from do_connect import *

def main():
    # 如果无法连接服务器 则显示无法连接窗口
    try:
        tftp = login_server(ADDR)
    except ConnectionRefusedError:
        root0 = tkinter.Tk()
        root0.geometry("125x100+750+400")
        label = tkinter.Label(root0, text="服务器拒绝连接")
        label.pack()
        root0.mainloop()
        return

    gui1 = connect_sever(tftp)
    gui1.mainloop()

if __name__ == "__main__":
    main()