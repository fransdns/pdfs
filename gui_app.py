#!/usr/bin/env python3
"""
gui_app.py
Interfaz gráfica moderna (GUI) para digitalizar, editar y regenerar boletas PDF.
Diseñada siguiendo principios de UI/UX moderna:
 - Tipografía legible y ampliada para pantallas de laptop y monitores.
 - Paleta de colores contemporánea (Slate, Indigo y Emerald) estilo software profesional.
 - Diseño totalmente responsivo (resizeable) compatible con modo mitad de pantalla (split screen).
 - Contenedor con scroll vertical automático para garantizar accesibilidad en cualquier resolución.
"""

import os
import sys
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any

from invoice_generator import (
    crear_template_base,
    extraer_datos_pdf,
    generar_pdf_final,
    obtener_ruta_recurso,
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

        self.title("Sistema Profesional de Boletas e Invoices PDF")
        
        # Tamaño inicial óptimo para laptop y soporte de resize
        self.geometry("860x780")
        self.minsize(580, 520)
        self.configure(bg="#f1f5f9")

        # Variables internas
        self.input_pdf_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar()
        self.template_path = tk.StringVar(value=obtener_ruta_recurso("invoice_template.html"))
        self.datos_base: Dict[str, Any] = {}

        # Variables de campos dinámicos editables
        self.var_invoice_no = tk.StringVar()
        self.var_date = tk.StringVar()
        self.var_model = tk.StringVar()
        self.var_imei1 = tk.StringVar()
        self.var_imei2 = tk.StringVar()
        self.var_serial_number = tk.StringVar()

        # Variables de resumen visual
        self.var_summary_client = tk.StringVar(value="—")
        self.var_summary_total = tk.StringVar(value="—")
        self.var_summary_item = tk.StringVar(value="—")

        # Variable de estado
        self.status_msg = tk.StringVar(value="Listo. Seleccione un archivo PDF para comenzar.")
        self.status_indicator = tk.StringVar(value="● Listo")

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

        # Colores de la paleta moderna (Tailwind Slate / Blue / Emerald)
        BG_APP = "#f1f5f9"
        CARD_BG = "#ffffff"
        TEXT_MAIN = "#0f172a"
        TEXT_MUTED = "#64748b"

        self.style.configure(".", background=BG_APP, font=("Helvetica", 11))
        
        # Estilo para marcos tipo 'Card'
        self.style.configure(
            "Card.TFrame",
            background=CARD_BG,
            relief=tk.SOLID,
            borderwidth=1,
        )

        # Encabezados de sección
        self.style.configure(
            "SectionTitle.TLabel",
            background=CARD_BG,
            foreground=TEXT_MAIN,
            font=("Helvetica", 12, "bold")
        )

        # Etiquetas de campos
        self.style.configure(
            "FieldLabel.TLabel",
            background=CARD_BG,
            foreground="#334155",
            font=("Helvetica", 11, "bold")
        )

        # Textos secundarios y de ayuda
        self.style.configure(
            "Muted.TLabel",
            background=CARD_BG,
            foreground=TEXT_MUTED,
            font=("Helvetica", 10)
        )

        # Badge de resumen
        self.style.configure(
            "BadgeLabel.TLabel",
            background="#f8fafc",
            foreground="#1e293b",
            font=("Helvetica", 10, "bold")
        )

    def _crear_interfaz_scrollable(self):
        """
        Crea una interfaz completamente adaptable a cambios de tamaño (responsive)
        mediante un Canvas con Scrollbar vertical que se ajusta automáticamente al ancho.
        """
        # Contenedor raíz
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

        # Actualizar región de scroll al cambiar tamaño
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Mantener el ancho del frame sincronizado con el ancho del canvas (Responsive)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        # Soporte para rueda del ratón
        self._vincular_scroll(self.canvas)
        self._vincular_scroll(self.scrollable_frame)

        self.canvas.configure(xscrollcommand=None, yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Construir contenido dentro del frame scrollable
        self._construir_contenido(self.scrollable_frame)

    def _vincular_scroll(self, widget):
        """Vincula el scroll de la rueda del ratón en plataformas Linux/Windows/Mac."""
        def _on_mousewheel(event):
            if platform.system() == "Darwin":
                self.canvas.yview_scroll(int(-1 * event.delta), "units")
            elif platform.system() == "Windows":
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                # Linux
                if event.num == 4:
                    self.canvas.yview_scroll(-2, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(2, "units")

        widget.bind("<MouseWheel>", _on_mousewheel)
        widget.bind("<Button-4>", _on_mousewheel)
        widget.bind("<Button-5>", _on_mousewheel)

    def _construir_contenido(self, parent):
        """Construye todos los bloques visuales con diseño espacioso y moderno."""
        # Margen exterior
        outer_pad = ttk.Frame(parent, padding="24 20 24 24")
        outer_pad.pack(fill=tk.BOTH, expand=True)

        # --- ENCABEZADO PRINCIPAL ---
        header_card = tk.Frame(outer_pad, bg="#ffffff", bd=1, relief=tk.SOLID, padx=20, pady=18)
        header_card.pack(fill=tk.X, pady=(0, 16))

        title_lbl = tk.Label(
            header_card,
            text="Generador & Editor Profesional de Boletas PDF",
            font=("Helvetica", 16, "bold"),
            fg="#0f172a",
            bg="#ffffff"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            header_card,
            text="Extraiga datos automáticamente, edite campos clave (IMEI, Serial, Fechas) y regenere una boleta idéntica con acabado perfecto.",
            font=("Helvetica", 11),
            fg="#64748b",
            bg="#ffffff",
            wraplength=760,
            justify=tk.LEFT
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(4, 0))

        # --- SECCIÓN 1: SELECCIÓN DE ENTRADA ---
        card_input = tk.Frame(outer_pad, bg="#ffffff", bd=1, relief=tk.SOLID, padx=20, pady=16)
        card_input.pack(fill=tk.X, pady=(0, 16))

        lbl_sec1 = tk.Label(
            card_input,
            text="1. Boleta Original en PDF (Entrada)",
            font=("Helvetica", 13, "bold"),
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl_sec1.pack(anchor=tk.W, pady=(0, 10))

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

        # --- SECCIÓN RESUMEN RÁPIDO (CARD DE DETALLES EXTRAÍDOS) ---
        self.card_summary = tk.Frame(card_input, bg="#f8fafc", bd=1, relief=tk.SOLID, padx=14, pady=10)
        self.card_summary.pack(fill=tk.X, pady=(12, 0))

        sum_grid = tk.Frame(self.card_summary, bg="#f8fafc")
        sum_grid.pack(fill=tk.X)
        sum_grid.columnconfigure(1, weight=1)
        sum_grid.columnconfigure(3, weight=1)

        tk.Label(sum_grid, text="Cliente Detectado:", font=("Helvetica", 10, "bold"), fg="#475569", bg="#f8fafc").grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)
        tk.Label(sum_grid, textvariable=self.var_summary_client, font=("Helvetica", 10), fg="#0f172a", bg="#f8fafc").grid(row=0, column=1, sticky=tk.W, padx=4, pady=2)

        tk.Label(sum_grid, text="Total Detectado:", font=("Helvetica", 10, "bold"), fg="#475569", bg="#f8fafc").grid(row=0, column=2, sticky=tk.W, padx=4, pady=2)
        tk.Label(sum_grid, textvariable=self.var_summary_total, font=("Helvetica", 10, "bold"), fg="#059669", bg="#f8fafc").grid(row=0, column=3, sticky=tk.W, padx=4, pady=2)

        tk.Label(sum_grid, text="Producto:", font=("Helvetica", 10, "bold"), fg="#475569", bg="#f8fafc").grid(row=1, column=0, sticky=tk.W, padx=4, pady=2)
        tk.Label(sum_grid, textvariable=self.var_summary_item, font=("Helvetica", 10), fg="#0f172a", bg="#f8fafc").grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=4, pady=2)

        # --- SECCIÓN 2: CAMPOS A EDITAR ---
        card_fields = tk.Frame(outer_pad, bg="#ffffff", bd=1, relief=tk.SOLID, padx=20, pady=18)
        card_fields.pack(fill=tk.X, pady=(0, 16))

        lbl_sec2 = tk.Label(
            card_fields,
            text="2. Modificar Datos Clave",
            font=("Helvetica", 13, "bold"),
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl_sec2.pack(anchor=tk.W)

        lbl_sec2_sub = tk.Label(
            card_fields,
            text="Edite los valores que desea sustituir. Los demás datos (cliente, totales, banco) se conservan automáticamente con espaciado perfecto.",
            font=("Helvetica", 10),
            fg="#64748b",
            bg="#ffffff"
        )
        lbl_sec2_sub.pack(anchor=tk.W, pady=(2, 14))

        # Rejilla responsiva de campos (2 columnas)
        grid_fields = tk.Frame(card_fields, bg="#ffffff")
        grid_fields.pack(fill=tk.X)
        grid_fields.columnconfigure(0, weight=1)
        grid_fields.columnconfigure(1, weight=1)

        # Helper para crear celda de entrada estilizada
        def _crear_campo(parent, row, col, label_text, var_obj, placeholder=""):
            cell_frame = tk.Frame(parent, bg="#ffffff", padx=8, pady=6)
            cell_frame.grid(row=row, column=col, sticky=tk.NSEW)

            lbl = tk.Label(
                cell_frame,
                text=label_text,
                font=("Helvetica", 11, "bold"),
                fg="#334155",
                bg="#ffffff"
            )
            lbl.pack(anchor=tk.W, pady=(0, 4))

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
            entry.pack(fill=tk.X, ipady=6)
            return entry

        # Fila 0
        _crear_campo(grid_fields, 0, 0, "Invoice No (N° Factura):", self.var_invoice_no)
        _crear_campo(grid_fields, 0, 1, "Date (Fecha de Emisión):", self.var_date)

        # Fila 1
        _crear_campo(grid_fields, 1, 0, "Model (Modelo ej. MU693LL/A):", self.var_model)
        _crear_campo(grid_fields, 1, 1, "Serial Number (Número de Serie):", self.var_serial_number)

        # Fila 2
        _crear_campo(grid_fields, 2, 0, "IMEI 1 (15 dígitos):", self.var_imei1)
        _crear_campo(grid_fields, 2, 1, "IMEI 2 (15 dígitos):", self.var_imei2)

        # --- SECCIÓN 3: ARCHIVO DE SALIDA ---
        card_output = tk.Frame(outer_pad, bg="#ffffff", bd=1, relief=tk.SOLID, padx=20, pady=16)
        card_output.pack(fill=tk.X, pady=(0, 20))

        lbl_sec3 = tk.Label(
            card_output,
            text="3. Archivo PDF de Destino (Salida)",
            font=("Helvetica", 13, "bold"),
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl_sec3.pack(anchor=tk.W, pady=(0, 10))

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
        """Crea una barra de estado moderna fijada en la parte inferior."""
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

            # Rellenar los campos editables
            self.var_invoice_no.set(self.datos_base.get("invoice_no", ""))
            self.var_date.set(self.datos_base.get("date", ""))
            self.var_model.set(self.datos_base.get("model", ""))
            self.var_imei1.set(self.datos_base.get("imei1", ""))
            self.var_imei2.set(self.datos_base.get("imei2", ""))
            self.var_serial_number.set(self.datos_base.get("serial_number", ""))

            # Actualizar card de resumen rápido
            cliente = self.datos_base.get("bill_to_name", "") or "No detectado"
            total = self.datos_base.get("total", "") or "No detectado"
            item = self.datos_base.get("item_description", "") or "No detectado"

            self.var_summary_client.set(cliente)
            self.var_summary_total.set(total)
            self.var_summary_item.set(item)

            # Sugerir ruta de salida inteligente
            directorio = os.path.dirname(ruta_pdf)
            nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0]
            salida_sugerida = os.path.join(directorio, f"{nombre_base}_EDITADO.pdf")
            self.output_pdf_path.set(salida_sugerida)

            self.status_indicator.set("● Listo")
            self.status_msg.set("Datos extraídos correctamente con espaciado normalizado.")
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

        # Preparar diccionario combinado
        datos_finales = dict(self.datos_base)
        datos_finales["invoice_no"] = self.var_invoice_no.get().strip()
        datos_finales["date"] = self.var_date.get().strip()
        datos_finales["model"] = self.var_model.get().strip()
        datos_finales["imei1"] = self.var_imei1.get().strip()
        datos_finales["imei2"] = self.var_imei2.get().strip()
        datos_finales["serial_number"] = self.var_serial_number.get().strip()

        # Generar PDF
        self.status_indicator.set("● Generando")
        self.status_msg.set("Compilando PDF con espaciado y márgenes corregidos...")
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
