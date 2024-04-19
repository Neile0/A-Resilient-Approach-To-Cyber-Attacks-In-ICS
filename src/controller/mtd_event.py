from ryu.controller import event

import datetime

class MTDEvent(event.EventBase):
    def __init__(self, message):
        print(f"MTD Event at {datetime.datetime.now()}")
        super(MTDEvent, self).__init__()
        self.msg = message
