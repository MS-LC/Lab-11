# Lab 11 Report — NYC 311 (November 2025)

**Dataset:** `nyc-311-2025-november.csv.gz` (not committed; see `.gitignore`).  
**Environment note:** CSV is not valid UTF-8 (contains a stray byte), so scripts read with `encoding="latin-1"`.

## Code (linked files)

| Task | Code | Notes / outputs |
|---|---|---|
| 1 | [`Task 1/check_311.py`](Task%201/check_311.py) | Basic file stats and verifications |
| 2 | [`Task 2/borough_analysis.py`](Task%202/borough_analysis.py) | Borough complaint analysis + `fig-borough-bronx.png` |
| 3 | [`Task 3/census_boroughs.py`](Task%203/census_boroughs.py) | Census API fetch (key from `CENSUS_API_KEY`), join/normalize, `fig-borough-per1000.png` |
| 4 | [`Task 4/hours_analysis.py`](Task%204/hours_analysis.py) | Hour-of-day rhythms, heat map, anomaly checks; `fig-hours.png`, `fig-nights.png` |
| 5 | [`Task 5/time_to_close.py`](Task%205/time_to_close.py) | Time-to-close by agency (top 6), open-case handling, longest case |
| 6 | [`Task 6/time_to_close.py`](Task%206/time_to_close.py) | Same-job comparison (HEAT/HOT WATER by borough), `fig-same-job.png`, verification export `verify_heat_borough.csv` |
| 7 | [`Task 7/analysis.txt`](Task%207/analysis.txt) | Anomaly chase write-up |

## Figures (Tasks 2–6)

### Task 2 — Bronx top 10 complaint types
![Task 2: Bronx top 10 complaints](Task%202/fig-borough-bronx.png)

### Task 3 — Complaints per 1,000 residents by borough
![Task 3: Complaints per 1,000 residents](Task%203/fig-borough-per1000.png)

### Task 4 — Complaints by hour of day (two problem types)
![Task 4: Complaints by hour](Task%204/fig-hours.png)

### Task 4 — Day × hour heat map
![Task 4: Day by hour heat map](Task%204/fig-nights.png)

### Task 6 — Same job, different boroughs (HEAT/HOT WATER median hours to close)
![Task 6: Same job by borough](Task%206/fig-same-job.png)

## Headline numbers and two-way verifications

> Two-way verification comments are left in the code (see linked scripts). Key headline numbers and their second checks are summarized below.

### Task 1 — File basics (`Task 1/check_311.py`)
| Headline number | Method 1 | Method 2 (verify) | Result |
|---|---:|---:|---|
| Rows (data) | pandas `len(df)` = 304,905 | `zcat nyc-311-2025-november.csv.gz \| wc -l` = 304,906 total → 304,905 data rows | Match |
| Columns | pandas `len(df.columns)` = 44 | header/schema inspection | 44 |
| Distinct `Problem (formerly Complaint Type)` | pandas `nunique(dropna=False)` = 174 | streaming `csv.DictReader` unique-set count = 174 | Match |
| Earliest `Created Date` | parsed pandas min = 2025-11-01 00:00:04 | streaming `strptime` min = 2025-11-01 00:00:04 | Match |
| Latest `Created Date` | parsed pandas max = 2025-11-30 23:59:52 | streaming `strptime` max = 2025-11-30 23:59:52 | Match |
| Rows with no `Closed Date` | pandas NA/blank filter = 4,136 | streaming empty-field filter = 4,136 | Match |
| Status values (no `Closed Date`) | pandas counts: In Progress 3402, Open 300, Pending 199, Assigned 168, Started 65, Closed 2 | streaming counts: same values/counts | Match |

Code comments (left in `Task 1/check_311.py`): row count, distinct problem, earliest/latest, and no-Closed-Date/status verifications are written side-by-side in comments.

