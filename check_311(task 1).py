import gzip
import subprocess
import pandas as pd

FILE = "nyc-311-2025-november.csv.gz"

# Read with tolerant encoding due to invalid UTF-8 byte in file
df = pd.read_csv(FILE, encoding="latin-1")

# 1) Rows and columns
rows_lib = len(df)
cols_lib = len(df.columns)

# Verify row count via zcat | wc -l (includes header line)
wc_out = subprocess.check_output(f"zcat '{FILE}' | wc -l", shell=True, text=True).strip()
rows_wc_total = int(wc_out)
rows_wc_data = rows_wc_total - 1  # subtract header
# Verification (row count): library=304905, zcat_data_rows=304905 (agree)

# 2) Distinct values of Problem (formerly Complaint Type)
prob_col = "Problem (formerly Complaint Type)"
distinct_lib = df[prob_col].nunique(dropna=False)

# Verify distinct via shell pipeline (awk/cut is tricky due to commas in quoted fields), use python streaming parse
import csv
seen = set()
with gzip.open(FILE, 'rt', encoding='latin-1', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        seen.add(row.get(prob_col))
distinct_stream = len(seen)
# Verification (distinct Problem): library=174, stream_csv=174 (agree)

# 3) Earliest and latest Created Date (parse before compare)
created = pd.to_datetime(df["Created Date"], format="%m/%d/%Y %I:%M:%S %p", errors="raise")
earliest_lib = created.min()
latest_lib = created.max()

# Verify by streaming min/max
import datetime
fmt = "%m/%d/%Y %I:%M:%S %p"
earliest_s = None
latest_s = None
with gzip.open(FILE, 'rt', encoding='latin-1', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dt = datetime.datetime.strptime(row["Created Date"], fmt)
        if earliest_s is None or dt < earliest_s:
            earliest_s = dt
        if latest_s is None or dt > latest_s:
            latest_s = dt
# Verification (earliest Created Date): library=2025-11-01 00:00:04, stream=2025-11-01 00:00:04 (agree)
# Verification (latest Created Date):   library=2025-11-30 23:59:52, stream=2025-11-30 23:59:52 (agree)

# 4) Rows with no Closed Date, and what Status values they carry
closed = df["Closed Date"]
no_closed_mask = closed.isna() | (closed.astype(str).str.strip() == "")
no_closed_lib = int(no_closed_mask.sum())
status_counts_lib = df.loc[no_closed_mask, "Status"].value_counts(dropna=False).to_dict()

# Verify open count by filtering on Closed Date being empty via streaming
no_closed_stream = 0
status_counts_stream = {}
with gzip.open(FILE, 'rt', encoding='latin-1', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cd = row.get("Closed Date")
        if cd is None or str(cd).strip() == "":
            no_closed_stream += 1
            st = row.get("Status")
            status_counts_stream[st] = status_counts_stream.get(st, 0) + 1
# Verification (no Closed Date count): library=4136, stream=4136 (agree)
# Verification (Status values/counts for no Closed Date): library={'In Progress': 3402, 'Open': 300, 'Pending': 199, 'Assigned': 168, 'Started': 65, 'Closed': 2}, stream={'In Progress': 3402, 'Pending': 199, 'Assigned': 168, 'Open': 300, 'Started': 65, 'Closed': 2} (agree; same counts, dict order differs)

print("1) Rows and columns")
print(f"rows={rows_lib}, cols={cols_lib}")
print(f"verify: library_rows={rows_lib}, zcat_data_rows={rows_wc_data}")
print()

print("2) Distinct Problem (formerly Complaint Type)")
print(f"distinct={distinct_lib}")
print(f"verify: library={distinct_lib}, stream_csv={distinct_stream}")
print()

print("3) Earliest and latest Created Date")
print(f"earliest={earliest_lib}")
print(f"latest={latest_lib}")
print(f"verify earliest: library={earliest_lib}, stream={earliest_s}")
print(f"verify latest:   library={latest_lib}, stream={latest_s}")
print()

print("4) Rows with no Closed Date and their Status values")
print(f"no_closed_date={no_closed_lib}")
print(f"status_counts={status_counts_lib}")
print(f"verify count: library={no_closed_lib}, stream={no_closed_stream}")
print(f"verify status_counts stream={status_counts_stream}")
