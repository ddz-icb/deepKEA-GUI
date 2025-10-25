import os

PLACEHOLDER_INPUT = """P06732_CKM_T108
O15273_TCAP_S161
Q96I15_SCLY_S129
Q8TAD8_SNIP1_S99
P23327_HRC_S145
P23327_HRC_S139, S145
O94874_UFL1_S458
Q9NP74_PALMD_S486
Q9H1E3_NUCKS1_S79"""

# Get the directory where this script is located
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.join(_BASE_DIR, "assets")

KIN_SUB_DATASET_PATH = os.path.join(_ASSETS_DIR, "Kinase_Substrate_Dataset.txt")
CUSTOM_DATASET_PATH  = os.path.join(_ASSETS_DIR, "PSP_HARRY_INTERSEC.tsv")

REACTOME_PATH = os.path.join(_ASSETS_DIR, "UniProt2Reactome_All_Levels.tsv")
SUB_ORGANISM = 'human'
KIN_ORGANISM = 'human'
ORGANISM_REACTOME = "Homo sapiens"


PRINT_TO_FILE = False
THRESHOLD = 1
QUIET = False
VIEW_ALL = False
OUTPUT_PATH = "results.txt"

APP_TITLE = "fuzzyKEA"
APP_SUBTITLE = "Fuzzy Kinase Enrichment Analysis"
APP_VERSION = "1.0.0-alpha"
STATUS = f"{APP_TITLE} v{APP_VERSION} | PSP DB last updated 14/09/2024"

# Color scheme for professional bioinformatics tool
PRIMARY_COLOR = "#1e3a5f"  # Deep blue
SECONDARY_COLOR = "#2c5f8d"  # Medium blue
ACCENT_COLOR = "#3498db"  # Bright blue
SUCCESS_COLOR = "#27ae60"  # Green
WARNING_COLOR = "#f39c12"  # Orange
DANGER_COLOR = "#e74c3c"  # Red
LIGHT_BG = "#f8f9fa"  # Light gray
DARK_TEXT = "#2c3e50"  # Dark gray

# DEFAULT_STYLE_DATA_CONDITIONAL = [
#     {'if': {'row_index': 'odd'}, 'backgroundColor': '#f5f5f5'},
#     {'if': {'row_index': 'even'}, 'backgroundColor': 'white'},
#     {'if': {'column_id': 'P_VALUE', 'filter_query': '{P_VALUE} < 0.05'},
#             'backgroundColor': '#2E6F40', 'color': 'white'},
# ]

DEFAULT_STYLE_DATA_CONDITIONAL = [
    {'if': {'row_index': 'odd'}, 'backgroundColor': LIGHT_BG},
    {'if': {'row_index': 'even'}, 'backgroundColor': 'white'},
    {
        'if': {'column_id': 'P_VALUE', 'filter_query': '{P_VALUE} < 0.05'},
        'backgroundColor': SUCCESS_COLOR,
        'color': 'white',
        'fontWeight': '500'
    },
    {
        'if': {'column_id': 'ADJ_P_VALUE', 'filter_query': '{ADJ_P_VALUE} < 0.05'},
        'backgroundColor': SUCCESS_COLOR,
        'color': 'white',
        'fontWeight': '500'
    },
    {
        'if': {'column_id': 'KINASE'},
        'fontWeight': 'bold',
        'color': PRIMARY_COLOR
    },
    {
        "if": {"column_id": "UPID"},
        "color": ACCENT_COLOR,
        "textAlign": "center",
        "textDecoration": "underline",
    },
    {
        'if': {
        'column_id': 'IMPUTED',
        'filter_query': '{IMPUTED} = "false"'},
        'fontWeight': 'bold'
    },
]


DEFAULT_CELL_STYLE = {
    'textAlign': 'center',
    'fontSize': '14px',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    'padding': '10px',
    }

DEFAULT_HEADER_STYLE = {
    'backgroundColor': PRIMARY_COLOR,
    'color': 'white',
    'fontWeight': 'bold',
    'textAlign': 'center',
    'fontSize': '14px',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    'padding': '12px',
}

BAR_COLORSCALE = "Viridis"

STORAGE_TYPE = "session"
DEFAULT_DOWNLOAD_FILE_NAME = "fuzzyKEA_results"

# Statistical test methods
STATISTICAL_TEST_METHODS = [
    {"label": "Fisher's Exact Test", "value": "fisher"},
    {"label": "Chi-Square Test", "value": "chi2"},
]

# Multiple testing correction methods
CORRECTION_METHODS = [
    {"label": "Benjamini-Hochberg (FDR)", "value": "fdr_bh"},
    {"label": "Benjamini-Yekutieli (FDR-BY)", "value": "fdr_by"},
    {"label": "Bonferroni", "value": "bonferroni"},
]