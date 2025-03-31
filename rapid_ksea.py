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

# Initialize the Dash app
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])
downloadable_df_deep_level = pd.DataFrame()
downloadable_df_high_level = pd.DataFrame()

raw_data = pd.DataFrame()
deep_hit_df = pd.DataFrame()
high_hit_df = pd.DataFrame()
current_title = ""

correction_methods = [
    {"label": "Benjamini-Hochberg (FDR-BH)", "value": "fdr_bh"},
    {"label": "Benjamini-Yekutieli (FDR-BY)", "value": "fdr_by"},
    {"label": "Bonferroni", "value": "bonferroni"}
]

app.layout = dbc.Container([

    dcc.Store(id="correction-method-store", data="fdr_bh"),  # Standard auf 'fdr_bh'

    # Main content
    dbc.Container([
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Status")),
                dbc.ModalBody(constants.STATUS),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal", className="ml-auto", n_clicks=0)
                ),
            ],
            id="modal",
            is_open=False,  # Modal ist initial geschlossen
        ),

        # Row for table viewer and buttons
        dbc.Row([
            # Table Viewer
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Input substrates (ProForma)"),
                    dbc.CardBody([
                        dcc.Textarea(
                            id='text-input',
                            style={'width': '100%', 'height': '27vh', 'box-sizing': 'border-box'},
                            placeholder='UNIPROT_GENNAME_SITE\nUNIPROT_GENNAME_SITE\nUNIPROT_GENNAME_SITE',
                            className='form-control rounded'
                        )
                    ])
                ])
            ], width=8),

            # Button Widget
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Button('Start Analysis', id='button-start-analysis', n_clicks=0,
                                   className='mb-3 btn-primary btn-block me-2'),
                        dbc.Button('Example', id='button-example', n_clicks=0,
                                   className='mb-3 btn-secondary btn-block me-2', outline=False, color='secondary'),
                        dbc.Button("Status", id="open-modal", className='mb-3 btn-secondary btn-block me-2', n_clicks=0,
                                   outline=True),

                        # Button to upload a text file
                        dcc.Upload(
                            id='upload-text-file',
                            children=dbc.Button('Upload File', className='mb-3 btn-secondary btn-block me-2'),
                            multiple=False,
                            style={'width': '100%'}
                        ),

                        # Checkbox for custom dataset
                        dcc.Checklist(
                            value=[],
                            id='checkbox_custom_dataset',
                            options=[{'label': 'Harry Only Mode', 'value': 'unchecked'}],
                            className='mt-3'
                        ),

                        # Dropdown für Korrektur Methode
                        html.Label("Correction Method:", className="mt-3"),
                        dcc.Dropdown(
                            id="correction-method-dropdown",
                            options=correction_methods,
                            value="fdr_bh",  # Standard auf FDR-BH
                            clearable=False,
                            style={"width": "100%"}
                        ),

                        # Debug: Zeigt aktuellen Wert
                        html.Br(),
                        html.Div(id="correction-method-display", style={"fontWeight": "bold", "color": "blue"}),

                    ])
                ], style={"padding": "10px"}),

                html.Div(style={'margin-bottom': '20px'}),

                dbc.Card([
                    dbc.CardHeader("Notes"),
                    dbc.CardBody([
                        dcc.Textarea(
                            id='notes',
                            style={'width': '100%', 'height': '7vh', 'box-sizing': 'border-box'},
                            placeholder='ENTER TITLE FOR DOWNLOAD FILE',
                            className='form-control rounded'
                        )
                    ])
                ])

            ], width=4),

        ], className='mb-4'),

        # Row for table viewer and buttons
        dbc.Row([
            # Table Viewer
            dbc.Col([
                dbc.Card([
                    dbc.Row([
                        dbc.Col(
                            dbc.CardHeader([
                                "Enriched kinases on modification Level",
                                dbc.Button("Download", id="button-download", n_clicks=0, className="me-2", style={
                                    "backgroundColor": "rgb(4, 60, 124)",
                                    "color": "white",
                                    "borderColor": "rgb(4, 60, 124)",  # Setzt die Umrandung auf dieselbe Farbe
                                    "float": "right",
                                    "padding": "0",
                                    "margin": "0"
                                })
                            ]),
                            width=12)
                    ]),

                    dcc.Download(id="download-tsv"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='table-viewer',
                            columns=[],
                            data=[],
                            style_table={
                                'overflowY': 'auto',
                                'maxHeight': '500px',  # Setzt eine maximale Höhe
                                'overflowX': 'auto'
                            },
                            sort_action='native',
                            filter_action='native',
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold'},
                            style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                            style_cell=constants.DEFAULT_CELL_STYLE
                        )
                    ])
                ])
            ], width=8),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Detail view"),
                    dbc.CardBody([
                        # table viewer for deep hits
                        dash_table.DataTable(
                            id='table-viewer-deep-hits',
                            columns=[{'name': i, 'id': i} for i in deep_hit_df.columns],
                            data=deep_hit_df.to_dict('records'),
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_as_list_view=True,
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold'},
                            style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL
                        )
                    ])
                ])
            ], width=4),

            html.Div(style={'margin-bottom': '20px'}),

            dbc.Col([
                dbc.Card([
                    dbc.Row([
                        dbc.Col(
                            dbc.CardHeader([
                                "Enriched kinases on substrate level Level",
                                dbc.Button("Download", id="button-download-high-level", n_clicks=0, className="me-2",
                                           style={
                                               "backgroundColor": "rgb(4, 60, 124)",
                                               "color": "white",
                                               "borderColor": "rgb(4, 60, 124)",
                                               # Setzt die Umrandung auf dieselbe Farbe
                                               "float": "right",
                                               "padding": "0",
                                               "margin": "0"
                                           })
                            ]),
                            width=12)
                    ]),
                    dcc.Download(id="download-tsv-high-level"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='table-viewer-high-level',
                            columns=[],
                            data=[],
                            style_table={
                                'overflowY': 'auto',
                                'maxHeight': '500px',  # Setzt eine maximale Höhe
                                'overflowX': 'auto'
                            },
                            sort_action='native',
                            filter_action='native',
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold'},
                            style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL,
                            style_cell=constants.DEFAULT_CELL_STYLE
                        )
                    ])
                ])
            ], width=8),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Detail view"),
                    dbc.CardBody([
                        # table viewer for deep hits
                        dash_table.DataTable(
                            id='table-viewer-high-hits',
                            columns=[{'name': i, 'id': i} for i in deep_hit_df.columns],
                            data=deep_hit_df.to_dict('records'),
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_as_list_view=True,
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold'},
                            style_data_conditional=constants.DEFAULT_STYLE_DATA_CONDITIONAL
                        )
                    ])
                ])
            ], width=4),

        ], className='mb-4'),

        # Platz zwischen den Rows durch zusätzlichen Container
        html.Div(style={'margin-bottom': '20px'}),

        # Row for bar plots
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Enriched kinases on substrate level by adj. p-value"),
                    dbc.CardBody([
                        dcc.Graph(id='bar-plot-site-enrichment', style={'max-height': '20%', 'max-width': '100%'})
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Enriched kinases on modification level by adj. p-value"),
                    dbc.CardBody([
                        dcc.Graph(id='bar-plot-sub-enrichment', style={'max-height': '20%', 'max-width': '100%'})
                    ])
                ])
            ], width=6)
        ], className='g-4'),

        html.Div(style={'margin-bottom': '20px'}),

        # Row for tables
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Kinase pathway enrichment"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='table-viewer-pathway',
                            columns=[],
                            data=[],
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_as_list_view=True,
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold',
                                          "align": 'left'},
                        )
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Input data pathway enrichment"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='table-viewer-pathway-input',
                            columns=[],
                            data=[],
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_as_list_view=True,
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold',
                                          "align": 'left'},
                        )
                    ])
                ])
            ], width=6)
        ], className='g-4')

    ], style={
        'padding': '20px',
        'width': '95%',  # Stellt sicher, dass der Container die restliche Breite einnimmt
        'box-sizing': 'border-box'}, fluid=True),
], fluid=True)


