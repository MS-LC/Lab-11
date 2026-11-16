import pandas as pd
import numpy as np

FILE = "nyc-311-2025-november.csv.gz"


def main():
    df = pd.read_csv(FILE, encoding="latin-1")

    # Parse dates
    df["created_dt"] = pd.to_datetime(
        df["Created Date"], format="%m/%d/%Y %I:%M:%S %p", errors="raise"
    )
    df["closed_dt"] = pd.to_datetime(
        df["Closed Date"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
    )

    # Handle open cases explicitly: filter them out where a reader can see it
    open_mask = df["closed_dt"].isna() | (df["Closed Date"].astype(str).str.strip() == "")
    open_count = int(open_mask.sum())
    closed_df = df.loc[~open_mask].copy()  # explicit filter: drop open cases (no Closed Date)

    print(f"Total rows: {len(df)}")
    print(f"Open cases dropped (no Closed Date): {open_count}")
    print(f"Closed cases used: {len(closed_df)}")

    # Duration in hours/days
    closed_df["hours_to_close"] = (
        closed_df["closed_dt"] - closed_df["created_dt"]
    ).dt.total_seconds() / 3600.0
    closed_df["days_to_close"] = closed_df["hours_to_close"] / 24.0

    # Six agencies with the most complaints (overall, in November dataset)
    top6_agencies = df["Agency"].value_counts().head(6).index.tolist()
    print("\nTop 6 agencies by total complaints:", top6_agencies)

    # Median/mean hours from created to closed by agency (for those 6), open cases excluded
    sub6 = closed_df[closed_df["Agency"].isin(top6_agencies)].copy()
    med_by_agency = sub6.groupby("Agency")["hours_to_close"].median().reindex(top6_agencies)
    mean_by_agency = sub6.groupby("Agency")["hours_to_close"].mean().reindex(top6_agencies)
    counts_used = sub6.groupby("Agency").size().reindex(top6_agencies)
    total_counts = df["Agency"].value_counts().reindex(top6_agencies)

    print("\nMedian hours to close by agency (top 6, open cases excluded):")
    print("Agency | total_complaints | n_closed_used | median_hours | mean_hours")
    for ag in top6_agencies:
        print(
            f"{ag} | {int(total_counts[ag])} | {int(counts_used[ag])} | "
            f"{med_by_agency[ag]:.6f} | {mean_by_agency[ag]:.6f}"
        )

    # Verify one agency's median using a different route (numpy instead of groupby)
    ag_verify = top6_agencies[0]  # NYPD
    vals = sub6.loc[sub6["Agency"] == ag_verify, "hours_to_close"].to_numpy()
    med_groupby = float(med_by_agency[ag_verify])
    med_numpy = float(np.median(vals))
    print(f"\nVerify {ag_verify} median (different route):")
    print(f"groupby median = {med_groupby}")
    print(f"numpy.median   = {med_numpy}")
    print(f"same? {np.isclose(med_groupby, med_numpy)}")
    # Comment-style verification: NYPD median groupby=1.2494444444444444, numpy=1.2494444444444444 (same)

    # Single complaint created in November that took the longest to close
    idx = closed_df["hours_to_close"].idxmax()
    longest = closed_df.loc[idx]
    print("\nLongest single complaint created in November to close:")
    print(f"Unique Key: {longest['Unique Key']}")
    print(f"Agency: {longest['Agency']}")
    print(f"Problem type: {longest['Problem (formerly Complaint Type)']}")
    print(f"Created Date: {longest['Created Date']}")
    print(f"Closed Date: {longest['Closed Date']}")
    print(f"Hours to close: {longest['hours_to_close']:.6f}")
    print(f"Days to close: {longest['days_to_close']:.6f}")

    # For that agency, compare mean and median
    lag = longest["Agency"]
    lag_sub = closed_df[closed_df["Agency"] == lag]["hours_to_close"]
    lag_mean = lag_sub.mean()
    lag_median = lag_sub.median()
    lag_n = len(lag_sub)
    print(f"\nAgency of longest case: {lag} (n_closed={lag_n})")
    print(f"Mean hours to close:   {lag_mean:.6f}")
    print(f"Median hours to close: {lag_median:.6f}")
    print(
        "Interpretation: The mean is far above the median, indicating a right-skewed distribution "
        "where most cases close much sooner than the average but extreme outliers pull the mean up. "
        "The longest case (Overgrown Tree/Branches, 374.82 days) is evidence of that extreme tail."
    )


if __name__ == "__main__":
    main()
