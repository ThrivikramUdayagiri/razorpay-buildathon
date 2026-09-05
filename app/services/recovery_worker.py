import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.recovery import RecoveryAttempt
from app.models.audit import NotificationEvent
from app.services.audit_service import AuditService
from app.integrations import get_razorpay_adapter

import random
from app.demo_state import demo_state

class BackgroundRecoveryWorker:
    def __init__(self):
        self.is_running = False
        self.task = None

    async def start(self):
        self.is_running = True
        self.task = asyncio.create_task(self.poll_loop())
        print("Live Interactive Demo Worker started.")

    async def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
        print("Live Interactive Demo Worker stopped.")

    async def poll_loop(self):
        while self.is_running:
            try:
                self._process_demo_users()
            except Exception as e:
                print(f"Error in Demo Worker: {e}")
            
            # Fast polling for snappy UI updates during presentation
            await asyncio.sleep(2)

    def _process_demo_users(self):
        # Get pending users (gray)
        pending = [u for u in demo_state.users if u.color_state == "gray"]
        if not pending:
            return

        # Sort by amount (process smaller amounts first as probes)
        pending.sort(key=lambda x: x.amount)

        # Process a small batch to make it look sequential and organic
        batch = pending[:2]
        
        current_prob = demo_state.global_probability

        for user in batch:
            # Adjust probability based on amount
            adjusted_prob = current_prob
            if user.amount < 1000:
                adjusted_prob += 10 # small amounts easier
            else:
                adjusted_prob -= 15 # large amounts harder

            roll = random.randint(1, 100)
            
            if roll <= adjusted_prob:
                if user.engine_type == "autopay":
                    # AutoPay Success
                    user.color_state = "green"
                    current_prob += 5 
                elif user.engine_type == "checkout":
                    # Good probability -> Link Sent!
                    user.color_state = "yellow"
                    current_prob += 2
            else:
                if user.engine_type == "autopay":
                    # AutoPay Failure
                    user.retry_count += 1
                    if user.retry_count >= user.max_retries:
                        user.color_state = "yellow" # Manual action needed
                    current_prob -= 5
                elif user.engine_type == "checkout":
                    # Bad probability -> Do not send link yet, wait.
                    current_prob -= 2

# Singleton instance
recovery_worker = BackgroundRecoveryWorker()
