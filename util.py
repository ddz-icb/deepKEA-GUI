import pandas as pd
from statsmodels.stats.multitest import multipletests
from scipy.stats import fisher_exact

import pandas as pd
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests

def performKSEA(raw_data, sites, correction_method):
    # Merge raw_data and sites on both SUB_ACC_ID and SUB_MOD_RSD to match sites accurately
    merged = pd.merge(raw_data, sites, on=["SUB_ACC_ID", "SUB_MOD_RSD"])

    # Group by KINASE and KIN_ACC_ID to get the counts for each kinase
    kinases = merged.groupby(['KINASE', 'KIN_ACC_ID']).size().reset_index(name='count')
    kinases = kinases.sort_values(by='count', ascending=False).reset_index(drop=True)

    # Count the number of hits for each kinase
    kinase_counts = count_kinases(kinases, raw_data)

    # Convert kinase counts to DataFrame and set KINASE as index for easy access
    kinase_counts = pd.DataFrame(kinase_counts, columns=["KINASE", "COUNT", "UPID"])
    kinase_counts = kinase_counts.set_index("KINASE")

    # Calculate p-values using Fisher's exact test
    results = calculate_p_vals(kinase_counts, kinases, merged, raw_data, "Deep")

    # Convert results to DataFrame and adjust p-values for multiple testing using FDR (Benjamini-Hochberg)
    results = pd.DataFrame(results, columns=["KINASE", "ODDS_RATIO", "P_VALUE", "UPID", "FOUND", "SUB#"])
    results = results.sort_values(by="P_VALUE")
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method=correction_method)[1]
    results = results.reset_index(drop=True)

    # Optional: Uncomment to add Uniprot links
    # results['UPID'] = results['UPID'].apply(lambda x: f"(https://www.uniprot.org/uniprotkb/{x}/entry)")
    # results["KINASE"] = results["KINASE"].apply(lambda x: f"[{x}]")
    # results["KINASE"] = results["KINASE"] + results["UPID"]

    return results, merged

def count_kinases(kinases, _raw_data):
    kinase_counts = []
    for _, row in kinases.iterrows():
        kinase = row["KINASE"]
        upid = row["KIN_ACC_ID"]

        # Count the total number of sites (hits) for each kinase in raw_data
        site_count = len(_raw_data[_raw_data["KINASE"] == kinase])
        kinase_counts.append([kinase, site_count, upid])

    return kinase_counts


def calculate_p_vals(kinase_counts, kinases, merged, _raw_data, mode = ""):
    results = []
    
    print("Calculating p-values...")
    print("Mode: ", mode)
    
    for _, row in kinases.iterrows():
        count = row["count"]
        kinase = row["KINASE"]
        upid = row["KIN_ACC_ID"]

        # No. of hits in sample for current kinase
        x = count
        
        # Sample size
        N = len(merged)
        
        # No. of annotated substrates for current kinase
        n = len(_raw_data[_raw_data["KINASE"] == kinase])
        
        
        M = len(_raw_data)
        ###
        

        table = [   [x,     n-x     ],
                    [N-x,   M-N-n+x] ]

        print(f"Kinase: {kinase}")
        print(table)
        
        # Flatten the table to check if any value is zero (Fisher's exact test requires positive values)
        flat_list = [item for sublist in table for item in sublist]

        if all(value > 0 for value in flat_list):
            odds_ratio, p_value = fisher_exact(table, alternative='two-sided')
            odds_ratio = round(odds_ratio, 2)
            print(f"P-value: {p_value}")
            results.append([kinase, odds_ratio, p_value, upid, x, n])
        else:
            # Default values when Fisher's test is not applicable
            results.append([kinase, -1, 1, upid, x, n])

    return results


