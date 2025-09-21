import pandas as pd
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper

KNS_Bill = "KNS_Bill"
KNS_BillInitiator = "KNS_BillInitiator"
KNS_Faction = "KNS_Faction"
KNS_Person = "KNS_Person"
KNS_PersonToPosition = "KNS_PersonToPosition"
BECAME_LAW_STATUS = 118 # Acoording to KNS_Status

def load_data():
    '''Load data from CSV files into pandas DataFrames.'''
    tables = {}
    for table_name in [KNS_Bill, KNS_BillInitiator, KNS_Faction, KNS_Person, KNS_PersonToPosition]:
        tables[table_name] = pd.read_excel(f'{table_name}.xlsx')
        tables[table_name] = tables[table_name].rename(columns=lambda s: s.split("[")[1].split("]")[0])
    return tables

def combine_tables(KNS_bills, KNS_BillInitiator, KNS_PersonToPosition):
    """
    Merge KNS_BillInitiator, KNS_Bills, and KNS_PersonToFaction into a single DataFrame.

    """
    KNS_BillInitiator = KNS_BillInitiator[KNS_BillInitiator['IsInitiator'] == True]
    merged = KNS_BillInitiator.merge(
        KNS_bills[['BillID', 'KnessetNum', 'StatusID']],
        on='BillID',
        how='left'
    )
    KNS_PersonToPosition = KNS_PersonToPosition[KNS_PersonToPosition['FactionID'].notna()]
    merged = merged.merge(
        KNS_PersonToPosition[['PersonID', 'KnessetNum', 'FactionID']],
        on=['PersonID', 'KnessetNum'],
        how='left'
    )
    merged = merged.reset_index(drop=True)
    merged = merged[['BillID', 'KnessetNum', 'FactionID', 'StatusID']]
    result = merged.drop_duplicates()
    return result

def faction_size(merged: pd.DataFrame, PersonToPosition: pd.DataFrame) -> pd.DataFrame:
    """
    Add a FactionSize column to the merged DataFrame, indicating the size of each faction in each Knesset.
    """
    faction_sizes = PersonToPosition.groupby(['FactionID', 'KnessetNum']).size().reset_index(name='FactionSize')
    merged = merged.merge(faction_sizes, on=['FactionID', 'KnessetNum'], how='left')
    return merged

def bill_counts(merged: pd.DataFrame) -> pd.DataFrame:
    """
    for each Knesset and Faction, count the number of bills initiated by that faction in that Knesset.
    """
    bills = merged.groupby(['KnessetNum', 'FactionID']).size().reset_index(name='BillCount')
    laws = merged[merged['StatusID'] == BECAME_LAW_STATUS]
    laws = laws.groupby(['KnessetNum', 'FactionID']).size().reset_index(name='LawCount')
    result = bills.merge(laws, on=['KnessetNum', 'FactionID'], how='left')
    
    result['LawCount'] = result['LawCount'].fillna(0).astype(int)
    result['SuccessRate'] = result['LawCount'] / result['BillCount']
    return result

def fix_hebrew(text):
    """Fix Hebrew text display for matplotlib."""
    return get_display(arabic_reshaper.reshape(text))

def plot_knesset_stats(df):
    """
    Create dual-axis plots of BillsPerMember and SuccessRate per faction,
    ordered by FactionSize, for selected Knesset numbers.
    """
    fig_width, fig_height = 12, 6  # consistent size for all plots

    for k in [20,23,24,25]:
        subset = df[df["KnessetNum"] == k].copy()
        # Prepare faction labels
        subset["FactionLabel"] = [
            f"{fix_hebrew(name)} ({size})" for name, size in zip(subset["FactionName"], subset["FactionSize"])
        ]

        # --- Plot 1: Bills per Member ---
        bills_sorted = subset.sort_values("BillsPerMember", ascending=False)

        plt.figure(figsize=(fig_width, fig_height))
        bars = plt.bar(bills_sorted["FactionLabel"], bills_sorted["BillsPerMember"], color="skyblue", label="Bills per Member")
        plt.xticks(rotation=90)
        plt.ylabel("Bills per Member")
        plt.title(f"Knesset {k}: Bills per Member by Faction")

        # Annotate bars with numeric values
        for bar, val in zip(bars, bills_sorted["BillsPerMember"]):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                     f"{val:.2f}", ha='center', va='bottom', fontsize=9, color='darkblue')

        # Legend shows only the metric
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.savefig(f"PartiesRankedPlots/Knesset_{k}_Bills.png", dpi=300, bbox_inches="tight")
        plt.show()

        # --- Plot 2: Success Rate ---
        success_sorted = subset.sort_values("SuccessRate", ascending=False)

        plt.figure(figsize=(fig_width, fig_height))
        bars = plt.bar(success_sorted["FactionLabel"], success_sorted["SuccessRate"], color="salmon", label="Success Rate")
        plt.xticks(rotation=90)
        plt.ylabel("Success Rate")
        plt.title(f"Knesset {k}: Success Rate by Faction")

        # Annotate bars with numeric values
        for bar, val in zip(bars, success_sorted["SuccessRate"]):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                     f"{val:.2f}", ha='center', va='bottom', fontsize=9, color='darkred')

        # Legend shows only the metric
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.savefig(f"PartiesRankedPlots/Knesset_{k}_Success.png", dpi=300, bbox_inches="tight")
        plt.show()
     
if __name__ == "__main__":
    print("Loading data...")
    tables = load_data()
    combined_data = combine_tables(tables[KNS_Bill], tables[KNS_BillInitiator], tables[KNS_PersonToPosition])
    bills_table = bill_counts(combined_data)
    bills_table = faction_size(bills_table, tables[KNS_PersonToPosition])
    bills_table["BillsPerMember"] = bills_table["BillCount"] / bills_table["FactionSize"]
    bills_table["LawsPerMember"] = bills_table["LawCount"] / bills_table["FactionSize"]
    bills_table = bills_table.merge(
        tables[KNS_Faction][['FactionID', 'Name']],
        on='FactionID',
        how='left'
    )
    bills_table = bills_table.rename(columns={'Name': 'FactionName'}).drop(columns=['FactionID'])
    bills_table = bills_table.sort_values(by=['KnessetNum', 'LawsPerMember'], ascending=[True, False])
    bills_table.to_csv("PartiesRanked.csv", index=False)
    plot_knesset_stats(bills_table)