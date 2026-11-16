import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FILE = "nyc-311-2025-november.csv.gz"
BOROUGH = "BRONX"
BOROUGH2 = "MANHATTAN"
PROB_COL = "Problem (formerly Complaint Type)"


def main():
    # Read with tolerant encoding due to invalid UTF-8 byte in the source file
    df = pd.read_csv(FILE, encoding="latin-1")

    # --- Primary borough: Bronx ---
    bdf = df[df["Borough"] == BOROUGH].copy()
    total = len(bdf)
    top = bdf[PROB_COL].value_counts()

    print(f"Borough: {BOROUGH}")
    print(f"Total complaints: {total}")
    print()
    print("Top 5 complaints (count and share of borough total):")
    for name, count in top.head(5).items():
        share = count / total * 100
        print(f"- {name}: {count} ({share:.2f}%)")

    print()
    print("Top 10 complaints:")
    for name, count in top.head(10).items():
        share = count / total * 100
        print(f"- {name}: {count} ({share:.2f}%)")

    # Address trap: counts measure calls, not people.
    # Check if one address dominates the top complaint.
    top1 = top.index[0]
    t1df = bdf[bdf[PROB_COL] == top1]
    addr_counts = t1df["Incident Address"].fillna("(missing)").value_counts()
    top_addr = addr_counts.index[0]
    top_addr_count = int(addr_counts.iloc[0])
    top_addr_share = top_addr_count / len(t1df) * 100
    print()
    print("Address trap check (top complaint):")
    print(f"  Top complaint: {top1} ({len(t1df)} complaints)")
    print(
        f"  Dominant address: {top_addr} -> {top_addr_count} complaints "
        f"({top_addr_share:.2f}% of this complaint type in {BOROUGH})"
    )
    print("  Note: Counts measure calls, not people; repeated calls from specific addresses can skew totals.")

    # --- Bar chart of top 10 ---
    fig, ax = plt.subplots(figsize=(10, 6))
    top10 = top.head(10).sort_values(ascending=True)
    ax.barh(top10.index, top10.values, color="#4C78A8")
    ax.set_xlabel("Number of 311 complaints")
    ax.set_ylabel("Complaint type")
    ax.set_title(f"Top 10 NYC 311 Complaint Types in the Bronx (November 2025)")
    ax.tick_params(axis="y", labelsize=9)
    plt.tight_layout()
    out_fig = "fig-borough-bronx.png"
    plt.savefig(out_fig, dpi=150)
    plt.close(fig)
    print()
    print(f"Saved chart: {out_fig}")

    # --- Second borough comparison ---
    mdf = df[df["Borough"] == BOROUGH2]
    total2 = len(mdf)
    top2 = mdf[PROB_COL].value_counts().head(5)
    print()
    print(f"Second borough for comparison: {BOROUGH2}")
    print(f"Total complaints: {total2}")
    print("Top 5 complaints:")
    for name, count in top2.items():
        share = count / total2 * 100
        print(f"- {name}: {count} ({share:.2f}%)")

    print()
    print("Comparison (hypothesis, not fact):")
    print(
        "In November 2025, the Bronx’s top complaints were led by Noise - Residential (29.75%) "
        "and HEAT/HOT WATER (22.33%), while Manhattan’s top five were HEAT/HOT WATER (18.46%), "
        "Noise - Residential (9.72%), Illegal Parking (9.54%), Noise - Street/Sidewalk (4.89%), "
        "and Encampment (4.79%). Compared with the Bronx, Manhattan shows a more mixed profile "
        "with relatively more street/public-space issues. Hypothesis: these differences may reflect "
        "differences in land use and density, housing/building conditions and heating complaint "
        "patterns, and reporting behavior—but the data cannot prove causes, and repeated calls "
        "from specific addresses can also skew category totals."
    )


if __name__ == "__main__":
    main()
