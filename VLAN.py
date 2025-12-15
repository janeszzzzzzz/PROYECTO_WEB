#VLAN.py



import io
import textfsm
from netmiko import ConnectHandler
from getpass import getpass

# ========================== #
#     PLANTILLAS TEXTFSM     #
# ========================== #
TEMPLATE_ARP = r"""Value IP (\d+\.\d+\.\d+\.\d+)
Value MAC ([0-9a-fA-F.]+)

Start
  ^Internet\s+${IP}\s+\S+\s+${MAC}\s+ARPA -> Record
"""

TEMPLATE_MAC = r"""Value VLAN (\d+)
Value MAC ([0-9a-fA-F.]+)
Value TYPE (\S+)
Value PORT (\S+)

Start
  ^\s*${VLAN}\s+${MAC}\s+${TYPE}\s+${PORT} -> Record
"""


def compilar(t):
    limpio = t.replace("\t","").strip("\n")
    return textfsm.TextFSM(io.StringIO(limpio))


# ===================================================== #
#   FUNCIONES DE AYUDA: ARP, MAC, CDP, SSH, VALIDACIÓN   #
# ===================================================== #

def obtener_cdp_por_puerto(conexion, puerto):
    salida = conexion.send_command(f"show cdp neighbors {puerto} detail")
    if "IP address:" not in salida:
        return None
    for linea in salida.splitlines():
        if "IP address:" in linea:
            return linea.split(":")[1].strip()
    return None

def obtener_ip_por_mac(salida_arp, mac):
    fsm = compilar(TEMPLATE_ARP)
    for ip, m in fsm.ParseText(salida_arp):
        if m.lower() == mac.lower():
            return ip
    return None

def obtener_mac_table(salida_mac):
    fsm = compilar(TEMPLATE_MAC)
    return list(fsm.ParseText(salida_mac))


# ===================================================== #
#   ESCANEO AUTOMÁTICO DE LA RED (INVENTARIO REAL)      #
# ===================================================== #
def escanear_switch(ip, usuario, contrasena, visitados, inventario):
    if ip in visitados:
        return

    print(f"\n🔗 Conectando a {ip} ...")
    visitados.add(ip)

    dispositivo = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": usuario,
        "password": contrasena,
    }

    try:
        conn = ConnectHandler(**dispositivo)
    except Exception as e:
        print(f"❌ Error conectando a {ip}: {e}")
        return

    hostname = conn.send_command("show run | i hostname").replace("hostname", "").strip()
    salida_arp = conn.send_command("show ip arp")
    salida_mac = conn.send_command("show mac address-table")

    # Aseguramos que la clave exista y sea una lista
    if hostname not in inventario:
        inventario[hostname] = []

    tabla_mac = obtener_mac_table(salida_mac)

    for vlan, mac, tipo, puerto in tabla_mac:

        # 1) Si el puerto tiene vecino (CDP) -> no es host, seguir por el vecino
        vecino = obtener_cdp_por_puerto(conn, puerto)
        if vecino:
            escanear_switch(vecino, usuario, contrasena, visitados, inventario)
            continue

        # 2) Es host real
        ip_host = obtener_ip_por_mac(salida_arp, mac) or "DESCONOCIDA"

        # Guardamos todas las claves posibles para evitar KeyError en otras partes del script
        inventario[hostname].append({
            "switch": ip,          # IP del switch donde está el host (útil para conectar)
            "ip_sw": ip,           # alias por compatibilidad
            "host": ip,            # alias por compatibilidad
            "hostname": hostname,  # nombre del switch
            "puerto": puerto,      # nombre que usaban funciones antiguas
            "interface": puerto,   # nombre que usan otras funciones
            "mac": mac,
            "ip": ip_host,
            "vlan": vlan
        })

    conn.disconnect()

# ===================================================== #
#     MOSTRAR INVENTARIO BONITO (SIN ERRORES)           #
# ===================================================== #

def mostrar_inventario(inventario):
    print("\n================= INVENTARIO =================\n")

    for sw, hosts in inventario.items():
        print(f"🟦 Switch {sw}")
        print("-------------------------------------------")

        if not hosts:
            print("Sin hosts.\n")
            continue

        for h in hosts:
            print(f"{h['puerto']:10} | {h['ip']:15} | {h['mac']:14} | VLAN {h['vlan']}")
        print()


