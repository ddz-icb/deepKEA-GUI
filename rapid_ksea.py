# TODO:
# - Fix disabled download button
#
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table
import plotly.graph_objects as go
import pandas as pd
import plotly.colors as colors
import util
import constants
import math
import base64
import io
import uuid

# Initialize the Dash app
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])


# site_level_results = pd.DataFrame()
# sub_level_results = pd.DataFrame()
# raw_data = pd.DataFrame()
# site_level_hits = pd.DataFrame()
# sub_level_hits = pd.DataFrame()
# current_title = "enrichment_results"

correction_methods = [
    {"label": "Benjamini-Hochberg (FDR-BH)", "value": "fdr_bh"},
    {"label": "Benjamini-Yekutieli (FDR-BY)", "value": "fdr_by"},
    {"label": "Bonferroni", "value": "bonferroni"},
]




app.layout = dbc.Container(
    [
        dcc.Store(id="session-id", storage_type=constants.STORAGE_TYPE),
        
        dcc.Store(id="site-level-results-store", storage_type=constants.STORAGE_TYPE),
        dcc.Store(id="sub-level-results-store", storage_type=constants.STORAGE_TYPE),
        dcc.Store(id="raw-data-store", data=util.load_psp_dataset(), storage_type=constants.STORAGE_TYPE),
        dcc.Store(id="site-hit-data-store", storage_type=constants.STORAGE_TYPE),
        dcc.Store(id="sub-hit-data-store", storage_type=constants.STORAGE_TYPE),
        dcc.Store(id="correction-method-store", data="fdr_bh", storage_type=constants.STORAGE_TYPE),  
        dcc.Store(id="current-title-store", data=constants.DEFAULT_DOWNLOAD_FILE_NAME, storage_type=constants.STORAGE_TYPE),
        dcc.Store(id="floppy-settings-store", storage_type=constants.STORAGE_TYPE),

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
                    is_open=False,  # Modal ist initial geschlossen
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
                                                # Button to upload a text file
                                                dcc.Upload(
                                                    id="upload-text-file",
                                                    children=dbc.Button(
                                                        "Upload File",
                                                        className="mb-3 btn-secondary btn-block me-2",
                                                    ),
                                                    multiple=False,
                                                    style={"width": "100%"},
                                                ),
                                                # Checkbox for custom dataset
                                                dcc.Checklist(
                                                    value=[],
                                                    id="checkbox_custom_dataset",
                                                    options=[
                                                        {
                                                            "label": "Harry Only Mode",
                                                            "value": "unchecked",
                                                        }
                                                    ],
                                                    className="mt-3",
                                                ),
                                                
                                                html.Label("Floppy Mode:", className="mt-3"),
                                                dcc.Slider(
                                                    id="floppy-slider",
                                                    min=0,
                                                    max=10,
                                                    step=1,
                                                    value=5,
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
                                                    value="exact",
                                                    labelStyle={"display": "inline-block", "margin-right": "15px"},
                                                ),
                                                
                                                # Dropdown für Korrektur Methode
                                                html.Label(
                                                    "Correction Method:",
                                                    className="mt-3",
                                                ),
                                                dcc.Dropdown(
                                                    id="correction-method-dropdown",
                                                    options=correction_methods,
                                                    value="fdr_bh",  # Standard auf FDR-BH
                                                    clearable=False,
                                                    style={"width": "100%"},
                                                ),
                                                # Debug: Zeigt aktuellen Wert
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
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Notes"),
                                        dbc.CardBody(
                                            [
                                                dcc.Textarea(
                                                    id="notes",
                                                    style={
                                                        "width": "100%",
                                                        "height": "7vh",
                                                        "box-sizing": "border-box",
                                                    },
                                                    placeholder="ENTER TITLE FOR DOWNLOAD FILE",
                                                    className="form-control rounded",
                                                )
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                            width=4,
                        ),
                    ],
                    className="mb-4",
                ),
                # Row for table viewer and buttons
                dbc.Row(
                    [
                        # Table Viewer
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
                                                                    "backgroundColor": "rgb(4, 60, 124)",
                                                                    "color": "white",
                                                                    "borderColor": "rgb(4, 60, 124)",  # Setzt die Umrandung auf dieselbe Farbe
                                                                    "float": "right",
                                                                    "padding": "0",
                                                                    "margin": "0",
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
                                                    id="table-viewer",
                                                    columns=[],
                                                    data=[],
                                                    style_table={
                                                        "overflowY": "auto",
                                                        "maxHeight": "500px",  # Setzt eine maximale Höhe
                                                        "overflowX": "auto",
                                                    },
                                                    sort_action="native",
                                                    filter_action="native",
                                                    style_header={
                                                        "backgroundColor": "rgb(4, 60, 124)",
                                                        "color": "white",
                                                        "fontWeight": "bold",
                                                    },
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
                                        dbc.CardHeader("Detail view"),
                                        dbc.CardBody(
                                            [
                                                # table viewer for deep hits
                                                dash_table.DataTable(
                                                    id="table-viewer-deep-hits",
                                                    # columns=[
                                                    #     {"name": i, "id": i}
                                                    #     for i in site_level_hits.columns
                                                    # ],
                                                    # data=site_level_hits.to_dict("records"),
                                                    page_size=10,
                                                    style_table={"overflowX": "auto"},
                                                    style_as_list_view=True,
                                                    style_header={
                                                        "backgroundColor": "rgb(4, 60, 124)",
                                                        "color": "white",
                                                        "fontWeight": "bold",
                                                    },
                                                    style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                                                )
                                            ]
                                        ),
                                    ]
                                )
                            ],
                            width=4,
                        ),
                        html.Div(style={"margin-bottom": "20px"}),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.CardHeader(
                                                        [
                                                            "Enriched kinases on substrate level Level",
                                                            dbc.Button(
                                                                "Download",
                                                                id="button-download-high-level",
                                                                n_clicks=0,
                                                                className="me-2",
                                                                style={
                                                                    "backgroundColor": "rgb(4, 60, 124)",
                                                                    "color": "white",
                                                                    "borderColor": "rgb(4, 60, 124)",
                                                                    # Setzt die Umrandung auf dieselbe Farbe
                                                                    "float": "right",
                                                                    "padding": "0",
                                                                    "margin": "0",
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
                                                    id="table-viewer-high-level",
                                                    columns=[],
                                                    data=[],
                                                    style_table={
                                                        "overflowY": "auto",
                                                        "maxHeight": "500px",  # Setzt eine maximale Höhe
                                                        "overflowX": "auto",
                                                    },
                                                    sort_action="native",
                                                    filter_action="native",
                                                    style_header={
                                                        "backgroundColor": "rgb(4, 60, 124)",
                                                        "color": "white",
                                                        "fontWeight": "bold",
                                                    },
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
                                        dbc.CardHeader("Detail view"),
                                        dbc.CardBody(
                                            [
                                                # table viewer for deep hits
                                                dash_table.DataTable(
                                                    id="table-viewer-high-hits",
                                                    # columns=[
                                                    #     {"name": i, "id": i}
                                                    #     for i in site_level_hits.columns
                                                    # ],
                                                    # data=site_level_hits.to_dict("records"),
                                                    page_size=10,
                                                    style_table={"overflowX": "auto"},
                                                    style_as_list_view=True,
                                                    style_header={
                                                        "backgroundColor": "rgb(4, 60, 124)",
                                                        "color": "white",
                                                        "fontWeight": "bold",
                                                    },
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
                # Platz zwischen den Rows durch zusätzlichen Container
                html.Div(style={"margin-bottom": "20px"}),
                # Row for bar plots
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "Enriched kinases on modification level by adj. p-value"
                                        ),
                                        dbc.CardBody(
                                            [
                                                dcc.Graph(
                                                    id="bar-plot-site-enrichment",
                                                    style={
                                                        "max-height": "20%",
                                                        "max-width": "100%",
                                                    },
                                                )
                                            ]
                                        ),
                                    ]
                                )
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "Enriched kinases on substrate level by adj. p-value"
                                        ),
                                        dbc.CardBody(
                                            [
                                                dcc.Graph(
                                                    id="bar-plot-sub-enrichment",
                                                    style={
                                                        "max-height": "20%",
                                                        "max-width": "100%",
                                                    },
                                                )
                                            ]
                                        ),
                                    ]
                                )
                            ],
                            width=6,
                        ),
                    ],
                    className="g-4",
                ),
                html.Div(style={"margin-bottom": "20px"}),
            ],
            style={
                "padding": "20px",
                "width": "95%",  # Stellt sicher, dass der Container die restliche Breite einnimmt
                "box-sizing": "border-box",
            },
            fluid=True,
        ),
    ],
    fluid=True,
)


