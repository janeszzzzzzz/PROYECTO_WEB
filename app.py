# from flask import Flask, render_template, request, jsonify
# from VLAN import escanear_switch, cambiar_vlan_por_ip, crear_vlan
# from IP_MAC import buscar_dispositivo
# from flask import session
# from werkzeug.security import generate_password_hash, check_password_hash
# import pymysql
# from db import get_db_connection


# import builtins
# import sys
# import io
# import traceback
# import subprocess
# import json
# import os


# app = Flask(__name__)
# app.secret_key = "super_clave_secreta_cambiala_luego"


# # Inventario global del escaneo
# inventario = {}




# # ---------------------------
# # Helper: ejecutar función que usa input() y captura stdout
# # ---------------------------
# def run_func_with_inputs_capture(func, args=(), input_values=None):
#     """
#     Ejecuta func(*args) pero:
#     - sustituye builtins.input por una función que devuelve values secuencialmente
#     - captura sys.stdout y devuelve (stdout_text, func_result)
#     """
#     old_input = builtins.input
#     old_stdout = sys.stdout
#     buf = io.StringIO()

#     inputs = list(input_values or [])

#     def fake_input(prompt=""):
#         # opcional: escribir el prompt en el buffer para ver el flujo
#         print(prompt, end='', file=buf)
#         if inputs:
#             return inputs.pop(0)
#         return ""

#     builtins.input = fake_input
#     sys.stdout = buf

#     result = None
#     try:
#         result = func(*args)
#     except Exception:
#         # capturamos la traza en el buffer para que el cliente la vea
#         traceback.print_exc(file=buf)
#     finally:
#         # restaurar siempre
#         builtins.input = old_input
#         sys.stdout = old_stdout

#     return buf.getvalue(), result


# # =======================
# #        PÁGINAS HTML
# # =======================

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/buscar")
# def buscar_html():
#     return render_template("buscar.html")


# @app.route("/vlan")
# def vlan_html():
#     return render_template("vlan.html")

# @app.route("/inventario")
# def inventario_html():
#     return render_template("inventario.html")

# @app.route("/login")
# def login_html():
#     return render_template("login.html")


# @app.route("/register")
# def register_html():
#     return render_template("register.html")




# # =======================
# #    API - BUSCAR MAC/IP
# # =======================

# @app.route("/api/buscar", methods=["POST"])
# def api_buscar():
#     data = request.json

#     try:
#         resultado = buscar_dispositivo(
#             data["ip_switch"],
#             data["usuario"],
#             data["contrasena"],
#             data["objetivo"],
#             data["modo"]
#         )

#         if not resultado:
#             return jsonify({"error": "No encontrado"}), 404

#         return jsonify(resultado)

#     except Exception as e:
#         print("❌ ERROR:", e)
#         return jsonify({"error": f"Error interno: {e}"}), 500



# # =======================
# #     API - ESCANEO
# # =======================

# @app.route("/api/escanear", methods=["POST"])
# def api_escanear():
#     global inventario
#     inventario = {}

#     data = request.json
#     usuario = data.get("usuario", "")
#     contrasena = data.get("contrasena", "")
#     # tu frontend debe enviar "ip" (no "ip_inicio")
#     ip_inicio = data.get("ip", "")

#     visitados = set()
#     escanear_switch(ip_inicio, usuario, contrasena, visitados, inventario)

#     return jsonify(inventario)

# # =======================
# #   API - CAMBIAR VLAN
# # =======================

# @app.route("/api/cambiar_vlan", methods=["POST"])
# def api_cambiar_vlan():
#     """
#     Llama a cambiar_vlan_por_ip(inventario, usuario, contrasena)
#     pero esa función pide por input() la ip del host y la nueva VLAN.
#     Aquí interceptamos y le inyectamos ip_host y nueva_vlan desde el request.
#     """
#     data = request.json
#     usuario = data.get("usuario", "").strip()
#     contrasena = data.get("contrasena", "").strip()
#     ip_host = data.get("ip", "").strip()        # IP del host (valor que pide la función)
#     nueva_vlan = data.get("vlan", "").strip()   # nueva VLAN (valor que pide la función)

#     if not ip_host or not nueva_vlan:
#         return jsonify({"error": "Faltan 'ip' o 'vlan' en la petición"}), 400

#     # Ejecutar la función con inputs simulados: primero ip_buscar, luego nueva_vlan
#     stdout_text, func_result = run_func_with_inputs_capture(
#         cambiar_vlan_por_ip,
#         args=(inventario, usuario, contrasena),
#         input_values=[ip_host, nueva_vlan]
#     )

#     return jsonify({
#         "stdout": stdout_text,
#         "result": str(func_result)
#     })

