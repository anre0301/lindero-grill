from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import datetime

# ===== Firebase Admin =====
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# ===== Login por PIN =====
VALID_PIN = os.environ.get("POS_PIN", "0102")
PIN_LEN = int(os.environ.get("POS_PIN_LEN", "4"))

# Rutas protegidas
PROTECTED_ENDPOINTS = {"panel", "seed"}

# ===== Inicialización Firebase (flexible para distintos hostings) =====
def init_firebase():
    if firebase_admin._apps:
        return

    # 1) Variable de entorno con el JSON completo (Railway, Deta, etc.)
    env_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if env_json:
        try:
            data = json.loads(env_json)
            cred = credentials.Certificate(data)
            firebase_admin.initialize_app(cred)
            return
        except Exception:
            # si falla, sigue probando otras rutas
            pass

    # 2) Ruta a secret file (Render: /etc/secrets/serviceAccountKey.json)
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.exists(env_path):
        cred = credentials.Certificate(env_path)
        firebase_admin.initialize_app(cred)
        return

    # 3) Archivo local (desarrollo)
    fixed_path = os.path.join("keys", "serviceAccountKey.json")
    if os.path.exists(fixed_path):
        cred = credentials.Certificate(fixed_path)
        firebase_admin.initialize_app(cred)
        return

    # 4) Último recurso: Application Default Credentials
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

init_firebase()
db = firestore.client()

# ===== Middleware auth simple por PIN =====
@app.before_request
def require_login():
    open_endpoints = {"static", "index", "verify_pin", "healthz"}
    if request.endpoint in open_endpoints or request.endpoint is None:
        return
    if request.endpoint in PROTECTED_ENDPOINTS and not session.get("user"):
        return redirect(url_for("index"))

# ===== Healthcheck (para hosting) =====
@app.route("/healthz")
def healthz():
    return "ok", 200

# ===== Rutas =====
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/verify-pin", methods=["POST"])
def verify_pin():
    data = request.get_json(silent=True) or {}
    pin = str(data.get("pin", "")).strip()
    if not (pin.isdigit() and len(pin) == PIN_LEN):
        return jsonify(ok=False, error=f"El PIN debe tener {PIN_LEN} dígitos."), 400
    if pin == str(VALID_PIN):
        session.clear()
        session["user"] = "cajero"
        session.permanent = False
        return jsonify(ok=True)
    return jsonify(ok=False, error="PIN incorrecto"), 401

@app.route("/panel")
def panel():
    return render_template("panel.html")

@app.route("/receta")
def receta():
    return render_template("receta.html")

@app.route("/movimientos")
def movimientos():
    return render_template("movimientos.html")

@app.route("/hoy")
def hoy():
    return render_template("hoy.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ===== Seed: datos demo =====
@app.route("/seed")
def seed():
    now = datetime.utcnow()

    db.collection("settings").document("main").set({
        "name": "Lindero Grill",
        "currency": "PEN",
        "igvRate": 0.18,
        "address": "Av. Ejemplo 123, Lima",
        "createdAt": now, "updatedAt": now
    })

    categories = [
        {"id": "pollos", "name": "Pollos", "order": 1, "active": True},
        {"id": "parrillas", "name": "Parrillas", "order": 2, "active": True},
        {"id": "bebidas", "name": "Bebidas", "order": 3, "active": True},
        {"id": "guarniciones", "name": "Guarniciones", "order": 4, "active": True},
    ]
    for c in categories:
        db.collection("categories").document(c["id"]).set(c)

    products = [
        {"id":"p1","name":"Pollo a la brasa Entero","catId":"pollos","price":52,"cost":32,"unit":"UND","taxRate":0.18,"trackStock":True,"stock":15,"minStock":3,"active":True},
        {"id":"p2","name":"1/2 Pollo a la brasa","catId":"pollos","price":27.5,"cost":17,"unit":"UND","taxRate":0.18,"trackStock":True,"stock":20,"minStock":4,"active":True},
        {"id":"p3","name":"Parrilla Personal","catId":"parrillas","price":38,"cost":22,"unit":"UND","taxRate":0.18,"trackStock":False,"stock":0,"minStock":0,"active":True},
        {"id":"p4","name":"Parrilla Familiar","catId":"parrillas","price":75,"cost":40,"unit":"UND","taxRate":0.18,"trackStock":False,"stock":0,"minStock":0,"active":True},
        {"id":"p5","name":"Papas fritas","catId":"guarniciones","price":9,"cost":4,"unit":"UND","taxRate":0.18,"trackStock":True,"stock":50,"minStock":8,"active":True},
        {"id":"p7","name":"Gaseosa 500ml","catId":"bebidas","price":5,"cost":2.8,"unit":"UND","taxRate":0.18,"trackStock":True,"stock":60,"minStock":10,"active":True},
        {"id":"p8","name":"Gaseosa 1.5L","catId":"bebidas","price":12,"cost":7,"unit":"UND","taxRate":0.18,"trackStock":True,"stock":30,"minStock":5,"active":True},
    ]
    for p in products:
        db.collection("products").document(p["id"]).set({**p, "createdAt": now, "updatedAt": now})

    for n in range(1, 16):
        db.collection("floors").document("piso1").collection("tables").document(f"m{n}").set({
            "number": n, "status": "libre", "total": 0, "currentOrderId": None, "updatedAt": now
        })

    return "✅ Seed listo: settings, categorías, productos y mesas (piso1). Abre /panel"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