# Callback function to update the table and bar plots when "Start Analysis" is clicked
@app.callback(
    [
        Output("site-level-results-store", "data"),
        Output("sub-level-results-store", "data"),
        Output("site-hit-data-store", "data"),
        Output("sub-hit-data-store", "data"),
        
        Output("table-viewer", "columns"),
        Output("table-viewer", "data"),
        Output("table-viewer-high-level", "columns"),
        Output("table-viewer-high-level", "data"),
        Output("bar-plot-site-enrichment", "figure"),
        Output("bar-plot-sub-enrichment", "figure")
    ],
    [
        Input("button-start-analysis", "n_clicks"),
    ],
    [
        State("text-input", "value"),
        State("correction-method-store", "data"),
        State("session-id", "data"),
        State("raw-data-store", "data"),
        State("current-title-store", "data"),
    ]
)
def update_output(n_clicks, text_value, correction_method, session_id, raw_data, current_title):
    if n_clicks > 0:
        
        raw_data = pd.DataFrame.from_dict(raw_data)
        print("Raw data loaded: ", str(len(raw_data)))
        
        site_level_results, sub_level_results, site_hits, sub_hits = util.start_eval(
            text_value, raw_data, correction_method, rounding=True
        )
        
        

        bar_plot_site_enrichment, bar_plot_sub_enrichment = create_barplots(site_level_results, sub_level_results)

        site_level_results = site_level_results.sort_values(
            by="P_VALUE", ascending=True
        )
        sub_level_results = sub_level_results.sort_values(
            by="ADJ_P_VALUE", ascending=True
        )
        # add uniprot-link column
        site_level_results = util.add_uniprot_link_col(site_level_results)
        sub_level_results = util.add_uniprot_link_col(sub_level_results)

        # Get display table columns via result_df
        table_columns = [{"name": i, "id": i} for i in site_level_results.columns]
        table_columns_high_level = [
            {"name": i, "id": i} for i in sub_level_results.columns
        ]

        # set upid columns to markdown mode to display links to uniprot
        table_columns_high_level = util.set_column_to_markdown(
            table_columns_high_level, "UPID"
        )
        table_columns = util.set_column_to_markdown(table_columns, "UPID")

        print("Success")

        return (
            site_level_results.to_dict("records"),
            sub_level_results.to_dict("records"),
            site_hits.to_dict("records"),
            sub_hits.to_dict("records"),
            table_columns,
            site_level_results.to_dict("records"),
            table_columns_high_level,
            sub_level_results.to_dict("records"),
            bar_plot_site_enrichment,
            bar_plot_sub_enrichment
        )
    else:
        empty_figure = {"data": [], "layout": go.Layout(title="Empty")}
        return [], [], empty_figure, empty_figure, [], [], [], []