### Task 2 — Borough focus (Bronx) and comparison (`Task 2/borough_analysis.py`)
| Headline number | Method 1 | Method 2 (verify) | Result |
|---|---:|---:|---|
| Bronx total complaints | filtered count = 74,674 | `df['Borough'].value_counts()` includes Bronx 74,674 | Match |
| Bronx top 5 (count, share) | `value_counts()` on Bronx: Noise - Residential 22,216 (29.75%), HEAT/HOT WATER 16,671 (22.33%), Illegal Parking 6,900 (9.24%), UNSANITARY CONDITION 3,148 (4.22%), Blocked Driveway 2,527 (3.38%) | shares recomputed as `count/74674*100` | Match |
| Address-trap concentration (top complaint) | Bronx Noise - Residential at `655 EAST 230 STREET` = 14,361 / 22,216 = 64.64% | address `value_counts()` on same filtered subset | Match |
| Manhattan total / top 5 | filtered count 61,956; HEAT/HOT WATER 11,438 (18.46%), Noise - Residential 6,024 (9.72%), Illegal Parking 5,910 (9.54%), Noise - Street/Sidewalk 3,029 (4.89%), Encampment 2,967 (4.79%) | computed from same grouped counts | Match |

### Task 3 — Census join and normalization (`Task 3/census_boroughs.py`, `Task 3/written_answers.txt`)
| Headline number | Method 1 | Method 2 (verify) | Result |
|---|---:|---:|---|
| Census 2020 P1_001N (5 NYC counties) | Census API call (`state:36`, counties 005/047/061/081/085): Bronx 1,472,654; Kings/Brooklyn 2,736,074; New York/Manhattan 1,694,251; Queens 2,405,464; Richmond/Staten Island 495,747 | FIPS-to-borough mapping and response values checked against requested counties | Match |
| Population sanity check | Sum = 8,804,190 | expected ~8.8 million (`abs(total-8,800,000) < 200,000`) | Pass |
| Unspecified rows set aside | 196 rows (`Borough == "Unspecified"`) excluded from normalization | `value_counts()` shows Unspecified 196 | Match |
| Complaints per 1,000 (Bronx) | code: 74,674 / 1,472,654 * 1000 = 50.70709073550202 | plain calculator: 74,674 / 1,472,654 * 1000 = 50.707 | Match |
| Per-1,000 rates (all) | Bronx 50.71, Manhattan 36.57, Brooklyn 32.38, Queens 28.94, Staten Island 19.91 | computed from joined complaint counts and Census populations | Match |
| Rank change | Raw: Brooklyn, Bronx, Queens, Manhattan, Staten Island; Per-1,000: Bronx, Manhattan, Brooklyn, Queens, Staten Island | derived from same counts/rates table | Match |

**Task 3 prose (quality focus):**
> Yes, the ranks changed substantially between the raw-count and per-1,000 charts. Brooklyn led in raw complaints (88,591) but fell to **3rd** per 1,000 (32.38), while the Bronx rose from 2nd in raw counts to **1st** per 1,000 (50.71) and Manhattan rose from 4th to **2nd** (36.57); Queens dropped from 3rd to 4th, and Staten Island remained last. This reflects borough size: larger populations (Brooklyn, Queens) can produce high raw counts even when the rate per resident is lower. The Bronx’s higher rate may relate to differences in housing stock, building/heating conditions, and reporting patterns, and Manhattan’s rate may reflect its dense mix of residential and commercial activity—hypotheses rather than facts the data can prove, with the reminder that rates still measure 311 calls, not people or underlying conditions.

(See also [`Task 3/written_answers.txt`](Task%203/written_answers.txt).)

