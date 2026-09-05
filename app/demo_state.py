import random
from typing import List, Dict, Any

class DemoUser:
    def __init__(self, id: int, name: str, amount: float, engine_type: str):
        self.id = id
        self.name = name
        self.amount = amount
        self.engine_type = engine_type  # "autopay" or "checkout"
        
        # States: "gray" (pending/link sent), "yellow" (action required), "green" (success), "red" (failed/declined)
        self.color_state = "gray" 
        
        self.retry_count = 0
        self.max_retries = 3

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "engine_type": self.engine_type,
            "color_state": self.color_state,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }

class DemoStateManager:
    def __init__(self):
        self.global_probability = 50  # 0 to 100
        self.users: List[DemoUser] = []
        self._initialize_users()

    def _initialize_users(self):
        self.users = []
        names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"]
        
        # 10 AutoPay Users
        for i in range(10):
            self.users.append(DemoUser(
                id=i+1, 
                name=f"Transaction {i+1} (Sub)", 
                amount=random.choice([299.0, 499.0, 999.0, 1999.0, 4999.0]),
                engine_type="autopay"
            ))
            
        # 10 Checkout Users
        for i in range(10):
            u = DemoUser(
                id=i+11, 
                name=f"Transaction {i+1} (Individual Payer)", 
                amount=random.choice([150.0, 800.0, 1200.0, 3500.0, 8000.0]),
                engine_type="checkout"
            )
            # They start as gray (waiting for good probability to send link)
            self.users.append(u)

    def get_state(self) -> Dict[str, Any]:
        return {
            "global_probability": self.global_probability,
            "autopay_users": [u.to_dict() for u in self.users if u.engine_type == "autopay"],
            "checkout_users": [u.to_dict() for u in self.users if u.engine_type == "checkout"]
        }

    def set_probability(self, prob: int):
        self.global_probability = max(0, min(100, prob))

    def user_action(self, user_id: int, action: str):
        user = next((u for u in self.users if u.id == user_id), None)
        if not user:
            return False
            
        if action == "pay":
            roll = random.randint(1, 100)
            
            if user.engine_type == "autopay":
                # Alternate method has fixed 90% success
                adjusted_prob = 90
            else:
                # Checkout link relies on bank server probability
                adjusted_prob = self.global_probability
                if user.amount < 1000:
                    adjusted_prob += 10
                else:
                    adjusted_prob -= 15
                
            if roll <= adjusted_prob:
                user.color_state = "green"
                self.global_probability = min(100, self.global_probability + 5)
            else:
                # Manual payment failed, goes straight to red
                user.color_state = "red"
                self.global_probability = max(0, self.global_probability - 2)
        elif action in ["decline", "cancel"]:
            user.color_state = "red"
            
        return True
        
    def reset(self):
        self._initialize_users()
        self.global_probability = 50

# Singleton instance
demo_state = DemoStateManager()
