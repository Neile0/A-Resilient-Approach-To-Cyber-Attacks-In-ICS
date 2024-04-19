from ryu.controller import event


class AttackDetectedEvent(event.EventBase):
    def __init__(self, target_ip):
        print(f"Attack against {target_ip}")
        super(AttackDetectedEvent, self).__init__()
        self.target = target_ip