# # =======================
# #     API - CREAR VLAN
# # =======================

# @app.route("/api/crear_vlan", methods=["POST"])
# def api_crear_vlan():
#     """
#     Llama a crear_vlan(usuario, contrasena)
#     pero esa función pide por input() ip, vlan, nombre.
#     Aquí se lo inyectamos desde el request.
#     """
#     data = request.json
#     usuario = data.get("usuario", "").strip()
#     contrasena = data.get("contrasena", "").strip()
#     ip_switch = data.get("ip", "").strip()
#     vlan = data.get("vlan", "").strip()
#     nombre = data.get("nombre", "").strip()

#     if not ip_switch or not vlan or not nombre:
#         return jsonify({"error": "Faltan 'ip', 'vlan' o 'nombre' en la petición"}), 400

#     stdout_text, func_result = run_func_with_inputs_capture(
#         crear_vlan,
#         args=(usuario, contrasena),
#         input_values=[ip_switch, vlan, nombre]
#     )

#     return jsonify({
#         "stdout": stdout_text,
#         "result": str(func_result)
#     })


# # =======================
# #     API - GENERAR INVENTARIO
# # =======================
# @app.route("/api/inventario/generar", methods=["POST"])
# def generar_inventario():
#     """
#     1. Ejecuta el playbook
#     2. Lee el JSON generado
#     3. Importa a MariaDB
#     4. Devuelve datos para el frontend
#     """

#     try:
#         # 1️⃣ Ejecutar playbook
#         result = subprocess.run(
#             ["ansible-playbook", "-i", "hosts", "playbook.yml"],
#             cwd=os.path.dirname(os.path.abspath(__file__)),
#             capture_output=True,
#             text=True
#         )

#         if result.returncode != 0:
#             return jsonify({
#                 "error": "Error ejecutando Ansible",
#                 "stderr": result.stderr
#             }), 500

#         # 2️⃣ Leer JSON generado
#         json_path = "/mnt/c/PROYECTO_WEB/dispositivos.json"
#         if not os.path.exists(json_path):
#             return jsonify({"error": "No se generó dispositivos.json"}), 500

#         with open(json_path, "r", encoding="utf-8") as f:
#             inventario = json.load(f)

#                # 3. Responder al frontend
#         return jsonify({
#             "status": "ok",
#             "devices": inventario
#         })

#         # # 3️⃣ Importar a MariaDB
#         # subprocess.run(
#         #     ["python3", "import_json_to_mariadb.py"],
#         #     cwd=os.path.dirname(os.path.abspath(__file__)),
#         #     check=True
#         # )

#         # # 4️⃣ Filtrar interfaces con IP
#         # salida = []
#         # for dispositivo in inventario:
#         #     interfaces_con_ip = {
#         #         k: v for k, v in dispositivo.get("interfaces", {}).items()
#         #         if v != "NO_IP"
#         #     }

#         #     salida.append({
#         #         "hostname": dispositivo.get("hostname"),
#         #         "mgmt_ip": dispositivo.get("mgmt_ip"),
#         #         "device_type": dispositivo.get("device_type"),
#         #         "modelo": dispositivo.get("modelo"),
#         #         "serial": dispositivo.get("serial"),
#         #         "version": dispositivo.get("version"),
#         #         "interfaces": interfaces_con_ip
#         #     })

#         # return jsonify(salida)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500




# # =======================
# #     API - REGISTRO
# # =======================
# @app.route("/api/register", methods=["POST"])
# def api_register():
#     data = request.json
#     username = data.get("username", "").strip()
#     password = data.get("password", "").strip()

#     if not username or not password:
#         return jsonify({"error": "Campos vacíos"}), 400

#     password_hash = generate_password_hash(password)

#     try:
#         db = get_db_connection()
#         with db.cursor() as cursor:
#             cursor.execute(
#                 "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
#                 (username, password_hash)
#             )
#         db.commit()
#         return jsonify({"ok": True})

#     except pymysql.err.IntegrityError:
#         return jsonify({"error": "Usuario ya existe"}), 409


# # =======================
# #     API - LOGIN
# # =======================

# @app.route("/api/login", methods=["POST"])
# def api_login():
#     data = request.json
#     username = data.get("username", "").strip()
#     password = data.get("password", "").strip()

#     db = get_db_connection()
#     with db.cursor() as cursor:
#         cursor.execute(
#             "SELECT * FROM users WHERE username = %s",
#             (username,)
#         )
#         user = cursor.fetchone()

#     if not user or not check_password_hash(user["password_hash"], password):
#         return jsonify({"error": "Credenciales inválidas"}), 401

