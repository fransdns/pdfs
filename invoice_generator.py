#!/usr/bin/env python3
"""
invoice_generator.py
Sistema modular para extraer, editar y regenerar boletas de venta en PDF
utilizando pdfplumber, Jinja2 y WeasyPrint.
Editor / Publisher: fransdns de Hosaka Inc.
"""

import os
import re
import sys
import base64
import argparse
from typing import Dict, Any, Optional

# --- Configuración de DLLs para Windows (Python 3.8+ / WeasyPrint / PyInstaller) ---
if sys.platform == "win32":
    rutas_dll_candidatas = []
    # 1. Si está congelado por PyInstaller (--onedir o --onefile)
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        rutas_dll_candidatas.append(base_dir)
        rutas_dll_candidatas.append(os.path.join(base_dir, '_internal'))
    else:
        # 2. Rutas estándar de instalación de GTK3 Runtime en Windows
        rutas_dll_candidatas.extend([
            r"C:\Program Files\GTK3-Runtime Win64\bin",
            r"C:\Program Files (x86)\GTK3-Runtime Win64\bin",
            os.path.join(os.path.expanduser("~"), "GTK3-Runtime Win64", "bin"),
        ])

    for ruta in rutas_dll_candidatas:
        if os.path.isdir(ruta):
            os.environ['PATH'] = ruta + os.pathsep + os.environ.get('PATH', '')
            os.environ['WEASYPRINT_DLL_DIRECTORIES'] = ruta
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(ruta)
                except Exception:
                    pass

import pdfplumber
import jinja2
import weasyprint

# Código QR oficial embebido en base64 para garantizar persistencia sin dependencias externas
DEFAULT_QR_CODE_BASE64 = (
    "data:image/png;base64,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"
    "8H9seU/j6lB/XQAAAABJRU5ErkJggg=="
)


# Patrones de Código 128 (anchuras de 6 módulos por carácter: b1, s1, b2, s2, b3, s3)
_PATRONES_CODE128 = [
    '212222', '222122', '222221', '121223', '121322', '131222', '122213', '122312', '132212', '221213',
    '221312', '231212', '112232', '122132', '122231', '113222', '123122', '123221', '223211', '221132',
    '221231', '213212', '223112', '312131', '311222', '321122', '321221', '312212', '322112', '322211',
    '212123', '212321', '232121', '111323', '131123', '131321', '112313', '132113', '132311', '211313',
    '231113', '231311', '112133', '112331', '132131', '113123', '113321', '133121', '313121', '211331',
    '231131', '213113', '213311', '213131', '311123', '311321', '331121', '312113', '312311', '332111',
    '314111', '221411', '431111', '111224', '111422', '121124', '121421', '141122', '141221', '112214',
    '112412', '122114', '122411', '142112', '142211', '241211', '221114', '413111', '241112', '134111',
    '111242', '121142', '121241', '114212', '124112', '124211', '411212', '421112', '421211', '212141',
    '214121', '412121', '111143', '111341', '131141', '114113', '114311', '411113', '411311', '113141',
    '114131', '311141', '411131', '211412', '211214', '211232', '2331112'
]


def generar_codigo128_svg(texto: str, ancho_pt: float = 100.5, alto_pt: float = 22.0) -> str:
    """
    Genera un código de barras estándar Code 128 (modo Code C de alta densidad para dígitos,
    conmutando limpiamente a Code B para dígitos impares o caracteres alfanuméricos)
    en formato SVG vectorial puro sin dependencias externas.
    """
    texto = str(texto or '').strip().replace(' ', '')
    if not texto:
        return ''

    # Si la cadena está compuesta enteramente de dígitos, usar Code C (óptimo para IMEIs)
    if texto.isdigit():
        codes = [105]  # START C
        i = 0
        n = len(texto)
        while i < n:
            if i + 2 <= n:
                codes.append(int(texto[i:i+2]))
                i += 2
            else:
                # Último dígito impar: conmutar a Code B (código 100) y codificar el dígito
                codes.append(100)
                codes.append(ord(texto[i]) - 32)
                i += 1
    else:
        # Code B para texto alfanumérico
        codes = [104]  # START B
        for ch in texto:
            codes.append(ord(ch) - 32 if 32 <= ord(ch) <= 126 else 0)

    # Cálculo oficial de checksum módulo 103
    checksum = (codes[0] + sum(idx * val for idx, val in enumerate(codes[1:], 1))) % 103
    codes.append(checksum)
    codes.append(106)  # STOP pattern

    pattern = ''.join(_PATRONES_CODE128[c] for c in codes)
    total_modules = sum(int(ch) for ch in pattern)

    rects = []
    x = 0
    h = 50  # Altura virtual normalizada en viewBox
    for idx, ch in enumerate(pattern):
        w = int(ch)
        if idx % 2 == 0:  # Barra negra
            rects.append(f'<rect x="{x}" y="0" width="{w}" height="{h}" fill="#000000"/>')
        x += w

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_modules} {h}" '
        f'width="{ancho_pt}pt" height="{alto_pt}pt" preserveAspectRatio="none">'
        f'{" ".join(rects)}'
        f'</svg>'
    )
    return svg


