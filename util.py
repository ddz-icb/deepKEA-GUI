import pandas as pd
from statsmodels.stats.multitest import multipletests
from scipy.stats import fisher_exact

def performKSEA(raw_data, sites):
    merged = pd.merge(raw_data, sites, on=["SUB_ACC_ID", "SUB_MOD_RSD"])
    kinases = merged.groupby(['KINASE', 'KIN_ACC_ID']).size().reset_index(name='count')
    kinases = kinases.sort_values(by='count', ascending=False).reset_index(drop=True)

    kinase_counts = count_kinases(kinases, raw_data)

    kinase_counts = pd.DataFrame(kinase_counts, columns=["KINASE", "COUNT", "UPID"])
    kinase_counts = kinase_counts.set_index("KINASE")

    results = calculate_p_vals(kinase_counts, kinases, merged, raw_data)

    results = pd.DataFrame(results, columns=["KINASE", "ODDS_RATIO", "P_VALUE", "UPID", "FOUND", "SUB#"])
    results = results.sort_values(by="P_VALUE")
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method='fdr_bh')[1]
    results = results.reset_index(drop=True)

    ### FIXME Disabled Uniprot link
    # results['UPID'] = results['UPID'].apply(lambda x: f"(https://www.uniprot.org/uniprotkb/{x}/entry)")
    # results["KINASE"] = results["KINASE"].apply(lambda x: f"[{x}]")
    # results["KINASE"] = results["KINASE"] + results["UPID"]
    #
    
    # FIXME UPID activated
    
    # results = results.drop(columns=["UPID"])

    return results

def performKSEA_high_level(raw_data, sites):
    merged = pd.merge(raw_data, sites, on=["SUB_ACC_ID"])
    
    
    kinases = merged.groupby(['KINASE', 'KIN_ACC_ID']).size().reset_index(name='count')
    kinases = kinases.sort_values(by='count', ascending=False).reset_index(drop=True)

    kinase_counts = count_kinases(kinases, raw_data)

    kinase_counts = pd.DataFrame(kinase_counts, columns=["KINASE", "COUNT", "UPID"])
    kinase_counts = kinase_counts.set_index("KINASE")

    results = calculate_p_vals(kinase_counts, kinases, merged, raw_data)

    results = pd.DataFrame(results, columns=["KINASE", "ODDS_RATIO", "P_VALUE", "UPID", "FOUND", "SUB#"])
    results = results.sort_values(by="P_VALUE")
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method='fdr_bh')[1]
    results = results.reset_index(drop=True)

    ### FIXME Disabled Uniprot link
    # results['UPID'] = results['UPID'].apply(lambda x: f"(https://www.uniprot.org/uniprotkb/{x}/entry)")
    # results["KINASE"] = results["KINASE"].apply(lambda x: f"[{x}]")
    # results["KINASE"] = results["KINASE"] + results["UPID"]
    #
    
    # FIXME UPID activated
    
    # results = results.drop(columns=["UPID"])

    return results



def calculate_p_vals(kinase_counts, kinases, merged, raw_data):
    results = []
    for index, row in kinases.iterrows():
        count = row["count"]
        kinase = row["KINASE"]
        upid = row["KIN_ACC_ID"]
        sub_in_sample = count
        sub_in_sample_w_other_kinase = len(merged[merged["KINASE"] != kinase])
        sub_not_in_sample = kinase_counts.loc[kinase, "COUNT"] - count
        subs_w_other_kinase = len(raw_data) - kinase_counts.loc[kinase, "COUNT"]

        table = [[sub_in_sample, sub_in_sample_w_other_kinase], [sub_not_in_sample, subs_w_other_kinase]]
        
        # Flatten the table to a single list
        flat_list = [item for sublist in table for item in sublist]
        
        if all(value > 0 for value in flat_list):
            odds_ratio, p_value = fisher_exact(table, alternative='greater')
            odds_ratio = round(odds_ratio, 2)
            results.append([kinase, odds_ratio, p_value, upid, sub_in_sample, sub_in_sample + sub_not_in_sample])
        else:
            results.append([kinase, -1, 1, upid, sub_in_sample, sub_in_sample + sub_not_in_sample])
        
        
        
        
    return results


def count_kinases(kinases, raw_data):
    kinase_counts = []
    for index, row in kinases.iterrows():
        count = row["count"]
        kinase = row["KINASE"]
        upid = row["KIN_ACC_ID"]
        sub_count = len(raw_data[raw_data["KINASE"] == kinase])
        kinase_counts.append([kinase, sub_count, upid])
    return kinase_counts


def read_sites(content):
    entries = [entry.strip() for entry in content.replace(';', '\n').splitlines() if entry]
    data = [entry.split('_') for entry in entries]
    df = pd.DataFrame(data, columns=['SUB_ACC_ID', 'UPID', 'SUB_MOD_RSD'])
    df = df.assign(SUB_MOD_RSD=df['SUB_MOD_RSD'].str.split(',')).explode('SUB_MOD_RSD')
    return df

def start_eval(content, raw_data):
    
    sites = read_sites(content)
    
    if not sites.empty:
        result = performKSEA(raw_data, sites)
        result_high_level = performKSEA_high_level(raw_data, sites)
        
        print(len(result))
        print(len(result_high_level))
        
        return pd.DataFrame(result), pd.DataFrame(result_high_level)
    else:
        return pd.DataFrame()

def format_p_value(value):
    if value < 0.05:
        return f"{value:.2e}"
    else:
        return f"{value:.2f}"


def get_pathways_by_upid(lookup, df_p):
    # join the lookup table with the results table 
    df_p = df_p.join(lookup.set_index('UPID'), on='UPID', how='inner')
    df_p = df_p.dropna()
    # return REACTOME_NAME column as a list
    return df_p['REACTOME_NAME'].tolist()
    
    