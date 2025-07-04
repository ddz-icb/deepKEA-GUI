# layout.py
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import constants # Falls Konstanten im Layout verwendet werden
import pandas as pd
# correction_methods kann hier bleiben oder in constants.py verschoben werden
correction_methods = [
    {"label": "Benjamini-Hochberg (FDR-BH)", "value": "fdr_bh"},
    {"label": "Benjamini-Yekutieli (FDR-BY)", "value": "fdr_by"},
    {"label": "Bonferroni", "value": "bonferroni"},
]

amino_acid_options = [
    {'label': 'Serin (S)', 'value': 'S'},
    {'label': 'Threonin (T)', 'value': 'T'},
    {'label': 'Tyrosin (Y)', 'value': 'Y'},
    {'label': 'Histidin (H)', 'value': 'H'} # Histidin ist seltener, aber manchmal relevant
]
default_amino_acids = ['S', 'T', 'Y', 'H'] # Alle standardmäßig ausgewählt

df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30]
})

df_dict = df.to_dict('records')


def create_layout():
    """Erstellt und gibt das Hauptlayout der Anwendung zurück."""
    layout = dbc.Container(
        [
            
            # ... (deine bestehenden dcc.Store Komponenten) ...
            dcc.Location(id='url', refresh=False), # Wichtig für Callbacks, die auf die URL zugreifen
            dcc.Store(id="active-download-type-store", storage_type=constants.STORAGE_TYPE), # Neuer Store
            dcc.Store(id="download-filename-store", storage_type=constants.STORAGE_TYPE), # Um Dateinamen zwischenzuspeichern
            dcc.Store(id="session-id", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="site-level-results-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="sub-level-results-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="raw-data-store", storage_type=constants.STORAGE_TYPE), # Initialisiere mit None, wird durch Callback befüllt
            dcc.Store(id="site-hit-data-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="sub-hit-data-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="correction-method-store", data="fdr_bh", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="current-title-store", data=constants.DEFAULT_DOWNLOAD_FILE_NAME, storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="floppy-settings-store", storage_type=constants.STORAGE_TYPE, data={"floppy_value": 5, "matching_mode": "exact"}), # Default Werte setzen
            dcc.Store(id="selected-amino-acids-store", storage_type=constants.STORAGE_TYPE, data=default_amino_acids),
            dcc.Store(id="limit-inferred-hits-store", storage_type=constants.STORAGE_TYPE, data={"max_hits": 7}), # Neuer Store für Limitierung der Hits
            # --- Modal für Dateinamen-Eingabe ---
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Enter Download Filename")),
                    dbc.ModalBody(
                        [
                            dbc.Label("Filename (without .tsv Erweiterung):"),
                            dbc.Input(id="download-filename-input", type="text", placeholder="z.B. my_analysis_results"),
                            html.Small("The file extension will be added automatically.", className="text-muted")
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="cancel-download-modal-button", color="secondary", className="ms-auto", n_clicks=0),
                            dbc.Button("Confirm Download", id="confirm-download-modal-button", color="primary", n_clicks=0),
                        ]
                    ),
                ],
                id="download-filename-modal",
                is_open=False,
            ),
            
            # Main content
            dbc.Container(
                [
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle("Status")),
                            dbc.ModalBody(constants.STATUS),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close",
                                    id="close-modal",
                                    className="ml-auto",
                                    n_clicks=0,
                                )
                            ),
                        ],
                        id="modal",
                        is_open=False,
                    ),
                    # Row for table viewer and buttons
                    dbc.Row(
                        [
                            # Table Viewer
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Input substrates (ProForma)"),
                                            dbc.CardBody(
                                                [
                                                    dcc.Textarea(
                                                        id="text-input",
                                                        style={
                                                            "width": "100%",
                                                            "height": "27vh",
                                                            "box-sizing": "border-box",
                                                        },
                                                        placeholder="UNIPROT_GENNAME_SITE\nUNIPROT_GENNAME_SITE\nUNIPROT_GENNAME_SITE",
                                                        className="form-control rounded",
                                                    )
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                width=8,
                            ),
                            # Button Widget
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    dbc.Button(
                                                        "Start Analysis",
                                                        id="button-start-analysis",
                                                        n_clicks=0,
                                                        className="mb-3 btn-primary btn-block me-2",
                                                    ),
                                                    dbc.Button(
                                                        "Example",
                                                        id="button-example",
                                                        n_clicks=0,
                                                        className="mb-3 btn-secondary btn-block me-2",
                                                        outline=False,
                                                        color="secondary",
                                                    ),
                                                    dbc.Button(
                                                        "Status",
                                                        id="open-modal",
                                                        className="mb-3 btn-secondary btn-block me-2",
                                                        n_clicks=0,
                                                        outline=True,
                                                    ),
                                                    dcc.Upload(
                                                        id="upload-text-file",
                                                        children=dbc.Button(
                                                            "Upload File",
                                                            className="mb-3 btn-secondary btn-block me-2",
                                                        ),
                                                        multiple=False,
                                                        style={"width": "100%"},
                                                    ),
                                                    # dcc.Checklist(
                                                    #     value=[], # Default value
                                                    #     id="checkbox_custom_dataset",
                                                    #     options=[
                                                    #         {
                                                    #             "label": "Harry Only Mode",
                                                    #             "value": "harry_only", # Eindeutiger Wert
                                                    #         }
                                                    #     ],
                                                    #     className="mt-3",
                                                    # ),
                                                    html.Label("Floppy Mode:", className="mt-3"),
                                                    dcc.Slider(
                                                        id="floppy-slider",
                                                        min=0,
                                                        max=10,
                                                        step=1,
                                                        value=5, # Default-Wert
                                                        marks={i: str(i) for i in range(0, 11)},
                                                        tooltip={"placement": "bottom"},
                                                        className="mb-3"
                                                    ),
                                                    html.Label("Limit Inferred Hits:", className="mt-3"),
                                                    dcc.Slider(
                                                        id="limit-inferred-hits-slider",
                                                        min=0,
                                                        max=10,
                                                        step=1,
                                                        value=5, # Default-Wert
                                                        marks={i: str(i) for i in range(0, 11)},
                                                        tooltip={"placement": "bottom"},
                                                        className="mb-3"
                                                    ),
                                                    
                                                    
                                                    html.Label("Matching Mode:", className="mt-3"),
                                                    dcc.RadioItems(
                                                        id="matching-mode-radio",
                                                        options=[
                                                            {"label": "Ignore", "value": "ignore"},
                                                            {"label": "Exact", "value": "exact"},
                                                            {"label": "ST-similar", "value": "st-similar"},
                                                        ],
                                                        value="exact", # Default-Wert
                                                        labelStyle={"display": "inline-block", "margin-right": "15px"},
                                                    ),
                                                    
                                                    # --- HIER: Aminosäure Checkboxen ---
                                                    html.Label("Phosphorylatable Amino Acids:", className="mt-3"),
                                                        dcc.Checklist(
                                                            id="amino-acid-checklist",
                                                            options=amino_acid_options,
                                                            value=default_amino_acids, # Standardmäßig alle ausgewählt
                                                            labelStyle={'display': 'inline-block', 'margin-right': '10px', 'margin-bottom': '5px'},
                                                            className="mb-3" # Etwas Abstand nach unten
                                                        ),
                                                    # ------------------------------------
                                                    
                                                    html.Label(
                                                        "Correction Method:",
                                                        className="mt-3",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="correction-method-dropdown",
                                                        options=correction_methods,
                                                        value="fdr_bh",
                                                        clearable=False,
                                                        style={"width": "100%"},
                                                    ),
                                                    html.Br(),
                                                    html.Div(
                                                        id="correction-method-display",
                                                        style={
                                                            "fontWeight": "bold",
                                                            "color": "blue",
                                                        },
                                                    ),
                                                ]
                                            )
                                        ],
                                        style={"padding": "10px"},
                                    ),
                                    html.Div(style={"margin-bottom": "20px"}),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Row for table viewer and buttons (Modification Level)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dbc.CardHeader(
                                                            [
                                                                "Enriched kinases on modification Level",
                                                                dbc.Button(
                                                                    "Download",
                                                                    id="button-download",
                                                                    n_clicks=0,
                                                                    className="me-2",
                                                                    style={
                                                                        "backgroundColor": "rgb(4, 60, 124)", "color": "white",
                                                                        "borderColor": "rgb(4, 60, 124)", "float": "right",
                                                                        "padding": "0", "margin": "0",
                                                                    },
                                                                ),
                                                            ]
                                                        ),
                                                        width=12,
                                                    )
                                                ]
                                            ),
                                            dcc.Download(id="download-tsv"),
                                            dbc.CardBody(
                                                [
                                                    dash_table.DataTable(
                                                        id="table-viewer", columns=[], data=[],
                                                        style_table={"overflowY": "auto", "maxHeight": "500px", "overflowX": "auto"},
                                                        sort_action="native", filter_action="native",
                                                        style_header={"backgroundColor": "rgb(4, 60, 124)", "color": "white", "fontWeight": "bold"},
                                                        style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                                                        style_cell=constants.DEFAULT_CELL_STYLE,
                                                    )
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Detail view (Modification Level)"),
                                            dbc.CardBody(
                                                [
                                                    dash_table.DataTable(
                                                        id="table-viewer-deep-hits", page_size=10,
                                                        style_table={"overflowX": "auto"}, style_as_list_view=True,
                                                        style_header={"backgroundColor": "rgb(4, 60, 124)", "color": "white", "fontWeight": "bold"},
                                                        style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                                                    )
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                width=4,
                            ),
                        ], className="mb-4" # Hinzugefügt für Konsistenz
                    ),
                    html.Div(style={"margin-bottom": "20px"}), # Abstandshalter
                     # Row for table viewer and buttons (Substrate Level)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dbc.CardHeader(
                                                            [
                                                                "Enriched kinases on substrate Level",
                                                                dbc.Button(
                                                                    "Download",
                                                                    id="button-download-high-level", n_clicks=0, className="me-2",
                                                                    style={
                                                                        "backgroundColor": "rgb(4, 60, 124)", "color": "white",
                                                                        "borderColor": "rgb(4, 60, 124)", "float": "right",
                                                                        "padding": "0", "margin": "0",
                                                                    },
                                                                ),
                                                            ]
                                                        ),
                                                        width=12,
                                                    )
                                                ]
                                            ),
                                            dcc.Download(id="download-tsv-high-level"),
                                            dbc.CardBody(
                                                [
                                                    dash_table.DataTable(
                                                        id="table-viewer-high-level", columns=[], data=[],
                                                        style_table={"overflowY": "auto", "maxHeight": "500px", "overflowX": "auto"},
                                                        sort_action="native", filter_action="native",
                                                        style_header={"backgroundColor": "rgb(4, 60, 124)", "color": "white", "fontWeight": "bold"},
                                                        style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                                                        style_cell=constants.DEFAULT_CELL_STYLE,
                                                    )
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Detail view (Substrate Level)"),
                                            dbc.CardBody(
                                                [
                                                    dash_table.DataTable(
                                                        id="table-viewer-high-hits", page_size=10,
                                                        style_table={"overflowX": "auto"}, style_as_list_view=True,
                                                        style_header={"backgroundColor": "rgb(4, 60, 124)", "color": "white", "fontWeight": "bold"},
                                                        style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                                                    )
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-4",
                    ),
                    html.Div(style={"margin-bottom": "20px"}),
                    # Row for bar plots
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Enriched kinases on modification level by adj. p-value"),
                                            dbc.CardBody([dcc.Graph(id="bar-plot-site-enrichment", style={"max-height": "20%", "max-width": "100%"})]),
                                        ]
                                    )
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Enriched kinases on substrate level by adj. p-value"),
                                            dbc.CardBody([dcc.Graph(id="bar-plot-sub-enrichment", style={"max-height": "20%", "max-width": "100%"})]),
                                        ]
                                    )
                                ],
                                width=6,
                            ),
                        ],
                        className="g-4", # "g-4" für gap (Abstand) zwischen den Spalten
                    ),
                    html.Div(style={"margin-bottom": "20px"}),
                ],
                style={"padding": "20px", "width": "95%", "box-sizing": "border-box"},
                fluid=True,
            ),
        ],
        fluid=True,
    )
    return layout