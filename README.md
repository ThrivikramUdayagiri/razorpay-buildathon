# Revox — AI-Governed Dual-Engine Payment Revenue Recovery

## Problem
Merchants lose expected revenue because recurring charges fail and one-off checkout attempts are abandoned or become stale. Current systems either blindly retry payments (causing bank penalties and spamming customers) or drop the recovery entirely.

## Solution
Revox uses AI to classify the failure context but uses deterministic policy controls to authorize recovery. 

It implements two distinct engines:
- **Engine A: AutoPay Recovery.** Handles recurring subscription failures. Schedules intelligent retries or generates alternate payment links based on AI classification.
- **Engine B: Checkout Recovery.** Handles one-off failed payments or individual payers. Secures checkout sessions using tokenized links, preventing stale payments, and never blindly reusing an old payment amount.

## AI Architecture (Gatekeeper Model)
- **AI decides classification:** The LLM receives the webhook payload and strictly outputs a JSON decision containing Intent, Reason, and Recommended Action.
- **Python decides permission:** The `PolicyEngine` evaluates the AI's recommendation against DB state. Hard Stops (e.g., mandate revoked, already paid, max touchpoints) always override the AI.
- **Python executes action:** The Backend handles all APIs and messaging. The LLM never touches external APIs.

## Safety & Guardrails
- **Idempotency:** Duplicate webhooks are rejected immediately.
- **Hard Stops:** Certain events (Mandate Revoked, Already Paid, Session Expired, Max Touchpoints) trigger a strict cessation of recovery.
- **Stale Validation:** When resuming a checkout, the original transaction is re-verified, and a *fresh* order is created.
- **Append-Only Audit Ledger:** Every state change is recorded in an immutable hash chain (SHA-256).

## Demo

To run the local prototype demo (Revox Recovery Simulator):

1. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Run the demo script:**
   This script synthesizes ~50 varied events (recurring, one-off, duplicates, hard stops) to populate the database and exercise all policies.
   ```bash
   python scripts/run_demo.py
   ```

3. **Start the server:**
   *Note: We run without `--reload` and on port 8050 to maintain state stability for the interactive simulator.*
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8050
   ```

4. **View the Simulator:**
   Open `http://127.0.0.1:8050/demo/` in your browser.

## Environment Variables
Copy `.env.example` to `.env`:
- `RAZORPAY_KEY_ID`: Razorpay Key ID
- `RAZORPAY_KEY_SECRET`: Razorpay Secret
- `RAZORPAY_WEBHOOK_SECRET`: Used to sign and verify incoming webhooks.
- `RAZORPAY_MODE`: `simulation` (default) or `test`. Simulation uses a deterministic internal stub without network calls.
- `LLM_PROVIDER`: `mock` (default), `gemini`, or `openai`.
- `LLM_API_KEY`: Your Gemini/OpenAI key.

## Razorpay Integration
The system supports two modes:
1. `simulation mode`: Does not make actual API calls to Razorpay. Highly recommended for offline testing and demos. Generates fake order/link IDs deterministically.
2. `test mode`: Uses the official Razorpay SDK to create real orders and links on the test network.

*Note: Simulated actions are clearly labeled and do not represent real financial transactions.*
