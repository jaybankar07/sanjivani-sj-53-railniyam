import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.records import load_records

df = pd.DataFrame([r.to_dict() for r in load_records()])
print(f"Fact 1: {len(df)} records; split by category:\n{df['category'].value_counts().to_string()}\n")
print(f"Fact 2: {(~df['verified']).sum()} records are unverified against official sources: {df.loc[~df['verified'], 'id'].tolist()}\n")
print(f"Fact 3: {df['charge_or_refund'].str.contains('full', case=False).sum()} records offer a full refund; "
      f"{df['charge_or_refund'].str.contains('no refund', case=False).sum()} say no refund.")
