import pandas as pd
from statsmodels.stats.multitest import multipletests
from scipy.stats import fisher_exact
import scipy.stats as stats
import constants
from tqdm import tqdm

tqdm.pandas()

def set_column_to_markdown(columns_dict, column):
    for col in columns_dict:
        if col['id'] == column:
            col['presentation'] = 'markdown'
    return columns_dict


def add_uniprot_link_col(df):
    if "UPID" not in df.columns:
        print("Can not generate uniprot column without uniprot ID")
    df["UPID"] = df["UPID"].apply(lambda x: f"[{x}](https://www.uniprot.org/uniprotkb/{x}/entry)")
    return df


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

    print("Initiating deep-level KSEA...")
    # print lenghts of parameters
    print("Length of kinases: ", len(kinases))
    print("Length of merged: ", len(merged))
    print("Length of raw_data: ", len(raw_data))

    # Calculate p-values using Fisher's exact test
    results = calculate_p_vals(kinases, merged, raw_data, "Deep")

    # Convert results to DataFrame and adjust p-values for multiple testing using FDR (Benjamini-Hochberg)
    results = pd.DataFrame(results, columns=["KINASE", "P_VALUE", "CHI2_P_VALUE", "UPID", "FOUND", "SUB#"])
    # results = results.sort_values(by="P_VALUE")
    # results['ADJ_P_VALUE'] = results['P_VALUE']
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method=correction_method)[1]
    results = results.reset_index(drop=True)

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


def calculate_p_vals(kinases, merged, _raw_data, mode=""):
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
        n = len(_raw_data[_raw_data["KIN_ACC_ID"] == upid])

        # No. of annotated substrates for all kinases
        M = len(_raw_data)

        table = [[x, n - x],
                [N - x, M - N - n + x]]

        # print(f"Kinase: {kinase}")
        # print(table)

        # Flatten the table to check if any value is zero (Fisher's exact test requires positive values)
        flat_list = [item for sublist in table for item in sublist]

        if all(value >= 0 for value in flat_list):
            _, fisch_exc_p_value = fisher_exact(table, alternative='greater')
            chi2, chi2_p_value, _, _ = stats.chi2_contingency(table)

            if (fisch_exc_p_value == 1):
                print("######" + str(kinase) + "############")
                print(table)
                print(f"P-value: {fisch_exc_p_value}")
                print("############################")
                
            #print(type(fisch_exc_p_value))
            if kinase == "ATM":
                print(type(chi2_p_value))
                print("P= ", chi2_p_value)
            
            if chi2_p_value.astype(float) < 0 or fisch_exc_p_value.astype(float) > 1:
                print("error")
                print("######" + str(kinase) + "############")
                print(table)

            results.append([kinase, fisch_exc_p_value, chi2_p_value, upid, x, n])
        else:
            # Default values when Fisher's test is not applicable
            results.append([kinase, -1, 2, 2, upid, x, n])

    return results


def performKSEA_high_level(raw_data, sites, correction_method):
    # Merge raw_data and sites on both SUB_ACC_ID and SUB_MOD_RSD to match sites accurately

    sites = sites.drop(columns=['SUB_MOD_RSD'])
    sites = sites.drop_duplicates(subset=["SUB_ACC_ID"])

    raw_data_cpy = raw_data.copy().drop(columns=['SUB_MOD_RSD'])
    raw_data_cpy = raw_data_cpy.drop_duplicates(subset=["KINASE", "SUB_ACC_ID"])

    merged = pd.merge(raw_data_cpy, sites, on=["SUB_ACC_ID"])

    # Group by KINASE and KIN_ACC_ID to get the counts for each kinase
    kinases = merged.groupby(['KINASE', 'KIN_ACC_ID']).size().reset_index(name='count')
    kinases = kinases.sort_values(by='count', ascending=False).reset_index(drop=True)

    # Count the number of hits for each kinase
    kinase_counts = count_kinases(kinases, raw_data_cpy)

    # Convert kinase counts to DataFrame and set KINASE as index for easy access
    kinase_counts = pd.DataFrame(kinase_counts, columns=["KINASE", "COUNT", "UPID"])
    kinase_counts = kinase_counts.set_index("KINASE")

    print("Initiating high-level KSEA...")
    # print lenghts of parameters
    print("Length of kinases: ", len(kinases))
    print("Length of merged: ", len(merged))
    print("Length of raw_data_cpy: ", len(raw_data_cpy))

    # Calculate p-values using Fisher's exact test
    results = calculate_p_vals(kinases, merged, raw_data_cpy, "High")

    # Convert results to DataFrame and adjust p-values for multiple testing using FDR (Benjamini-Hochberg)
    results = pd.DataFrame(results, columns=["KINASE", "P_VALUE", "CHI2_P_VALUE", "UPID", "FOUND", "SUB#"])
    results = results.sort_values(by="P_VALUE")
    # results['ADJ_P_VALUE'] = results['P_VALUE']
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method=correction_method)[1]
    results = results.reset_index(drop=True)

    return results, merged


