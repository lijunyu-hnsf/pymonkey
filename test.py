from pymonkey import monkeyClient

if __name__=="__main__":
    demo = monkeyClient("192.168.1.23:5555")#这里具体填你自己的设备，具体看adb devices
    demo.touch_down(100, 100)
    demo.touch_up(100, 100)