import pandas as pd
import os
import logging
import sys
from datetime import datetime
from statsmodels.stats.multitest import multipletests
from scipy.stats import fisher_exact
import scipy.stats as stats
import constants
from tqdm import tqdm

tqdm.pandas()

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    FORMATS = {
        logging.DEBUG: Colors.BRIGHT_BLACK + '%(asctime)s [DEBUG] %(name)s: %(message)s' + Colors.RESET,
        logging.INFO: Colors.BRIGHT_CYAN + '%(asctime)s' + Colors.RESET + ' [' + Colors.GREEN + 'INFO' + Colors.RESET + '] ' + Colors.CYAN + '%(name)s' + Colors.RESET + ': %(message)s',
        logging.WARNING: Colors.BRIGHT_CYAN + '%(asctime)s' + Colors.RESET + ' [' + Colors.YELLOW + 'WARN' + Colors.RESET + '] ' + Colors.CYAN + '%(name)s' + Colors.RESET + ': ' + Colors.YELLOW + '%(message)s' + Colors.RESET,
        logging.ERROR: Colors.BRIGHT_CYAN + '%(asctime)s' + Colors.RESET + ' [' + Colors.RED + 'ERROR' + Colors.RESET + '] ' + Colors.CYAN + '%(name)s' + Colors.RESET + ': ' + Colors.RED + '%(message)s' + Colors.RESET,
        logging.CRITICAL: Colors.BRIGHT_CYAN + '%(asctime)s' + Colors.RESET + ' [' + Colors.BRIGHT_RED + Colors.BOLD + 'CRITICAL' + Colors.RESET + '] ' + Colors.CYAN + '%(name)s' + Colors.RESET + ': ' + Colors.BRIGHT_RED + Colors.BOLD + '%(message)s' + Colors.RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

# Configure logging system with colors
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter())

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)

logger = logging.getLogger('fuzzyKEA')
logger.setLevel(logging.INFO)

def log_info(message, user_context=None):
    """Structured logging with optional user context"""
    if user_context:
        logger.info(f"[User: {user_context}] {message}")
    else:
        logger.info(message)

def log_warning(message, user_context=None):
    """Warning logging"""
    if user_context:
        logger.warning(f"[User: {user_context}] {message}")
    else:
        logger.warning(message)

