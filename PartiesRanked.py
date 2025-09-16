import pandas as pd

KNS_Bill = "KNS_Bill"
KNS_BillInitiator = "KNS_BillInitiator"
KNS_Faction = "KNS_Faction"
KNS_Person = "KNS_Person"
KNS_PersonToPosition = "KNS_PersonToPosition"

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
    merged = KNS_BillInitiator.merge(
        KNS_bills[['BillID', 'KnessetNum']],
        on='BillID',
        how='left'
    )
    ##
    KNS_PersonToPosition = KNS_PersonToPosition[KNS_PersonToPosition['FactionID'].notna()]

    merged = merged.merge(
        KNS_PersonToPosition[['PersonID', 'KnessetNum', 'FactionID']],
        on=['PersonID', 'KnessetNum'],
        how='left'
    )
    result = merged[['BillInitiatorID', 'BillID', 'PersonID', 'KnessetNum', 'FactionID']]
    return result

if __name__ == "__main__":
    tables = load_data()
    print(tables[KNS_Bill].head())
    combined_data = combine_tables(tables[KNS_Bill], tables[KNS_BillInitiator], tables[KNS_PersonToPosition])
    print(combined_data.head())