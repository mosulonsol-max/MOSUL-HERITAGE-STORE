#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import connect, process_refunds
with connect(os.environ.get("PAYMENT_DB", "data/payments.sqlite3")) as db:
    print(json.dumps(process_refunds(db, os.environ["DEVNET_REFUND_KEYPAIR"])))
