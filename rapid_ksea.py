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
import io

# Initialize the Dash app
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])
downloadable_df = pd.DataFrame()
downloadable_df_high_level = pd.DataFrame()


app.layout = dbc.Container([
    # Sidebar
    dbc.Card([
        dbc.CardBody([
            html.Img(src='/assets/ddz_logo_de.png', id='logo', className='img-fluid rounded', style={'padding': '10px'}),
            html.Hr(),
            html.Ul([
                html.Li(dbc.NavLink('Dashboard 1', href='/', className='nav-link'))
            ], style={'list-style-type': 'none', 'padding': '0', 'margin': '0'})
        ])
    ], className='bg-light', style={
        'width': '250px',
        'height': '100vh',
        'position': 'fixed',
        'left': '0',
        'top': '0'
    }),

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
                    style={'width': '100%', 'height': '15vh', 'box-sizing': 'border-box'},
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
                        dbc.Button('Start Analysis', id='button-start-analysis', n_clicks=0, className='mb-3 btn-primary btn-block me-2'),
                        dbc.Button('Example', id='button-example', n_clicks=0, className='mb-3 btn-secondary btn-block me-2' ,outline=False, color='secondary'),
                        dbc.Button('Download', id='button-download', n_clicks=0, className='mb-3 btn-secondary btn-block me-2', disabled=True, outline=True),
                        dbc.Button("Status", id="open-modal",className='mb-3 btn-secondary btn-block me-2' ,n_clicks=0, outline=True),
    
                    ])
                ], style={"padding": "10px"})
            ], width=4),

            dcc.Download(id="download-tsv")
        ], className='mb-4'),
        

        # Row for table viewer and buttons
        dbc.Row([
            # Table Viewer
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Enriched kinases on modification Level"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='table-viewer',
                            columns=[],
                            data=[],
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_as_list_view=True,
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold' },
                        )
                    ])
                ])
            ], width=12),
            
            html.Div(style={'margin-bottom': '20px'}),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Enriched kinases on substrate level"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='table-viewer-high-level',
                            columns=[],
                            data=[],
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_as_list_view=True,
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold' },
                        )
                    ])
                ])
            ], width=12),
            
        ], className='mb-4'),

        # Platz zwischen den Rows durch zusätzlichen Container
        html.Div(style={'margin-bottom': '20px'}),

        # Row for bar plots
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Enriched kinases on substrate level by adj. p-value"),
                    dbc.CardBody([
                        dcc.Graph(id='bar-plot1', style={'max-height': '20%', 'max-width': '100%'})
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Enriched kinases on modification level by adj. p-value"),
                    dbc.CardBody([
                        dcc.Graph(id='bar-plot2', style={'max-height': '20%', 'max-width': '100%'})
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
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold', "align": 'left' },
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
                            style_header={'backgroundColor': 'rgb(4, 60, 124)', 'color': 'white', 'fontWeight': 'bold', "align": 'left' },
                        )
                    ])
                ])
            ], width=6)
        ], className='g-4')
        
        
        
    ], style={
    'margin-left': '250px',   # Für die Sidebar
    'padding': '20px',
    'width': 'calc(100% - 250px)',  # Stellt sicher, dass der Container die restliche Breite einnimmt
    'box-sizing': 'border-box'}),
], fluid=True )

