import pyautogui
import time
c = 0
while True:
    for i in range(0,100):
        try:
            pyautogui.moveTo(1000,i*10)
            c= c+1
            print(c)
            time.sleep(5)
        except:
            continue
