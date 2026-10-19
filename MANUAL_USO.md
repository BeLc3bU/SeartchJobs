# 📘 Guía de Uso del Asistente Inteligente de Empleo
**Candidato:** Pedro Úbeda Sánchez  
**Proyecto:** AlertasEmpleo & AI Job Search Assistant

Esta guía explica de forma clara y paso a paso cómo utilizar el sistema en tu día a día, tanto desde el móvil con **Telegram** como desde tu ordenador con la consola de comandos (**CLI**).

---

## 🎯 ¿Cómo funciona el sistema?

El proyecto combina dos entornos para hacerte la búsqueda y postulación lo más cómoda y rápida posible:

```
┌─────────────────────────────────┐       ┌───────────────────────────────────────┐
│     📱 TU MÓVIL (Telegram)       │       │       💻 TU ORDENADOR (Terminal)      │
│  - Recibes alertas de ofertas   │  ───► │  - Generas el CV a medida en 2 seg    │
│  - Lees el resumen y salario    │       │  - Creas la Carta de Presentación     │
│  - Pulsas "⭐ Me Interesa"      │       │  - Preparas la entrevista (Marco STAR)│
└─────────────────────────────────┘       └───────────────────────────────────────┘
```

---

## 📱 1. Uso Diario en Telegram (En tu móvil)

No tienes que buscar ofertas manualmente por internet. El sistema rastrea los 5 portales principales (**InfoJobs, Tecnoempleo, LinkedIn, Indeed y Job Today**) y filtra con tus criterios estrictos:
- **100% Remoto en España** o **Presencial/Híbrido en Hellín/Albacete en turno de tarde o fines de semana**.
- Descarta automáticamente puestos de jornada completa de mañana presenciales fuera de tu zona o profesiones no afines.

### ¿Qué recibes en Telegram?
Por cada vacante clasificada como **Clase A** (encaje directo) o **Clase B** (potencial), recibirás un mensaje como este:

> 🎯 **[Clase A] Administrador de Sistemas Linux y Redes**  
> 🏢 **Empresa:** Tech Cloud Solutions  
> 📍 **Ubicación:** Remoto (España)  
> ⏰ **Horario:** Jornada parcial / Tardes  
> 💰 **Salario:** 24.000 € - 28.000 € / año  
> 💡 **Por qué encaja:** Cumple requisitos de Linux, redes y horario compatible.  
> 🆔 **Hash:** `fa4d2be7`
>
> 🔘 `[🔗 Ver Oferta]` `[⭐ Me Interesa]` `[🗑️ Descartar]`

**¿Qué hacer desde el móvil?**
- Si la oferta te llama la atención: pulsa **`⭐ Me Interesa`**.
- Si no te convence: pulsa **`🗑️ Descartar`**.
- Anota o recuerda los primeros caracteres del identificador (por ejemplo, `fa4d2be7`).

---

## 💻 2. Uso en el Ordenador (Generación de Candidaturas)

Cuando tengas un momento frente al ordenador y quieras postularte a las ofertas que marcaste como interesantes, abre una consola de comandos (PowerShell o Terminal) en la carpeta del proyecto.

### Paso 2.1: Ver tus ofertas interesantes pendientes
```powershell
python src/gestionar.py list INTERESANTE
```
Verás una tabla con el hash, la empresa y el puesto de las ofertas guardadas.

Para ver todos los detalles y requisitos de una oferta concreta:
```powershell
python src/gestionar.py info <hash>
```
*Ejemplo:* `python src/gestionar.py info fa4d2be7`

---

### Paso 2.2: Generar tu CV y Carta a Medida en 1 segundo (`apply`)
Para postularte con la máxima ventaja competitiva:

```powershell
python src/gestionar.py apply <hash>
```
*Ejemplo:* `python src/gestionar.py apply fa4d2be7`

**¿Qué ocurre al ejecutar esto?**
El sistema analiza la oferta, detecta qué tecnologías o competencias pide y genera automáticamente una carpeta en:
📁 `documents/applications/<empresa_puesto_hash>/`

