#!/usr/bin/env python3
"""
gui_app.py
Interfaz gráfica moderna (GUI) para digitalizar, editar y regenerar boletas PDF.
Editor / Publisher: fransdns de Hosaka Inc.
Diseñada siguiendo principios de UI/UX moderna:
 - Tipografía legible y ampliada para pantallas de laptop y monitores.
 - Paleta de colores contemporánea (Slate, Indigo y Emerald).
 - Diseño totalmente responsivo (resizeable) compatible con modo mitad de pantalla.
 - Contenedor con scroll vertical automático para garantizar accesibilidad en cualquier resolución.
 - Cálculo automático en tiempo real de IL TAX (7.00%) y TOTAL en base al SUBTOTAL.
"""

import os
import sys
import subprocess
import platform

# --- Configuración de DLLs para Windows (Python 3.8+ / WeasyPrint / PyInstaller) ---
if sys.platform == "win32":
    rutas_dll_candidatas = []
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        rutas_dll_candidatas.append(base_dir)
        rutas_dll_candidatas.append(os.path.join(base_dir, '_internal'))
    else:
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

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any

from invoice_generator import (
    crear_template_base,
    extraer_datos_pdf,
    generar_pdf_final,
    obtener_ruta_recurso,
    calcular_totales,
)


class ModernButton(tk.Button):
    """Botón estilizado moderno con soporte para esquinas limpias y estados hover."""
    def __init__(self, master=None, bg_color="#2563eb", hover_color="#1d4ed8",
                 fg_color="#ffffff", **kwargs):
        super().__init__(
            master,
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_color,
            activeforeground=fg_color,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            **kwargs
        )
        self.default_bg = bg_color
        self.hover_bg = hover_color
        self.bind("<Enter>", lambda e: self.configure(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.configure(bg=self.default_bg))


class InvoiceEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Editor y Generador de Boletas PDF — fransdns de Hosaka Inc.")
        
        # Tamaño inicial óptimo para laptop y soporte de resize
        self.geometry("880x790")
        self.minsize(580, 520)
        self.configure(bg="#f1f5f9")

        # Variables internas
        self.input_pdf_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar()
        self.template_path = tk.StringVar(value=obtener_ruta_recurso("invoice_template.html"))
        self.datos_base: Dict[str, Any] = {}
        self._updating_prices = False

        # --- Variables de campos dinámicos editables ---
        # 1. Datos del Cliente
        self.var_bill_to_name = tk.StringVar()
        self.var_ship_to_name = tk.StringVar()
        self.sync_ship_to = tk.BooleanVar(value=True)

        # 2. Datos del Producto
        self.var_item_description = tk.StringVar()
        self.var_model = tk.StringVar()
        self.var_serial_number = tk.StringVar()
        self.var_imei1 = tk.StringVar()
        self.var_imei2 = tk.StringVar()

        # 3. Metadatos de la Factura
        self.var_invoice_no = tk.StringVar()
        self.var_date = tk.StringVar()

        # 4. Valores Económicos y Totales
        self.var_unit_price = tk.StringVar()
        self.var_amount = tk.StringVar()
        self.var_subtotal = tk.StringVar()
        self.var_tax_amount = tk.StringVar(value="$0.00")
        self.var_total = tk.StringVar(value="$0.00")

        # Variables de resumen visual
        self.var_summary_client = tk.StringVar(value="—")
        self.var_summary_total = tk.StringVar(value="—")
        self.var_summary_item = tk.StringVar(value="—")

        # Variable de estado
        self.status_msg = tk.StringVar(value="Listo. Seleccione un archivo PDF para comenzar.")
        self.status_indicator = tk.StringVar(value="● Listo")

        # Vincular trazas para recálculo automático en tiempo real
        self.var_subtotal.trace_add("write", self._on_subtotal_changed)
        self.var_unit_price.trace_add("write", self._on_unit_price_changed)
        self.var_bill_to_name.trace_add("write", self._on_bill_to_changed)
        self.var_item_description.trace_add("write", self._on_item_desc_changed)

        # Configurar estilos ttk
        self._configurar_estilos()

        # Construir interfaz gráfica responsiva
        self._crear_interfaz_scrollable()

        # Asegurar plantilla base
        try:
            crear_template_base(self.template_path.get())
        except Exception as e:
            messagebox.showwarning("Advertencia", f"No se pudo inicializar la plantilla HTML: {e}")

        # Precargar boleta por defecto si existe en la carpeta
        default_sample = "INVOICE-15 PROMAX 256gb.pdf"
        if os.path.exists(default_sample):
            abs_sample = os.path.abspath(default_sample)
            self.input_pdf_path.set(abs_sample)
            self._procesar_pdf_seleccionado(abs_sample)

    def _configurar_estilos(self):
        """Configura la apariencia visual moderna con ttk.Style."""
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        BG_APP = "#f1f5f9"
        CARD_BG = "#ffffff"
        TEXT_MAIN = "#0f172a"
        TEXT_MUTED = "#64748b"

        self.style.configure(".", background=BG_APP, font=("Helvetica", 11))
        
        self.style.configure(
            "Card.TFrame",
            background=CARD_BG,
            relief=tk.SOLID,
            borderwidth=1,
        )

        self.style.configure(
            "SectionTitle.TLabel",
            background=CARD_BG,
            foreground=TEXT_MAIN,
            font=("Helvetica", 12, "bold")
        )

        self.style.configure(
            "FieldLabel.TLabel",
            background=CARD_BG,
            foreground="#334155",
            font=("Helvetica", 11, "bold")
        )

        self.style.configure(
            "Muted.TLabel",
            background=CARD_BG,
            foreground=TEXT_MUTED,
            font=("Helvetica", 10)
        )

    def _crear_interfaz_scrollable(self):
        """
        Crea una interfaz completamente adaptable a cambios de tamaño (responsive)
        mediante un Canvas con Scrollbar vertical que se ajusta automáticamente al ancho.
        """
        root_container = ttk.Frame(self)
        root_container.pack(fill=tk.BOTH, expand=True)

        # Barra de estado fija al fondo
        self._crear_barra_estado(root_container)

        # Canvas y scrollbar para el área de contenido
        canvas_frame = ttk.Frame(root_container)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#f1f5f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.configure(style="TFrame")

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self._vincular_scroll(self.canvas)
        self._vincular_scroll(self.scrollable_frame)

        self.canvas.configure(xscrollcommand=None, yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._construir_contenido(self.scrollable_frame)

    def _vincular_scroll(self, widget):
        """Vincula el scroll de la rueda del ratón en plataformas Linux/Windows/Mac."""
        def _on_mousewheel(event):
            if platform.system() == "Darwin":
                self.canvas.yview_scroll(int(-1 * event.delta), "units")
            elif platform.system() == "Windows":
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.canvas.yview_scroll(-2, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(2, "units")

        widget.bind("<MouseWheel>", _on_mousewheel)
        widget.bind("<Button-4>", _on_mousewheel)
        widget.bind("<Button-5>", _on_mousewheel)

    def _construir_contenido(self, parent):
        """Construye todos los bloques visuales compactos y espaciosos."""
        outer_pad = ttk.Frame(parent, padding="20 14 20 16")
        outer_pad.pack(fill=tk.BOTH, expand=True)

        # --- SECCIÓN 1: SELECCIÓN DE ENTRADA & RESUMEN ---
        card_input = tk.Frame(outer_pad, bg="#ffffff", bd=1, relief=tk.SOLID, padx=18, pady=14)
        card_input.pack(fill=tk.X, pady=(0, 14))

        lbl_sec1 = tk.Label(
            card_input,
            text="1. Boleta Original en PDF (Entrada)",
            font=("Helvetica", 12, "bold"),
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl_sec1.pack(anchor=tk.W, pady=(0, 8))

        frame_input_row = tk.Frame(card_input, bg="#ffffff")
        frame_input_row.pack(fill=tk.X)

        entry_input = tk.Entry(
            frame_input_row,
            textvariable=self.input_pdf_path,
            font=("Helvetica", 11),
            bg="#f8fafc",
            fg="#0f172a",
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor="#2563eb"
        )
        entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))

        btn_browse_input = ModernButton(
            frame_input_row,
            text="Examinar PDF...",
            bg_color="#334155",
            hover_color="#1e293b",
            font=("Helvetica", 11, "bold"),
            padx=16,
            pady=6,
            command=self._seleccionar_input_pdf
        )
        btn_browse_input.pack(side=tk.RIGHT)

        # Resumen rápido dinámico
        self.card_summary = tk.Frame(card_input, bg="#f8fafc", bd=1, relief=tk.SOLID, padx=14, pady=8)
        self.card_summary.pack(fill=tk.X, pady=(10, 0))

        sum_grid = tk.Frame(self.card_summary, bg="#f8fafc")
        sum_grid.pack(fill=tk.X)
        sum_grid.columnconfigure(1, weight=1)
        sum_grid.columnconfigure(3, weight=1)

        tk.Label(sum_grid, text="Cliente:", font=("Helvetica", 10, "bold"), fg="#475569", bg="#f8fafc").grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)
        tk.Label(sum_grid, textvariable=self.var_summary_client, font=("Helvetica", 10, "bold"), fg="#0f172a", bg="#f8fafc").grid(row=0, column=1, sticky=tk.W, padx=4, pady=2)

        tk.Label(sum_grid, text="Total Actual:", font=("Helvetica", 10, "bold"), fg="#475569", bg="#f8fafc").grid(row=0, column=2, sticky=tk.W, padx=4, pady=2)
        tk.Label(sum_grid, textvariable=self.var_summary_total, font=("Helvetica", 11, "bold"), fg="#059669", bg="#f8fafc").grid(row=0, column=3, sticky=tk.W, padx=4, pady=2)

        tk.Label(sum_grid, text="Producto:", font=("Helvetica", 10, "bold"), fg="#475569", bg="#f8fafc").grid(row=1, column=0, sticky=tk.W, padx=4, pady=2)
        tk.Label(sum_grid, textvariable=self.var_summary_item, font=("Helvetica", 10), fg="#0f172a", bg="#f8fafc").grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=4, pady=2)

        # --- SECCIÓN 2: CAMPOS A EDITAR ---
        card_fields = tk.Frame(outer_pad, bg="#ffffff", bd=1, relief=tk.SOLID, padx=18, pady=16)
        card_fields.pack(fill=tk.X, pady=(0, 14))

        lbl_sec2 = tk.Label(
            card_fields,
            text="2. Edición de Datos de la Boleta",
            font=("Helvetica", 12, "bold"),
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl_sec2.pack(anchor=tk.W, pady=(0, 10))

        # Helper para crear celda de entrada estilizada
        def _crear_campo(parent, row, col, label_text, var_obj, colspan=1):
            cell_frame = tk.Frame(parent, bg="#ffffff", padx=6, pady=5)
            cell_frame.grid(row=row, column=col, columnspan=colspan, sticky=tk.NSEW)

            lbl = tk.Label(
                cell_frame,
                text=label_text,
                font=("Helvetica", 10, "bold"),
                fg="#334155",
                bg="#ffffff"
            )
            lbl.pack(anchor=tk.W, pady=(0, 3))

            entry = tk.Entry(
                cell_frame,
                textvariable=var_obj,
                font=("Helvetica", 11),
                bg="#ffffff",
                fg="#0f172a",
                relief=tk.SOLID,
                bd=1,
                highlightthickness=1,
                highlightbackground="#cbd5e1",
                highlightcolor="#2563eb"
            )
            entry.pack(fill=tk.X, ipady=5)
            return entry

        # --- GRUPO A: DATOS DEL CLIENTE (BILL TO / SHIP TO) ---
        group_client = tk.LabelFrame(
            card_fields,
            text=" Datos del Cliente (BILL TO / SHIP TO) ",
            font=("Helvetica", 10, "bold"),
            fg="#2563eb",
            bg="#ffffff",
            bd=1,
            relief=tk.GROOVE,
            padx=10,
            pady=8
        )
        group_client.pack(fill=tk.X, pady=(0, 12))
        group_client.columnconfigure(0, weight=1)
        group_client.columnconfigure(1, weight=1)

        _crear_campo(group_client, 0, 0, "Nombre Cliente (BILL TO):", self.var_bill_to_name)
        _crear_campo(group_client, 0, 1, "Nombre Cliente (SHIP TO):", self.var_ship_to_name)

        chk_sync = tk.Checkbutton(
            group_client,
            text="Sincronizar automáticamente SHIP TO con BILL TO",
            variable=self.sync_ship_to,
            font=("Helvetica", 9),
            fg="#475569",
            bg="#ffffff",
            activebackground="#ffffff",
            command=self._on_sync_toggled
        )
        chk_sync.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=6, pady=(4, 0))

        # --- GRUPO B: DATOS DEL PRODUCTO & DISPOSITIVO ---
        group_prod = tk.LabelFrame(
            card_fields,
            text=" Datos del Producto y Dispositivo ",
            font=("Helvetica", 10, "bold"),
            fg="#2563eb",
            bg="#ffffff",
            bd=1,
            relief=tk.GROOVE,
            padx=10,
            pady=8
        )
        group_prod.pack(fill=tk.X, pady=(0, 12))
        group_prod.columnconfigure(0, weight=1)
        group_prod.columnconfigure(1, weight=1)

        # Fila completa para descripción de producto
        _crear_campo(group_prod, 0, 0, "Descripción del Producto (Description):", self.var_item_description, colspan=2)
        _crear_campo(group_prod, 1, 0, "Modelo (Model ej. MU693LL/A):", self.var_model)
        _crear_campo(group_prod, 1, 1, "Serial Number (Número de Serie):", self.var_serial_number)
        _crear_campo(group_prod, 2, 0, "IMEI 1 (15 dígitos):", self.var_imei1)
        _crear_campo(group_prod, 2, 1, "IMEI 2 (15 dígitos):", self.var_imei2)

        lbl_barcode_info = tk.Label(
            group_prod,
            text="★ Los códigos de barras Code 128 y el código QR se generan/actualizan automáticamente en el PDF.",
            font=("Helvetica", 9, "italic"),
            fg="#059669",
            bg="#ffffff"
        )
        lbl_barcode_info.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=6, pady=(4, 2))

        # --- GRUPO C: FACTURA, PRECIOS E IMPUESTOS (CÁLCULO AUTOMÁTICO 7%) ---
        group_prices = tk.LabelFrame(
            card_fields,
            text=" Precios, Subtotal y Totales (Cálculo Automático 7% de Impuesto) ",
            font=("Helvetica", 10, "bold"),
            fg="#2563eb",
            bg="#ffffff",
            bd=1,
            relief=tk.GROOVE,
            padx=10,
            pady=8
        )
        group_prices.pack(fill=tk.X, pady=(0, 4))
        group_prices.columnconfigure(0, weight=1)
        group_prices.columnconfigure(1, weight=1)
        group_prices.columnconfigure(2, weight=1)

        # Fila 0: Invoice No & Date
        _crear_campo(group_prices, 0, 0, "Invoice No (N° Factura):", self.var_invoice_no)
        _crear_campo(group_prices, 0, 1, "Date (Fecha de Emisión):", self.var_date, colspan=2)

        # Fila 1: Precios de la tabla
        _crear_campo(group_prices, 1, 0, "Unit Price (Precio Unitario):", self.var_unit_price)
        _crear_campo(group_prices, 1, 1, "Amount (Monto de Item):", self.var_amount)
        _crear_campo(group_prices, 1, 2, "SUBTOTAL (Base imponible):", self.var_subtotal)

        # Fila 2: Cuadros de Impuestos y Total calculados
        frame_tax = tk.Frame(group_prices, bg="#f8fafc", bd=1, relief=tk.SOLID, padx=8, pady=6)
        frame_tax.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, padx=6, pady=8)
        tk.Label(
            frame_tax,
            text="IL TAX ( 7.00% ) Calculado:",
            font=("Helvetica", 10, "bold"),
            fg="#334155",
            bg="#f8fafc"
        ).pack(side=tk.LEFT)
        tk.Label(
            frame_tax,
            textvariable=self.var_tax_amount,
            font=("Helvetica", 11, "bold"),
            fg="#1e293b",
            bg="#f8fafc"
        ).pack(side=tk.RIGHT)

        frame_tot = tk.Frame(group_prices, bg="#ecfdf5", bd=1, relief=tk.SOLID, padx=8, pady=6)
        frame_tot.grid(row=2, column=2, sticky=tk.NSEW, padx=6, pady=8)
        tk.Label(
            frame_tot,
            text="TOTAL Final:",
            font=("Helvetica", 10, "bold"),
            fg="#065f46",
            bg="#ecfdf5"
        ).pack(side=tk.LEFT)
        tk.Label(
            frame_tot,
            textvariable=self.var_total,
            font=("Helvetica", 12, "bold"),
            fg="#047857",
            bg="#ecfdf5"
        ).pack(side=tk.RIGHT)

        # --- SECCIÓN 3: ARCHIVO DE SALIDA ---
        card_output = tk.Frame(outer_pad, bg="#ffffff", bd=1, relief=tk.SOLID, padx=18, pady=14)
        card_output.pack(fill=tk.X, pady=(0, 16))

        lbl_sec3 = tk.Label(
            card_output,
            text="3. Archivo PDF de Destino (Salida)",
            font=("Helvetica", 12, "bold"),
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl_sec3.pack(anchor=tk.W, pady=(0, 8))

        frame_output_row = tk.Frame(card_output, bg="#ffffff")
        frame_output_row.pack(fill=tk.X)

        entry_output = tk.Entry(
            frame_output_row,
            textvariable=self.output_pdf_path,
            font=("Helvetica", 11),
            bg="#f8fafc",
            fg="#0f172a",
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor="#2563eb"
        )
        entry_output.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))

        btn_browse_output = ModernButton(
            frame_output_row,
            text="Guardar como...",
            bg_color="#334155",
            hover_color="#1e293b",
            font=("Helvetica", 11, "bold"),
            padx=16,
            pady=6,
            command=self._seleccionar_output_pdf
        )
        btn_browse_output.pack(side=tk.RIGHT)

        # --- SECCIÓN 4: BOTÓN DE ACCIÓN GENERAR ---
        btn_generate = ModernButton(
            outer_pad,
            text="⚙ GENERAR NUEVA BOLETA PDF",
            bg_color="#059669",
            hover_color="#047857",
            font=("Helvetica", 13, "bold"),
            pady=12,
            command=self._ejecutar_generacion
        )
        btn_generate.pack(fill=tk.X, pady=(0, 10))

    def _crear_barra_estado(self, parent):
        """Crea una barra de estado moderna con mención del editor/publisher."""
        status_bar = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID, padx=16, pady=8)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        lbl_indicator = tk.Label(
            status_bar,
            textvariable=self.status_indicator,
            font=("Helvetica", 10, "bold"),
            fg="#059669",
            bg="#ffffff"
        )
        lbl_indicator.pack(side=tk.LEFT, padx=(0, 8))

        lbl_msg = tk.Label(
            status_bar,
            textvariable=self.status_msg,
            font=("Helvetica", 10),
            fg="#475569",
            bg="#ffffff"
        )
        lbl_msg.pack(side=tk.LEFT, fill=tk.X, expand=True)

        lbl_pub = tk.Label(
            status_bar,
            text="fransdns de Hosaka Inc.",
            font=("Helvetica", 9, "bold"),
            fg="#64748b",
            bg="#ffffff"
        )
        lbl_pub.pack(side=tk.RIGHT, padx=(10, 0))

    # --- Lógica de Recálculo y Sincronización en Tiempo Real ---
    def _on_subtotal_changed(self, *args):
        if self._updating_prices:
            return
        self._updating_prices = True
        try:
            s_val = self.var_subtotal.get()
            s_fmt, tx_fmt, tot_fmt = calcular_totales(s_val)
            self.var_tax_amount.set(tx_fmt)
            self.var_total.set(tot_fmt)
            self.var_summary_total.set(tot_fmt)
        finally:
            self._updating_prices = False

    def _on_unit_price_changed(self, *args):
        if self._updating_prices:
            return
        u_val = self.var_unit_price.get().strip()
        if u_val:
            self._updating_prices = True
            try:
                # Sincronizar Amount y Subtotal con Unit Price si no han sido modificados
                self.var_amount.set(u_val)
                self.var_subtotal.set(u_val)
                s_fmt, tx_fmt, tot_fmt = calcular_totales(u_val)
                self.var_tax_amount.set(tx_fmt)
                self.var_total.set(tot_fmt)
                self.var_summary_total.set(tot_fmt)
            finally:
                self._updating_prices = False

    def _on_bill_to_changed(self, *args):
        nombre = self.var_bill_to_name.get()
        if self.sync_ship_to.get():
            self.var_ship_to_name.set(nombre)
        self.var_summary_client.set(nombre or "—")

    def _on_sync_toggled(self):
        if self.sync_ship_to.get():
            self.var_ship_to_name.set(self.var_bill_to_name.get())

    def _on_item_desc_changed(self, *args):
        self.var_summary_item.set(self.var_item_description.get() or "—")

    def _seleccionar_input_pdf(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar Boleta en PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.input_pdf_path.set(archivo)
            self._procesar_pdf_seleccionado(archivo)

    def _procesar_pdf_seleccionado(self, ruta_pdf: str):
        try:
            self.status_indicator.set("● Procesando")
            self.status_msg.set(f"Extrayendo datos de '{os.path.basename(ruta_pdf)}'...")
            self.update_idletasks()

            self.datos_base = extraer_datos_pdf(ruta_pdf)

            # Poblar campos editables dinámicamente
            self.var_bill_to_name.set(self.datos_base.get("bill_to_name", ""))
            self.var_ship_to_name.set(self.datos_base.get("ship_to_name", ""))
            self.var_item_description.set(self.datos_base.get("item_description", ""))
            self.var_model.set(self.datos_base.get("model", ""))
            self.var_serial_number.set(self.datos_base.get("serial_number", ""))
            self.var_imei1.set(self.datos_base.get("imei1", ""))
            self.var_imei2.set(self.datos_base.get("imei2", ""))
            self.var_invoice_no.set(self.datos_base.get("invoice_no", ""))
            self.var_date.set(self.datos_base.get("date", ""))

            # Precios
            subtotal_raw = self.datos_base.get("subtotal", "$773.50")
            unit_price_raw = self.datos_base.get("item_unit_price", subtotal_raw)
            amount_raw = self.datos_base.get("item_amount", subtotal_raw)

            self.var_unit_price.set(unit_price_raw)
            self.var_amount.set(amount_raw)
            self.var_subtotal.set(subtotal_raw)

            # Disparar cálculo de 7% de IL TAX y TOTAL
            s_fmt, tx_fmt, tot_fmt = calcular_totales(subtotal_raw)
            self.var_tax_amount.set(tx_fmt)
            self.var_total.set(tot_fmt)

            # Resumen visual
            self.var_summary_client.set(self.datos_base.get("bill_to_name", "") or "No detectado")
            self.var_summary_total.set(tot_fmt)
            self.var_summary_item.set(self.datos_base.get("item_description", "") or "No detectado")

            # Sugerir ruta de salida inteligente
            directorio = os.path.dirname(ruta_pdf)
            nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0]
            salida_sugerida = os.path.join(directorio, f"{nombre_base}_EDITADO.pdf")
            self.output_pdf_path.set(salida_sugerida)

            self.status_indicator.set("● Listo")
            self.status_msg.set("Datos extraídos correctamente con recálculo automático del 7% de impuesto.")
        except Exception as e:
            self.status_indicator.set("● Error")
            self.status_msg.set(f"Fallo al leer PDF: {e}")
            messagebox.showerror("Error de Lectura", f"No se pudo extraer información del archivo PDF:\n{e}")

    def _seleccionar_output_pdf(self):
        ruta_defecto = self.output_pdf_path.get() or "INVOICE_MODIFICADO.pdf"
        directorio = os.path.dirname(ruta_defecto) or "."
        nombre = os.path.basename(ruta_defecto)

        archivo = filedialog.asksaveasfilename(
            title="Guardar Nuevo PDF",
            initialdir=directorio,
            initialfile=nombre,
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            self.output_pdf_path.set(archivo)

    def _ejecutar_generacion(self):
        in_pdf = self.input_pdf_path.get().strip()
        out_pdf = self.output_pdf_path.get().strip()

        if not in_pdf or not os.path.exists(in_pdf):
            messagebox.showwarning("Atención", "Por favor seleccione un archivo PDF de entrada válido.")
            return

        if not out_pdf:
            messagebox.showwarning("Atención", "Por favor especifique la ruta de destino para el PDF generado.")
            return

        # Preparar diccionario combinado con todos los campos editables
        datos_finales = dict(self.datos_base)
        
        # Cliente
        datos_finales["bill_to_name"] = self.var_bill_to_name.get().strip()
        datos_finales["ship_to_name"] = self.var_ship_to_name.get().strip()
        
        # Producto
        datos_finales["item_description"] = self.var_item_description.get().strip()
        datos_finales["model"] = self.var_model.get().strip()
        datos_finales["serial_number"] = self.var_serial_number.get().strip()
        datos_finales["imei1"] = self.var_imei1.get().strip()
        datos_finales["imei2"] = self.var_imei2.get().strip()
        datos_finales["invoice_no"] = self.var_invoice_no.get().strip()
        datos_finales["date"] = self.var_date.get().strip()

        # Precios e Impuestos
        u_price = self.var_unit_price.get().strip()
        if not u_price.startswith("$"):
            u_price = f"${u_price}" if u_price else "$0.00"
        datos_finales["item_unit_price"] = u_price

        amt = self.var_amount.get().strip()
        if not amt.startswith("$"):
            amt = f"${amt}" if amt else u_price
        datos_finales["item_amount"] = amt

        # Calcular con precisión el 7% de IL TAX y TOTAL
        s_fmt, tx_fmt, tot_fmt = calcular_totales(self.var_subtotal.get().strip())
        datos_finales["subtotal"] = s_fmt
        datos_finales["tax_label"] = "IL TAX ( 7.00% )"
        datos_finales["tax_amount"] = tx_fmt
        datos_finales["total"] = tot_fmt

        # Generar PDF
        self.status_indicator.set("● Generando")
        self.status_msg.set("Compilando PDF con nuevos valores y totales recalculados...")
        self.update_idletasks()

        tpl_path = self.template_path.get()
        if not os.path.exists(tpl_path):
            crear_template_base(tpl_path)

        exito = generar_pdf_final(tpl_path, datos_finales, out_pdf)

        if exito:
            self.status_indicator.set("● Exitoso")
            self.status_msg.set(f"¡PDF generado con éxito en: {os.path.basename(out_pdf)}!")
            resp = messagebox.askyesno(
                "PDF Generado Exitosamente",
                f"La nueva boleta ha sido creada en:\n\n{out_pdf}\n\n¿Desea abrir el archivo PDF ahora?"
            )
            if resp:
                self._abrir_archivo(out_pdf)
        else:
            self.status_indicator.set("● Falló")
            self.status_msg.set("Ocurrió un error al compilar el PDF con WeasyPrint.")
            messagebox.showerror(
                "Error al Generar",
                "Hubo un fallo al compilar el PDF con WeasyPrint. Verifique los registros en la terminal."
            )

    def _abrir_archivo(self, ruta: str):
        try:
            if platform.system() == "Windows":
                os.startfile(ruta)
            elif platform.system() == "Darwin":
                subprocess.run(["open", ruta], check=False)
            else:
                subprocess.run(["xdg-open", ruta], check=False)
        except Exception as e:
            messagebox.showwarning("Aviso", f"No se pudo abrir el archivo automáticamente: {e}")


def run_gui():
    app = InvoiceEditorApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