# Callback function to update the table and bar plots when "Start Analysis" is clicked
@app.callback(
    [Output('table-viewer', 'columns'),
     Output('table-viewer', 'data'),
     Output('table-viewer-high-level', 'columns'),
     Output('table-viewer-high-level', 'data'),
     Output('bar-plot-site-enrichment', 'figure'),
     Output('bar-plot-sub-enrichment', 'figure'),
     Output('table-viewer-pathway', 'columns'),
     Output('table-viewer-pathway', 'data'),
     Output('table-viewer-pathway-input', 'columns'),
     Output('table-viewer-pathway-input', 'data')
     ],
    [Input('button-start-analysis', 'n_clicks')],
    [State('text-input', 'value')],
    State('correction-method-store', 'data')
)
def update_output(n_clicks, text_value, correction_method):
    if n_clicks > 0:
        site_level_results, sub_level_results, site_hits, sub_hits = util.start_eval(text_value, raw_data, correction_method)
        df_a = site_level_results.copy()

        global downloadable_df_deep_level, deep_hit_df
        downloadable_df_deep_level = site_level_results.copy()
        downloadable_df_high_level = sub_level_results.copy()

        global downloadable_df_high_level, high_hit_df
        deep_hit_df = site_hits.copy()
        high_hit_df = sub_hits.copy()

        site_level_results = site_level_results.sort_values(by='P_VALUE', ascending=False)
        df_a = df_a.sort_values(by='ADJ_P_VALUE', ascending=False)
        sub_level_results = sub_level_results.sort_values(by='ADJ_P_VALUE', ascending=False)

        log_adj_p_values = df_a['ADJ_P_VALUE'].apply(lambda x: -math.log10(x))
        log_adj_p_values_high_level = sub_level_results['ADJ_P_VALUE'].apply(lambda x: -math.log10(x))

        bar_plot_site_enrichment, bar_plot_sub_enrichment = create_barplots(df_a, log_adj_p_values,
                                                                            log_adj_p_values_high_level,sub_level_results)

        site_level_results = site_level_results.sort_values(by='P_VALUE', ascending=True)
        df_a = df_a.sort_values(by='ADJ_P_VALUE', ascending=True)
        sub_level_results = sub_level_results.sort_values(by='ADJ_P_VALUE', ascending=True)


        site_level_results['P_VALUE'] = site_level_results['P_VALUE'].astype(float).apply(util.format_p_value)
        site_level_results['ADJ_P_VALUE'] = site_level_results['ADJ_P_VALUE'].astype(float).apply(util.format_p_value)
        site_level_results['CHI2_P_VALUE'] = site_level_results['CHI2_P_VALUE'].astype(float).apply(util.format_p_value)
        table_data = site_level_results.to_dict('records')

        # add uniprot-link column
        site_level_results = util.add_uniprot_link_col(site_level_results)
        sub_level_results = util.add_uniprot_link_col(sub_level_results)

        # Get display table columns via result_df
        table_columns = [{'name': i, 'id': i} for i in site_level_results.columns]
        table_columns_high_level = [{'name': i, 'id': i} for i in sub_level_results.columns]

        # set upid columns to markdown mode to display links to uniprot
        table_columns_high_level = util.set_column_to_markdown(table_columns_high_level, "UPID")
        table_columns = util.set_column_to_markdown(table_columns, "UPID")

        sub_level_results = sub_level_results.sort_values(by='ADJ_P_VALUE', ascending=True)
        sub_level_results["P_VALUE"] = sub_level_results["P_VALUE"].astype(float).apply(util.format_p_value)
        sub_level_results["ADJ_P_VALUE"] = sub_level_results["ADJ_P_VALUE"].astype(float).apply(util.format_p_value)
        sub_level_results["CHI2_P_VALUE"] = sub_level_results["CHI2_P_VALUE"].astype(float).apply(util.format_p_value)
        table_data_high_level = sub_level_results.to_dict('records')

        #update_download_button(0)

        pathways = []
        df_p = downloadable_df_deep_level.drop(columns=["P_VALUE", "FOUND", "SUB#", "ADJ_P_VALUE"])

        pathways = util.get_pathways_by_upid(reactome, df_p)

        # count occurences of pathways
        pathway_counts = {}
        for pathway in pathways:
            if pathway in pathway_counts:
                pathway_counts[pathway] += 1
            else:
                pathway_counts[pathway] = 1

        pathway_counts = pd.DataFrame(list(pathway_counts.items()), columns=['Pathway', 'Count'])
        pathway_counts = pathway_counts.sort_values(by='Count', ascending=False)

        # create table data for pathway
        table_columns_pathway = [{'name': i, 'id': i} for i in pathway_counts.columns]
        table_data_pathway = pathway_counts.to_dict('records')

        df_p_input = util.read_sites(text_value)

        df_p_input = df_p_input.drop(columns=["UPID", "SUB_MOD_RSD"])
        # rename SUB_ACC_ID column to UPID
        df_p_input = df_p_input.rename(columns={"SUB_ACC_ID": "UPID"})
        df_p_input = df_p_input.drop_duplicates()

        input_pathways = util.get_pathways_by_upid(reactome, df_p_input)

        # count occurences of pathways
        pathway_counts_input = {}
        for pathway in input_pathways:
            if pathway in pathway_counts_input:
                pathway_counts_input[pathway] += 1
            else:
                pathway_counts_input[pathway] = 1

        pathway_counts_input = pd.DataFrame(list(pathway_counts_input.items()), columns=['Pathway', 'Count'])
        pathway_counts_input = pathway_counts_input.sort_values(by='Count', ascending=False)




        # create table data for pathway
        table_columns_pathway_input = [{'name': i, 'id': i} for i in pathway_counts_input.columns]
        table_data_pathway_input = pathway_counts_input.to_dict('records')

        return table_columns, table_data, table_columns_high_level, table_data_high_level, bar_plot_site_enrichment, bar_plot_sub_enrichment, table_columns_pathway, table_data_pathway, table_columns_pathway_input, table_data_pathway_input
    else:
        empty_figure = {'data': [], 'layout': go.Layout(title='Empty')}
        return [], [], empty_figure, empty_figure, [], [], [], []


