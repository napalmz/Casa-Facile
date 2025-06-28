#!/usr/bin/env python3
import tkinter as tk
import calendar
from tkinter import ttk, messagebox, filedialog
import datetime
import json
import os
import sys
import psutil
import uuid
import importlib.util
import subprocess
import shutil
import ctypes
import urllib.request
import platform
from tkinter import Toplevel
from tkcalendar import Calendar, DateEntry
import shutil
import hashlib


# URL del file su GitHub (sostituiscilo con il tuo link reale)
GITHUB_FILE_URL = "https://raw.githubusercontent.com/Renato-4132/Casa-Facile/refs/heads/main/Casa%20Facile.pyw"
NOME_FILE = "Casa Facile.pyw"  # Nome del file da salvare

EXPORTDB_DIR = "export"
DB_DIR = "db"
DB_FILE = os.path.join(DB_DIR, "spese_db.json")
DATI_FILE = os.path.join(DB_DIR,"rubrica.json")
UTENZE_DB = os.path.join(DB_DIR, "utenze_db.json")
SALDO_FILE = os.path.join(DB_DIR, "saldo_db.json")
EXPORT_FILES = "export"
EXP_DB = os.path.join(DB_DIR, EXPORTDB_DIR)
PW_FILE = os.path.join(DB_DIR, "password.json")

