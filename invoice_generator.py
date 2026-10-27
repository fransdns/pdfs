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
    line-height: 18.0pt;
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
    top: 418.0pt;
    left: 54.3pt;
    width: 504.2pt;
    height: 0.92pt;
    background-color: #000000;
  }
  .totals-block {
    position: absolute;
    top: 423.0pt;
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
    top: 494.1pt;
    left: 53.25pt;
    width: 504.45pt;
    height: 92.25pt;
    border: 1px solid #2b2b2f;
    padding: 10.0pt 11.6pt;
    font-size: 10.45pt;
    line-height: 13.4pt;
  }
  .thank-you-text {
    position: absolute;
    top: 626.1pt;
    left: 0;
    width: 612.0pt;
    text-align: center;
    font-size: 10.4pt;
    letter-spacing: 0.5pt;
  }
  .page-number {
    position: absolute;
    top: 761.2pt;
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
      <div>{{ item_description|default('Apple Iphone 15 Pro Max A2849 256GB Blue Unlocked') }}</div>
      <div>Imei1:{{ imei1 }} / Imei2:{{ imei2 }}</div>
      <div>Model: {{ model }}</div>
      <div>Serial Number: {{ serial_number }}</div>
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
    {{ bank_line_5|default('SWIFT Code: BOFAUS3N') }}
  </div>
  <div class="thank-you-text">{{ thank_you_text|default('THANK YOU') }}</div>
  <div class="page-number">{{ page_info|default('Page 1 of 1') }}</div>
</body>
</html>
"""


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
    # Si estamos en desarrollo o el archivo reside junto al script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, nombre_archivo)


def crear_template_base(template_path: str = "invoice_template.html") -> str:
    """
    Crea o valida la plantilla HTML base con sintaxis Jinja2.
    Si el archivo no existe, lo crea a partir del diseño por defecto.
    Retorna la ruta absoluta del archivo de plantilla.
    """
    try:
        # Si la ruta es relativa y existe en recursos empaquetados o junto al script
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
    # Separar minúscula de mayúscula (ej: DueñasRojas -> Dueñas Rojas)
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    # Separar letras de números (ej: Nw25th -> Nw 25th)
    s = re.sub(r'([A-Za-z]+)(\d+)', r'\1 \2', s)
    # Separar números de letras excepto sufijos ordinales (ej: 7270Nw -> 7270 Nw, pero respeta 25th)
    s = re.sub(r'(\d+)(?!(?:th|st|nd|rd)\b)([A-Za-z]+)', r'\1 \2', s, flags=re.IGNORECASE)
    # Separar ordinales de nombres de calles (ej: 25thTer -> 25th Ter)
    s = re.sub(r'(\d+(?:th|st|nd|rd))([A-Za-z]+)', r'\1 \2', s, flags=re.IGNORECASE)
    # Separar comas pegadas a texto (ej: Miami,FL -> Miami, FL)
    s = re.sub(r',([^\s])', r', \1', s)
    # Separar código de estado de código postal (ej: FL33166 -> FL 33166)
    s = re.sub(r'([A-Za-z]{2})(\d{5})', r'\1 \2', s)
    # Normalizar múltiples espacios
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
        "item_description": "Apple Iphone 15 Pro Max A2849 256GB Blue Unlocked",
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
        "thank_you_text": "THANK YOU",
        "page_info": "Page 1 of 1",
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError("El archivo PDF no contiene ninguna página.")

            page = pdf.pages[0]
            # Extraer con tolerancia x reducida (1.5) para preservar el espaciado
            # entre palabras renderizadas sin carácter de espacio explícito
            text = page.extract_text(x_tolerance=1.5) or ""

            # 1. Invoice No (ej: 689912)
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

            # 4. IMEI 1 y IMEI 2
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

            # 5. Model (ej: MU693LL/A)
            m_model = re.search(r'Model\s*:\s*([A-Za-z0-9/_ -]+)', text, re.IGNORECASE)
            if m_model:
                datos["model"] = m_model.group(1).strip()

            # 6. Serial Number (ej: C1Q0FP227Q)
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

            # 9. Item Description, QTY, Unit Price y Amount (100% dinámico para cualquier producto)
            m_item = re.search(r'\n\s*([^\n]+?)\s+(\d+)\s+(\$[\d,.]+)\s+(\$[\d,.]+)\s*\n\s*Imei', text, re.IGNORECASE)
            if m_item:
                datos["item_description"] = m_item.group(1).strip()
                datos["item_qty"] = m_item.group(2).strip()
                datos["item_unit_price"] = m_item.group(3).strip()
                datos["item_amount"] = m_item.group(4).strip()
            else:
                # Búsqueda alternativa en la tabla entre cabeceras y SUBTOTAL
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
    Inyecta los datos en la plantilla Jinja2 y compila el documento resultante
    en un archivo PDF idéntico visualmente utilizando WeasyPrint.
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
        html_rendered = template.render(**datos)

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
    print("=" * 60)

    # 1. Asegurar plantilla
    template_path = crear_template_base(args.template)

    # 2. Extracción de datos del PDF base
    if not os.path.exists(args.input):
        print(f"[ERROR] El archivo de entrada '{args.input}' no existe.", file=sys.stderr)
        print("Por favor especifique un PDF válido con el argumento -i <ruta>.")
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

    # 3. Solicitar nuevos datos por consola
    datos_finales = solicitar_nuevos_datos(datos_extraidos)

    # 4. Generar el PDF final
    exito = generar_pdf_final(template_path, datos_finales, args.output)
    if exito:
        print(f"\n[FINALIZADO] Proceso completado exitosamente.")
        print(f"Puede abrir su nuevo archivo: {os.path.abspath(args.output)}")
    else:
        print("\n[FALLO] No se pudo completar la generación del PDF.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
