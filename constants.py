placeholder = """P06732_CKM_T108
O15273_TCAP_S161
Q96I15_SCLY_S129
Q8TAD8_SNIP1_S99
P23327_HRC_S145
P23327_HRC_S139, S145
O94874_UFL1_S458
Q9NP74_PALMD_S486
Q9H1E3_NUCKS1_S79"""

KIN_SUB_DATASET_PATH = "assets/Kinase_Substrate_Dataset.txt"
CUSTOM_DATASET_PATH  = "assets/PSP_HARRY_INTERSEC.tsv"

REACTOME_PATH = "assets/UniProt2Reactome_All_Levels.tsv"
SUB_ORGANISM = 'human'
KIN_ORGANISM = 'human'
ORGANISM_REACTOME = "Homo sapiens"


PRINT_TO_FILE = False
THRESHOLD = 1
QUIET = False
VIEW_ALL = False
OUTPUT_PATH = "results.txt"

STATUS = "PSP DB last updated 14/09/2024. Unreleased alpha."

# DEFAULT_STYLE_DATA_CONDITIONAL = [
#     {'if': {'row_index': 'odd'}, 'backgroundColor': '#f5f5f5'},
#     {'if': {'row_index': 'even'}, 'backgroundColor': 'white'},
#     {'if': {'column_id': 'P_VALUE', 'filter_query': '{P_VALUE} < 0.05'},
#             'backgroundColor': '#2E6F40', 'color': 'white'},
# ]

DEFAULT_STYLE_DATA_CONDITIONAL = [
    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f5f5f5'},
    {'if': {'row_index': 'even'}, 'backgroundColor': 'white'},
    {
        'if': {'column_id': 'P_VALUE', 'filter_query': '{P_VALUE} < 0.05'},
        'backgroundColor': 'green',
        'color': 'white'
    },
    {
        'if': {'column_id': 'CHI2_P_VALUE', 'filter_query': '{CHI2_P_VALUE} < 0.05'},
        'backgroundColor': 'green',
        'color': 'white'
    },
    {
        'if': {'column_id': 'ADJ_P_VALUE', 'filter_query': '{ADJ_P_VALUE} < 0.05'},
        'backgroundColor': 'green',
        'color': 'white'
    },
    {
        'if': {'column_id': 'KINASE'},
        'fontWeight': 'bold'
    },
    {
        "if": {"column_id": "UPID"},
        "color": "black",
        "textAlign": "center",
        "textDecoration": "none",
    }
]


DEFAULT_CELL_STYLE = {
    'textAlign': 'center',
    'fontSize': '16px',
    }

BAR_COLORSCALE = "Viridis"

STORAGE_TYPE = "session"
DEFAULT_DOWNLOAD_FILE_NAME = "results.txt"