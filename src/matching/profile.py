# src/matching/profile.py
import re

LOCALIDADES_LOCALES = ["albacete", "hellin", "hellín", "chinchilla", "la gineta"]

TECH_KEYWORDS = {
    "sistemas_redes": [
        "linux", "debian", "ubuntu", "redhat", "centos", "rocky", "windows server",
        "active directory", "ldap", "redes", "lan", "wan", "routing", "switching",
        "vlan", "firewall", "vpn", "tcp/ip", "dns", "dhcp", "cisco", "mikrotik",
        "soporte tecnico", "soporte técnico", "soporte informatico", "soporte informático",
        "helpdesk", "soporte l2", "soporte l3", "soporte a usuarios", "soporte it",
        "it support", "sysadmin", "administrador de sistemas", "asir", "virtualizacion",
        "vmware", "vsphere", "proxmox", "hyper-v", "microinformatica", "microinformática"
    ],
    "avionica_electronica": [
        "avionica", "aviónica", "aeronautica", "aeronáutica", "simulador", "simuladores",
        "electronica", "electrónica", "hardware", "calibracion", "calibración",
        "banco de pruebas", "mantenimiento electronico", "mantenimiento electrónico",
        "instrumentacion", "instrumentación", "soldadura", "pcb", "osciloscopio",
        "multimetro", "multímetro", "c-101", "pilatus", "defensa", "militar"
    ],
    "desarrollo_automatizacion": [
        "python", "bash", "shell script", "powershell", "scripting", "automatizacion",
        "automatización", "sql", "sqlite", "javascript", "typescript", "react",
        "api rest", "git", "scraping", "ci/cd", "ansible"
    ],
    "logistica_calidad": [
        "almacen", "almacén", "logistica", "logística", "repuestos", "stock",
        "inventario", "compras tecnicas", "compras técnicas", "control de calidad",
        "gestion de calidad", "calidad iso", "iso 9001", "normativa aeronautica",
        "normativa militar", "gestion de material", "gestión de material"
    ],
    "administracion_contabilidad": [
        "administrativo", "administrativa", "administracion", "administración",
        "contable", "contabilidad", "facturacion", "facturación", "asientos contables",
        "conciliacion bancaria", "conciliación bancaria", "gestion de albaranes",
        "gestion documental", "gestión documental", "archivo", "erp", "sap",
        "excel", "backoffice", "back office", "auxiliar administrativo",
        "auxiliar administrativa", "gestion de cobros", "tramitacion", "tramitación"
    ],
    "ciberseguridad": [
        "ciberseguridad", "seguridad informatica", "seguridad de la informacion",
        "incibe", "soc", "siem", "criptografia", "hardening", "iso 27001", "ens"
    ]
}

EXCLUDED_PROFESSIONS = [
    r'\bortodonc\w*', r'\bdent\w*', r'\bodont[oó]log\w*', r'\bm[eé]dic\w*', r'\benferm\w*',
    r'\bveterinar\w*', r'\bfarmac[eé]ut\w*', r'\bfisioterap\w*', r'\bpsic[oó]log\w*',
    r'\babogad\w*', r'\bletrad\w*', r'\bjur[ií]dic\w*',
    r'\bviajes?\b', r'\bhotel\w*', r'\bhosteler\w*', r'\bcamarer\w*', r'\bcocin\w*',
    r'\bcrupier\b', r'\bcasino\b', r'\binmobiliar\w*',
    r'\bobra civil\b', r'\bjefe de obra\b', r'\bjefa de obra\b',
    r'\bcomercial\b', r'\bventas?\b', r'\baccount manager\b', r'\bvendedor\w*', r'\bteleoperador\w*'
]

EXCLUDED_DEGREE_TITLES = [
    r'\bingeniero\b', r'\bingeniera\b', r'\bingenier[íi]a\b',
    r'\barquitecto\b', r'\barquitecta\b',
    r'\bcivil\b', r'\bclimat\w*', r'\bambiental\b', r'\bqu[íi]mic\w*',
    r'\bagr[oó]nom\w*', r'\bagr[ií]col\w*', r'\bge[oó]log\w*'
]

FP_ACCEPTED_KEYWORDS = [
    'grado superior', 'ciclo formativo', 'fp ii', 'fp 2', 'fp',
    'formación profesional', 'formacion profesional', 'técnico superior', 'tecnico superior',
    'cfgs', 'asir', 'dam', 'daw', 'o experiencia equivalente'
]

MANDATORY_DEGREE_KEYWORDS = [
    r'titulaci[oó]n universitaria\b',
    r'grado universitario\b',
    r'carrera universitaria\b',
    r'licenciatura\b',
    r'estudios universitarios imprescindibles\b',
    r'm[aá]ster universitario\b',
    r'imprescindible grado\b',
    r'imprescindible ingenier[íi]a\b',
    r'imprescindible carrera\b'
]

TARGET_TITLE_KEYWORDS = [
    # Sistemas / Redes / Informática
    r'sistemas?', r'redes?', r'sysadmin', r'linux', r'windows', r'soporte', r'helpdesk',
    r'inform[aá]tic\w*', r'asir', r'ciberseguridad', r'seguridad', r'devops', r'cloud',
    r'virtualizaci[oó]n', r'microinform[aá]tic\w*', r'operador', r't[eé]cnic\w*',
    # Aviónica / Electrónica / Hardware / Simulación
    r'avi[oó]nic\w*', r'electr[oó]nic\w*', r'hardware', r'simulador\w*', r'calibraci[oó]n',
    r'instrumentaci[oó]n', r'aeron[aá]utic\w*', r'mantenimiento', r'soldadura', r'defensa',
    # Automatización / Scripting
    r'python', r'automatizaci[oó]n', r'scripting', r'programador\w*', r'desarrollador\w*',
    # Logística técnica / Almacén / Calidad
    r'almac[eé]n', r'log[ií]stic\w*', r'repuestos?', r'stock', r'inventario', r'material',
    # Administración / Gestión documental
    r'administrativ\w*', r'facturaci[oó]n', r'gesti[oó]n documental', r'backoffice', r'archivo', r'tramitaci[oó]n'
]

VERIFICAR_KEYWORDS = [
    ("easa", "Verificar requisito de licencia/normativa civil aeronáutica EASA (Parte 66 / Parte 145) frente a experiencia militar"),
    ("ccna", "Verificar exigencia de certificación oficial Cisco CCNA"),
    ("ccnp", "Verificar nivel avanzado Cisco CCNP"),
    ("aws", "Verificar certificación específica AWS Cloud"),
    ("azure", "Verificar certificación específica Microsoft Azure"),
    ("itil", "Verificar certificación en marco ITIL"),
    ("ingles", "Verificar nivel de inglés requerido (B2/C1) para operativa diaria"),
    ("b2", "Verificar nivel de inglés formal B2"),
    ("c1", "Verificar nivel de inglés formal C1")
]