def create_barplots(df_a, log_adj_p_values, log_adj_p_values_high_level, sub_level_results):


    bar_plot1_figure = {
        'data': [
            go.Bar(
                y=sub_level_results['KINASE'],
                x=log_adj_p_values_high_level,
                name='adj-p-value',
                orientation='h',
                marker=dict(
                    color=log_adj_p_values_high_level,  # Färbe die Balken nach den log_adj_p_values
                    colorscale=constants.BAR_COLORSCALE,  # Wähle eine Farbskala
                    colorbar=dict(title='Log Adj. P-Value')  # Füge eine Farbskala hinzu
                )
            ),
        ],
        'layout': go.Layout(
            title='Kinases by adjusted p-value high level',
            xaxis={'title': 'p-value (-log10 scale)'},
            yaxis={
                'title': 'Kinases',
                'tickangle': -45,  # Rotiert die Tick-Beschriftungen
                'automargin': True  # Passt die Ränder automatisch an
            },
            margin=dict(l=50, r=10, t=30, b=50),
            height=500
        )
    }
    bar_plot2_figure = {
        'data': [
            go.Bar(
                y=df_a['KINASE'],
                x=log_adj_p_values,
                name='adj-p-value',
                orientation='h',
                marker=dict(
                    color=log_adj_p_values,  # Färbe die Balken nach den log_adj_p_values
                    colorscale=constants.BAR_COLORSCALE,  # Wähle eine Farbskala
                    colorbar=dict(title='Log Adj. P-Value')  # Füge eine Farbskala hinzu
                )
            ),
        ],
        'layout': go.Layout(
            title='Kinases by adjusted p-value (deep)',
            xaxis={'title': 'Benjamini Hochberg adjusted p-value (-log10 scale)'},
            yaxis={
                'title': 'Kinases',
                'tickangle': -45,  # Rotiert die Tick-Beschriftungen
                'automargin': True  # Passt die Ränder automatisch an
            },
            margin=dict(l=50, r=10, t=30, b=50),
            height=500
        )
    }
    return bar_plot1_figure, bar_plot2_figure