def performKSEA_high_level(raw_data, sites, correction_method):
    # Merge raw_data and sites on both SUB_ACC_ID and SUB_MOD_RSD to match sites accurately
    
    sites = sites.drop(columns=['SUB_MOD_RSD'])
    sites = sites.drop_duplicates(subset=["SUB_ACC_ID"])
    
    raw_data_cpy = raw_data.copy().drop(columns=['SUB_MOD_RSD'])
    raw_data_cpy = raw_data_cpy.drop_duplicates(subset=["KINASE","SUB_ACC_ID"])
    
    merged = pd.merge(raw_data_cpy, sites, on=["SUB_ACC_ID"])
    
    
    # Group by KINASE and KIN_ACC_ID to get the counts for each kinase
    kinases = merged.groupby(['KINASE', 'KIN_ACC_ID']).size().reset_index(name='count')
    kinases = kinases.sort_values(by='count', ascending=False).reset_index(drop=True)

    # Count the number of hits for each kinase
    kinase_counts = count_kinases(kinases, raw_data_cpy)

    # Convert kinase counts to DataFrame and set KINASE as index for easy access
    kinase_counts = pd.DataFrame(kinase_counts, columns=["KINASE", "COUNT", "UPID"])
    kinase_counts = kinase_counts.set_index("KINASE")

    # Calculate p-values using Fisher's exact test
    results = calculate_p_vals(kinase_counts, kinases, merged, raw_data_cpy, "High")

    # Convert results to DataFrame and adjust p-values for multiple testing using FDR (Benjamini-Hochberg)
    results = pd.DataFrame(results, columns=["KINASE", "ODDS_RATIO", "P_VALUE", "UPID", "FOUND", "SUB#"])
    results = results.sort_values(by="P_VALUE")
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method=correction_method)[1]
    results = results.reset_index(drop=True)

    return results, merged



def calculate_p_vals_high_level(kinase_counts, kinases, merged_unique_substrates, raw_data):
    results = []
    for index, row in kinases.iterrows():
        count = row["count"]
        kinase = row["KINASE"]
        upid = row["KIN_ACC_ID"]
        
        # Number of distinct substrates in the sample for this kinase
        sub_in_sample = count
        
        # Number of distinct substrates in the sample with other kinases
        sub_in_sample_w_other_kinase = len(merged_unique_substrates[merged_unique_substrates["KINASE"] != kinase])
        
        # Number of distinct substrates not in the sample for this kinase
        sub_not_in_sample = kinase_counts.loc[kinase, "COUNT"] - count
        
        # Distinct substrates with other kinases (total number of raw data points minus this kinase's count)
        subs_w_other_kinase = len(raw_data.drop_duplicates(subset="SUB_ACC_ID")) - kinase_counts.loc[kinase, "COUNT"]

        # Fisher's exact test
        table = [[sub_in_sample, sub_in_sample_w_other_kinase], [sub_not_in_sample, subs_w_other_kinase]]
        flat_list = [item for sublist in table for item in sublist]  # Flatten table for the check
        
        if all(value > 0 for value in flat_list):
            odds_ratio, p_value = fisher_exact(table, alternative='greater')
            odds_ratio = round(odds_ratio, 2)
            results.append([kinase, odds_ratio, p_value, upid, sub_in_sample, sub_in_sample + sub_not_in_sample])
        else:
            results.append([kinase, -1, 1, upid, sub_in_sample, sub_in_sample + sub_not_in_sample])
    
    return results



def read_sites(content):
    entries = [entry.strip() for entry in content.replace(';', '\n').splitlines() if entry]
    data = [entry.split('_') for entry in entries]
    df = pd.DataFrame(data, columns=['SUB_ACC_ID', 'UPID', 'SUB_MOD_RSD'])
    df = df.assign(SUB_MOD_RSD=df['SUB_MOD_RSD'].str.split(',')).explode('SUB_MOD_RSD')
    
    df = df.drop_duplicates()
    return df

def start_eval(content, raw_data, correction_method):
    
    sites = read_sites(content)
    
    if not sites.empty:
        result, deep_hits = performKSEA(raw_data, sites, correction_method)
        result_high_level, high_level_hits = performKSEA_high_level(raw_data, sites, correction_method)
        
        
        deep_hit_columns=['SUB_GENE', 'SUB_MOD_RSD', 'KINASE']
        deep_hits = deep_hits[deep_hit_columns]
        
        high_level_hit_columns=['SUB_GENE', 'KINASE']
        high_level_hits = high_level_hits[high_level_hit_columns]
        
        return pd.DataFrame(result), pd.DataFrame(result_high_level), deep_hits, high_level_hits
    else:
        return pd.DataFrame()

def format_p_value(value):
    if value < 0.000001:
        return f"{value:.2e}"
    else:
        return f"{value:.6f}"


def get_pathways_by_upid(lookup, df_p):
    # join the lookup table with the results table 
    df_p = df_p.join(lookup.set_index('UPID'), on='UPID', how='inner')
    df_p = df_p.dropna()
    # return REACTOME_NAME column as a list
    return df_p['REACTOME_NAME'].tolist()
    
    