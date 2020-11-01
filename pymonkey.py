import socket
import os
import time

class mySocket():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(15)
        self.sock.connect((self.host, self.port))

    def checkOk(self, cmd):
        res = self.recv(4)
        print(str(cmd).replace("\n", "") + "==>", res.decode("utf-8").replace("\n", ""))
        return res

    def recv(self, num):
        return self.sock.recv(num)

    def _rec(self, size=4096):
        b = b""
        res = self.sock.recv(size)
        while res:
            b += res
            res = self.sock.recv(size)
        return b

    def _send(self, msg, ischeckok=False, isreconnect=False, isreturn=False):
        if type(msg) == type(""):
            b = bytearray(msg, 'utf-8')
        elif type(msg) == type(b''):
            b = msg
        else:
            return None
        self.sock.send(b)
        res = None
        if ischeckok:
            res = self.checkOk(msg)
        if isreturn:
            res = self._rec()
        if isreconnect:
            self.connect()
        return res

    def close(self):
        self.sock.close()

class adbClient(mySocket):
    def __init__(self):
        try:
            super().__init__(host = "localhost",port=5037)
        except:
            os.popen("adb devices")
            time.sleep(1)
            self.connect()

    def adbSend(self,msg,ischeckok = False,isreconnect=False,isreturn=False):
        b = bytearray(msg, 'utf-8')
        msg = b'%04x%s'%(len(b),b)
        return self._send(msg,ischeckok = ischeckok,isreconnect=isreconnect,isreturn=isreturn)

    def getDevice(self,sn):
        d = device()
        self.adbSend("host:devices-l", isreconnect=True)
        if self.adbSend("host:transport:%s" % (sn), ischeckok=True) == b"FAIL":
            os.popen("adb connect %s" % (sn))
            time.sleep(1)
            self.adbSend("host:transport:%s" % (sn), ischeckok=True)
        d.adbsk = self
        d.name = sn
        return d


class device():
    def __init__(self):
        self.adbsk = adbClient()
        self.name = ''

    def recon(self):
        self.adbsk.close()
        self.adbsk.connect()

    def createforward(self,localport,remoteport):
        self.resetDevice()
        self.adbsk.adbSend("host-serial:%s:forward:tcp:%d;tcp:%d"%(self.name,localport,remoteport),ischeckok=True)

    def resetDevice(self):
        self.adbsk.adbSend("host:devices-l", isreconnect=True)
        self.adbsk.adbSend("host:transport:%s" % (self.name), ischeckok=True)

    def shell(self, cmd, reset=True):
        self.resetDevice()
        re = self.adbsk.adbSend("shell:%s" % (cmd), ischeckok=True ,isreturn=True)
        if reset:
            self.resetDevice()
        return re

class monkeyClient(mySocket):
    def __init__(self,sn,port = 12345,adbsk = adbClient()):
        self.name = sn
        self.adbsk = adbsk
        self.mkport = port
        self.preset()
        super().__init__(host = "localhost",port=port)
        time.sleep(0.2)
        self.wake()

    def __del__(self):
        try:
            self.quit()
            os.system("adb disconnect %s" % (self.name))
        except:
            pass

    def preset(self):
        self.adbsk.getDevice(self.name).createforward(self.mkport,self.mkport)
        os.popen("adb -s %s shell monkey --port %d"%(self.name,self.mkport))
        time.sleep(1)

    def mkSend(self,msg):
        self._send(msg+"\n",ischeckok=True)

    def wake(self):
        self.mkSend("wake")

    def quit(self):
        self.mkSend("quit")

    def tap(self,x,y):
        self.mkSend("tap %d %d" % (x, y))

    def type(self,msg):
        self.mkSend("type %s"%(msg))

    def touch_move(self,x,y):
        self.mkSend("touch move %d %d"%(x,y))

    def touch_up(self,x,y):
        self.mkSend("touch up %d %d"%(x,y))

    def touch_down(self,x,y):
        self.mkSend("touch down %d %d"%(x,y))
 
class viewClient(mySocket):
    def __init__(self,sn,port=4939,adbsk = adbClient()):
        self.name = sn
        self.adbsk = adbsk
        self.port = port
        self.preset()
        super().__init__("localhost",port)

    def startViewServer(self):
        return self.adbsk.getDevice(self.name).shell("service call window 1 i32 %d"%(self.port))

    def stopViewServer(self):
        return self.adbsk.getDevice(self.name).shell("service call window 2 i32 %d" % (self.port))

    def checkViewServer(self):
        return self.adbsk.getDevice(self.name).shell("service call window 3")

    def preset(self):
        self.startViewServer()
        self.adbsk.getDevice(self.name).createforward(self.port,self.port)
        time.sleep(0.2)

    def viewSend(self,msg):
        return self._send(msg+"\n",isreturn=True,isreconnect=True)