Dentro encontrarás 3 archivos:
1. `cv_adaptado.md`: Tu currículum resaltando automáticamente las habilidades clave para esa vacante (Linux, redes, Proxmox, aviónica, seguridad INCIBE, etc.).
2. `carta_presentacion.md`: Carta de presentación personalizada, profesional y formal, conectando tu experiencia de 22 años en el Ejército del Aire con el rol.
3. `postulacion_completa.html`: **Dossier visual listo para imprimir**.
   - Haz doble clic sobre el archivo para abrirlo en Chrome o Edge.
   - Pulsa <kbd>Ctrl</kbd> + <kbd>P</kbd> y selecciona **Guardar como PDF**. ¡Listo para adjuntar!

Una vez enviada la candidatura a la empresa, actualiza su estado:
```powershell
python src/gestionar.py fa4d2be7 SOLICITADA
```

---

### Paso 2.3: Preparar la Entrevista de Trabajo (`interview`)
Si la empresa te responde y concierta una entrevista:

```powershell
python src/gestionar.py interview <hash>
```
*Ejemplo:* `python src/gestionar.py interview fa4d2be7`

Se generará un documento en `documents/interview_...md` con:
- Respuestas estructuradas bajo el **método STAR** (Situación, Tarea, Acción, Resultado) basadas en tus vivencias reales (aviónica, simuladores de vuelo C-101 / Pilatus, servidores).
- Argumentario sólido para responder a: *"¿Por qué decides pasar del Ejército al sector civil / teletrabajo?"*.
- Preguntas técnicas de alto nivel para hacerle tú al entrevistador y causar una excelente impresión.

---

## 📊 3. Cuadro de Mando y Análisis de Formación

El proyecto incluye dos herramientas analíticas offline:

### Cuadro de Mando Visual (Dashboard local)
```powershell
python src/gestionar.py report
```
Genera un informe interactivo en `documents/reporte_empleo.html`. Ábrelo en tu navegador para ver:
- Gráficos de distribución por portales (InfoJobs, LinkedIn, etc.).
- Estadísticas de ofertas detectadas, solicitadas y descartadas.
- Listado rápido de las últimas ofertas procesadas.

### Analizador de Brechas Tecnológicas (Upskilling)
```powershell
python src/gestionar.py upskill
```
Examina todas las ofertas recogidas en el mercado y te indica **qué tecnologías están pidiendo más** (ej. AWS, Azure, Docker, Kubernetes, etc.) para que sepas qué cursos o certificaciones te conviene priorizar para aumentar tu empleabilidad.

---

## ⚙️ 4. Ejecución Manual y Mantenimiento

### Lanzar el rastreador de ofertas manualmente
Si quieres ejecutar una búsqueda ahora mismo sin esperar a la programación automática:
```powershell
python src/job_agent.py
```

### Limpieza de la base de datos (Purga)
Para eliminar ofertas antiguas que ya hayan caducado:
```powershell
python src/gestionar.py purgar
```
> [!NOTE]
> La purga es inteligente: **nunca borra** las ofertas que hayas marcado como `INTERESANTE` o `SOLICITADA`.

---

## 📌 Tabla Resumen de Comandos

| Acción | Comando |
| :--- | :--- |
| **Listar ofertas relevantes** | `python src/gestionar.py list` |
| **Listar por estado** | `python src/gestionar.py list INTERESANTE` |
| **Ver detalle de una oferta** | `python src/gestionar.py info <hash>` |
| **Marcar como Interesante** | `python src/gestionar.py <hash> INTERESANTE` |
| **Marcar como Solicitada** | `python src/gestionar.py <hash> SOLICITADA` |
| **Generar CV y Carta (PDF)** | `python src/gestionar.py apply <hash>` |
| **Dossier de entrevista (STAR)**| `python src/gestionar.py interview <hash>` |
| **Ver Cuadro de Mando (HTML)** | `python src/gestionar.py report` |
| **Análisis de tecnologías** | `python src/gestionar.py upskill` |
| **Limpiar ofertas antiguas** | `python src/gestionar.py purgar` |
| **Ejecutar rastreador** | `python src/job_agent.py` |