##############
# DEPRECATED #
##############
# def calculate_p_vals_high_level(kinase_counts, kinases, merged_unique_substrates, raw_data):
#     results = []
#     for index, row in kinases.iterrows():
#         count = row["count"]
#         kinase = row["KINASE"]
#         upid = row["KIN_ACC_ID"]

#         # Number of distinct substrates in the sample for this kinase
#         sub_in_sample = count

#         # Number of distinct substrates in the sample with other kinases
#         sub_in_sample_w_other_kinase = len(merged_unique_substrates[merged_unique_substrates["KINASE"] != kinase])

#         # Number of distinct substrates not in the sample for this kinase
#         sub_not_in_sample = kinase_counts.loc[kinase, "COUNT"] - count

#         # Distinct substrates with other kinases (total number of raw data points minus this kinase's count)
#         subs_w_other_kinase = len(raw_data.drop_duplicates(subset="SUB_ACC_ID")) - kinase_counts.loc[kinase, "COUNT"]

#         # Fisher's exact test
#         table = [[sub_in_sample, sub_in_sample_w_other_kinase], [sub_not_in_sample, subs_w_other_kinase]]
#         flat_list = [item for sublist in table for item in sublist]  # Flatten table for the check

#         if all(value > 0 for value in flat_list):
#             odds_ratio, p_value = fisher_exact(table, alternative='greater')
#             odds_ratio = round(odds_ratio, 2)
#             results.append([kinase, odds_ratio, p_value, upid, sub_in_sample, sub_in_sample + sub_not_in_sample])
#         else:
#             results.append([kinase, -1, 1, upid, sub_in_sample, sub_in_sample + sub_not_in_sample])

#     return results


def read_sites(content):
    entries = [entry.strip() for entry in content.replace(';', '\n').splitlines() if entry]
    data = [entry.split('_') for entry in entries]
    df = pd.DataFrame(data, columns=['SUB_ACC_ID', 'UPID', 'SUB_MOD_RSD'])
    df = df.assign(SUB_MOD_RSD=df['SUB_MOD_RSD'].str.split(',')).explode('SUB_MOD_RSD')

    # remove rows where second characters in SUB_MOD_RSD is not a digit
    df = df[df['SUB_MOD_RSD'].str[1:].str.isdigit()]
    
    df = df.drop_duplicates()
    return df


def start_eval(content, raw_data, correction_method, rounding=False, aa_mode='exact', tolerance=0):
    sites = read_sites(content)

    if not sites.empty:
        site_result, site_hits = start_fuzzy_enrichment(
            content=content,
            raw_data=raw_data,
            correction_method=correction_method,
            rounding=rounding,
            aa_mode=aa_mode,
            tolerance=tolerance
        )
        sub_results, sub_hits = performKSEA_high_level(raw_data, sites, correction_method)

        
        #print(sub_results[sub_results["KINASE"] == "ATM"])
        
        if site_result.isnull().values.any() or sub_results.isnull().values.any():
            print("Warning: site_result or sub_results contains null or NA values.")
        
        site_hit_columns = ['SUB_GENE', 'SUB_MOD_RSD_sample', 'SUB_MOD_RSD_bg', 'KINASE', 'IMPUTED']
        site_hits = site_hits[site_hit_columns]

        high_level_hit_columns = ['SUB_GENE', 'KINASE']
        sub_hits = sub_hits[high_level_hit_columns]

        # if rounding:
            # round_p_values(site_result, sub_results)


        return site_result, sub_results, site_hits, sub_hits
    else:
        return pd.DataFrame()