def obtener_ruta_recurso(nombre_archivo: str) -> str:
    """
    Obtiene la ruta absoluta de un archivo de recursos, garantizando total
    compatibilidad tanto en modo desarrollo (.py) como al compilarse en .exe
    con PyInstaller (utilizando la carpeta temporal sys._MEIPASS).
    """
    if hasattr(sys, '_MEIPASS'):
        ruta_empaquetada = os.path.join(sys._MEIPASS, nombre_archivo)
        if os.path.exists(ruta_empaquetada):
            return ruta_empaquetada
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, nombre_archivo)


def obtener_qr_code_src() -> str:
    """
    Obtiene la fuente del código QR. Si existe el archivo qr_code.png en disco
    o empaquetado, lo lee y codifica a data URI; en caso contrario, utiliza
    el valor por defecto embebido en base64 de alta resolución.
    """
    posible_archivo = obtener_ruta_recurso("qr_code.png")
    if os.path.exists(posible_archivo):
        try:
            with open(posible_archivo, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
                return f"data:image/png;base64,{b64}"
        except Exception:
            pass
    return DEFAULT_QR_CODE_BASE64


# Plantilla HTML embebida por defecto en caso de que no exista el archivo
DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Billing Invoice</title>
<style>
  @page {
    size: 612pt 792pt;
    margin: 0;
  }
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  body {
    width: 612pt;
    height: 792pt;
    font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
    color: #000000;
    font-size: 10.5pt;
    line-height: 1.35;
    background: #ffffff;
    position: relative;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .company-name {
    position: absolute;
    top: 56.2pt;
    left: 56.0pt;
    font-size: 24.0pt;
    font-weight: normal;
    color: #000000;
    letter-spacing: -0.2pt;
    white-space: nowrap;
  }
  .company-address {
    position: absolute;
    top: 88.0pt;
    left: 54.6pt;
    font-size: 10.5pt;
    line-height: 14.8pt;
  }
  .invoice-title {
    position: absolute;
    top: 57.0pt;
    right: 54.5pt;
    font-size: 27.5pt;
    font-weight: bold;
    letter-spacing: 0.5pt;
    text-transform: uppercase;
    text-align: right;
  }
  .invoice-meta-table {
    position: absolute;
    top: 98.0pt;
    right: 52.0pt;
    border-collapse: collapse;
    font-size: 10.5pt;
  }
  .invoice-meta-table td {
    padding: 2.2pt 0;
  }
  .invoice-meta-table td.meta-label {
    text-align: right;
    padding-right: 15.0pt;
    font-weight: normal;
    white-space: nowrap;
  }
  .invoice-meta-table td.meta-value {
    text-align: right;
    white-space: nowrap;
  }
  .divider-thick-top {
    position: absolute;
    top: 168.4pt;
    left: 54.3pt;
    width: 504.2pt;
    height: 2.5pt;
    background-color: #000000;
  }
  .bill-to-box {
    position: absolute;
    top: 186.7pt;
    left: 54.6pt;
    width: 236.7pt;
  }
  .ship-to-box {
    position: absolute;
    top: 186.7pt;
    left: 320.4pt;
    width: 237.8pt;
  }
  .addr-title {
    font-size: 10.5pt;
    font-weight: normal;
  }
  .addr-line {
    height: 1.15pt;
    background-color: #2b2b2b;
    margin-top: 5.5pt;
    margin-bottom: 9.0pt;
    width: 100%;
  }
  .addr-text {
    font-size: 10.5pt;
    line-height: 15.2pt;
  }
  .table-header {
    position: absolute;
    top: 292.0pt;
    left: 54.0pt;
    width: 504.5pt;
    height: 32.0pt;
  }
  .th-desc {
    position: absolute;
    left: 9.6pt;
    top: 9.0pt;
    font-size: 10.4pt;
  }
  .th-item-no {
    position: absolute;
    left: 265.0pt;
    top: 1.5pt;
    font-size: 10.4pt;
    text-align: center;
    line-height: 14.5pt;
  }
  .th-qty {
    position: absolute;
    left: 342.8pt;
    top: 7.0pt;
    font-size: 10.4pt;
  }
  .th-price {
    position: absolute;
    left: 396.6pt;
    top: 0.0pt;
    font-size: 10.4pt;
    text-align: center;
    line-height: 16.0pt;
  }
  .th-amount {
    position: absolute;
    right: 3.6pt;
    top: 9.0pt;
    font-size: 10.4pt;
  }
  .divider-table-header {
    position: absolute;
    top: 323.9pt;
    left: 53.8pt;
    width: 504.7pt;
    height: 3.0pt;
    background-color: #000000;
  }
  .item-content {
    position: absolute;
    top: 337.0pt;
    left: 54.0pt;
    width: 504.5pt;
  }
  .item-desc {
    position: absolute;
    left: 8.9pt;
    top: 0;
    width: 325.0pt;
    font-size: 10.4pt;
    line-height: 15.5pt;
  }
  .imei-row {
    margin-top: 3.0pt;
    position: relative;
    height: 38.0pt;
  }
  .imei-col-1 {
    position: absolute;
    left: 0;
    top: 0;
    width: 125.0pt;
  }
  .imei-col-2 {
    position: absolute;
    left: 133.5pt;
    top: 0;
    width: 125.0pt;
  }
  .imei-lbl {
    font-size: 10.4pt;
    line-height: 13.0pt;
    white-space: nowrap;
  }
  .barcode-box {
    margin-top: 1.5pt;
    width: 100.5pt;
    height: 22.0pt;
  }
  .barcode-box svg {
    width: 100.5pt;
    height: 22.0pt;
    display: block;
  }
  .item-qty-val {
    position: absolute;
    left: 350.0pt;
    top: 0;
    font-size: 10.4pt;
    text-align: center;
  }
  .item-price-val {
    position: absolute;
    left: 389.2pt;
    top: 0;
    font-size: 10.4pt;
    width: 42.0pt;
    text-align: right;
  }
  .item-amount-val {
    position: absolute;
    right: 3.6pt;
    top: 0;
    font-size: 10.4pt;
    text-align: right;
  }
  .divider-table-bottom {
    position: absolute;
    top: 432.0pt;
    left: 54.3pt;
    width: 504.2pt;
    height: 0.92pt;
    background-color: #000000;
  }
  .totals-block {
    position: absolute;
    top: 437.0pt;
    right: 52.8pt;
    width: 204.5pt;
  }
  .totals-row {
    display: flex;
    justify-content: space-between;
    font-size: 10.5pt;
    padding-bottom: 7.5pt;
  }
  .totals-row .col-lbl {
    width: 125.0pt;
    text-align: right;
  }
  .totals-row .col-val {
    width: 79.5pt;
    text-align: right;
  }
  .totals-divider {
    width: 204.5pt;
    height: 1.15pt;
    background-color: #2f2f2f;
    margin-top: 1.0pt;
    margin-bottom: 7.0pt;
    margin-left: auto;
  }
  .total-highlight {
    display: flex;
    justify-content: space-between;
    font-size: 12.0pt;
    font-weight: bold;
    color: #000000;
  }
  .total-highlight .col-lbl {
    width: 125.0pt;
    text-align: right;
  }
  .total-highlight .col-val {
    width: 79.5pt;
    text-align: right;
  }
  .bank-details-box {
    position: absolute;
    top: 518.0pt;
    left: 53.25pt;
    width: 504.45pt;
    height: 86.0pt;
    border: 1px solid #2b2b2f;
    padding: 7.0pt 11.6pt;
    font-size: 10.45pt;
    line-height: 12.8pt;
  }
  .thank-you-text {
    position: absolute;
    top: 616.0pt;
    left: 0;
    width: 612.0pt;
    text-align: center;
    font-size: 10.4pt;
    letter-spacing: 0.5pt;
  }
  .qr-code-box {
    position: absolute;
    top: 636.0pt;
    left: 254.75pt;
    width: 102.5pt;
    height: 102.5pt;
    text-align: center;
  }
  .qr-code-img {
    width: 102.5pt;
    height: 102.5pt;
    display: block;
  }
  .page-number {
    position: absolute;
    top: 760.0pt;
    right: 54.0pt;
    font-size: 10.4pt;
  }
</style>
</head>
<body>
  <div class="company-name">{{ company_name|default('AO Digital INC') }}</div>
  <div class="company-address">
    {{ company_address_1|default('1604 York Ct') }}<br>
    {{ company_address_2|default('Mundelein, IL 60060') }}
  </div>
  <div class="invoice-title">BILLING INVOICE</div>
  <table class="invoice-meta-table">
    <tr>
      <td class="meta-label">INVOICE NO.</td>
      <td class="meta-value">{{ invoice_no }}</td>
    </tr>
    <tr>
      <td class="meta-label">DATE</td>
      <td class="meta-value">{{ date }}</td>
    </tr>
    <tr>
      <td class="meta-label">TERMS</td>
      <td class="meta-value">{{ terms|default('Bank Transfer/Wire') }}</td>
    </tr>
  </table>
  <div class="divider-thick-top"></div>
  <div class="bill-to-box">
    <div class="addr-title">BILL TO:</div>
    <div class="addr-line"></div>
    <div class="addr-text">
      {{ bill_to_name|default('Jean Dueñas Rojas') }}<br>
      {{ bill_to_address_1|default('7270 Nw 25th Ter') }}<br>
      {{ bill_to_address_2|default('Miami, FL 33166-4756') }}
    </div>
  </div>
  <div class="ship-to-box">
    <div class="addr-title">SHIP TO:</div>
    <div class="addr-line"></div>
    <div class="addr-text">
      {{ ship_to_name|default('Jean Dueñas Rojas') }}<br>
      {{ ship_to_address_1|default('7270 Nw 25th Ter') }}<br>
      {{ ship_to_address_2|default('Miami, FL 33166-4756') }}
    </div>
  </div>
  <div class="table-header">
    <span class="th-desc">DESCRIPTION</span>
    <span class="th-item-no">ITEM<br>NUMBER</span>
    <span class="th-qty">QTY</span>
    <span class="th-price">UNIT<br>PRICE</span>
    <span class="th-amount">AMOUNT</span>
  </div>
  <div class="divider-table-header"></div>
  <div class="item-content">
    <div class="item-desc">
      <div>{{ item_description|default('Apple Iphone 15 Pro Max A2849 512GB Natural Unlocked') }}</div>
      <div>Model: {{ model }}</div>
      <div>Serial Number: {{ serial_number }}</div>
      <div class="imei-row">
        <div class="imei-col-1">
          <div class="imei-lbl">IMEI1: {{ imei1 }}</div>
          <div class="barcode-box">{{ barcode1_svg|safe }}</div>
        </div>
        <div class="imei-col-2">
          <div class="imei-lbl">IMEI2: {{ imei2 }}</div>
          <div class="barcode-box">{{ barcode2_svg|safe }}</div>
        </div>
      </div>
    </div>
    <div class="item-qty-val">{{ item_qty|default('1') }}</div>
    <div class="item-price-val">{{ item_unit_price|default('$773.50') }}</div>
    <div class="item-amount-val">{{ item_amount|default('$773.50') }}</div>
  </div>
  <div class="divider-table-bottom"></div>
  <div class="totals-block">
    <div class="totals-row">
      <span class="col-lbl">SUBTOTAL</span>
      <span class="col-val">{{ subtotal|default('$773.50') }}</span>
    </div>
    <div class="totals-row">
      <span class="col-lbl">{{ tax_label|default('IL TAX ( 7.00% )') }}</span>
      <span class="col-val">{{ tax_amount|default('$54.15') }}</span>
    </div>
    <div class="totals-divider"></div>
    <div class="total-highlight">
      <span class="col-lbl">TOTAL</span>
      <span class="col-val">{{ total|default('$827.65') }}</span>
    </div>
  </div>
  <div class="bank-details-box">
    {{ bank_line_1|default('AO Digital, Inc. Bank Name: Bank of America,') }}<br>
    {{ bank_line_2|default('Account Name: AO Digital, Inc.') }}<br>
    {{ bank_line_3|default('Account Number: 291040780652') }}<br>
    {{ bank_line_4|default('ABA/Routing Number: 026009593 (wires)') }}<br>
    {{ bank_line_5|default('SWIFT Code: BOFAUS3N') }}<br>
    {{ bank_line_6|default('Contact us : aodigitalcraftus@gmail.com') }}
  </div>
  <div class="thank-you-text">{{ thank_you_text|default('THANK YOU') }}</div>
  <div class="qr-code-box">
    <img src="{{ qr_code_src }}" class="qr-code-img" alt="QR Code">
  </div>
  <div class="page-number">{{ page_info|default('Page 1 of 1') }}</div>
</body>
</html>
"""


def crear_template_base(template_path: str = "invoice_template.html") -> str:
    """
    Crea o valida la plantilla HTML base con sintaxis Jinja2.
    Si el archivo no existe, lo crea a partir del diseño por defecto.
    Retorna la ruta absoluta del archivo de plantilla.
    """
    try:
        if not os.path.isabs(template_path):
            ruta_posible = obtener_ruta_recurso(template_path)
            if os.path.exists(ruta_posible):
                return ruta_posible
            abs_path = os.path.abspath(template_path)
        else:
            abs_path = template_path

        if not os.path.exists(abs_path):
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(DEFAULT_HTML_TEMPLATE.strip())
            print(f"[OK] Plantilla base creada exitosamente en: {abs_path}")
        else:
            print(f"[INFO] Plantilla existente cargada desde: {abs_path}")
        return abs_path
    except (IOError, OSError) as e:
        print(f"[ERROR] No se pudo crear o acceder a la plantilla: {e}", file=sys.stderr)
        raise


def calcular_totales(subtotal_str: str) -> tuple:
    """
    Calcula IL TAX (7.00%) y TOTAL en base al SUBTOTAL ingresado.
    Fórmula: IL TAX = Subtotal * 0.07; TOTAL = Subtotal + IL TAX.
    Retorna (subtotal_formateado, tax_formateado, total_formateado).
    """
    cleaned = re.sub(r'[^\d.]', '', str(subtotal_str or '0'))
    try:
        subtotal = float(cleaned)
    except ValueError:
        subtotal = 0.0
    tax = round(subtotal * 0.07, 2)
    total = round(subtotal + tax, 2)
    return f"${subtotal:.2f}", f"${tax:.2f}", f"${total:.2f}"


def limpiar_direccion_espaciado(texto: str) -> str:
    """
    Normaliza y asegura que las palabras y números de una dirección o nombre
    tengan el espaciado adecuado (evita '7270Nw25thTer' o 'Miami,FL33166-4756').
    """
    if not texto:
        return ""
    s = texto.strip()
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([A-Za-z]+)(\d+)', r'\1 \2', s)
    s = re.sub(r'(\d+)(?!(?:th|st|nd|rd)\b)([A-Za-z]+)', r'\1 \2', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:th|st|nd|rd))([A-Za-z]+)', r'\1 \2', s, flags=re.IGNORECASE)
    s = re.sub(r',([^\s])', r', \1', s)
    s = re.sub(r'([A-Za-z]{2})(\d{5})', r'\1 \2', s)
    return re.sub(r'\s+', ' ', s).strip()


def extraer_datos_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Lee un PDF de boleta de entrada usando pdfplumber y extrae tanto los datos
    fijos como los dinámicos utilizando expresiones regulares y bounding boxes.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"El archivo PDF de entrada no existe: {pdf_path}")

    datos: Dict[str, Any] = {
        "company_name": "AO Digital INC",
        "company_address_1": "1604 York Ct",
        "company_address_2": "Mundelein, IL 60060",
        "invoice_no": "",
        "date": "",
        "terms": "Bank Transfer/Wire",
        "bill_to_name": "Jean Dueñas Rojas",
        "bill_to_address_1": "7270 Nw 25th Ter",
        "bill_to_address_2": "Miami, FL 33166-4756",
        "ship_to_name": "Jean Dueñas Rojas",
        "ship_to_address_1": "7270 Nw 25th Ter",
        "ship_to_address_2": "Miami, FL 33166-4756",
        "item_description": "Apple Iphone 15 Pro Max A2849 512GB Natural Unlocked",
        "item_number": "",
        "item_qty": "1",
        "item_unit_price": "$773.50",
        "item_amount": "$773.50",
        "imei1": "",
        "imei2": "",
        "model": "",
        "serial_number": "",
        "subtotal": "$773.50",
        "tax_label": "IL TAX ( 7.00% )",
        "tax_amount": "$54.15",
        "total": "$827.65",
        "bank_line_1": "AO Digital, Inc. Bank Name: Bank of America,",
        "bank_line_2": "Account Name: AO Digital, Inc.",
        "bank_line_3": "Account Number: 291040780652",
        "bank_line_4": "ABA/Routing Number: 026009593 (wires)",
        "bank_line_5": "SWIFT Code: BOFAUS3N",
        "bank_line_6": "Contact us : aodigitalcraftus@gmail.com",
        "thank_you_text": "THANK YOU",
        "page_info": "Page 1 of 1",
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError("El archivo PDF no contiene ninguna página.")

            page = pdf.pages[0]
            text = page.extract_text(x_tolerance=1.5) or ""

            # 1. Invoice No (ej: 689912 o 689915)
            m_inv = re.search(r'INVOICENO\.\s*([A-Za-z0-9_-]+)', text, re.IGNORECASE) or \
                    re.search(r'INVOICE\s*NO\.?\s*[:#]?\s*([A-Za-z0-9_-]+)', text, re.IGNORECASE)
            if m_inv:
                datos["invoice_no"] = m_inv.group(1).strip()

            # 2. Date (ej: 15/08/2026)
            m_date = re.search(r'DATE\s*[:#]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', text, re.IGNORECASE)
            if m_date:
                datos["date"] = m_date.group(1).strip()

            # 3. Terms (ej: Bank Transfer/Wire)
            m_terms = re.search(r'TERMS\s+([^\r\n]+)', text, re.IGNORECASE)
            if m_terms:
                datos["terms"] = m_terms.group(1).strip()

            # 4. IMEI 1 y IMEI 2 (soporta formatos con barra o separados por espacios)
            m_imei = re.search(r'Imei1\s*:\s*([0-9]+)\s*/\s*Imei2\s*:\s*([0-9]+)', text, re.IGNORECASE)
            if m_imei:
                datos["imei1"] = m_imei.group(1).strip()
                datos["imei2"] = m_imei.group(2).strip()
            else:
                m1 = re.search(r'Imei\s*1\s*:\s*([0-9]+)', text, re.IGNORECASE)
                m2 = re.search(r'Imei\s*2\s*:\s*([0-9]+)', text, re.IGNORECASE)
                if m1:
                    datos["imei1"] = m1.group(1).strip()
                if m2:
                    datos["imei2"] = m2.group(1).strip()

            # 5. Model (ej: MU693LL/A o MU6A3LL/A)
            m_model = re.search(r'Model\s*:\s*([A-Za-z0-9/_ -]+)', text, re.IGNORECASE)
            if m_model:
                datos["model"] = m_model.group(1).strip()

            # 6. Serial Number (ej: C1Q0FP227Q o HY9J4WDWK5)
            m_serial = re.search(r'SerialNumber\s*:\s*([A-Za-z0-9]+)', text, re.IGNORECASE) or \
                       re.search(r'Serial\s*Number\s*:\s*([A-Za-z0-9]+)', text, re.IGNORECASE)
            if m_serial:
                datos["serial_number"] = m_serial.group(1).strip()

            # 7. Bounding Box extraction para BILL TO (x0=50, top=185, x1=300, bottom=265)
            try:
                bill_crop = page.crop((50, 185, 300, 265))
                bill_words = bill_crop.extract_words(x_tolerance=1.5)
                bill_lines = {}
                for w in bill_words:
                    if "BILL" in w["text"] or "TO:" in w["text"]:
                        continue
                    t = round(w["top"] / 5) * 5
                    bill_lines.setdefault(t, []).append(w["text"])
                lines = [limpiar_direccion_espaciado(" ".join(words)) for _, words in sorted(bill_lines.items())]
                lines = [l for l in lines if l]
                if len(lines) >= 1:
                    datos["bill_to_name"] = lines[0]
                if len(lines) >= 2:
                    datos["bill_to_address_1"] = lines[1]
                if len(lines) >= 3:
                    datos["bill_to_address_2"] = lines[2]
            except Exception:
                pass

            # 8. Bounding Box extraction para SHIP TO (x0=310, top=185, x1=560, bottom=265)
            try:
                ship_crop = page.crop((310, 185, 560, 265))
                ship_words = ship_crop.extract_words(x_tolerance=1.5)
                ship_lines = {}
                for w in ship_words:
                    if "SHIP" in w["text"] or "TO:" in w["text"]:
                        continue
                    t = round(w["top"] / 5) * 5
                    ship_lines.setdefault(t, []).append(w["text"])
                slines = [limpiar_direccion_espaciado(" ".join(words)) for _, words in sorted(ship_lines.items())]
                slines = [l for l in slines if l]
                if len(slines) >= 1:
                    datos["ship_to_name"] = slines[0]
                if len(slines) >= 2:
                    datos["ship_to_address_1"] = slines[1]
                if len(slines) >= 3:
                    datos["ship_to_address_2"] = slines[2]
            except Exception:
                pass

            # 9. Item Description, QTY, Unit Price y Amount (100% dinámico)
            item_found = False
            for line in text.splitlines():
                line = line.strip()
                m_line = re.match(r"^([A-Za-z0-9][^\n]+?)\s+(\d+)\s+(\$[\d,.]+)\s+(\$[\d,.]+)$", line)
                if m_line and "DESCRIPTION" not in m_line.group(1).upper() and "TOTAL" not in m_line.group(1).upper():
                    datos["item_description"] = m_line.group(1).strip()
                    datos["item_qty"] = m_line.group(2).strip()
                    datos["item_unit_price"] = m_line.group(3).strip()
                    datos["item_amount"] = m_line.group(4).strip()
                    item_found = True
                    break

            if not item_found:
                m_between = re.search(r'(?:PRICE|NUMBER)\s*\n\s*([^\n]+?)(?:\s+(\d+)\s+(\$[\d,.]+)\s+(\$[\d,.]+))?\s*\n', text, re.IGNORECASE)
                if m_between and m_between.group(1):
                    raw_desc = m_between.group(1).strip()
                    cleaned_desc = re.sub(r'\s+\d+\s+\$[\d,.]+\s+\$[\d,.]+$', '', raw_desc).strip()
                    if cleaned_desc:
                        datos["item_description"] = cleaned_desc
                    if m_between.group(2): datos["item_qty"] = m_between.group(2).strip()
                    if m_between.group(3): datos["item_unit_price"] = m_between.group(3).strip()
                    if m_between.group(4): datos["item_amount"] = m_between.group(4).strip()

            # 10. Subtotal, Tax y Total
            m_sub = re.search(r'SUBTOTAL\s*(\$[\d,.]+)', text, re.IGNORECASE)
            if m_sub:
                datos["subtotal"] = m_sub.group(1).strip()
                if not datos.get("item_unit_price"):
                    datos["item_unit_price"] = datos["subtotal"]
                if not datos.get("item_amount"):
                    datos["item_amount"] = datos["subtotal"]

            m_tax = re.search(r'(IL\s*TAX\s*(?:\([^)]+\))?)\s*(\$[\d,.]+)', text, re.IGNORECASE) or \
                    re.search(r'([A-Za-z ]*TAX\s*(?:\([^)]+\))?)\s*(\$[\d,.]+)', text, re.IGNORECASE)
            if m_tax:
                datos["tax_label"] = m_tax.group(1).strip()
                datos["tax_amount"] = m_tax.group(2).strip()

            # Evitar capturar SUBTOTAL como TOTAL usando un límite de palabra negativo
            m_tot = re.search(r'(?<!SUB)\bTOTAL\s*(\$[\d,.]+)', text, re.IGNORECASE)
            if m_tot:
                datos["total"] = m_tot.group(1).strip()

            # Contact line en datos bancarios si existe
            m_contact = re.search(r'(Contact\s*us\s*:\s*[^\r\n]+)', text, re.IGNORECASE)
            if m_contact:
                datos["bank_line_6"] = m_contact.group(1).strip()

            # Asegurar consistencia matemática automática (7% de IL TAX)
            if datos.get("subtotal"):
                s_fmt, tx_fmt, tot_fmt = calcular_totales(datos["subtotal"])
                datos["subtotal"] = s_fmt
                datos["tax_amount"] = tx_fmt
                datos["total"] = tot_fmt

    except Exception as e:
        print(f"[ERROR] Error al procesar el archivo PDF '{pdf_path}': {e}", file=sys.stderr)
        raise

    return datos


def solicitar_nuevos_datos(datos_extraidos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solicita al usuario a través de la consola ingresar nuevos valores para
    los campos modificables: imei1, imei2, model, serial_number, date y invoice_no.
    Si el usuario presiona Enter sin escribir, se conserva el valor original extraído.
    Retorna el diccionario unificado con los datos actualizados.
    """
    datos_actualizados = dict(datos_extraidos)

    print("\n" + "=" * 60)
    print(" ACTUALIZACIÓN DE DATOS DE LA BOLETA")
    print(" Ingrese el nuevo valor o presione [ENTER] para mantener el actual.")
    print("=" * 60)

    campos = [
        ("invoice_no", "Invoice No (Número de Factura)", datos_extraidos.get("invoice_no", "")),
        ("date", "Date (Fecha ej. 15/08/2026)", datos_extraidos.get("date", "")),
        ("model", "Model (Modelo ej. MU693LL/A)", datos_extraidos.get("model", "")),
        ("imei1", "IMEI 1", datos_extraidos.get("imei1", "")),
        ("imei2", "IMEI 2", datos_extraidos.get("imei2", "")),
        ("serial_number", "Serial Number (Número de Serie)", datos_extraidos.get("serial_number", "")),
    ]

    for clave, etiqueta, valor_actual in campos:
        try:
            prompt = f" -> {etiqueta} [{valor_actual}]: "
            entrada = input(prompt).strip()
            if entrada:
                datos_actualizados[clave] = entrada
            else:
                datos_actualizados[clave] = valor_actual
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada por el usuario.")
            sys.exit(0)

    print("=" * 60)
    print("[OK] Datos combinados listos para la inyección en plantilla.\n")
    return datos_actualizados


def generar_pdf_final(template_path: str, datos: Dict[str, Any], output_pdf_path: str) -> bool:
    """
    Inyecta los datos en la plantilla Jinja2, genera automáticamente los códigos
    de barra Code 128 a partir de los IMEIs y compila el documento en un PDF
    idéntico visualmente utilizando WeasyPrint.
    """
    try:
        # Cargar plantilla
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"No se encontró el archivo de plantilla: {template_path}")

        template_dir = os.path.dirname(os.path.abspath(template_path))
        template_file = os.path.basename(template_path)

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir or "."),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        template = env.get_template(template_file)

        # Generar códigos de barras Code 128 vectoriales a partir de los IMEIs
        datos_render = dict(datos)
        imei1_val = str(datos_render.get("imei1", "")).strip()
        imei2_val = str(datos_render.get("imei2", "")).strip()

        if "barcode1_svg" not in datos_render or not datos_render["barcode1_svg"]:
            datos_render["barcode1_svg"] = generar_codigo128_svg(imei1_val) if imei1_val else ""
        if "barcode2_svg" not in datos_render or not datos_render["barcode2_svg"]:
            datos_render["barcode2_svg"] = generar_codigo128_svg(imei2_val) if imei2_val else ""

        # Asegurar código QR oficial
        if "qr_code_src" not in datos_render or not datos_render["qr_code_src"]:
            datos_render["qr_code_src"] = obtener_qr_code_src()

        html_rendered = template.render(**datos_render)

        # Generar PDF con WeasyPrint
        out_dir = os.path.dirname(os.path.abspath(output_pdf_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        print(f"[INFO] Renderizando PDF con WeasyPrint hacia: {output_pdf_path} ...")
        weasy_doc = weasyprint.HTML(string=html_rendered, base_url=template_dir)
        weasy_doc.write_pdf(output_pdf_path)

        if os.path.exists(output_pdf_path):
            file_size_kb = os.path.getsize(output_pdf_path) / 1024
            print(f"[EXITO] PDF generado con éxito: {output_pdf_path} ({file_size_kb:.1f} KB)")
            return True
        else:
            print(f"[ERROR] El archivo de salida no fue creado: {output_pdf_path}", file=sys.stderr)
            return False

    except jinja2.TemplateError as e:
        print(f"[ERROR] Error al procesar la plantilla Jinja2: {e}", file=sys.stderr)
        return False
    except weasyprint.WeasyPrintErrors as e:
        print(f"[ERROR] WeasyPrint falló al compilar el PDF: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Excepción inesperada durante la generación del PDF: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Digitalizador y regenerador de boletas de venta en PDF."
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default="INVOICE-15 PROMAX 256gb.pdf",
        help="Ruta al archivo PDF original de entrada."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="INVOICE_GENERATED.pdf",
        help="Ruta donde se guardará el nuevo PDF generado."
    )
    parser.add_argument(
        "-t", "--template",
        type=str,
        default="invoice_template.html",
        help="Ruta a la plantilla HTML con sintaxis Jinja2."
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Lanzar la interfaz gráfica de usuario en lugar del modo consola."
    )

    args = parser.parse_args()

    if args.gui:
        try:
            import gui_app
            gui_app.run_gui()
            return
        except ImportError:
            print("[ERROR] No se pudo cargar el módulo de interfaz gráfica 'gui_app.py'.", file=sys.stderr)
            sys.exit(1)

    print("=" * 60)
    print(" SISTEMA DE DIGITALIZACIÓN Y REGENERACIÓN DE BOLETAS")
    print(" Editor / Publisher: fransdns de Hosaka Inc.")
    print("=" * 60)

    template_path = crear_template_base(args.template)

    if not os.path.exists(args.input):
        print(f"[ERROR] El archivo de entrada '{args.input}' no existe.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Extrayendo datos desde: {args.input} ...")
    datos_extraidos = extraer_datos_pdf(args.input)
    print(f"[OK] Datos base extraídos:")
    print(f"     - Invoice No:    {datos_extraidos.get('invoice_no')}")
    print(f"     - Fecha:         {datos_extraidos.get('date')}")
    print(f"     - Modelo:        {datos_extraidos.get('model')}")
    print(f"     - IMEI 1:        {datos_extraidos.get('imei1')}")
    print(f"     - IMEI 2:        {datos_extraidos.get('imei2')}")
    print(f"     - Serial Number: {datos_extraidos.get('serial_number')}")

    datos_finales = solicitar_nuevos_datos(datos_extraidos)

    exito = generar_pdf_final(template_path, datos_finales, args.output)
    if exito:
        print(f"\n[FINALIZADO] Proceso completado exitosamente.")
        print(f"Puede abrir su nuevo archivo: {os.path.abspath(args.output)}")
    else:
        print("\n[FALLO] No se pudo completar la generación del PDF.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
