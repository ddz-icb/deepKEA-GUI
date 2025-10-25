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
            raw_data = util.load_psp_dataset()
            print(f"Default dataset loaded, rows: {len(raw_data) if raw_data is not None else 0}")
            if raw_data is not None and len(raw_data) > 0:
                return raw_data
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

    @app.callback(
        Output("selected-amino-acids-store", "data"),
        Input("amino-acid-checklist", "value")
    )
    def update_selected_amino_acids(selected_values):
        # Die `selected_values` ist eine Liste der 'value's der angeklickten Checkboxen
        print(f"INFO: Selected amino acids updated in store: {selected_values}")
        return selected_values


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
        Input("correction-method-dropdown", "value")
    )
    def update_correction_method_store(selected_method):
        return selected_method
    
    @app.callback(
        Output("statistical-test-store", "data"),
        Input("statistical-test-dropdown", "value")
    )
    def update_statistical_test_store(selected_test):
        return selected_test

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
            State("statistical-test-store", "data"),
            State("raw-data-store", "data"),
            State("floppy-settings-store", "data"),
            State("selected-amino-acids-store", "data"),
            State("limit-inferred-hits-store", "data")
        ],
        prevent_initial_call=True
    )
    def run_analysis(n_clicks, text_value, correction_method, statistical_test, raw_data_dict, floppy_settings, selected_amino_acids, limit_inferred_hits):
        # Validate button click
        if not n_clicks or n_clicks == 0:
            print("Analysis not started: Button not clicked.")
            return (dash.no_update,) * 10
        
        # Check if at least one amino acid is selected
        if not selected_amino_acids or len(selected_amino_acids) == 0:
            print("Analysis not started: No amino acids selected.")
            return (dash.no_update,) * 10
        
        # Validate all required inputs
        if not text_value or not text_value.strip():
            print("Analysis not started: No text input provided.")
            return (dash.no_update,) * 10
        
        if not raw_data_dict:
            print("Analysis not started: Raw data not loaded.")
            return (dash.no_update,) * 10
        
        if not floppy_settings:
            print("Analysis not started: Floppy settings not available.")
            return (dash.no_update,) * 10
        
        if not limit_inferred_hits:
            print("Analysis not started: Limit inferred hits setting not available.")
            return (dash.no_update,) * 10
        
        # Extract limit value
        limit_inferred_hits_value = int(limit_inferred_hits.get("max_hits", 7))
        print(f"Inferred hit limit: {limit_inferred_hits_value}")

        # Convert raw_data_dict to DataFrame
        raw_data_df = pd.DataFrame.from_dict(raw_data_dict)
        if raw_data_df.empty:
            print("Raw data is empty. Cannot start analysis.")
            return (dash.no_update,) * 10

        print(f"INFO: Starting analysis with selected amino acids: {selected_amino_acids}")
        print(f"Raw data (from store) rows: {len(raw_data_df)}")
        
        floppy_val = floppy_settings.get("floppy_value", 5)
        match_mode = floppy_settings.get("matching_mode", "exact")
        print(f"Analysis params: Floppy={floppy_val}, MatchMode={match_mode}, Correction={correction_method}, Statistical Test={statistical_test}")

        try:
            site_level_results, sub_level_results, site_hits, sub_hits = util.start_eval(
                content=text_value,
                raw_data=raw_data_df,
                correction_method=correction_method,
                statistical_test=statistical_test,
                rounding=True,
                aa_mode=match_mode,
                tolerance=floppy_val,
                selected_amino_acids=selected_amino_acids,
                inferred_hit_limit=limit_inferred_hits_value
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
            
            # Sort by ADJ_P_VALUE (lowest p-value = most significant) and take top 10
            site_df = site_df.sort_values(by="ADJ_P_VALUE", ascending=True).head(10)
            # Then sort by LOG_ADJ_P_VALUE for display (ascending=True puts highest at top in horizontal bar)
            site_df = site_df.sort_values(by="LOG_ADJ_P_VALUE", ascending=True)
            
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
                    title="Site-level enriched kinases (Top 10)",
                    xaxis={"title": "-log10 (adjusted p-value)"},
                    yaxis={"title": "Kinases", "automargin": True},
                    margin=dict(l=150, r=20, t=50, b=50), # Adjust margins
                    height=max(300, len(site_df) * 25 + 100) # Dynamische Höhe
                ),
            }

        if sub_level_results is not None and not sub_level_results.empty and "ADJ_P_VALUE" in sub_level_results.columns and "KINASE" in sub_level_results.columns:
            sub_df = sub_level_results.copy()
            sub_df["LOG_ADJ_P_VALUE"] = sub_df["ADJ_P_VALUE"].astype(float).apply(lambda x: -math.log10(x) if pd.notna(x) and x > 0 else 0)
            
            # Sort by ADJ_P_VALUE (lowest p-value = most significant) and take top 10
            sub_df = sub_df.sort_values(by="ADJ_P_VALUE", ascending=True).head(10)
            # Then sort by LOG_ADJ_P_VALUE for display
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
                    title="Substrate-level enriched kinases (Top 10)",
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
        Input("button-download-high-level", "n_clicks"),
        Input("cancel-download-modal-button", "n_clicks")],
        [State("current-title-store", "data")], # State für is_open hier nicht mehr nötig für reines Öffnen
        prevent_initial_call=True
    )
    def open_download_modal(n_site, n_high, n_cancel, current_title_from_store):
        ctx = dash.callback_context
        if not ctx.triggered_id:
            return dash.no_update, dash.no_update, dash.no_update

        button_id_triggered = ctx.triggered_id

        if button_id_triggered == "cancel-download-modal-button" and n_cancel:
            print("INFO: Cancel button clicked. Closing modal.")
            return False, dash.no_update, dash.no_update
        
        if button_id_triggered == "button-download" and n_site and n_site > 0:
            print(f"INFO: Download-Button '{button_id_triggered}' geklickt. Öffne Dateinamen-Modal für Site-Level.") # <--- Logging
            default_filename = get_default_filename(current_title_from_store)
            return True, default_filename, "site" # Modal öffnen
        elif button_id_triggered == "button-download-high-level" and n_high and n_high > 0:
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
        if not n_confirm or n_confirm == 0 or not input_filename or not active_download_type:
            # Wenn nicht durch Klick oder keine Filename/Type, keine Aktion für Downloads,
            # Modal-Status nicht ändern (oder explizit offen lassen, wenn gewünscht)
            return dash.no_update, dash.no_update, dash.no_update # oder True, um Modal offen zu halten

        filename_base = input_filename.strip()
        if not filename_base: # Fallback, falls der Nutzer alles löscht oder nichts eingibt
            filename_base = "enrichment_results" # Oder ein anderer sinnvoller Default

        # Logik für SITE-LEVEL DOWNLOAD
        if active_download_type == "site":
            if not site_results_dict:
                print("FEHLER: Site-Level Ergebnisse nicht im Store für den Download.")
                return dash.no_update, dash.no_update, False 

            site_results_df = pd.DataFrame.from_dict(site_results_dict)
            if site_results_df.empty:
                print("INFO: Site-Level DataFrame ist leer. Kein Download.")
                return dash.no_update, dash.no_update, False 

            downloadable_df_site = site_results_df.copy() 

            if site_hits_dict:
                site_hits_df = pd.DataFrame.from_dict(site_hits_dict)
                if not site_hits_df.empty and "KINASE" in site_hits_df.columns and \
                   "SUB_MOD_RSD_sample" in site_hits_df.columns and "IMPUTED" in site_hits_df.columns: # Prüfe auf neue Spalten
                    print("INFO: Site hits data available for custom merging.")

                    # Sicherstellen, dass die Spalten die richtigen Typen haben
                    site_hits_df["SUB_MOD_RSD_sample"] = site_hits_df["SUB_MOD_RSD_sample"].astype(str)
                    site_hits_df["IMPUTED"] = site_hits_df["IMPUTED"].astype(bool) # Sicherstellen, dass IMPUTED boolean ist

                    
                    
                    def format_hit_string(row):
                        # todo fixme gene names or upid
                        upid = row.get("SUB_ACC_ID", "")
                        # upid = row.get("SUB_GENE", "")
                        site = row.get("SUB_MOD_RSD_sample", "")
                        hit_str = f"{upid}-{site}"
                        if row.get("IMPUTED", False):
                            hit_str += "(i)"
                        return hit_str

                    site_hits_df["FORMATTED_HIT"] = site_hits_df.apply(format_hit_string, axis=1)
                    
                    
                    
                    
                    # def format_hit_string(row):
                    #     site = row["SUB_MOD_RSD_sample"]
                    #     if row["IMPUTED"]:
                    #         return f"{site}(i)"
                    #     return site

                    # # Anwenden der Formatierung auf jede Zeile
                    # site_hits_df["FORMATTED_HIT"] = site_hits_df.apply(format_hit_string, axis=1)

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
                return dash.no_update, None, False # Modal schließen, kein Download

            sub_results_df = pd.DataFrame.from_dict(sub_results_dict)
            if sub_results_df.empty:
                print("INFO: Sub-Level DataFrame ist leer. Kein Download.")
                return dash.no_update, None, False # Modal schließen, kein Download

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
            
            
            print("Download mode: ", active_download_type)
            print(f"INFO: Bereite Sub-Level Download vor: {final_filename_sub} with len {str(len(downloadable_df_sub))}")
            # Hier wird der Download für "download-tsv-high-level" ausgelöst
            return dash.no_update, dcc.send_data_frame(downloadable_df_sub.to_csv, final_filename_sub, sep="\t", index=False), False
        
        else:
            print(f"WARNUNG: Unbekannter active_download_type: {active_download_type}")
            return dash.no_update, dash.no_update, False # Modal schließen, kein Download
    
    
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
        
    @app.callback(
        Output("limit-inferred-hits-store", "data"),
        Input("limit-inferred-hits-slider", "value"),
        prevent_initial_call=True
    )
    def update_max_inferred_hit_store(slider_value):
        settings = {
            "max_hits": int(slider_value)
        }
        print(f"Maxium hits settings updated in store: {settings}")
        return settings

    # --- About Modal Callbacks ---
    @app.callback(
        Output("about-modal", "is_open"),
        [Input("open-about-button", "n_clicks"), Input("close-about-button", "n_clicks")],
        [State("about-modal", "is_open")],
    )
    def toggle_about_modal(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    @app.callback(
        Output("about-tab-content", "children"),
        Input("about-tabs", "active_tab")
    )
    def render_about_tab_content(active_tab):
        if active_tab == "tab-overview":
            return html.Div([
                html.H4("Overview", className="mb-3"),
                html.P([
                    html.Strong("fuzzyKEA"), 
                    " is a web-based application for kinase enrichment analysis in phosphoproteomic data."
                ]),
                html.P([
                    "This tool performs Kinase-Substrate Enrichment Analysis (KSEA) using the ",
                    html.A("PhosphoSitePlus", href="https://www.phosphosite.org/", target="_blank"),
                    " database to identify enriched kinases in your phosphoproteomics datasets."
                ]),
                html.H5("Key Features", className="mt-4 mb-2"),
                html.Ul([
                    html.Li("Upload phosphoproteomics data (Uniprot IDs + phosphosites)"),
                    html.Li("Fuzzy matching with configurable position tolerance"),
                    html.Li("Site-level and substrate-level enrichment analysis"),
                    html.Li("Multiple statistical tests (Fisher's Exact, Chi-Square)"),
                    html.Li("Multiple testing correction methods (FDR-BH, FDR-BY, Bonferroni)"),
                    html.Li("Interactive visualizations and downloadable results"),
                ]),
                html.H5("Database Information", className="mt-4 mb-2"),
                html.P([
                    "PhosphoSitePlus® dataset: ",
                    html.Code("Kinase_Substrate_Dataset.txt"),
                    html.Br(),
                    "Last updated: September 14, 2024"
                ]),
                html.Hr(),
                html.P([
                    "Developed at the ",
                    html.Strong("German Diabetes Center (DDZ)"),
                    " - Institute for Clinical Bioinformatics"
                ], className="text-muted"),
            ])
        
        elif active_tab == "tab-features":
            return html.Div([
                html.H4("Features & Capabilities", className="mb-3"),
                
                html.H5("1. Fuzzy Matching Algorithm", className="mt-3"),
                html.P([
                    "The fuzzy matching engine allows approximate matching between your input sites and the database with configurable parameters:"
                ]),
                html.Ul([
                    html.Li([html.Strong("Position Tolerance: "), "Match sites within ±N positions"]),
                    html.Li([html.Strong("Amino Acid Modes: "), html.Ul([
                        html.Li([html.Strong("Exact: "), "Require exact amino acid match"]),
                        html.Li([html.Strong("S/T-similar: "), "Treat Serine and Threonine as equivalent"]),
                        html.Li([html.Strong("Ignore: "), "Match any amino acid at the position"]),
                    ])]),
                    html.Li([html.Strong("1:1 Constraint: "), "Each input site maps to at most one database site (the closest match)"]),
                    html.Li([html.Strong("Inferred Hit Limit: "), "Limit fuzzy matches per kinase to avoid over-representation"]),
                ]),
                
                html.H5("2. Statistical Analysis", className="mt-4"),
                html.Ul([
                    html.Li([html.Strong("Fisher's Exact Test: "), "Recommended for small sample sizes"]),
                    html.Li([html.Strong("Chi-Square Test: "), "Alternative test for larger datasets"]),
                    html.Li([html.Strong("Multiple Testing Correction: "), "FDR-BH (recommended), FDR-BY, or Bonferroni"]),
                ]),
                
                html.H5("3. Two-Level Analysis", className="mt-4"),
                html.Ul([
                    html.Li([html.Strong("Site-level: "), "Enrichment based on individual phosphorylation sites"]),
                    html.Li([html.Strong("Substrate-level: "), "Enrichment based on unique substrate proteins"]),
                ]),
                
                html.H5("4. Export Options", className="mt-4"),
                html.P("Download results in CSV or Excel format with detailed hit information."),
                
                html.Hr(),
                html.Div([
                    dbc.Alert([
                        html.I(className="bi bi-info-circle me-2"),
                        html.Strong("Tip: "),
                        "Use the substrate-level analysis to reduce bias from highly phosphorylated proteins."
                    ], color="info", className="mt-3")
                ])
            ])
        
        elif active_tab == "tab-citation":
            return html.Div([
                html.H4("Citation & Credits", className="mb-3"),
                
                html.H5("How to Cite", className="mt-3"),
                html.Div([
                    html.P("If you use fuzzyKEA in your research, please cite:"),
                    dbc.Card([
                        dbc.CardBody([
                            html.P([
                                "fuzzyKEA: Fuzzy Kinase Enrichment Analysis for Phosphoproteomics Data",
                                html.Br(),
                                "German Diabetes Center (DDZ), Institute for Clinical Bioinformatics",
                                html.Br(),
                                html.Code("https://github.com/ddz-icb/deepKEA-GUI"),
                            ], className="font-monospace small mb-0")
                        ])
                    ], className="mb-3", color="light"),
                ]),
                
                html.H5("PhosphoSitePlus Database", className="mt-4"),
                html.P("This tool uses data from PhosphoSitePlus®. Please cite:"),
                dbc.Card([
                    dbc.CardBody([
                        html.P([
                            "Hornbeck PV, Zhang B, Murray B, Kornhauser JM, Latham V, Skrzypek E ",
                            html.Br(),
                            html.Em("PhosphoSitePlus, 2014: mutations, PTMs and recalibrations."),
                            html.Br(),
                            "Nucleic Acids Res. 2015 Jan;43(Database issue):D512-20.",
                            html.Br(),
                            "PMID: ", html.A("25514926", href="https://pubmed.ncbi.nlm.nih.gov/25514926/", target="_blank")
                        ], className="small mb-0")
                    ])
                ], className="mb-3", color="light"),
                
                html.H5("Development & Contributors", className="mt-4"),
                html.Ul([
                    html.Li([
                        html.Strong("Lead Developer: "), 
                        "German Diabetes Center (DDZ)"
                    ]),
                    html.Li([
                        html.Strong("Institution: "), 
                        "Institute for Clinical Bioinformatics"
                    ]),
                    html.Li([
                        html.Strong("Framework: "), 
                        "Built with Plotly Dash & Python"
                    ]),
                ]),
                
                html.Hr(),
                html.Div([
                    html.H5("Contact & Support", className="mt-4"),
                    html.P([
                        "For questions, bug reports, or feature requests, please visit our ",
                        html.A("GitHub repository", 
                              href="https://github.com/ddz-icb/deepKEA-GUI/issues", 
                              target="_blank"),
                        "."
                    ]),
                ]),
                
                html.Hr(),
                html.P([
                    html.Small([
                        "Version ", constants.APP_VERSION, " | ",
                        "© 2024 German Diabetes Center (DDZ)"
                    ])
                ], className="text-muted text-center mt-4")
            ])
        
        return html.Div("Select a tab to view content.")
