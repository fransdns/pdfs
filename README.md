# Digitalizador y Regenerador de Boletas de Venta en PDF

Sistema modular en Python para extraer datos de una boleta PDF de entrada, permitir su edición (mediante interfaz gráfica interactiva o consola) y regenerar una réplica exacta del PDF con el mismo formato, alineación y estilo visual.

---

## 📁 Estructura del Proyecto

```text
├── invoice_template.html     # Fase 1: Plantilla HTML/CSS con Jinja2 (diseño visual exacto)
├── invoice_generator.py      # Fase 2: Script principal modular y ejecutable por terminal
├── gui_app.py                # Interfaz Gráfica (GUI) en Tkinter
├── requirements.txt          # Dependencias de Python (pdfplumber, weasyprint, Jinja2)
├── run_gui.bat               # Lanzador 1-clic para la GUI en Windows
├── run_cli.bat               # Lanzador 1-clic para la consola en Windows
├── instalar_windows.bat      # Instalador automático de dependencias en Windows
└── INVOICE-15 PROMAX 256gb.pdf # PDF de muestra base
```

---

## 🛠️ Requisitos e Instalación en Windows

### 1. Requisitos Previos
- **Python 3.10 o superior** instalado en Windows ([python.org](https://www.python.org/downloads/)).
  > ⚠️ Durante la instalación de Python, asegúrate de marcar la casilla **"Add Python to PATH"**.

### 2. Instalación Rápida
Haz doble clic sobre el archivo:
```bat
instalar_windows.bat
```
O desde la terminal (CMD / PowerShell):
```bash
pip install -r requirements.txt
```

> **Nota sobre WeasyPrint en Windows:**
> Las versiones modernas de WeasyPrint (v60+) traen soporte optimizado. Si utilizas una versión previa o requieres bibliotecas GTK adicionales, WeasyPrint proporciona documentación oficial con instalador GTK o wheels precompilados.

---

## 🚀 Modos de Uso

### Modo 1: Interfaz Gráfica (Recomendado)
Haz doble clic en `run_gui.bat` o ejecuta:
```bash
python gui_app.py
```

**Flujo en la GUI:**
1. Haz clic en **"Examinar..."** y selecciona tu boleta PDF.
2. El sistema extraerá automáticamente los valores actuales:
   - **Invoice No (N° Factura)**
   - **Date (Fecha)**
   - **Model (Modelo)**
   - **IMEI 1**
   - **IMEI 2**
   - **Serial Number (N° Serie)**
3. Edita cualquiera de los valores en pantalla.
4. Elige el nombre del PDF de salida (por defecto `{nombre}_EDITADO.pdf`).
5. Presiona **"⚙ GENERAR PDF REGENERADO"**. Al finalizar te ofrecerá abrir el PDF inmediatamente.

---

### Modo 2: Consola / Terminal
Haz doble clic en `run_cli.bat` o ejecuta:
```bash
python invoice_generator.py -i "INVOICE-15 PROMAX 256gb.pdf" -o "NUEVA_BOLETA.pdf"
```

El script te preguntará campo por campo el nuevo valor. Si presionas `[ENTER]` sin escribir nada, mantendrá el valor original extraído.

---

## 🧩 Funciones Principales del Módulo (`invoice_generator.py`)

- `crear_template_base(template_path)`: Asegura y valida la existencia de la plantilla HTML/CSS.
- `extraer_datos_pdf(pdf_path)`: Lee el PDF usando `pdfplumber`, extrayendo campos fijos y variables con regex y bounding boxes.
- `solicitar_nuevos_datos(datos_extraidos)`: Interacción con el usuario para sobreescribir los 6 campos requeridos.
- `generar_pdf_final(template_path, datos, output_pdf_path)`: Compila la plantilla Jinja2 a PDF vía WeasyPrint con manejo de errores y validación.
