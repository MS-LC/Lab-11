import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FILE = "nyc-311-2025-november.csv.gz"
P1 = "Noise - Residential"
P2 = "HEAT/HOT WATER"


def main():
    df = pd.read_csv(FILE, encoding="latin-1")
    df["created_dt"] = pd.to_datetime(df["Created Date"], format="%m/%d/%Y %I:%M:%S %p", errors="raise")
    # Verify dtype (parsing check - silent failures from unparsed text would show object/string)
    print("created_dt dtype:", df["created_dt"].dtype)  # datetime64[ns]
    df["hour"] = df["created_dt"].dt.hour
    df["date"] = df["created_dt"].dt.date

    d1 = df[df["Problem (formerly Complaint Type)"] == P1]
    d2 = df[df["Problem (formerly Complaint Type)"] == P2]

    h1 = d1.groupby("hour").size().reindex(range(24), fill_value=0)
    h2 = d2.groupby("hour").size().reindex(range(24), fill_value=0)

    # Verify plotted peak hours match value_counts() output for same filtered data
    vc1 = d1["hour"].value_counts().reindex(range(24), fill_value=0).sort_index()
    vc2 = d2["hour"].value_counts().reindex(range(24), fill_value=0).sort_index()
    print(f"{P1} peak (groupby): hour={int(h1.idxmax())}, count={int(h1.max())}")
    print(f"{P1} peak (value_counts verify): hour={int(vc1.idxmax())}, count={int(vc1.max())}")
    print(f"{P2} peak (groupby): hour={int(h2.idxmax())}, count={int(h2.max())}")
    print(f"{P2} peak (value_counts verify): hour={int(vc2.idxmax())}, count={int(vc2.max())}")
    assert h1.equals(vc1) and h2.equals(vc2), "Peak/hour distributions must match"

    # Line chart (both on one chart)
    plt.figure(figsize=(10, 5))
    plt.plot(h1.index, h1.values, marker="o", label=P1)
    plt.plot(h2.index, h2.values, marker="o", label=P2)
    plt.xlabel("Hour of day (0–23, from parsed Created Date)")
    plt.ylabel("Number of complaints (November 2025)")
    plt.title("NYC 311 Complaints by Hour of Day: Noise - Residential vs HEAT/HOT WATER")
    plt.xticks(range(24))
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("fig-hours.png", dpi=150)
    plt.close()
    print("Saved fig-hours.png")

    # Claim check: split by one borough
    b = "BRONX"
    b1 = d1[d1["Borough"] == b].groupby("hour").size().reindex(range(24), fill_value=0)
    b2 = d2[d2["Borough"] == b].groupby("hour").size().reindex(range(24), fill_value=0)
    print(f"Bronx {P1} peak: hour={int(b1.idxmax())}, count={int(b1.max())}")
    print(f"Bronx {P2} peak: hour={int(b2.idxmax())}, count={int(b2.max())}")

    # Day × hour table (30 rows, 24 columns) for pooled nights of the two selected types
    both = df[df["Problem (formerly Complaint Type)"].isin([P1, P2])].copy()
    table = both.pivot_table(index="date", columns="hour", values="Unique Key", aggfunc="count", fill_value=0)
    table = table.reindex(columns=range(24), fill_value=0).sort_index()
    print("day×hour table shape:", table.shape)  # (30, 24)

    plt.figure(figsize=(12, 8))
    im = plt.imshow(table.values, aspect="auto", cmap="YlOrRd")
    plt.colorbar(im, label="Complaint count")
    plt.yticks(range(len(table.index)), [str(d) for d in table.index])
    plt.xticks(range(24), range(24))
    plt.xlabel("Hour of day (0–23)")
    plt.ylabel("Date (November 2025)")
    plt.title("Day × Hour Heat Map: Noise - Residential + HEAT/HOT WATER (Nov 2025)")
    plt.tight_layout()
    plt.savefig("fig-nights.png", dpi=150)
    plt.close()
    print("Saved fig-nights.png")

    # Identify anomalous night/hour
    hour_means = table.mean(axis=0)
    hour_stds = table.std(axis=0).replace(0, np.nan)
    z = (table - hour_means) / hour_stds
    top = z.stack().dropna().sort_values(ascending=False).head(1)
    (aday, ahour), az = top.index[0], float(top.iloc[0])
    print(f"Top anomaly: {aday} hour {ahour}, z={az:.3f}, count={int(table.loc[aday, ahour])}")

    # Checks for boring explanations on the anomalous slice
    sub = both[(both["date"] == aday) & (both["hour"] == ahour)]
    print("Check 1 (bad/duplicated rows):", {
        "rows": len(sub),
        "unique_keys": sub["Unique Key"].nunique(),
        "dup_unique_keys": len(sub) - sub["Unique Key"].nunique(),
        "fully_duplicated_rows": int(sub.duplicated().sum()),
        "null_unique_key": int(sub["Unique Key"].isna().sum()),
        "null_created_date": int(sub["Created Date"].isna().sum()),
    })
    print("Check 2 (burst characterization / real complaints):", {
        "distinct_created_timestamps": int(sub["Created Date"].nunique()),
        "problem_types": sub["Problem (formerly Complaint Type)"].value_counts().to_dict(),
        "boroughs": sub["Borough"].value_counts().to_dict(),
        "top_timestamps": sub["Created Date"].value_counts().head(5).to_dict(),
    })


if __name__ == "__main__":
    main()
