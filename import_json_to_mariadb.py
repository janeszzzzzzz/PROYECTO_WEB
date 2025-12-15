# import json
# import pymysql
# from datetime import datetime

# JSON_PATH = "dispositivos.json"  # pon la ruta real (ej: /mnt/c/PROYECTO_WEB/dispositivos.json)

# DB = {
#     "host": "127.0.0.1",
#     "user": "root",
#     "password": "TU_PASSWORD",
#     "database": "proyecto_web",
#     "cursorclass": pymysql.cursors.DictCursor,
#     "autocommit": True
# }

# def detect_type(hostname: str) -> str:
#     h = (hostname or "").upper()
#     if h.startswith("SW"):
#         return "switch"
#     if h.startswith("R") or "ROUT" in h:
#         return "router"
#     return "unknown"

# def main():
#     with open(JSON_PATH, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     conn = pymysql.connect(**DB)

#     with conn.cursor() as cur:
#         for item in data:
#             hostname = item.get("hostname", "UNKNOWN")
#             serial = item.get("serial", "UNKNOWN")
#             model = item.get("modelo", "UNKNOWN")
#             ios_version = item.get("version", "UNKNOWN")
#             interfaces = item.get("interfaces", {}) or {}
#             err = item.get("error")

#             # OJO: tu JSON NO trae mgmt_ip. Ideal: que el playbook lo agregue.
#             # Mientras tanto, si hostname es una IP (como los que fallan), usamos eso.
#             # Si hostname NO es IP (SW1), NO tenemos mgmt_ip real -> queda como hostname (mala práctica).
#             mgmt_ip = item.get("mgmt_ip") or hostname

#             device_type = detect_type(hostname)

#             # Si hubo error, lo registramos y seguimos (igual puede insertarse device si quieres).
#             if err:
#                 cur.execute(
#                     "INSERT INTO device_errors (mgmt_ip, hostname, error_text) VALUES (%s,%s,%s)",
#                     (mgmt_ip, hostname, err)
#                 )
#                 # si no quieres crear device cuando hay error, descomenta:
#                 # continue

#             # UPSERT del dispositivo por mgmt_ip
#             cur.execute("""
#                 INSERT INTO devices (hostname, mgmt_ip, device_type, model, serial, ios_version, last_seen)
#                 VALUES (%s,%s,%s,%s,%s,%s,NOW())
#                 ON DUPLICATE KEY UPDATE
#                   hostname=VALUES(hostname),
#                   device_type=VALUES(device_type),
#                   model=VALUES(model),
#                   serial=VALUES(serial),
#                   ios_version=VALUES(ios_version),
#                   last_seen=NOW()
#             """, (hostname, mgmt_ip, device_type, model, serial, ios_version))

#             # Obtener device_id
#             cur.execute("SELECT id FROM devices WHERE mgmt_ip=%s", (mgmt_ip,))
#             device_id = cur.fetchone()["id"]

#             # Limpiar interfaces anteriores del device (así siempre queda sincronizado)
#             cur.execute("DELETE FROM device_interfaces WHERE device_id=%s", (device_id,))

#             # Insertar solo interfaces con IP real
#             for if_name, ip in interfaces.items():
#                 if not ip or ip == "NO_IP":
#                     continue

#                 # Si ip viene como "192.168.1.1" (sin prefijo), prefix_len queda NULL.
#                 cur.execute("""
#                     INSERT INTO device_interfaces (device_id, interface_name, ip_address, prefix_len)
#                     VALUES (%s,%s,%s,%s)
#                 """, (device_id, if_name, ip, None))

#     conn.close()
#     print("✅ Importación completada.")

# if __name__ == "__main__":
#     main()


import json
from db import get_db_connection

def guess_device_type(hostname: str) -> str:
    h = (hostname or "").upper()
    if h.startswith("SW"):
        return "switch"
    if h.startswith("R") or h.startswith("RTR") or h.startswith("ROUTER"):
        return "router"
    return "unknown"

def import_json(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_db_connection()
    with conn.cursor() as cur:
        for item in data:
            hostname = item.get("hostname", "UNKNOWN")
            model = item.get("modelo", "UNKNOWN")
            serial = item.get("serial", "UNKNOWN")
            ios_version = item.get("version", "UNKNOWN")
            interfaces = item.get("interfaces", {}) or {}
            error = item.get("error")

            # mgmt_ip: si hostname viene como IP por fallback, úsalo
            mgmt_ip = hostname if hostname.count(".") == 3 else None

            # si en el inventario tienes alguna SVI con IP, usa eso como mgmt_ip preferido
            # (ej Vlan10 = 192.168.1.11)
            for ifname, ip in interfaces.items():
                if ip and ip != "NO_IP" and ifname.lower().startswith("vlan"):
                    mgmt_ip = ip
                    break

            if not mgmt_ip:
                # fallback: UNKNOWN
                mgmt_ip = "0.0.0.0"

            device_type = guess_device_type(hostname)

            # Si hubo error, guárdalo y sigue
            if error:
                cur.execute(
                    "INSERT INTO device_errors (mgmt_ip, hostname, error_text) VALUES (%s,%s,%s)",
                    (mgmt_ip, hostname, str(error))
                )

            # UPSERT device por mgmt_ip (así no duplicas)
            cur.execute("""
                INSERT INTO devices (hostname, mgmt_ip, device_type, model, serial, ios_version)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    hostname=VALUES(hostname),
                    device_type=VALUES(device_type),
                    model=VALUES(model),
                    serial=VALUES(serial),
                    ios_version=VALUES(ios_version),
                    last_seen=CURRENT_TIMESTAMP
            """, (hostname, mgmt_ip, device_type, model, serial, ios_version))

            # sacar id del device
            cur.execute("SELECT id FROM devices WHERE mgmt_ip=%s", (mgmt_ip,))
            device_id = cur.fetchone()["id"]

            # insertar SOLO interfaces con IP (ip != NO_IP)
            for ifname, ip in interfaces.items():
                if not ip or ip == "NO_IP":
                    continue
                cur.execute("""
                    INSERT INTO device_interfaces (device_id, interface_name, ip_address)
                    VALUES (%s,%s,%s)
                    ON DUPLICATE KEY UPDATE updated_at=CURRENT_TIMESTAMP
                """, (device_id, ifname, ip))

    conn.close()
    return True
