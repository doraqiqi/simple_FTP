# Author：zhaoyanqi

import socket
import struct
import json
import os

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"download")
UP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"up")
print(DOWNLOAD_DIR)

class FtpClient:
    def __init__(self,host,port):
        self.host=host
        self.port=port
        self.client=socket.socket()
        self.client.connect((self.host,self.port))

    def interactive(self):

        if self.login():
            while True:
                data = input(">>:").strip()
                if not data:continue
                params = data.split()
                cmd = params[0] #提取代码的命令部分
                if hasattr(self,cmd): #判断是否有这个命令
                    func = getattr(self,cmd) #运行本对象里的cmd这个变量代表命令同名的方法
                    func(params)
        else:
            print('用户名或密码错')


    def get(self,params):
        '''
        下载模块
        :param params:
        :return:
        '''
        params_json = json.dumps(params)
        self.client.send(params_json.encode('utf-8'))#把命令用json打包，编码成byte后发送

        #接受报头的长度
        struct_recv = self.client.recv(4)#接收struct包
        header_size = struct.unpack('i',struct_recv)[0]#解struct包，获取报头的长度

        #接收报头
        header_byte = self.client.recv(header_size)#通过报头的长度接收报头
        header_json = header_byte.decode('utf-8')#把报头传来的jason文件解码
        header = json.loads(header_json)#把json文件装载进来获取报头原格式
        filename = header['filename'] #获取文件名
        filesize = header['filesize'] #获取文件大小
        filepath = os.path.join(DOWNLOAD_DIR,filename) #获取文件路径

        #接受文件
        with open(filepath,'wb') as f:
            recv_size = 0
            while recv_size < filesize:
                line = self.client.recv(1024)
                f.write(line)
                recv_size += len(line)
            print('Download seccessful')

    def put(self,params):
        '''
        上传模块
        :param params:
        :return:
        '''
        #print(params) #['up','16.mp4']

        params_json = json.dumps(params)
        params_json_byte = params_json.encode('utf-8')
        #print(params_json_byte)
        self.client.send(params_json_byte)#把命令用json打包，编码成byte后发送

        filename = params[1]
        filepath = os.path.join(UP_DIR,filename)
        #print('filepath',filepath)
        if os.path.exists(filepath):
            #先要发送这个文件存在的信息
            self.client.send(b'1')
            #制作报头
            data_dic = {
                'filename':filename,
                'filesize':os.path.getsize(filepath),
            }
            data_dic_json = json.dumps(data_dic)
            data_dic_json_byte = data_dic_json.encode('utf-8')
            #print('报头制作完了')

            #用struct打包报头并发送
            data_dic_json_byte_struct = struct.pack('i',len(data_dic_json_byte))
            self.client.send(data_dic_json_byte_struct)
            #print('struct发送完了')

            #发送报头
            self.client.send(data_dic_json_byte)
            #print('报头发送完了')

            #发送数据
            with open(filepath,'rb') as f:
                for line in f:
                    self.client.send(line)
            print('put seccessful')

        else:
            print("File not exists")
            self.client.send(b'0')
            return


    def login(self):
        #输入用户名密码并发送
        username = input('请输入你的用户名:').strip()
        password = input('请输入你的密码:').strip()
        identify_list = [username,password]
        identify_list_json = json.dumps(identify_list)
        identify_list_json_byte = identify_list_json.encode('utf-8')
        identify_list_json_byte_struct = struct.pack('i',len(identify_list_json_byte))
        self.client.send(identify_list_json_byte_struct)
        self.client.send(identify_list_json_byte)

        #接收回复信息
        recive = self.client.recv(1)
        return recive


    def ls(self,params):
        params_json = json.dumps(params)
        self.client.send(params_json.encode('utf-8'))#把命令用json打包，编码成byte后发送

        data_json_byte = self.client.recv(1024)
        data = json.loads(data_json_byte.decode('utf-8'))
        for item in data:
            print(item,end=' ')
        print()



if __name__ == '__main__':
    client_Ftp = FtpClient('127.0.0.1',8089)
    client_Ftp.interactive()







