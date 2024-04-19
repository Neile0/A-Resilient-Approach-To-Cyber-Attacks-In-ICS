import time

def try_receive(self, tag, ip_tag):
    tries = 0
    while tries < 100:
        try:
            value = self.receive(tag, f"192.168.1.{self.get(ip_tag)}")
            time.sleep(0.1)
            return value
        except OSError as e:
            print(f"DEBUG OS Error in try receive: {e}")
            tries += 1
        except Exception as e:
            print(f"DEBUG Error in try receive: {e}")
            tries += 1
    return None

def try_send(self, tag, value, ip_tag):
    tries = 0
    while tries < 100:
        try:
            self.send(tag, value, f"192.168.1.{self.get(ip_tag)}")
            return True
        except OSError as e:
            print(f"DEBUG OS Error in try receive: {e}")
            tries += 1
        except Exception as e:
            print(f"DEBUG Error in try receive: {e}")
            tries += 1
    return False