def create_barplots(
    site_level_results, sub_level_results
):
    site_level_results = site_level_results.sort_values(
        by="ADJ_P_VALUE", ascending=False
    )
    sub_level_results = sub_level_results.sort_values(
        by="ADJ_P_VALUE", ascending=False
    )
    

    site_level_barplot = {
        "data": [
            go.Bar(
                y=site_level_results["KINASE"],
                x=site_level_results["ADJ_P_VALUE"].astype(float).apply(lambda x: -math.log10(x)),
                name="adj-p-value",
                orientation="h",
                marker=dict(
                    color=site_level_results["ADJ_P_VALUE"].astype(float).apply(lambda x: -math.log10(x)),  # Färbe die Balken nach den log_adj_p_values
                    colorscale=constants.BAR_COLORSCALE,
                ),
            ),
        ],
        "layout": go.Layout(
            title="Site-level enriched kinases",
            xaxis={"title": "adjusted p-value (-log10 scale)"},
            yaxis={
                "title": "Kinases",
                "tickangle": -45,
                "automargin": True,
            },
            margin=dict(l=50, r=10, t=30, b=50),
            height=500,
        ),
    }

    sub_level_barplot = {
        "data": [
            go.Bar(
                y=sub_level_results["KINASE"],
                x=sub_level_results["ADJ_P_VALUE"].astype(float).apply(lambda x: -math.log10(x)),
                name="adj-p-value",
                orientation="h",
                marker=dict(
                    color=sub_level_results["ADJ_P_VALUE"].astype(float).apply(lambda x: -math.log10(x)),
                    colorscale=constants.BAR_COLORSCALE,
                ),
            ),
        ],
        "layout": go.Layout(
            title="Substrate-level enriched kinases",
            xaxis={"title": "adjusted p-value (-log10 scale)"},
            yaxis={
                "title": "Kinases",
                "tickangle": -45,
                "automargin": True,
            },
            margin=dict(l=50, r=10, t=30, b=50),
            height=500,
        ),
    }
    return site_level_barplot, sub_level_barplot


