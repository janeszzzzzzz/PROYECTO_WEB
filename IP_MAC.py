#IP_MAC.py

import re
import io
import textfsm
from netmiko import ConnectHandler
from getpass import getpass
#================== #
# Plantillas TextFSM            #
# ============================= #

TEMPLATE_ARP = r"""Value IP (\d+\.\d+\.\d+\.\d+)
Value MAC ([0-9a-fA-F.]+)
Value INTERFACE (\S+)

Start
  ^Internet\s+${IP}\s+\S+\s+${MAC}\s+ARPA\s+${INTERFACE} -> Record
"""

TEMPLATE_MAC = r"""Value VLAN (\d+)
Value MAC ([0-9a-fA-F.]+)
Value TYPE (\S+)
Value PORT (\S+)

Start
  ^\s*${VLAN}\s+${MAC}\s+${TYPE}\s+${PORT} -> Record
"""


# ============================= #
# Funciones auxiliares          #
# ============================= #

def compilar(plantilla):
    return textfsm.TextFSM(io.StringIO(plantilla))


def buscar_mac_por_ip(salida_arp, ip):
    fsm = compilar(TEMPLATE_ARP)
    for ip_fsm, mac_fsm, intf in fsm.ParseText(salida_arp):
        if ip_fsm == ip:
            return mac_fsm
    return None


def buscar_puerto_por_mac(salida_mac, mac):
    fsm = compilar(TEMPLATE_MAC)
    for vlan, mac_fsm, tipo, puerto in fsm.ParseText(salida_mac):
        if mac_fsm.lower() == mac.lower():
            return puerto
    return None


def easter_egg():
    print("""
UN QUE UN QUE!!
  |\\---/|
  | o_o |
   \\_^_/
MIAU NYA~
""")


# ============================= #
# Función principal de búsqueda #
# ============================= #

def buscar_dispositivo(ip_switch, usuario, contrasena, objetivo, modo, visitados=None, ruta=None):

    if visitados is None:
        visitados = set()
    if ruta is None:
        ruta = []

    if ip_switch in visitados:
        return None

    visitados.add(ip_switch)

    print(f"\n🦂 Conectando a {ip_switch}…")
    dispositivo = {
        "device_type": "cisco_ios",
        "host": ip_switch,
        "username": usuario,
        "password": contrasena,
    }

    try:
        conexion = ConnectHandler(**dispositivo)
    except Exception as e:
        print(f"🦂 Error conectando: {e}")
        return None

    hostname = conexion.send_command("show run | i hostname").replace("hostname", "").strip()
    salida_arp = conexion.send_command("show ip arp")
    salida_mac = conexion.send_command("show mac address-table")

    # ------------------------------- #
    # MODO: buscar IP → obtener MAC   #
    # ------------------------------- #
    if modo == "ip":
        mac = buscar_mac_por_ip(salida_arp, objetivo)
        if not mac:
            conexion.disconnect()
            return None
    else:
        # MODO MAC: ya traemos la MAC
        mac = objetivo

    puerto = buscar_puerto_por_mac(salida_mac, mac)
    if not puerto:
        conexion.disconnect()
        return None

    paso = {"switch": hostname, "ip": ip_switch, "puerto": puerto, "mac": mac}
    ruta.append(paso)

    # Revisar si hay vecino CDP en el puerto
    salida_cdp = conexion.send_command(f"show cdp neighbors {puerto} detail")

    if "IP address:" in salida_cdp:
        for line in salida_cdp.splitlines():
            if "IP address:" in line:
                vecino_ip = line.split(":")[1].strip()
                print(f"🦂 MAC detectada en {puerto}, conectada a switch vecino {vecino_ip}")
                conexion.disconnect()
                return buscar_dispositivo(vecino_ip, usuario, contrasena, objetivo, modo, visitados, ruta)

    # No hay vecino → host final
    print(f"\n🦂 Host final encontrado en {hostname} ({ip_switch})")
    print(f"🦂 Puerto físico: {puerto}")
    print(f"🦂 MAC Address: {mac}")
    conexion.disconnect()

    # Resumen bonito
    print("\n📜 === RESUMEN DE BÚSQUEDA ===")
    for i, paso in enumerate(ruta):
        sw = paso["switch"]
        ip = paso["ip"]
        p = paso["puerto"]
        m = paso["mac"]
        if i < len(ruta) - 1:
            print(f"🦂 {sw} ({ip}) → MAC vista por {p}, sigue a otro switch")
        else:
            print(f"🦂 {sw} ({ip}) → HOST FINAL encontrado – Puerto {p}, MAC {m}")

    print("\n🦂 ¡Búsqueda completada con éxito!")
    easter_egg()

    return {"switch": hostname, "ip": ip_switch, "puerto": puerto, "mac": mac}




# Menú principal con MATCH      #
# ============================= #

def menu():
    print("""
=== 🦂 Localizador Durango Edition 🦂 ===

1) Buscar por IP
2) Buscar por MAC
3) Salir
""")
    return input("Selecciona una opción: ").strip()


# ============================= #
# Main program                  #
# ============================= #

def main():
    usuario = input("Usuario SSH (default admin): ").strip() or "admin"
    contrasena = getpass("Contraseña SSH: ")

    while True:
        opcion = menu()

        match opcion:
            case "1":
                print("\n--- BÚSQUEDA POR IP ---")
                ip_switch = input("IP de un switch inicial: ").strip()
                ip_objetivo = input("IP del host objetivo: ").strip()

                buscar_dispositivo(ip_switch, usuario, contrasena, ip_objetivo, "ip")

            case "2":
                print("\n--- BÚSQUEDA POR MAC ---")
                ip_switch = input("IP de un switch inicial: ").strip()
                mac_objetivo = input("MAC del host objetivo (aaaa.bbbb.cccc): ").strip()

                buscar_dispositivo(ip_switch, usuario, contrasena, mac_objetivo, "mac")

            case "3":
                print("🦂 Saliendo del Localizador Durango Edition…")
                break

            case _:
                print("❌ Opción inválida, intenta otra vez mija…")


if __name__ == "__main__":
    main()
