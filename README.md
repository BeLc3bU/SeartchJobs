# 🤖 Agente Autónomo de Búsqueda Diaria de Empleo Personalizado

Sistema autónomo, de coste cero y alta precisión, diseñado para rastrear, filtrar, clasificar y notificar diariamente oportunidades de empleo adaptadas al perfil técnico, operativo y administrativo multidisciplinar de **Pedro Úbeda Sánchez**.

---

## 🎯 Perfil Profesional de Referencia

* **Candidato:** Pedro Úbeda Sánchez ([pedroubedasanchez.es](https://pedroubedasanchez.es)).
* **Trayectoria:** Cabo Primero del Ejército del Aire y del Espacio (22 años de servicio continuo en sistemas críticos).
* **Formación y Certificaciones:**
  - Grado Superior ASIR (Administración de Sistemas Informáticos en Red).
  - Técnico Especialista en Informática de Gestión.
  - Ciberseguridad (INCIBE).
  - Curso Especializado NATO HPS CRYPTO.
  - Condecoraciones: Cruz del Mérito Aeronáutico y Cruz a la Constancia.
* **Competencias Núcleo:**
  - **Aviónica y Hardware:** Diagnóstico, mantenimiento, calibración y banco de pruebas de aviónica y simuladores de vuelo (C-101 y sistemas Pilatus).
  - **Sistemas & Redes:** Administración avanzada de Linux y Windows Server, Active Directory, redes LAN/WAN, routing/switching, firewalls, virtualización (VMware/vSphere/Proxmox) y soporte técnico L2/L3.
  - **Desarrollo y Automatización:** Python, JavaScript, TypeScript, React, SQL/SQLite, Bash scripting, control de versiones Git.
  - **Logística y Operativa:** Gestión de almacén técnico y repuestos aeronáuticos/militares, control de calidad, redacción de documentación técnica y rigurosa disciplina procedimental.
  - **Apertura Multisectorial:** Telecomunicaciones, defensa civil, soporte postventa tecnológico, infraestructuras e industria.

---

## 🧭 Filtros Estrictos de Ubicación y Horario

El motor descarta automáticamente cualquier oferta que no cumpla una de estas dos condiciones:
1. **Modalidad 1 (Prioridad Máxima):** **Teletrabajo / Remoto 100%** desde España (con horario flexible o compatible).
2. **Modalidad 2 (Presencial o Híbrido local):** Exclusivamente en **Hellín** o **Albacete capital**, y **OBLIGATORIAMENTE en turno de tarde** o compatible (descartando turnos de mañana o jornada partida presencial clásica).
3. **Nacional:** Solo si contempla teletrabajo o esquemas de desplazamiento flexibles compatibles.

---

## 📊 Clasificación de Ofertas (Sin porcentajes arbitrarios)

* **🟢 Clase A (Encaje directo):** Requisitos técnicos y operativos alineados con el perfil de Pedro + cumplimiento estricto de ubicación/horario.
* **🟡 Clase B (Encaje potencial):** Alta compatibilidad en la base técnica o de gestión, pero con algún requisito civil específico a validar (licencia EASA civil frente a militar, certificados específicos de fabricante o confirmación de turno en Albacete/Hellín).
* **⚪ Clase C (Encaje limitado):** Tecnologías excluyentes, desajuste funcional o incumplimiento geográfico/horario. **Se almacenan en SQLite pero se omiten del informe diario** para evitar saturación de notificaciones.

---

## 🏗️ Arquitectura y Estructura del Repositorio

```text
AlertasEmpleo/
├── .github/
│   └── workflows/
│       └── empleo.yml        # Orquestación diaria (06:00 UTC) en GitHub Actions
├── data/
│   ├── .gitkeep
│   └── empleo.db             # Base de datos SQLite persistida vía git push
├── src/
│   ├── job_agent.py          # Pipeline principal: Ingesta, Filtrado, Persistencia y Telegram
│   └── gestionar.py          # Herramienta CLI para consultar y actualizar estados
├── requirements.txt          # Dependencias esenciales (requests, feedparser, beautifulsoup4)
└── README.md                 # Manual de configuración y uso
```

---

## 🚀 Puesta en Marcha Rápida (Paso a Paso)

### Paso 1: Configurar el Bot de Telegram

1. Abre Telegram y busca a **[@BotFather](https://t.me/BotFather)**.
2. Envía el comando `/newbot`, asigna un nombre (ej. `Pedro Job Hunter Bot`) y un username único (ej. `PedroJobAgentBot`).
3. BotFather te proporcionará un **Token HTTP API** (ej. `7123456789:AAH...`). Guárdalo como `TELEGRAM_TOKEN`.
4. Pulsa en el enlace de tu nuevo bot e inicia la conversación con `/start`.
5. Para obtener tu ID personal de Telegram, habla con **[@userinfobot](https://t.me/userinfobot)**; te responderá con tu `Id` numérico (ej. `123456789`). Guárdalo como `TELEGRAM_CHAT_ID`.

---

### Paso 2: Configurar los Secrets en GitHub

1. En tu repositorio de GitHub, dirígete a:
   **Settings** ➔ **Secrets and variables** ➔ **Actions** ➔ **New repository secret**.
2. Añade los siguientes dos secretos:
   - `TELEGRAM_TOKEN`: Tu token generado por BotFather.
   - `TELEGRAM_CHAT_ID`: Tu ID numérico obtenido de @userinfobot.

---

### Paso 3: Habilitar Permisos de Escritura para GitHub Actions

Para que el agente pueda hacer `git commit` y `git push` de `data/empleo.db` tras cada ejecución diaria:
1. En tu repositorio, entra en **Settings** ➔ **Actions** ➔ **General**.
2. Desplázate hasta la sección **Workflow permissions**.
3. Selecciona la opción **"Read and write permissions"**.
4. Haz clic en **Save**.

---

## 💻 Uso Local y Pruebas

### 1. Instalación de dependencias
```bash
python -m pip install -r requirements.txt
```

### 2. Ejecutar búsqueda manualmente
Puedes probar la ejecución en modo local configurando tus variables de entorno (o ejecutándolo directamente; si no defines las variables de Telegram, el agente registrará las alertas en la consola y actualizará la base de datos sin error):
```bash
# En Windows (PowerShell):
$env:TELEGRAM_TOKEN="tu_token"
$env:TELEGRAM_CHAT_ID="tu_chat_id"
python src/job_agent.py

# En Linux/macOS:
export TELEGRAM_TOKEN="tu_token"
export TELEGRAM_CHAT_ID="tu_chat_id"
python src/job_agent.py
```

---

## 🛠️ CLI de Gestión de Ofertas (`gestionar.py`)

Puedes consultar el historial o cambiar el estado de cualquier oferta utilizando el prefijo de su hash identificador:

### 1. Listar ofertas registradas
```bash
# Listar todas las ofertas relevantes (Clase A y B):
python src/gestionar.py --list

# Filtrar por un estado concreto:
python src/gestionar.py --list INTERESANTE
python src/gestionar.py --list SOLICITADA
python src/gestionar.py --list DESCARTADA
```

### 2. Actualizar el estado de una oferta
Los estados válidos son: `NUEVA`, `INTERESANTE`, `SOLICITADA`, `DESCARTADA`.
```bash
# Ejemplo: Marcar como interesante usando los primeros caracteres del hash:
python src/gestionar.py a7c612 INTERESANTE

# Ejemplo: Marcar como solicitada tras haber enviado el CV:
python src/gestionar.py a7c612 SOLICITADA
```

### 3. Inspeccionar el detalle completo de una vacante
```bash
python src/gestionar.py --info a7c612
```

---

## 📡 Fuentes de Ingesta y Extensibilidad

El sistema incluye conectores a:
* **Remotive API:** API JSON oficial con puestos de teletrabajo a nivel nacional e internacional.
* **Tecnoempleo RSS:** Feed estructurado oficial de España (`alertas-empleo-rss.php`) con datos parseados de Empresa, Salario, Tecnologías y Provincia.
* **WeWorkRemotely RSS:** Canales específicos para perfiles DevOps, Sysadmin y Programación.

### ¿Cómo añadir un nuevo canal RSS o API?
En [src/job_agent.py](file:///c:/Proyectos/AlertasEmpleo/src/job_agent.py), crea una clase con el método `fetch()` que devuelva diccionarios con el formato normalizado, y añádela a la lista `self.connectors` en `JobAgent.__init__`.

---

## ⏰ Programación Automática

El workflow de GitHub Actions (`.github/workflows/empleo.yml`) está programado mediante expresión cron:
```yaml
schedule:
  - cron: '0 6 * * *' # 06:00 UTC = 08:00 CEST (España)
```
También puedes lanzarlo en cualquier momento desde la pestaña **Actions** en GitHub seleccionando **Agente Diario de Empleo** ➔ **Run workflow**.
