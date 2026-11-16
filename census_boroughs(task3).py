import json
import urllib.request
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FILE = "nyc-311-2025-november.csv.gz"
CENSUS_KEY = "34b14edfe82a9f1fdfa4a303f3f7009dd8acfa7d"

FIPS_TO_BOROUGH = {
    "005": "BRONX",        # Bronx County
    "047": "BROOKLYN",     # Kings County
    "061": "MANHATTAN",    # New York County
    "081": "QUEENS",       # Queens County
    "085": "STATEN ISLAND" # Richmond County
}


def fetch_census_populations():
    # 3a — Pull the populations from the Census API (one API call)
    url = (
        "https://api.census.gov/data/2020/dec/pl"
        "?get=NAME,P1_001N&for=county:005,047,061,081,085&in=state:36"
        f"&key={CENSUS_KEY}"
    )
    print("Census API call:")
    print(url.replace(CENSUS_KEY, "YOUR_KEY"))
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    # data is [header, rows...]
    header = data[0]
    rows = data[1:]
    records = []
    for row in rows:
        rec = dict(zip(header, row))
        county_fips = rec["county"]
        records.append(
            {
                "Borough": FIPS_TO_BOROUGH[county_fips],
                "NAME": rec["NAME"],
                "FIPS": f"36{county_fips}",
                "population": int(rec["P1_001N"]),
            }
        )
    pop_df = pd.DataFrame(records)[["Borough", "population", "NAME", "FIPS"]]
    pop_df = pop_df.sort_values("Borough").reset_index(drop=True)
    return pop_df


def main():
    pop_df = fetch_census_populations()
    print("\nFetched borough populations (P1_001N):")
    print(pop_df[["Borough", "NAME", "FIPS", "population"]].to_string(index=False))

    # Sanity check: five numbers should add up to roughly 8.8 million
    pop_total = pop_df["population"].sum()
    print("\n3a Sanity check - total population of 5 boroughs:", pop_total)
    print("Expected ~8.8 million:", abs(pop_total - 8_800_000) < 200_000)

    # 3b — Join and normalize
    df = pd.read_csv(FILE, encoding="latin-1")
    counts = df["Borough"].value_counts(dropna=False).rename_axis("Borough").reset_index(name="complaints")

    # Drop or set aside the 196 rows where Borough is Unspecified — no population to normalize against.
    unspecified_rows = int(counts.loc[counts["Borough"] == "Unspecified", "complaints"].sum())
    print("\n3b Note: dropped/set aside Unspecified borough rows (no population to normalize against):", unspecified_rows)

    counts5 = counts[counts["Borough"].isin(pop_df["Borough"])].copy()
    merged = counts5.merge(pop_df[["Borough", "population"]], on="Borough", how="inner", validate="one_to_one")
    merged["complaints_per_1000"] = merged["complaints"] / merged["population"] * 1000
    merged = merged.sort_values("complaints_per_1000", ascending=False)

    print("\nBorough, complaints, population, complaints_per_1000:")
    print(merged[["Borough", "complaints", "population", "complaints_per_1000"]].to_string(index=False))

    # Bar chart (same style as Task 2) now per 1,000
    plot_df = merged.sort_values("complaints_per_1000", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(plot_df["Borough"], plot_df["complaints_per_1000"], color="#4C78A8")
    ax.set_xlabel("311 complaints per 1,000 residents (November 2025)")
    ax.set_ylabel("Borough")
    ax.set_title("NYC 311 Complaints per 1,000 Residents by Borough (November 2025)")
    for i, v in enumerate(plot_df["complaints_per_1000"]):
        ax.text(v + 0.2, i, f"{v:.2f}", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig("fig-borough-per1000.png", dpi=150)
    plt.close(fig)
    print("\nSaved chart: fig-borough-per1000.png")

    # Raw-count ranking for comparison (excluding Unspecified)
    raw_rank = counts5.sort_values("complaints", ascending=False)["Borough"].tolist()
    per1000_rank = merged.sort_values("complaints_per_1000", ascending=False)["Borough"].tolist()
    print("\nRank comparison:")
    print("Raw-count rank:   ", raw_rank)
    print("Per-1,000 rank:   ", per1000_rank)

    # Verify: recompute one borough’s per-1,000 figure with a plain calculator from the two raw numbers
    # Bronx: 74,674 complaints / 1,472,654 population * 1000 = 50.7071... per 1,000
    bronx = merged[merged["Borough"] == "BRONX"].iloc[0]
    print("\nVerification (Bronx, plain calc): 74674 / 1472654 * 1000 = 50.707 per 1,000")
    print(f"Computed in code: {bronx['complaints_per_1000']}")


if __name__ == "__main__":
    main()