#     session["user_id"] = user["id"]
#     session["username"] = user["username"]
#     session["role"] = user["role"]

#     return jsonify({"ok": True})



# @app.route("/api/test_db")
# def test_db():
#     try:
#         conn = get_db_connection()
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT DATABASE() AS db;")
#             result = cursor.fetchone()
#         conn.close()
#         return jsonify({
#             "status": "ok",
#             "database": result["db"]
#         })
#     except Exception as e:
#         return jsonify({
#             "status": "error",
#             "error": str(e)
#         }), 500




# # =======================
# #        MAIN
# # =======================

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)



from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import json
import os
import pymysql

from db import get_db_connection
from import_json_to_mariadb import import_json

# tus módulos existentes
from VLAN import escanear_switch, cambiar_vlan_por_ip, crear_vlan
from IP_MAC import buscar_dispositivo

import builtins, sys, io, traceback

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_cambialo")
app.config["DEBUG"] = True
app.config["PROPAGATE_EXCEPTIONS"] = True


inventario = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "dispositivos.json")
PLAYBOOK_PATH = os.path.join(BASE_DIR, "playbook.yml")
HOSTS_PATH = os.path.join(BASE_DIR, "hosts")


def run_func_with_inputs_capture(func, args=(), input_values=None):
    old_input = builtins.input
    old_stdout = sys.stdout
    buf = io.StringIO()
    inputs = list(input_values or [])

    def fake_input(prompt=""):
        print(prompt, end='', file=buf)
        return inputs.pop(0) if inputs else ""

    builtins.input = fake_input
    sys.stdout = buf

    result = None
    try:
        result = func(*args)
    except Exception:
        traceback.print_exc(file=buf)
    finally:
        builtins.input = old_input
        sys.stdout = old_stdout

    return buf.getvalue(), result


# =======================
#        PÁGINAS
# =======================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/buscar")
def buscar_html():
    return render_template("buscar.html")

@app.route("/vlan")
def vlan_html():
    return render_template("vlan.html")

@app.route("/inventario")
def inventario_html():
    return render_template("inventario.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, password_hash, role FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Usuario o contraseña incorrectos")

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if len(username) < 3 or len(password) < 4:
        return render_template("register.html", error="Usuario o contraseña muy cortos")

    pw_hash = generate_password_hash(password)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s,%s)",
                (username, pw_hash)
            )
    except Exception:
        conn.close()
        return render_template("register.html", error="Ese usuario ya existe")
    conn.close()

    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# =======================
#    API BUSCAR MAC/IP
# =======================

@app.route("/api/buscar", methods=["POST"])
def api_buscar():
    data = request.json
    try:
        resultado = buscar_dispositivo(
            data["ip_switch"],
            data["usuario"],
            data["contrasena"],
            data["objetivo"],
            data["modo"]
        )
        if not resultado:
            return jsonify({"error": "No encontrado"}), 404
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


# =======================
#       API VLAN
# =======================

@app.route("/api/escanear", methods=["POST"])
def api_escanear():
    global inventario
    inventario = {}

    data = request.json
    usuario = data.get("usuario", "")
    contrasena = data.get("contrasena", "")
    ip_inicio = data.get("ip", "")

    visitados = set()
    escanear_switch(ip_inicio, usuario, contrasena, visitados, inventario)
    return jsonify(inventario)

@app.route("/api/cambiar_vlan", methods=["POST"])
def api_cambiar_vlan():
    data = request.json
    usuario = data.get("usuario", "").strip()
    contrasena = data.get("contrasena", "").strip()
    ip_host = data.get("ip", "").strip()
    nueva_vlan = data.get("vlan", "").strip()

    stdout_text, func_result = run_func_with_inputs_capture(
        cambiar_vlan_por_ip,
        args=(inventario, usuario, contrasena),
        input_values=[ip_host, nueva_vlan]
    )
    return jsonify({"stdout": stdout_text, "result": str(func_result)})

@app.route("/api/crear_vlan", methods=["POST"])
def api_crear_vlan():
    data = request.json
    usuario = data.get("usuario", "").strip()
    contrasena = data.get("contrasena", "").strip()
    ip_switch = data.get("ip", "").strip()
    vlan = data.get("vlan", "").strip()
    nombre = data.get("nombre", "").strip()

    stdout_text, func_result = run_func_with_inputs_capture(
        crear_vlan,
        args=(usuario, contrasena),
        input_values=[ip_switch, vlan, nombre]
    )
    return jsonify({"stdout": stdout_text, "result": str(func_result)})


# =======================
#  INVENTARIO (ANSIBLE)
# =======================