def round_p_values(site_result, sub_results):
    site_result["P_VALUE"] = (
        site_result["P_VALUE"].astype(float).apply(format_p_value)
    )
    site_result["ADJ_P_VALUE"] = (
        site_result["ADJ_P_VALUE"].astype(float).apply(format_p_value)
    )
    site_result["CHI2_P_VALUE"] = (
        site_result["CHI2_P_VALUE"].astype(float).apply(format_p_value)
    )
    sub_results["P_VALUE"] = (
        sub_results["P_VALUE"].astype(float).apply(format_p_value)
    )
    sub_results["ADJ_P_VALUE"] = (
        site_result["ADJ_P_VALUE"].astype(float).apply(format_p_value)
    )
    sub_results["CHI2_P_VALUE"] = (
        site_result["CHI2_P_VALUE"].astype(float).apply(format_p_value)
    )


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

def load_psp_dataset():
    try:
        raw_data = pd.read_csv(constants.KIN_SUB_DATASET_PATH, sep="\t")
        raw_data = raw_data[raw_data["SUB_ORGANISM"] == constants.SUB_ORGANISM]
        raw_data = raw_data[raw_data["KIN_ORGANISM"] == constants.KIN_ORGANISM]
        raw_data = raw_data[
            [
                "GENE",
                "KINASE",
                "KIN_ACC_ID",
                "KIN_ORGANISM",
                "SUBSTRATE",
                "SUB_ACC_ID",
                "SUB_GENE",
                "SUB_ORGANISM",
                "SUB_MOD_RSD",
            ]
        ]
        
        return raw_data.to_dict("records")
    except Exception as e:
        print("CRITICAL ERROR LOADING PSP DATASET: ", e)

# Hilfsfunktion zum Parsen der Site-Spalte
def parse_site(site_str):
    site_str = site_str.strip()
    # split string into letter and number
    if not isinstance(site_str, str) or len(site_str) < 2:
        raise ValueError(f"Ungültiges Format für site_str: {site_str}")
    
    # print(f"Parsing site_str: {site_str}")
    # print(f"AA: {site_str[0]}")
    # print(f"Position: {site_str[1:]}")
    # print("A")
    
    return site_str[0], int(site_str[1:])

# Aminosäurevergleich je nach Modus
def aa_match(aa1, aa2, aa_mode):
    if aa_mode == 'ignore':
        return True
    elif aa_mode == 'exact':
        return aa1 == aa2
    elif aa_mode == 'ST-similar':
        if aa1 == aa2:
            return True
        if {aa1, aa2} <= {'S', 'T'}:
            return True
        return False
    else:
        raise ValueError(f"Unbekannter aa_mode: {aa_mode}")

# Fuzzy Join Funktion
def fuzzy_join(samples, background, tolerance=0, aa_mode='exact'):
    
    samples = samples.copy()
    background = background.copy()

    # AA + Pos extrahieren
    samples[['AA', 'Pos']] = samples['SUB_MOD_RSD'].progress_apply(parse_site).progress_apply(pd.Series)
    background[['AA', 'Pos']] = background['SUB_MOD_RSD'].progress_apply(parse_site).progress_apply(pd.Series)
    print("Applying fuzzy matching...")
    # Merge über UniprotID
    merged = samples.merge(background, on='SUB_ACC_ID', suffixes=('_sample', '_bg'))

    # Fuzzy-Matching
    def match_and_flag(row):
        if aa_match(row['AA_sample'], row['AA_bg'], aa_mode):
            distance = abs(row['Pos_sample'] - row['Pos_bg'])
            if distance <= tolerance:
                return True, distance > 0
        return False, None

    # Apply Matching
    
    tqdm.pandas(desc="Matching rows")
    results = merged.progress_apply(lambda row: match_and_flag(row), axis=1)
    merged[['match', 'IMPUTED']] = pd.DataFrame(results.tolist(), index=merged.index)

    # Nur passende behalten
    filtered = merged[merged['match']].copy()
    
    print("Filtered columns: ", filtered.columns)
    # rename gene column to SUB_GENE
    filtered.rename(columns={'GENE': 'SUB_GENE'}, inplace=True)
    
    return filtered[['SUB_ACC_ID', 'SUB_MOD_RSD_sample', 'SUB_MOD_RSD_bg', 'KINASE','KIN_ACC_ID','IMPUTED', "SUB_GENE"]]


