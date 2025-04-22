import os
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from graph import start_agentic_flow

# ──────────────────────────────────────────────────────────────────────────────
#  Configurazione
# ──────────────────────────────────────────────────────────────────────────────

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "replace‑me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)

# ──────────────────────────────────────────────────────────────────────────────
#  Modelli
# ──────────────────────────────────────────────────────────────────────────────
class RunSequence(db.Model):
    __tablename__ = "run_sequence"
    id = db.Column(db.String(256), primary_key=True)
    date = db.Column(db.DateTime, nullable=False)

    requests = db.relationship("Request", back_populates="run_seq",
                               cascade="all, delete-orphan")


class Request(db.Model):
    __tablename__ = "request"
    id = db.Column(db.String(256), primary_key=True)
    date = db.Column(db.DateTime)
    api = db.Column(db.String(256), nullable=False)
    api_path = db.Column(db.String(512), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    http_code = db.Column(db.Integer, nullable=False)
    outcome = db.Column(db.String(10), nullable=False)
    request_json = db.Column("request", db.JSON)
    response_json = db.Column("response", db.JSON)
    run_sequence = db.Column(db.String(256),
                             db.ForeignKey("run_sequence.id"),
                             nullable=False)

    run_seq = db.relationship("RunSequence", back_populates="requests")

# ──────────────────────────────────────────────────────────────────────────────
#  Utils
# ──────────────────────────────────────────────────────────────────────────────
def strftime_or_empty(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""

# ──────────────────────────────────────────────────────────────────────────────
#  Rotte
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    """Pagina 1 – elenco run_sequence con filtri data."""
    q = RunSequence.query

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    if date_from:
        q = q.filter(RunSequence.date >= date_from)
    if date_to:
        q = q.filter(RunSequence.date <= date_to)

    sequences = q.order_by(RunSequence.date.desc()).all()
    return render_template("home.html",
                           sequences=sequences,
                           date_from=date_from or "",
                           date_to=date_to or "")


@app.route("/run/<run_id>")
def run_details(run_id: str):
    """Pagina 2 – richieste di un run_sequence."""
    seq = RunSequence.query.get_or_404(run_id)

    # DataTables può fare l’ordinamento lato client;
    # se preferisci lato server, usa request.args.get("order") ecc.
    requests_rows = Request.query.filter_by(run_sequence=run_id).all()
    return render_template("requests.html",
                           seq=seq,
                           requests_rows=requests_rows)


@app.route("/upload-spec", methods=["POST"])
def upload_spec():
    """Upload di file .json/.yaml; al momento li salviamo e basta."""
    f = request.files.get("spec_file")
    if not f:
        flash("Nessun file selezionato", "danger")
        return redirect(url_for("home"))

    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in {".json", ".yaml", ".yml"}:
        flash("Formato non consentito", "danger")
        return redirect(url_for("home"))

    f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    flash("Spec caricato correttamente!", "success")
    # Qui potresti lanciare la tua logica di import/test.
    return redirect(url_for("home"))


# ──────────────────────────────────────────────────────────────────────────────
#  API Json per popup (opzionale, usata da JS per caricare JSON completo)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/request/<req_id>/json/<kind>")
def request_json(req_id: str, kind: str):
    """Restituisce request_json o response_json intero."""
    row = Request.query.get_or_404(req_id)
    if kind == "request":
        return jsonify(row.request_json)
    elif kind == "response":
        return jsonify(row.response_json)
    else:
        return {}, 404


if __name__ == "__main__":
    app.run(debug=True)