### Task 4 — Hourly rhythms and night-to-night variation (`Task 4/hours_analysis.py`, `Task 4/written_answers.txt`)
| Headline number | Method 1 | Method 2 (verify) | Result |
|---|---:|---:|---|
| `Created Date` parsing | `pd.to_datetime(..., format='%m/%d/%Y %I:%M:%S %p', errors='raise')` | dtype checked as `datetime64[ns]` (guards against silent unparsed-text plotting) | Valid parse |
| Noise - Residential peak | `groupby(hour).size()` → hour 22, count 3,878 | `value_counts()` on same filtered data → hour 22, count 3,878 | Match |
| HEAT/HOT WATER peak | `groupby(hour).size()` → hour 9, count 2,799 | `value_counts()` on same filtered data → hour 9, count 2,799 | Match |
| Borough split check (Bronx) | Noise peak hour 23 (1,769), Heat/Hot Water peak hour 19 (934) | computed from Bronx-filtered grouped counts | Reported (claim’s exact peak hours do not fully survive in Bronx) |
| Day×hour heat map table | pivot table shape (30, 24) for Noise - Residential + HEAT/HOT WATER | 30 unique dates in Nov 2025, hours 0–23 reindexed | Match |
| Top anomaly cell | 2025-11-02, hour 1: count 371 (z≈3.578) | z-score computed from hour-wise mean/std across days; same-hour distribution inspected | Consistent |

**Anomaly checks (two checks run, ruling out boring explanations):**
1. **Bad/duplicated rows:** 371 rows, 371 unique `Unique Key`s, 0 duplicate keys, 0 fully duplicated rows, 0 null `Unique Key`/`Created Date`.
2. **Burst characterization / real complaints:** 353 distinct `Created Date` timestamps, spread across boroughs and both problem types (Noise - Residential 308, HEAT/HOT WATER 63), with at most 3 identical timestamps — consistent with many real records rather than a malformed bulk insert.

**Task 4 prose (quality focus):**
> In November 2025, `Noise - Residential` complaints peak at **hour 22 (10:00–10:59 PM)** with **3,878** complaints, while `HEAT/HOT WATER` complaints peak at **hour 9 (9:00–9:59 AM)** with **2,799** complaints, showing an evening/night noise rhythm versus a morning-centered heating/hot-water rhythm. These plotted peak hours match `value_counts()`/grouped counts on the same filtered, parsed data (`Noise - Residential`: hour 22, 3,878; `HEAT/HOT WATER`: hour 9, 2,799). The claim does **not** fully survive by exact peak hour in the Bronx split (`Noise - Residential` peaks at hour 23, 1,769; `HEAT/HOT WATER` peaks at hour 19, 934), though the two complaint types still exhibit different hourly patterns.

> The overall shape is broadly similar on many nights (nighttime activity for noise and daytime/morning activity for heating), but it is **not** the same every night, with several dates showing much higher or lower intensity. One night that stands out is **2025-11-02 at hour 1 (1:00–1:59 AM)**, with **371** complaints in that cell (highest z-score anomaly, z≈3.58, vs a mean of ~118.5 for hour 1 across days). I think this spike was caused by the end of daylight saving time on 2025-11-02 (clocks fell back), which makes the labeled 1 AM clock hour cover a repeated local hour and can concentrate reports there, alongside normal late-night activity. To rule out boring explanations, I ran (1) a bad/duplicated-rows check on that slice (371 rows, 371 unique `Unique Key`s, 0 duplicate keys, 0 fully duplicated rows, 0 null `Unique Key`/`Created Date`) and (2) a burst-characterization check showing it reflects many real records rather than a malformed bulk insert (353 distinct `Created Date` timestamps, spread across boroughs and both problem types, with at most 3 identical timestamps). The cause is still a hypothesis, but the checks support treating the spike as a real pattern in the recorded data rather than a parsing or duplication artifact.

(See also [`Task 4/written_answers.txt`](Task%204/written_answers.txt).)

