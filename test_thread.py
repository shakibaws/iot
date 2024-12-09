import threading
import time

class CustomExcpetion(Exception):
    pass

def th_fun(timer):
    while True:
        time.sleep(timer)
        raise CustomExcpetion(f"Error from timer: {timer}")

try:
    t1=threading.Thread(target=th_fun, args=[10,])
    t2=threading.Thread(target=th_fun, args=[1,])
    t3=threading.Thread(target=th_fun, args=[2,])
    t4=threading.Thread(target=th_fun, args=[3,])
    t5=threading.Thread(target=th_fun, args=[5,])
except CustomExcpetion as e:
    print(e)
    
t1.start()
t2.start()
t3.start()
t4.start()
t5.start()

t1.join()
t2.join()
t3.join()
t4.join()
t5.join()