def log_error(message, exception=None, user_context=None):
    """Structured error logging"""
    prefix = f"[User: {user_context}] " if user_context else ""
    if exception:
        logger.error(f"{prefix}{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(f"{prefix}{message}")

def log_debug(message, user_context=None):
    """Debug logging"""
    if user_context:
        logger.debug(f"[User: {user_context}] {message}")
    else:
        logger.debug(message)

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


def performKSEA(raw_data, sites, correction_method, statistical_test='fisher'):
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

    log_info("Initiating site-level KSEA analysis")
    log_info(f"Statistical test: {statistical_test}")
    log_info(f"Dataset sizes - Kinases: {len(kinases)}, Merged: {len(merged)}, Raw data: {len(raw_data)}")

    # Calculate p-values using specified statistical test
    results = calculate_p_vals(kinases, merged, raw_data, statistical_test, "Site")

    # Convert results to DataFrame and adjust p-values for multiple testing
    results = pd.DataFrame(results, columns=["KINASE", "P_VALUE", "UPID", "FOUND", "SUB#"])
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


def calculate_p_vals(kinases, merged, _raw_data, statistical_test='fisher', mode=""):
    """
    Calculate p-values using Fisher's Exact Test or Chi-Square Test.
    
    Args:
        kinases: DataFrame with kinase information
        merged: Merged data
        _raw_data: Raw dataset
        statistical_test: 'fisher' or 'chi2'
        mode: Description of the mode for logging
    
    Returns:
        List of results: [KINASE, P_VALUE, UPID, FOUND, SUB#]
    """
    results = []

    print(f"Calculating p-values using {statistical_test} test...")
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

        # Flatten the table to check if any value is valid
        flat_list = [item for sublist in table for item in sublist]

        if all(value >= 0 for value in flat_list):
            if statistical_test == 'fisher':
                _, p_value = fisher_exact(table, alternative='greater')
            elif statistical_test == 'chi2':
                _, p_value, _, _ = stats.chi2_contingency(table)
            else:
                print(f"Warning: Unknown statistical test '{statistical_test}', defaulting to Fisher's exact")
                _, p_value = fisher_exact(table, alternative='greater')
            
            # Validation
            if p_value < 0 or p_value > 1:
                print(f"Warning: Invalid p-value {p_value} for kinase {kinase}")
                print(table)
            
            results.append([kinase, p_value, upid, x, n])
        else:
            # Default values when test is not applicable
            results.append([kinase, 1.0, upid, x, n])

    return results


def performKSEA_high_level(raw_data, sites, correction_method, statistical_test='fisher'):
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

    print("Initiating substrate-level KSEA...")
    log_info("Initiating substrate-level KSEA analysis")
    log_info(f"Statistical test: {statistical_test}")
    log_info(f"Dataset sizes - Kinases: {len(kinases)}, Merged: {len(merged)}, Raw data: {len(raw_data_cpy)}")

    # Calculate p-values using specified statistical test
    results = calculate_p_vals(kinases, merged, raw_data_cpy, statistical_test, "Substrate")

    # Convert results to DataFrame and adjust p-values for multiple testing
    results = pd.DataFrame(results, columns=["KINASE", "P_VALUE", "UPID", "FOUND", "SUB#"])
    results = results.sort_values(by="P_VALUE")
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
    # Zerlege den Input in Einträge
    entries = [entry.strip() for entry in content.replace(';', '\n').splitlines() if entry]
    # Spalte jeden Eintrag anhand von '_'
    data = [entry.split('_') for entry in entries]
    df = pd.DataFrame(data, columns=['SUB_ACC_ID', 'UPID', 'SUB_MOD_RSD'])
    
    # Zerlege SUB_MOD_RSD an ',' und entferne Leerzeichen
    df['SUB_MOD_RSD'] = df['SUB_MOD_RSD'].str.split(',').apply(lambda x: [s.strip() for s in x])
    df = df.explode('SUB_MOD_RSD')

    # Behalte nur Zeilen, bei denen das zweite Zeichen eine Ziffer ist (z. B. S2246)
    df = df[df['SUB_MOD_RSD'].str[1:].str.isdigit()]
    
    return df.drop_duplicates()


def start_eval(content, raw_data, correction_method, statistical_test='fisher', rounding=False, aa_mode='exact', tolerance=0, selected_amino_acids = None, inferred_hit_limit = None):
    log_info(f"Starting evaluation with amino acids: {selected_amino_acids}")
    log_info(f"Statistical test method: {statistical_test}")
    
    if raw_data is not None and not raw_data.empty and 'SUB_MOD_RSD' in raw_data.columns and selected_amino_acids:
        # Extrahiere den ersten Buchstaben (die Aminosäure) aus SUB_MOD_RSD
        # Diese Logik muss an dein genaues Datenformat angepasst werden!
        # z.B. wenn SUB_MOD_RSD 'S123' ist, wollen wir 'S'
        try:
            # filter raw_data and only keep rows where SUB_MOD_RSD starts with one of the selected amino acids
            original_rows = len(raw_data)
            raw_data = raw_data[raw_data['SUB_MOD_RSD'].str[0].isin(selected_amino_acids)]
            print(f"Filtered raw_data from {original_rows} to {len(raw_data)} rows based on selected amino acids: {selected_amino_acids}")
            
            
            print(f"Util: Filtered raw_data from {original_rows} to {len(raw_data)} rows based on selected amino acids: {selected_amino_acids}")
            if raw_data.empty:
                print("WARNUNG: Nach Filterung der Aminosäuren ist raw_data leer.")
                # Rückgabe leerer DataFrames, wenn nach Filterung nichts übrig bleibt
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        except Exception as e:
            print(f"FEHLER beim Filtern nach Aminosäuren: {e}")
            # Eventuell hier auch leere DataFrames zurückgeben oder Fehler weiterleiten
    
    sites = read_sites(content)

    if not sites.empty:
        site_result, site_hits = start_fuzzy_enrichment(
            content=content,
            raw_data=raw_data,
            correction_method=correction_method,
            statistical_test=statistical_test,
            rounding=rounding,
            aa_mode=aa_mode,
            tolerance=tolerance,
            inferred_hit_limit=inferred_hit_limit
        )
        sub_results, sub_hits = performKSEA_high_level(raw_data, sites, correction_method, statistical_test)

        
        #print(sub_results[sub_results["KINASE"] == "ATM"])
        
        if site_result.isnull().values.any() or sub_results.isnull().values.any():
            print("Warning: site_result or sub_results contains null or NA values.")
        
        site_hit_columns = ['SUB_GENE',"SUB_ACC_ID",'SUB_MOD_RSD_sample', 'SUB_MOD_RSD_bg', 'KINASE', 'IMPUTED']
        site_hits = site_hits[site_hit_columns]

        high_level_hit_columns = ['SUB_GENE', 'KINASE']
        sub_hits = sub_hits[high_level_hit_columns]

        # if rounding:
            # round_p_values(site_result, sub_results)


        return site_result, sub_results, site_hits, sub_hits
    else:
        return pd.DataFrame()


def round_p_values(site_result, sub_results):
    """Round p-values for display purposes."""
    site_result["P_VALUE"] = site_result["P_VALUE"].astype(float).apply(format_p_value)
    site_result["ADJ_P_VALUE"] = site_result["ADJ_P_VALUE"].astype(float).apply(format_p_value)
    
    sub_results["P_VALUE"] = sub_results["P_VALUE"].astype(float).apply(format_p_value)
    sub_results["ADJ_P_VALUE"] = sub_results["ADJ_P_VALUE"].astype(float).apply(format_p_value)


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
        if not os.path.exists(constants.KIN_SUB_DATASET_PATH):
            error_msg = f"Dataset file not found at: {constants.KIN_SUB_DATASET_PATH}"
            print(f"CRITICAL ERROR: {error_msg}")
            print(f"Please ensure the file exists in the assets/ folder.")
            print(f"Expected path: {os.path.abspath(constants.KIN_SUB_DATASET_PATH)}")
            return []
        
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
        return []

# Hilfsfunktion zum Parsen der Site-Spalte
def parse_site(site_str):
    """Parse a site string like 'S123' into amino acid and position."""
    try:
        if pd.isna(site_str):
            return None, None
        
        site_str = str(site_str).strip()
        
        if len(site_str) < 2:
            print(f"Warning: Invalid site format (too short): '{site_str}'")
            return None, None
        
        aa = site_str[0]
        pos_str = site_str[1:]
        
        # Check if position is a valid number
        if not pos_str.lstrip('-').isdigit():
            print(f"Warning: Invalid position in site: '{site_str}'")
            return None, None
        
        pos = int(pos_str)
        
        return aa, pos
    except Exception as e:
        print(f"Warning: Error parsing site '{site_str}': {e}")
        return None, None

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

def limit_inferred_hits(df, inferred_hit_limit):
    """
    Limit the number of inferred (fuzzy-matched) hits per kinase.
    Keeps all exact matches and only the closest inferred hits up to the limit.
    
    Args:
        df: DataFrame with matched sites
        inferred_hit_limit: Maximum number of inferred hits to keep per kinase
    
    Returns:
        DataFrame with limited inferred hits
    """
    if df.empty:
        return df
    
    if "SUB_MOD_RSD_sample" not in df.columns:
        print(f"ERROR: SUB_MOD_RSD_sample not in columns. Available columns: {list(df.columns)}")
        raise ValueError("DataFrame must contain 'SUB_MOD_RSD_sample' column to limit inferred hits.")
    
    if "SUB_MOD_RSD_bg" not in df.columns:
        print(f"ERROR: SUB_MOD_RSD_bg not in columns. Available columns: {list(df.columns)}")
        raise ValueError("DataFrame must contain 'SUB_MOD_RSD_bg' column to limit inferred hits.")
    
    # Work on a copy and reset index immediately to avoid alignment issues
    df = df.copy().reset_index(drop=True)
    
    log_debug(f"limit_inferred_hits: Processing {df.shape[0]} hits")
    
    # Calculate position difference - handle parsing errors
    def safe_extract_pos(site_str):
        """Safely extract position from site string."""
        try:
            if pd.isna(site_str):
                return None
            site_str = str(site_str).strip()
            if len(site_str) < 2:
                return None
            pos_part = site_str[1:]
            if not pos_part.lstrip('-').isdigit():
                return None
            return int(pos_part)
        except (ValueError, IndexError) as e:
            print(f"Warning: Could not extract position from '{site_str}': {e}")
            return None
    
    df["sample_pos"] = df["SUB_MOD_RSD_sample"].apply(safe_extract_pos)
    df["bg_pos"] = df["SUB_MOD_RSD_bg"].apply(safe_extract_pos)
    
    # Remove rows where position extraction failed
    before_drop = len(df)
    try:
        df = df.dropna(subset=["sample_pos", "bg_pos"]).copy()
        if len(df) < before_drop:
            log_warning(f"Removed {before_drop - len(df)} rows with invalid positions")
    except Exception as e:
        log_error("Error during position filtering", e)
        raise
    
    if df.empty:
        log_warning("No valid positions found in limit_inferred_hits, returning empty DataFrame")
        return pd.DataFrame(columns=df.columns)
    
    try:
        df["pos_diff"] = abs(df["sample_pos"] - df["bg_pos"])
    except Exception as e:
        log_error("Error calculating position difference", e)
        raise
    
    # For each kinase, keep all exact matches + closest inferred hits up to limit
    result_rows = []
    try:
        for kinase, group in df.groupby("KINASE"):
            # Reset index for the group to avoid negative index issues
            group = group.reset_index(drop=True).copy()
            log_debug(f"Processing kinase: {kinase}, {group.shape[0]} hits")
            
            # Convert IMPUTED to boolean explicitly to avoid indexing issues
            imputed_mask = group["IMPUTED"].astype(bool)
            
            # Separate exact matches from inferred using .loc to be explicit
            exact_mask = ~imputed_mask
            
            exact = group.loc[exact_mask].copy()
            inferred = group.loc[imputed_mask].copy()
            log_debug(f"Kinase {kinase} - exact: {len(exact)}, inferred: {len(inferred)}")
            
            # Sort inferred by position difference and keep only the closest ones
            if not inferred.empty and inferred_hit_limit > 0:
                inferred = inferred.sort_values("pos_diff", ascending=True).head(inferred_hit_limit)
            elif inferred_hit_limit == 0:
                inferred = pd.DataFrame(columns=group.columns)
            
            # Combine exact and limited inferred hits
            kinase_hits = pd.concat([exact, inferred], ignore_index=True)
            result_rows.append(kinase_hits)
        
        log_debug(f"Finished processing {len(result_rows)} kinases")
    except Exception as e:
        log_error("Error in kinase grouping loop", e)
        raise
    
    log_info(f"Before limiting: {len(df)} total hits")
    try:
        df_limited = pd.concat(result_rows, ignore_index=True) if result_rows else pd.DataFrame(columns=df.columns)
        log_info(f"After limiting: {len(df_limited)} total hits (max {inferred_hit_limit} inferred per kinase)")
    except Exception as e:
        log_error("Error concatenating results", e)
        raise
    
    # Clean up temporary columns
    try:
        df_limited = df_limited.drop(columns=["sample_pos", "bg_pos", "pos_diff"])
    except Exception as e:
        log_error(f"Error dropping temporary columns. Available: {list(df_limited.columns)}", e)
        raise
    
    return df_limited
    
    
# Fuzzy Join Funktion
def fuzzy_join(samples, background, tolerance=0, aa_mode='exact', inferred_hit_limit=None):
    """
    Fuzzy matching of sample sites to background database sites.
    Each sample site is matched to AT MOST ONE database site (the closest one by position).
    
    Args:
        samples: DataFrame with sample sites
        background: DataFrame with database sites
        tolerance: Maximum position difference allowed
        aa_mode: Amino acid matching mode ('exact', 'st-similar', 'ignore')
        inferred_hit_limit: Maximum number of inferred hits per kinase
    
    Returns:
        DataFrame with matched sites, each sample site matched to max 1 DB site
    """
    
    samples = samples.copy()
    background = background.copy()

    # AA + Pos extrahieren
    log_info("Parsing sample sites...")
    samples[['AA', 'Pos']] = samples['SUB_MOD_RSD'].progress_apply(parse_site).progress_apply(pd.Series)
    
    log_info("Parsing background sites...")
    background[['AA', 'Pos']] = background['SUB_MOD_RSD'].progress_apply(parse_site).progress_apply(pd.Series)
    
    # Remove rows with invalid sites (None values)
    samples_before = len(samples)
    samples = samples.dropna(subset=['AA', 'Pos'])
    if len(samples) < samples_before:
        print(f"Warning: Removed {samples_before - len(samples)} invalid sample sites")
    
    background_before = len(background)
    background = background.dropna(subset=['AA', 'Pos'])
    if len(background) < background_before:
        print(f"Warning: Removed {background_before - len(background)} invalid background sites")
    
    if samples.empty:
        print("Error: No valid sample sites after parsing!")
        return pd.DataFrame(columns=['SUB_ACC_ID', 'SUB_MOD_RSD_sample', 'SUB_MOD_RSD_bg', 
                                     'KINASE', 'KIN_ACC_ID', 'IMPUTED', 'SUB_GENE'])
    
    if background.empty:
        print("Error: No valid background sites after parsing!")
        return pd.DataFrame(columns=['SUB_ACC_ID', 'SUB_MOD_RSD_sample', 'SUB_MOD_RSD_bg', 
                                     'KINASE', 'KIN_ACC_ID', 'IMPUTED', 'SUB_GENE'])
    
    log_info("Applying fuzzy matching with 1:1 constraint (closest match)...")
    
    # Merge über UniprotID
    merged = samples.merge(background, on='SUB_ACC_ID', suffixes=('_sample', '_bg'))

    # Fuzzy-Matching mit Position-Distanz
    def match_and_calculate_distance(row):
        if aa_match(row['AA_sample'], row['AA_bg'], aa_mode):
            distance = abs(row['Pos_sample'] - row['Pos_bg'])
            if distance <= tolerance:
                is_imputed = distance > 0
                return True, is_imputed, distance
        return False, None, None

    # Apply Matching
    tqdm.pandas(desc="Matching rows")
    results = merged.progress_apply(lambda row: match_and_calculate_distance(row), axis=1)
    merged[['match', 'IMPUTED', 'pos_distance']] = pd.DataFrame(results.tolist(), index=merged.index)

    # Nur passende behalten
    filtered = merged[merged['match']].copy()
    
    if filtered.empty:
        print("Warning: No matches found!")
        return pd.DataFrame(columns=['SUB_ACC_ID', 'SUB_MOD_RSD_sample', 'SUB_MOD_RSD_bg', 
                                     'KINASE', 'KIN_ACC_ID', 'IMPUTED', 'SUB_GENE'])
    
    log_info(f"Total matches before deduplication: {len(filtered)}")
    
    # CRITICAL: Each sample site should map to ONLY ONE database site
    # Group by sample identifier (SUB_ACC_ID + SUB_MOD_RSD_sample) and keep only the closest match
    filtered = filtered.copy()  # Ensure we're working with a copy
    filtered['sample_site_id'] = filtered['SUB_ACC_ID'] + '_' + filtered['SUB_MOD_RSD_sample']
    
    # Sort by distance and keep only the first (closest) match for each sample site
    filtered = filtered.sort_values('pos_distance')
    filtered_unique = filtered.drop_duplicates(subset=['sample_site_id'], keep='first').copy()
    
    log_info(f"Matches after 1:1 deduplication: {len(filtered_unique)} (closest match per input site)")
    log_info(f"Removed {len(filtered) - len(filtered_unique)} duplicate mappings")
    
    # Determine which GENE column to use (from sample or background)
    if 'GENE_sample' in filtered_unique.columns:
        gene_col = 'GENE_sample'
    elif 'GENE_bg' in filtered_unique.columns:
        gene_col = 'GENE_bg'
    elif 'GENE' in filtered_unique.columns:
        gene_col = 'GENE'
    elif 'SUB_GENE_bg' in filtered_unique.columns:
        gene_col = 'SUB_GENE_bg'
    elif 'SUB_GENE_sample' in filtered_unique.columns:
        gene_col = 'SUB_GENE_sample'
    else:
        print("Warning: No GENE column found in filtered data!")
        print(f"Available columns: {list(filtered_unique.columns)}")
        gene_col = None
    
    # Create SUB_GENE column
    if gene_col and gene_col != 'SUB_GENE':
        filtered_unique = filtered_unique.copy()
        filtered_unique['SUB_GENE'] = filtered_unique[gene_col]
    elif not gene_col:
        # If no gene column exists, create an empty one
        filtered_unique = filtered_unique.copy()
        filtered_unique['SUB_GENE'] = ''
    
    # Select final columns
    result = filtered_unique[['SUB_ACC_ID', 'SUB_MOD_RSD_sample', 'SUB_MOD_RSD_bg', 
                              'KINASE', 'KIN_ACC_ID', 'IMPUTED', 'SUB_GENE']].copy()
    
    # APPLYING MAX INFERRED HIT LIMIT (per kinase)
    if inferred_hit_limit is not None:
        print(f"Applying inferred hit limit: {inferred_hit_limit} per kinase")
        result = limit_inferred_hits(result, inferred_hit_limit)
    
    return result


def calculate_fuzzy_p_vals(kinases, merged, _raw_data, statistical_test='fisher', mode="limit"):
    """
    Calculate p-values for fuzzy matching results.
    
    Args:
        kinases: DataFrame with kinase information
        merged: Merged fuzzy data
        _raw_data: Raw dataset
        statistical_test: 'fisher' or 'chi2'
        mode: 'limit' to cap x at n
    
    Returns:
        List of results: [KINASE, P_VALUE, UPID, FOUND, SUB#]
    """
    results = []

    print(f"Calculating fuzzy p-values using {statistical_test} test...")
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
                original_x = x
                x = n
                print(f"Warning: Capping x from {original_x} to n={n} for kinase {kinase}")

        table = [[x, n - x],
                [N - x, M - N - n + x]]

        # Flatten the table to check if any value is valid
        flat_list = [item for sublist in table for item in sublist]

        if all(value >= 0 for value in flat_list):
            if statistical_test == 'fisher':
                _, p_value = fisher_exact(table, alternative='greater')
            elif statistical_test == 'chi2':
                _, p_value, _, _ = stats.chi2_contingency(table)
            else:
                print(f"Warning: Unknown statistical test '{statistical_test}', defaulting to Fisher's exact")
                _, p_value = fisher_exact(table, alternative='greater')
            
            # Validation
            if p_value < 0 or p_value > 1:
                print(f"Warning: Invalid p-value {p_value} for kinase {kinase}")
                print(table)

            results.append([kinase, p_value, upid, x, n])
        else:
            # Default values when test is not applicable
            results.append([kinase, 1.0, upid, x, n])

    return results



def perform_fuzzy_enrichment(raw_data, sites, correction_method, statistical_test='fisher', tolerance=0, aa_mode='exact', inferred_hit_limit=None):
    
    fuzzy_merged = fuzzy_join(
        samples=sites,
        background=pd.DataFrame(raw_data),
        tolerance=tolerance,
        aa_mode=aa_mode,
        inferred_hit_limit=inferred_hit_limit
    )
    print(fuzzy_merged)
    kinases = fuzzy_merged.groupby(['KINASE', 'KIN_ACC_ID']).size().reset_index(name='count')
    kinases = kinases.sort_values(by='count', ascending=False).reset_index(drop=True)
    # Count the number of hits for each kinase
    kinase_counts = count_kinases(kinases, raw_data)
    # Convert kinase counts to DataFrame and set KINASE as index for easy access
    kinase_counts = pd.DataFrame(kinase_counts, columns=["KINASE", "COUNT", "UPID"])
    kinase_counts = kinase_counts.set_index("KINASE")
    
    results = calculate_fuzzy_p_vals(kinases, fuzzy_merged, raw_data, statistical_test)
    # Convert results to DataFrame and adjust p-values for multiple testing
    results = pd.DataFrame(results, columns=["KINASE", "P_VALUE", "UPID", "FOUND", "SUB#"])
    results['ADJ_P_VALUE'] = multipletests(results['P_VALUE'], method=correction_method)[1]
    results = results.reset_index(drop=True)
    return results, fuzzy_merged

def start_fuzzy_enrichment(content, raw_data, correction_method, statistical_test='fisher', rounding=False, aa_mode='exact', tolerance=0, inferred_hit_limit=None):
    
    sites = read_sites(content)

    if not sites.empty:
        fuzzy_result, fuzzy_hits = perform_fuzzy_enrichment(raw_data, sites, correction_method, statistical_test, aa_mode=aa_mode, tolerance=tolerance, inferred_hit_limit=inferred_hit_limit)
        
        if fuzzy_result.isnull().values.any():
            print("Warning: site_result or sub_results contains null or NA values.")
        
        fuzzy_hit_columns = ['SUB_GENE',"SUB_ACC_ID" ,'SUB_MOD_RSD_sample', 'KINASE', 'KIN_ACC_ID','SUB_MOD_RSD_bg', 'IMPUTED']

        print("Fuzzy hit colums ", fuzzy_hits.columns)
        
        fuzzy_hits = fuzzy_hits[fuzzy_hit_columns]        

        # if rounding:
            # round_p_values(site_result, sub_results)

        
        
        return fuzzy_result, fuzzy_hits
    else:
        return pd.DataFrame()