@app.callback(
    Output('text-input', 'value'),
    [Input('button-example', 'n_clicks'),
     Input('upload-text-file', 'contents')]
)
def load_example(n_clicks, file_contents):
    if n_clicks > 0:
        # Wenn der Button gedrückt wurde, füge den Beispieltext ein
        return constants.placeholder
    elif file_contents:
        # Wenn eine Datei hochgeladen wurde, dekodiere den Inhalt
        content_type, content_string = file_contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            # Versuche, den dekodierten Text zu extrahieren
            text = decoded.decode('utf-8')
        except UnicodeDecodeError:
            return "Error: The file is not a valid text file."

        return text
    else:
        # Wenn weder der Button gedrückt noch eine Datei hochgeladen wurde, gib einen leeren Wert zurück
        return ''


@app.callback(
    Output("download-tsv", "data"),
    Input("button-download", "n_clicks"),
    prevent_initial_call=True
)
def download_tsv(n_clicks):
    if not downloadable_df_deep_level.empty:

        ######### Join hits on download file #############
        deep_hits_grouped = (
            deep_hit_df
            .assign(GENE_SITE=lambda df: df["SUB_GENE"] + "-" + df["SUB_MOD_RSD"])  # Kombiniere die zwei Spalten
            .groupby("KINASE")["GENE_SITE"]
            .apply(lambda x: ', '.join(x))  # Verbinde alle Hits mit Komma
            .reset_index()
        )
        downloadable_df_deep_level_with_hits = downloadable_df_deep_level.merge(deep_hits_grouped, on="KINASE",
                                                                                how="left")
        ##################################################

        if current_title != "":
            filename = current_title + "_results_site_level.tsv"
            return dcc.send_data_frame(downloadable_df_deep_level_with_hits.to_csv, filename, sep='\t')
        else:
            return dcc.send_data_frame(downloadable_df_deep_level_with_hits.to_csv, "results_site_level.tsv", sep='\t')
    else:
        return None