@app.route("/api/inventario/generar", methods=["POST"])
def api_generar_inventario():
    """
    1) ejecuta ansible-playbook
    2) lee dispositivos.json
    3) inserta en MariaDB
    4) responde con data para la tabla
    """
    try:
        cmd = ["ansible-playbook", "-i", HOSTS_PATH, PLAYBOOK_PATH]
        run = subprocess.run(cmd, capture_output=True, text=True)

        if run.returncode != 0:
            return jsonify({
                "ok": False,
                "error": "Falló ansible-playbook",
                "stdout": run.stdout,
                "stderr": run.stderr
            }), 500

        if not os.path.exists(JSON_PATH):
            return jsonify({"ok": False, "error": "No se generó dispositivos.json"}), 500

        # insertar a DB
        import_json(JSON_PATH)

        # leer para devolver al frontend
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # devolver SOLO interfaces con IP para mostrar bonito
        cleaned = []
        for d in data:
            interfaces = d.get("interfaces", {}) or {}
            only_ip = {k: v for k, v in interfaces.items() if v != "NO_IP"}
            cleaned.append({
                "hostname": d.get("hostname"),
                "modelo": d.get("modelo"),
                "serial": d.get("serial"),
                "version": d.get("version"),
                "interfaces_ip": only_ip,
                "error": d.get("error")
            })

        return jsonify({"ok": True, "data": cleaned})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/inventario/listar", methods=["GET"])
def api_listar_inventario_db():
    """
    Saca datos ya guardados en DB (para que el HTML no dependa del JSON)
    """
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, hostname, mgmt_ip, model, serial, ios_version FROM devices ORDER BY hostname")
        devices = cur.fetchall()

        for d in devices:
            cur.execute("""
                SELECT interface_name, ip_address
                FROM device_interfaces
                WHERE device_id=%s
                ORDER BY interface_name
            """, (d["id"],))
            d["interfaces_ip"] = cur.fetchall()

    conn.close()
    return jsonify({"ok": True, "data": devices})


##CONSULTAS
# @app.route("/api/inventario/devices")
# def get_devices():
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("""
#         SELECT id, hostname, mgmt_ip, device_type, model, serial, ios_version, last_seen
#         FROM devices
#         ORDER BY hostname
#     """)

#     data = cur.fetchall()
#     conn.close()
#     return jsonify(data)


# ##INTERFAZ CON IP
# @app.route("/api/inventario/interfaces")
# def get_interfaces():
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("""
#         SELECT d.hostname, d.mgmt_ip, i.interface_name, i.ip_address
#         FROM device_interfaces i
#         JOIN devices d ON d.id = i.device_id
#         ORDER BY d.hostname, i.interface_name
#     """)

#     data = cur.fetchall()
#     conn.close()
#     return jsonify(data)

# #### BUSCAR POR IP

# @app.route("/api/inventario/buscar/ip/<ip>")
# def buscar_por_ip(ip):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("""
#         SELECT d.hostname, d.model, d.serial, i.interface_name, i.ip_address
#         FROM device_interfaces i
#         JOIN devices d ON d.id = i.device_id
#         WHERE i.ip_address = %s
#     """, (ip,))

#     data = cur.fetchall()
#     conn.close()
#     return jsonify(data)

# ##por hostame
# @app.route("/api/inventario/buscar/hostname/<hostname>")
# def buscar_por_hostname(hostname):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("""
#         SELECT d.hostname, d.mgmt_ip, d.model, d.serial, d.ios_version,
#                i.interface_name, i.ip_address
#         FROM devices d
#         LEFT JOIN device_interfaces i ON d.id = i.device_id
#         WHERE d.hostname LIKE %s
#     """, (f"%{hostname}%",))

#     data = cur.fetchall()
#     conn.close()
#     return jsonify(data)

@app.route("/api/inventario/devices")
def api_inventario_devices():
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)



    cur.execute("""
        SELECT d.id, d.hostname, d.model, d.serial, d.ios_version, e.error_text
        FROM devices d
        LEFT JOIN device_errors e ON d.mgmt_ip = e.mgmt_ip
        ORDER BY d.hostname
    """)
    devices = cur.fetchall()

    resultado = []

    for d in devices:
        cur.execute("""
            SELECT interface_name, ip_address
            FROM device_interfaces
            WHERE device_id = %s
        """, (d["id"],))

        interfaces = {
            r["interface_name"]: r["ip_address"]
            for r in cur.fetchall()
        }

        resultado.append({
            "hostname": d["hostname"],
            "modelo": d["model"],
            "serial": d["serial"],
            "version": d["ios_version"],
            "interfaces_ip": interfaces,
            "error": d["error_text"]
        })

    conn.close()
    return jsonify(resultado)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