# ===================================================== #
#           CAMBIO DE VLAN POR IP (INTELIGENTE)         #
# ===================================================== #
def cambiar_vlan_por_ip(inventario, usuario, contrasena):
    ip_buscar = input("Ingresa la IP del host: ").strip()
    nueva_vlan = input("Ingresa la nueva VLAN: ").strip()

    encontrado = None
    origen_sw_key = None

    # inventario puede ser {hostname: [hosts...]} o {hostname: {"puertos": [...]}}
    for sw_key, valor in inventario.items():
        host_list = valor if isinstance(valor, list) else valor.get("puertos", [])
        for h in host_list:
            if h.get("ip") == ip_buscar:
                encontrado = h
                origen_sw_key = sw_key
                break
        if encontrado:
            break

    if not encontrado:
        print("\n❌ No se encontró esa IP en el inventario.\n")
        return

    # obtener interfaz (acepta 'puerto' o 'interface')
    interfaz = encontrado.get("puerto") or encontrado.get("interface")
    if not interfaz:
        print("\n❌ El registro del inventario no contiene la interfaz (puerto/interface).\n")
        print("Registro:", encontrado)
        return

    # obtener IP del switch: acepta muchas variantes por compatibilidad
    ip_switch = encontrado.get("ip_sw") or encontrado.get("switch") or encontrado.get("host") or encontrado.get("switch_ip") or origen_sw_key

    if not ip_switch:
        print("\n❌ No se pudo determinar la IP del switch para ese host.")
        print("Registro:", encontrado)
        return

    print(f"\n🔧 Host encontrado en {origen_sw_key} puerto {interfaz} (conectar a {ip_switch})")

    dispositivo = {
        "device_type": "cisco_ios",
        "host": ip_switch,
        "username": usuario,
        "password": contrasena
    }

    try:
        conn = ConnectHandler(**dispositivo)

        comandos = [
            f"interface {interfaz}",
            f"switchport mode access",
            f"switchport access vlan {nueva_vlan}",
            "exit"
        ]

        # versión compatible: SIN expect_string
        salida = conn.send_config_set(comandos)
        print(salida)

        # intentar guardar la config (algunos dispositivos no soportan save_config())
        try:
            conn.save_config()
        except Exception:
            # fallback: usar write memory si save_config no existe o falla
            try:
                conn.send_command("write memory")
            except Exception:
                pass

        conn.disconnect()
        print(f"\n✅ VLAN cambiada correctamente a {nueva_vlan} en {ip_switch}:{interfaz}\n")

    except Exception as e:
        print(f"\n❌ Error configurando VLAN: {e}\n")

# ===================================================== #
#           CAMBIO DE VLAN POR IP (INTELIGENTE)         #
# ===================================================== #
def crear_vlan(usuario, contrasena):
    ip = input("IP del switch donde crear la VLAN: ").strip()
    vlan = input("Número de VLAN: ").strip()
    nombre = input("Nombre de la VLAN: ").strip()

    dispositivo = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": usuario,
        "password": contrasena,
    }

    try:
        conn = ConnectHandler(**dispositivo)

        # Validar si existe
        existente = conn.send_command(f"show vlan id {vlan}")
        if f"VLAN Name" in existente and str(vlan) in existente:
            print(f"\n⚠️ La VLAN {vlan} ya existe en {ip}.\n")
            conn.disconnect()
            return

        comandos = [
            f"vlan {vlan}",
            f"name {nombre}",
            "exit"
        ]

        print("\n⚙️ Creando VLAN...\n")

        salida = conn.send_config_set(comandos)
        print(salida)

        conn.save_config()

        print(f"\n✅ VLAN {vlan} ({nombre}) creada exitosamente en {ip}.\n")

        conn.disconnect()

    except Exception as e:
        print(f"❌ Error creando la VLAN: {e}")




# ===================================================== #
#                     MENÚ PRINCIPAL                    #
# ===================================================== #
def menu():
    usuario = input("Usuario: ")
    contrasena = input("Contraseña: ")

    inventario = {}

    while True:
        print("""
================ MENÚ =================
1) Escanear red y generar inventario
2) Ver inventario
3) Cambiar VLAN de un host
4) Crear VLAN
5) Salir
""")

        opcion = input("Selecciona una opción: ")

        if opcion == "1":
            inventario.clear()
            visitados = set()
            ip_inicio = input("IP del switch inicial: ").strip()
            escanear_switch(ip_inicio, usuario, contrasena, visitados, inventario)
            print("\n✅ Escaneo completado.\n")

        elif opcion == "2":
            print("\n===== INVENTARIO =====")
            for sw, hosts in inventario.items():
                print(f"\nSwitch {sw}:")
                for h in hosts:
                    print(h)

        elif opcion == "3":
            cambiar_vlan_por_ip(inventario, usuario, contrasena)

        elif opcion == "4":
            crear_vlan(usuario, contrasena)

        elif opcion == "5":
            print("Saliendo...")
            break

        else:
            print("Opción inválida.")



# ============================= #
#            MAIN               #
# ============================= #

if __name__ == "__main__":
    menu()