### Task 5 — Time to close by agency (`Task 5/time_to_close.py`)
| Headline number | Method 1 | Method 2 (verify) | Result |
|---|---:|---:|---|
| Open cases dropped | explicit filter `closed_dt.isna() | Closed Date blank` → 4,136 dropped | consistent with Task 1 no-Closed-Date count (4,136) | Match |
| Closed cases used | 300,769 | 304,905 − 4,136 = 300,769 | Match |
| Top 6 agencies (total complaints) | NYPD 139,819; HPD 86,247; DSNY 20,363; DOT 14,516; DEP 13,734; DOB 8,318 | `df['Agency'].value_counts().head(6)` | Match |
| Median hours to close (top 6, closed only) | NYPD 1.249 h (n=139,819), HPD 53.837 h (n=86,032), DSNY 38.554 h (n=20,150), DOT 82.836 h (n=14,148), DEP 39.583 h (n=13,608), DOB 182.537 h (n=8,318) | groupby medians on filtered closed cases | Match |
| NYPD median verification | `groupby(...).median()` = 1.2494444444444444 h | `numpy.median(...)` on same values = 1.2494444444444444 h | Match |
| Longest single complaint to close | Unique Key 66705910, Agency DPR, Problem `Overgrown Tree/Branches`, Created 11/02/2025 03:35:44 PM, Closed 11/12/2026 11:18:34 AM, 8,995.714 h (374.82 days) | `idxmax` on `hours_to_close` over closed cases | Match |
| DPR mean vs median (closed, n=5,468) | mean 917.515 h, median 186.692 h | computed on DPR closed subset; long-tail evidenced by 374.82-day case | Match |

**Interpretation:** The mean for DPR is far above the median, indicating a right-skewed distribution where most cases close much nearer ~187 hours but extreme outliers (e.g., the 374.82-day Overgrown Tree/Branches case) pull the mean up.

### Task 6 — Same job, different places (HEAT/HOT WATER, HPD) (`Task 6/time_to_close.py`, `Task 6/paragraph.txt`)
| Headline number | Method 1 | Method 2 (verify) | Result |
|---|---:|---:|---|
| HEAT/HOT WATER total / agency | 47,946 rows, all HPD | filtered `value_counts()` | Match |
| Open HEAT/HOT WATER cases dropped | 34 (explicit open-mask filter) | closed used 47,912 = 47,946 − 34 | Match |
| Median hours to close by borough (closed) | Staten Island 27.744 h (n=348), Bronx 30.815 h (n=16,663), Manhattan 34.159 h (n=11,425), Brooklyn 37.726 h (n=12,569), Queens 42.840 h (n=6,907) | groupby medians/counts on filtered closed cases | Match |
| Fastest–slowest gap | Queens 42.840000 h − Staten Island 27.744028 h = 15.095972 h (0.629 days) | plain subtraction of medians | Match |
| Staten Island median verification | `groupby` median = 27.744027777777777 h | `statistics.median` on plain list = 27.744027777777777 h; `statistics.median` from exported CSV (`verify_heat_borough.csv`) = 27.744027777777777 h | Match (all same) |

**Task 6 prose (quality focus):**
> For identical work (closed HPD HEAT/HOT WATER complaints), the gap between the fastest borough (Staten Island, 27.74 hours median) and the slowest (Queens, 42.84 hours median) is **15.10 hours (about 0.63 days)**, showing meaningful variation even when the complaint type and responding agency are held constant. The “different jobs” excuse is not available here because every case is the same problem category handled by the same agency; remaining differences could come from factors such as building stock and repair complexity, staffing/workload and routing by field office, access/inspection logistics, time-of-month/weather-driven surges, or differing complaint composition within HEAT/HOT WATER (and Staten Island’s small n=348 may also add volatility). To tell these candidates apart, we would need more detail than this file provides (e.g., building characteristics, severity/repair type, inspector/office assignment, access attempts, and workload/capacity data), though within this file we could further stratify by problem detail, time of day/week, location/community district, or resolution descriptions to test some explanations.

(See also [`Task 6/paragraph.txt`](Task%206/paragraph.txt) and [`Task 6/verify_heat_borough.csv`](Task%206/verify_heat_borough.csv).)