@app.callback(
    Output("download-tsv-high-level", "data"),
    Input("button-download-high-level", "n_clicks"),
    prevent_initial_call=True
)
def download_tsv_high_level(n_clicks):
    if not downloadable_df_high_level.empty:

        ######### Join hits on download file #############
        high_hits_grouped = high_hit_df.groupby("KINASE")["SUB_GENE"].apply(lambda x: ', '.join(x)).reset_index()
        downloadable_df_high_level_with_hits = downloadable_df_high_level.merge(high_hits_grouped, on="KINASE",
                                                                                how="left")
        ##################################################

        if current_title != "":
            filename = current_title + "_results_sub_level.tsv"
            return dcc.send_data_frame(downloadable_df_high_level_with_hits.to_csv, filename, sep='\t')
        else:
            return dcc.send_data_frame(downloadable_df_high_level_with_hits.to_csv, "results_sub_level.tsv", sep='\t')
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
@app.callback(
    Output('notes', 'value'),
    Input('notes', 'value')
)
def update_title(value):
    global current_title
    current_title = value
    return value


@app.callback(
    Output('table-viewer-deep-hits', 'columns'),
    Output('table-viewer-deep-hits', 'data'),
    Input('table-viewer', 'active_cell'),
    State('table-viewer', 'data'),
)
def display_row_details(active_cell, table_data):
    if active_cell is not None:
        row_index = active_cell['row']  # Holen der Zeilenindex der aktiven Zelle
        # get value of column KINASE from selected row
        kinase = table_data[row_index]['KINASE']

        # display data from deep_hits for selected kinase
        deep_hits = deep_hit_df[deep_hit_df['KINASE'] == kinase]
        columns = [{'name': i, 'id': i} for i in deep_hits.columns]
        data = deep_hits.to_dict('records')
        return columns, data

    return "Keine Zelle ausgewählt"