DAYS_THRESHOLD = 25
VERSION = "4.7"
class GestioneSpese(tk.Tk):
    CATEGORIA_RIMOSSA = "Categoria Rimossa"

    def __init__(self):
        super().__init__()
        self.withdraw()
        if not self.gestione_login():
            return  # oppure self.destroy(); exit()
        self.deiconify()
   
        self.title("Casa Facile pro v.{VERSION}")
        self.resizable(True, True)

        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        if not os.path.exists(EXP_DB):
            os.makedirs(EXP_DB)
            
        backup_incrementale(DB_FILE)
        backup_incrementale(SALDO_FILE)
        backup_incrementale(DATI_FILE)
        backup_incrementale(UTENZE_DB)

        self.aggiorna_titolo_finestra()

        initial_width = 1366
        initial_height = 720
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self._window_geometry = None
        self.load_window_geometry()

        if self._window_geometry:
            self.geometry(self._window_geometry)
        else:
            x = (screen_width // 2) - (initial_width // 2)
            y = (screen_height // 2) - (initial_height // 2)
            self.geometry(f"{initial_width}x{initial_height}+{x}+{y}")

        self.update_idletasks()
        self.lift()
        self.focus_force()
        self.deiconify()

        
        
        self.categorie = ["Generica", self.CATEGORIA_RIMOSSA]
        self.categorie_tipi = {"Generica": "Uscita", self.CATEGORIA_RIMOSSA: "Uscita"}
        self.spese = {}
        self.ricorrenze = {}  
        self.modifica_idx = None
        self.stats_refdate = datetime.date.today()
        self.load_db()
        topbar = ttk.Frame(self)
        topbar.pack(fill=tk.X, pady=4)
        
        style = ttk.Style()
        #style.theme_use('clam')
        
        # Definizione dei colori dei pulsanti aggiornati
        style.configure("Salva.TButton", background="#FF6666", foreground="black")  # Salva - rosso chiaro
        style.configure("Importa.TButton", background="#90EE90", foreground="black")  # Importa - verde chiaro
        style.configure("Esporta.TButton", background="#FFA500", foreground="black")  # Esporta - arancione chiaro
        style.configure("Reset.TButton", background="red", foreground="black")  # Reset Database - rosso
        style.configure("Info.TButton", background="green", foreground="black")  # Info - verde
        style.configure("Saldo.TButton", background="#FFA500", foreground="black")  # Saldo Conto - arancione chiaro
        style.configure("Confronta.TButton", background="yellow", foreground="black")  # Confronta - giallo
        style.configure("Utenze.TButton", background="#90EE90", foreground="black")  # Utenze - verde chiaro
        style.configure("Rubrica.TButton", background="#90EE90", foreground="black")  # Rubrica - verde chiaro
        style.configure("Stampa.TButton", background="#90EE90", foreground="black")  # Stampa - verde chiaro
        style.configure("Cerca.TButton", background="yellow", foreground="black")  # Stampa - verde chiaro
        style.configure("TM.TButton", background="yellow", foreground="black")  # Stampa - verde chiaro
        style.configure("Gruppi.TButton", background="yellow", foreground="black")  # Stampa - verde chiaro
        
        self.btn_save = ttk.Button(topbar, text="💾 Salva", command=self.save_db_and_notify, style="Salva.TButton")
        self.btn_save.pack(side=tk.RIGHT, padx=6)

        ttk.Button(topbar, text="📤 Importa DB", command=self.import_db, style="Importa.TButton").pack(side=tk.RIGHT, padx=1)
        ttk.Button(topbar, text="📤 Esporta DB", command=self.export_db, style="Esporta.TButton").pack(side=tk.RIGHT, padx=1)
        ttk.Button(topbar, text="🔄 Reset DB", command=self.show_reset_dialog, style="Reset.TButton").pack(side=tk.RIGHT, padx=1)

        ttk.Button(topbar, text="ℹ️ Info", command=self.show_info_app, style="Info.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="💰 Saldo", command=self.open_saldo_conto, style="Saldo.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="🔍 Confronta", command=self.open_compare_window, style="Confronta.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="👤 Utenze", command=self.utenze, style="Utenze.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="📅 Rubrica", command=self.rubrica_app, style="Rubrica.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="📥 Stampa", command=self.anteprima_e_stampa_txt, style="Stampa.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="📥 Cerca", command=self.cerca_operazioni, style="Cerca.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="📥 T.M.", command=self.time_machine, style="TM.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(topbar, text="🔍 Aggrega", command=self.gruppo_categorie, style="Gruppi.TButton").pack(side=tk.LEFT, padx=1)
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        cal_frame = ttk.Frame(main_frame)
        cal_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        today = datetime.date.today()
        
        self.cal = Calendar(
            cal_frame,
            selectmode="day",
            year=today.year,
            month=today.month,
            day=today.day,
            date_pattern="dd-mm-yyyy",
            locale="it_IT",
            font=("Arial", 10),
            weekendbackground="lightblue",
            weekendforeground="darkblue",
            selectbackground="blue"
        )
        
        
        self.cal.pack(fill="both", expand=True)
        # Legenda colori calendario
        legenda = ttk.Frame(cal_frame)
        legenda.pack(pady=(4, 0))

        ttk.Label(legenda, text="Entrata", background="lightgreen", width=10, anchor="center", font=("Arial", 7)).pack(side="left", padx=3)
        ttk.Label(legenda, text="Uscita", background="lightcoral", width=10, anchor="center", font=("Arial", 7)).pack(side="left", padx=3)
        ttk.Label(legenda, text="Entrata + Uscita", background="khaki", width=16, anchor="center", font=("Arial", 7)).pack(side="left", padx=3)
        ttk.Label(legenda, text="Oggi", background="gold", width=8, anchor="center", font=("Arial", 7)).pack(side="left", padx=3)
        ttk.Label(legenda, text="Weekend", background="lightblue", font=("Arial", 7), width=10, anchor="center").pack(side="left", padx=3)
        
        # Evidenzia oggi in giallo
        oggi = datetime.date.today()
        self.cal.calevent_create(oggi, "Oggi", "today")
        self.cal.tag_config("today", background="gold", foreground="black")

        # Ingrandisce il font di mese/anno in alto
        try:
            self.cal._header["font"] = ("Arial", 14, "bold")
        except:
            pass

        
        self.cal.pack(fill="x", expand=True, padx=10, pady=5)
        self.cal.tag_config("verde", background="lightgreen")
        self.cal.tag_config("rosso", background="lightcoral")
        self.cal.tag_config("misto", background="khaki")

       ########### #self.cal.bind("<<CalendarSelected>>", lambda e: self.update_stats())
        self.cal.bind("<<CalendarSelected>>", self.on_calendar_change)
        self.colora_giorni_spese()

        # Stile unico giallo (lo definisci una volta sola)
       
        style.configure("Yellow.TButton", background="yellow", foreground="black", font=("Arial", 8))

        # Frame orizzontale per contenere entrambi i bottoni
        barra_azione = ttk.Frame(cal_frame)
        barra_azione.pack(fill="x", pady=(6, 0))

        # Pulsante “Oggi”
        btn_today = ttk.Button(
            barra_azione,
            text="↺ Torna alla data odierna",
            width=25,
            command=self.goto_today,
            style="Yellow.TButton"
        )
        btn_today.pack(side="left", padx=(0, 5))
        
        style.map("Custom.TCombobox",
          foreground=[("disabled", "black")],
          fieldbackground=[("disabled", "lightgray")])

        
        select_frame = ttk.Frame(cal_frame)
        select_frame.pack(pady=(6, 0), fill=tk.X)
        self.estratto_month_var = tk.StringVar(value=f"{today.month:02d}")
        current_year = today.year
        years = [str(y) for y in range(current_year - 15, current_year + 11)]
        months = [
            "01 - Gennaio", "02 - Febbraio", "03 - Marzo", "04 - Aprile", "05 - Maggio", "06 - Giugno",
            "07 - Luglio", "08 - Agosto", "09 - Settembre", "10 - Ottobre", "11 - Novembre", "12 - Dicembre"
        ]

        ttk.Label(select_frame, text="📅 Mese:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.cb_estratto_month = ttk.Combobox(select_frame, values=months, width=12, font=("Arial", 10, "bold"),
                                      textvariable=self.estratto_month_var, state="disabled", style="Custom.TCombobox")
        self.cb_estratto_month.grid(row=0, column=1, sticky="w", padx=(0, 4))
        self.cb_estratto_month.current(today.month - 1)
        ttk.Label(select_frame, text="← Mese visualizzato (seleziona dal calendario)", font=("Arial", 10, "bold")).grid(
            row=0, column=2, sticky="w", padx=2)

        ttk.Label(select_frame, text="📆 Anno:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="e", padx=2, pady=2)
        self.estratto_year_var = tk.StringVar(value=str(today.year))
        self.cb_estratto_year = ttk.Combobox(select_frame, values=years, width=12, font=("Arial", 10, "bold"),
                                     textvariable=self.estratto_year_var, state="disabled", style="Custom.TCombobox")
        self.cb_estratto_year.grid(row=1, column=1, sticky="w", padx=(0, 4))
        ttk.Label(select_frame, text="← Anno visualizzato (seleziona dal calendario)", font=("Arial", 10, "bold")).grid(
            row=1, column=2, sticky="w", padx=2)
   
        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))

        self.totalizzatore_frame = ttk.LabelFrame(cal_frame, text="⚙️ Riepilogo Anno corrente", style="RedBold.TLabelframe")
        self.totalizzatore_frame.pack(fill=tk.X, padx=2, pady=(8, 8))
        
        self.totalizzatore_entrate_label = ttk.Label(self.totalizzatore_frame, text="Totale Entrate: 0.00 €", foreground="green",
        font=("Arial", 10, "bold"))
        self.totalizzatore_entrate_label.pack(anchor="w", padx=6, pady=(2,0))
        self.totalizzatore_uscite_label = ttk.Label(self.totalizzatore_frame, text="Totale Uscite: 0.00 €", foreground="red", font=("Arial", 10, "bold"))
        self.totalizzatore_uscite_label.pack(anchor="w", padx=6, pady=(2,0))
        self.totalizzatore_diff_label = ttk.Label(self.totalizzatore_frame, text="Differenza: 0.00 €", foreground="blue", font=("Arial", 10, "bold"))
        self.totalizzatore_diff_label.pack(anchor="w", padx=6, pady=(2,4))
        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))

        self.totalizzatore_mese_frame = ttk.LabelFrame(cal_frame, text="⚙️ Riepilogo Mese corrente", style="RedBold.TLabelframe")
        self.totalizzatore_mese_frame.pack(fill=tk.X, padx=2, pady=(8, 8))

        self.totalizzatore_mese_entrate_label = ttk.Label(self.totalizzatore_mese_frame, text="Totale Entrate mese: 0.00 €", foreground="green", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_entrate_label.pack(anchor="w", padx=6, pady=(2,0))
        self.totalizzatore_mese_uscite_label = ttk.Label(self.totalizzatore_mese_frame, text="Totale Uscite mese: 0.00 €", foreground="red", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_uscite_label.pack(anchor="w", padx=6, pady=(2,0))
        self.totalizzatore_mese_diff_label = ttk.Label(self.totalizzatore_mese_frame, text="Differenza mese: 0.00 €", foreground="blue", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_diff_label.pack(anchor="w", padx=6, pady=(2,4))
        self.spese_mese_frame = ttk.LabelFrame(cal_frame, text="Riepilogo mese per data", style="RedBold.TLabelframe")
        self.spese_mese_frame.pack(fill=tk.BOTH, expand=False, padx=2, pady=(2,4))
        self.spese_mese_tree = ttk.Treeview(
            self.spese_mese_frame,
            columns=("Data", "Categoria", "Descrizione", "Importo", "Tipo"),
            show="headings",
            height=10  # <-- Modificato qui da 10 a 5
        )
        self.spese_mese_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.spese_mese_tree.heading("Data", text="Data")
        self.spese_mese_tree.heading("Categoria", text="Categoria")
        self.spese_mese_tree.heading("Descrizione", text="Descrizione")
        self.spese_mese_tree.heading("Importo", text="Importo (€)")
        self.spese_mese_tree.heading("Tipo", text="Tipo")
        self.spese_mese_tree.column("Data", width=90, anchor="center")
        self.spese_mese_tree.column("Categoria", width=90, anchor="center")
        self.spese_mese_tree.column("Descrizione", width=120, anchor="w")
        self.spese_mese_tree.column("Importo", width=80, anchor="e")
        self.spese_mese_tree.column("Tipo", width=60, anchor="center")
        self.spese_mese_tree.tag_configure('entrata', foreground='green')
        self.spese_mese_tree.tag_configure('uscita', foreground='red')
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))
        stat_frame = ttk.LabelFrame(right_frame, text="⚙️ Statistiche Spese", style="RedBold.TLabelframe")
        stat_frame.pack(fill=tk.X, padx=2, pady=(8, 8))

        mode_frame = ttk.Frame(stat_frame)
        mode_frame.pack(anchor="w", padx=6, pady=(4,0), fill=tk.X)
        self.stats_mode = tk.StringVar(value="giorno")
       
        # Definizione degli stili con i colori richiesti
        style.configure("Giorno.TButton", background="#00FFFF", foreground="black")  # Giorno - verde acqua, testo nero
        style.configure("Mese.TButton", background="#00FFFF", foreground="black")  # Mese - verde acqua, testo nero
        style.configure("Anno.TButton", background="#00FFFF", foreground="black")  # Anno - verde acqua, testo nero
        style.configure("Totali.TButton", background="#FF6666", foreground="black")  # Totali - rosso chiaro, testo nero
        style.configure("Categoria.TButton", background="#90EE90", foreground="black")  # Categoria - verde chiaro, testo nero
        style.configure("Esporta.TButton", background="#ADD8E6", foreground="black")  # Esporta giorno/mese/anno - azzurro

        ttk.Button(mode_frame, text="📅 Giorno", command=lambda: self.set_stats_mode("giorno"), width=9, style="Giorno.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(mode_frame, text="📅 Mese", command=lambda: self.set_stats_mode("mese"), width=9, style="Mese.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(mode_frame, text="📅 Anno", command=lambda: self.set_stats_mode("anno"), width=9, style="Anno.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(mode_frame, text="📅 Totali", command=lambda: self.set_stats_mode("totali"), width=9, style="Totali.TButton").pack(side=tk.LEFT, padx=1)

        mode_frame_right = ttk.Frame(mode_frame)
        mode_frame_right.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        ttk.Button(mode_frame_right, text="⏰ Estrai Giorno", command=self.export_giorno_forzato, style="Esporta.TButton").pack(side=tk.RIGHT, padx=1)
        ttk.Button(mode_frame_right, text="⏰ Estrai Mese", command=self.export_month_detail, style="Esporta.TButton").pack(side=tk.RIGHT, padx=1)
        ttk.Button(mode_frame_right, text="⏰ Estrai Anno", command=self.export_anno_dettagliato, style="Esporta.TButton").pack(side=tk.RIGHT, padx=1)

        ttk.Button(mode_frame, text="🔍 Categoria", command=self.open_analisi_categoria, width=12, style="Categoria.TButton").pack(side=tk.LEFT, padx=2)

        self.stats_label = ttk.Label(stat_frame, text="")
        self.stats_label.pack(anchor="w", padx=6, pady=(2,0))
        self.totali_label = ttk.Label(stat_frame, text="", font=("Arial", 11, "bold"))
        self.totali_label.pack(anchor="w", padx=6, pady=(2,0))
        self.stats_table = ttk.Treeview(stat_frame, columns=("A","B","C","D","E","F"), show="headings", height=8)
        self.stats_table.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.stats_table.column("A", width=10, anchor="center")      # Data o Categoria
        self.stats_table.column("B", width=18, anchor="center")      # Categoria o Totale Categoria (€)
        self.stats_table.column("C", width=20, anchor="w")           # Descrizione o Tipo
        self.stats_table.column("D", width=10, anchor="e")           # Importo (€)
        self.stats_table.column("E", width=10, anchor="center")      # Tipo
        self.stats_table.column("F", width=10, anchor="center")      # Modifica
        self.set_stats_mode("giorno")
        self.stats_table.tag_configure("uscita", foreground="red")
        self.stats_table.tag_configure("entrata", foreground="green")
        self.stats_table.bind('<ButtonRelease-1>', self.on_table_click)
        
        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))
        form_frame = ttk.LabelFrame(right_frame, text="⚙️ Inserisci/Modifica Spesa/Entrata", style="RedBold.TLabelframe")
        form_frame.pack(fill=tk.X, padx=2, pady=(8, 8))

        row = 0
        ttk.Label(form_frame, text="Data spesa:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="e")

        self.data_spesa_var = tk.StringVar(value=today.strftime("%d-%m-%Y"))

        data_frame = ttk.Frame(form_frame)
        data_frame.grid(row=row, column=1, columnspan=2, sticky="w")

        self.data_spesa_entry = ttk.Entry(
            data_frame,
            width=15,
            font=("Arial", 10, "bold"),
            textvariable=self.data_spesa_var
        )
        self.data_spesa_entry.pack(side="left")

        style.configure("Yellow.TButton", background="yellow", foreground="black")

        self.btn_cal_data_spesa = ttk.Button(
            data_frame,
            text="📅",
            width=2,
            command=lambda: self.mostra_calendario_popup(self.data_spesa_entry, self.data_spesa_var),
            style="Yellow.TButton"
        )
        self.btn_cal_data_spesa.pack(side="left", padx=4)

        self.btn_reset_data_spesa = ttk.Button(
            data_frame,
            text="↺",
            width=2,
            command=self.reset_data_spesa,
            style="Yellow.TButton"
        )
        self.btn_reset_data_spesa.pack(side="left", padx=4)

        row += 1
        self.cat_sel = tk.StringVar(value=self.categorie[0])
        ttk.Label(form_frame, text="🔍 Seleziona categoria:").grid(row=row, column=0, sticky="e")
       
        self.cat_menu = ttk.Combobox(form_frame, textvariable=self.cat_sel, values=sorted(self.categorie), state="readonly", width=25)

        self.cat_menu.grid(row=row, column=1, sticky="w")
        self.cat_menu.bind("<<ComboboxSelected>>", self.on_categoria_changed)
        row += 1
        
        ttk.Label(form_frame, text="ℹ️ Descrizione:").grid(row=row, column=0, sticky="e")
        def convalida_descrizione(nuovo_valore_1):
         return len(nuovo_valore_1) <= 30

        vdesc = form_frame.register(convalida_descrizione)
        self.desc_entry = ttk.Entry(form_frame, width=30, validate="key", validatecommand=(vdesc, "%P"))
        self.desc_entry.grid(row=row, column=1, sticky="w")
        row += 1
        
        ttk.Label(form_frame, text="💰 Importo (€):").grid(row=row, column=0, sticky="e")
        importo_frame = ttk.Frame(form_frame)
        def convalida_input(nuovo_valore_2):
         if nuovo_valore_2 == "":
              return True  # consente campo vuoto
         import re
         return len(nuovo_valore_2) <= 12 and re.match(r"^\d*[.,]?\d{0,2}$", nuovo_valore_2) is not None
         
        vcmd = form_frame.register(convalida_input)
        self.imp_entry = ttk.Entry(importo_frame, width=12, validate="key", validatecommand=(vcmd, "%P"))
        self.imp_entry.pack(side=tk.LEFT)
        #self.imp_entry.bind("<Return>", lambda event: self.conferma_importo()) ############Premi return per confermsre
        importo_frame.grid(row=row, column=1, sticky="w")
       
        row += 1

        style.configure("AggiungiSpesa.TButton", background="#32CD32", foreground="black")  # Aggiungi Spesa/Entrata - verde
        style.configure("SalvaModifica.TButton", background="#32CD32", foreground="black")  # Salva Modifica - verde
        style.configure("CancellaVoce.TButton", background="red", foreground="black")  # Cancella - rosso
        
        self.btn_aggiungi = ttk.Button(form_frame, text="💸 Aggiungi Spesa/Entrata", command=self.add_spesa, style="AggiungiSpesa.TButton")
        self.btn_aggiungi.grid(row=row, column=1, sticky="w", pady=(6, 2))

        self.btn_modifica = ttk.Button(form_frame, text="💾 Salva Modifica", command=self.salva_modifica, state=tk.DISABLED, style="SalvaModifica.TButton")
        self.btn_modifica.grid(row=row, column=2, sticky="w", padx=8, pady=(6, 2))

        self.btn_cancella = ttk.Button(form_frame, text="❌ Cancella", command=self.cancella_voce, state=tk.DISABLED, style="CancellaVoce.TButton")
        self.btn_cancella.grid(row=row, column=3, sticky="w", padx=8, pady=(6, 2))
        row += 1
       
        style.configure('GreenOutline.TButton', foreground='green', borderwidth=2, relief='solid')
        style.map('GreenOutline.TButton',
            bordercolor=[('!disabled', 'green')], foreground=[('!disabled', 'green')]
        )
        style.configure('RedOutline.TButton', foreground='red', borderwidth=2, relief='solid')
        style.map('RedOutline.TButton',
            bordercolor=[('!disabled', 'red')], foreground=[('!disabled', 'red')]
        )
        cat_default_type = self.categorie_tipi.get(self.cat_sel.get(), "Uscita")
        self.tipo_spesa_var = tk.StringVar(value=cat_default_type)
        btn_style = 'GreenOutline.TButton' if self.tipo_spesa_var.get() == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa = ttk.Button(
            importo_frame,
            text=self.tipo_spesa_var.get(),
            width=10,
            command=self.toggle_tipo_spesa,
            style=btn_style
        )
        self.btn_tipo_spesa.pack(side=tk.LEFT, padx=8)
        row += 1

        style.configure("Red.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))
        ric_frame = ttk.LabelFrame(form_frame, text="🔄 Ripeti Spesa/Entrata", style="Red.TLabelframe")
        
        ric_frame.grid(row=row, column=0, columnspan=4, sticky="w", padx=2, pady=(2, 7))
        self.ricorrenza_tipo = tk.StringVar(value="Nessuna")
        self.ricorrenza_n = tk.IntVar(value=1)
        self.ricorrenza_data_inizio = tk.StringVar(value=self.data_spesa_var.get())
        ttk.Label(ric_frame, text="📅 Ripeti:").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.ric_combo = ttk.Combobox(ric_frame, values=["Nessuna", "Ogni giorno", "Ogni mese", "Ogni anno"], width=10, state="readonly", textvariable=self.ricorrenza_tipo)
        self.ric_combo.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        
        ttk.Label(ric_frame, text="Ripeti volte:").grid(row=0, column=2, sticky="e", padx=2, pady=2)
        def convalida_ric_n(valore):
            if valore == "":
                return True  # campo vuoto ammesso durante digitazione
            import re
            return len(valore) <= 4 and re.fullmatch(r"\d{0,3}([.,]?\d?)?", valore) is not None
        vcmd_ric = ric_frame.register(convalida_ric_n)
        self.ric_n_entry = ttk.Entry(
            ric_frame,
            width=4,
            textvariable=self.ricorrenza_n,
            validate="key",
            validatecommand=(vcmd_ric, "%P")
        )
        self.ric_n_entry.grid(row=0, column=3, sticky="w", padx=2, pady=2)
       
        ttk.Label(ric_frame, text="Inizio:").grid(row=0, column=4, sticky="e", padx=2, pady=2)

        ric_data_frame = ttk.Frame(ric_frame)
        ric_data_frame.grid(row=0, column=5, sticky="w", padx=2, pady=2)

        self.ric_data_entry = ttk.Entry(ric_data_frame, textvariable=self.ricorrenza_data_inizio, width=15, font=("Arial", 10, "bold"))
        self.ric_data_entry.pack(side="left")

        btn_cal_popup = ttk.Button(
            ric_data_frame,
            text="📅",
            width=2,
            command=lambda: self.mostra_calendario_popup(self.ric_data_entry, self.ricorrenza_data_inizio),
            style="Yellow.TButton"
        )
        btn_cal_popup.pack(side="left", padx=4)



        self.btn_reset_ric_data = ttk.Button(
            ric_data_frame,
            text="↺",
            width=2,
            command=self.reset_ric_data_inizio,  # Assicurati di avere questo metodo definito
            style="Yellow.TButton"
        )
        self.btn_reset_ric_data.pack(side="left", padx=4)

        style.configure("AggiungiRicorrenza.TButton", background="#32CD32", foreground="black")  # Aggiungi Ricorrenza - verde
        style.configure("CancellaRicorrenza.TButton", background="red", foreground="black")  # Cancella Ricorrenza - rosso
        style.configure("ListaRicorrenze.TButton", background="#FFA500", foreground="black")  # Lista Ricorrenze - arancione

        self.btn_add_ricorrenza = ttk.Button(ric_frame, text="📂 Aggiungi", command=self.add_ricorrenza, style="AggiungiRicorrenza.TButton")
        self.btn_add_ricorrenza.grid(row=0, column=6, padx=10, pady=2)

        self.btn_cancella_ricorrenza = ttk.Button(ric_frame, text="❌ Cancella", command=self.del_ricorrenza, style="CancellaRicorrenza.TButton")
        self.btn_cancella_ricorrenza.grid(row=0, column=7, padx=5, pady=2)

        self.btn_modifica_ricorrenza = ttk.Button(ric_frame, text="🔄 Lista", command=self.mostra_lista_ricorrenze, style="ListaRicorrenze.TButton")
        self.btn_modifica_ricorrenza.grid(row=0, column=8, padx=5, pady=2)

        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        
        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))

        aggiungi_cat_frame = ttk.LabelFrame(right_frame, text="✅ Aggiungi/Modifica Categoria", style="RedBold.TLabelframe")
        aggiungi_cat_frame.pack(fill=tk.X, padx=2, pady=(8, 2))

       
        self.nuova_cat = tk.StringVar()
       
        # Definizione degli stili con i colori richiesti
        style.configure("AggiungiCategoria.TButton", background="#32CD32", foreground="black")  # Aggiungi Categoria - verde
        style.configure("ModificaNome.TButton", background="#FFA500", foreground="black")  # Modifica Nome - arancione
        style.configure("CancellaCategoria.TButton", background="red", foreground="black")  # Cancella Categoria - rosso

        def convalida_categoria(valore):
            return len(valore) <= 30

        vcmd_cat = aggiungi_cat_frame.register(convalida_categoria)

        self.nuova_cat = tk.StringVar()
        ttk.Label(aggiungi_cat_frame, text="🔍 Nome categoria:").grid(row=0, column=0, sticky="e", padx=4, pady=6)
        self.entry_nuova_cat = ttk.Entry(
            aggiungi_cat_frame,
            textvariable=self.nuova_cat,
            width=30,
            validate="key",
            validatecommand=(vcmd_cat, "%P")
        )
        self.entry_nuova_cat.grid(row=0, column=1, sticky="w", padx=4, pady=6)
        #self.entry_nuova_cat.bind("<Return>", lambda event: self.add_categoria()) ### enter per confermare
        ttk.Button(aggiungi_cat_frame, text="🔍 Aggiungi Categoria", command=self.add_categoria).grid(row=0, column=2, padx=8, pady=6)
       
        ttk.Label(aggiungi_cat_frame, text="✅ Seleziona categoria:").grid(row=1, column=0, sticky="e", padx=4, pady=6)
        self.cat_mod_sel = tk.StringVar(value=self.categorie[0])
        self.cat_mod_menu = ttk.Combobox(
        aggiungi_cat_frame,
        textvariable=self.cat_mod_sel,
        values=sorted(self.categorie),  # 👈 ordina in ordine alfabetico
        state="readonly",
        width=20
        )

        self.cat_mod_menu.grid(row=1, column=1, sticky="w", padx=2, pady=6)
        self.cat_mod_menu.bind("<<ComboboxSelected>>", lambda e: self.on_categoria_modifica_changed())

        self.btn_modifica_categoria = ttk.Button(aggiungi_cat_frame, text="⚙️ Modifica Nome", command=self.modifica_categoria, style="ModificaNome.TButton")
        self.btn_modifica_categoria.grid(row=1, column=2, padx=4, pady=6)

        self.btn_cancella_categoria = ttk.Button(aggiungi_cat_frame, text="❌ Cancella Categoria", command=self.cancella_categoria, style="CancellaCategoria.TButton")
        self.btn_cancella_categoria.grid(row=1, column=3, padx=8, pady=6)
       
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        

    def colora_giorni_spese(self):
        if not os.path.exists(DB_FILE):
            return
        self.cal.calevent_remove('all')  # <-- questa riga rimuove tutti gli eventi vecchi
        
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)

        giornate = db.get("spese", [])  # o il nome corretto se è diverso
        for giorno in giornate:
            try:
                data_str = giorno.get("date", "")
                data = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()

                tipi = {entry.get("tipo", "").lower() for entry in giorno.get("entries", [])}

                if "entrata" in tipi and "uscita" in tipi:
                    tag = "misto"
                elif "entrata" in tipi:
                    tag = "verde"
                elif "uscita" in tipi:
                    tag = "rosso"
                else:
                    continue

                self.cal.calevent_create(data, "", tag)

            except Exception as e:
                print(f"Errore su giorno {giorno}: {e}")


        self.cal.tag_config("verde", background="lightgreen", foreground="black")
        self.cal.tag_config("rosso", background="lightcoral", foreground="black")
        self.cal.tag_config("misto", background="khaki", foreground="black")


    def on_calendar_change(self, event=None):
        try:
            data = self.cal.selection_get()
            if not data:
                return

            mese_corrente = self.estratto_month_var.get()
            anno_corrente = self.estratto_year_var.get()

            mese_da_cal = f"{data.month:02d}"
            anno_da_cal = str(data.year)

            if mese_corrente != mese_da_cal:
                self.estratto_month_var.set(mese_da_cal)
                self.cb_estratto_month.current(data.month - 1)

            if anno_corrente != anno_da_cal:
                self.estratto_year_var.set(anno_da_cal)
                self.cb_estratto_year.set(anno_da_cal)

            # Salva la data selezionata
            selected_date = data

            # Chiama apply_estratto e poi ripristina la selezione
            def restore_selection():
                self.cal.selection_set(selected_date)

            #self.after(100, lambda: [self.apply_estratto(), restore_selection()])
            self.after(100, lambda: self.apply_estratto("giorno"))


        except Exception as e:
            print(f"Errore durante il cambio data: {e}")


    def aggiorna_titolo_finestra(self):
        now = datetime.datetime.now().strftime("%A, %d %B %Y | %H:%M:%S")
        self.title(f"Casa Facile Pro v {VERSION}  — Email: helpcasafacilepro@gmail.com —  {now} ")
        self.after(1000, self.aggiorna_titolo_finestra)

    def load_window_geometry(self):
        if not os.path.exists(DB_FILE):
            return
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._window_geometry = data.get("_window_geometry", None)
        except Exception:
            self._window_geometry = None

    def save_window_geometry(self):
        geometry = self.geometry()
        self._window_geometry = geometry
        try:
            data = {}
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["_window_geometry"] = geometry
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Errore salvataggio geometria finestra:", e)

    def _on_close(self):
        self.save_window_geometry()
        self.save_db()
        self.destroy()

    def load_db(self):
        if not os.path.exists(DB_FILE):
            return
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.categorie = data.get("categorie", ["Generica"])
            self.categorie_tipi = data.get("categorie_tipi", {"Generica": "Uscita"})
            self.spese = {}
            for obj in data.get("spese", []):
                d = datetime.datetime.strptime(obj["date"], "%d-%m-%Y").date()
                entries = []
                for e in obj.get("entries", []):
                    if "id_ricorrenza" in e:
                        entries.append((e["categoria"], e["descrizione"], float(e["importo"]), e["tipo"], e["id_ricorrenza"]))
                    else:
                        entries.append((e["categoria"], e["descrizione"], float(e["importo"]), e["tipo"]))
                self.spese[d] = entries
            self.ricorrenze = data.get("ricorrenze", {})
            self._window_geometry = data.get("_window_geometry", None)
        except Exception as e:
            print("Errore caricamento DB:", e)
            self.categorie = ["Generica"]
            self.categorie_tipi = {"Generica": "Uscita"}
            self.spese = {}
            self.ricorrenze = {}
            self._window_geometry = None

    def save_db(self):
        data = {
            "categorie": self.categorie,
            "categorie_tipi": self.categorie_tipi,
            "spese": [
                {"date": d.strftime("%d-%m-%Y"), "entries": [
                    {"categoria": c, "descrizione": desc, "importo": imp, "tipo": tipo, **({"id_ricorrenza": rid} if len(entry) == 5 else {})}
                        for entry in sp
                        for c, desc, imp, tipo, *rest in [entry]
                        for rid in [rest[0] if rest else None]
                ]} for d, sp in self.spese.items()
            ],
            "ricorrenze": self.ricorrenze
        }
        if self._window_geometry is not None:
            data["_window_geometry"] = self._window_geometry
        else:
            try:
                data["_window_geometry"] = self.geometry()
            except Exception:
                pass
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def toggle_tipo_spesa(self):
        v = self.tipo_spesa_var.get()
        nuovo = "Entrata" if v == "Uscita" else "Uscita"
        self.tipo_spesa_var.set(nuovo)
        self.btn_tipo_spesa.config(text=nuovo)
        new_style = 'GreenOutline.TButton' if nuovo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)

    def aggiorna_combobox_categorie(self):
        # Ordina la lista (case-insensitive)
        self.categorie.sort(key=str.lower)

        self.cat_menu["values"] = self.categorie
        self.cat_mod_menu["values"] = self.categorie

        if self.categorie:
            self.cat_sel.set(self.categorie[0])
            self.cat_mod_sel.set(self.categorie[0])


    def on_categoria_changed(self, event=None):
        cat = self.cat_sel.get()
        tipo_cat = self.categorie_tipi.get(cat, "Uscita")
        self.tipo_spesa_var.set(tipo_cat)
        self.btn_tipo_spesa.config(text=tipo_cat)
        new_style = 'GreenOutline.TButton' if tipo_cat == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)
      
    def on_categoria_modifica_changed(self, event=None):
        pass

    def add_categoria(self):
        nome = self.nuova_cat.get().strip()
        tipo = "Uscita"
        if not nome or nome in self.categorie or nome == self.CATEGORIA_RIMOSSA:
            self.show_custom_warning("Attenzione", "Nome categoria vuoto, già esistente o riservato.")
            return
        self.categorie.append(nome)
        self.categorie_tipi[nome] = tipo
        self.aggiorna_combobox_categorie()
        self.nuova_cat.set("")
        self.cat_sel.set(nome)
        self.cat_mod_sel.set(nome)
        self.on_categoria_changed()

    def modifica_categoria(self):
        old_nome = self.cat_mod_sel.get()
        if old_nome == "Generica":
         self.show_custom_warning("Attenzione", "La categoria 'Generica' non può essere rinominata.")
         return
        new_nome = self.nuova_cat.get().strip()
        if not new_nome:
            self.show_custom_warning("Attenzione", "Inserisci il nuovo nome della categoria.")
            return
        if new_nome == old_nome:
            self.show_custom_info("Info", "Il nuovo nome è uguale a quello attuale.")
            return
        if new_nome in self.categorie:
            self.show_custom_warning("Attenzione", "Esiste già una categoria con questo nome.")
            return
        idx = self.categorie.index(old_nome)
        self.categorie[idx] = new_nome
        self.categorie_tipi[new_nome] = self.categorie_tipi.pop(old_nome)
        for d in self.spese:
            new_entries = []
            for entry in self.spese[d]:
                if entry[0] == old_nome:
                    entry = (new_nome,) + entry[1:]
                new_entries.append(entry)
            self.spese[d] = new_entries
        self.cat_menu["values"] = self.categorie
        self.cat_mod_menu["values"] = self.categorie
        self.cat_sel.set(new_nome)
        self.cat_mod_sel.set(new_nome)
        self.nuova_cat.set("")
        self.save_db()
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.show_custom_info("Attenzione", f"Categoria '{old_nome}' rinominata in '{new_nome}'.")
        
    def conferma_cancella_categoria(self, cat):
        popup = tk.Toplevel(self)
        popup.title("Conferma eliminazione")
        popup.resizable(False, False)
        width, height = 320, 120
        popup.withdraw()
        popup.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        x = parent_x + (parent_w // 2) - (width // 2)
        y = parent_y + (parent_h // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.deiconify()
        popup.grab_set()
        label = tk.Label(
            popup,
            text=f"Vuoi davvero cancellare la categoria '{cat}'?\nLe spese rimarranno ma saranno\nrinominate come '{self.CATEGORIA_RIMOSSA}'.",
            font=("Arial",10),
            justify="center",
            wraplength=280
        )
        label.pack(pady=8, padx=10)
        frame = tk.Frame(popup)
        frame.pack(pady=4)
        result = {"ok": False}
        def do_ok():
            result["ok"] = True
            popup.destroy()
        def do_cancel():
            popup.destroy()
        b1 = tk.Button(frame, text="Elimina", font=("Arial", 9), width=8, command=do_ok)
        b2 = tk.Button(frame, text="Annulla", font=("Arial", 9), width=8, command=do_cancel)
        b1.pack(side="left", padx=8)
        b2.pack(side="right", padx=8)
        popup.wait_window()
        return result["ok"]

    def cancella_categoria(self):
        cat = self.cat_mod_sel.get()
        if cat in ("Generica", self.CATEGORIA_RIMOSSA):
            self.show_custom_warning("Attenzione", f"Non puoi cancellare la categoria '{cat}'.")
            return
        if not self.conferma_cancella_categoria(cat):
            return
        if cat in self.categorie:
            self.categorie.remove(cat)
        if cat in self.categorie_tipi:
            del self.categorie_tipi[cat]
        for giorno in list(self.spese):  # <- meglio usare list() per modificare il dizionario durante l'iterazione
            nuove_spese = []
            for voce in self.spese[giorno]:
                voce_cat = voce[0]
                if voce_cat == cat:
                    nuove_spese.append((self.CATEGORIA_RIMOSSA,) + voce[1:])
                else:
                    nuove_spese.append(voce)
    
            # ✅ Qui va il blocco di controllo
            if nuove_spese:
                self.spese[giorno] = nuove_spese
            else:
                del self.spese[giorno]

        self.aggiorna_combobox_categorie()
        self.save_db()
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.on_categoria_changed()
        
    def show_custom_warning(self, title, message):
        self._show_custom_message(title, message, "yellow", "black", "warning")

    def show_custom_info(self, title, message):
        self._show_custom_message(title, message, "lightblue", "black", "info")

    def show_custom_askyesno(self, title, message):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 150,
            self.winfo_rooty() + 150
        ))
        label = tk.Label(dialog, text=message, font=("Arial", 9), justify="left", padx=16, pady=12)
        label.pack()
        btns = tk.Frame(dialog)
        btns.pack(pady=(0,10))
        result = {"value": False}
        def yes():
            result["value"] = True
            dialog.destroy()
        def no():
            result["value"] = False
            dialog.destroy()
        b1 = tk.Button(btns, text="Sì", width=8, command=yes)
        b2 = tk.Button(btns, text="No", width=8, command=no)
        b1.grid(row=0, column=0, padx=8)
        b2.grid(row=0, column=1, padx=8)
        dialog.wait_window()
        return result["value"]

    def _show_custom_message(self, title, message, bg, fg, icon=None):
        dialog = tk.Toplevel(self)
        dialog.attributes("-topmost", True)
        dialog.withdraw()  
        dialog.title(title)
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        frame = tk.Frame(dialog, bg=bg)
        frame.pack(fill="both", expand=True)
        frame.pack_propagate(False) 
        label = tk.Label(frame, text=message, font=("Arial", 10), bg=bg, fg=fg, justify="left", padx=16, pady=12)
        label.pack()
        btn = tk.Button(frame, text="OK", width=10, command=dialog.destroy)
        btn.pack(pady=(0, 10))
        btn.focus_set()
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.update_idletasks()  
        width = label.winfo_reqwidth() + 40  
        height = label.winfo_reqheight() + btn.winfo_reqheight() + 40
        x = (dialog.winfo_screenwidth() - width) // 2
        y = (dialog.winfo_screenheight() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.deiconify()  
        dialog.wait_window()  
 
    def reset_data_spesa(self):
        today = datetime.date.today()
        self.data_spesa_var.set(today.strftime("%d-%m-%Y"))


    def reset_ric_data_inizio(self):
        oggi = datetime.date.today()
        self.ricorrenza_data_inizio.set(oggi.strftime("%d-%m-%Y"))

    def add_ricorrenza(self):
        ric_type = self.ricorrenza_tipo.get()
        if ric_type == "Nessuna":
            self.add_spesa()
            return
        try:
            n = int(self.ricorrenza_n.get())
            if n <= 0:
                raise ValueError
        except Exception:
            self.show_custom_warning("Errore", "Numero ripetizioni non valido")
            return
        try:
            data_inizio = datetime.datetime.strptime(self.ricorrenza_data_inizio.get(), "%d-%m-%Y").date()
        except Exception:
            self.show_custom_warning("Errore", "Data inizio ricorrenza non valida")
            return
        cat = self.cat_sel.get()
        desc = self.desc_entry.get().strip()
        try:
            imp = float(self.imp_entry.get().replace(",", "."))
        except Exception:
            self.show_custom_warning("Errore", "Importo non valido")
            return
        tipo = self.tipo_spesa_var.get()
        ric_id = str(uuid.uuid4())
        date_list = []
        for i in range(n):
            if ric_type == "Ogni giorno":
                d = data_inizio + datetime.timedelta(days=i)
            elif ric_type == "Ogni mese":
                month = (data_inizio.month - 1 + i) % 12 + 1
                year = data_inizio.year + (data_inizio.month - 1 + i) // 12
                day = min(data_inizio.day, [31,
                    29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                    31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                try:
                    d = datetime.date(year, month, day)
                except Exception:
                    d = datetime.date(year, month, 1)
            elif ric_type == "Ogni anno":
                year = data_inizio.year + i
                try:
                    d = datetime.date(year, data_inizio.month, data_inizio.day)
                except Exception:
                    d = datetime.date(year, data_inizio.month, 1)
            else:
                break
            date_list.append(d)
        for d in date_list:
            if d not in self.spese:
                self.spese[d] = []
            self.spese[d].append((cat, desc, imp, tipo, ric_id))
        self.ricorrenze[ric_id] = {
            "tipo": ric_type,
            "n": n,
            "data_inizio": data_inizio.strftime("%d-%m-%Y"),
            "cat": cat,
            "desc": desc,
            "imp": imp,
            "tipo_voce": tipo,
            "date_list": [d.strftime("%d-%m-%Y") for d in date_list]
        }
        self.save_db()
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.show_custom_info("Ricorrenza aggiunta", f"Spesa/entrata ricorrente aggiunta per {n} volte.")
        self.ricorrenza_tipo.set("Nessuna")  
        self.reset_modifica_form()
        self.colora_giorni_spese() 

    def del_ricorrenza(self):
        if not self.ricorrenze:
            self.show_custom_warning("Info", "Nessuna ricorrenza trovata.")
            return
        popup = tk.Toplevel(self)
        popup.title("Cancella Ricorrenza")
        popup.grab_set()
        popup.resizable(False, False)
        popup.geometry("+%d+%d" % (
            self.winfo_rootx() + 200,
            self.winfo_rooty() + 120
        ))
        tk.Label(popup, text="Seleziona una ricorrenza da cancellare:", font=("Arial", 10)).pack(padx=12, pady=7)
        frame = tk.Frame(popup)
        frame.pack(padx=8, pady=4)
        ric_list = list(self.ricorrenze.items())
        showlist = []
        for rid, r in ric_list[-10:]:
            tipo = r["tipo"]
            n = r["n"]
            data_inizio = r["data_inizio"]
            desc = r["desc"]
            cat = r["cat"]
            showlist.append(f"{tipo} x{n} da {data_inizio} - {cat} - {desc} ({rid[:8]})")
        ric_sel = tk.StringVar(value=showlist[0] if showlist else "")
        ric_combo = ttk.Combobox(frame, values=showlist, state="readonly", width=60, textvariable=ric_sel)
        ric_combo.grid(row=0, column=0, padx=4, pady=4)
        def get_selected_id():
            idx = showlist.index(ric_sel.get())
            return ric_list[-10:][idx][0]
        def do_ok():
            rid = get_selected_id()
            self._delete_ricorrenza_by_id(rid)
            popup.destroy()
        def do_cancel():
            popup.destroy()
        frame_btn = tk.Frame(popup)
        frame_btn.pack(pady=5)
        tk.Button(frame_btn, text="Cancella", command=do_ok, width=10).grid(row=0, column=0, padx=8)
        tk.Button(frame_btn, text="Annulla", command=do_cancel, width=10).grid(row=0, column=1, padx=8)

    def _delete_ricorrenza_by_id(self, ric_id):
        if ric_id not in self.ricorrenze:
            self.show_custom_warning("Errore", "Ricorrenza non trovata.")
            return
        for data, voci in list(self.spese.items()):
            nuove_voci = []
            for voce in voci:
                if len(voce) == 5 and voce[4] == ric_id:
                    continue
                nuove_voci.append(voce)
            if nuove_voci:
                self.spese[data] = nuove_voci
            else:
                del self.spese[data]    
        del self.ricorrenze[ric_id]
        residui = []
        for data, voci in self.spese.items():
            for voce in voci:
                if len(voce) == 5 and voce[4] == ric_id:
                    residui.append((data, voce))
        if residui:
            print("❗ Voci residue trovate:")
            for data, voce in residui:
                print("  -", data, voce)        
        if hasattr(self, "db"):
            self.db["spese"] = self.spese
            self.db["ricorrenze"] = self.ricorrenze
        self.save_db()
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.colora_giorni_spese() 
        
    def mostra_lista_ricorrenze(self, larghezza_colonne=None):
        """Mostra una finestra centrata con l'elenco delle ricorrenze, permettendo di impostare la larghezza delle colonne."""
        lista_window = tk.Toplevel(self)
        lista_window.title("Lista Ricorrenze")
        larghezza, altezza = 840, 300
        x = (self.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (self.winfo_screenheight() // 2) - (altezza // 2)
        lista_window.geometry(f"{larghezza}x{altezza}+{x}+{y}")
        lista_window.resizable(False, False)
        columns = ("Categoria", "Ripetizioni", "ID", "Data Inserimento")
        tree = ttk.Treeview(lista_window, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
        default_larghezze = {
            "Categoria": 300,
            "Ripetizioni": 90,
            "ID": 300,
            "Data Inserimento": 130,
    }

        larghezze = larghezza_colonne if larghezza_colonne else default_larghezze
        for col in columns:
            tree.column(col, width=larghezze.get(col, 200))  # Se manca, usa 200 come default
        tree.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        for id_ricorrenza, dati in self.ricorrenze.items():
            categoria = dati.get("cat", "Sconosciuta")  
            ripetizioni = dati.get("n", "N/D")  
            data_inserimento = dati.get("data_inizio", "N/D")  
            tree.insert("", "end", values=(categoria, ripetizioni, id_ricorrenza, data_inserimento))
        ttk.Button(lista_window, text="❌ Chiudi", command=lista_window.destroy).grid(row=1, column=1, pady=10)

    def add_spesa(self):
        if self.ricorrenza_tipo.get() != "Nessuna":
            self.add_ricorrenza()
            return
        data = self.data_spesa_var.get()
        cat = self.cat_sel.get()
        desc = self.desc_entry.get().strip()
        try:
            imp = float(self.imp_entry.get().replace(",", "."))
        except Exception:
            self.show_custom_warning("Errore", "Importo non valido")
            return
        tipo = self.tipo_spesa_var.get()
        d = datetime.datetime.strptime(data, "%d-%m-%Y").date()
        if d not in self.spese:
            self.spese[d] = []
        self.spese[d].append((cat, desc, imp, tipo))
        self.desc_entry.delete(0, tk.END)
        self.imp_entry.delete(0, tk.END)
        self.on_categoria_changed()
        self.save_db()
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.reset_modifica_form()
        self.colora_giorni_spese()
        
    def set_tipo_spesa_editable(self, editable=True):
        if editable:
            self.btn_tipo_spesa.state(["!disabled"])
        else:
            self.btn_tipo_spesa.state(["disabled"])

    def on_table_click(self, event):
        mode = self.stats_mode.get()
        if mode != "giorno":
            return
        region = self.stats_table.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.stats_table.identify_column(event.x)
        if col != "#6":
            return
        rowid = self.stats_table.identify_row(event.y)
        if not rowid:
            return
        vals = self.stats_table.item(rowid, "values")
        giorno_str, cat, desc, imp, tipo, _ = vals
        giorno = datetime.datetime.strptime(giorno_str, "%d-%m-%Y").date()
        idx = self.stats_table.index(rowid)
        voce = self.spese[giorno][idx]
        self.modifica_idx = (giorno, idx)
        self.cat_sel.set(cat)
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, desc)
        self.imp_entry.delete(0, tk.END)
        self.imp_entry.insert(0, imp)
        self.tipo_spesa_var.set(tipo)
        self.btn_tipo_spesa.config(text=tipo)
        self.btn_modifica["state"] = tk.NORMAL
        self.btn_aggiungi["state"] = tk.DISABLED
        self.btn_cancella["state"] = tk.NORMAL
        self.data_spesa_var.set(giorno.strftime("%d-%m-%Y"))
        #Modifica entrata uscita consentito
        self.set_tipo_spesa_editable(False)
        self.set_tipo_spesa_editable(True)
        new_style = 'GreenOutline.TButton' if tipo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)
        if len(voce) == 5:
            ric_id = voce[4]
            if ric_id in self.ricorrenze:
                ric = self.ricorrenze[ric_id]
                self.show_custom_info("Voce ricorrente", f"Questa voce è parte di una ricorrenza: {ric['tipo']} x{ric['n']} da {ric['data_inizio']}.\nPuoi cancellare tutta la ricorrenza dal pannello sotto.")

    def reset_modifica_form(self):
        self.modifica_idx = None
        self.btn_modifica["state"] = tk.DISABLED
        self.btn_aggiungi["state"] = tk.NORMAL
        self.btn_cancella["state"] = tk.DISABLED
        self.desc_entry.delete(0, tk.END)
        self.imp_entry.delete(0, tk.END)
        self.on_categoria_changed()
        self.data_spesa_var.set(datetime.date.today().strftime("%d-%m-%Y"))
        self.set_tipo_spesa_editable(True)

    def salva_modifica(self):
        if not self.modifica_idx:
            return
        old_dt, idx = self.modifica_idx
        new_data = self.data_spesa_var.get()
        new_dt = datetime.datetime.strptime(new_data, "%d-%m-%Y").date()
        cat = self.cat_sel.get()
        desc = self.desc_entry.get().strip()
        try:
            imp = float(self.imp_entry.get().replace(",", "."))
        except Exception:
            self.show_custom_warning("Errore", "Importo non valido")
            return
        tipo = self.tipo_spesa_var.get()

        if old_dt not in self.spese or idx >= len(self.spese[old_dt]):
            self.show_custom_warning("Errore", "La voce selezionata non esiste più.")
            self.reset_modifica_form()
            return
        voce_old = self.spese[old_dt][idx]
        id_ric = voce_old[4] if len(voce_old) == 5 else None

        del self.spese[old_dt][idx]
        if not self.spese[old_dt]:
            del self.spese[old_dt]
        if new_dt not in self.spese:
            self.spese[new_dt] = []
        voce_new = (cat, desc, imp, tipo)
        if id_ric is not None:
            voce_new += (id_ric,)
        self.spese[new_dt].append(voce_new)
        self.save_db()
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.reset_modifica_form()
        self.colora_giorni_spese()

    def cancella_voce(self):
        if not self.modifica_idx:
            return
        dt, idx = self.modifica_idx
        if dt in self.spese and 0 <= idx < len(self.spese[dt]):
            del self.spese[dt][idx]
            if not self.spese[dt]:
                del self.spese[dt]
            self.save_db()
            self.update_stats()
            self.update_totalizzatore_anno_corrente()
            self.update_totalizzatore_mese_corrente()
            self.update_spese_mese_corrente()
        self.reset_modifica_form()
        self.colora_giorni_spese()

    def update_spese_mese_corrente(self):
        for i in self.spese_mese_tree.get_children():
            self.spese_mese_tree.delete(i)
        now = datetime.date.today()
        year, month = now.year, now.month
        spese_mese = []
        for d in sorted(self.spese.keys()):
            if d.year == year and d.month == month:
                for entry in self.spese[d]:
                    cat, desc, imp, tipo = entry[:4]
                    spese_mese.append((d, cat, desc, imp, tipo))
        for d, cat, desc, imp, tipo in spese_mese:
            tag = 'entrata' if tipo == 'Entrata' else 'uscita'
            self.spese_mese_tree.insert("", "end", values=(
                d.strftime("%d-%m-%Y"), cat, desc, f"{imp:.2f}", tipo
            ), tags=(tag,))

    def apply_estratto(self, forza_modalita=None):
        try:
            m = int(self.cb_estratto_month.get().split(" - ")[0])
            y = int(self.cb_estratto_year.get())
            d = datetime.date(y, m, 1)
            self.stats_refdate = d
            #self.cal.selection_set(d)

            # Cambia solo se viene specificata una modalità
            if forza_modalita:
                self.set_stats_mode(forza_modalita)

            self.update_totalizzatore_anno_corrente()
            self.update_totalizzatore_mese_corrente()
            self.update_spese_mese_corrente()
        except Exception:
            self.show_custom_warning("Errore", "Mese o anno non validi")


    def set_stats_mode(self, mode):
        self.stats_mode.set(mode)
        if mode == "giorno":
            self.stats_label.config(text="Statistiche giornaliere")
            self.stats_table["displaycolumns"] = ("A","B","C","D","E","F")
            self.stats_table.heading("A", text="Data")
            self.stats_table.heading("B", text="Categoria")
            self.stats_table.heading("C", text="Descrizione")
            self.stats_table.heading("D", text="Importo (€)")
            self.stats_table.heading("E", text="Tipo")
            self.stats_table.heading("F", text="Modifica")
        elif mode == "mese":
            ref = self.stats_refdate
            monthname = self.get_month_name(ref.month)
            self.stats_label.config(text=f"Statistiche mensili per {monthname} {ref.year}")
            self.stats_table["displaycolumns"] = ("A","B","C")
            self.stats_table.heading("A", text="Categoria")
            self.stats_table.heading("B", text="Totale Categoria (€)")
            self.stats_table.heading("C", text="Tipo")
        elif mode == "anno":
            ref = self.stats_refdate
            self.stats_label.config(text=f"Statistiche annuali per {ref.year}")
            self.stats_table["displaycolumns"] = ("A","B","C")
            self.stats_table.heading("A", text="Categoria")
            self.stats_table.heading("B", text="Totale Categoria (€)")
            self.stats_table.heading("C", text="Tipo")
        else:
            self.stats_label.config(text="Totali per categoria")
            self.stats_table["displaycolumns"] = ("A","B","C")
            self.stats_table.heading("A", text="Categoria")
            self.stats_table.heading("B", text="Totale Categoria (€)")
            self.stats_table.heading("C", text="Tipo")
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()

    def get_month_name(self, month):
        mesi = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        return mesi[month-1] if 1 <= month <= 12 else str(month)

    def update_stats(self):
        for i in self.stats_table.get_children():
            self.stats_table.delete(i)
        mode = self.stats_mode.get()
        tot_entrate, tot_uscite = 0.0, 0.0
        if mode == "giorno":
            try:
                giorno = datetime.datetime.strptime(self.cal.get_date(), "%d-%m-%Y").date()
            except Exception:
                giorno = datetime.date.today()
            spese = self.spese.get(giorno, [])
            for idx, entry in enumerate(spese):
                cat, desc, imp, tipo = entry[:4]
                tag = "entrata" if tipo == "Entrata" else "uscita"
                self.stats_table.insert(
                    "", "end",
                    values=(giorno.strftime("%d-%m-%Y"), cat, desc, f"{imp:.2f}", tipo, "Modifica"),
                    tags=(f"{giorno.strftime('%d-%m-%Y')}|{idx}", tag)
                )
                if tipo == "Entrata":
                    tot_entrate += imp
                else:
                    tot_uscite += imp
        else:
            totali = {}
            ref = self.stats_refdate
            for d, sp in self.spese.items():
                if mode == "mese":
                    if not (d.year == ref.year and d.month == ref.month):
                        continue
                elif mode == "anno":
                    if d.year != ref.year:
                        continue
                for entry in sp:
                    cat, desc, imp, tipo = entry[:4]
                    if cat not in totali:
                        totali[cat] = {"Entrata": 0.0, "Uscita": 0.0}
                    totali[cat][tipo] += imp
            for cat in sorted(totali.keys()):
                for tipo in ("Entrata", "Uscita"):
                    if totali[cat][tipo] > 0:
                        tag = "entrata" if tipo == "Entrata" else "uscita"
                        self.stats_table.insert(
                            "", "end",
                            values=(cat, f"{totali[cat][tipo]:.2f}", tipo),
                            tags=(tag,)
                        )
                        if tipo == "Entrata":
                            tot_entrate += totali[cat][tipo]
                        else:
                            tot_uscite += totali[cat][tipo]
        txt_tot = f"Totale Entrate: {tot_entrate:.2f}    Totale Uscite: {tot_uscite:.2f}    Differenza: {(tot_entrate-tot_uscite):.2f}"
        self.totali_label.config(text=txt_tot)

    def update_totalizzatore_anno_corrente(self):
        anno = datetime.date.today().year
        totale_entrate = 0.0
        totale_uscite = 0.0
        for d, sp in self.spese.items():
            if d.year == anno:
                for entry in sp:
                    tipo = entry[3]
                    imp = entry[2]
                    if tipo == "Entrata":
                        totale_entrate += imp
                    else:
                        totale_uscite += imp
        differenza = totale_entrate - totale_uscite
        self.totalizzatore_entrate_label.config(text=f"Totale Entrate: {totale_entrate:.2f} €")
        self.totalizzatore_uscite_label.config(text=f"Totale Uscite:  {totale_uscite:.2f} €")
        self.totalizzatore_diff_label.config(
            text=f"Differenza:      {differenza:.2f} €",
            foreground="blue" if differenza >= 0 else "red"
        )

    def update_totalizzatore_mese_corrente(self):
        now = datetime.date.today()
        year, month = now.year, now.month
        totale_entrate = 0.0
        totale_uscite = 0.0
        for d, sp in self.spese.items():
            if d.year == year and d.month == month:
                for entry in sp:
                    tipo = entry[3]
                    imp = entry[2]
                    if tipo == "Entrata":
                        totale_entrate += imp
                    else:
                        totale_uscite += imp
        differenza = totale_entrate - totale_uscite
        self.totalizzatore_mese_entrate_label.config(text=f"Totale Entrate mese: {totale_entrate:.2f} €")
        self.totalizzatore_mese_uscite_label.config(text=f"Totale Uscite mese:  {totale_uscite:.2f} €")
        self.totalizzatore_mese_diff_label.config(
            text=f"Differenza mese:     {differenza:.2f} €",
            foreground="blue" if differenza >= 0 else "red"
        )

    def show_reset_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Reset Database")
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.transient(self)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600  
        window_height = 250 
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2

        dialog.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        label = tk.Label(dialog, text=(
            "Vuoi cancellare tutte le spese e/o le categorie?\n\n"
            "Scegli 'Sì' per cancellare tutto (spese + categorie, resterà solo la categoria di default)\n\n"
            "'No' per cancellare solo le spese.\n\n"
            "'Letture' per cancellare le letture delle utenze\n\n"
            "'Rubrica' per cancellare tutta la rubrica\n"
            "'Password' per cancellare la password\n"
        ), font=("Arial", 10), justify="left", padx=12, pady=10)
        label.pack()

        btns = tk.Frame(dialog)
        btns.pack(pady=(0, 10))
 

        def do_yes():
            dialog.destroy()
            self.spese = {}
            self.categorie = ["Generica"]
            self.categorie_tipi = {"Generica": "Uscita"}
            self.ricorrenze = {}
            self.cat_menu["values"] = self.categorie
            self.cat_mod_menu["values"] = self.categorie
            self.cat_sel.set(self.categorie[0])
            self.cat_mod_sel.set(self.categorie[0])
            self.save_db()
            self.update_stats()
            self.update_totalizzatore_anno_corrente()
            self.update_totalizzatore_mese_corrente()
            self.update_spese_mese_corrente()
            self.show_custom_warning("Spese", "Spese e categorie azzerate")
        def do_no():
            dialog.destroy()
            self.spese = {}
            self.ricorrenze = {}
            self.save_db()
            self.update_stats()
            self.update_totalizzatore_anno_corrente()
            self.update_totalizzatore_mese_corrente()
            self.update_spese_mese_corrente()
            self.show_custom_warning("Spese", "Spese azzerate")
        def do_letture():
            dialog.destroy()
            if os.path.exists(UTENZE_DB):
             os.remove(UTENZE_DB)
            self.show_custom_warning("Letture", "Letture utenze azzerate")
        def do_rubrica():
            dialog.destroy()
            if os.path.exists(DATI_FILE):
             os.remove(DATI_FILE)
            self.show_custom_warning("Rubrica", "Dati Rubrica azzerate")
        def do_password():
            dialog.destroy()
            if os.path.exists(PW_FILE):
             os.remove(PW_FILE)
            self.show_custom_warning("Password", "Password azzerata")
        def do_cancel():
            dialog.destroy()
        tk.Button(btns, text="✅ Sì", command=do_yes, width=3, bg="#ff6666", fg="black").grid(row=0, column=0, padx=5)
        tk.Button(btns, text="❌ No", command=do_no, width=3, bg="#ffff66", fg="black").grid(row=0, column=1, padx=5)
        tk.Button(btns, text="📅 Letture", command=do_letture, width=9, bg="#ffcc66", fg="black").grid(row=0, column=2, padx=5)
        tk.Button(btns, text="📅 Rubrica", command=do_rubrica, width=9, bg="#cc99ff", fg="white").grid(row=0, column=3, padx=5)
        tk.Button(btns, text="📅 Password", command=do_password, width=9, bg="#ff6666", fg="white").grid(row=0, column=4, padx=5)
        tk.Button(btns, text="❌ Annulla", command=do_cancel, width=8, bg="#99ff99", fg="black").grid(row=0, column=5, padx=5)

        btns.focus_set()
        dialog.bind("<Escape>", lambda e: do_cancel())
        dialog.bind("<Return>", lambda e: do_yes())

    def export_giorno_forzato(self):
        old_mode = self.stats_mode.get()
        self.stats_mode.set("giorno")
        self.export_stats()
        self.stats_mode.set(old_mode)

    def export_stats(self):
        mode = self.stats_mode.get()
        lines = []
 
        label_width = 20
        desc_width = 30
        value_width = 14
        tipo_width = 10

        tot_entrate, tot_uscite = 0.0, 0.0

        if mode == "giorno":
            try:
                giorno = datetime.datetime.strptime(self.cal.get_date(), "%d-%m-%Y").date()
            except Exception:
                giorno = datetime.date.today()

            spese = self.spese.get(giorno, []) or self.spese.get(giorno.strftime("%d-%m-%Y"), [])
            header = f"{'Categoria':<{label_width}} {'Descrizione':<{desc_width}} {'Importo (€)':>{value_width}}  {'Tipo':<{tipo_width}}"
            sep = "-" * len(header)

            lines.append("=" * len(header))
            lines.append(f"{('STATISTICHE GIORNALIERE - ' + giorno.strftime('%d-%m-%Y')).center(len(header))}")
            lines.append("=" * len(header))
            lines.append("")
            lines.append(header)
            lines.append(sep)

            if not spese:
                lines.append("Nessuna spesa trovata per il giorno selezionato.")
            else:
                for entry in spese:
                    cat, desc, imp, tipo = entry[:4]
                    lines.append(f"{cat:<{label_width}.{label_width}} {desc:<{desc_width}.{desc_width}} {imp:>{value_width}.2f}  {tipo:<{tipo_width}}")
                    if tipo == "Entrata":
                        tot_entrate += imp
                    else:
                        tot_uscite += imp

            lines.append(sep)

        else:
            totali = {}
            tipo_cat = {}
            ref = self.stats_refdate

            if mode == "mese":
                year, month = ref.year, ref.month
                monthname = self.get_month_name(month)
                title = f"STATISTICHE MENSILI - {monthname} {year}"
            elif mode == "anno":
                year = ref.year
                title = f"STATISTICHE ANNUALI - ANNO {year}"
            else:
                title = "STATISTICHE TOTALI PER CATEGORIA"

            header = f"{'Categoria':<{label_width}} {'Totale (€)':>{value_width}}  {'Tipo':<{tipo_width}}"
            sep = "-" * len(header)

            lines.append("=" * len(header))
            lines.append(title.center(len(header)))
            lines.append("=" * len(header))
            lines.append("")
            lines.append(header)
            lines.append(sep)

            for d, sp in self.spese.items():
                try:
                    d2 = datetime.datetime.strptime(d, "%d-%m-%Y").date() if isinstance(d, str) else d
                except:
                    continue

                if (mode == "mese" and d2.year == year and d2.month == month) or \
                   (mode == "anno" and d2.year == year) or \
                   (mode == "totali"):
                    for entry in sp:
                        cat, desc, imp, tipo = entry[:4]
                        totali[cat] = totali.get(cat, 0.0) + imp
                        tipo_cat[cat] = self.categorie_tipi.get(cat, tipo)

            for cat in sorted(totali.keys()):
                val = totali[cat]
                tipo = tipo_cat.get(cat, "Uscita")
                lines.append(f"{cat:<{label_width}.{label_width}} {val:>{value_width}.2f}  {tipo:<{tipo_width}}")
                if tipo == "Entrata":
                    tot_entrate += val
                else:
                    tot_uscite += val

            lines.append(sep)

        diff = tot_entrate - tot_uscite
        lines.append(f"{'Totale Entrate:':<{label_width}} {tot_entrate:>{value_width}.2f}")
        lines.append(f"{'Totale Uscite:':<{label_width}} {tot_uscite:>{value_width}.2f}")
        lines.append(f"{'Differenza:':<{label_width}} {diff:>{value_width}.2f} €")
        lines.append("=" * max(len(header), label_width + value_width + tipo_width + 3))

        self.show_export_preview("\n".join(lines))
        

    def export_month_detail(self):
        ref = self.stats_refdate
        month = ref.month
        year = ref.year
        monthname = self.get_month_name(month)

        giorni_settimana = [
            "Lunedì", "Martedì", "Mercoledì", "Giovedì",
            "Venerdì", "Sabato", "Domenica"
        ]

        lines = []
        tot_entrate, tot_uscite = 0.0, 0.0

        lines.append("=" * 100)
        lines.append(f"{('Spese per il mese di ' + monthname + ' ' + str(year)).center(100)}")
        lines.append("=" * 100 + "\n")

        days_in_month = [
            d for d in sorted(self.spese.keys())
            if d.year == year and d.month == month
        ]

        if not days_in_month:
            lines.append("Nessuna spesa registrata in questo mese.\n")
        else:
            for d in days_in_month:
                giorno_it = giorni_settimana[d.weekday()]
                lines.append(f"{giorno_it:<10} {d.strftime('%d/%m/%Y')}")
                lines.append("-" * 100)
                lines.append(f"{'':2}{'Categoria':<20}{'Descrizione':<40}{'Tipo':<10}{'Importo (€)':>14}")
                ent_giorno, usc_giorno = 0.0, 0.0
                for entry in self.spese.get(d, []):
                    if len(entry) >= 4:
                        cat, desc, imp, tipo = entry[:4]
                        lines.append(f"{'':2}{cat:<20.20}{desc:<40.40}{tipo:<10}{imp:14.2f}")
                        if tipo == "Entrata":
                            ent_giorno += imp
                            tot_entrate += imp
                        else:
                            usc_giorno += imp
                            tot_uscite += imp
                lines.append(f"\n{'':2}Totale giorno → Entrate: {ent_giorno:8.2f} €   Uscite: {usc_giorno:8.2f} €\n")

        lines.append("-" * 100)
        lines.append(f"{'Totale entrate mese:':<60}{tot_entrate:14.2f} €")
        lines.append(f"{'Totale uscite mese:':<60}{tot_uscite:14.2f} €")
        lines.append(f"{'Saldo finale:':<60}{(tot_entrate - tot_uscite):14.2f} €")

        # ✅ Riutilizza la stessa funzione di preview
        self.show_export_preview("\n".join(lines))


    def show_export_preview(self, content):
        """ Mostra la finestra di anteprima dell'esportazione con posizione fissa. """
        preview = tk.Toplevel(self)
        preview.withdraw()  
        preview.title("Anteprima Esportazione Statistiche")
        preview.resizable(False, False)  # Blocca il ridimensionamento
        
        larghezza_finestra = 1300
        altezza_finestra = 600

        def centra_finestra():
                screen_width = preview.winfo_screenwidth()
                screen_height = preview.winfo_screenheight()
                x = (screen_width - larghezza_finestra) // 2
                y = (screen_height - altezza_finestra) // 2
                preview.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
                preview.deiconify()
                preview.lift()
                preview.focus_force()

        preview.after(0, centra_finestra)
        preview.grab_set()

        text = tk.Text(preview, wrap="none", font=("Courier new", 10))
        text.insert("1.0", content)
        text.config(state="disabled")
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


        def save_file():
            """ Salva il contenuto dell'anteprima su file e chiude la finestra. """
            now = datetime.date.today()
            default_dir = EXPORT_FILES
            default_filename = f"Statistiche_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=default_dir,
                initialfile=default_filename,
                title="Salva Statistiche",
                parent=preview)
            if file:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)
                preview.destroy()
                self.show_custom_warning("Esportazione completata", f"Statistiche esportate in {file}")

        btn_frame = ttk.Frame(preview)
        btn_frame.pack(fill=tk.X, pady=8)

        btn_salva = ttk.Button(btn_frame, text="💾 Salva", command=save_file)
        btn_salva.pack(side=tk.LEFT, padx=10)

        btn_chiudi = ttk.Button(btn_frame, text="❌ Chiudi", command=preview.destroy)
        btn_chiudi.pack(side=tk.RIGHT, padx=10)

        preview.update() 
        
    def import_db(self):
        file = filedialog.askopenfilename(
            title="Importa Database",
            defaultextension=".json",
            initialdir=EXP_DB,
            filetypes=[("File JSON", "*.json"), ("Tutti i file", "*.*")]
        )
        if file:
            try:
                with open(file, "r", encoding="utf-8") as fsrc:
                    dbdata = fsrc.read()
                with open(EXP_DB, "w", encoding="utf-8") as fdst:
                    fdst.write(dbdata)
                self.load_db()
                self.cat_menu["values"] = self.categorie
                self.cat_mod_menu["values"] = self.categorie
                if self.categorie:
                    self.cat_sel.set(self.categorie[0])
                    self.cat_mod_sel.set(self.categorie[0])
                self.update_stats()
                self.update_totalizzatore_anno_corrente()
                self.update_totalizzatore_mese_corrente()
                self.update_spese_mese_corrente()
                self.show_custom_warning("Importazione completata", f"Database importato da {file}")
            except Exception as e:
                self.show_custom_warning("Errore", "Errore durante l'esportazione:", f"{e}")

    def export_db(self):
        now = datetime.date.today()
        default_dir = EXP_DB
        default_filename = f"Export_Database{now.day:02d}-{now.month:02d}-{now.year}.json"
        file = filedialog.asksaveasfilename(
            title="Esporta Database",
            defaultextension=".json",
            initialdir=default_dir,
            initialfile=default_filename,
            filetypes=[("File JSON", "*.json"), ("Tutti i file", "*.*")]
        )
        if file:
            try:
                with open(DB_FILE, "r", encoding="utf-8") as fsrc:
                    dbdata = fsrc.read()
                with open(file, "w", encoding="utf-8") as fdst:
                    fdst.write(dbdata)
                self.show_custom_warning("Esportazione completata", f"Database esportato in {file}")
            except Exception as e:
                self.show_custom_warning("Errore", "Errore durante l'esportazione:", f"{e}")

    def export_anno_dettagliato(self):
        try:
            year = int(self.estratto_year_var.get())
        except Exception:
            year = datetime.date.today().year

        mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
                "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        label_width = 22

        categorie = sorted(
            set(
                entry[0]
                for sp in self.spese.values()
                for entry in sp
                if isinstance(entry, (list, tuple)) and len(entry) >= 4
            ).union(self.categorie)
        )

        tot_entrate_mese = [0.0] * 12
        tot_uscite_mese = [0.0] * 12
        cat_entrate = {cat: [0.0] * 12 for cat in categorie}
        cat_uscite = {cat: [0.0] * 12 for cat in categorie}
        tot_entrate_anno = 0.0
        tot_uscite_anno = 0.0

        def date_from_key(d):
            if isinstance(d, datetime.date):
                return d
            try:
                return datetime.datetime.strptime(d, "%d-%m-%Y").date()
            except:
                return None

        for d, sp in self.spese.items():
            d2 = date_from_key(d)
            if d2 and d2.year == year:
                m = d2.month - 1
                for entry in sp:
                    if len(entry) >= 4:
                        cat, desc, imp, tipo = entry[:4]
                        if tipo == "Entrata":
                            tot_entrate_mese[m] += imp
                            tot_entrate_anno += imp
                            cat_entrate[cat][m] += imp
                        else:
                            tot_uscite_mese[m] += imp
                            tot_uscite_anno += imp
                            cat_uscite[cat][m] += imp

        def format_row(label, values):
            label_fmt = f"{label:<{label_width}.{label_width}}"
            numeri = "".join(f"{v:10.2f}" for v in values)
            return f"{label_fmt}{numeri}{sum(values):12.2f}"

        header = f"{'Categoria':<{label_width}}" + "".join(f"{m:>10}" for m in mesi) + f"{'Totale':>12}"

        sep = "-" * len(header)

        lines = []
        lines.append("=" * len(header))
        lines.append(f"{('REPORT ENTRATE/USCITE ANNO ' + str(year)).center(len(header))}")
        lines.append("=" * len(header))
        lines.append("")

        lines.append(header)
        lines.append(sep)
        lines.append("")

        lines.append("ENTRATE PER CATEGORIA:")
        lines.append(header)
        for cat in categorie:
            if any(cat_entrate[cat]):
                lines.append(format_row(cat, cat_entrate[cat]))
        lines.append(sep)
        lines.append(format_row("• Totale Entrate", tot_entrate_mese))
        lines.append(sep)
        lines.append("")

        
        lines.append("USCITE PER CATEGORIA:")
        lines.append(header)
        for cat in categorie:
            if any(cat_uscite[cat]):
                lines.append(format_row(cat, cat_uscite[cat]))
        lines.append("")

        lines.append(sep)
        lines.append(format_row("• Totale Uscite", tot_uscite_mese))
        lines.append("-" * len(header))
        saldo = tot_entrate_anno - tot_uscite_anno
        lines.append(f"{'SALDO FINALE:':<{label_width}}{saldo:>{len(header) - label_width}.2f} €")
        lines.append("=" * len(header))

        text = "\n".join(lines)

        self.show_export_preview("\n".join(lines))

    def open_analisi_categoria(self):
        popup = tk.Toplevel(self)
        popup.title("Analisi Categoria")
        popup.geometry("700x600")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
    
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 350
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 300
        popup.geometry(f"+{x}+{y}")
  
        frame_top = ttk.Frame(popup)
        frame_top.pack(padx=18, pady=10, fill=tk.X)
        ttk.Label(frame_top, text="🔍 Seleziona modalità:").pack(side=tk.LEFT)
        mode_var = tk.StringVar(value="Giorno")
        mode_combo = ttk.Combobox(frame_top, values=["Giorno", "Mese", "Anno", "Totale"], textvariable=mode_var, state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=10)
    
        frame_period = ttk.Frame(popup)
        frame_period.pack(padx=18, pady=2, fill=tk.X)
    
        months = [
            "01 - Gennaio", "02 - Febbraio", "03 - Marzo", "04 - Aprile", "05 - Maggio", "06 - Giugno",
            "07 - Luglio", "08 - Agosto", "09 - Settembre", "10 - Ottobre", "11 - Novembre", "12 - Dicembre"
        ]
        today = datetime.date.today()
        current_year = today.year
    
        day_var = tk.StringVar(value=str(today.day))
        month_var = tk.StringVar(value=months[today.month - 1])
        year_var = tk.StringVar(value=str(today.year))
    
        def get_years(center=None):
            if center is None:
                center = datetime.date.today().year
            return [str(y) for y in range(center-10, center+11)]
    
        year_combo = ttk.Combobox(frame_period, values=get_years(current_year), textvariable=year_var, state="readonly", width=8)
        month_combo = ttk.Combobox(frame_period, values=months, textvariable=month_var, state="readonly", width=16)
        day_combo = ttk.Combobox(frame_period, values=[str(d) for d in range(1, 32)], textvariable=day_var, state="readonly", width=4)
        year_combo_only = ttk.Combobox(frame_period, values=get_years(current_year), textvariable=year_var, state="readonly", width=8)

        def update_days(*_):
            try:
                m = months.index(month_var.get()) + 1
                y = int(year_var.get())
            except Exception:
                m = today.month
                y = today.year
            n_days = calendar.monthrange(y, m)[1]
            days = [str(d) for d in range(1, n_days+1)]
            day_combo['values'] = days
            if day_var.get() not in days:
                day_var.set(days[-1])
        month_var.trace_add("write", update_days)
        year_var.trace_add("write", update_days)
     
        def reset_period():
            oggi = datetime.date.today()
            day_var.set(str(oggi.day))
            month_var.set(months[oggi.month - 1])
            year_var.set(str(oggi.year))
    
        def update_period_inputs(*_):
            for widget in frame_period.winfo_children():
                widget.pack_forget()
            mode = mode_var.get()
            if mode == "Giorno":
                day_combo.pack(side=tk.LEFT)
                month_combo.pack(side=tk.LEFT, padx=(4,8))
                year_combo.pack(side=tk.LEFT)
                reset_btn = ttk.Button(frame_period, text="Reset", width=8, command=reset_period)
                reset_btn.pack(side=tk.LEFT, padx=(10, 0))
                update_days()
            elif mode == "Mese":
                month_combo.pack(side=tk.LEFT, padx=(0,8))
                year_combo.pack(side=tk.LEFT)
                reset_btn = ttk.Button(frame_period, text="Reset", width=8, command=reset_period)
                reset_btn.pack(side=tk.LEFT, padx=(10, 0))
            elif mode == "Anno":
                year_combo_only.pack(side=tk.LEFT)
                reset_btn = ttk.Button(frame_period, text="Reset", width=8, command=reset_period)
                reset_btn.pack(side=tk.LEFT, padx=(10, 0))
        mode_combo.bind("<<ComboboxSelected>>", update_period_inputs)
        update_period_inputs()

        def update_years(*_):
            try:
                y = int(year_var.get())
            except Exception:
                y = datetime.date.today().year
            year_combo['values'] = get_years(y)
            year_combo_only['values'] = get_years(y)
            update_days()
        year_var.trace_add("write", update_years)
    
        frame_cat = ttk.Frame(popup)
        frame_cat.pack(padx=18, pady=12, fill=tk.X)
        ttk.Label(frame_cat, text="Categoria:").pack(side=tk.LEFT)
        def get_catlist():
            return ["Tutte le categorie"] + sorted(self.categorie)
        cat_var = tk.StringVar(value="Tutte le categorie")
        cat_combo = ttk.Combobox(frame_cat, values=get_catlist(), textvariable=cat_var, state="readonly", width=25)
        cat_combo.pack(side=tk.LEFT, padx=10)
 
        main_result_frame = ttk.Frame(popup)
        main_result_frame.pack(padx=18, fill=tk.BOTH, expand=True)
        text_result = tk.Text(main_result_frame, height=22, width=90, font=("Arial", 10), wrap='none')
        text_result.pack(fill=tk.BOTH, expand=True)
        frame_buttons = ttk.Frame(main_result_frame)
        frame_buttons.pack(fill=tk.X, pady=8)
        export_btn = ttk.Button(frame_buttons, text="💾 Esporta", width=15)
        export_btn.pack(side=tk.LEFT, padx=4)
        
        close_btn = ttk.Button(frame_buttons, text="❌ Chiudi", width=15, command=popup.destroy)
        close_btn.pack(side=tk.RIGHT, padx=4)

        def aggiorna_cat_combo():
            cat_combo['values'] = get_catlist()
            if cat_var.get() not in cat_combo['values']:
                cat_var.set("Tutte le categorie")
        aggiorna_cat_combo()
    
        def mostra_dettagli(*_):
            cat = cat_var.get()
            mode = mode_var.get()
            result_lines = []
            ENTRATA_CAT = "Entrata"
            today = datetime.date.today()

            def calcola_totali(entries):
                entrate = sum(e[2] for _, e in filtered if "entrata" in e[3].lower())
                uscite  = sum(e[2] for _, e in filtered if "entrata" not in e[3].lower())
                return entrate, uscite, entrate - uscite  

            filtered = []
            label_intestazione = ""

            if mode == "Giorno":
                try:
                    m = months.index(month_var.get()) + 1
                    d = int(day_var.get())
                    y = int(year_var.get())
                    giorno = datetime.date(y, m, d)
                except Exception:
                    giorno = today
                spese = self.spese.get(giorno, [])
                filtered = [(giorno, e) for e in spese if cat == "Tutte le categorie" or e[0] == cat]
                label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} per il giorno {giorno.strftime('%d-%m-%Y')}"

            elif mode == "Mese":
                try:
                    m = months.index(month_var.get()) + 1
                    y = int(year_var.get())
                except Exception:
                    m = today.month
                    y = today.year
                for d, sp in self.spese.items():
                    if d.year == y and d.month == m:
                        for e in sp:
                            if cat == "Tutte le categorie" or e[0] == cat:
                                filtered.append((d, e))
                label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} per {self.get_month_name(m)} {y}"

            elif mode == "Anno":
                try:
                    y = int(year_var.get())
                except Exception:
                    y = today.year
                for d, sp in self.spese.items():
                    if d.year == y:
                        for e in sp:
                            if cat == "Tutte le categorie" or e[0] == cat:
                                filtered.append((d, e))
                label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} per l'anno {y}"

            elif mode == "Totale":
                for d, sp in self.spese.items():
                    for e in sp:
                        if cat == "Tutte le categorie" or e[0] == cat:
                            filtered.append((d, e))
                label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} totali"

            text_result.configure(font=("Courier New", 10))
            result_lines.clear()

            if not filtered:
                result_lines.append(f"Nessuna spesa per '{cat}'.")
            else:
                result_lines.append("=" * 80)
                result_lines.append(label_intestazione)
                result_lines.append("-" * 80)
                result_lines.append(f"{'Data':<12}  {'Categoria':<12}  {'Descrizione':<25}  {'Importo':>10}")
                result_lines.append("-" * 80)

                for d, e in sorted(filtered, key=lambda x: x[0]):
                    valore = abs(e[2])
                    categoria = e[0][:12] if len(e[0]) > 12 else e[0]
                    descrizione = e[1][:25] if len(e[1]) > 25 else e[1]
                    f"{categoria:<12}  {descrizione:<25}"
                    result_lines.append(
                        f"{d.strftime('%d-%m-%Y'):<12}  {categoria:<12}  {descrizione:<25}  {valore:>9.2f} € ({e[3]})"
                    )

                result_lines.append("-" * 80)
                entrate, uscite, saldo = calcola_totali([e for _, e in filtered])
                result_lines.append(f"{'Totale entrate':<54}  {entrate:>9.2f} €")
                result_lines.append(f"{'Totale uscite':<54}  {uscite:>9.2f} €")
                result_lines.append(f"{'Saldo finale':<54}  {saldo:+9.2f} €")
                result_lines.append("=" * 80)

            text_result.delete("1.0", tk.END)
            text_result.insert("end", "\n".join(result_lines))

        def esporta_analisi():
            contenuto = text_result.get("1.0", tk.END).strip()
            if not contenuto:
                self.show_custom_warning("Esporta", "Nulla da esportare.")
                return
            preview = tk.Toplevel(popup)
            preview.title("Preview esportazione")
            preview.geometry("800x500")
            preview.transient(popup)
            preview.grab_set()
            preview.focus_set()
            tx = tk.Text(preview, font=("Courier new", 10), wrap="none")
            tx.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            contenuto_preview = "\n".join(" " + l for l in contenuto.splitlines())

            tx.insert(tk.END, contenuto_preview)
            tx.config(state="disabled")
            frm = ttk.Frame(preview)
            frm.pack(fill=tk.X, padx=10, pady=8)
            def do_save():
                now = datetime.date.today()
                default_dir = EXPORT_FILES
                default_filename = f"Analisi_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
                file = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("File txt", "*.txt")],
                    initialdir=default_dir,
                    title="Esporta Analisi Categoria",
                    initialfile=default_filename,
                    parent=preview)
                if file:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto_preview)
                        self.show_custom_warning("Esporta", f"Analisi esportata in {file}")
                    preview.destroy()
            ttk.Button(frm, text="💾 Salva", command=do_save, width=15).pack(side=tk.LEFT, padx=6)
            ttk.Button(frm, text="❌ Chiudi", command=preview.destroy, width=12).pack(side=tk.RIGHT, padx=6)
            preview.lift()
            preview.attributes('-topmost', True)
            preview.after(100, lambda: preview.attributes('-topmost', False))
    
        export_btn.config(command=esporta_analisi)
 
        mode_var.trace_add("write", mostra_dettagli)
        month_var.trace_add("write", mostra_dettagli)
        year_var.trace_add("write", mostra_dettagli)
        day_var.trace_add("write", mostra_dettagli)
        cat_var.trace_add("write", mostra_dettagli)
    
        mostra_dettagli()
        

    def open_saldo_conto(self):
        popup = tk.Toplevel(self)
        popup.title("Saldo Conto Corrente")
        popup.geometry("480x480")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
    
        saldo_data = {"saldo": 0.0, "data": datetime.date.today().strftime("%d-%m-%Y")}
        if os.path.exists(SALDO_FILE):
            try:
                with open(SALDO_FILE, "r", encoding="utf-8") as f:
                     db = json.load(f)
                saldo_data["saldo"] = db.get("saldo", 0.0)
                saldo_data["data"] = db.get("saldo_data", saldo_data["data"])
            except Exception:
                pass
    
        frame = ttk.Frame(popup)
        frame.pack(padx=28, pady=18, fill=tk.BOTH, expand=True)
    
        lastframe = ttk.LabelFrame(frame, text="Ultimo saldo inserito", padding=10)
        lastframe.pack(fill=tk.X, padx=0, pady=(0, 18))
    
        last_saldo_var = tk.StringVar(value=f"{saldo_data['saldo']:.2f}")
        last_data_var = tk.StringVar(value=saldo_data["data"])
    
        ttk.Label(lastframe, text="💰 Ultimo saldo:", font=("Arial", 11)).grid(row=0, column=0, sticky="e", padx=(0,8), pady=2)
        ttk.Entry(lastframe, textvariable=last_saldo_var, width=15, font=("Arial", 11), state="readonly").grid(row=0, column=1, padx=(0,8), pady=2)
        ttk.Label(lastframe, text="€", font=("Arial", 11)).grid(row=0, column=2, sticky="w", pady=2)
    
        ttk.Label(lastframe, text="📅 Data inserimento:", font=("Arial", 11)).grid(row=1, column=0, sticky="e", padx=(0,8), pady=2)
        ttk.Entry(lastframe, textvariable=last_data_var, width=12, font=("Arial", 11), state="readonly").grid(row=1, column=1, pady=2, sticky="w")
    
        btmframe = ttk.LabelFrame(frame, text="🔄 Aggiorna saldo bancario", padding=10)
        btmframe.pack(fill=tk.X, padx=0, pady=(0, 0))
    
        try:
            default_dt = datetime.datetime.strptime(saldo_data["data"], "%d-%m-%Y").date()
        except Exception:
            default_dt = datetime.date.today()
    
        anni = list(range(default_dt.year - 5, default_dt.year + 6))
        mesi = list(range(1, 13))
        giorni = list(range(1, 32))
    
        ttk.Label(btmframe, text="Data saldo:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e", padx=(0,8), pady=2)
        day_var = tk.StringVar(value=f"{default_dt.day:02d}")
        month_var = tk.StringVar(value=f"{default_dt.month:02d}")
        year_var = tk.StringVar(value=str(default_dt.year))
    
        ttk.Combobox(btmframe, textvariable=day_var, values=[f"{g:02d}" for g in giorni], width=4, state="readonly").grid(row=0, column=1, sticky="w", padx=(0,2))
        ttk.Combobox(btmframe, textvariable=month_var, values=[f"{m:02d}" for m in mesi], width=4, state="readonly").grid(row=0, column=2, sticky="w", padx=(0,2))
        ttk.Combobox(btmframe, textvariable=year_var, values=[str(a) for a in anni], width=6, state="readonly").grid(row=0, column=3, sticky="w", padx=(0,6))
    
        ttk.Button(btmframe, text="↺", width=2, command=lambda: [
            day_var.set(f"{datetime.date.today().day:02d}"),
            month_var.set(f"{datetime.date.today().month:02d}"),
            year_var.set(str(datetime.date.today().year))
        ]).grid(row=0, column=4)
    
        ttk.Label(btmframe, text="Nuovo saldo:", font=("Arial", 11)).grid(row=1, column=0, sticky="e", pady=(14,2))
        saldo_var = tk.StringVar()
        ttk.Entry(btmframe, textvariable=saldo_var, width=15, font=("Arial", 11)).grid(row=1, column=1, columnspan=2, sticky="w", padx=4, pady=(14,2))
        ttk.Label(btmframe, text="€", font=("Arial", 11)).grid(row=1, column=3, sticky="w", pady=(14,2))
    
        data_var = tk.StringVar()
        def aggiorna_data_var(*_):
            data_var.set(f"{day_var.get()}-{month_var.get()}-{year_var.get()}")
        day_var.trace_add("write", aggiorna_data_var)
        month_var.trace_add("write", aggiorna_data_var)
        year_var.trace_add("write", aggiorna_data_var)
        aggiorna_data_var()
    
        lbl_saldo_mese = ttk.Label(frame, text="", font=("Arial", 11))
        lbl_saldo_anno = ttk.Label(frame, text="", font=("Arial", 11))
        lbl_saldo_tot = ttk.Label(frame, text="", font=("Arial", 11, "bold"))
        lbl_saldo_mese.pack(anchor="w", pady=(20, 0))
        lbl_saldo_anno.pack(anchor="w")
        lbl_saldo_tot.pack(anchor="w", pady=(0, 12))
    
        def get_selected_date():
            try:
                return datetime.datetime.strptime(data_var.get(), "%d-%m-%Y").date()
            except Exception:
                return datetime.date.today()
    
        def calcola_saldo(filtro):
            try:
                saldo = float(last_saldo_var.get())
            except Exception:
                saldo = 0.0
    
            data_saldo = get_selected_date()
            mese = data_saldo.month
            anno = data_saldo.year
    
            saldo_mese = saldo
            saldo_anno = saldo
            saldo_totale = saldo
    
            for d in sorted(self.spese.keys()):
                if d < data_saldo:
                    continue
                for entry in self.spese[d]:
                    imp = entry[2]
                    tipo = entry[3]
                    if tipo == "Entrata":
                        saldo_totale += imp
                        if d.year == anno:
                            saldo_anno += imp
                            if d.month == mese:
                                saldo_mese += imp
                    else:
                        saldo_totale -= imp
                        if d.year == anno:
                            saldo_anno -= imp
                            if d.month == mese:
                                saldo_mese -= imp
    
            return {"mese": saldo_mese, "anno": saldo_anno, "totale": saldo_totale}[filtro]
    
        def aggiorna_saldi(*_):
            lbl_saldo_mese.config(text=f"Saldo nel mese: {calcola_saldo('mese'):.2f} €")
            lbl_saldo_anno.config(text=f"Saldo nell'anno: {calcola_saldo('anno'):.2f} €")
            lbl_saldo_tot.config(text=f"Saldo totale    : {calcola_saldo('totale'):.2f} €")
    
        data_var.trace_add("write", aggiorna_saldi)
        aggiorna_saldi()
    
        def custom_warning(msg, parent):
            win = tk.Toplevel(parent)
            win.title("Avviso")
            win.configure(bg="#ffffcc")
            win.resizable(False, False)
            win.grab_set()
            win.geometry("420x140")
            ttk.Label(win, text=msg, background="#ffffcc", font=("Arial", 10)).pack(padx=20, pady=20)
            ttk.Button(win, text="OK", command=win.destroy).pack(pady=(0,16))
            win.transient(parent)
            win.lift()
            win.focus_force()
            win.attributes('-topmost', True)
            win.after(200, lambda: win.attributes('-topmost', False))
    
        def salva_saldo():
            try:
                nuovo_saldo = float(saldo_var.get().replace(",", "."))
                nuova_data = data_var.get()

                last_saldo_var.set(f"{nuovo_saldo:.2f}")
                last_data_var.set(nuova_data)

                # Leggi il file, oppure crea un dizionario nuovo
                db = {}
                if os.path.exists(SALDO_FILE):
                    try:
                        with open(SALDO_FILE, "r", encoding="utf-8") as f:
                            db = json.load(f)
                    except json.JSONDecodeError:
                        db = {}

                db["saldo"] = nuovo_saldo
                db["saldo_data"] = nuova_data

                with open(SALDO_FILE, "w", encoding="utf-8") as f:
                    json.dump(db, f, indent=2, ensure_ascii=False)
          
                saldo_var.set("")
                aggiorna_saldi()
                custom_warning("✅ Saldo aggiornato correttamente.", popup)
            except ValueError:
                custom_warning("❌ Inserisci un numero valido come saldo.", popup)

    
        def esporta():
            sm = calcola_saldo("mese")
            sa = calcola_saldo("anno")
            st = calcola_saldo("totale")
    
            lines = [
                f"Saldo inserito il {last_data_var.get()}: {last_saldo_var.get()} €",
                f"Saldo nel mese: {sm:.2f} €",
                f"Saldo nell'anno: {sa:.2f} €",
                f"Saldo totale: {st:.2f} €",
            ]
    
            preview = tk.Toplevel(popup)
            preview.title("Esporta saldo")
            preview.geometry("420x200")
            preview.transient(popup)
            preview.grab_set()
    
            txt = tk.Text(preview, font=("Arial", 10), wrap="word", height=6)
            txt.insert("1.0", "\n".join(lines))
            txt.configure(state="disabled")
            txt.pack(fill="both", expand=True, padx=10, pady=10)
    
            def do_save():
                default_dir = EXPORT_FILES
                default_filename = f"Saldo_Export_{datetime.date.today().strftime('%d-%m-%Y')}.txt"
                path = filedialog.asksaveasfilename(
                    initialfile= default_filename,
                    initialdir=default_dir,
                    defaultextension=".txt",
                    title="Salva Saldo",
                    filetypes=[("File di testo", "*.txt")],
                    parent=preview
                )
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                    custom_warning("✅ Esportazione completata.", preview)
    
            btns = ttk.Frame(preview)
            btns.pack(pady=10)
            ttk.Button(btns, text="💾 Salva", command=do_save, width=12).pack(side="left", padx=6)
            ttk.Button(btns, text="❌ Chiudi", command=preview.destroy, width=10).pack(side="right", padx=6)
    
        # Pulsanti finali
        btn_frame = ttk.Frame(popup)
        btn_frame.pack(pady=(12, 10))
        style = ttk.Style()
        style.configure("SalvaSaldo.TButton", background="#FF6666", foreground="black")
        style.configure("PreviewEsporta.TButton", background="#ADD8E6", foreground="black")
        style.configure("Chiudi.TButton", background="yellow", foreground="black")
    
        ttk.Button(btn_frame, text="💾 Salva saldo", command=salva_saldo, style="SalvaSaldo.TButton").pack(side="left", padx=6)
        ttk.Button(btn_frame, text="📄 Preview/Esporta", command=esporta, style="PreviewEsporta.TButton").pack(side="left", padx=6)
        ttk.Button(btn_frame, text="❌ Chiudi", command=popup.destroy, style="Chiudi.TButton").pack(side="right", padx=6)
            
    def goto_today(self):
        today = datetime.date.today()
        self.cal.selection_set(today)
        self.stats_refdate = today
        self.update_stats()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()

    def open_compare_window(self):
        today = datetime.date.today()
        mese_oggi = f"{today.month:02d}"
        anno_oggi = str(today.year)    
        compare_by_year = tk.BooleanVar(value=False)
    
        def get_rows(mese, anno, per_anno=False):
            rows = []
            for d in sorted(self.spese):
                if (per_anno and d.year == anno) or (not per_anno and d.month == mese and d.year == anno):
                    for voce in self.spese[d]:
                        cat = voce[0]
                        imp = voce[2]
                        tipo = voce[3]
                        data_pagamento = d.strftime("%d-%m-%Y")
                        entrata = imp if tipo == "Entrata" else 0
                        uscita = imp if tipo == "Uscita" else 0
                        rows.append((cat, data_pagamento, entrata, uscita))
            return rows
    
        win = tk.Toplevel(self)
        win.title("Confronta mesi/anni per categoria")
        win.geometry("1035x510")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
    
        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
    
        anni_spese = set(d.year for d in self.spese.keys())
        anno_corrente = today.year
        anni = sorted(list(set(list(range(anno_corrente-10, anno_corrente+11))).union(anni_spese)))
        mesi = [f"{i:02d}" for i in range(1, 13)]
  
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,8))
        tk.Label(mode_frame, text="Modalità confronto:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(mode_frame, text="Mese", variable=compare_by_year, value=False, command=lambda: update_tables()).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Anno", variable=compare_by_year, value=True, command=lambda: update_tables()).pack(side=tk.LEFT)
   
        left = ttk.Frame(frame)
        left.grid(row=2, column=0, sticky="nswe", padx=(0,16))
        left_select_frame = ttk.Frame(frame)
        left_select_frame.grid(row=1, column=0, sticky="ew", padx=(0,16), pady=(0,6))
        tk.Label(left_select_frame, text="Mese/Anno 1", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0,8))
        left_mese = tk.StringVar(value=mese_oggi)
        left_anno = tk.StringVar(value=anno_oggi)
        cb_lm = ttk.Combobox(left_select_frame, textvariable=left_mese, values=mesi, width=4, state="readonly", font=("Arial", 10))
        cb_la = ttk.Combobox(left_select_frame, textvariable=left_anno, values=[str(a) for a in anni], width=7, state="readonly", font=("Arial", 10))
        cb_lm.pack(side="left", padx=(0,3))
        cb_la.pack(side="left")
        def reset_left():
            left_mese.set(mese_oggi)
            left_anno.set(anno_oggi)
        ttk.Button(left_select_frame, text="Reset", command=reset_left, width=6).pack(side=tk.RIGHT, padx=7)
        left_tree = ttk.Treeview(left, columns=("Categoria","Data","Entrata","Uscita"), show="headings", height=12)
        style = ttk.Style()
        style.configure("Big.Treeview.Heading", font=("Arial", 10, "bold"))
        style.configure("Big.Treeview", font=("Arial", 10))
        left_tree.configure(style="Big.Treeview")
        for col, w, anchor in [("Categoria",180,"w"),("Data",110,"center"),("Entrata",100,"e"),("Uscita",100,"e")]:
            left_tree.heading(col, text=col, anchor=anchor)
            left_tree.column(col, width=w, anchor=anchor, stretch=True)
        left_tree.pack(fill=tk.BOTH, expand=True)
        left_diff_lbl = tk.Label(left, text="", font=("Arial", 10, "bold"))
        left_diff_lbl.pack(pady=(4,0))
   
        right = ttk.Frame(frame)
        right.grid(row=2, column=1, sticky="nswe")
        right_select_frame = ttk.Frame(frame)
        right_select_frame.grid(row=1, column=1, sticky="ew", pady=(0,6))
        tk.Label(right_select_frame, text="Mese/Anno 2", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0,8))
        right_mese = tk.StringVar(value=mese_oggi)
        right_anno = tk.StringVar(value=anno_oggi)
        cb_rm = ttk.Combobox(right_select_frame, textvariable=right_mese, values=mesi, width=4, state="readonly", font=("Arial", 10))
        cb_ra = ttk.Combobox(right_select_frame, textvariable=right_anno, values=[str(a) for a in anni], width=7, state="readonly", font=("Arial", 10))
        cb_rm.pack(side="left", padx=(0,3))
        cb_ra.pack(side="left")
        def reset_right():
            right_mese.set(mese_oggi)
            right_anno.set(anno_oggi)
        ttk.Button(right_select_frame, text="Reset", command=reset_right, width=6).pack(side=tk.RIGHT, padx=7)
        right_tree = ttk.Treeview(right, columns=("Categoria","Data","Entrata","Uscita"), show="headings", height=12)
        right_tree.configure(style="Big.Treeview")
        for col, w, anchor in [("Categoria",180,"w"),("Data",110,"center"),("Entrata",100,"e"),("Uscita",100,"e")]:
            right_tree.heading(col, text=col, anchor=anchor)
            right_tree.column(col, width=w, anchor=anchor, stretch=True)
        right_tree.pack(fill=tk.BOTH, expand=True)
        right_diff_lbl = tk.Label(right, text="", font=("Arial", 10, "bold"))
        right_diff_lbl.pack(pady=(4,0))
    
        def update_month_visibility():
            if compare_by_year.get():
                cb_lm.pack_forget()
                cb_rm.pack_forget()
            else:
                if not cb_lm.winfo_ismapped():
                    cb_lm.pack(side="left", padx=(0,3))
                if not cb_rm.winfo_ismapped():
                    cb_rm.pack(side="left", padx=(0,3))
    
        def update_tables():
            update_month_visibility()
            per_anno = compare_by_year.get()
            a1 = int(left_anno.get())
            a2 = int(right_anno.get())
            m1 = int(left_mese.get()) if not per_anno else 1
            m2 = int(right_mese.get()) if not per_anno else 1
            rows1 = get_rows(m1, a1, per_anno=per_anno)
            rows2 = get_rows(m2, a2, per_anno=per_anno)
            left_tree.delete(*left_tree.get_children())
            right_tree.delete(*right_tree.get_children())
            tot_ent1 = tot_usc1 = 0
            for cat, data, ent, usc in rows1:
                left_tree.insert("", "end", values=(cat, data, f"{ent:.2f}", f"{usc:.2f}"))
                tot_ent1 += ent
                tot_usc1 += usc
            diff1 = tot_ent1 - tot_usc1
            left_diff_lbl.config(text=f"Totale entrate: {tot_ent1:.2f}   Totale uscite: {tot_usc1:.2f}   Differenza: {diff1:.2f} €", fg="blue" if diff1>=0 else "red")
            tot_ent2 = tot_usc2 = 0
            for cat, data, ent, usc in rows2:
                right_tree.insert("", "end", values=(cat, data, f"{ent:.2f}", f"{usc:.2f}"))
                tot_ent2 += ent
                tot_usc2 += usc
            diff2 = tot_ent2 - tot_usc2
            right_diff_lbl.config(text=f"Totale entrate: {tot_ent2:.2f}   Totale uscite: {tot_usc2:.2f}   Differenza: {diff2:.2f} €", fg="blue" if diff2>=0 else "red")
    
        for var in [left_mese, left_anno, right_mese, right_anno, compare_by_year]:
            var.trace_add("write", lambda *a: update_tables())
        update_tables()
    
        def do_preview_export():
            per_anno = compare_by_year.get()
            a1 = int(left_anno.get())
            a2 = int(right_anno.get())
            m1 = int(left_mese.get()) if not per_anno else 1
            m2 = int(right_mese.get()) if not per_anno else 1

            rows1 = get_rows(m1, a1, per_anno=per_anno)
            rows2 = get_rows(m2, a2, per_anno=per_anno)

            label1 = f"{m1:02d}/{str(a1)[-2:]}" if not per_anno else str(a1)
            label2 = f"{m2:02d}/{str(a1)[-2:]}" if not per_anno else str(a2)

            lines = []
            lines.append(f"Confronto tra {label1} e {label2}\n")
            lines.append(
                f"{'Categoria':18} {'Data':12} "
                f"{'Entrate ' + label1[-5:]:>12} {'Uscite ' + label1[-5:]:>12}  "
                f"{'Entrate ' + label2[-5:]:>12} {'Uscite ' + label2[-5:]:>12}  "
                f"{'Δ Entrate':>12} {'Δ Uscite':>12}"
            )

            lines.append("-" * 120)

            d1 = {(cat, data): (ent, usc) for cat, data, ent, usc in rows1}
            d2 = {(cat, data): (ent, usc) for cat, data, ent, usc in rows2}
            tutte_le_chiavi = sorted(set(d1.keys()) | set(d2.keys()))

            for cat, data in tutte_le_chiavi:
                ent1, usc1 = d1.get((cat, data), (0.0, 0.0))
                ent2, usc2 = d2.get((cat, data), (0.0, 0.0))
                diff_ent = ent2 - ent1
                diff_usc = usc2 - usc1
                lines.append(
                    f"{cat:18.18} {data:12} "
                    f"{ent1:12.2f} {usc1:12.2f}  "
                    f"{ent2:12.2f} {usc2:12.2f}  "
                    f"{diff_ent:12.2f} {diff_usc:12.2f}"
                )

            tot_ent1 = sum(ent for _, _, ent, _ in rows1)
            tot_usc1 = sum(usc for _, _, _, usc in rows1)
            diff1 = tot_ent1 - tot_usc1
            tot_ent2 = sum(ent for _, _, ent, _ in rows2)
            tot_usc2 = sum(usc for _, _, _, usc in rows2)
            diff2 = tot_ent2 - tot_usc2
            diff_ent_tot = tot_ent2 - tot_ent1
            diff_usc_tot = tot_usc2 - tot_usc1

            lines.append("-" * 120)
            lines.append(
                f"{'Totali':19} {'':12}"
                f"{tot_ent1:12.2f} {tot_usc1:12.2f}  "
                f"{tot_ent2:12.2f} {tot_usc2:12.2f}  "
                f"{diff_ent_tot:12.2f} {diff_usc_tot:12.2f}"
            )
            lines.append(
                f"{'Differenza':17} {'':12}"
                f"{'':57}{diff1:12.2f}{diff2:12.2f}"
            )

            text = "\n".join(lines)

            prev = tk.Toplevel(win)
            prev.title("Preview/Esporta confronto")
            prev.geometry("1200x580")
            prev.transient(win)
            prev.resizable(False, False)
         
            t = tk.Text(prev, font=("Courier New", 10), wrap="none")
            t.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
            t.insert(tk.END, text)
            t.config(state="disabled")
           
            def do_save():
                now = datetime.date.today()
                default_dir = EXPORT_FILES
                default_filename = f"Confronto_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
                file = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("File txt", "*.txt")],
                    initialdir=default_dir,
                    initialfile=default_filename,
                    title="Esporta confronto",
                    parent=prev)
                if file:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(text)
                    self.show_custom_warning("Esportazione completata", f"Tabella confronti esportata in:\n{file}")

            frm = ttk.Frame(prev)
            frm.pack(fill=tk.X, padx=10, pady=8)
            ttk.Button(frm, text="💾 Salva", command=do_save, width=15).pack(side=tk.LEFT, padx=6)
            ttk.Button(frm, text="❌ Chiudi", command=prev.destroy, width=12).pack(side=tk.RIGHT, padx=6)
            prev.lift()
            prev.focus_force()
            prev.attributes('-topmost', True)
            prev.after(100, lambda: prev.attributes('-topmost', False))
    
        btnframe = ttk.Frame(win)
        btnframe.pack(side=tk.BOTTOM, fill=tk.X, pady=(10,7))
        ttk.Button(btnframe, text="📄 Preview/Esporta", command=do_preview_export, width=18).pack(side=tk.LEFT, padx=8)
        ttk.Button(btnframe, text="❌ Chiudi", command=win.destroy, width=14).pack(side=tk.RIGHT, padx=8)

    def aggiorna(self, url, nome_file):
        """Scarica un file da GitHub e lo salva nella cartella corrente, creando un backup sicuro."""
        try:
            # Crea un backup del file esistente, se presente
            if os.path.exists(nome_file):
                nome_backup = f"{nome_file}.bak"
                try:
                    shutil.copy2(nome_file, nome_backup)  # Copia con metadati
                    print(f"Backup creato: {nome_backup}")
                except Exception as backup_err:
                    print(f"Errore durante la creazione del backup: {backup_err}")
                    self.show_custom_warning("Attenzione", "⚠️ Impossibile creare il backup. Aggiornamento annullato.")
                    return

            # Scarica il nuovo file
            urllib.request.urlretrieve(url, nome_file)
            print(f"Download completato! {nome_file} è stato aggiornato.")
            self.show_custom_warning("Attenzione", "Aggiornamento completato con successo \n\n 🚀 🔄 Riavviare il programma per applicare le modifiche !")
            return

        except Exception as e:
            print(f"Errore durante il download: {str(e)}")
            self.show_custom_warning("Attenzione", "❌ Aggiornamento NON completato ! \n\n Sembra ci sia stato un problema. 😕")
            return

    def show_info_app(self):
    
            info = (
                "Casa FacilePro\n"
                f"Versione v.{VERSION}\n"
                " © 2025 Casa Facile Pro - Sviluppo Python/Tkinter, 2023-2025 Email: helpcasafacilepro@gmail.com \n\n"
                "Funzionalità principali:\n"
                "• Inserimento, modifica e cancellazione di spese ed entrate per categoria\n"
                "• Gestione categorie personalizzate\n"
                "• Gestione Ricorrenze (spese/entrate ripetute)\n"
                "• Esportazione dettagliata giorno/mese/anno/utenze (Formato stampabile)\n"
                "• Statistiche giornaliere, mensili, annuali e totali e analisi categorie, Bonus Time Machine\n"
                "• Backup, import/export database, Rubrica personale , Gestione utenze, Cerca, ...\n"
                "• Usa i pulsanti in alto per scegliere la modalità di visualizzazione delle statistiche (Giorno, Mese, Anno, Totali).\n"
                "• Per esportare,visualizzare,stampare  le statistiche, usa 'Estrai'.\n"
                "• Calendario interattivo con caselle colorate.\n\n"
                 "• Questo programma si basa su Python. Puoi scaricare Python dal sito ufficiale: https://www.python.org/downloads/\n"
                 "• I plugin pip python sono autoinstallanti, ma per buona promemoria, allego come installarli manualmente. \n\n"
                 
                 "Su Linux:\n"
                 "  Apri il terminale e digita:\n"
                 "  sudo apt install tkcalendar python3-psutil python3-urllib3\n"
                 "  In alternativa puoi usare i pacchetti python pip 'pip install tkcalendar psutil urllib3'\n"
                 "Su Windows:\n"
                 "  Apri il terminale (Prompt dei comandi) e digita:\n"
                 "  py -m pip install tkcalendar psutil urllib3 win32print win32api win32con\n"
                 "  Assicurati di installare Python, psutil tkcalendar win32print win32api win32con prima di avviare il programma.\n"
            )
            info_win = tk.Toplevel(self)
            info_win.withdraw()
            info_win.title("Informazioni sulla applicazione")
            info_win.resizable(False, False)
            label = tk.Label(info_win, text=info, font=("Arial", 11), justify="left", padx=18, pady=18)
            label.pack()
            btn_aggiorna = ttk.Button(info_win, text="Aggiorna", command=lambda: self.aggiorna(GITHUB_FILE_URL, NOME_FILE))
            btn_aggiorna.pack(side=tk.LEFT, padx=100, pady=10)  
            btn_chiudi = ttk.Button(info_win, text="❌ Chiudi", command=info_win.destroy)
            btn_chiudi.pack(side=tk.RIGHT, padx=100, pady=10)  
            info_win.update_idletasks()
            min_w, min_h = 1160, 620
            win_width = max(info_win.winfo_width(), min_w)
            win_height = max(info_win.winfo_height(), min_h)
            parent_x = self.winfo_rootx()
            parent_y = self.winfo_rooty()
            parent_width = self.winfo_width()
            parent_height = self.winfo_height()
            x = parent_x + (parent_width // 2) - (win_width // 2)
            y = parent_y + (parent_height // 2) - (win_height // 2)
            info_win.geometry(f"{win_width}x{win_height}+{x}+{y}")
            info_win.deiconify()
            info_win.grab_set()
            info_win.transient(self)
            info_win.focus_set()

    def save_db_and_notify(self):
            """Salva il database e mostra una finestra che conferma il salvataggio."""
            self.save_db()
            self.show_custom_warning("Attenzione", "Dati Salvati correttamente !")
          
    def check_UTENZE_DB(self):
         if not os.path.exists(UTENZE_DB):
            with open(UTENZE_DB, "w") as file:
                file.write("")  # Crea un file vuoto
                self.utenze()
         else:
            now = datetime.datetime.now()
            threshold = now - datetime.timedelta(days=DAYS_THRESHOLD)
            file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(UTENZE_DB))
          
         if file_mod_time < threshold:
            self.show_custom_warning("Attenzione", "Ricordati di aggiornare i dati !")
            self.update_file_date()

    def update_file_date(self):
            now_timestamp = datetime.datetime.now().timestamp()
            os.utime(UTENZE_DB, (now_timestamp, now_timestamp))  # Aggiorna la data del file

    def utenze(self):
        self.check_UTENZE_DB()  
        def get_consumi_per_anno(anno):
            return {
                "Acqua": [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
                "Luce":  [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
                "Gas":   [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
            }

        utenze = ["Acqua", "Luce", "Gas"]

        def carica_db():
            if os.path.exists(UTENZE_DB):
                try:
                    with open(UTENZE_DB, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    letture = data.get("letture_salvate", {u: {} for u in utenze})
                    for utenza, per_anno in letture.items():
                        for anno, righe in per_anno.items():
                            letture_norm = []
                            for r in righe:
                                if len(r) == 4:
                                   mese, prec, att, _ = r
                                   try:
                                       consumo = max(0.0, float(att) - float(prec))
                                   except:
                                       prec, att, consumo = 0.0, 0.0, 0.0
                                       letture_norm.append((mese, prec, att, consumo))
                                else:
                                   letture_norm.append(tuple(r))
                                   letture[utenza][anno] = letture_norm

                    anagrafiche = data.get("anagrafiche", {u: {
                        "Ragione sociale": "",
                        "Telefono": "",
                        "Email": "",
                        "Numero contratto": "",
                        "POD": "",
                        "Note": ""
                    } for u in utenze})
                    for utenza in utenze:
                        if utenza not in anagrafiche:
                            anagrafiche[utenza] = {
                                "Ragione sociale": "",
                                "Telefono": "",
                                "Email": "",
                                "Numero contratto": "",
                                "POD": "",
                                "Note": ""
                            }
                        else:
                            for campo in ["Ragione sociale", "Telefono", "Email", "Numero contratto", "POD", "Note"]:
                                if campo not in anagrafiche[utenza]:
                                    anagrafiche[utenza][campo] = ""
                    return letture, anagrafiche
                except Exception as e:
                    #####self.show_custom_warning("Errore", "Errore lettura dati") ###se non vengono inseriti i dati darebbe un errore sempre
                    return {u: {} for u in utenze}, {u: {
                        "Ragione sociale": "",
                        "Telefono": "",
                        "Email": "",
                        "Numero contratto": "",
                        "POD": "",
                        "Note": ""
                    } for u in utenze}
            else:
                return {u: {} for u in utenze}, {u: {
                    "Ragione sociale": "",
                    "Telefono": "",
                    "Email": "",
                    "Numero contratto": "",
                    "POD": "",
                    "Note": ""
                } for u in utenze}


        def scrivi_db():
            try:
                data = {
                    "letture_salvate": {
                        u: {a: [list(r) for r in anni] for a, anni in letture_salvate[u].items()}
                        for u in utenze
                    },
                    "anagrafiche": anagrafiche
                }
                with open(UTENZE_DB, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=1, ensure_ascii=False)
            except Exception as e:
                 self.show_custom_warning("Errore", "Errore scrittura dati")
 
        letture_salvate, anagrafiche = carica_db()
        self.letture_salvate_utenze = letture_salvate
        self.anagrafiche_salvate_utenze = anagrafiche

        anno_corrente = str(datetime.datetime.now().year)
        year_current = int(anno_corrente)
        anni = [str(a) for a in range(year_current-10, year_current+10)]
        consumi = get_consumi_per_anno(anno_corrente)

        win = tk.Toplevel(self)
        win.title("Gestione Consumi Utenze")
        win.geometry("1366x768")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        top_controls = ttk.Frame(win)
        top_controls.pack(pady=(0, 6))
        ttk.Label(top_controls, text="Gestione Consumi Utenze", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=(0, 25))
        ttk.Label(top_controls, text="Anno: ").pack(side=tk.LEFT)
        anno_var = tk.StringVar(value=anno_corrente)

        def salva_letture_preview(txt, preview_win):
            """Salva il contenuto della preview in un file, mantenendo l'allineamento a colonne distanziate."""
            now = datetime.date.today()
            default_dir = EXPORT_FILES
            default_filename = f"Letture_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            preview_win.wm_attributes('-topmost', 1)
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=default_dir,
                initialfile=default_filename,
                title="Salva Preview",
                parent=preview_win)
            preview_win.wm_attributes('-topmost', 0)

            if file:
                with open(file, "w", encoding="utf-8") as f:
                    lines = txt.get("1.0", tk.END)
                    f.write(lines)
                preview_win.destroy()
                self.show_custom_warning("Esportazione completata", f"Statistiche esportate in\n{file}")
        
        def esporta_preview():
            """Mostra anteprima con utenze affiancate in formato tabellare, con spaziatura allineata."""
            preview_win = tk.Toplevel(win)
            preview_win.title("Preview Esportazione")
            preview_win.geometry("1050x600")
            screen_width = preview_win.winfo_screenwidth()
            screen_height = preview_win.winfo_screenheight()
            x = (screen_width - 1050) // 2
            y = (screen_height - 600) // 2
            preview_win.geometry(f"1050x600+{x}+{y}")
            preview_win.after(10, lambda: preview_win.focus_force())

            txt = tk.Text(preview_win, font=("Courier New", 10), wrap="none")
            txt.pack(fill=tk.BOTH, expand=True)

            anno_x = anno_var.get()
            txt.insert(tk.END, f"Consumi utenze per anno {anno_x}\n\n")

            header = f"{'Mese':<10}"
            for utenza in utenze:
                header += f"{utenza:^30}"
            txt.insert(tk.END, header + "\n")

            sub_header = f"{'':<10}"
            for _ in utenze:
                sub_header += f"{'Prec':>8}{'Att':>10}{'Cons':>10}  "
            txt.insert(tk.END, sub_header + "\n")
            txt.insert(tk.END, "-" * len(header) + "\n")

            mesi = [self.trees[utenze[0]].item(iid)['values'][0] for iid in self.trees[utenze[0]].get_children()]
            for i, mese in enumerate(mesi):
                riga = f"{mese:<10}"
                for utenza in utenze:
                    values = self.trees[utenza].item(self.trees[utenza].get_children()[i])['values']
                    prec, att, cons = float(values[1]), float(values[2]), float(values[3])
                    riga += f"{prec:8.2f}{att:10.2f}{cons:10.2f}  "
                txt.insert(tk.END, riga + "\n")

            txt.insert(tk.END, "-" * len(header) + "\n")

            tot_riga = f"{'Totale':<10}"
            for utenza in utenze:
                somma = sum(float(self.trees[utenza].item(iid)['values'][3]) for iid in self.trees[utenza].get_children())
                tot_riga += f"{'':8}{'':10}{somma:10.2f}  "
            txt.insert(tk.END, tot_riga + "\n")

            txt.config(state="disabled")

            btn_frame = ttk.Frame(preview_win)
            btn_frame.pack(fill=tk.X, pady=12)
            ttk.Button(btn_frame, text="💾 Salva", command=lambda: salva_letture_preview(txt, preview_win)).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_frame, text="❌ Chiudi", command=preview_win.destroy).pack(side=tk.RIGHT, padx=10)

            preview_win.lift()
            preview_win.attributes('-topmost', True)
            preview_win.after(200, lambda: preview_win.attributes('-topmost', False))


        def chiudi():
            win.destroy()

        def cambia_anno(*args):
            nonlocal consumi
            for utenza in utenze:
                if self.trees[utenza].get_children():
                    anno_attuale = self.trees[utenza].item(self.trees[utenza].get_children()[0])['values'][0].split("/")[1]
                    letture_salvate[utenza][anno_attuale] = [
                        tuple(self.trees[utenza].item(iid)['values']) for iid in self.trees[utenza].get_children()
                    ]
            scrivi_db()
            for utenza in utenze:
                self.trees[utenza].delete(*self.trees[utenza].get_children())
            anno_sel = anno_var.get()
            consumi = get_consumi_per_anno(anno_sel)
            for utenza in utenze:
                if (anno_sel not in letture_salvate[utenza]) or (not letture_salvate[utenza][anno_sel]):
                    letture_salvate[utenza][anno_sel] = [
                        (f"{m:02d}/{anno_sel}", 0.0, 0.0, 0.0) for m in range(1, 13)
                    ]
                righe = letture_salvate[utenza][anno_sel]
                righe_norm = []
                for r in righe:
                    if len(r) == 4:
                        mese, prec, att, consumo = r
                        consumo = max(0.0, float(att) - float(prec))
                        righe_norm.append((mese, float(prec), float(att), float(consumo)))
                    else:
                        righe_norm.append(tuple(r))
                letture_salvate[utenza][anno_sel] = righe_norm
                for mese, prec, att, consumo in righe_norm:
                    self.trees[utenza].insert("", "end", values=(mese, float(prec), float(att), float(consumo)))

        anno_cb = ttk.Combobox(top_controls, values=anni, textvariable=anno_var, state="readonly", width=8)
        anno_cb.pack(side=tk.LEFT)
        def reset_anno():
            anno_var.set(anno_corrente)
        style = ttk.Style()
        style.configure("Giallo.TButton", background="#ffffcc")
        style.map("Giallo.TButton", background=[("active", "#ffeb99")])

        style.configure("Verde.TButton", background="#ccffcc")
        style.map("Verde.TButton", background=[("active", "#b2fab2")])

        style.configure("Rosso.TButton", background="#ffcccc")
        style.map("Rosso.TButton", background=[("active", "#ff9999")])

        ttk.Button(top_controls, text="🔄 Reset anno", style="Giallo.TButton", command=reset_anno).pack(side=tk.LEFT, padx=7)
        ttk.Button(top_controls, text="📂 Esporta", style="Verde.TButton", command=esporta_preview).pack(side=tk.LEFT, padx=7)
        ttk.Button(top_controls, text="⚙️ Analizza", command=lambda: crea_tabella_consumi(UTENZE_DB)).pack(side=tk.LEFT, padx=7)
        ttk.Button(top_controls, text="❌ Chiudi", style="Giallo.TButton", command=chiudi).pack(side=tk.LEFT, padx=7)
        ttk.Button(top_controls, text="📂 Esporta DB", style="Rosso.TButton", command=lambda: esporta_letture_data(UTENZE_DB)).pack(side=tk.LEFT, padx=7)
        ttk.Button(top_controls, text="📂 Importa DB", style="Rosso.TButton", command=lambda: importa_letture_data(letture_salvate, anagrafiche)).pack(side=tk.LEFT, padx=7)
        anno_var.trace_add("write", cambia_anno)

        main_frame = ttk.Frame(win)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=6)
        for c in range(len(utenze)):
            main_frame.grid_columnconfigure(c, weight=1)

        colori = {"Acqua": "#ccefff", "Luce": "#fff9cc", "Gas": "#ffe0cc"}
        self.trees = {}
        anag_entries = {}


        def importa_letture_data(letture_salvate, anagrafiche):
            now = datetime.date.today()
            default_dir = EXP_DB
            default_filename = f"Letture_import_{now.day:02d}-{now.month:02d}-{now.year}.json"
            file = filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("File JSON", "*.json")],
                initialdir=default_dir,
                initialfile=default_filename,
                title="Importa utenze",
            )
            if file:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    letture = data.get("letture_salvate", {})
                    anagrafiche = data.get("anagrafiche", {})
                    self.letture_salvate_utenze.update(letture)
                    self.anagrafiche_salvate_utenze.update(anagrafiche)
                    self.show_custom_warning("Importazione riuscita", "Utenze importate correttamente!")
                except Exception as e:
                    self.show_custom_warning("Errore", f"Errore durante l'importazione:\n{e}")

        def esporta_letture_data(UTENZE_DB):
            now = datetime.date.today()
            default_dir = EXP_DB
            default_filename = f"Letture_Export_{now.day:02d}-{now.month:02d}-{now.year}.json"
            file = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("File JSON", "*.json")],
                initialdir=default_dir,
                initialfile=default_filename,
                title="Esporta utenze",
            )
            if file:
                try:
                    data = {
                        "letture_salvate": self.letture_salvate_utenze,
                        "anagrafiche": self.anagrafiche_salvate_utenze
                    }
                    with open(file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self.show_custom_warning("Esportazione completata", f"Database utenze salvato in:\n{file}")
                except Exception as e:
                    self.show_custom_warning("Errore", f"Errore durante l'esportazione:\n{e}")



        def crea_tabella_consumi(UTENZE_DB):
            """Mostra i consumi di Luce, Acqua e Gas in una finestra con scrolling verticale."""

            try:
                with open(UTENZE_DB, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    letture_salvate = data.get("letture_salvate", {})
            except Exception as e:
                print(f"❌ Errore lettura file: {e}")
                return
            utenze = ["Acqua", "Luce", "Gas"]
            win = tk.Tk()
            win.title("Consumi Utenze - Anteprima")
            win.geometry("1150x600")
            screen_width = win.winfo_screenwidth()
            screen_height = win.winfo_screenheight()
            x_coordinate = (screen_width - 1150) // 2
            y_coordinate = (screen_height - 600) // 2
            win.geometry(f"1150x600+{x_coordinate}+{y_coordinate}")
            frame_principale = ttk.Frame(win)
            frame_principale.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            canvas = tk.Canvas(frame_principale)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            frame_interno = ttk.Frame(canvas)
            canvas.create_window((0, 0), window=frame_interno, anchor="nw")

            for utenza in utenze:
                frame_tabella = ttk.Frame(frame_interno)
                frame_tabella.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                ttk.Label(frame_tabella, text=f"Consumi {utenza}", font=("Arial", 12, "bold")).pack(pady=5)
                colonne = ["Anno"] + ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic", "Totale"]
                tree = ttk.Treeview(frame_tabella, columns=colonne, show="headings", height=6)
                for col in colonne:
                    tree.heading(col, text=col)
                    tree.column(col, width=80, anchor="center") 
                tree.pack(fill=tk.BOTH, expand=True)
                for anno in sorted(letture_salvate.get(utenza, {}).keys(), reverse=True):
                    row = [anno]
                    tot_consumi = 0.0
                    for mese in range(1, 13):
                        mese_str = f"{mese:02d}/{anno}"
                        consumo = sum(float(r[3]) for r in letture_salvate.get(utenza, {}).get(anno, []) if r[0] == mese_str)
                        row.append(consumo)
                        tot_consumi += consumo
                    row.append(tot_consumi) 
                    tree.insert("", tk.END, values=row)
               
            frame_bottoni = ttk.Frame(win)
            frame_bottoni.pack(fill=tk.X, padx=10, pady=10)
            ttk.Button(frame_bottoni, text="💾 Salva", command=lambda: salva_dati_letture(letture_salvate)).pack(side=tk.LEFT, padx=10)
            ttk.Button(frame_bottoni, text="❌ Chiudi", command=win.destroy).pack(side=tk.RIGHT, padx=10)
            frame_interno.update_idletasks()
            canvas.yview_moveto(0)
            win.mainloop()

        def salva_dati_letture(letture_salvate):
            """Esporta i dati dei consumi in formato testo, simile alla visualizzazione tabellare."""
            win.focus_force()
            now = datetime.date.today()
            default_dir = EXPORT_FILES
            default_filename = f"Letture_anno_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=default_dir,
                initialfile=default_filename,
                title="Salva i dati dei consumi"
               )
               
            if not file_path:
                print("❌ Salvataggio annullato dall'utente.")
                return

            mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
            "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for utenza, anni in letture_salvate.items():
                        f.write(f"Consumi {utenza}:\n")
                        intestazione = f"{'Anno':>6} " + "".join([f"{mese:>8}" for mese in mesi]) + f"{'Totale':>10}\n"
                        f.write(intestazione)
                        f.write("-" * len(intestazione) + "\n")

                        for anno in sorted(anni.keys(), reverse=True):
                            valori_mensili = {r[0]: float(r[3]) for r in anni[anno]}
                            riga = f"{anno:>6} "
                            totale = 0.0
                            for m in range(1, 13):
                                mese_str = f"{m:02d}/{anno}"
                                consumo = valori_mensili.get(mese_str, 0.0)
                                riga += f"{consumo:8.2f}"
                                totale += consumo
                            riga += f"{totale:10.2f}\n"
                            f.write(riga)

                        f.write("\n")

                self.show_custom_warning("Esportazione", f"Statistiche esportate correttamente in:\n{file_path}")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante il salvataggio:\n{e}")

        def centra_su_padre(finestra, padre):
            padre.update_idletasks()
            larghezza = finestra.winfo_reqwidth()
            altezza = finestra.winfo_reqheight()
            px = padre.winfo_rootx() + (padre.winfo_width() // 2) - (larghezza // 2)
            py = padre.winfo_rooty() + (padre.winfo_height() // 2) - (altezza // 2)
            finestra.geometry(f"+{px}+{py}")

        def salva_letture_utenza(utenza):
            anno_sel = anno_var.get()
            letture_salvate[utenza][anno_sel] = [
                tuple(self.trees[utenza].item(iid)['values']) for iid in self.trees[utenza].get_children()
            ]
            scrivi_db()

        def salva_anagrafica_utenza(utenza):
            for field, ent in anag_entries[utenza].items():
                if field == "Note":
                    anagrafiche[utenza][field] = ent.get("1.0", "end-1c")
                else:
                    anagrafiche[utenza][field] = ent.get()
            scrivi_db()

        def apri_modale(utenza):
            selected = self.trees[utenza].focus()
            if not selected:
                  self.show_custom_warning("Errore", "Seleziona un mese dalla tabella")
                  return
            item = self.trees[utenza].item(selected)
            mese, prec, att, _ = item['values']

            items = self.trees[utenza].get_children()
            idx = items.index(selected)

            if idx > 0:
                prev_item = self.trees[utenza].item(items[idx - 1])
                prev_att = float(prev_item['values'][2])
                prec = prev_att

            modal = tk.Toplevel(win)
            modal.title(f"Modifica letture {utenza} - {mese}")
            modal.geometry("520x220")
            modal.resizable(False, False)
            modal.transient(win)
            modal.grab_set()
            centra_su_padre(modal, win)

            tk.Label(modal, text=f"{utenza} - {mese}", font=("Arial", 12, "bold")).pack(pady=10)
            tk.Label(modal, text="Lettura precedente:").pack()
            prec_var = tk.DoubleVar(value=prec)
            e_prec = tk.Entry(modal, textvariable=prec_var, font=("Arial", 10), width=22)
            e_prec.pack()
            tk.Label(modal, text="Lettura attuale:").pack()
            att_var = tk.DoubleVar(value=att)
            tk.Entry(modal, textvariable=att_var, font=("Arial", 10), width=22).pack()
            
            def salva():
                try:
                    p = float(prec_var.get())
                    a = float(att_var.get())
                    if a < p:
                        conferma = tk.Toplevel(modal)
                        conferma.title("Conferma Forzatura")
                        conferma.geometry("350x120")
                        conferma.resizable(False, False)
                        conferma.transient(modal)
                        conferma.grab_set()
                        centra_su_padre(conferma, modal)
                        fnt = ("Arial", 9, "bold")
                        msg = tk.Label(conferma,
                                       text="La lettura attuale è minore della precedente.\nVuoi forzare l'inserimento?",
                                       font=fnt, fg="red")
                        msg.pack(pady=15)
                        btn_frame = ttk.Frame(conferma)
                        btn_frame.pack()
                        def ok():
                            consumo = round(max(0.0, a - p), 2)
                            self.trees[utenza].item(selected, values=(mese, p, a, consumo))
                            if idx + 1 < len(items):
                                next_item = self.trees[utenza].item(items[idx + 1])
                                next_mese, _, next_att, _ = next_item['values']
                                next_att_f = float(next_att)
                                next_cons = round(next_att_f - a, 2)
                                self.trees[utenza].item(items[idx + 1], values=(next_mese, a, next_att_f, next_cons))
                            conferma.destroy()
                            modal.destroy()
                            salva_letture_utenza(utenza)
                        def annulla():
                            conferma.destroy()
                        ttk.Button(btn_frame, text="Forza", command=ok).pack(side=tk.LEFT, padx=12)
                        ttk.Button(btn_frame, text="Annulla", command=annulla).pack(side=tk.LEFT, padx=12)
                        return
                    consumo = round(a - p, 2)
                    self.trees[utenza].item(selected, values=(mese, p, a, consumo))
                    if idx + 1 < len(items):
                        next_item = self.trees[utenza].item(items[idx + 1])
                        next_mese, _, next_att, _ = next_item['values']
                        next_att_f = float(next_att)
                        
                        #next_cons = round(next_att_f - a, 2)
                        next_cons = max(0.0, next_att_f - a)
                        ###########self.show_custom_warning("Attenzione", "Attenzione: il mese successivo è stato aggiornato per evitare un consumo negativo !")
                        
                        
                        self.trees[utenza].item(items[idx + 1], values=(next_mese, a, next_att_f, next_cons))
                    modal.destroy()
                    salva_letture_utenza(utenza)
                except ValueError:
                    self.show_custom_warning("Errore", "Valori non validi")

            ttk.Button(modal, text="💾 Salva", command=salva).pack(pady=10)
            
            
        for idx, utenza in enumerate(utenze):
            frame = tk.Frame(main_frame, bg=colori[utenza], bd=2, relief="groove")
            frame.grid(row=0, column=idx, padx=8, pady=6, sticky="nswe")

            top_btn_fr = tk.Frame(frame, bg=colori[utenza])
            top_btn_fr.pack(fill="x", padx=4, pady=(2,0))
            btn_mod_letture = tk.Button(
                top_btn_fr,
                text="📥 Modifica Letture",
                bg="red",
                fg="white",
                activebackground="#c00",
                font=("Arial", 11, "bold"),
                command=lambda u=utenza: apri_modale(u)
            )
            btn_mod_letture.pack(side=tk.LEFT, anchor="nw", padx=2, pady=2)

            tk.Label(frame, text=utenza, font=("Arial", 12, "bold"), bg=colori[utenza]).pack(pady=(2,2))

            tree = ttk.Treeview(frame, columns=("Mese", "Prec", "Att", "Consumo"), show="headings", height=13)
            tree.heading("Mese", text="Mese")
            tree.heading("Prec", text="Precedente")
            tree.heading("Att", text="Attuale")
            tree.heading("Consumo", text="Consumo")
            tree.column("Mese", width=68, anchor="center")
            tree.column("Prec", width=70, anchor="e")
            tree.column("Att", width=70, anchor="e")
            tree.column("Consumo", width=85, anchor="e")
            tree.pack(padx=8, pady=6, fill="both", expand=True)

            anno_sel = anno_var.get()
            if (anno_sel not in letture_salvate[utenza]) or (not letture_salvate[utenza][anno_sel]):
                letture_salvate[utenza][anno_sel] = [
                    (f"{m:02d}/{anno_sel}", 0.0, 0.0, 0.0) for m in range(1, 13)
                ]
            righe = letture_salvate[utenza][anno_sel]
            righe_norm = []
            for r in righe:
                if len(r) == 4:
                    mese, prec, att, consumo = r
                    consumo = max(0.0, float(att) - float(prec))
                    righe_norm.append((mese, float(prec), float(att), float(consumo)))
                else:
                    righe_norm.append(tuple(r))
            letture_salvate[utenza][anno_sel] = righe_norm
            for mese, prec, att, consumo in righe_norm:
                tree.insert("", "end", values=(mese, float(prec), float(att), float(consumo)))

            self.trees[utenza] = tree

            def salva_letture_local(u=utenza):
                salva_letture_utenza(u)
                self.show_custom_warning("Attenzione", f"Dati {u} Salvati Corretamente !")
                
            ttk.Button(frame, text="💾 Salva Letture", width=16, command=salva_letture_local).pack(pady=(0,6))

            anag_frame = tk.Frame(frame, bg=colori[utenza], bd=1, relief="ridge")
            anag_frame.pack(fill="both", padx=4, pady=(0,8))

            anag_entries[utenza] = {}
            campi = [
                ("Ragione sociale", 32),
                ("Telefono", 32),
                ("Email", 32),
                ("Numero contratto", 32),
                ("POD", 32)
            ]
            
            for row, (label, width) in enumerate(campi):
                tk.Label(anag_frame, text=label+":", font=("Arial", 9, "bold"), bg=colori[utenza]).grid(row=row, column=0, sticky="e", padx=3, pady=1)
                ent = tk.Entry(anag_frame, width=width)
                ent.grid(row=row, column=1, sticky="w", padx=3, pady=1)
                ent.insert(0, anagrafiche[utenza][label])
                ent.config(state="readonly")
                anag_entries[utenza][label] = ent

            tk.Label(anag_frame, text="Note:", font=("Arial", 9, "bold"), bg=colori[utenza]).grid(row=5, column=0, sticky="ne", padx=3, pady=(5,1))
            note_txt = tk.Text(anag_frame, width=30, height=3, wrap="word")
            note_txt.grid(row=5, column=1, sticky="w", padx=3, pady=(5,1))
            note_txt.insert("1.0", anagrafiche[utenza]["Note"])
            note_txt.config(state="disabled")
            anag_entries[utenza]["Note"] = note_txt

            btns = ttk.Frame(anag_frame)
            btns.grid(row=6, column=0, columnspan=2, pady=(5,5))

            def set_editable(editable, u=utenza):
                for k, ent in anag_entries[u].items():
                    if k == "Note":
                        ent.config(state="normal" if editable else "disabled")
                    else:
                        ent.config(state="normal" if editable else "readonly")

            def salva_dati(u=utenza):
                for field, ent in anag_entries[u].items():
                    if field == "Note":
                        anagrafiche[u][field] = ent.get("1.0", "end-1c")
                    else:
                        anagrafiche[u][field] = ent.get()
                set_editable(False, u)
                scrivi_db()
                self.show_custom_warning("Attenzione", f"Dati {u} Salvati correttamente !")

            def modifica_dati(u=utenza):
                set_editable(True, u)

            ttk.Button(btns, text="💾 Salva", width=9, command=salva_dati).pack(side=tk.LEFT, padx=2)
            ttk.Button(btns, text="📄 Modifica", width=11, command=modifica_dati).pack(side=tk.LEFT, padx=2)


    def cerca_operazioni(self):
   
        larghezza, altezza = 900, 600
        x = self.winfo_screenwidth() // 2 - larghezza // 2
        y = self.winfo_screenheight() // 2 - altezza // 2

        finestra = Toplevel()
        finestra.title("Ricerca operazioni")
        finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")
        finestra.transient(self)
        finestra.grab_set()

        # Top: barra ricerca
        frame_superiore = tk.Frame(finestra)
        frame_superiore.pack(fill="x", pady=10, padx=10)

        label_descrizione = tk.Label(frame_superiore, text="🔎 Ricerca su tutti i campi (⏎ per cercare):")
        label_descrizione.pack(side="left")

        campo_input = tk.Entry(frame_superiore, width=30, font=("Arial", 11))
        campo_input.pack(side="left", padx=(10, 0))
        campo_input.focus_set()

        def resetta_campo():
            campo_input.delete(0, tk.END)

        tk.Button(frame_superiore, text="↺", command=resetta_campo, width=2).pack(side="left", padx=(8, 0))

        # Area risultati
        frame_risultati = tk.Frame(finestra)
        frame_risultati.pack(fill="both", expand=True, padx=10)

        scrollbar = tk.Scrollbar(frame_risultati)
        scrollbar.pack(side="right", fill="y")

        area_testo = tk.Text(frame_risultati, wrap="word", yscrollcommand=scrollbar.set)
        area_testo.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=area_testo.yview)

        # Legenda
        tk.Label(
            frame_risultati,
            text="[↑] Entrata\n\n[↓] Uscita",
            font=("Arial", 9, "bold"),
            fg="black"
        ).pack(anchor="w", pady=(5, 0), padx=5)

        # Azioni inferiori
        frame_inferiore = tk.Frame(finestra)
        frame_inferiore.pack(fill="x", padx=10, pady=10)

        def chiudi():
            finestra.destroy()

        tk.Button(frame_inferiore, text="❌ Chiudi", command=chiudi).pack(side="left")

        def esegui_ricerca(event=None):
            parola = campo_input.get().strip().lower()
            area_testo.delete(1.0, tk.END)

            if not parola:
                area_testo.insert(tk.END, "⚠️ Cerca per parola, importo o categoria...")
                return

            risultati = []

            for data_key in sorted(self.spese.keys(), reverse=True):
                try:
                    data = datetime.datetime.strptime(data_key, "%Y-%m-%d").date() if isinstance(data_key, str) else data_key
                except Exception:
                    data = data_key

                for voce in self.spese[data_key]:
                    categoria = str(voce[0]).lower() if len(voce) > 0 else ""
                    descrizione = str(voce[1]).lower() if len(voce) > 1 else ""
                    importo = str(voce[2]) if len(voce) > 2 else ""
                    tipo = str(voce[3]).lower() if len(voce) > 3 else ""

                    if any(parola in campo for campo in [categoria, descrizione, tipo, importo]):
                        emoji = "[↑]" if tipo == "entrata" else "[↓]" if tipo == "uscita" else "[=]"
                        riga = "\n"
                        riga += f"📅 {data.strftime('%d/%m/%Y')}  {emoji} "
                        riga += f"{'':3}Categoria   : {voce[0]}\n"
                        riga += f"{'':3}Descrizione : {voce[1]}\n"
                        riga += f"{'':3}Tipo        : {tipo:<10}    Importo: {float(voce[2]):>10,.2f} €\n"
                        riga += f"{'═'*80}\n"
                        risultati.append(riga)

            area_testo.insert(tk.END, "".join(risultati) if risultati else f"🔍 Nessuna corrispondenza per: '{parola}'")

        campo_input.bind("<Return>", esegui_ricerca)
        tk.Button(frame_inferiore, text="🔍 Cerca", command=esegui_ricerca).pack(side="left", padx=6)

        def esporta_risultato():
            contenuto = area_testo.get(1.0, tk.END).strip()
            if not contenuto:
                messagebox.showinfo("Esporta", "⚠️ Nessun risultato da salvare.")
                return

            now = datetime.date.today()
            default_filename = f"Risultati_Ricerca_{now.year}_{now.month:02d}_{now.day:02d}.txt"

            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                title="Salva risultati ricerca",
                parent=finestra,
            )
            if file:
                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto)
                        self.show_custom_warning("Esportazione completata", f"Risultati salvati in:\n{file}")
                except Exception as e:
                        messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{e}")

        tk.Button(frame_inferiore, text="📄 Esporta", command=esporta_risultato).pack(side="right")

    def rubrica_app(self):
        root = tk.Toplevel()
        root.title("Rubrica Contatti")
        window_width, window_height = 800, 560
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        pos_x = (screen_width - window_width) // 2
        pos_y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        root.resizable(False, False)
        
        contatti = []

        def salva_su_json():
            with open(DATI_FILE, "w", encoding="utf-8") as f:
                json.dump(contatti, f, indent=2, ensure_ascii=False)

        def carica_da_json():
            if os.path.exists(DATI_FILE):
                with open(DATI_FILE, "r", encoding="utf-8") as f:
                    try:
                        dati = json.load(f)
                        contatti.clear()
                        contatti.extend(dati)
                        aggiorna_lista()
                    except:
                        self.show_custom_warning("Attenzione", "File rubrica non valido !")

        def aggiorna_lista():
            lista_contatti.delete(0, tk.END)
            for c in contatti:
                lista_contatti.insert(tk.END, c["nome"])

        def aggiungi_contatto():
            nome = entry_nome.get().strip()
            telefono = entry_telefono.get().strip()
            email = entry_email.get().strip()
            note = entry_note.get("1.0", tk.END).strip()
            
            if len(nome) > 43 or len(telefono) > 43 or len(email) > 43 or len(note) > 100:
               self._show_custom_message("Limite superato", "Hai superato il limite massimo di caratteri:\n\n"
                                "- Nome: 43\n- Telefono: 43\n- Email: 43\n- Note:100",
                                "#fff3cd", "#856404")
               return
               
            if nome:
                contatti.append({"nome": nome, "telefono": telefono, "email": email, "note": note})
                salva_su_json()
                aggiorna_lista()
                pulisci_campi()
                self.show_custom_warning("Attenzione", "Contatto aggiunto correttamente !")
                
        def modifica_contatto():
            idx = lista_contatti.curselection()
            if not idx: return
            i = idx[0]
            contatti[i] = {
                "nome": entry_nome.get(),
                "telefono": entry_telefono.get(),
                "email": entry_email.get(),
                "note": entry_note.get("1.0", tk.END).strip()
            }
            salva_su_json()
            aggiorna_lista()
            self.show_custom_warning("Attenzione", "Contatto modificato correttamente !")
            
        def cancella_contatto():
            idx = lista_contatti.curselection()
            if not idx: return
            contatti.pop(idx[0])
            salva_su_json()
            aggiorna_lista()
            pulisci_campi()
            self.show_custom_warning("Attenzione", "Contatto cancellato con successo !")
            
        def esporta_txt():
            now = datetime.date.today()
            if not contatti:
                self.show_custom_warning("Attenzione", "Nessun Contatto. Rubrica vuota")
                return
            default_dir = EXPORT_FILES
            default_filename = f"Rubrica_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=default_dir,
                initialfile=default_filename,
                title="Salva Rubrica",
                parent=root)
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    for c in contatti:
                        f.write(f"Nome: {c['nome']}   Telefono: {c['telefono']}   Email: {c['email']}\nNote: {c['note']}\n\n")
                    self.show_custom_warning("Attenzione", f"Rubrica esportata con successo in {path}")
                        
        def esporta_rubrica():
            now = datetime.date.today()
            default_dir = EXP_DB
            default_filename = f"Rubrica_Export_{now.day:02d}-{now.month:02d}-{now.year}.json"
            if not contatti:
                self.show_custom_warning("Attenzione", "Nessun contatto, la rubrica e' vuota !")
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("File JSON", "*.json")],
                initialdir=default_dir,
                initialfile=default_filename,
                title="Salva Rubrica .json",
                parent=root
            )
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(contatti, f, indent=2, ensure_ascii=False)
                    self.show_custom_warning("Attenzione", f"Rubrica salvata con successo in {path}")
                except Exception as e:
                    self.show_custom_warning("Attenzione", f"Impossibile salvare la rubrica:\n{e}")
        
        def importa_rubrica():
            default_dir = EXP_DB
            path = filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("File JSON", "*.json")],
                initialdir=EXP_DB,
                parent=root
            )
            if path:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        dati_importati = json.load(f)
                        if isinstance(dati_importati, list):
                            contatti.clear()
                            contatti.extend(dati_importati)
                            aggiorna_lista()
                            self.show_custom_warning("Importazione riuscita", "Rubrica importata correttamente!")
                        else:
                            self.show_custom_warning("Errore", "Il file selezionato non contiene una rubrica valida.")
                except Exception as e:
                            self.show_custom_warning("Errore", f"Impossibile importare la rubrica:\n{e}")
                   

        def seleziona_contatto(event):
            idx = lista_contatti.curselection()
            if not idx: return
            c = contatti[idx[0]]
            entry_nome.delete(0, tk.END)
            entry_nome.insert(0, c["nome"])
            entry_telefono.delete(0, tk.END)
            entry_telefono.insert(0, c["telefono"])
            entry_email.delete(0, tk.END)
            entry_email.insert(0, c["email"])
            entry_note.delete("1.0", tk.END)
            entry_note.insert("1.0", c["note"])

        def cerca_contatto(event=None):
            query = entry_cerca.get().lower()
            lista_contatti.delete(0, tk.END)
            for c in contatti:
                if query in c["nome"].lower():
                    lista_contatti.insert(tk.END, c["nome"])

        def pulisci_campi():
            entry_nome.delete(0, tk.END)
            entry_telefono.delete(0, tk.END)
            entry_email.delete(0, tk.END)
            entry_note.delete("1.0", tk.END)
            lista_contatti.selection_clear(0, tk.END)

        # Layout
        frame_input = ttk.Frame(root)
        frame_input.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(frame_input, text="Nome:").grid(row=0, column=0, sticky="e")
        entry_nome = ttk.Entry(frame_input, width=45)
        entry_nome.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame_input, text="Telefono:").grid(row=1, column=0, sticky="e")
        entry_telefono = ttk.Entry(frame_input, width=45)
        entry_telefono.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame_input, text="Email:").grid(row=2, column=0, sticky="e")
        entry_email = ttk.Entry(frame_input, width=45)
        entry_email.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame_input, text="Note:").grid(row=3, column=0, sticky="ne")
        entry_note = tk.Text(frame_input, width=45, height=5)
        entry_note.grid(row=3, column=1, padx=5, pady=2)

        frame_cerca = ttk.Frame(root)
        frame_cerca.pack(padx=10, pady=(5, 10), fill=tk.X)
        ttk.Label(frame_cerca, text="      Cerca:  ").pack(side=tk.LEFT)
        entry_cerca = ttk.Entry(frame_cerca, width=30)
        entry_cerca.pack(side=tk.LEFT, padx=5)
        entry_cerca.bind("<Return>", cerca_contatto)

        lista_contatti = tk.Listbox(root, width=85, height=10)
        lista_contatti.pack(padx=10, pady=10)
        lista_contatti.bind("<<ListboxSelect>>", seleziona_contatto)
        
        frame_btn = ttk.Frame(root)
        frame_btn.pack(pady=10)

        tk.Button(frame_btn, text="👤 Aggiungi", command=aggiungi_contatto, bg="#32CD32", fg="black").pack(side=tk.LEFT, padx=4)
        tk.Button(frame_btn, text="🔄 Modifica", command=modifica_contatto, bg="#FFA500", fg="black").pack(side=tk.LEFT, padx=4)
        tk.Button(frame_btn, text="❌ Cancella", command=cancella_contatto, bg="red", fg="black").pack(side=tk.LEFT, padx=4)
        tk.Button(frame_btn, text="ℹ️ Esporta stampa", command=esporta_txt, bg="yellow", fg="black").pack(side=tk.LEFT, padx=4)
        tk.Button(frame_btn, text="📂 Esporta Rubrica", command=esporta_rubrica, bg="red", fg="black").pack(side=tk.LEFT, padx=4)
        tk.Button(frame_btn, text="📂 Importa Rubrica", command=importa_rubrica, bg="red", fg="black").pack(side=tk.LEFT, padx=4)

        carica_da_json()
        root.mainloop()

    def mostra_calendario_popup(self, entry_widget, var_data):
 
        # Se già aperto: chiudi
        if hasattr(self, "popup_calendario") and self.popup_calendario and self.popup_calendario.winfo_exists():
            self.popup_calendario.destroy()
            self.popup_calendario = None
            return

        # Calcola posizione popup
        entry_widget.update_idletasks()
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty()
        w = entry_widget.winfo_width()

        self.popup_calendario = tk.Toplevel(self)
        self.popup_calendario.wm_overrideredirect(True)
        self.popup_calendario.geometry(f"{w+210}x310+{x}+{y - 320}")

        # Crea calendario
        cal = Calendar(
            self.popup_calendario,
            date_pattern="dd-mm-yyyy",
            locale="it_IT",
            font=("Arial", 10),
            selectbackground="blue",
            weekendbackground="lightblue",
            weekendforeground="darkblue"
        )
        cal.pack(fill="both", expand=True)

        # Evidenzia giorno corrente in giallo
        oggi = datetime.date.today()
        cal.calevent_create(oggi, "Oggi", "today")
        cal.tag_config("today", background="gold", foreground="black")

        # Ingrandisce intestazione mese/anno
        try:
            cal._header["font"] = ("Arial", 14, "bold")
        except:
            pass  # fallback se non presente

        # Selezione data → aggiorna Entry + chiudi
        def seleziona_data(event=None):
            var_data.set(cal.get_date())
            chiudi_popup_calendario()

        # Chiusura intelligente su FocusOut (solo se fuori dal popup)
        def chiudi_se_fuori(event=None):
            x, y = self.popup_calendario.winfo_pointerxy()
            widget_sotto = self.popup_calendario.winfo_containing(x, y)
            if widget_sotto is None or not str(widget_sotto).startswith(str(self.popup_calendario)):
                chiudi_popup_calendario()

        def chiudi_popup_calendario():
             if self.popup_calendario and self.popup_calendario.winfo_exists():
                 self.popup_calendario.destroy()
                 self.popup_calendario = None

        cal.bind("<<CalendarSelected>>", seleziona_data)
        self.popup_calendario.bind("<FocusOut>", lambda e: self.popup_calendario.after(150, chiudi_se_fuori))
        cal.focus_set()

    def anteprima_e_stampa_txt(self):
        now = datetime.date.today()
        default_dir = EXPORT_FILES
        default_filename = f"Statistiche_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
        path = filedialog.askopenfilename(
               filetypes=[("File txt", "*.txt")],
               initialdir=default_dir,
               initialfile=default_filename,
               title="Stampa Testi"
               )
        if not path:
            return

        with open(path, "r", encoding="utf-8") as f:
            contenuto = f.read()

        anteprima = tk.Toplevel()
        anteprima.withdraw()
        anteprima.title(f"Anteprima stampa: {os.path.basename(path)}")
        anteprima.resizable(False, False)  # Blocca il ridimensionamento
        
        larghezza_finestra = 1300
        altezza_finestra = 600

        # Centra la finestra
        def centra_finestra():
            larghezza_schermo = anteprima.winfo_screenwidth()
            altezza_schermo = anteprima.winfo_screenheight()
            x = (larghezza_schermo // 2) - (larghezza_finestra // 2)
            y = (altezza_schermo // 2) - (altezza_finestra // 2)
            anteprima.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
            anteprima.deiconify()
            anteprima.lift()
            anteprima.focus_force()
        anteprima.after(0, centra_finestra)
            
        txt = tk.Text(anteprima, wrap="word", font=("Courier new", 10))
        txt.insert("1.0", contenuto)
        txt.config(state="disabled")
        txt.pack(padx=10, pady=10, fill="both", expand=True)


        def stampa():
            try:
                sistema = platform.system()

                if not os.path.exists(path):
                    raise FileNotFoundError("File non trovato per la stampa")

                if sistema == "Windows":
                    import win32print
                    import win32ui
                    import win32con

                    printer_name = win32print.GetDefaultPrinter()

                    # Ottieni e modifica il DEVMODE
                    hprinter = win32print.OpenPrinter(printer_name)
                    properties = win32print.GetPrinter(hprinter, 2)
                    devmode = properties["pDevMode"]
                    devmode.Orientation = 2  # 2 = Landscape
                    win32print.ClosePrinter(hprinter)

                    pdc = win32ui.CreateDC()
                    pdc.CreatePrinterDC(printer_name)
                    pdc.SetMapMode(win32con.MM_TEXT)
                    if hasattr(pdc, "ResetDC"):
                          pdc.ResetDC(devmode)
                    else:
                          print("⚠️ Attenzione: ResetDC non disponibile su questo oggetto DC")                                       

                    HORZRES = pdc.GetDeviceCaps(win32con.HORZRES)  # larghezza stampabile
                    VERTRES = pdc.GetDeviceCaps(win32con.VERTRES)  # altezza stampabile

                    font = win32ui.CreateFont({
                         "name": "Courier New",     
                         "height": -int(VERTRES / 60),  # 60 righe circa
                         "width": int(HORZRES / 160),   # 150 caratteri circa
                    })
                    pdc.SelectObject(font)

                    pdc.StartDoc("Stampa compatibile")
                    pdc.StartPage()
                    margin_x = 100  # Margine sinistro
                    margin_y = 100  # Margine superiore
                    line_height = int(VERTRES / 70)     #60 righe circa dal fondo def.
                    with open(path, "r", encoding="utf-8") as file:
                        y = margin_y
                        for line in file:
                            pdc.TextOut(margin_x, y, line.rstrip())
                            y += line_height
                            if y + line_height > VERTRES:
                             # Nuova pagina se si supera il limite
                                   pdc.EndPage()
                                   pdc.StartPage()
                                   y = margin_y

                    
                    pdc.EndPage()
                    pdc.EndDoc()
                    pdc.DeleteDC()

                elif sistema in ["Linux", "Darwin"]:
                    subprocess.run([
                        "lp",
                        "-o", "orientation-requested=4",
                        "-o", "fit-to-page",
                        "-o", "cpi=17",
                        "-o", "lpi=8",
                        path
                    ], check=True)

                else:
                    raise OSError(f"Sistema non supportato: {sistema}")

                self.show_custom_warning("Stampa Avviata", f"Inviato alla stampante predefinita ({sistema})")

            except subprocess.CalledProcessError as e:
                self.show_custom_warning("Stampa Errore", f"Errore di stampa: {e}")
            except Exception as ex:
                self.show_custom_warning("Errore imprevisto", str(ex))
            
        frame_bottoni = tk.Frame(anteprima)
        frame_bottoni.pack(pady=10, fill="x")

        btn_stampa = tk.Button(frame_bottoni, text="🖨️ Stampa ora", command=stampa)
        btn_stampa.pack(side="left", padx=20)

        btn_chiudi = tk.Button(frame_bottoni, text="❌ Chiudi", command=anteprima.destroy)
        btn_chiudi.pack(side="right", padx=20)





    def gruppo_categorie(self):
        popup = tk.Toplevel()
        popup.title("📂 Analisi per categorie selezionate")

        # Dimensioni e centratura
        w, h = 800, 600
        x = (popup.winfo_screenwidth() // 2) - (w // 2)
        y = (popup.winfo_screenheight() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.resizable(False, False)

        # Contenitore principale e barra inferiore
        main_frame = ttk.Frame(popup, padding=10)
        main_frame.pack(fill="both", expand=True)

        bottom_buttons = ttk.Frame(popup)
        bottom_buttons.pack(fill="x", pady=10)

        # Selezione mese e anno
        today = datetime.date.today()
        mesi = ["Tutti"] + ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        mese_var = tk.StringVar(value="Tutti")
        anno_var = tk.StringVar(value=str(today.year))

        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill="x", pady=(0, 10))

        ttk.Label(top_bar, text="Mese:").pack(side="left", padx=(0, 5))
        ttk.Combobox(top_bar, values=mesi, textvariable=mese_var, state="readonly", width=12).pack(side="left")

        anni = sorted({
            d.year if not isinstance(d, str) else datetime.datetime.strptime(d, "%d-%m-%Y").year
            for d in self.spese
        }, reverse=True)

        ttk.Label(top_bar, text="Anno:").pack(side="left", padx=(10, 5))
        ttk.Combobox(top_bar, values=[str(a) for a in anni], textvariable=anno_var, state="readonly", width=8).pack(side="left")

        # Categorie disponibili
        categorie = set()
        for d, sp in self.spese.items():
            if isinstance(d, str):
                d = datetime.datetime.strptime(d, "%d-%m-%Y").date()
            for voce in sp:
                if len(voce) >= 4 and voce[3] == "Uscita":
                    categorie.add(voce[0].strip().title())
        valori_combo = ["— Nessuna —"] + sorted(categorie)

        # Selettori categorie
        selettori_box = ttk.LabelFrame(main_frame, text="🎯 Seleziona fino a 10 categorie da analizzare")
        selettori_box.pack(fill="x", pady=(5, 15))

        sx = ttk.Frame(selettori_box)
        dx = ttk.Frame(selettori_box)
        sx.pack(side="left", fill="both", expand=True, padx=(0, 10))
        dx.pack(side="right", fill="both", expand=True)

        combo_vars = []
        for i in range(10):
            var = tk.StringVar(value="— Nessuna —")
            cb = ttk.Combobox(sx if i < 5 else dx, values=valori_combo, textvariable=var, state="readonly", width=35)
            cb.pack(anchor="w", pady=2)
            combo_vars.append(var)

        # Output risultati
        ttk.Label(main_frame, text="📊 Risultato:", font=("Arial", 10, "bold")).pack(anchor="w")
        text_output = tk.Text(main_frame, height=16, wrap="word", font=("Courier New", 10))
        scroll = ttk.Scrollbar(main_frame, command=text_output.yview)
        text_output.config(yscrollcommand=scroll.set)
        text_output.pack(side="left", fill="both", expand=True, pady=(5, 10))
        scroll.pack(side="right", fill="y")


        def analizza():
            text_output.delete("1.0", "end")
            try:
                anno = int(anno_var.get())
            except:
                self.show_custom_warning("Errore", "Anno non valido.")
                return

            selezionato = mese_var.get()
            if selezionato not in mesi:
                self.show_custom_warning("Errore", "Mese non valido.")
                return

            scelte = {v.get().strip().title() for v in combo_vars if v.get() != "— Nessuna —"}
            risultato = []
            totale = 0.0

            for d, sp in self.spese.items():
                if isinstance(d, str):
                    d = datetime.datetime.strptime(d, "%d-%m-%Y").date()
                if d.year == anno and (selezionato == "Tutti" or d.month == mesi.index(selezionato)):
                    for voce in sp:
                        if len(voce) >= 3:
                            cat = voce[0].strip().title()
                            imp = voce[2]
                            if cat in scelte:
                                entry = next((r for r in risultato if r[0] == cat), None)
                                if entry:
                                    entry[1] += 1
                                    entry[2] += imp
                                else:
                                    risultato.append([cat, 1, imp])
                                totale += imp


            risultato.sort(key=lambda x: -x[2])
            righe = [f"📅 Analisi categorie – {mese_var.get()} {anno}\n"]
            righe.append(f"{'Categoria':<30} {'Num':>4}   {'Totale (€)':>12}")
            righe.append("-" * 52)
            for cat, num, tot in risultato:
                righe.append(f"{cat:<30} {num:>4}   {tot:>12.2f}")
            righe.append("-" * 52)
            righe.append(f"💰 Totale gruppo categorie: {totale:.2f} €")
            text_output.insert("1.0", "\n".join(righe))

        def salva():
            contenuto = text_output.get("1.0", "end").strip()
            if not contenuto:
                self.show_custom_warning("Nessun dato", "Nessun risultato da salvare.")
                return
            now = datetime.date.today()
            default_dir = EXPORT_FILES
            nome_file = f"AnalisiCategorie_{now:%Y_%m_%d}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialfile=nome_file,
                initialdir=default_dir,
                title="Esporta risultati",
                parent=popup
            )
            if file:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(contenuto)
                self.show_custom_warning("Esportazione completata", f"File salvato:\n{file}")

        # 🔘 Pulsanti fissi in fondo
        tk.Button(bottom_buttons, text="📥 Analizza", command=analizza, fg="white", bg="forestgreen").pack(side="left", padx=10)
        tk.Button(bottom_buttons, text="💾 Esporta", command=salva, fg="white", bg="teal").pack(side="left", padx=10)
        tk.Button(bottom_buttons, text="🟨 Chiudi", command=popup.destroy, bg="gold").pack(side="right", padx=10)
















    def time_machine(self):
        popup = tk.Toplevel()
        popup.withdraw()
        popup.title("🕰️ Time Machine – Simulazione per categoria")
        w, h = 780, 670
        x = (popup.winfo_screenwidth() // 2) - (w // 2)
        y = (popup.winfo_screenheight() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.resizable(False, False)
        popup.deiconify()

        main = ttk.Frame(popup, padding=10)
        main.pack(fill="both", expand=True)

        # Selettore Anno
        anni_disponibili = sorted({datetime.datetime.strptime(str(d), "%d-%m-%Y").year
                                   if isinstance(d, str) else d.year for d in self.spese}, reverse=True)
        anno_var = tk.IntVar(value=datetime.date.today().year)

        top_bar = ttk.Frame(main)
        top_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(top_bar, text="Anno:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        anno_combo = ttk.Combobox(top_bar, textvariable=anno_var, values=anni_disponibili, state="readonly", width=8)
        anno_combo.pack(side="left")

        # Colonne categorie
        colonne = ttk.Frame(main)
        colonne.pack(fill="x", padx=5)

        sinistra = ttk.Frame(colonne)
        destra = ttk.Frame(colonne)
        sinistra.pack(side="left", fill="both", expand=True, padx=(0, 40))
        destra.pack(side="right", fill="both", expand=True)

        ttk.Label(sinistra, text="🎯 Selezione manuale", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 6))
        destra_label = ttk.Label(destra, text="📊 Top 10 categorie per spesa", font=("Arial", 10, "bold"))
        destra_label.pack(anchor="w", pady=(0, 6))

        combo_vars = []
        combo_widgets = []
        for _ in range(10):
            var = tk.StringVar()
            cbx = ttk.Combobox(sinistra, textvariable=var, state="readonly", width=30)
            cbx.set("— Nessuna —")
            cbx.pack(pady=2, anchor="w")
            combo_vars.append(var)
            combo_widgets.append(cbx)

        selezioni = {}

        # Area di output
        ttk.Separator(main, orient="horizontal").pack(fill="x", pady=14)
        ttk.Label(main, text="💡 Risultato della simulazione:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
        text_output = tk.Text(main, height=12, wrap="word")
        text_output.pack(fill="both", expand=False, padx=5, pady=(0, 10))
        text_output.configure(font=("Courier New", 10))

        # Funzioni di supporto
        def aggiorna_categorie():
            anno = anno_var.get()
            contatori = {}
            for d, sp in self.spese.items():
                try:
                    if isinstance(d, str):
                        d = datetime.datetime.strptime(d, "%d-%m-%Y").date()
                except:
                    continue
                if d.year != anno:
                    continue
                for voce in sp:
                    if len(voce) < 4:
                        continue
                    cat, _, imp, tipo = voce[:4]
                    if tipo != "Uscita":
                        continue
                    key = cat.strip().title()
                    contatori.setdefault(key, {"count": 0, "totale": 0.0})
                    contatori[key]["count"] += 1
                    contatori[key]["totale"] += imp
            return contatori

        def aggiorna_interfaccia():
            contatori = aggiorna_categorie()
            tutte_categorie = sorted(contatori.keys())
            valori_combo = ["— Nessuna —"] + tutte_categorie

            # aggiorna combo manuali
            for var, cb in zip(combo_vars, combo_widgets):
                cb["values"] = valori_combo
                if var.get().strip().title() not in tutte_categorie:
                    var.set("— Nessuna —")

            # aggiorna checkbox destra
            for w in destra.winfo_children():
                if w != destra_label:
                    w.destroy()

            top_cat = sorted(contatori.items(), key=lambda x: -x[1]["totale"])[:10]
            selezioni.clear()
            for cat, dati in top_cat:
                var = tk.BooleanVar(value=True)
                selezioni[cat] = (var, dati)
                txt = f"{cat} – {dati['count']}×, {dati['totale']:.2f} €"
                chk = ttk.Checkbutton(destra, text=txt, variable=var)
                chk.pack(anchor="w", pady=2)

        def esegui_simulazione():
            contatori = aggiorna_categorie()
            text_output.delete("1.0", tk.END)
            lines = [f"🕰️ Time Machine – Anno {anno_var.get()}\n"]
            totale = 0.0
            scelte = set()

            for cat, (var, _) in selezioni.items():
                if var.get():
                    scelte.add(cat)

            for var in combo_vars:
                val = var.get().strip().title()
                if val and val != "— Nessuna —" and val in contatori:
                    scelte.add(val)

            risultati = []
            for cat in scelte:
                dati = contatori.get(cat)
                if dati:
                    risultati.append((cat, dati["count"], dati["totale"]))

            risultati.sort(key=lambda x: -x[2])
            
            lines.append(f"💭 Proiezione del risparmio ottenibile nel {anno_var.get()}, escludendo le categorie selezionate: ➤\n")
            lines.append(f"{'Categoria':<25} {'Num':>4}   {'Risparmio (€)':>14}")
            lines.append("-" * 50)
            for cat, n, tot in risultati:
                lines.append(f"{cat:<25} {n:>4}   {tot:>14.2f}")
                totale += tot
            lines.append("-" * 50)
            lines.append(f"\n💰 Risparmio totale teorico: {totale:.2f} €")
            text_output.insert("1.0", "\n".join(lines))

        def salva_file():
            content = text_output.get("1.0", "end").strip()
            if not content:
                self.show_custom_warning("Nessun dato", "Non c'è nessuna simulazione da salvare.")
                return
            now = datetime.date.today()
            default_filename = f"TimeMachine_{now.year}_{now.month:02d}_{now.day:02d}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                title="Esporta risultato simulazione",
                parent=popup)
            if file:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.show_custom_warning("Esportazione completata", f"Simulazione salvata in:\n{file}")

        anno_combo.bind("<<ComboboxSelected>>", lambda e: aggiorna_interfaccia())
        aggiorna_interfaccia()

        # Pulsanti finali
        pulsanti = ttk.Frame(main)
        pulsanti.pack(pady=5)

        pulsanti = ttk.Frame(main)
        pulsanti.pack(pady=5)
        tk.Button(pulsanti, text="🟥 Simula Risparmio", command=esegui_simulazione, fg="white", bg="red", activebackground="#aa0000").pack(side="left", padx=10)
        tk.Button(pulsanti, text="💾 Esporta", command=salva_file, fg="white", bg="cadetblue", activebackground="steelblue").pack(side="left", padx=10)
        tk.Button(pulsanti, text="🟨 Chiudi", command=popup.destroy, fg="black", bg="gold", activebackground="orange").pack(side="right", padx=10)


    def gestione_login(self):
   
        def hash_pw(pw):
            return hashlib.sha256(pw.encode()).hexdigest()

        def salva_hash(pw):
            with open(PW_FILE, "w") as f:
                json.dump({"hash": hash_pw(pw)}, f)

        def leggi_hash():
            if not os.path.exists(PW_FILE):
                return None
            with open(PW_FILE) as f:
                return json.load(f).get("hash")

        login_riuscito = [False]

        def mostra_finestra_login():
            login = tk.Toplevel(self)
            login.withdraw()
            login.title("🔐 Accesso Casa Facile")
            login.resizable(False, False)

            def chiusura():
                self.quit()
                self.destroy()

            login.protocol("WM_DELETE_WINDOW", chiusura)

            w, h = 320, 200
            x = self.winfo_screenwidth() // 2 - w // 2
            y = self.winfo_screenheight() // 2 - h // 2
            login.geometry(f"{w}x{h}+{x}+{y}")

            login.deiconify()
            login.lift()
            login.focus_force()
            login.grab_set()

            if os.path.exists(PW_FILE):
                  # Password già impostata → richiesta login
                  tk.Label(login, text="🔑 Inserisci la password:", font=("Arial", 10)).pack(pady=(15, 5))
            else:
                  # Prima volta → benvenuto
                  tk.Label(login, text="🔐 Benvenuto! Inserisci una nuova password:", font=("Arial", 10)).pack(pady=(15, 5))
       
            entry_pw = tk.Entry(login, show="*", width=26)
            
            entry_pw.pack()
            entry_pw.focus()

            messaggio_errore = tk.Label(login, text="", fg="red", font=("Arial", 9))
            messaggio_errore.pack()

            visibile = tk.BooleanVar(value=False)
            tk.Checkbutton(
                login, text="👁 Mostra password", variable=visibile,
                command=lambda: entry_pw.config(show="" if visibile.get() else "*")
            ).pack(pady=4)

            def conferma_login():
                inserita = entry_pw.get()
                salvata = leggi_hash()
                if not salvata:
                    salva_hash(inserita)
                    messaggio_errore.config(
                        text="✅ Password creata con successo.",
                        fg="green"
                   )
                    login_riuscito[0] = True
                    login.after(1500, login.destroy)
                elif hash_pw(inserita) == salvata:
                    login_riuscito[0] = True
                    login.destroy()
                else:
                    entry_pw.delete(0, tk.END)  # cancella tutto
                    messaggio_errore.config(text="❌ Password errata.")

            entry_pw.bind("<Return>", lambda e: conferma_login())

            def cambia_password():
                win = tk.Toplevel(login)
                win.title("🔁 Cambia password")
                win.resizable(False, False)
                win.geometry(f"320x250+{x}+{y}")
                win.grab_set()

                tk.Label(win, text="Vecchia password:").pack()
                entry_attuale = tk.Entry(win, show="*")
                entry_attuale.pack()

                tk.Label(win, text="Nuova password:").pack()
                entry_nuova = tk.Entry(win, show="*")
                entry_nuova.pack()

                tk.Label(win, text="Conferma nuova password:").pack()
                entry_conferma = tk.Entry(win, show="*")
                entry_conferma.pack()

                mess = tk.Label(win, text="", fg="red")
                mess.pack()

                def conferma_cambio():
                    attuale = entry_attuale.get()
                    nuova = entry_nuova.get()
                    conferma = entry_conferma.get()
                    if hash_pw(attuale) != leggi_hash():
                        mess.config(text="❌ Password attuale errata.")
                    elif nuova != conferma:
                        mess.config(text="❌ Le nuove non corrispondono.")
                    else:
                        salva_hash(nuova)
                        mess.config(text="✅ Password aggiornata.", fg="green")
                        win.after(1000, win.destroy)

                tk.Button(win, text="💾 Salva", command=conferma_cambio).pack(pady=8)

            #tk.Button(login, text="➡️ Accedi", command=conferma_login).pack(pady=(8, 2))
            tk.Button(login, text="🔁 Cambia password", command=cambia_password).pack(pady=(2, 8))

            login.wait_window()

        mostra_finestra_login()
        return login_riuscito[0]

def backup_incrementale(file_path, cartella_backup="backup", max_backup=10):
    if not os.path.exists(file_path):
        return
    os.makedirs(cartella_backup, exist_ok=True)
    nome = os.path.basename(file_path)
    data = datetime.datetime.today().strftime("%Y-%m-%d")
    backup_file = os.path.join(cartella_backup, f"{nome}.{data}.bak.json")
    shutil.copy2(file_path, backup_file)

    # Mantieni solo i più recenti
    files = sorted(
        [f for f in os.listdir(cartella_backup) if f.startswith(nome)],
        key=lambda x: os.path.getmtime(os.path.join(cartella_backup, x)),
        reverse=True
    )
    for f in files[max_backup:]:
        os.remove(os.path.join(cartella_backup, f))

 
def check_and_install_python():
    """ Verifica se Python è installato e lo installa se mancante """
    # Controlla se l'eseguibile Python è disponibile
    python_path = shutil.which("python") or shutil.which("python3")
    
    if python_path:
        print(f"Python è già installato: {python_path}")
    else:
        print("Python non è installato. Tentativo di installazione...")

        if sys.platform.startswith("win"):
            subprocess.run(["winget", "install", "Python.Python"], check=True)  # Installa Python su Windows
        elif sys.platform.startswith("linux"):
            subprocess.run(["sudo", "apt", "install", "-y", "python3"], check=True)  # Installa Python su Linux (Debian-based)
        elif sys.platform.startswith("darwin"):
            subprocess.run(["brew", "install", "python"], check=True)  # Installa Python su macOS
        else:
            print("Sistema operativo non supportato per l'installazione automatica.")
        
        print("Installazione completata. Riavvia il terminale per aggiornare i percorsi.")

def install_tkcalendar():
    """ Controlla se tkcalendar è installato e, se mancante, lo installa automaticamente """
    package_name = "tkcalendar"
    # Verifica se il pacchetto è installato
    if importlib.util.find_spec(package_name) is None:
        print(f"{package_name} non è installato. Installazione in corso...")
        # Esegue il comando di installazione
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        print(f"{package_name} installato con successo!")
    else:
        print(f"{package_name} è già installato.")

def install_psutil():
    """ Controlla se psutil è installato e, se mancante, lo installa automaticamente """
    package_name = "psutil"
    # Verifica se il pacchetto è installato
    if importlib.util.find_spec(package_name) is None:
        print(f"{package_name} non è installato. Installazione in corso...")
        # Esegue il comando di installazione
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        print(f"{package_name} installato con successo!")
    else:
        print(f"{package_name} è già installato.")

def install_urllib3():
    """ Controlla se urllib3 è installato e, se mancante, lo installa automaticamente """
    package_name = "urllib3"
    # Verifica se il pacchetto è installato
    if importlib.util.find_spec(package_name) is None:
        print(f"{package_name} non è installato. Installazione in corso...")
        # Esegue il comando di installazione
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        print(f"{package_name} installato con successo!")
    else:
        print(f"{package_name} è già installato.")


def install_win32_libraries():
    """Installa pywin32 su Windows se necessario (include win32print, win32api, win32con)."""
    if platform.system() != "Windows":
        print("Sistema operativo non Windows: installazione non necessaria.")
        return

    modules = ["win32print", "win32api", "win32con"]
    missing = [mod for mod in modules if importlib.util.find_spec(mod) is None]

    if missing:
        print(f"Moduli mancanti: {', '.join(missing)}. Installazione di pywin32 in corso...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pywin32"], check=True)
            print("pywin32 installato con successo.")
        except subprocess.CalledProcessError as e:
            print(f"Errore durante l'installazione: {e}")
    else:
        print("I moduli win32print, win32api e win32con sono già installati.")


def check_single_instance():
    """ Impedisce avvio multiplo su Windows Linux Osx"""
    if sys.platform.startswith("win"):
        # 🔒 Controllo su Windows con Mutex
        mutex_name = "Global\\AppMutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # Il mutex esiste già
            print("Un'altra istanza è già in esecuzione!")
            show_warning_popup()
            sys.exit(1)
        return  # Evita il controllo successivo
    else:
         current_pid = os.getpid()
         current_script = os.path.abspath(sys.argv[0])
         for proc in psutil.process_iter(attrs=["pid", "cmdline"]):  # Usa 'cmdline' su Linux/macOS
          try:
            cmd = proc.info["cmdline"]
            if cmd and current_script in cmd and proc.info["pid"] != current_pid:
                print("Un'altra istanza è già in esecuzione!")
                show_warning_popup()
                sys.exit(1)
          except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
         return  # Evita il controllo successivo

def show_warning_popup():
    """ Mostra un messaggio di avviso con tkinter """
    root = tk.Tk()
    root.withdraw()  
    messagebox.showwarning("Attenzione", "Oops! \n\nSembra che il programma sia già aperto. \n\nChiudilo e riprova! \n\n Gestione Spese Pro \n© 2025 Tutti i diritti riservati \n")
    sys.exit(1)


if __name__ == "__main__":
    # 🔧 Prepara tutto PRIMA dello splash
    check_and_install_python()
    install_tkcalendar()
    install_psutil()
    install_urllib3()
    install_win32_libraries()
    #check_single_instance()
    print("Programma avviato.")

    # 📁 Crea le cartelle se non esistono
    if not os.path.exists(EXPORT_FILES):
        os.makedirs(EXPORT_FILES)
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    if not os.path.exists(EXP_DB):
        os.makedirs(EXP_DB)
    if not os.path.exists(UTENZE_DB):
        with open(UTENZE_DB, "w") as file:
            file.write("")  # Crea un file vuoto

    def avvia_app(splash):
        splash.destroy()
        app = GestioneSpese()
        app.mainloop()

    splash = tk.Tk()
    splash.overrideredirect(True)
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    width = 300
    height = 100
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    label = tk.Label(splash, text="Caricamento Casa Facile...", font=("Arial", 12))
    label.pack(expand=True)
    splash.after(800, lambda: avvia_app(splash))
    splash.mainloop()

    
    
