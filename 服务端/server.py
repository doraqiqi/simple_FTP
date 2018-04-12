# Author：zhaoyanqi
import socket
import os
import json
import struct
from os import listdir

SHARE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"share")
print(SHARE_DIR)

class FtpServer:
    def __init__(self,host,port):
        self.host=host
        self.port=port
        self.server=socket.socket()
        self.server.bind((self.host,self.port))
        self.server.listen(5)

    def serve_connect(self):
        print('server starting...')
        while True:
            self.conn,self.client_addr = self.server.accept()
            print(self.client_addr)

            username,password = self.login_info()
            if self.identify(username,password):

                while True:
                    try:#防止客户端断开，服务端报错
                        data = self.conn.recv(1024)
                        if not data:break
                        print("命令接受成功",data)
                        params = json.loads(data.decode('utf-8'))
                        cmd = params[0]
                        if hasattr(self,cmd):
                            func = getattr(self,cmd)
                            func(params,username)
                        else:
                            print('cmd not exists')
                    except ConnectionResetError:
                        break
                self.conn.close()
            self.conn.close()
        self.server.close()

    def ls(self,params,username):
        if len(params)>1:
            msg = "ls命令使用方式错误"
            msg_json = json.dumps(msg)
            msg_json_byte = msg_json.encode('utf-8')
            self.conn.send(msg_json_byte)
        else:
            user_path = os.path.join(SHARE_DIR,username)
            user_file_list = listdir(user_path)
            user_file_list_json = json.dumps(user_file_list)
            user_file_list_json_byte = user_file_list_json.encode('utf-8')
            self.conn.send(user_file_list_json_byte)


    def get(self,params,username):
        filename = params[1]
        print()
        filepath = os.path.join(SHARE_DIR,username,filename)
        if os.path.exists(filepath):#如果这个文件存在
            #就开始制作报头
            headers = {
                'filename':filename,
                'filesize':os.path.getsize(filepath),
            }
            headers_jason = json.dumps(headers)#用jason打包这个报头
            header_bytes = headers_jason.encode('utf-8')#把他编码成bytes

            #然后开始把这个报头报头长度用struct模块打包成4字节的一个头文件
            struct_packet = struct.pack('i',len(header_bytes))
            self.conn.send(struct_packet)

            #客户端通过struct_packet知道了报头的长度，那就开始发送报头
            self.conn.send(header_bytes)

            #客户端通过报头知道了文件名和文件大小，那就开始传文件
            with open(filepath,'rb') as f:
                for line in f:
                    self.conn.send(line)

    def put(self,params,username):
        #接受存在信息
        exsit_info = self.conn.recv(1)
        if exsit_info == b'1':
            #接收struct，获取报头大小
            struct_recv = self.conn.recv(4)
            header_size = struct.unpack('i',struct_recv)[0]
            print('报头大小',header_size)

            #接收报头,获取文件大小
            header_json_byte = self.conn.recv(header_size)
            print('header_json_byte',header_json_byte)
            header_json = header_json_byte.decode('utf-8')
            header = json.loads(header_json)
            print('报头',header)
            filename = header['filename']
            filepath = os.path.join(SHARE_DIR,username,filename)
            filesize = header['filesize']
            #接收文件
            with open(filepath,'wb') as f:
                data_size = 0
                while data_size < filesize:
                    line = self.conn.recv(1024)
                    f.write(line)
                    data_size += len(line)
                else:
                    print("up data seccessful！")

    def login_info(self):

        #接收struct 获取认证信息大小
        identify_json_byte_struct = self.conn.recv(4)
        identify_json_byte_size = identify_json_byte_struct[0]

        #接收identify信息
        identify_json_byte = self.conn.recv(identify_json_byte_size)
        identify_json = identify_json_byte.decode('utf-8')
        identify_list = json.loads(identify_json)
        print(identify_list)
        username = identify_list[0]
        password = identify_list[1]
        return username,password

    def identify(self,username,password):
        #验证identify信息
        with open('config','r') as f:
            user_dic = json.loads(f.read())
        print(user_dic)
        if username in user_dic and password == user_dic[username]['password']:
            self.conn.send(bytes(1))
            return True
        else:
            self.conn.send(bytes(0))
            return False







if __name__ == '__main__':
    server = FtpServer('127.0.0.1',8089)
    server.serve_connect()