#table-viewer-high-level
@app.callback(
    Output('table-viewer-high-hits', 'columns'),
    Output('table-viewer-high-hits', 'data'),
    Input('table-viewer-high-level', 'active_cell'),
    State('table-viewer-high-level', 'data'),
)
def display_row_details_high(active_cell, table_data):
    if active_cell is not None:
        row_index = active_cell['row']  # Holen der Zeilenindex der aktiven Zelle
        # get value of column KINASE from selected row
        kinase = table_data[row_index]['KINASE']

        # display data from deep_hits for selected kinase
        high_hits = high_hit_df[high_hit_df['KINASE'] == kinase]
        columns = [{'name': i, 'id': i} for i in high_hits.columns]
        data = high_hits.to_dict('records')
        return columns, data

    return "Keine Zelle ausgewählt"


@app.callback(
    Output('checkbox_custom_dataset', 'className'),  # Dummy-Ausgabe, nur zur Ausführung
    Input('checkbox_custom_dataset', 'value')
)
def handle_checkbox(checked):
    global raw_data
    raw_data = pd.DataFrame()
    if 'checked' in checked:
        print("Before ovveride: ", len(raw_data))
        raw_data = pd.read_csv(constants.CUSTOM_DATASET_PATH, sep='\t')
        raw_data = raw_data.drop_duplicates()
        print("After overide: ", len(raw_data))
        raw_data = raw_data[raw_data['SUB_ORGANISM'] == constants.SUB_ORGANISM]
        raw_data = raw_data[raw_data['KIN_ORGANISM'] == constants.KIN_ORGANISM]
        print("After overide (2): ", len(raw_data))

        print("Custom dataset loaded")
    else:
        raw_data = pd.read_csv(constants.KIN_SUB_DATASET_PATH, sep='\t')
        raw_data = raw_data[raw_data['SUB_ORGANISM'] == constants.SUB_ORGANISM]
        raw_data = raw_data[raw_data['KIN_ORGANISM'] == constants.KIN_ORGANISM]
        print("Default dataset loaded")

    return 'mt-3'  # Unverändert, dient nur als Dummy


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


if __name__ == '__main__':
    raw_data = pd.read_csv(constants.KIN_SUB_DATASET_PATH, sep='\t')
    raw_data = raw_data[raw_data['SUB_ORGANISM'] == constants.SUB_ORGANISM]
    raw_data = raw_data[raw_data['KIN_ORGANISM'] == constants.KIN_ORGANISM]
    raw_data = raw_data[
        ["GENE", "KINASE", "KIN_ACC_ID", "KIN_ORGANISM", "SUBSTRATE", "SUB_ACC_ID", "SUB_GENE", "SUB_ORGANISM",
         "SUB_MOD_RSD"]]

    reactome = pd.read_csv(constants.REACTOME_PATH, sep='\t', header=None,
                           names=['UPID', 'REACTOME_ID', 'LINK', 'REACTOME_NAME', '0', 'SPECIES'])
    reactome = reactome[reactome['SPECIES'] == constants.ORGANISM_REACTOME]

    app.run_server(debug=True)
    #app.run_server(host="192.168.2.47", port = 8080, debug=True)
