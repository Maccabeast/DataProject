import pandas as pd

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

if __name__ == "__main__":
    print("Loading data...")
    tables = load_data()
    combined_data = combine_tables(tables[KNS_Bill], tables[KNS_BillInitiator], tables[KNS_PersonToPosition])
    print(combined_data.head())
    bills_table = bill_counts(combined_data)
    print(bills_table.sort_values(by='LawCount', ascending=False).head())
    bills_table = faction_size(bills_table, tables[KNS_PersonToPosition])
    bills_table["BillsPerMember"] = bills_table["BillCount"] / bills_table["FactionSize"]
    bills_table["LawsPerMember"] = bills_table["LawCount"] / bills_table["FactionSize"]
    print(bills_table.head())
    bills_table.to_csv("PartiesRanked.csv", index=False)