@app.callback(
    Output("text-input", "value"),
    [Input("button-example", "n_clicks"), Input("upload-text-file", "contents")],
)
def load_example(n_clicks, file_contents):
    if n_clicks > 0:
        # Wenn der Button gedrückt wurde, füge den Beispieltext ein
        return constants.placeholder
    elif file_contents:
        # Wenn eine Datei hochgeladen wurde, dekodiere den Inhalt
        content_type, content_string = file_contents.split(",")
        decoded = base64.b64decode(content_string)

        try:
            # Versuche, den dekodierten Text zu extrahieren
            text = decoded.decode("utf-8")
        except UnicodeDecodeError:
            return "Error: The file is not a valid text file."

        return text
    else:
        # Wenn weder der Button gedrückt noch eine Datei hochgeladen wurde, gib einen leeren Wert zurück
        return ""


@app.callback(
    Output("download-tsv", "data"),
    Input("button-download", "n_clicks"),
    State("site-level-results-store", "data"),
    State("site-hit-data-store", "data"),
    State("current-title-store", "data"),
    prevent_initial_call=True,
)
def download_tsv(n_clicks, site_level_results, site_level_hits, current_title):
    
    site_level_results = pd.DataFrame.from_dict(site_level_results)
    site_level_hits = pd.DataFrame.from_dict(site_level_hits)
    
    if not site_level_results.empty:
        ######### Join hits on download file #############
        deep_hits_grouped = (
            site_level_hits.assign(
                GENE_SITE=lambda df: df["SUB_GENE"] + "-" + df["SUB_MOD_RSD"]
            )  # Kombiniere die zwei Spalten
            .groupby("KINASE")["GENE_SITE"]
            .apply(lambda x: ", ".join(x))  # Verbinde alle Hits mit Komma
            .reset_index()
        )
        downloadable_df_deep_level_with_hits = site_level_results.merge(
            deep_hits_grouped, on="KINASE", how="left"
        )
        ##################################################

        if current_title != "":
            filename = current_title + "_results_site_level.tsv"
            return dcc.send_data_frame(
                downloadable_df_deep_level_with_hits.to_csv, filename, sep="\t"
            )
        else:
            return dcc.send_data_frame(
                downloadable_df_deep_level_with_hits.to_csv,
                "results_site_level.tsv",
                sep="\t",
            )
    else:
        return None


@app.callback(
    Output("download-tsv-high-level", "data"),
    Input("button-download-high-level", "n_clicks"),
    State("sub-level-results-store", "data"),
    State("sub-hit-data-store", "data"),
    State("current-title-store", "data"),
    prevent_initial_call=True,
)
def download_tsv_high_level(n_clicks, sub_level_results, sub_level_hits, current_title):
    
    sub_level_results = pd.DataFrame.from_dict(sub_level_results)
    sub_level_hits = pd.DataFrame.from_dict(sub_level_hits)
    
    if not sub_level_results.empty:
        ######### Join hits on download file #############
        high_hits_grouped = (
            sub_level_hits.groupby("KINASE")["SUB_GENE"]
            .apply(lambda x: ", ".join(x))
            .reset_index()
        )
        downloadable_df_high_level_with_hits = sub_level_results.merge(
            high_hits_grouped, on="KINASE", how="left"
        )
        ##################################################

        if current_title != "":
            filename = current_title + "_results_sub_level.tsv"
            return dcc.send_data_frame(
                downloadable_df_high_level_with_hits.to_csv, filename, sep="\t"
            )
        else:
            return dcc.send_data_frame(
                downloadable_df_high_level_with_hits.to_csv,
                "results_sub_level.tsv",
                sep="\t",
            )
    else:
        return None


@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open  # Umschalten zwischen offen und geschlossen
    return is_open


# when input in notes are changes, update the title
@app.callback(Output("notes", "value"), Input("notes", "value"))
def update_title(value):
    global current_title
    current_title = value
    return value