### Task 7 — Anomaly chase (`Task 7/analysis.txt`)
| Headline number | Method 1 | Method 2 (verify) | Result |
|---|---:|---:|---|
| Unspecified-borough rows | 196 rows | `df['Borough'].value_counts()` shows Unspecified 196 | Match |
| Missingness in Unspecified rows | Zip missing/blank 176, address missing/blank 163, lat/lon missing 183 | column-wise null/blank checks on same subset | Match |
| Dominant subgroups | Ferry-related 38 (mostly no address/zip/coords), Taxi/For-hire 58 (mostly missing addresses/zips) | filtered subgroup counts/field inspection | Match |

**Task 7 prose (quality focus):**
> I found that the 196 `Borough = Unspecified` rows are a concentrated anomaly: they are disproportionately tied to non-place-specific or weakly geocoded service categories (e.g., TLC and DOT dominate, with top problems like Ferry Inquiry/Complaint, Taxi/For-Hire complaints, Derelict Vehicles, and Traffic Signal Condition) and are largely missing standard location fields. Query 1 profiled these rows by agency/problem/location type/channel (n=196; agencies led by TLC 70, DOT 59, DSNY 30; problems led by Ferry Inquiry 29, Taxi Complaint 24, Derelict Vehicles 23; channels ONLINE 89, PHONE 67, UNKNOWN 36). Query 2 checked location completeness and geography (Incident Zip missing/blank in 176, Incident Address missing/blank in 163, Latitude/Longitude missing in 183, and City mostly missing but occasionally outside NYC such as Buffalo, Albany, and San Francisco). Query 3 drilled into dominant subgroups (38 ferry-related rows almost all with Location Type Ferry/Terminal and no address/zip/coordinates; 58 taxi/for-hire rows mostly lacking addresses/zips; plus a few rows with non-NYC cities/zips), showing the pattern is driven by records that are not easily tied to a single NYC borough. Verdict: **mixed/mostly cannot be fully resolved from this file alone**—many cases look like a real or structural “unspecified/un-geocoded” reporting category (especially ferries and some taxi/inquiry reports), but the small subset with out-of-area cities or mismatched location details suggests some data-entry or attribution artifacts.

## LLM use

- **What I asked:** I used the coding assistant to inspect/read the NYC 311 CSV (`.csv.gz`), write and run analysis scripts for Tasks 1–7 (counts, parsing/normalization, charts, joins with Census data, time-to-close calculations, and anomaly checks), and organize the repository/report.
- **What it got wrong (or where it failed):**
  - It initially assumed the CSV was UTF-8-readable; a direct read failed with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2...` (and an early byte-position guess from the traceback context was not the true root location).
  - It could not fetch Census populations from the provided API endpoint at first because the Census API required a key in this environment (request redirected to `missing_key.html`), so it had to pause and proceed only after I supplied a key.
  - During repo cleanup/reorganization, `Task 6/time_to_close.py` in the cloned repo ended up containing the Task 5 script content; I corrected it to the proper same-job (HEAT/HOT WATER by borough) analysis script in the final report setup.
- **How I caught it:** I inspected the raw bytes/gzip stream to locate the actual invalid UTF-8 sequence and switched to a tolerant encoding (`latin-1`); I tested the Census endpoint directly with `curl` to confirm the key requirement and then re-ran the fetch with the provided key (and updated the script to read `CENSUS_API_KEY` from the environment so no key is stored in the repo); I compared script contents/outputs against task requirements and figures/results, ran scripts, and cross-verified headline numbers with second methods (e.g., `zcat | wc -l`, streaming CSV scans, `numpy`/`statistics.median`, plain-calculator recomputation, and exported-CSV median checks), leaving two-way verification comments in code.

## Reproducibility / data and secrets hygiene

- **No API keys in repo:** `Task 3/census_boroughs.py` reads the Census key from `CENSUS_API_KEY`.
- **No large data files committed:** `.gitignore` excludes `*.csv.gz` and other large/raw data patterns (the source `nyc-311-2025-november.csv.gz` is not tracked).
- **Small verification artifact:** `Task 6/verify_heat_borough.csv` is a small exported slice used to verify one borough’s median by a second route.
