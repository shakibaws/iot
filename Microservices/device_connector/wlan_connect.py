from wifi_manager import WifiManager
import utime

# Example of usage

class Connector:
    def __init__(self):
        self.wm = WifiManager()
    
    def connect(self):
        self.wm.connect()
        print("...")
        print("Connected")
        return self.isconnected()
    
    def isconnected(self):
        return self.wm.is_connected()
