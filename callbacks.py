# callbacks.py
import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc # Falls direkt in Callbacks verwendet
from dash import dcc, html # Falls direkt in Callbacks verwendet (z.B. für dcc.send_data_frame)
import plotly.graph_objects as go
import pandas as pd
import math
import base64
import uuid

import util  # Deine Utility-Funktionen
import constants # Deine Konstanten

# Globale DataFrame-Variablen hier entfernen! Daten werden über Stores verwaltet.

def register_callbacks(app):
    """Registriert alle Callbacks der Anwendung."""

    # --- Store Initialization Callbacks ---
    @app.callback(
        Output("raw-data-store", "data", allow_duplicate=False),
        Input("session-id", "data"),
        prevent_initial_call=False
    )
    def initialize_raw_data_store(session_id):
        if session_id:
            print("Initializing raw-data-store with default dataset.")
            raw_data_df = util.load_psp_dataset()
            print(f"Default dataset loaded, rows: {len(raw_data_df) if raw_data_df is not None else 0}")
            if raw_data_df is not None and not raw_data_df.empty:
                return raw_data_df.to_dict("records")
            else:
                print("Failed to load default dataset or dataset is empty.")
                return [] # Leere Liste als Fallback
        return dash.no_update

    @app.callback(
        Output('session-id', 'data'),
        Input('url', 'pathname'), # Reagiert auf das Laden der Seite (aus dcc.Location)
        State('session-id', 'data')
    )
    def initialize_session(pathname, existing_id):
        if existing_id:
            return existing_id
        new_id = str(uuid.uuid4())
        print(f"New session started: {new_id}")
        return new_id

    # # --- Input and Settings Callbacks ---
    # @app.callback(
    #     Output("raw-data-store", "data"),
    #     Input("checkbox_custom_dataset", "value"),
    #     prevent_initial_call=True # Erst reagieren, wenn User klickt
    # )
    # def handle_dataset_selection(checked_values):
    #     if "harry_only" in checked_values:
    #         print("Harry Only Mode selected. Loading custom dataset into store.")
    #         raw_data_df = pd.read_csv(constants.CUSTOM_DATASET_PATH, sep="\t")
    #         raw_data_df = raw_data_df.drop_duplicates()
    #         raw_data_df = raw_data_df[raw_data_df["SUB_ORGANISM"] == constants.SUB_ORGANISM]
    #         raw_data_df = raw_data_df[raw_data_df["KIN_ORGANISM"] == constants.KIN_ORGANISM]
    #         print("Custom dataset loaded into store, rows:", len(raw_data_df))
    #     else:
    #         print("Harry Only Mode deselected. Loading default dataset into store.")
    #         raw_data_df = util.load_psp_dataset()
    #         print("Default dataset loaded into store, rows:", len(raw_data_df) if raw_data_df is not None else 0)
        
    #     if raw_data_df is not None and not raw_data_df.empty:
    #         return raw_data_df.to_dict("records")
    #     return []


    @app.callback(
        Output("current-title-store", "data"),
        Input("notes", "value")
    )
    def update_download_title_in_store(notes_value):
        if notes_value and notes_value.strip() != "":
            return notes_value.strip()
        return constants.DEFAULT_DOWNLOAD_FILE_NAME


    @app.callback(
        Output("text-input", "value"),
        [Input("button-example", "n_clicks"), Input("upload-text-file", "contents")],
        prevent_initial_call=True
    )
    def load_example_or_file(n_clicks_example, file_contents):
        triggered_id = dash.callback_context.triggered_id
        if not triggered_id: # Sollte durch prevent_initial_call nicht passieren
            return dash.no_update

        if "button-example" in triggered_id:
            return constants.PLACEHOLDER_INPUT
        elif "upload-text-file" in triggered_id and file_contents:
            try:
                content_type, content_string = file_contents.split(",")
                decoded = base64.b64decode(content_string)
                text = decoded.decode("utf-8")
                return text
            except Exception as e:
                print(f"Error processing uploaded file: {e}")
                return "Error: Could not read file content."
        return dash.no_update

    @app.callback(
        Output("correction-method-store", "data"),
        Output("correction-method-display", "children"),
        Input("correction-method-dropdown", "value")
    )
    def update_correction_method_store_and_display(selected_method):
        return selected_method, f"Selected method: {selected_method}"

    @app.callback(
        Output("floppy-settings-store", "data"),
        Input("floppy-slider", "value"),
        Input("matching-mode-radio", "value"),
    )
    def update_floppy_settings(slider_value, radio_value):
        settings = {
            "floppy_value": int(slider_value),
            "matching_mode": radio_value
        }
        print(f"Floppy settings updated in store: {settings}")
        return settings

    # --- Analysis Callback ---
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
        [Input("button-start-analysis", "n_clicks")],
        [
            State("text-input", "value"),
            State("correction-method-store", "data"),
            State("raw-data-store", "data"),
            State("floppy-settings-store", "data")
        ],
        prevent_initial_call=True
    )
    def run_analysis(n_clicks, text_value, correction_method, raw_data_dict, floppy_settings):
        if not all([n_clicks > 0, text_value, raw_data_dict, floppy_settings]):
            print("Analysis not started: Missing inputs.")
            return (dash.no_update,) * 10 # Korrekte Anzahl an no_updates

        raw_data_df = pd.DataFrame.from_dict(raw_data_dict)
        if raw_data_df.empty:
            print("Raw data is empty. Cannot start analysis.")
            # Hier könntest du eine Meldung für den User ausgeben, z.B. über ein dcc.ConfirmDialogProvider
            return (dash.no_update,) * 10

        print(f"Raw data (from store) rows: {len(raw_data_df)}")
        
        floppy_val = floppy_settings.get("floppy_value", 5)
        match_mode = floppy_settings.get("matching_mode", "exact")
        print(f"Analysis params: Floppy={floppy_val}, MatchMode={match_mode}, Correction={correction_method}")

        try:
            site_level_results, sub_level_results, site_hits, sub_hits = util.start_eval(
                content=text_value,
                raw_data=raw_data_df,
                correction_method=correction_method,
                rounding=True,
                aa_mode=match_mode,
                tolerance=floppy_val,
            )
        except Exception as e:
            print(f"Error during start_eval: {e}")
            # Hier könntest du eine Fehlermeldung an den User senden
            empty_figure = {"data": [], "layout": go.Layout(title=f"Error during analysis: {e}")}
            return [], [], [], [], [], [], [], [], empty_figure, empty_figure


        if site_level_results.empty and sub_level_results.empty:
            print("No enrichment results from start_eval.")
            empty_figure = {"data": [], "layout": go.Layout(title="No significant enrichment found.")}
            return [], [], [], [], [], [], [], [], empty_figure, empty_figure

        bar_plot_site_enrichment, bar_plot_sub_enrichment = create_barplots(site_level_results, sub_level_results)

        site_level_results_sorted = site_level_results.sort_values(by="P_VALUE", ascending=True) if not site_level_results.empty else pd.DataFrame()
        sub_level_results_sorted = sub_level_results.sort_values(by="ADJ_P_VALUE", ascending=True) if not sub_level_results.empty else pd.DataFrame()
        
        site_level_results_linked = util.add_uniprot_link_col(site_level_results_sorted.copy())
        sub_level_results_linked = util.add_uniprot_link_col(sub_level_results_sorted.copy())

        table_columns_site = [{"name": i, "id": i, "presentation": "markdown" if i == "UPID" else "input"} for i in site_level_results_linked.columns] if not site_level_results_linked.empty else []
        table_columns_sub = [{"name": i, "id": i, "presentation": "markdown" if i == "UPID" else "input"} for i in sub_level_results_linked.columns] if not sub_level_results_linked.empty else []

        print("Analysis successful.")
        return (
            site_level_results_sorted.to_dict("records"),
            sub_level_results_sorted.to_dict("records"),
            site_hits.to_dict("records") if not site_hits.empty else [],
            sub_hits.to_dict("records") if not sub_hits.empty else [],
            table_columns_site,
            site_level_results_linked.to_dict("records"),
            table_columns_sub,
            sub_level_results_linked.to_dict("records"),
            bar_plot_site_enrichment,
            bar_plot_sub_enrichment
        )

    # --- Plotting Function (kann hier bleiben oder nach util.py) ---
    def create_barplots(site_level_results, sub_level_results):
        site_level_barplot = {"data": [], "layout": go.Layout(title="Site-level: No data to display")}
        sub_level_barplot = {"data": [], "layout": go.Layout(title="Substrate-level: No data to display")}

        if site_level_results is not None and not site_level_results.empty and "ADJ_P_VALUE" in site_level_results.columns and "KINASE" in site_level_results.columns:
            site_df = site_level_results.copy()
            site_df["LOG_ADJ_P_VALUE"] = site_df["ADJ_P_VALUE"].astype(float).apply(lambda x: -math.log10(x) if pd.notna(x) and x > 0 else 0)
            site_df = site_df.sort_values(by="LOG_ADJ_P_VALUE", ascending=True) # ascending True for horizontal barplot to have highest on top
            
            site_level_barplot = {
                "data": [
                    go.Bar(
                        y=site_df["KINASE"],
                        x=site_df["LOG_ADJ_P_VALUE"],
                        orientation="h",
                        marker=dict(
                            color=site_df["LOG_ADJ_P_VALUE"],
                            colorscale=constants.BAR_COLORSCALE,
                        ),
                    ),
                ],
                "layout": go.Layout(
                    title="Site-level enriched kinases",
                    xaxis={"title": "-log10 (adjusted p-value)"},
                    yaxis={"title": "Kinases", "automargin": True},
                    margin=dict(l=150, r=20, t=50, b=50), # Adjust margins
                    height=max(300, len(site_df) * 25 + 100) # Dynamische Höhe
                ),
            }

        if sub_level_results is not None and not sub_level_results.empty and "ADJ_P_VALUE" in sub_level_results.columns and "KINASE" in sub_level_results.columns:
            sub_df = sub_level_results.copy()
            sub_df["LOG_ADJ_P_VALUE"] = sub_df["ADJ_P_VALUE"].astype(float).apply(lambda x: -math.log10(x) if pd.notna(x) and x > 0 else 0)
            sub_df = sub_df.sort_values(by="LOG_ADJ_P_VALUE", ascending=True)

            sub_level_barplot = {
                "data": [
                    go.Bar(
                        y=sub_df["KINASE"],
                        x=sub_df["LOG_ADJ_P_VALUE"],
                        orientation="h",
                        marker=dict(
                            color=sub_df["LOG_ADJ_P_VALUE"],
                            colorscale=constants.BAR_COLORSCALE,
                        ),
                    ),
                ],
                "layout": go.Layout(
                    title="Substrate-level enriched kinases",
                    xaxis={"title": "-log10 (adjusted p-value)"},
                    yaxis={"title": "Kinases", "automargin": True},
                    margin=dict(l=150, r=20, t=50, b=50),
                    height=max(300, len(sub_df) * 25 + 100)
                ),
            }
        return site_level_barplot, sub_level_barplot


    def get_default_filename(current_title_from_store, level_type=""):
        prefix = current_title_from_store if current_title_from_store and current_title_from_store.strip() != "" and current_title_from_store != constants.DEFAULT_DOWNLOAD_FILE_NAME else "enrichment_results"
        return prefix
    
    @app.callback(
        [Output("download-filename-modal", "is_open"),
        Output("download-filename-input", "value"),
        Output("active-download-type-store", "data")],
        [Input("button-download", "n_clicks"),
        Input("button-download-high-level", "n_clicks")],
        [State("current-title-store", "data")], # State für is_open hier nicht mehr nötig für reines Öffnen
        prevent_initial_call=True
    )
    def open_download_modal(n_site, n_high, current_title_from_store):
        ctx = dash.callback_context
        if not ctx.triggered_id:
            return dash.no_update, dash.no_update, dash.no_update

        button_id_triggered = ctx.triggered_id.split(".")[0]

        if button_id_triggered == "button-download" and n_site > 0:
            print(f"INFO: Download-Button '{button_id_triggered}' geklickt. Öffne Dateinamen-Modal für Site-Level.") # <--- Logging
            default_filename = get_default_filename(current_title_from_store)
            return True, default_filename, "site" # Modal öffnen
        elif button_id_triggered == "button-download-high-level" and n_high > 0:
            print(f"INFO: Download-Button '{button_id_triggered}' geklickt. Öffne Dateinamen-Modal für Sub-Level.") # <--- Logging
            default_filename = get_default_filename(current_title_from_store)
            return True, default_filename, "sub" # Modal öffnen
        
        return dash.no_update, dash.no_update, dash.no_update
    
    
    @app.callback(
        [Output("download-tsv", "data"),  # Output für Site-Level dcc.Download
        Output("download-tsv-high-level", "data"),  # Output für Sub-Level dcc.Download
        Output("download-filename-modal", "is_open", allow_duplicate=True)],  # Modal nach Aktion schließen
        Input("confirm-download-modal-button", "n_clicks"),
        [State("download-filename-input", "value"),
        State("active-download-type-store", "data"),
        State("site-level-results-store", "data"),
        State("site-hit-data-store", "data"),
        State("sub-level-results-store", "data"),
        State("sub-hit-data-store", "data")],
        prevent_initial_call=True
    )
    def trigger_actual_download(n_confirm, input_filename, active_download_type,
                                site_results_dict, site_hits_dict,
                                sub_results_dict, sub_hits_dict):

        # Prüfen, ob der Callback durch den Button-Klick ausgelöst wurde und ob Eingaben vorhanden sind
        if n_confirm == 0 or not input_filename or not active_download_type:
            # Wenn nicht durch Klick oder keine Filename/Type, keine Aktion für Downloads,
            # Modal-Status nicht ändern (oder explizit offen lassen, wenn gewünscht)
            return dash.no_update, dash.no_update, dash.no_update # oder True, um Modal offen zu halten

        filename_base = input_filename.strip()
        if not filename_base: # Fallback, falls der Nutzer alles löscht oder nichts eingibt
            filename_base = "enrichment_results" # Oder ein anderer sinnvoller Default

        # Initialisiere Download-Daten mit None (oder dash.no_update)
        site_download_data = None
        sub_download_data = None

        # Logik für SITE-LEVEL DOWNLOAD
        # Logik für SITE-LEVEL DOWNLOAD
        if active_download_type == "site":
            if not site_results_dict:
                print("FEHLER: Site-Level Ergebnisse nicht im Store für den Download.")
                return None, None, False 

            site_results_df = pd.DataFrame.from_dict(site_results_dict)
            if site_results_df.empty:
                print("INFO: Site-Level DataFrame ist leer. Kein Download.")
                return None, None, False 

            downloadable_df_site = site_results_df.copy() 

            if site_hits_dict:
                site_hits_df = pd.DataFrame.from_dict(site_hits_dict)
                if not site_hits_df.empty and "KINASE" in site_hits_df.columns and \
                   "SUB_MOD_RSD_sample" in site_hits_df.columns and "IMPUTED" in site_hits_df.columns: # Prüfe auf neue Spalten
                    print("INFO: Site hits data available for custom merging.")

                    # Sicherstellen, dass die Spalten die richtigen Typen haben
                    site_hits_df["SUB_MOD_RSD_sample"] = site_hits_df["SUB_MOD_RSD_sample"].astype(str)
                    site_hits_df["IMPUTED"] = site_hits_df["IMPUTED"].astype(bool) # Sicherstellen, dass IMPUTED boolean ist

                    # Hilfsfunktion, um den Hit-String zu formatieren
                    def format_hit_string(row):
                        site = row["SUB_MOD_RSD_sample"]
                        if row["IMPUTED"]:
                            return f"{site}(i)"
                        return site

                    # Anwenden der Formatierung auf jede Zeile
                    site_hits_df["FORMATTED_HIT"] = site_hits_df.apply(format_hit_string, axis=1)

                    # Gruppieren nach KINASE und die formatierten Hits zusammenfassen
                    # Wichtig: `dropna()` um sicherzustellen, dass nur Zeilen mit gültigen KINASE-Werten berücksichtigt werden
                    # `set` um Duplikate innerhalb einer Kinase-Gruppe zu entfernen, dann `sorted` für konsistente Reihenfolge
                    grouped_hits = (
                        site_hits_df.dropna(subset=['KINASE', 'FORMATTED_HIT'])
                        .groupby("KINASE")["FORMATTED_HIT"]
                        .apply(lambda x: ", ".join(sorted(list(set(x))))) # Eindeutige, sortierte Hits
                        .reset_index(name="HITS") # Spaltenname jetzt "HITS"
                    )
                    
                    # Merge mit dem Haupt-DataFrame
                    if not grouped_hits.empty:
                        downloadable_df_site = pd.merge(downloadable_df_site, grouped_hits, on="KINASE", how="left")
                    else:
                        # Falls grouped_hits leer ist, füge eine leere HITS-Spalte hinzu, um Konsistenz zu wahren
                        downloadable_df_site["HITS"] = pd.NA 
                else:
                    print("WARNUNG: Erforderliche Spalten (KINASE, SUB_MOD_RSD_sample, IMPUTED) nicht in site_hits_df gefunden oder DataFrame leer.")
                    downloadable_df_site["HITS"] = pd.NA # Füge eine leere Spalte hinzu, falls keine Hits vorhanden sind
            else:
                print("INFO: Keine site_hits_dict Daten vorhanden.")
                downloadable_df_site["HITS"] = pd.NA # Füge eine leere Spalte hinzu, falls keine Hits vorhanden sind
            
            final_filename_site = f"{filename_base}_site_level.tsv"
            print(f"INFO: Bereite Site-Level Download vor: {final_filename_site}")
            return dcc.send_data_frame(downloadable_df_site.to_csv, final_filename_site, sep="\t", index=False), dash.no_update, False

        # Logik für SUB-LEVEL DOWNLOAD
        elif active_download_type == "sub":
            if not sub_results_dict:
                print("FEHLER: Sub-Level Ergebnisse nicht im Store für den Download.")
                return None, None, False # Modal schließen, kein Download

            sub_results_df = pd.DataFrame.from_dict(sub_results_dict)
            if sub_results_df.empty:
                print("INFO: Sub-Level DataFrame ist leer. Kein Download.")
                return None, None, False # Modal schließen, kein Download

            # DataFrame für den Download vorbereiten
            downloadable_df_sub = sub_results_df.copy()
            if sub_hits_dict:
                sub_hits_df = pd.DataFrame.from_dict(sub_hits_dict)
                if not sub_hits_df.empty and "KINASE" in sub_hits_df.columns and "SUB_GENE" in sub_hits_df.columns:
                    sub_hits_df["SUB_GENE"] = sub_hits_df["SUB_GENE"].astype(str)
                    high_hits_grouped = (
                        sub_hits_df.groupby("KINASE")["SUB_GENE"]
                        .apply(lambda x: ", ".join(sorted(list(set(x)))))
                        .reset_index(name="ASSOCIATED_SUBSTRATES")
                    )
                    downloadable_df_sub = pd.merge(downloadable_df_sub, high_hits_grouped, on="KINASE", how="left")

            final_filename_sub = f"{filename_base}_sub_level.tsv"
            print(f"INFO: Bereite Sub-Level Download vor: {final_filename_sub}")
            # Hier wird der Download für "download-tsv-high-level" ausgelöst
            return dcc.send_data_frame(downloadable_df_sub.to_csv, final_filename_sub, sep="\t", index=False)
        
        else:
            print(f"WARNUNG: Unbekannter active_download_type: {active_download_type}")
            return None, None, False # Modal schließen, kein Download

        # Gibt die vorbereiteten Download-Daten (oder None) an die dcc.Download Komponenten
        # und schließt das Modal.
        return site_download_data, sub_download_data, False
    
    
    # --- UI Interaction Callbacks (Modal, Detail Tables) ---
    @app.callback(
        Output("modal", "is_open"),
        [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
        [State("modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_modal(n_open, n_close, is_open):
        return not is_open

    @app.callback(
        [Output("table-viewer-deep-hits", "columns"), Output("table-viewer-deep-hits", "data")],
        Input("table-viewer", "active_cell"),
        State("table-viewer", "data"),
        State("site-hit-data-store", "data"),
        prevent_initial_call=True
    )
    def display_deep_hit_details(active_cell, table_data, site_hits_dict):
        if not active_cell or not table_data or not site_hits_dict:
            return [], [{"Info": "Select a kinase from the table above to see details."}]
        
        try:
            row_data = table_data[active_cell["row"]]
            kinase = row_data.get("KINASE")
            if not kinase:
                return [], [{"Info": "Could not identify kinase from selected row."}]

            site_hits_df = pd.DataFrame.from_dict(site_hits_dict)
            if site_hits_df.empty or "KINASE" not in site_hits_df.columns:
                return [], [{"Info": f"No detailed hits data available for {kinase}."}]

            filtered_hits = site_hits_df[site_hits_df["KINASE"] == kinase]
            if filtered_hits.empty:
                return [{"name": "Info", "id": "Info"}], [{"Info": f"No specific hits found for {kinase} in the detailed data."}]

            columns = [{"name": i, "id": i} for i in filtered_hits.columns]
            return columns, filtered_hits.to_dict("records")
        except Exception as e:
            print(f"Error in display_deep_hit_details: {e}")
            return [], [{"Error": "An error occurred while fetching details."}]


    @app.callback(
        [Output("table-viewer-high-hits", "columns"), Output("table-viewer-high-hits", "data")],
        Input("table-viewer-high-level", "active_cell"),
        State("table-viewer-high-level", "data"),
        State("sub-hit-data-store", "data"),
        prevent_initial_call=True
    )
    def display_high_hit_details(active_cell, table_data, sub_hits_dict):
        if not active_cell or not table_data or not sub_hits_dict:
            return [], [{"Info": "Select a kinase from the table above to see details."}]

        try:
            row_data = table_data[active_cell["row"]]
            kinase = row_data.get("KINASE")
            if not kinase:
                return [], [{"Info": "Could not identify kinase from selected row."}]

            sub_hits_df = pd.DataFrame.from_dict(sub_hits_dict)
            if sub_hits_df.empty or "KINASE" not in sub_hits_df.columns:
                return [], [{"Info": f"No detailed hits data available for {kinase}."}]
                
            filtered_hits = sub_hits_df[sub_hits_df["KINASE"] == kinase]
            if filtered_hits.empty:
                return [{"name": "Info", "id": "Info"}], [{"Info": f"No specific hits found for {kinase} in the detailed data."}]
                
            columns = [{"name": i, "id": i} for i in filtered_hits.columns]
            return columns, filtered_hits.to_dict("records")
        except Exception as e:
            print(f"Error in display_high_hit_details: {e}")
            return [], [{"Error": "An error occurred while fetching details."}]