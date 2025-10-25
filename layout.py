# layout.py
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import constants

amino_acid_options = [
    {'label': 'Serine (S)', 'value': 'S'},
    {'label': 'Threonine (T)', 'value': 'T'},
    {'label': 'Tyrosine (Y)', 'value': 'Y'},
    {'label': 'Histidine (H)', 'value': 'H'}
]
default_amino_acids = ['S', 'T', 'Y', 'H']


def create_layout():
    """Creates the main layout for the fuzzyKEA application."""
    layout = dbc.Container(
        [
            # Header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.H1(constants.APP_TITLE, 
                                   style={
                                       'color': constants.PRIMARY_COLOR,
                                       'fontWeight': 'bold',
                                       'marginBottom': '0',
                                       'fontSize': '3rem',
                                       'display': 'inline-block'
                                   }),
                            dbc.Button(
                                "About",
                                id="open-about-button",
                                color="info",
                                outline=True,
                                size="sm",
                                style={
                                    'marginLeft': '20px',
                                    'verticalAlign': 'middle'
                                }
                            )
                        ], style={'textAlign': 'center'}),
                        html.P(constants.APP_SUBTITLE,
                              style={
                                  'color': constants.SECONDARY_COLOR,
                                  'fontSize': '1.2rem',
                                  'marginBottom': '5px'
                              }),
                        html.Small(f"Version {constants.APP_VERSION}",
                                  style={'color': '#6c757d'})
                    ], style={'textAlign': 'center', 'padding': '20px 0'})
                ])
            ], className="mb-4"),
            
            # About Modal
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("About fuzzyKEA")),
                dbc.ModalBody([
                    dbc.Tabs([
                        dbc.Tab(label="Overview", tab_id="tab-overview"),
                        dbc.Tab(label="Features", tab_id="tab-features"),
                        dbc.Tab(label="Citation & Credits", tab_id="tab-citation"),
                    ],
                    id="about-tabs",
                    active_tab="tab-overview",
                    ),
                    html.Div(id="about-tab-content", style={'marginTop': '20px'})
                ]),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-about-button", className="ms-auto", n_clicks=0)
                ),
            ],
            id="about-modal",
            size="xl",
            is_open=False,
            ),
            
            # Store components
            dcc.Location(id='url', refresh=False),
            dcc.Store(id="active-download-type-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="download-filename-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="session-id", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="site-level-results-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="sub-level-results-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="raw-data-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="site-hit-data-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="sub-hit-data-store", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="correction-method-store", data="fdr_bh", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="statistical-test-store", data="fisher", storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="current-title-store", data=constants.DEFAULT_DOWNLOAD_FILE_NAME, storage_type=constants.STORAGE_TYPE),
            dcc.Store(id="floppy-settings-store", storage_type=constants.STORAGE_TYPE, data={"floppy_value": 5, "matching_mode": "exact"}),
            dcc.Store(id="selected-amino-acids-store", storage_type=constants.STORAGE_TYPE, data=default_amino_acids),
            dcc.Store(id="limit-inferred-hits-store", storage_type=constants.STORAGE_TYPE, data={"max_hits": 7}),
            
            # Download modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Download Results")),
                    dbc.ModalBody([
                        dbc.Label("Filename (without extension):"),
                        dbc.Input(id="download-filename-input", type="text", 
                                 placeholder="e.g., my_analysis_results"),
                        html.Small("The .tsv extension will be added automatically.", 
                                  className="text-muted")
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancel", id="cancel-download-modal-button", 
                                  color="secondary", className="ms-auto", n_clicks=0),
                        dbc.Button("Download", id="confirm-download-modal-button", 
                                  color="primary", n_clicks=0),
                    ]),
                ],
                id="download-filename-modal",
                is_open=False,
            ),
            
            # Status modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Application Status")),
                    dbc.ModalBody(constants.STATUS),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close-modal", className="ml-auto", n_clicks=0)
                    ),
                ],
                id="modal",
                is_open=False,
            ),
            
            # Input and Controls Row
            dbc.Row([
                # Input Text Area
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Phosphosite Input", style={
                            'backgroundColor': constants.PRIMARY_COLOR,
                            'color': 'white',
                            'fontWeight': 'bold'
                        }),
                        dbc.CardBody([
                            dcc.Textarea(
                                id="text-input",
                                placeholder="Enter phosphosites in format:\nUNIPROT_GENENAME_SITE\n\nExample:\nP06732_CKM_T108\nO15273_TCAP_S161",
                                style={
                                    "width": "100%",
                                    "height": "30vh",
                                    "fontFamily": "monospace",
                                    "fontSize": "14px"
                                },
                                className="form-control",
                            )
                        ])
                    ])
                ], width=8),
                
                # Control Panel
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Analysis Parameters", style={
                            'backgroundColor': constants.PRIMARY_COLOR,
                            'color': 'white',
                            'fontWeight': 'bold'
                        }),
                        dbc.CardBody([
                            # Action Buttons
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("Start Analysis", id="button-start-analysis",
                                              color="primary", className="w-100 mb-2", n_clicks=0),
                                ], width=6),
                                dbc.Col([
                                    dbc.Button("Load Example", id="button-example",
                                              color="secondary", outline=True, className="w-100 mb-2", n_clicks=0),
                                ], width=6),
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Upload(
                                        id="upload-text-file",
                                        children=dbc.Button("Upload File", color="info", 
                                                          outline=True, className="w-100 mb-2"),
                                        multiple=False,
                                    ),
                                ], width=6),
                                dbc.Col([
                                    dbc.Button("Info", id="open-modal", color="secondary",
                                              outline=True, className="w-100 mb-2", n_clicks=0),
                                ], width=6),
                            ]),
                            
                            html.Hr(),
                            
                            # Fuzzy Matching Tolerance
                            html.Label("Position Tolerance:", className="fw-bold mt-2 mb-1",
                                      style={'color': constants.DARK_TEXT}),
                            html.Small("Maximum position difference for fuzzy matching", className="text-muted d-block mb-2"),
                            dcc.Slider(
                                id="floppy-slider",
                                min=0, max=10, step=1, value=5,
                                marks={i: str(i) for i in range(0, 11)},
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                            
                            # Max Inferred Hits
                            html.Label("Max Inferred Hits per Kinase:", className="fw-bold mt-3 mb-1",
                                      style={'color': constants.DARK_TEXT}),
                            html.Small("Limit imputed sites per kinase", className="text-muted d-block mb-2"),
                            dcc.Slider(
                                id="limit-inferred-hits-slider",
                                min=0, max=10, step=1, value=7,
                                marks={i: str(i) for i in range(0, 11)},
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                            
                            # Amino Acid Matching Mode
                            html.Label("Amino Acid Matching:", className="fw-bold mt-3 mb-1",
                                      style={'color': constants.DARK_TEXT}),
                            dcc.RadioItems(
                                id="matching-mode-radio",
                                options=[
                                    {"label": " Exact", "value": "exact"},
                                    {"label": " S/T Similar", "value": "st-similar"},
                                    {"label": " Ignore", "value": "ignore"},
                                ],
                                value="exact",
                                inline=True,
                                className="mb-2"
                            ),
                            
                            # Phosphorylatable Amino Acids
                            html.Label("Phosphorylatable Residues:", className="fw-bold mt-3 mb-1",
                                      style={'color': constants.DARK_TEXT}),
                            dcc.Checklist(
                                id="amino-acid-checklist",
                                options=amino_acid_options,
                                value=default_amino_acids,
                                inline=True,
                                className="mb-2"
                            ),
                            
                            # Statistical Test Method
                            html.Label("Statistical Test:", className="fw-bold mt-3 mb-1",
                                      style={'color': constants.DARK_TEXT}),
                            dcc.Dropdown(
                                id="statistical-test-dropdown",
                                options=constants.STATISTICAL_TEST_METHODS,
                                value="fisher",
                                clearable=False,
                                className="mb-2"
                            ),
                            
                            # Multiple Testing Correction
                            html.Label("Multiple Testing Correction:", className="fw-bold mt-3 mb-1",
                                      style={'color': constants.DARK_TEXT}),
                            dcc.Dropdown(
                                id="correction-method-dropdown",
                                options=constants.CORRECTION_METHODS,
                                value="fdr_bh",
                                clearable=False,
                            ),
                        ])
                    ])
                ], width=4),
            ], className="mb-4"),
            
            # Site-Level Results
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Span("Site-Level Enrichment Results", className="fw-bold"),
                            dbc.Button("Download", id="button-download", size="sm",
                                      color="light", className="float-end", n_clicks=0),
                        ], style={'backgroundColor': constants.PRIMARY_COLOR, 'color': 'white'}),
                        dcc.Download(id="download-tsv"),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="table-viewer",
                                columns=[],
                                data=[],
                                style_table={"overflowY": "auto", "maxHeight": "500px"},
                                style_header=constants.DEFAULT_HEADER_STYLE,
                                style_cell=constants.DEFAULT_CELL_STYLE,
                                style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                                sort_action="native",
                                filter_action="native",
                                page_size=15,
                            )
                        ])
                    ])
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Kinase Details", style={
                            'backgroundColor': constants.SECONDARY_COLOR,
                            'color': 'white',
                            'fontWeight': 'bold'
                        }),
                        dbc.CardBody([
                            html.Small("Click on a kinase to view details", className="text-muted d-block mb-2"),
                            dash_table.DataTable(
                                id="table-viewer-deep-hits",
                                page_size=10,
                                style_table={"overflowX": "auto"},
                                style_header=constants.DEFAULT_HEADER_STYLE,
                                style_cell=constants.DEFAULT_CELL_STYLE,
                                style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                            )
                        ])
                    ])
                ], width=4),
            ], className="mb-4"),
            
            # Substrate-Level Results
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Span("Substrate-Level Enrichment Results", className="fw-bold"),
                            dbc.Button("Download", id="button-download-high-level", size="sm",
                                      color="light", className="float-end", n_clicks=0),
                        ], style={'backgroundColor': constants.PRIMARY_COLOR, 'color': 'white'}),
                        dcc.Download(id="download-tsv-high-level"),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="table-viewer-high-level",
                                columns=[],
                                data=[],
                                style_table={"overflowY": "auto", "maxHeight": "500px"},
                                style_header=constants.DEFAULT_HEADER_STYLE,
                                style_cell=constants.DEFAULT_CELL_STYLE,
                                style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                                sort_action="native",
                                filter_action="native",
                                page_size=15,
                            )
                        ])
                    ])
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Substrate Details", style={
                            'backgroundColor': constants.SECONDARY_COLOR,
                            'color': 'white',
                            'fontWeight': 'bold'
                        }),
                        dbc.CardBody([
                            html.Small("Click on a kinase to view substrates", className="text-muted d-block mb-2"),
                            dash_table.DataTable(
                                id="table-viewer-high-hits",
                                page_size=10,
                                style_table={"overflowX": "auto"},
                                style_header=constants.DEFAULT_HEADER_STYLE,
                                style_cell=constants.DEFAULT_CELL_STYLE,
                                style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                            )
                        ])
                    ])
                ], width=4),
            ], className="mb-4"),
            
            # Visualization Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Site-Level Enrichment Visualization", style={
                            'backgroundColor': constants.SECONDARY_COLOR,
                            'color': 'white',
                            'fontWeight': 'bold'
                        }),
                        dbc.CardBody([
                            dcc.Graph(id="bar-plot-site-enrichment")
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Substrate-Level Enrichment Visualization", style={
                            'backgroundColor': constants.SECONDARY_COLOR,
                            'color': 'white',
                            'fontWeight': 'bold'
                        }),
                        dbc.CardBody([
                            dcc.Graph(id="bar-plot-sub-enrichment")
                        ])
                    ])
                ], width=6),
            ], className="mb-4"),
            
            # Footer
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P(constants.STATUS, className="text-center text-muted small")
                ])
            ])
        ],
        fluid=True,
        style={'maxWidth': '1800px', 'padding': '20px'}
    )
    return layout