# Callback function to update the table and bar plots when "Start Analysis" is clicked
@app.callback(
    [Output('table-viewer', 'columns'),
     Output('table-viewer', 'data'),
     Output('table-viewer-high-level', 'columns'),
     Output('table-viewer-high-level', 'data'),
     Output('bar-plot1', 'figure'),
     Output('bar-plot2', 'figure'),
     Output('table-viewer-pathway', 'columns'),
     Output('table-viewer-pathway', 'data'),
     Output('table-viewer-pathway-input', 'columns'),
     Output('table-viewer-pathway-input', 'data')
     ],
    [Input('button-start-analysis', 'n_clicks')],
    [State('text-input', 'value')]
)
def update_output(n_clicks, text_value):
    if n_clicks > 0:
        df,df_high_level = util.start_eval(text_value, raw_data)
        df_a = df.copy()
        
        #####
        global downloadable_df
        downloadable_df = df.copy()
        
        global downloadable_df_high_level
        downloadable_df_high_level = df_high_level.copy()
        #####
        
        df = df.drop(columns=["UPID"])
        df_a = df_a.drop(columns=["UPID"])
        
        df = df.sort_values(by='P_VALUE', ascending=False)
        df_a = df_a.sort_values(by='ADJ_P_VALUE', ascending=False)
        df_high_level = df_high_level.sort_values(by='ADJ_P_VALUE', ascending=False)
        
        
        log_adj_p_values = df_a['ADJ_P_VALUE'].apply(lambda x: -math.log10(x))
        log_adj_p_values_high_level = df_high_level['ADJ_P_VALUE'].apply(lambda x: -math.log10(x))
        
        
        bar_plot1_figure = {
            'data': [
                go.Bar(y=df_high_level['KINASE'], x=log_adj_p_values_high_level, name='adj-p-value', orientation='h',
                    marker=dict(color="#043c7c")),
            ],
            'layout': go.Layout(
                title='Kinases by adjusted p-value high level',
                xaxis={'title': 'p-value (-log10 scale)'},
                yaxis={
                    'title': 'Kinases',
                    'tickangle': -45,  # Rotate tick labels if necessary
                    'automargin': True  # Automatically adjust margins
                },
                margin=dict(l=50, r=10, t=30, b=50),
                height=500
            )
        }

        bar_plot2_figure = {
            'data': [
                go.Bar(y=df_a['KINASE'], x=log_adj_p_values, name='adj-p-value', orientation='h',
                    marker=dict(color="#043c7c")),
            ],
            'layout': go.Layout(
                title='Kinases by adjusted p-value (deep)',
                xaxis={'title': 'benjamini hochberg adjusted p-value (-log10 scale)'},
                yaxis={
                    'title': 'Kinases',
                    'tickangle': -45,  # Rotate tick labels if necessary
                    'automargin': True  # Automatically adjust margins
                },
                margin=dict(l=50, r=10, t=30, b=50),
                height=500
            )
        }

        
        # apply format_p_value to adj p and normal  from util to format p-values in table_data
        table_columns = [{'name': i, 'id': i} for i in df.columns]
        df = df.sort_values(by='ADJ_P_VALUE')
        df['P_VALUE'] = df['P_VALUE'].astype(float).apply(util.format_p_value)
        df['ADJ_P_VALUE'] = df['ADJ_P_VALUE'].astype(float).apply(util.format_p_value)
        table_data = df.to_dict('records')
        
        
        table_columns_high_level = [{'name': i, 'id': i} for i in df_high_level.columns]
        df_high_level = df_high_level.sort_values(by='ADJ_P_VALUE', ascending=True)
        df_high_level["P_VALUE"] = df_high_level["P_VALUE"].astype(float).apply(util.format_p_value)
        df_high_level["ADJ_P_VALUE"] = df_high_level["ADJ_P_VALUE"].astype(float).apply(util.format_p_value)
        table_data_high_level = df_high_level.to_dict('records')
        
        
        
        #update_download_button(0)
        
        pathways = []
        df_p =  downloadable_df.drop(columns=["P_VALUE", "ODDS_RATIO", "FOUND", "SUB#", "ADJ_P_VALUE"])
        
        
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
        
        
        
        return table_columns, table_data, table_columns_high_level ,table_data_high_level ,bar_plot1_figure, bar_plot2_figure, table_columns_pathway, table_data_pathway, table_columns_pathway_input, table_data_pathway_input
    else:
        empty_figure = {'data': [], 'layout': go.Layout(title='Empty')}
        return [], [], empty_figure, empty_figure, [], [], [], []


@app.callback(
    [Output('text-input', 'value')],
    [Input('button-example', 'n_clicks')]
)
def load_example(n_clicks):
    if n_clicks > 0:
        return [constants.placeholder]
    else:
        return "",

@app.callback(
    Output("download-tsv", "data"),
    Input("button-download", "n_clicks"),
    prevent_initial_call=True
)
def download_tsv(n_clicks):
    if not downloadable_df.empty:
        return dcc.send_data_frame(downloadable_df.to_csv, "results_site_level.tsv", sep='\t')
    else:
        return None


@app.callback(
    Output('button-download', 'disabled'),
    Input('button-start-analysis', 'n_clicks'),
    prevent_initial_call=True
)
def update_download_button(n_clicks):
    if n_clicks > 0:
        if not downloadable_df.empty:
            return False
    return True


@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open  # Umschalten zwischen offen und geschlossen
    return is_open





if __name__ == '__main__':
    raw_data = pd.read_csv(constants.KIN_SUB_DATASET_PATH, sep='\t')
    raw_data = raw_data[raw_data['SUB_ORGANISM'] == constants.SUB_ORGANISM]
    raw_data = raw_data[raw_data['KIN_ORGANISM'] == constants.KIN_ORGANISM]
    
    reactome = pd.read_csv(constants.REACTOME_PATH, sep='\t', header=None, names=['UPID', 'REACTOME_ID', 'LINK', 'REACTOME_NAME', '0', 'SPECIES'])
    reactome = reactome[reactome['SPECIES'] == constants.ORGANISM_REACTOME]
    

    app.run_server(debug=True)