def calculate_fuzzy_p_vals(kinases, merged, _raw_data, mode="limit"):
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
        n = len(_raw_data[_raw_data["KIN_ACC_ID"] == upid])

        # No. of annotated substrates for all kinases
        M = len(_raw_data)
        
        if mode == "limit":
            if x > n:
                x = n
                print(f"Warning: x ({x}) is greater than n ({n}) for kinase {kinase}. Limiting x to n.")

        table = [[x, n - x],
                [N - x, M - N - n + x]]

        # print(f"Kinase: {kinase}")
        # print(table)

        # Flatten the table to check if any value is zero (Fisher's exact test requires positive values)
        flat_list = [item for sublist in table for item in sublist]

        if all(value >= 0 for value in flat_list):
            _, fisch_exc_p_value = fisher_exact(table, alternative='greater')
            chi2, chi2_p_value, _, _ = stats.chi2_contingency(table)

            if (fisch_exc_p_value == 1):
                print("######" + str(kinase) + "############")
                print(table)
                print(f"P-value: {fisch_exc_p_value}")
                print("############################")
                
            #print(type(fisch_exc_p_value))
            if kinase == "ATM":
                print(type(chi2_p_value))
                print("P= ", chi2_p_value)
            
            if chi2_p_value.astype(float) < 0 or fisch_exc_p_value.astype(float) > 1:
                print("error")
                print("######" + str(kinase) + "############")
                print(table)

            results.append([kinase, fisch_exc_p_value, chi2_p_value, upid, x, n])
        else:
            # Default values when Fisher's test is not applicable
            results.append([kinase, -1, 2, 2, upid, x, n])

    return results



def perform_fuzzy_enrichment(raw_data, sites, correction_method, tolerance=0, aa_mode='exact'):
    #### Platzhalter TODO FIXME 
    
    fuzzy_merged = fuzzy_join(
        samples=sites,
        background=pd.DataFrame(raw_data),
        tolerance=tolerance,
        aa_mode=aa_mode
    )
    print(fuzzy_merged)
    kinases = fuzzy_merged.groupby(['KINASE', 'KIN_ACC_ID']).size().reset_index(name='count')
    kinases = kinases.sort_values(by='count', ascending=False).reset_index(drop=True)
    # Count the number of hits for each kinase
    kinase_counts = count_kinases(kinases, raw_data)
    # Convert kinase counts to DataFrame and set KINASE as index for easy access
    kinase_counts = pd.DataFrame(kinase_counts, columns=["KINASE", "COUNT", "UPID"])
    kinase_counts = kinase_counts.set_index("KINASE")
    
    results = calculate_fuzzy_p_vals(kinases, fuzzy_merged, raw_data)
    # Convert results to DataFrame and adjust p-values for multiple testing using FDR (Benjamini-Hochberg)
    results = pd.DataFrame(results, columns=["KINASE", "P_VALUE", "CHI2_P_VALUE", "UPID", "FOUND", "SUB#"])
    # results = results.sort_values(by="P_VALUE")
    # results['ADJ_P_VALUE'] = results['P_VALUE']
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method=correction_method)[1]
    results = results.reset_index(drop=True)
    return results, fuzzy_merged

def start_fuzzy_enrichment(content, raw_data, correction_method, rounding=False, aa_mode='exact', tolerance=0):
    sites = read_sites(content)

    if not sites.empty:
        fuzzy_result, fuzzy_hits = perform_fuzzy_enrichment(raw_data, sites, correction_method, aa_mode=aa_mode, tolerance=tolerance)
        
        if fuzzy_result.isnull().values.any():
            print("Warning: site_result or sub_results contains null or NA values.")
        
        fuzzy_hit_columns = ['SUB_GENE', 'SUB_MOD_RSD_sample', 'KINASE', 'KIN_ACC_ID','SUB_MOD_RSD_bg', 'IMPUTED']

        print("Fuzzy hit colums ", fuzzy_hits.columns)
        
        fuzzy_hits = fuzzy_hits[fuzzy_hit_columns]        

        # if rounding:
            # round_p_values(site_result, sub_results)

        
        
        return fuzzy_result, fuzzy_hits
    else:
        return pd.DataFrame()

