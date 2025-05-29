# app.py
import dash
import dash_bootstrap_components as dbc

# Eigene Module importieren
from layout import create_layout
from callbacks import register_callbacks
# import util # Wird hier nicht mehr direkt benötigt, wenn Callbacks ausgelagert sind
# import constants # Wird hier nicht mehr direkt benötigt

# Initialize the Dash app
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css" # Oder eine lokale Kopie in /assets
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css],
                suppress_callback_exceptions=True) # Wichtig, wenn Komponenten dynamisch erzeugt/entfernt werden

server = app.server # Für die Bereitstellung (z.B. mit Gunicorn)

# Layout zuweisen
app.layout = create_layout()

# Callbacks registrieren
register_callbacks(app)

# Server starten
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
    # app.run_server(host="0.0.0.0", port=8080, debug=False) # Beispiel für Produktion