@app.callback(
    Output("table-viewer-deep-hits", "columns"),
    Output("table-viewer-deep-hits", "data"),
    Input("table-viewer", "active_cell"),
    State("table-viewer", "data"),
    State("site-hit-data-store", "data"),
)
def display_row_details(active_cell, table_data, site_level_hits):
    site_level_hits = pd.DataFrame.from_dict(site_level_hits)
    
    if active_cell is not None:
        row_index = active_cell["row"]  # Holen der Zeilenindex der aktiven Zelle
        # get value of column KINASE from selected row
        kinase = table_data[row_index]["KINASE"]

        # display data from deep_hits for selected kinase
        deep_hits = site_level_hits[site_level_hits["KINASE"] == kinase]
        columns = [{"name": i, "id": i} for i in deep_hits.columns]
        data = deep_hits.to_dict("records")
        return columns, data

    return "Keine Zelle ausgewählt"


# table-viewer-high-level
@app.callback(
    Output("table-viewer-high-hits", "columns"),
    Output("table-viewer-high-hits", "data"),
    Input("table-viewer-high-level", "active_cell"),
    State("table-viewer-high-level", "data"),
    State("sub-hit-data-store", "data"),
)
def display_row_details_high(active_cell, table_data, sub_level_hits):
    sub_level_hits = pd.DataFrame.from_dict(sub_level_hits)
    if active_cell is not None:
        row_index = active_cell["row"]  # Holen der Zeilenindex der aktiven Zelle
        # get value of column KINASE from selected row
        kinase = table_data[row_index]["KINASE"]

        # display data from deep_hits for selected kinase
        high_hits = sub_level_hits[sub_level_hits["KINASE"] == kinase]
        columns = [{"name": i, "id": i} for i in high_hits.columns]
        data = high_hits.to_dict("records")
        return columns, data

    return "Keine Zelle ausgewählt"

@app.callback(
    Output("checkbox_custom_dataset", "className"),  # Dummy-Ausgabe, nur zur Ausführung
    Input("checkbox_custom_dataset", "value"),
)
def handle_checkbox(checked):
    global raw_data
    raw_data = pd.DataFrame()
    if "checked" in checked:
        print("Before overide: ", len(raw_data))
        raw_data = pd.read_csv(constants.CUSTOM_DATASET_PATH, sep="\t")
        raw_data = raw_data.drop_duplicates()
        print("After overide: ", len(raw_data))
        raw_data = raw_data[raw_data["SUB_ORGANISM"] == constants.SUB_ORGANISM]
        raw_data = raw_data[raw_data["KIN_ORGANISM"] == constants.KIN_ORGANISM]
        print("After overide (2): ", len(raw_data))
        print("Custom dataset loaded")
    else:
        raw_data = pd.read_csv(constants.KIN_SUB_DATASET_PATH, sep="\t")
        raw_data = raw_data[raw_data["SUB_ORGANISM"] == constants.SUB_ORGANISM]
        raw_data = raw_data[raw_data["KIN_ORGANISM"] == constants.KIN_ORGANISM]
        print("Default dataset loaded")

    return "mt-3"  # Unverändert, dient nur als Dummy


# Callback, um die Korrekturmethode in `dcc.Store` zu speichern und anzuzeigen
@app.callback(
    Output("correction-method-store", "data"),
    Output("correction-method-display", "children"),  # Debug-Anzeige
    Input("correction-method-dropdown", "value"),
)
def update_correction_method(selected_method):
    # simulate click on start analysis
    update_output(1, constants.placeholder, selected_method)

    return selected_method, f"Selected correction method: {selected_method}"


@app.callback(
    Output('session-id', 'data'),
    Input('url', 'pathname'),
    State('session-id', 'data')
)
def initialize_session(pathname, existing_id):
    return existing_id if existing_id else str(uuid.uuid4())

@app.callback(
    Output("floppy-settings-store", "data"),
    Input("floppy-slider", "value"),
    Input("matching-mode-radio", "value"),
    State("floppy-settings-store", "data"),
)
def update_floppy_settings(slider_value, radio_value, current_data):
    if current_data is None:
        current_data = {}

    current_data["floppy_value"] = int(slider_value)
    current_data["matching_mode"] = radio_value
    return current_data



if __name__ == "__main__":
    

    app.run_server(debug=True)
    # app.run_server(host="192.168.2.47", port = 8080, debug=True)
