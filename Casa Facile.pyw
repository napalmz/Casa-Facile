#!/usr/bin/env python3
# 🔧 Moduli standard Python
import os
import sys
import csv
import json
import html
import uuid
import socket
import ctypes
import shutil
import hashlib
import calendar
import platform
import datetime
import tempfile
import threading
import subprocess
import webbrowser
import importlib.util

# 🌐 Network e URL
import urllib.parse
import urllib.request
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict

# 🎨 Interfaccia grafica Tkinter
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel, Label, Button

# 🔒 Alias personalizzato (se serve per escaping HTML)
import html as html_escape  # facoltativo se serve solo una volta


# URL del file su GitHub (sostituiscilo con il tuo link reale)
URL_PDF = "https://raw.githubusercontent.com/Renato-4132/Casa-Facile/refs/heads/main/Casa%20Facile.pdf"
GITHUB_FILE_URL = "https://raw.githubusercontent.com/Renato-4132/Casa-Facile/refs/heads/main/Casa%20Facile.pyw"
NOME_FILE = "Casa Facile.pyw"  # Nome del file da salvare
REPO_OWNER = "Renato-4132"
REPO_NAME = "Casa-Facile"
NAME = "Casa-Facile"
EXPORTDB_DIR = "export"
DB_DIR = "db"
DB_FILE = os.path.join(DB_DIR, "spese_db.json")
DATI_FILE = os.path.join(DB_DIR,"rubrica.json")
UTENZE_DB = os.path.join(DB_DIR, "utenze_db.json")
SALDO_FILE = os.path.join(DB_DIR, "saldo_db.json")
EXPORT_FILES = "export"
EXP_DB = os.path.join(DB_DIR, EXPORTDB_DIR)
PW_FILE = os.path.join(DB_DIR, "password.json")
MEM_CAT = os.path.join(DB_DIR, "memoria_categorie.json")
PORTA_DB = os.path.join(DB_DIR, "webserver_port.json")
CONFIG = os.path.join(DB_DIR, "config.json")
RIMANDA_FILE = os.path.join(DB_DIR, "update.json")


# Imposta timeout self.show_custom_warning
# millisecondi
WARN_TIMEOUT = 20000  # millisecondi

# Imposta a True se vuoi chiusura con conferma self.show_custom_warning
# Imposta a False per forzare timeout chiusura  self.show_custom_warning
USE_WAIT_WINDOW = False

# 🔁 Nome directory
current_folder = os.path.basename(os.getcwd())
# 🔁 Imposta working directory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

#Tolleranza SmartCat
toll = 30 #Euro

#Avviso mancata lettura entro gg
DAYS_THRESHOLD = 25

#Versione
VERSION = "6.8"

# ⏱️ 5 minuti in millisecondi Timer Iconizza
TIMEOUT_INATTIVITA_MS = 300000


class CasaFacileWebHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path
        cookie = self.headers.get("Cookie", "")
        is_logged_in = "logged_in=true" in cookie
        if path == "/login":
            html = self.server.app.html_login(self.path)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        elif path == "/logoff":
            self.send_response(303)
            self.send_header("Set-Cookie", "logged_in=false; Path=/")
            self.send_header("Location", "/login")
            self.end_headers()
            return
        if not is_logged_in:
            self.send_response(303)
            self.send_header("Location", "/login")
            self.end_headers()
            return
        if path == "/":
            html = self.server.app.html_form()
        elif path.startswith("/stats"):
            html = self.server.app.stats_mensili_html()
        elif path.startswith("/lista"):
            html = self.server.app.html_lista_spese_mensili()
        elif path.startswith("/menu_esplora"):
            html = self.server.app.pagina_menu_esplora()
        elif path.startswith("/cerca_avanzata"):
            params = parse_qs(urlparse(self.path).query)
            html = self.server.app.pagina_risultati_avanzati(params)
        elif path.startswith("/modifica"):
            params = parse_qs(urlparse(self.path).query)
            html = self.server.app.modifica_voce_form(params)
        elif path.startswith("/report_annuo"):
            params = parse_qs(urlparse(self.path).query)
            html = self.server.app.pagina_statistiche_annuali_web()
        elif path.startswith("/utenze"):
            params = parse_qs(urlparse(self.path).query)
            anno = params.get("anno", [str(datetime.datetime.now().year)])[0]
            html = self.server.app.genera_html_utenze(UTENZE_DB, anno)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        else:
            self.send_error(404, "Pagina non trovata")
            return
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


    def do_POST(self):
        path = self.path
        cookie = self.headers.get("Cookie", "")
        is_logged_in = "logged_in=true" in cookie

        # 🔐 Login
        if path.startswith("/check_login"):
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            params = parse_qs(body)
            password = params.get("password", [""])[0].strip()

            if not self.server.app.leggi_hash():
                self.server.app.salva_hash(password)
                success = True
            else:
                success = self.server.app.verifica_password(password)

            if success:
                self.send_response(303)
                self.send_header("Set-Cookie", "logged_in=true; Path=/")
                self.send_header("Location", "/")
            else:
                self.send_response(303)
                self.send_header("Location", "/login?error=1")
            self.end_headers()
            return

        # 🔒 Blocco accesso se non autenticato
        if not is_logged_in:
            self.send_response(303)
            self.send_header("Location", "/login")
            self.end_headers()
            return

        # ➕ Aggiunta voce
        if path == "/":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            params = parse_qs(body)

            voce = {
                "date": params.get("data", ["01-01-2024"])[0],
                "categoria": params.get("categoria", ["Generica"])[0],
                "descrizione": params.get("descrizione", [""])[0],
                "importo": float(params.get("importo", ["0"])[0]),
                "tipo": params.get("tipo", ["Uscita"])[0]
            }

            self.server.app.aggiungi_voce_web(voce)
            self.server.app.carica_db_web()
            self.server.app.refresh_gui()
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        # ✏️ Salvataggio modifica
        if path == "/salva_modifica":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            params = parse_qs(body)

            self.server.app.salva_modifica_voce(params)
            self.server.app.refresh_gui()
            self.send_response(303)
            self.send_header("Location", "/lista")
            self.end_headers()
            return

        # 🗑️ Cancellazione voce
        if path == "/cancella":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            params = parse_qs(body)

            giorno = params.get("data", [""])[0]
            idx = int(params.get("idx", ["-1"])[0])
            print(f"🧹 Cancello voce {idx} del giorno {giorno}")

            self.server.app.cancella_voce_web(giorno, idx)
            self.server.app.refresh_gui()
            self.send_response(303)
            self.send_header("Location", "/lista")
            self.end_headers()
            return

        # 🚫 Path non gestito
        self.send_error(404, "Pagina POST non gestita")



class GestioneSpese(tk.Tk):

    CATEGORIA_RIMOSSA = "Categoria Rimossa"
    
    def __init__(self):
        super().__init__()

        self.withdraw()
        self.update_idletasks()
        
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

        self.modalita = leggi_modalita()
        
        if not self.gestione_login():
            self.destroy()
            return  # oppure self.destroy(); exit()

        self.resizable(True, True)
        self.lift()
        self.focus_force()
        self.after(250, self.deiconify)

        # 🧭 Barra dei menu in alto
        barra_menu = tk.Menu(self, background="lightblue", foreground="black")
        self.config(menu=barra_menu)

        # 🧭 Menu Funzioni
        menu_funzioni = tk.Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="⚙️ Funzioni", menu=menu_funzioni)
        menu_funzioni.add_command(label="👥 Utenze", accelerator="Ctrl+U", command=self.utenze)
        self.bind_all("<Control-u>", lambda e: self.utenze())
        menu_funzioni.add_command(label="📅 Rubrica", accelerator="Ctrl+R", command=self.rubrica_app)
        self.bind_all("<Control-r>", lambda e: self.rubrica_app())
        menu_funzioni.add_separator()
        menu_funzioni.add_command(label="🔍 Cerca", accelerator="Ctrl+F", command=self.cerca_operazioni)
        self.bind_all("<Control-f>", lambda e: self.cerca_operazioni())
        menu_funzioni.add_command(label="📅 Stampa", accelerator="Ctrl+P", command=self.anteprima_e_stampa_txt)
        self.bind_all("<Control-p>", lambda e: self.anteprima_e_stampa_txt())
        menu_funzioni.add_separator()
        menu_funzioni.add_command(label="📊 Confronta", accelerator="Ctrl+C", command=self.open_compare_window)
        self.bind_all("<Control-c>", lambda e: self.open_compare_window())
        menu_funzioni.add_command(label="📊 Time Machine", accelerator="Ctrl+T", command=self.time_machine)
        self.bind_all("<Control-t>", lambda e: self.time_machine())
        menu_funzioni.add_command(label="📂 Aggrega", accelerator="Ctrl+G", command=self.gruppo_categorie)
        self.bind_all("<Control-g>", lambda e: self.gruppo_categorie())
        menu_funzioni.add_separator()
        menu_funzioni.add_command(label="💰 Saldo", accelerator="Ctrl+S", command=self.open_saldo_conto)
        self.bind_all("<Control-s>", lambda e: self.open_saldo_conto())
        menu_funzioni.add_command(label="📋 Report", accelerator="Ctrl+L", command=self.calcola_statistiche_annuali)
        self.bind_all("<Control-l>", lambda e: self.calcola_statistiche_annuali())
        menu_funzioni.add_separator()
        menu_funzioni.add_command(label="📋 Controllo", accelerator="Ctrl+Z", command=self.calcola_mancanti)
        self.bind_all("<Control-z>", lambda e: self.calcola_mancanti())
        menu_funzioni.add_separator()
        menu_funzioni.add_command(label="✖️ Salva e chiudi", accelerator="Ctrl+Q", command=self._on_close)
        self.bind_all("<Control-q>", lambda e: 
        self._on_close())
        #menu_funzioni.add_separator()
        #menu_funzioni.add_command(label="🧳 Riduci a icona",accelerator="Escape",command=self.iconify)
        #self.bind_all("<Escape>", lambda e: self.iconify())
        
        # 📆 Menu Estrazioni
        menu_estrazioni = tk.Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="🗃️ Estrazioni", menu=menu_estrazioni)
        menu_estrazioni.add_command(label="📅 Estrai Giorno", accelerator="Alt+J", command=self.export_giorno_forzato)
        self.bind_all("<Alt-j>", lambda e: self.export_giorno_forzato())
        menu_estrazioni.add_command(label="📅 Estrai Mese", accelerator="Alt+K", command=self.export_month_detail)
        self.bind_all("<Alt-k>", lambda e: self.export_month_detail())
        menu_estrazioni.add_command(label="📊 Estrai Anno", accelerator="Alt+L", command=self.export_anno_dettagliato)
        self.bind_all("<Alt-l>", lambda e: self.export_anno_dettagliato())

        # 📆 Menu Categorie
        menu_categorie = tk.Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="📆 Categorie", menu=menu_categorie)
        menu_categorie.add_command(label="⏰ Analisi Categorie", accelerator="Ctrl+K", command=self.open_analisi_categoria)
        self.bind_all("<Control-k>", lambda e: self.open_analisi_categoria())
        menu_categorie.add_command(label="⏰ Suggerisci Categorie", accelerator="Ctrl+Shift+K", command=self.apri_categorie_suggerite)
        self.bind_all("<Control-Shift-K>", lambda e: self.apri_categorie_suggerite())

        # 📆 Menu Webserver
        menu_webserver = tk.Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="🌐 Webserver", menu=menu_webserver)
        menu_webserver.add_command(label="🌐 Apri WebServer",command=self.apri_webserver)
        menu_webserver.add_command(label="🌐 Apri Web Port",command=self.apri_webserver_port)
        
        # 🛠️ Menu Setup
        menu_setup = tk.Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="🛠️ Setup", menu=menu_setup)
        menu_setup.add_command(
            label="🔰 Modalità Semplice", 
            command=lambda: (
                salva_modalita("semplice"),
                self.save_db(),
                self.cambio_modalita("Modalità Semplice attivata.\nRiavvio l’interfaccia."),
                self.destroy(),
                self.__class__().mainloop()
            )
        )
        menu_setup.add_command(
            label="🚀 Modalità Avanzata",
            command=lambda: (
                salva_modalita("avanzata"),
                 self.save_db(),
                 self.cambio_modalita("Modalità Avanzata attivata.\nRiavvio l’interfaccia."),
                 self.destroy(),
                 self.__class__().mainloop()
            )
        )
        
        # 💾 Menu Database
        menu_db = tk.Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="💾 Database", menu=menu_db)
        menu_db.add_command(label="📥 Importa DB", command=self.import_db)
        menu_db.add_command(label="📤 Esporta DB", command=self.export_db)
        menu_db.add_command(label="📤 Reset DB", command=self.show_reset_dialog)
        # ⚙️ Menu Info
        menu_info = tk.Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="🛈 Info", menu=menu_info)
        menu_info.add_command(label="🛈 Info", command=self.show_info_app, accelerator="Ctrl+I")
        self.bind_all("<Control-i>", lambda e: self.show_info_app())
        menu_info.add_command(label="📘 Apri Manuale",command=self.scarica_manuale, accelerator="Ctrl+M")
        self.bind_all("<Control-m>", lambda e: self.scarica_manuale())
        
        # Carica Server
        #threading.Thread(target=self.start_web_server, daemon=True).start()

        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        if not os.path.exists(EXP_DB):
            os.makedirs(EXP_DB)
            
        backup_incrementale(DB_FILE)
        backup_incrementale(SALDO_FILE)
        backup_incrementale(DATI_FILE)
        backup_incrementale(UTENZE_DB)

        self.aggiorna_titolo_finestra()
        
        self.categoria_bloccata = False
        self.suggerimenti_attivi = True # ⛔ Disattiva suggerimento categoria=spesa

        #Timeout Iconizza
        self._timeout_inattivita = TIMEOUT_INATTIVITA_MS
        self._timer_inattivita = None
        self._attiva_timer_inattivita()
        
        self.categorie = ["Generica", self.CATEGORIA_RIMOSSA]
        self.categorie_tipi = {"Generica": "Uscita", self.CATEGORIA_RIMOSSA: "Uscita"}
        self.spese = {}
        self.ricorrenze = {}  
        self.modifica_idx = None
        self.stats_refdate = datetime.date.today()
        self.load_db()
        self.carica_memoria_descrizioni()
        topbar = ttk.Frame(self)
        topbar.pack(fill=tk.X, pady=4)
        
        style = ttk.Style()

        # Definizione dei colori dei pulsanti aggiornati
        style.configure("Salva.TButton", background="#FF6666", foreground="black", font=("Arial", 8))  # Salva - rosso chiaro
        style.configure("Importa.TButton", background="#90EE90", foreground="black", font=("Arial", 8))  # Importa - verde chiaro
        style.configure("Esporta.TButton", background="#FFA500", foreground="black", font=("Arial", 8))  # Esporta - arancione chiaro
        style.configure("Reset.TButton", background="red", foreground="black", font=("Arial", 8))  # Reset Database - rosso
        style.configure("Info.TButton", background="green", foreground="black", font=("Arial", 8))  # Info - verde
        style.configure("Saldo.TButton", background="#FFA500", foreground="black", font=("Arial", 8))  # Saldo Conto - arancione chiaro
        style.configure("Confronta.TButton", background="yellow", foreground="black", font=("Arial", 8))  # Confronta - giallo
        style.configure("Utenze.TButton", background="#90EE90", foreground="black", font=("Arial", 8))  # Utenze - verde chiaro
        style.configure("Rubrica.TButton", background="#90EE90", foreground="black", font=("Arial", 8))  # Rubrica - verde chiaro
        style.configure("Stampa.TButton", background="#90EE90", foreground="black", font=("Arial", 8))  # Stampa - verde chiaro
        style.configure("Cerca.TButton", background="yellow", foreground="black", font=("Arial", 8))  # Stampa - verde chiaro
        style.configure("TM.TButton", background="yellow", foreground="black", font=("Arial", 8))  # Stampa - verde chiaro
        style.configure("Gruppi.TButton", background="yellow", foreground="black", font=("Arial", 8))  # Stampa - verde chiaro
        style.configure("Report.TButton", background="yellow", foreground="black", font=("Arial", 8))  # Report - verde chiaro
        style.configure("Webserver.TButton", background="#90EE90", foreground="black", font=("Arial", 8))  # Webserver - verde chiaro
        style.configure("Webserver_port.TButton", background="#90EE90", foreground="black", font=("Arial", 8))  # Webserver - verde chiaro
        style.configure("Manuale.TButton", background="#FFA500", foreground="black", font=("Arial", 8))  # Manuale - verde chiaro
 
        if self.modalita == "avanzata":
         ttk.Button(topbar, text="💾 Salva", command=self.save_db_and_notify, style="Salva.TButton").pack(side=tk.RIGHT, padx=1)
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
         ttk.Button(topbar, text="🔍 Report", command=self.calcola_statistiche_annuali, style="Report.TButton").pack(side=tk.LEFT, padx=1)
        
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

        self.cal.bind("<<CalendarSelected>>", self.on_calendar_change)
        self.cal.bind("<<CalendarMonthChanged>>", self.on_month_changed)
        self.colora_giorni_spese()

        # Stile unico giallo (lo definisci una volta sola)      
        style.configure("Yellow.TButton", background="yellow", foreground="black", font=("Arial", 8))

        # Frame orizzontale per contenere entrambi i bottoni
        barra_azione = ttk.Frame(cal_frame)
        barra_azione.pack(fill="x", pady=(6, 0))

        # Pulsante “Oggi”
        btn_today = ttk.Button(barra_azione, text="↺ Torna alla data odierna", width=25, command=self.goto_today, style="Yellow.TButton")
        btn_today.pack(side="left", padx=(0, 5))
        
        if self.modalita == "avanzata":
         btn_webserver = ttk.Button(barra_azione, text="🌐 Apri WebServer", width=20, command=self.apri_webserver, style="Webserver.TButton")
         btn_webserver.pack(side="left", padx=(0, 5))

         btn_webserver_port = ttk.Button(barra_azione, text="🌐 Web port", width=10, command=self.apri_webserver_port, style="Webserver_port.TButton")
         btn_webserver_port.pack(side="left", padx=(0, 5))
        
         btn_manuale = ttk.Button(barra_azione, text="🌐 Apri Manuale", width=20, command=self.scarica_manuale, style="Manuale.TButton")
         btn_manuale.pack(side="left", padx=(0, 5))
        
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
        self.cb_estratto_month = ttk.Combobox(select_frame, values=months, width=13, foreground="green", font=("Arial", 10, "bold"),
                                      textvariable=self.estratto_month_var, state="disabled", style="Custom.TCombobox")
        self.cb_estratto_month.grid(row=0, column=1, sticky="w", padx=(0, 4))
        self.cb_estratto_month.current(today.month - 1)
        ttk.Label(select_frame, text="← Mese visualizzato (seleziona dal calendario)", font=("Arial", 10, "bold")).grid(
            row=0, column=2, sticky="w", padx=2)

        ttk.Label(select_frame, text="📆 Anno:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="e", padx=2, pady=2)
        self.estratto_year_var = tk.StringVar(value=str(today.year))
        self.cb_estratto_year = ttk.Combobox(select_frame, values=years, width=13, foreground="green", font=("Arial", 10, "bold"),
                                     textvariable=self.estratto_year_var, state="disabled", style="Custom.TCombobox")
        self.cb_estratto_year.grid(row=1, column=1, sticky="w", padx=(0, 4))
        ttk.Label(select_frame, text="← Anno visualizzato (seleziona dal calendario)", font=("Arial", 10, "bold")).grid(
            row=1, column=2, sticky="w", padx=2)
            
        # Nascondi in modalita semplice    
        if self.modalita != "avanzata":
            self.cb_estratto_month.grid_remove()
            self.cb_estratto_year.grid_remove()
            
        # 🧱 Contenitore orizzontale per i due LabelFrame
        riepilogo_frame = tk.Frame(cal_frame)
        riepilogo_frame.pack(fill=tk.X, padx=2, pady=(8, 8))

        # 🔴 Riepilogo Mese
        self.totalizzatore_mese_frame = ttk.LabelFrame(riepilogo_frame, text="⚙️ Riepilogo Mese corrente", style="RedBold.TLabelframe")
        self.totalizzatore_mese_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.totalizzatore_mese_entrate_label = ttk.Label(self.totalizzatore_mese_frame, text="Totale Entrate mese: 0.00 €", foreground="green", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_entrate_label.pack(anchor="w", padx=6, pady=(2,0))

        self.totalizzatore_mese_uscite_label = ttk.Label(self.totalizzatore_mese_frame, text="Totale Uscite mese: 0.00 €", foreground="red", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_uscite_label.pack(anchor="w", padx=6, pady=(2,0))

        self.totalizzatore_mese_diff_label = ttk.Label(self.totalizzatore_mese_frame, text="Differenza mese: 0.00 €", foreground="blue", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_diff_label.pack(anchor="w", padx=6, pady=(2,4))

        # 🔵 Riepilogo Anno
        self.totalizzatore_frame = ttk.LabelFrame(riepilogo_frame, text="⚙️ Riepilogo Anno corrente", style="RedBold.TLabelframe")
        self.totalizzatore_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self.totalizzatore_entrate_label = ttk.Label(self.totalizzatore_frame, text="Totale Entrate: 0.00 €", foreground="green", font=("Arial", 10, "bold"))
        self.totalizzatore_entrate_label.pack(anchor="w", padx=6, pady=(2,0))

        self.totalizzatore_uscite_label = ttk.Label(self.totalizzatore_frame, text="Totale Uscite: 0.00 €", foreground="red", font=("Arial", 10, "bold"))
        self.totalizzatore_uscite_label.pack(anchor="w", padx=6, pady=(2,0))

        self.totalizzatore_diff_label = ttk.Label(self.totalizzatore_frame, text="Differenza: 0.00 €", foreground="blue", font=("Arial", 10, "bold"))
        self.totalizzatore_diff_label.pack(anchor="w", padx=6, pady=(2,4))

        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))
        style.configure("Custom.Treeview", font=("Arial", 10))  # Testo normale nelle celle
        style.configure("Custom.Treeview.Heading", font=("Arial", 10))  # Testo normale nelle intestazioni

        self.spese_mese_frame = ttk.LabelFrame(cal_frame, text="Riepilogo mese per data", style="RedBold.TLabelframe")
        self.spese_mese_frame.pack(fill=tk.BOTH, expand=False, padx=2, pady=(2,4))
        self.spese_mese_tree = ttk.Treeview(
            self.spese_mese_frame,
            style="Custom.Treeview",
            columns=("Data", "Categoria", "Descrizione", "Importo", "Tipo"),
            show="headings",
            height=30  # <-- Modificato qui da 10 a 5
        )
        self.spese_mese_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.spese_mese_tree.bind("<Double-1>", self.on_spese_mese_tree_double_click) # Doppio click riepilogo mese corrente
        
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
        for col in self.spese_mese_tree["columns"]:
            self.spese_mese_tree.heading(col, command=lambda _col=col: self.treeview_sort_column(self.spese_mese_tree, _col, False))
  
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
  
        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))
        stat_frame = ttk.LabelFrame(right_frame, text="⚙️ Statistiche Spese", style="RedBold.TLabelframe")
        stat_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(8, 8))

        # 🔧 Espansione tabella
        stat_frame.rowconfigure(3, weight=1)
        stat_frame.columnconfigure(0, weight=1)

        mode_frame = ttk.Frame(stat_frame)
        mode_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 0))
        self.stats_mode = tk.StringVar(value="giorno")

        # Stili pulsanti
        style.configure("Giorno.TButton", background="#00FFFF", foreground="black", font=("Arial", 8))
        style.configure("Mese.TButton", background="#00FFFF", foreground="black", font=("Arial", 8))
        style.configure("Anno.TButton", background="#00FFFF", foreground="black", font=("Arial", 8))
        style.configure("Totali.TButton", background="#FF6666", foreground="black", font=("Arial", 8))
        style.configure("Categoria.TButton", background="#90EE90", foreground="black", font=("Arial", 8))
        style.configure("Esporta.TButton", background="#ADD8E6", foreground="black", font=("Arial", 8))
        style.configure("Stat.Custom.Treeview", font=("Arial", 10))  # Testo normale nelle celle
        style.configure("Stat.Custom.Treeview.Heading", font=("Arial", 10))  # Testo normale nelle intestazioni

        ttk.Button(mode_frame, text="📅 Giorno", command=lambda: self.set_stats_mode("giorno"), width=9, style="Giorno.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(mode_frame, text="📅 Mese", command=lambda: self.set_stats_mode("mese"), width=9, style="Mese.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(mode_frame, text="📅 Anno", command=lambda: self.set_stats_mode("anno"), width=9, style="Anno.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(mode_frame, text="📅 Totali", command=lambda: self.set_stats_mode("totali"), width=9, style="Totali.TButton").pack(side=tk.LEFT, padx=1)

        mode_frame_right = ttk.Frame(mode_frame)
        mode_frame_right.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        if self.modalita == "avanzata":
            ttk.Button(mode_frame_right, text="⏰ Estrai Giorno", command=self.export_giorno_forzato, style="Esporta.TButton").pack(side=tk.RIGHT, padx=1)
            ttk.Button(mode_frame_right, text="⏰ Estrai Mese", command=self.export_month_detail, style="Esporta.TButton").pack(side=tk.RIGHT, padx=1)
            ttk.Button(mode_frame_right, text="⏰ Estrai Anno", command=self.export_anno_dettagliato, style="Esporta.TButton").pack(side=tk.RIGHT, padx=1)
            ttk.Button(mode_frame, text="🔍 Categoria", command=self.open_analisi_categoria, width=12, style="Categoria.TButton").pack(side=tk.LEFT, padx=2)

        self.stats_label = ttk.Label(stat_frame, text="")
        self.stats_label.grid(row=1, column=0, sticky="w", padx=6, pady=(2, 0))

        totali_row = ttk.Frame(stat_frame)
        totali_row.grid(row=2, column=0, sticky="ew", padx=6, pady=(2, 0))

        self.totali_label = ttk.Label(totali_row, text="", font=("Arial", 11))
        self.totali_label.pack(side=tk.LEFT)

        self.considera_ricorrenze_var = tk.BooleanVar(value=True)
        if self.modalita == "avanzata":
            self.chk_ricorrenze = tk.Checkbutton(
                totali_row,
                text="Includi movimenti futuri nei totali",
                bg="yellow",
                activebackground="gold",
                variable=self.considera_ricorrenze_var,
                command=self.refresh_gui,
                font=("Arial", 8)
            )
            self.chk_ricorrenze.pack(side=tk.RIGHT, padx=12)

        # 📊 Tabella con intestazioni e colori
        table_container = tk.Frame(stat_frame)
        table_container.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)

        self.stats_table = ttk.Treeview(table_container, columns=("A", "B", "C", "D", "E", "F"), show="headings",style="Stat.Custom.Treeview")
        self.stats_table.pack(fill=tk.BOTH, expand=True)

        # Intestazioni descrittive
        headers = {
            "A": "🗓️ Data",
            "B": "📂 Categoria",
            "C": "📝 Descrizione",
            "D": "💰 Importo (€)",
            "E": "📌 Tipo",
            "F": "✏️ Modifica"
        }

        for col in ("A", "B", "C", "D", "E", "F"):
            self.stats_table.heading(col, text=headers[col], command=lambda _col=col: self.treeview_sort_column(self.stats_table, _col, False))

        self.stats_table.column("A", width=10, anchor="center")
        self.stats_table.column("B", width=18, anchor="center")
        self.stats_table.column("C", width=20, anchor="w")
        self.stats_table.column("D", width=10, anchor="e")
        self.stats_table.column("E", width=10, anchor="center")
        self.stats_table.column("F", width=10, anchor="center")

        self.set_stats_mode("giorno")
        self.stats_table.tag_configure("uscita", foreground="red")
        self.stats_table.tag_configure("entrata", foreground="green")
        self.stats_table.bind("<Double-1>", self.on_stats_table_double_click)
        self.stats_table.bind("<ButtonRelease-1>", self.on_table_click)

        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))
        form_frame = ttk.LabelFrame(right_frame, text="⚙️ Inserisci/Modifica Spesa/Entrata", style="RedBold.TLabelframe")
        form_frame.pack(fill=tk.X, padx=2, pady=(8, 8))
        form_frame.grid_columnconfigure(1, weight=1)

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

        self.blocca_data_var = tk.BooleanVar(value=False)
        self.checkbox_blocca_data = tk.Checkbutton(
            data_frame,
            text="Blocca data",
            variable=self.blocca_data_var,
            command=self.on_blocca_data_changed
        )
        self.checkbox_blocca_data.pack(side="left", padx=4)

        row += 1
        
        ttk.Label(form_frame, text="🔍 Seleziona categoria:").grid(row=row, column=0, sticky="e")
        combo_frame = ttk.Frame(form_frame)
        combo_frame.grid(row=row, column=1, sticky="w", columnspan=2)  

        self.cat_sel = tk.StringVar(value=self.categorie[0])
        
        self.cat_menu = ttk.Combobox(combo_frame, textvariable=self.cat_sel, values=sorted(self.categorie), state="readonly", width=25, font=("Arial", 11, "bold"))
        self.cat_menu.pack(side="left")
        
        self.label_smartcat = ttk.Label(combo_frame, text="💡 SmartCat attiva", foreground="red", font=("Arial", 9, "bold"))
        self.label_smartcat.pack(side="left", padx=(6, 0))
        
        # 🔍 Pulsante "Voci simili"
        self.btn_spese_simili = tk.Button(
            combo_frame,
            text=f"🔍 Voci simili ± {toll}",
            font=("Arial", 9),
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            activeforeground="white",
            relief="raised",
            cursor="hand2",
            command=self.mostra_spese_simili
        )
        self.btn_spese_simili.pack(side="left", padx=(6, 0))
        self.btn_spese_simili.pack_forget()  # 👈 lo nascondi all'avvio

        if not self.suggerimenti_attivi:
            self.label_smartcat.config(text="🛠️ SmartCat disattiva", foreground="green")
            self.aggiorna_bottone_spese_simili(visibile=False)
        else:
             self.label_smartcat.config(text="💡 SmartCat attiva", foreground="red")
             
        self.cat_menu.bind("<<ComboboxSelected>>", self.on_categoria_changed)
        row += 1
        
        ttk.Label(form_frame, text="ℹ️ Descrizione:").grid(row=row, column=0, sticky="e")
        def convalida_descrizione(nuovo_valore_1):
         return len(nuovo_valore_1) <= 30

        vdesc = form_frame.register(convalida_descrizione)
        self.desc_entry = ttk.Entry(form_frame, width=30, validate="key", validatecommand=(vdesc, "%P"))
        self.desc_entry.grid(row=row, column=1, sticky="w")
        row += 1
        
        ttk.Label(form_frame, text="💰 Importo (€):⏎").grid(row=row, column=0, sticky="e")
        importo_frame = ttk.Frame(form_frame)
        
        def convalida_input(nuovo_valore_2):
         if nuovo_valore_2 == "":
              return True  # consente campo vuoto
         import re
         return len(nuovo_valore_2) <= 12 and re.match(r"^\d*[.,]?\d{0,2}$", nuovo_valore_2) is not None
         
        vcmd = form_frame.register(convalida_input)       
        self.imp_entry = ttk.Entry(importo_frame, width=12, validate="key", validatecommand=(vcmd, "%P")) #cat auto    
        self.imp_entry.pack(side=tk.LEFT)      
        self.imp_entry.bind("<KeyRelease>", self.aggiorna_categoria_automatica)
        self.imp_entry.bind("<Return>", lambda event: self.add_spesa()) ############Premi return per confermsre
        importo_frame.grid(row=row, column=1, sticky="w")
       
        row += 1

        # Contenitore orizzontale per i bottoni
        pannello_bottoni = tk.Frame(form_frame)
        pannello_bottoni.grid(row=row, column=1, columnspan=6, sticky="w", pady=4)

        style.configure("AggiungiSpesa.TButton", background="#32CD32", foreground="black", font=("Arial", 8))
        style.configure("SalvaModifica.TButton", background="#32CD32", foreground="black", font=("Arial", 8))
        style.configure("CancellaVoce.TButton", background="red", foreground="black", font=("Arial", 8))
        style.configure("CalcolaMancanti.TButton", background="orange", foreground="black", font=("Arial", 8))
        
        # Bottoni dentro il pannello — uno accanto all'altro
        self.btn_aggiungi = ttk.Button(pannello_bottoni, text="💸 Aggiungi Spesa/Entrata", command=self.add_spesa, style="AggiungiSpesa.TButton")
        self.btn_aggiungi.pack(side="left", padx=4)
        self.btn_modifica = ttk.Button(pannello_bottoni, text="💾 Salva Modifica", command=self.salva_modifica, state=tk.DISABLED, style="SalvaModifica.TButton")
        self.btn_modifica.pack(side="left", padx=4)
        self.btn_cancella = ttk.Button(pannello_bottoni, text="❌ Cancella", command=self.cancella_voce, state=tk.DISABLED, style="CancellaVoce.TButton")
        self.btn_cancella.pack(side="left", padx=4)
        btn_importa_popup = ttk.Button(pannello_bottoni, text="📥 Importa", command=self.apri_finestra_importa, style="AggiungiSpesa.TButton")
        btn_importa_popup.pack(side="left", padx=6)
        btn_calcola_mancanti_popup = ttk.Button(pannello_bottoni, text="📥", command=self.calcola_mancanti, style="CalcolaMancanti.TButton", width=2)
        btn_calcola_mancanti_popup.pack(side="left", padx=6)
        
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
        self.lbl_tipo_percentuale = ttk.Label(importo_frame, text="", font=("Arial", 9, "bold"))
        self.lbl_tipo_percentuale.pack(side=tk.LEFT, padx=4)
        self.on_categoria_changed(manuale=False)
        
        style.configure("Red.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))
        ric_frame = ttk.LabelFrame(form_frame, text="🔄 Ripeti Spesa/Entrata", style="Red.TLabelframe")
        ric_frame.grid(row=row, column=0, columnspan=4, sticky="w", padx=2, pady=(2, 7))
        
        # Nascondi in modalita semplice
        if self.modalita != "avanzata":
            ric_frame.grid_remove()
            
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

        style.configure("AggiungiRicorrenza.TButton", background="#32CD32", foreground="black", font=("Arial", 8))  # Aggiungi Ricorrenza - verde
        style.configure("CancellaRicorrenza.TButton", background="red", foreground="black", font=("Arial", 8))  # Cancella Ricorrenza - rosso
        style.configure("ListaRicorrenze.TButton", background="#FFA500", foreground="black", font=("Arial", 8))  # Lista Ricorrenze - arancione

        self.btn_add_ricorrenza = ttk.Button(ric_frame, text="📂 Aggiungi", command=self.add_ricorrenza, style="AggiungiRicorrenza.TButton")
        self.btn_add_ricorrenza.grid(row=0, column=6, padx=10, pady=2)
        self.btn_cancella_ricorrenza = ttk.Button(ric_frame, text="❌ Cancella", command=self.del_ricorrenza, style="CancellaRicorrenza.TButton")
        self.btn_cancella_ricorrenza.grid(row=0, column=7, padx=5, pady=2)
        
        # Nascondi in modalita semplice
        if self.modalita == "avanzata":
        
         self.btn_modifica_ricorrenza = ttk.Button(ric_frame, text="🔄 Lista", command=self.mostra_lista_ricorrenze, style="ListaRicorrenze.TButton")
         self.btn_modifica_ricorrenza.grid(row=0, column=8, padx=5, pady=2)

        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()

        style.configure("RedBold.TLabelframe.Label", foreground="red", font=("Arial", 10, "bold"))

        aggiungi_cat_frame = ttk.LabelFrame(right_frame, text="✅ Aggiungi/Modifica Categoria", style="RedBold.TLabelframe")
        aggiungi_cat_frame.pack(fill=tk.X, padx=2, pady=(8, 2))

        self.nuova_cat = tk.StringVar()
        style.configure("AggiungiCategoria.TButton", background="#32CD32", foreground="black", font=("Arial", 8))
        style.configure("SuggerisciCategoria.TButton", background="#FFA500", foreground="black", font=("Arial", 8))
        style.configure("ModificaNome.TButton", background="#FFA500", foreground="black", font=("Arial", 8))
        style.configure("CancellaCategoria.TButton", background="red", foreground="black", font=("Arial", 8))

        def convalida_categoria(valore): return len(valore) <= 20
        vcmd_cat = aggiungi_cat_frame.register(convalida_categoria)

        # Tutto in una sola riga (row=0)
        ttk.Label(aggiungi_cat_frame, text="🔍 Nome:").grid(row=0, column=0, sticky="e", padx=4)
        self.entry_nuova_cat = ttk.Entry(
            aggiungi_cat_frame,
            textvariable=self.nuova_cat,
            width=20,
            validate="key",
            validatecommand=(vcmd_cat, "%P")
        )
        self.entry_nuova_cat.grid(row=0, column=1, sticky="w", padx=2)
        self.entry_nuova_cat.bind("<Return>", lambda event: self.add_categoria())

        ttk.Button(aggiungi_cat_frame, text="➕ Aggiungi", command=self.add_categoria, style="AggiungiCategoria.TButton").grid(row=0, column=2, padx=4)

        # Selettore e bottoni su stessa riga
        ttk.Label(aggiungi_cat_frame, text="✅ Seleziona:").grid(row=0, column=3, sticky="e", padx=4)
        self.cat_mod_sel = tk.StringVar(value=self.categorie[0])
        self.cat_mod_menu = ttk.Combobox(
            aggiungi_cat_frame,
            textvariable=self.cat_mod_sel,
            values=sorted(self.categorie),
            state="readonly",
            width=18
        )
        self.cat_mod_menu.grid(row=0, column=4, sticky="w", padx=2)
        self.cat_mod_menu.bind("<<ComboboxSelected>>", lambda e: self.on_categoria_modifica_changed())

        self.btn_modifica_categoria = ttk.Button(aggiungi_cat_frame, text="⚙️ Modifica", command=self.modifica_categoria, style="ModificaNome.TButton")
        self.btn_modifica_categoria.grid(row=0, column=5, padx=4)

        self.btn_cancella_categoria = ttk.Button(aggiungi_cat_frame, text="❌ Cancella", command=self.cancella_categoria, style="CancellaCategoria.TButton")
        self.btn_cancella_categoria.grid(row=0, column=6, padx=4)

        if self.modalita == "avanzata":
            ttk.Button(aggiungi_cat_frame, text="✨", command=self.apri_categorie_suggerite, style="SuggerisciCategoria.TButton", width=2 ).grid(row=0, column=7, padx=6)

        self.refresh_gui()
        self.after(1000, self.check_aggiornamento_con_api)
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
            # Aggiorna la variabile della data spesa se non bloccata
            if not self.blocca_data_var.get():
                self.data_spesa_var.set(data.strftime("%d-%m-%Y"))

            mese_corrente = self.estratto_month_var.get()
            anno_corrente = self.estratto_year_var.get()

            mese_da_cal = f"{data.month:02d}"
            anno_da_cal = str(data.year)

            # Aggiorna i combobox solo se mese o anno sono cambiati
            if mese_corrente != mese_da_cal:
                self.estratto_month_var.set(mese_da_cal)
                self.cb_estratto_month.current(data.month - 1)

            if anno_corrente != anno_da_cal:
                self.estratto_year_var.set(anno_da_cal)
                self.cb_estratto_year.set(anno_da_cal)

            # Applica l’estratto (aggiornamento vista) con leggero ritardo per evitare loop
            self.after(100, lambda: self.apply_estratto("giorno"))
            
        except Exception as e:
            print(f"Errore durante il cambio data: {e}")
            
    def on_month_changed(self, event=None):
        m, y = self.cal.get_displayed_month()
        primo = datetime.date(y, m, 1)

        # Solo se il giorno 1 NON è già selezionato (eviti loop infiniti)
        if self.cal.selection_get() != primo:
            self.cal.selection_set(primo)
        self.data_spesa_var.set(primo.strftime("%d-%m-%Y"))

        # Aggiorna i combobox per riflettere il mese e anno attualmente visualizzati
        self.cb_estratto_month.set("{:02d} - {}".format(m, self.cb_estratto_month['values'][m-1][5:]))
        self.cb_estratto_year.set(str(y))

        # Aggiorna la vista GIORNO
        self.apply_estratto("giorno")
    
    def aggiorna_titolo_finestra(self):
        current_folder = os.path.basename(os.getcwd())
        self.title(f"💰 {NAME} Pro v {VERSION}  — Email: helpcasafacilepro@gmail.com —  Utente:► {current_folder}")
              
    def aggiorna_bottone_spese_simili(self, visibile=True):
        if visibile:
            if not self.btn_spese_simili.winfo_ismapped():
                self.btn_spese_simili.pack(side="left", padx=(6, 0))
        else:
            if self.btn_spese_simili.winfo_ismapped():
                self.btn_spese_simili.pack_forget()

    def aggiorna_categoria_automatica(self, event=None):

        if not self.suggerimenti_attivi:
            self.label_smartcat.config(text="🛠️ SmartCat disattiva", foreground="green")
            self.aggiorna_bottone_spese_simili(visibile=False)
            return

        valore = self.imp_entry.get().replace(",", ".").strip()
        if not valore:
            self.categoria_bloccata = False
            self.aggiorna_bottone_spese_simili(visibile=False)
            return

        try:
            imp_corrente = float(valore)
        except ValueError:
            return

        # 👇 Limite: solo spese degli ultimi 12 mesi
        oggi = datetime.date.today()
        un_anno_fa = oggi - datetime.timedelta(days=365)

        somiglianza_minima = float("inf")
        categoria_migliore = None

        for d, lista in self.spese.items():
            if d < un_anno_fa:
                continue  # ⛔ fuori intervallo

            for voce in lista:
                try:
                    categoria, _, importo, _ = voce[:4]
                except ValueError:
                    continue
                diff = abs(importo - imp_corrente)
                if diff < somiglianza_minima:
                    somiglianza_minima = diff
                    categoria_migliore = categoria

        if categoria_migliore and not self.categoria_bloccata:
            self.cat_sel.set(categoria_migliore)
            self.on_categoria_changed(manuale=False)
            self.label_smartcat.config(text="💡 SmartCat attiva", foreground="red")
            self.btn_spese_simili.pack(side="left", padx=(6, 0))

            style = ttk.Style()
            style.configure("Highlight.TCombobox", foreground="red")
            self.cat_menu.configure(style="Highlight.TCombobox")
            self.cat_menu.after(2000, lambda: self.cat_menu.configure(style="TCombobox"))
         
    def mostra_spese_simili(self):
   
        valore = self.imp_entry.get().replace(",", ".").strip()
        try:
            target = float(valore)
        except ValueError:
            self.show_custom_warning("Errore", "Importo mancante o non valido.")
            return

        tolleranza = int(self.spin_tolleranza.get()) if hasattr(self, "spin_tolleranza") else toll
        limite_basso = target - tolleranza
        limite_alto = target + tolleranza

        # Include la data (d) accanto a ogni voce
        voci_simili = [
            (d, *voce)
            for d, lista in self.spese.items()
            for voce in lista
            if len(voce) >= 4 and limite_basso <= voce[2] <= limite_alto
        ]

        if not voci_simili:
            self.show_custom_warning("Nessuna corrispondenza", "Nessuna spesa trovata con questo importo.")
            return

        popup = tk.Toplevel(self)
        popup.title(f"Spese simili a €{target:.2f}")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.bind("<Escape>", lambda e: popup.destroy())

        larghezza, altezza = 650, 360
        x = (popup.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (popup.winfo_screenheight() // 2) - (altezza // 2)
        popup.geometry(f"{larghezza}x{altezza}+{x}+{y}")

        tk.Label(
            popup,
            text=f"🔎 Spese comprese tra €{limite_basso:.2f} e €{limite_alto:.2f}",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(pady=(10, 4))

        columns = ("data", "tipo", "categoria", "descrizione", "importo")
        headers = {
            "data": "📅 Data",
            "tipo": "💼 Tipo",
            "categoria": "📂 Categoria",
            "descrizione": "📝 Descrizione",
            "importo": "💶 Importo"
        }

        tree = ttk.Treeview(popup, columns=columns, show="headings", height=10)
        tree.pack(padx=12, pady=(0, 6), fill="both", expand=True)

        for col in columns:
            tree.heading(col, text=headers[col], command=lambda c=col: sort_column(tree, c, False))

        tree.column("data", width=90, anchor="center")
        tree.column("tipo", width=80, anchor="center")
        tree.column("categoria", width=120, anchor="w")
        tree.column("descrizione", width=220, anchor="w")
        tree.column("importo", width=80, anchor="e")
        voci_simili.sort(key=lambda x: x[0], reverse=True)  # 👈 ordina per data, decrescente
        for voce in voci_simili:
            try:
                data, categoria, descrizione, importo, tipo = voce
                tree.insert("", tk.END, values=(
                    data.strftime("%d-%m-%Y"),
                    tipo,
                    categoria,
                    descrizione,
                    f"€{importo:.2f}"
                ))
            except Exception as e:
                print(f"[Voce malformata]: {voce} → {e}")
                continue

        def usa_categoria():
            selezione = tree.selection()
            if not selezione:
                self.show_custom_warning("Attenzione", "Seleziona una spesa per copiarne la categoria.")
                return
            valori = tree.item(selezione[0], "values")
            self.cat_sel.set(valori[2])  # categoria
            self.on_categoria_changed(manuale=True)
            popup.destroy()

        btn_frame = tk.Frame(popup, bg="white")
        btn_frame.pack(pady=(4, 12))

        tk.Button(
            btn_frame,
            text="📥 Usa questa categoria",
            command=usa_categoria,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 9, "bold"),
            relief="raised",
            cursor="hand2",
            padx=10
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame,
            text="❌ Chiudi",
            command=popup.destroy,
            bg="#FFCC00",
            fg="black",
            font=("Arial", 9, "bold"),
            relief="raised",
            cursor="hand2",
            padx=10
        ).pack(side="left", padx=8)

        # Ordinamento colonne (con supporto data/importo)
        def sort_column(tv, col, reverse):
            def extract(val):
                try:
                    if col == "importo":
                        return float(val.replace("€", "").replace(",", "").strip())
                    elif col == "data":
                        return datetime.datetime.strptime(val, "%d-%m-%Y")
                    return str(val).lower()
                except:
                    return val

            idx = columns.index(col)
            dati = [(tv.item(k)["values"], k) for k in tv.get_children()]
            try:
                dati.sort(key=lambda x: extract(x[0][idx]), reverse=reverse)
            except Exception as e:
                print(f"[Errore ordinamento '{col}']: {e}")
                return
    
            for i, (valori, k) in enumerate(dati):
                tv.move(k, "", i)

            tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

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
        print("🔚 Chiusura dell'app in corso...")
        # 🗂️ Salva geometria e database
        self.save_window_geometry()
        self.save_db()
        # 🌐 Chiudi il web server se esiste
        try:
            if hasattr(self, "server"):
                self.server.shutdown()
                self.server.server_close()
                print("🌐 Web server chiuso.")
            else:
                print("🌐 Nessun web server attivo.")
        except Exception as e:
            print(f"⚠️ Web server non attivo o errore in chiusura: {e}")
        # 🧹 Distruggi la GUI
        try:
            self.destroy()
        except Exception as e:
            print(f"⚠️ Errore nella chiusura della GUI: {e}")
        sys.exit(0)

        
    def carica_memoria_descrizioni(self):
        if os.path.exists(MEM_CAT):
           with open(MEM_CAT, "r", encoding="utf-8") as f:
            self.memoria_descrizioni_categoria = json.load(f)
        else:
            self.memoria_descrizioni_categoria = {}

    def load_db(self):
        if not os.path.exists(DB_FILE):
            # Inizializza tutto da zero
            self.db = {
                "categorie": ["Generica"],
                "categorie_tipi": {"Generica": "Uscita"},
                "spese": [],
                "ricorrenze": {},
                "_window_geometry": None
            }
            self.categorie = self.db["categorie"]
            self.categorie_tipi = self.db["categorie_tipi"]
            self.spese = {}
            self.ricorrenze = self.db["ricorrenze"]
            self._window_geometry = self.db["_window_geometry"]
            return

        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.db = json.load(f)

            self.categorie = self.db.get("categorie", ["Generica"])
            self.categorie_tipi = self.db.get("categorie_tipi", {"Generica": "Uscita"})
            self.spese = {}
            for obj in self.db.get("spese", []):
                d = datetime.datetime.strptime(obj["date"], "%d-%m-%Y").date()
                entries = []
                for e in obj.get("entries", []):
                    if "id_ricorrenza" in e:
                        entries.append((e["categoria"], e["descrizione"], float(e["importo"]), e["tipo"], e["id_ricorrenza"]))
                    else:
                        entries.append((e["categoria"], e["descrizione"], float(e["importo"]), e["tipo"]))
                self.spese[d] = entries
            self.ricorrenze = self.db.get("ricorrenze", {})
            self._window_geometry = self.db.get("_window_geometry", None)

        except Exception as e:
            print("Errore caricamento DB:", e)
            self.db = {
                "categorie": ["Generica"],
                "categorie_tipi": {"Generica": "Uscita"},
                "spese": [],
                "ricorrenze": {},
                "_window_geometry": None
            }

            self.categorie = self.db["categorie"]
            self.categorie_tipi = self.db["categorie_tipi"]
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

        with open(MEM_CAT, "w", encoding="utf-8") as f:
            json.dump(self.memoria_descrizioni_categoria, f, ensure_ascii=False, indent=2)

    def toggle_tipo_spesa(self):
        v = self.tipo_spesa_var.get()
        nuovo = "Entrata" if v == "Uscita" else "Uscita"
        self.tipo_spesa_var.set(nuovo)
        self.btn_tipo_spesa.config(text=nuovo)
        new_style = 'GreenOutline.TButton' if nuovo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)

    def aggiorna_combobox_categorie(self):
        """Ordina le categorie alfabeticamente, mette 'Generica' in cima se presente, e forza la selezione visiva."""
        altre = sorted([c for c in self.categorie if c != "Generica"], key=str.lower)
        ordinata = ["Generica"] + altre if "Generica" in self.categorie else altre

        self.categorie = ordinata
        self.cat_menu["values"] = self.categorie
        self.cat_mod_menu["values"] = self.categorie

        if "Generica" in self.categorie:
            idx = self.categorie.index("Generica")
            self.cat_menu.current(idx)
            self.cat_mod_menu.current(idx)
        elif self.categorie:
            self.cat_menu.current(0)
            self.cat_mod_menu.current(0)

    def on_categoria_changed(self, event=None, manuale=True):
        if manuale:    
          self.categoria_bloccata = True  # ⛔ Blocca suggerimenti automatici
        cat = self.cat_sel.get()
        tipo_cat, perc_entrate, perc_uscite = self.suggerisci_tipo_categoria(cat)
        self.tipo_spesa_var.set(tipo_cat)
        self.btn_tipo_spesa.config(text=tipo_cat)
        new_style = 'GreenOutline.TButton' if tipo_cat == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)
        self.lbl_tipo_percentuale.config(
            text=f"{perc_entrate}% Entrate / {perc_uscite}% Uscite"
        )
        self.label_smartcat.config(text="🛠️ SmartCat disattiva", foreground="green")
        self.aggiorna_bottone_spese_simili(visibile=False)
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
        self.refresh_gui()
        self.show_custom_info("Attenzione", f"Categoria '{old_nome}' rinominata in '{new_nome}'.")
        
    def conferma_cancella_categoria(self, cat):
        popup = tk.Toplevel(self)
        popup.title("Conferma eliminazione")
        popup.resizable(False, False)
        width, height = 320, 130
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
        popup.configure(bg="#FFFACD")  #
        label = tk.Label(
            popup,
            text=f"Vuoi davvero cancellare la categoria '{cat}'?\nLe spese rimarranno ma saranno\nrinominate come '{self.CATEGORIA_RIMOSSA}'.",
            font=("Arial",10),
            justify="center",
            wraplength=280,
            bg="#FFFACD"
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
            
        frame = tk.Frame(popup, bg="#FFFACD")
        frame.pack(pady=4)
        b1 = tk.Button(frame, text="Elimina", font=("Arial", 9), width=8, command=do_ok, bg="#FF4444")
        b2 = tk.Button(frame, text="Annulla", font=("Arial", 9), width=8, command=do_cancel, bg="#FFEB3B")
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

        self.save_db()
        self.refresh_gui()
        self.on_categoria_changed()
        
    def show_custom_warning(self, title, message):
        self._show_custom_message(title, message, "yellow", "black", "warning")

    def show_custom_info(self, title, message):
        self._show_custom_message(title, message, "lightblue", "black", "info")

    def show_custom_askyesno(self, title, message):
        dialog = tk.Toplevel(self, bg="yellow")  # Giallo chiaro
        dialog.withdraw() 
        dialog.title(title)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.transient(self)

        dialog.update_idletasks()
        w, h = 320, 140
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        dialog.deiconify()
        dialog.lift()              # Porta in cima
        dialog.attributes("-topmost", True)  # Mantieni in primo piano

        # Etichetta del messaggio con sfondo giallo
        label = tk.Label(dialog, text=message, font=("Arial", 10), justify="left", padx=16, pady=12, bg="yellow")
        label.pack()

        # Frame bottoni con sfondo giallo
        btns = tk.Frame(dialog, bg="yellow")
        btns.pack(pady=(0,10))

        result = {"value": False}

        def yes():
            result["value"] = True
            dialog.destroy()

        def no():
            result["value"] = False
            dialog.destroy()

        b1 = tk.Button(btns, text="Sì", width=8, command=yes, bg="#32CD32", fg="black")   # Verde chiaro
        b2 = tk.Button(btns, text="No", width=8, command=no, bg="#FFA500", fg="black")    # Giallo chiaro
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
        #dialog.wait_window()  
        #dialog.after(20000, dialog.destroy)
        if USE_WAIT_WINDOW:
            dialog.wait_window()
        else:
            dialog.after(WARN_TIMEOUT, dialog.destroy)

        
    def reset_data_spesa(self):
        today = datetime.date.today()
        self.data_spesa_var.set(today.strftime("%d-%m-%Y"))

    def reset_ric_data_inizio(self):
        oggi = datetime.date.today()
        self.ricorrenza_data_inizio.set(oggi.strftime("%d-%m-%Y"))

    def add_ricorrenza(self):
        ric_type = self.ricorrenza_tipo.get()
        if ric_type == "Nessuna":
            self.show_custom_warning("Errore", "Seleziona un tipo di ricorrenza valido.")
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
            self.show_custom_warning("Errore", "Importo mancante o non valido.")
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
        self.refresh_gui()
        self.show_custom_info("Ricorrenza aggiunta", f"Spesa/entrata ricorrente aggiunta per {n} volte.")
        self.ricorrenza_tipo.set("Nessuna")  
        self.reset_modifica_form()
         
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
        tk.Button(frame_btn, text="Cancella", command=do_ok, width=10, bg="red", fg="white").grid(row=0, column=0, padx=8)
        tk.Button(frame_btn, text="Annulla", command=do_cancel, width=10, bg="yellow", fg="black").grid(row=0, column=1, padx=8)

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
        self.refresh_gui()
        
    def mostra_lista_ricorrenze(self, larghezza_colonne=None):
        """Mostra una finestra centrata con l'elenco delle ricorrenze, inclusa la colonna tipo."""
        lista_window = tk.Toplevel(self)
        lista_window.title("Lista Ricorrenze")
        larghezza, altezza = 870, 300
        x = (self.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (self.winfo_screenheight() // 2) - (altezza // 2)
        lista_window.geometry(f"{larghezza}x{altezza}+{x}+{y}")
        lista_window.resizable(False, False)
        lista_window.bind("<Escape>", lambda e: lista_window.destroy())
        columns = ("Categoria", "Tipo", "Ripetizioni", "ID", "Data Inserimento")
        tree = ttk.Treeview(lista_window, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
        default_larghezze = {
            "Categoria": 220,
            "Tipo": 110,
            "Ripetizioni": 90,
            "ID": 300,
            "Data Inserimento": 130,
       }

        larghezze = larghezza_colonne if larghezza_colonne else default_larghezze
        for col in columns:
            tree.column(col, width=larghezze.get(col, 200))  # Default 200 se mancante
        tree.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        for id_ricorrenza, dati in self.ricorrenze.items():
            categoria = dati.get("cat", "Sconosciuta")
            ric_tipo = dati.get("tipo", "N/D")
            ripetizioni = dati.get("n", "N/D")
            data_inserimento = dati.get("data_inizio", "N/D")
            tree.insert("", "end", values=(categoria, ric_tipo, ripetizioni, id_ricorrenza, data_inserimento))
        tk.Button(lista_window, text="❌ Chiudi", command=lista_window.destroy, bg="gold", fg="black").grid(row=1, column=1, pady=10)

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
            self.show_custom_warning("Errore", "Importo mancante o non valido.")
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
        
        self.reset_modifica_form()
        self.refresh_gui()
        if not self.blocca_data_var.get():
            self.data_spesa_var.set(datetime.date.today().strftime("%d-%m-%Y"))
        self.categoria_bloccata = False  # 🧠 Rende nuovamente attivo il suggerimento
        self.label_smartcat.config(text="🛠️ SmartCat attiva", foreground="red")
        
    def set_tipo_spesa_editable(self, editable=True):
        if editable:
            self.btn_tipo_spesa.state(["!disabled"])
        else:
            self.btn_tipo_spesa.state(["disabled"])

    def on_table_click(self, event):
        self.suggerimenti_attivi = False  # 🔕 Blocca suggerimento categoria
        self.label_smartcat.config(text="🛠️ SmartCat disattiva", foreground="green")
        self.aggiorna_bottone_spese_simili(visibile=False)
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
        self.set_tipo_spesa_editable(True)
        
        new_style = 'GreenOutline.TButton' if tipo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)
        if len(voce) == 5:
            ric_id = voce[4]
            if ric_id in self.ricorrenze:
                ric = self.ricorrenze[ric_id]
                self.show_custom_info("Voce ricorrente", f"Questa voce è parte di una ricorrenza: {ric['tipo']} x{ric['n']} da {ric['data_inizio']}.\nPuoi cancellare tutta la ricorrenza dal pannello sotto.")

    def reset_modifica_form(self):
        self.suggerimenti_attivi = True  # ✅ Riattiva suggerimento categoria
        self.label_smartcat.config(text="🛠️ SmartCat attiva", foreground="red")
        self.modifica_idx = None
        self.btn_modifica["state"] = tk.DISABLED
        self.btn_aggiungi["state"] = tk.NORMAL
        self.btn_cancella["state"] = tk.DISABLED
        self.desc_entry.delete(0, tk.END)
        self.imp_entry.delete(0, tk.END)
        self.on_categoria_changed()
        self.set_tipo_spesa_editable(True)
        if not self.blocca_data_var.get():
         self.data_spesa_var.set(datetime.date.today().strftime("%d-%m-%Y"))
        self.categoria_bloccata = False  # 🔄 Si riparte da capo

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
            self.show_custom_warning("Errore", "Importo mancante o non valido.")
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
        self.refresh_gui()
        self.reset_modifica_form()
        
    def cancella_voce(self):
        if not self.modifica_idx:
            return
        dt, idx = self.modifica_idx
        if dt in self.spese and 0 <= idx < len(self.spese[dt]):
            del self.spese[dt][idx]
            if not self.spese[dt]:
                del self.spese[dt]
            self.save_db()
            self.refresh_gui()
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

    def treeview_sort_column(self, tv, col, reverse):
        items = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:  
            items.sort(key=lambda t: float(str(t[0]).replace(",", ".").replace("€", "")), reverse=reverse)
        except Exception:
            items.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(items):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

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
        oggi = datetime.date.today()
        ref = self.stats_refdate

        if mode == "giorno":
            try:
                giorno = datetime.datetime.strptime(self.cal.get_date(), "%d-%m-%Y").date()
            except Exception:
                giorno = oggi
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
            for d, sp in self.spese.items():
                
                if mode == "mese":
                    if not (d.year == ref.year and d.month == ref.month):
                        continue
                elif mode == "anno":
                    if d.year != ref.year:
                        continue
                for entry in sp:
                    data_voce = d
                    if not self.considera_ricorrenze_var.get():
                        if mode == "totali":
                            if data_voce > oggi:
                                continue
                        elif mode == "anno":
                            if ref.year == oggi.year:
                                if data_voce > oggi:
                                    continue    
                        elif mode == "mese":
                            if ref.year == oggi.year and ref.month == oggi.month:
                                if data_voce > oggi:
                                    continue
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

        txt_tot = f"Totale Entrate: {tot_entrate:.2f}    Totale Uscite: {tot_uscite:.2f}    Differenza: {(tot_entrate - tot_uscite):.2f}"
        self.totali_label.config(text=txt_tot)

    def update_totalizzatore_anno_corrente(self):
        anno = datetime.date.today().year
        totale_entrate = 0.0
        totale_uscite = 0.0
        for d, sp in self.spese.items():
            if d.year == anno:
                for entry in sp:
                    if hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get() and len(entry) == 5:
                        if d > datetime.date.today():
                            continue
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
                    if hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get() and len(entry) == 5:
                        if d > now:
                            continue
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

        dialog.bind("<Escape>", lambda e: dialog.destroy())

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
            if not os.path.exists(UTENZE_DB):
               with open(UTENZE_DB, "w") as file:
                 file.write("{\n}\n")  # Crea un file vuoto
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

        now = datetime.date.today()
        filename = ""

        if mode == "giorno":
            try:
                giorno = datetime.datetime.strptime(self.cal.get_date(), "%d-%m-%Y").date()
            except Exception:
                giorno = now
            filename = f"Statistiche_Giorno_{giorno.strftime('%d-%m-%Y')}.txt"
        elif mode == "mese":
            monthname = self.get_month_name(ref.month)
            filename = f"Statistiche_Mese_{monthname}_{ref.year}.txt"
        elif mode == "anno":
            filename = f"Statistiche_Anno_{ref.year}.txt"
        else:
            filename = f"Statistiche_Per_Categoria.txt"

        self.show_export_preview("\n".join(lines), default_filename=filename)

        
    def export_month_detail(self):
        ref = self.stats_refdate
        month = ref.month
        year = ref.year
        monthname = self.get_month_name(month)
        oggi = datetime.date.today()

        giorni_settimana = [
            "Lunedì", "Martedì", "Mercoledì", "Giovedì",
            "Venerdì", "Sabato", "Domenica"
        ]

        lines = []
        tot_entrate, tot_uscite = 0.0, 0.0

        lines.append("=" * 100)
        lines.append(f"{('Spese per il mese di ' + monthname + ' ' + str(year)).center(100)}")
        lines.append("=" * 100 + "\n")

        # Trova tutti i giorni con spese in questo mese
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
                    is_ricorrenza = len(entry) == 5
                    # Filtro ricorrenze future se la checkbox è spenta
                    if not self.considera_ricorrenze_var.get():
                        if d > oggi:
                            continue
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

        now = datetime.date.today()
        month = now.strftime("%m-%Y")
        filename = f"Statistiche_Mese_{month}.txt"
        self.show_export_preview("\n".join(lines), default_filename=filename)


    def show_export_preview(self, content, default_filename=None):
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
        
        preview.bind("<Escape>", lambda e: preview.destroy())

        text = tk.Text(preview, wrap="none", font=("Courier new", 10))
        text.insert("1.0", content)
        text.config(state="disabled")
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def save_file():
            """ Salva il contenuto dell'anteprima su file e chiude la finestra. """
            now = datetime.date.today()
            filename = default_filename or f"Statistiche_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=filename,
                title="Salva Statistiche",
                confirmoverwrite=False,
                parent=preview)
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio

                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)
                preview.destroy()
                self.show_custom_warning("Esportazione completata", f"Statistiche esportate in {file}")

        btn_frame = ttk.Frame(preview)
        btn_frame.pack(fill=tk.X, pady=8)

        btn_salva = tk.Button(btn_frame, text="💾 Salva", command=save_file, width=15, bg="forestgreen", fg="black")
        btn_salva.pack(side=tk.LEFT, padx=10)

        btn_chiudi = tk.Button(btn_frame, text="❌ Chiudi", command=preview.destroy, width=15, bg="gold", fg="black")
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
                with open(DB_FILE, "w", encoding="utf-8") as fdst:
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
                self.show_custom_warning("Errore", f"Errore durante l'esportazione: {e}")

    def export_db(self):
        now = datetime.date.today()
        default_dir = EXP_DB
        default_filename = f"Export_Database{now.day:02d}-{now.month:02d}-{now.year}.json"
        file = filedialog.asksaveasfilename(
            title="Esporta Database",
            defaultextension=".json",
            initialdir=default_dir,
            initialfile=default_filename,
            confirmoverwrite=False,
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

        oggi = datetime.date.today()

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
                    is_ricorrenza = len(entry) == 5
                    # Filtro ricorrenze future se la variabile esiste e la checkbox è disattivata
                    if hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get():
                        if year == oggi.year:
                            if d2 > oggi:
                                continue
                        # Se anno è passato, includi tutte le spese dell'anno
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
        
        now = datetime.date.today()
        self.show_export_preview(text, default_filename=f"Statistiche_Anno_{year}.txt")

    def suggerisci_tipo_categoria(self, categoria):
        n_entrate = 0
        n_uscite = 0
        for voci in self.spese.values():
            for voce in voci:
                if len(voce) >= 4 and voce[0] == categoria:
                    tipo = voce[3]
                    if tipo == "Entrata":
                        n_entrate += 1
                    elif tipo == "Uscita":
                        n_uscite += 1
        totale = n_entrate + n_uscite
        if totale == 0:
            return ("Uscita", 0, 0)
        perc_entrate = int(n_entrate / totale * 100)
        perc_uscite = int(n_uscite / totale * 100)
        tipo_prevalente = "Entrata" if n_entrate >= n_uscite else "Uscita"
        return (tipo_prevalente, perc_entrate, perc_uscite)

    def open_analisi_categoria(self):
        popup = tk.Toplevel(self)
        popup.title("Analisi Categoria")
        popup.geometry("700x600")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
    
        popup.bind("<Escape>", lambda e: popup.destroy())
    
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
                
                reset_btn = tk.Button(
                    frame_period,
                    text="↺",              
                    width=2,
                    bg="gold",             
                    fg="black",            
                    font=("Arial", 9, "bold"),
                    command=reset_period
                )
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
        export_btn = tk.Button(frame_buttons, text="💾 Esporta", width=15, bg="orange", fg="white")
        export_btn.pack(side=tk.LEFT, padx=4)
        
        close_btn = tk.Button(frame_buttons, text="❌ Chiudi", width=15, command=popup.destroy, bg="gold", fg="black")
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

                for d, e in sorted(filtered, key=lambda x: x[0], reverse=True):
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
                default_filename = f"Analisi_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
                file = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("File txt", "*.txt")],
                    initialdir=EXPORT_FILES,
                    title="Esporta Analisi Categoria",
                    initialfile=default_filename,
                    confirmoverwrite=False,
                    parent=preview)
                if file:
                    if os.path.exists(file):
                        conferma = self.show_custom_askyesno(
                            "Sovrascrivere file?",
                            f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                        )
                        if not conferma:
                            return  # Annulla salvataggio

                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto_preview)
                        self.show_custom_warning("Esporta", f"Analisi esportata in {file}")
                    preview.destroy()
            tk.Button(frm, text="💾 Salva", command=do_save, width=15, bg="forestgreen", fg="white").pack(side=tk.LEFT, padx=6)
            tk.Button(frm, text="❌ Chiudi", command=preview.destroy, width=12, bg="gold", fg="black").pack(side=tk.RIGHT, padx=6)

            preview.lift()
            preview.attributes('-topmost', True)
            preview.after(100, lambda: preview.attributes('-topmost', False))
            
            preview.bind("<Escape>", lambda e: preview.destroy())
            
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
        
        popup.bind("<Escape>", lambda e: popup.destroy())
    
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
    
        tk.Button(
            btmframe,
            text="↺",
            width=2,
            bg="gold",
            fg="black",
            command=lambda: [
            day_var.set(f"{datetime.date.today().day:02d}"),
            month_var.set(f"{datetime.date.today().month:02d}"),
            year_var.set(str(datetime.date.today().year))
            ]
        ).grid(row=0, column=4)

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
    
            preview.bind("<Escape>", lambda e: preview.destroy())
    
            txt = tk.Text(preview, font=("Arial", 10), wrap="word", height=6)
            txt.insert("1.0", "\n".join(lines))
            txt.configure(state="disabled")
            txt.pack(fill="both", expand=True, padx=10, pady=10)
    
            def do_save():
                default_filename = f"Saldo_Export_{datetime.date.today().strftime('%d-%m-%Y')}.txt"
                path = filedialog.asksaveasfilename(
                    initialfile= default_filename,
                    initialdir=EXPORT_FILES,
                    defaultextension=".txt",
                    title="Salva Saldo",
                    confirmoverwrite=False,
                    filetypes=[("File di testo", "*.txt")],
                    parent=preview
                )
                if path:
                    if os.path.exists(path):
                        conferma = self.show_custom_askyesno(
                            "Sovrascrivere file?",
                            f"Il file '{os.path.basename(path)}' \nesiste già. Vuoi sovrascriverlo?"
                        )
                        if not conferma:
                            return  # Annulla salvataggio
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                    custom_warning("✅ Esportazione completata.", preview)
    
            btns = ttk.Frame(preview)
            btns.pack(pady=10)
            tk.Button(btns, text="💾 Salva", command=do_save, width=12, bg="forestgreen", fg="white").pack(side="left", padx=6)
            tk.Button(btns, text="❌ Chiudi", command=preview.destroy, width=10, bg="gold", fg="black").pack(side="right", padx=6)
            
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
        m = today.month
        self.cb_estratto_month.set("{:02d} - {}".format(m, self.cb_estratto_month['values'][m-1][5:]))
        self.cb_estratto_year.set(str(today.year))
        self.set_stats_mode("mese") 
        self.set_stats_mode("giorno") 
        
    def open_compare_window(self):
        today = datetime.date.today()
        mese_oggi = f"{today.month:02d}"
        anno_oggi = str(today.year)
        compare_by_year = tk.BooleanVar(value=False)
        mostra_future_var = tk.BooleanVar(value=True)
    
        def parse_date(d):
            if isinstance(d, datetime.date):
                return d
            try:
                # Gestisce sia "dd-mm-yyyy" che "yyyy-mm-dd"
                if len(d.split("-")[0]) == 4:
                    return datetime.datetime.strptime(d, "%Y-%m-%d").date()
                else:
                    return datetime.datetime.strptime(d, "%d-%m-%Y").date()
            except Exception:
                return None
    
        def get_rows(mese, anno, per_anno=False):
            rows = []
            oggi = datetime.date.today()
            for d_raw in sorted(self.spese):
                d = parse_date(d_raw)
                if not d:
                    continue
                if not mostra_future_var.get() and d > oggi:
                    continue  # NASCONDI tutte le spese future!
                if (per_anno and d.year == anno) or (not per_anno and d.month == mese and d.year == anno):
                    for voce in self.spese[d_raw]:
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
    
        win.bind("<Escape>", lambda e: win.destroy())
    
        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
    
        anni_spese = set()
        for d in self.spese.keys():
            pd = parse_date(d)
            if pd:
                anni_spese.add(pd.year)
        anno_corrente = today.year
        anni = sorted(set(range(anno_corrente-10, anno_corrente+11)).union(anni_spese), reverse=True)

        mesi = [f"{i:02d}" for i in range(1, 13)]
    
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,8))
        tk.Label(mode_frame, text="Modalità confronto:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(mode_frame, text="Mese", variable=compare_by_year, value=False, command=lambda: update_tables()).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Anno", variable=compare_by_year, value=True, command=lambda: update_tables()).pack(side=tk.LEFT)
        tk.Checkbutton(
            mode_frame,
            text="Includi movimenti futuri nei totali",
            bg="yellow",
            activebackground="gold",
            variable=mostra_future_var
        ).pack(side=tk.LEFT, padx=(30,0))
        mostra_future_var.trace_add("write", lambda *a: update_tables())
    
        # Selezione sinistra
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
        tk.Button(left_select_frame, text="↺", command=reset_left, width=2, bg="gold", fg="black").pack(side="right", padx=7)
        left_tree = ttk.Treeview(left, columns=("Categoria","Data","Entrata","Uscita"), show="headings", height=12)
        style = ttk.Style()
        style.configure("Big.Treeview.Heading", font=("Arial", 10, "bold"))
        style.configure("Big.Treeview", font=("Arial", 10))
        left_tree.configure(style="Big.Treeview")
        for col, w, anchor in [("Categoria",180,"center"),("Data",110,"center"),("Entrata",100,"center"),("Uscita",100,"center")]:
            left_tree.heading(col, text=col, anchor=anchor, command=lambda _col=col: treeview_sort_column(left_tree, _col, False))
            left_tree.column(col, width=w, anchor=anchor, stretch=True)
        left_tree.pack(fill=tk.BOTH, expand=True)
        left_diff_lbl = tk.Label(left, text="", font=("Arial", 10, "bold"))
        left_diff_lbl.pack(pady=(4,0))
    
        # Selezione destra
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
        tk.Button(right_select_frame, text="↺", command=reset_right, width=2, bg="gold", fg="black").pack(side=tk.RIGHT, padx=7)
        right_tree = ttk.Treeview(right, columns=("Categoria","Data","Entrata","Uscita"), show="headings", height=12)
        right_tree.configure(style="Big.Treeview")
        for col, w, anchor in [("Categoria",180,"center"),("Data",110,"center"),("Entrata",100,"center"),("Uscita",100,"center")]:
            right_tree.heading(col, text=col, anchor=anchor, command=lambda _col=col: treeview_sort_column(right_tree, _col, False))
            right_tree.column(col, width=w, anchor=anchor, stretch=True)
        right_tree.pack(fill=tk.BOTH, expand=True)
        right_diff_lbl = tk.Label(right, text="", font=("Arial", 10, "bold"))
        right_diff_lbl.pack(pady=(4,0))
    
        def treeview_sort_column(tv, col, reverse):
            # Prendi tutti gli elementi con i valori della colonna
            l = [(tv.set(k, col), k) for k in tv.get_children('')]

            # Prova a convertire in numeri se possibile
            try:
                l.sort(key=lambda t: float(t[0].replace(',', '').replace('€','')), reverse=reverse)
            except ValueError:
                l.sort(key=lambda t: t[0].lower(), reverse=reverse)

            # Riorganizza gli elementi
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            # Toggle ordine al prossimo click
            tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

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
            for cat, data, ent, usc in sorted(rows1, key=lambda x: x[0].lower()):
                left_tree.insert("", "end", values=(cat, data, f"{ent:.2f}", f"{usc:.2f}"))
                tot_ent1 += ent
                tot_usc1 += usc
            diff1 = tot_ent1 - tot_usc1
            left_diff_lbl.config(text=f"Totale entrate: {tot_ent1:.2f}   Totale uscite: {tot_usc1:.2f}   Differenza: {diff1:.2f} €", fg="blue" if diff1>=0 else "red")
            tot_ent2 = tot_usc2 = 0
            for cat, data, ent, usc in sorted(rows2, key=lambda x: x[0].lower()):
                right_tree.insert("", "end", values=(cat, data, f"{ent:.2f}", f"{usc:.2f}"))
                tot_ent2 += ent
                tot_usc2 += usc
            diff2 = tot_ent2 - tot_usc2
            right_diff_lbl.config(text=f"Totale entrate: {tot_ent2:.2f}   Totale uscite: {tot_usc2:.2f}   Differenza: {diff2:.2f} €", fg="blue" if diff2>=0 else "red")
    
        for var in [left_mese, left_anno, right_mese, right_anno, compare_by_year]:
            var.trace_add("write", lambda *a: update_tables())
        mostra_future_var.trace_add("write", lambda *a: update_tables())
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
            label2 = f"{m2:02d}/{str(a2)[-2:]}" if not per_anno else str(a2)
    
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
    
            prev.bind("<Escape>", lambda e: prev.destroy())
    
            t = tk.Text(prev, font=("Courier New", 10), wrap="none")
            t.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
            t.insert(tk.END, text)
            t.config(state="disabled")
    
            def do_save():
                now = datetime.date.today()
                default_filename = f"Confronto_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
                file = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("File txt", "*.txt")],
                    initialdir=EXPORT_FILES,
                    initialfile=default_filename,
                    title="Esporta confronto",
                    confirmoverwrite=False,
                    parent=prev)
                    
                if file:
                    if os.path.exists(file):
                        conferma = self.show_custom_askyesno(
                            "Sovrascrivere file?",
                            f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                        )
                        if not conferma:
                            return  # Annulla salvataggio

                    with open(file, "w", encoding="utf-8") as f:
                        f.write(text)
                    if hasattr(self, "show_custom_warning"):
                        self.show_custom_warning("Esportazione completata", f"Tabella confronti esportata in:\n{file}")
    
            frm = ttk.Frame(prev)
            frm.pack(fill=tk.X, padx=10, pady=8)
            tk.Button(frm, text="💾 Salva", command=do_save, width=15, bg="forestgreen", fg="black").pack(side=tk.LEFT, padx=6)
            tk.Button(frm, text="❌ Chiudi", command=prev.destroy, width=12, bg="gold", fg="black").pack(side=tk.RIGHT, padx=6)
    
            prev.lift()
            prev.focus_force()
            prev.attributes('-topmost', True)
            prev.after(100, lambda: prev.attributes('-topmost', False))
    
        btnframe = ttk.Frame(win)
        btnframe.pack(side=tk.BOTTOM, fill=tk.X, pady=(10,7))
        tk.Button(btnframe, text="📄 Preview/Esporta", command=do_preview_export, width=18, bg="orange", fg="black").pack(side=tk.LEFT, padx=8)
        tk.Button(btnframe, text="❌ Chiudi", command=win.destroy, width=14, bg="gold", fg="black").pack(side=tk.RIGHT, padx=8)

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
            #self.show_custom_warning("Attenzione", "Aggiornamento completato con successo \n\n 🚀 🔄 Riavviare il programma per applicare le modifiche !")
            # ✋ Chiede all’utente se chiudere
            if self.show_custom_askyesno(
                "Conferma chiusura",
                "✅ L'aggiornamento è stato eseguito correttamente!\n\n🔒 Vuoi chiudere il programma adesso?"
            ):
                self.save_db()
                self.destroy()
            return

        except Exception as e:
            print(f"Errore durante il download: {str(e)}")
            self.show_custom_warning("Attenzione", "❌ Aggiornamento NON completato ! \n\n Sembra ci sia stato un problema. 😕")
            return

    def show_info_app(self):
        
        def apri_email(event):
            webbrowser.open("mailto:helpcasafacilepro@gmail.com")

        def apri_link_python(event):
            webbrowser.open("https://www.python.org/downloads/")

        info_win = tk.Toplevel(self)
        info_win.title("Informazioni sulla applicazione")
        info_win.resizable(False, False)

        text = tk.Text(info_win, wrap="word", bg="white", font=("Courier New", 10))
        text.pack(fill="both", expand=True, padx=20, pady=10)

        text.insert("end", f"{NAME}\n", "titolo")
        text.insert("end", f"Versione v.{VERSION}\n", "versione")
        text.insert("end", "© 2025 Casa Facile Pro - Sviluppo Python/Tkinter, 2023-2025\n")
        text.insert("end", "Email: ")
        text.insert("end", "helpcasafacilepro@gmail.com\n", "email")

        text.insert("end", "\nFunzionalità principali:\n", "sezione")
        text.insert("end", "• Inserimento, modifica e cancellazione di spese ed entrate per categoria\n")
        text.insert("end", "• Gestione categorie personalizzate\n")
        text.insert("end", "• Gestione Ricorrenze (spese/entrate ripetute)\n")
        text.insert("end", "• Esportazione dettagliata giorno/mese/anno/utenze (Formato stampabile)\n")
        text.insert("end", "• Statistiche giornaliere, mensili, annuali e totali e analisi categorie, Bonus Time Machine\n")
        text.insert("end", "• Backup, import/export database, Rubrica personale , Gestione utenze, Cerca, ...\n")
        text.insert("end", "• Usa i pulsanti in alto per scegliere la modalità di visualizzazione delle statistiche (Giorno, Mese, Anno, Totali).\n")
        text.insert("end", "• Per esportare,visualizzare,stampare  le statistiche, usa 'Estrai'.\n")
        text.insert("end", "• Calendario interattivo con caselle colorate.\n")

        text.insert("end", "\nQuesto programma si basa su Python.")
        text.insert("end", "Scarica da: ")
        text.insert("end", "https://www.python.org/downloads/\n", "link")

        text.insert("end", "\nI plugin pip python sono autoinstallanti, ma per buona promemoria, ecco come installarli manualmente:\n", "sezione")

        text.insert("end", "\nSu Linux:\n")
        text.insert("end", "  Apri il terminale e digita:\n")
        text.insert("end", "  sudo apt install tkcalendar python3-psutil python3-requests\n")
        text.insert("end", "  Oppure:\n")
        text.insert("end", "  pip install tkcalendar psutil requests\n")

        text.insert("end", "\nSu Windows:\n")
        text.insert("end", "  Apri il Prompt dei comandi e digita:\n")
        text.insert("end", "  py -m pip install tkcalendar psutil requests win32print win32api win32con\n")
        text.insert("end", "  Assicurati di installare Python, psutil, tkcalendar, requests, win32print, win32api e win32con prima di avviare il programma.\n")

        text.tag_config("titolo", foreground="darkblue", font=("Courier New", 11, "bold"))
        text.tag_config("versione", foreground="blue", font=("Courier New", 10, "italic"))
        text.tag_config("sezione", foreground="darkgreen", font=("Courier New", 10, "bold"))
        text.tag_config("email", foreground="blue", underline=1)
        text.tag_bind("email", "<Button-1>", apri_email)
        text.tag_config("link", foreground="blue", underline=1)
        text.tag_bind("link", "<Button-1>", apri_link_python)

        text.config(state="disabled")

        btn_aggiorna = tk.Button(info_win, text="🔄 Aggiorna Software", command=lambda: self.aggiorna(GITHUB_FILE_URL, NOME_FILE), bg="orange", fg="black")
        btn_aggiorna.pack(side="left", padx=100, pady=10)

        btn_chiudi = tk.Button(info_win, text="❌ Chiudi", command=info_win.destroy, bg="gold", fg="black")
        btn_chiudi.pack(side="right", padx=100, pady=10)

        info_win.withdraw()
        info_win.update_idletasks()
        min_w, min_h = 1160, 620
        w = max(info_win.winfo_width(), min_w)
        h = max(info_win.winfo_height(), min_h)
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
        info_win.geometry(f"{w}x{h}+{x}+{y}")
        info_win.grab_set()
        info_win.transient(self)
        info_win.focus_set()
        info_win.deiconify()
        
        info_win.bind("<Escape>", lambda e: info_win.destroy())
        
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
        win.geometry("1366x700")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()


        # 🔹 Crea barra menu
        menu_win = tk.Menu(win)
        
        # 📂 Menu "Funzioni"
        menu_funzioni = tk.Menu(menu_win, tearoff=0)
        menu_funzioni.add_separator()
        menu_funzioni.add_command(label="📂 Esporta Preview", command=lambda: esporta_preview())
        menu_funzioni.add_command(label="⚙️ Analizza", command=lambda: crea_tabella_consumi(UTENZE_DB))
        menu_funzioni.add_command(label="📂 Esporta DB", command=lambda: esporta_letture_data(UTENZE_DB))
        menu_funzioni.add_command(label="📂 Importa DB", command=lambda: importa_letture_data(letture_salvate, anagrafiche))
        menu_funzioni.add_command(label="❌ Chiudi", command=win.destroy)
        menu_win.add_cascade(label="📂 File", menu=menu_funzioni)

        win.config(menu=menu_win)

        win.bind("<Escape>", lambda e: win.destroy())

        top_controls = ttk.Frame(win)
        top_controls.pack(pady=(0, 6))
        ttk.Label(top_controls, text="Gestione Consumi Utenze", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=(0, 25))
        ttk.Label(top_controls, text="Anno: ").pack(side=tk.LEFT)
        anno_var = tk.StringVar(value=anno_corrente)

        def salva_letture_preview(txt, preview_win):
            """Salva il contenuto della preview in un file, mantenendo l'allineamento a colonne distanziate."""
            now = datetime.date.today()
            default_filename = f"Letture_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            preview_win.wm_attributes('-topmost', 1)
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                title="Salva Preview",
                confirmoverwrite=False,
                parent=preview_win)
            preview_win.wm_attributes('-topmost', 0)
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio

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
            tk.Button(btn_frame, text="💾 Salva", command=lambda: salva_letture_preview(txt, preview_win), width=12, bg="forestgreen", fg="white").pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="❌ Chiudi", command=preview_win.destroy, width=10, bg="gold", fg="black").pack(side=tk.RIGHT, padx=10)

            preview_win.lift()
            preview_win.attributes('-topmost', True)
            preview_win.after(200, lambda: preview_win.attributes('-topmost', False))

            preview_win.bind("<Escape>", lambda e: preview_win.destroy())

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
        if self.modalita == "avanzata":
         ttk.Button(top_controls, text="📂 Esporta", style="Verde.TButton", command=esporta_preview).pack(side=tk.LEFT, padx=7)
         ttk.Button(top_controls, text="⚙️ Analizza", command=lambda: crea_tabella_consumi(UTENZE_DB)).pack(side=tk.LEFT, padx=7)
         #ttk.Button(top_controls, text="❌ Chiudi", style="Giallo.TButton", command=chiudi).pack(side=tk.LEFT, padx=7)
         ttk.Button(top_controls, text="📂 Esporta DB", style="Rosso.TButton", command=lambda: esporta_letture_data(UTENZE_DB)).pack(side=tk.LEFT, padx=7)
         ttk.Button(top_controls, text="📂 Importa DB", style="Rosso.TButton", command=lambda: importa_letture_data(letture_salvate, anagrafiche)).pack(side=tk.LEFT, padx=7)
        legenda = tk.Label(
                  top_controls,
                  text="🖱️ 2 Click sx: Mod.letture | Click dx: Mod.consumo",
                  font=("Arial", 9, "bold"),
                  fg="black"
        )
        legenda.pack(side=tk.LEFT, padx=15)
        ttk.Button(top_controls, text="❌ Chiudi", style="Giallo.TButton", command=chiudi).pack(side=tk.LEFT, padx=7)
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
                confirmoverwrite=False,
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
            
            win.bind("<Escape>", lambda e: win.destroy())
            
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
            tk.Button(frame_bottoni, text="💾 Salva", command=lambda: salva_dati_letture(letture_salvate), width=12, bg="forestgreen", fg="white").pack(side=tk.LEFT, padx=10)
            tk.Button(frame_bottoni, text="❌ Chiudi", command=win.destroy, width=10, bg="gold", fg="black").pack(side=tk.RIGHT, padx=10)

            frame_interno.update_idletasks()
            canvas.yview_moveto(0)
            win.mainloop()

        def salva_dati_letture(letture_salvate):
            """Esporta i dati dei consumi in formato testo, simile alla visualizzazione tabellare."""
            win.focus_force()
            now = datetime.date.today()
            default_filename = f"Letture_anno_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                confirmoverwrite=False,
                title="Salva i dati dei consumi"
               )

            if file_path:
                if os.path.exists(file_path):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file_path)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio

            if not file_path:
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

        def on_tree_double_click(event, utenza):
            tree = self.trees[utenza]
            item_id = tree.identify_row(event.y)
            if item_id:
                tree.selection_set(item_id)
                tree.focus(item_id)
                apri_modale(utenza)

        def on_tree_right_click(event, utenza):
            tree = self.trees[utenza]
            item_id = tree.identify_row(event.y)
            if not item_id:
                return
            tree.selection_set(item_id)  # Seleziona la riga
            tree.focus(item_id)
            apri_modale_solo_totale(utenza)
    
        def apri_modale_solo_totale(utenza):
            selected = self.trees[utenza].focus()
            if not selected:
                self.show_custom_warning("Errore", "Seleziona un mese dalla tabella")
                return

            item = self.trees[utenza].item(selected)
            mese, prec, att, consumo = item['values']

            try:
                consumo = float(consumo)
            except:
                consumo = 0.0
    
            modal = tk.Toplevel(win)
            modal.title(f"Consumo {utenza} - {mese}")
            modal.geometry("400x160")
            modal.resizable(False, False)
            modal.transient(win)
            centra_su_padre(modal, win)
            modal.after_idle(modal.grab_set)

            # 🔒 Validazione: massimo 8 cifre e solo numeri
            def only_numeric_8char(val):
                if len(val) > 8:
                    return False
                if val == "":
                    return True
                if val.count(".") > 1:
                    return False
                return all(c.isdigit() or c == "." for c in val)

            vcmd = modal.register(only_numeric_8char)

            tk.Label(modal, text=f"{utenza} - {mese}", font=("Arial", 12, "bold")).pack(pady=10)
            tk.Label(modal, text="Consumo:").pack()

            consumo_var = tk.DoubleVar(value=consumo)
            e_cons = tk.Entry(modal, textvariable=consumo_var, font=("Arial", 10), width=15,
                      validate="key", validatecommand=(vcmd, "%P"))
            e_cons.pack()
            e_cons.focus_set()
            modal.bind("<Return>", lambda event: salva()) ## premi  per confermare

            def salva():
                val = e_cons.get().strip()
                if not val:
                    self.show_custom_warning("Campo vuoto", "Inserisci il valore del consumo.")
                    return
                try:
                    cons = float(consumo_var.get())
                    if cons < 0:
                        self.show_custom_warning("Errore", "Consumo non può essere negativo.")
                        return
                    nuovo_att = float(prec) + cons
                    self.trees[utenza].item(selected, values=(mese, prec, nuovo_att, cons))
                    anno_sel = anno_var.get()
                    righe = [
                        tuple(self.trees[utenza].item(iid)['values'])
                        for iid in self.trees[utenza].get_children()
                    ]
                    letture_salvate[utenza][anno_sel] = righe
                    scrivi_db()
                    modal.destroy()
                except ValueError:
                    self.show_custom_warning("Errore", "Valore non valido.")

            btn_frame = tk.Frame(modal)
            btn_frame.pack(fill="x", pady=10, padx=10)

            btn_salva = tk.Button(btn_frame, text="💾 Salva", command=salva, width=12, bg="forestgreen", fg="white")
            btn_salva.pack(side=tk.LEFT, padx=(0,10))

            btn_chiudi = tk.Button(btn_frame, text="❌ Chiudi", command=modal.destroy, width=12, bg="gold", fg="black")
            btn_chiudi.pack(side=tk.RIGHT, padx=(10,0))
            modal.bind("<Escape>", lambda e: modal.destroy())

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
                try:
                    prec = float(prev_item['values'][2])
                except:
                    prec = 0.0

            # 🔨 Forza fallback per valori iniziali se non convertibili
            try:
                prec = float(prec)
            except:
                prec = 0.0

            try:
                att = float(att)
            except:
                att = 0.0

            modal = tk.Toplevel(win)
            modal.title(f"Modifica letture {utenza} - {mese}")
            modal.geometry("520x220")
            modal.resizable(False, False)
            modal.transient(win)
            centra_su_padre(modal, win)
            modal.after_idle(modal.grab_set)
            modal.bind("<Return>", lambda e: salva())

            # ✅ Funzione di validazione: solo numeri, max 8 caratteri
            def only_numeric_8char(val):
                if len(val) > 8:
                    return False
                if val == "":
                    return True
                if val.count(".") > 1:
                    return False
                return all(c.isdigit() or c == "." for c in val)

            vcmd = modal.register(only_numeric_8char)
    
            tk.Label(modal, text=f"{utenza} - {mese}", font=("Arial", 12, "bold")).pack(pady=10)

            tk.Label(modal, text="Lettura precedente:").pack()
            prec_var = tk.DoubleVar(value=prec)
            e_prec = tk.Entry(modal, textvariable=prec_var, font=("Arial", 10), width=22,
                      validate="key", validatecommand=(vcmd, "%P"))
            e_prec.pack()

            tk.Label(modal, text="Lettura attuale:").pack()
            att_var = tk.DoubleVar(value=att)
            e_att = tk.Entry(modal, textvariable=att_var, font=("Arial", 10), width=22,
                     validate="key", validatecommand=(vcmd, "%P"))
            e_att.pack()

            modal.e_prec = e_prec
            modal.e_att = e_att
            modal.prec_var = prec_var
            modal.att_var = att_var
            modal.mese = mese
            modal.utenza = utenza
            
            def salva():
                try:
                
                    if not e_prec.get().strip() or not e_att.get().strip():
                        self.show_custom_warning("Campo vuoto", "Compila entrambi i campi prima di salvare.")
                        return

                    p = float(prec_var.get())
                    a = float(att_var.get())
                    if a < p:
                        conferma = tk.Toplevel(modal)
                        conferma.title("Conferif att_var.get() == 0.0 and e_att.get().strip() == "":ma Forzatura")
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
                        tk.Button(btn_frame, text="Forza", command=ok, width=10, bg="orange", fg="white").pack(side=tk.LEFT, padx=12)
                        tk.Button(btn_frame, text="Annulla", command=annulla, width=10, bg="gold", fg="black").pack(side=tk.LEFT, padx=12)
                        return
                    consumo = round(a - p, 2)
                    self.trees[utenza].item(selected, values=(mese, p, a, consumo))
                    if idx + 1 < len(items):
                        next_item = self.trees[utenza].item(items[idx + 1])
                        next_mese, _, next_att, _ = next_item['values']
                        next_att_f = float(next_att)
                        
                        #next_cons = round(next_att_f - a, 2)
                        next_cons = max(0.0, next_att_f - a)
                        #self.show_custom_warning("Attenzione", "Attenzione: il mese successivo è stato aggiornato per evitare un consumo negativo !") 
                        self.trees[utenza].item(items[idx + 1], values=(next_mese, a, next_att_f, next_cons))
                    modal.destroy()
                    salva_letture_utenza(utenza)
                except ValueError:
                    self.show_custom_warning("Errore", "Valori non validi")

            tk.Button(modal, text="💾 Salva", width=9, command=salva, bg="forestgreen", fg="white").pack(side=tk.LEFT, padx=10)
            tk.Button(modal, text="📄 Chiudi", width=11, command=modal.destroy, bg="gold", fg="black").pack(side=tk.RIGHT, padx=10)
            modal.bind("<Escape>", lambda e: modal.destroy())
            
            
        for idx, utenza in enumerate(utenze):
            frame = tk.Frame(main_frame, bg=colori[utenza], bd=2, relief="groove")
            frame.grid(row=0, column=idx, padx=8, pady=6, sticky="nswe")

            top_btn_fr = tk.Frame(frame, bg=colori[utenza])
            top_btn_fr.pack(fill="x", padx=4, pady=(2,0))
            btn_mod_letture = tk.Button(
                top_btn_fr,
                text="📥 Modifica Letture",
                bg="red",
                fg="black",
                activebackground="#c00",
                font=("Arial", 11, "bold"),
                command=lambda u=utenza: apri_modale(u)
            )
            btn_mod_letture.pack(side=tk.LEFT, anchor="nw", padx=2, pady=2)
            btn_mod_totale = tk.Button(
                top_btn_fr,
                text="🟢 Modifica SOLO Consumo",
                bg="forestgreen",
                fg="black",
                activebackground="#080",
                font=("Arial", 11, "bold"),
                command=lambda u=utenza: apri_modale_solo_totale(u)
            )
            btn_mod_totale.pack(side=tk.LEFT, anchor="nw", padx=2, pady=2)

            tk.Label(frame, text=utenza, font=("Arial", 10, "bold"), bg=colori[utenza]).pack(pady=(2,2))

            tree = ttk.Treeview(frame, columns=("Mese", "Prec", "Att", "Consumo"), show="headings", height=12)
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
            tree.bind("<Double-1>", lambda event, utenza=utenza: on_tree_double_click(event, utenza))
            tree.bind("<Button-3>", lambda event, utenza=utenza: on_tree_right_click(event, utenza))
            def salva_letture_local(u=utenza):
                salva_letture_utenza(u)
                self.show_custom_warning("Attenzione", f"Dati {u} Salvati Corretamente !")
                
            tk.Button(
                frame,
                text="💾 Salva Letture",
                width=16,
                command=salva_letture_local,
                bg="forestgreen",
                fg="black"
            ).pack(pady=(0, 6))

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

            tk.Button(btns, text="💾 Salva", width=9, command=salva_dati, bg="forestgreen", fg="black").pack(side=tk.LEFT, padx=2)
            tk.Button(btns, text="📄 Modifica", width=11, command=modifica_dati, bg="gold", fg="black").pack(side=tk.LEFT, padx=2)

    def cerca_operazioni(self):
        larghezza, altezza = 900, 600
        x = self.winfo_screenwidth() // 2 - larghezza // 2
        y = self.winfo_screenheight() // 2 - altezza // 2

        finestra = tk.Toplevel()
        finestra.title("Ricerca operazioni")
        finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")
        finestra.transient(self)
        finestra.grab_set()
        finestra.bind("<Escape>", lambda e: finestra.destroy())

        # 🔍 Barra superiore
        frame_superiore = tk.Frame(finestra)
        frame_superiore.pack(fill="x", pady=10, padx=10)

        tk.Label(frame_superiore, text="🔎 Ricerca generale:").pack(side="left")
        campo_input = tk.Entry(frame_superiore, width=30)
        campo_input.pack(side="left", padx=8)
        campo_input.focus_set()

        mostra_futuro_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_superiore, text="Includi futuri", variable=mostra_futuro_var).pack(side="left", padx=10)

        def resetta_campo():
            campo_input.delete(0, tk.END)
            area_testo.delete("1.0", tk.END)  # ✅ Ripulisce l'area risultati
            self.filtri_avanzati = {}  # ✅ Cancella tutti i filtri

        tk.Button(frame_superiore, text="↺", command=resetta_campo, width=2, bg="yellow", activebackground="gold").pack(side="left", padx=5)

        def apri_filtri_avanzati():
            filtro_win = tk.Toplevel(finestra)
            filtro_win.title("⚙️ Filtri avanzati")
            filtro_win.geometry("400x250")
            filtro_win.transient(finestra)
            filtro_win.grab_set()

            # Variabili
            categoria_var = tk.StringVar(value="—")
            tipo_var = tk.StringVar(value="—")
            anno_var = tk.StringVar(value="—")
            mese_var = tk.StringVar(value="—")
            da_var = tk.StringVar()
            a_var = tk.StringVar()

            def crea_riga(testo, var, values=None):
                f = tk.Frame(filtro_win); f.pack(fill="x", padx=12, pady=5)
                tk.Label(f, text=testo, width=14, anchor="w").pack(side="left")
                if values:
                    ttk.Combobox(f, textvariable=var, values=values, state="readonly", width=22).pack(side="left")
                else:
                    tk.Entry(f, textvariable=var, width=24).pack(side="left")

            tutte_cat = sorted(set(v[0].strip().title() for sp in self.spese.values() for v in sp if len(v) >= 1))
            anni = sorted(set(str(d.year if isinstance(d, datetime.date)else datetime.datetime.strptime(d, "%d-%m-%Y").year) for d in self.spese), reverse=True)
            mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                         "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
           
            crea_riga("Categoria:", categoria_var, ["—"] + tutte_cat)
            crea_riga("Tipo voce:", tipo_var, ["—", "Entrata", "Uscita"])
            crea_riga("Anno:", anno_var, ["—"] + anni)
            crea_riga("Mese:", mese_var, ["—"] + mesi_nomi)
            crea_riga("Importo da:", da_var)
            crea_riga("Importo a:", a_var)

            def applica():
                self.filtri_avanzati = {
                    "categoria": categoria_var.get(),
                    "tipo": tipo_var.get(),
                    "anno": anno_var.get(),
                    "mese": mese_var.get(),
                    "da": da_var.get(),
                    "a": a_var.get()
                }

                filtro_win.destroy()
                esegui_ricerca()  # 🔄 Aggiorna i risultati dopo aver applicato i filtri

            def cancella():
                self.filtri_avanzati = {}
                for var in [categoria_var, tipo_var, anno_var, mese_var, da_var, a_var]:
                    var.set("—" if var != da_var and var != a_var else "")
                filtro_win.destroy()

            f_btn = tk.Frame(filtro_win); f_btn.pack(pady=10)
            tk.Button(f_btn, text="✅ Applica", command=applica, bg="green", fg="black").pack(side="left", padx=10)
            tk.Button(f_btn, text="🎛 Cancella filtri", command=cancella, bg="red", fg="black").pack(side="right", padx=10)

        # 📋 Area risultati
        frame_risultati = tk.Frame(finestra)
        frame_risultati.pack(fill="both", expand=True, padx=10)

        area_testo = tk.Text(frame_risultati, wrap="word")
        area_testo.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(frame_risultati, command=area_testo.yview)
        scroll.pack(side="right", fill="y")
        area_testo.config(yscrollcommand=scroll.set)

        # 🔍 Ricerca
        def esegui_ricerca(event=None):
            parola = campo_input.get().strip().lower()
            area_testo.delete("1.0", tk.END)
            parola = campo_input.get().strip().lower()
            area_testo.delete("1.0", tk.END)

            risultati = []
            oggi = datetime.date.today()
            mostra_futuro = mostra_futuro_var.get()
            filtri = getattr(self, "filtri_avanzati", {})


            risultati = []
            oggi = datetime.date.today()
            mostra_futuro = mostra_futuro_var.get()
            filtri = getattr(self, "filtri_avanzati", {})

            for data_key in sorted(self.spese.keys(), reverse=True):
                d = data_key if isinstance(data_key, datetime.date) else datetime.datetime.strptime(data_key, "%d-%m-%Y").date()
                if not mostra_futuro and d > oggi:
                    continue

                for voce in self.spese[data_key]:
                    categoria = str(voce[0]).lower()
                    descrizione = str(voce[1]).lower()
                    importo = str(voce[2])
                    tipo = str(voce[3]).lower()

                    # ✅ Inserisci il filtro mese qui
                    mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
                    mesi_map = {m: i+1 for i, m in enumerate(mesi_nomi)}
                    mese_selezionato = filtri.get("mese", "").strip().capitalize()

                    if mese_selezionato and mese_selezionato != "—":
                        if d.month != mesi_map.get(mese_selezionato, 0):
                            continue

                    if not any(parola in campo for campo in [categoria, descrizione, tipo, importo]):
                        continue

                    # 🎛 Filtri applicati
                    if filtri:
                        if filtri.get("categoria") not in ["", "—"] and categoria != filtri["categoria"].lower():
                            continue
                        if filtri.get("tipo") not in ["", "—"] and tipo != filtri["tipo"].lower():
                            continue
                        if filtri.get("anno") not in ["", "—"] and str(d.year) != filtri["anno"]:
                            continue
                        if filtri.get("mese") not in ["", "—"]:
                            mesi_map = {m: i+1 for i, m in enumerate(mesi_nomi)}
                            if d.month != mesi_map.get(filtri["mese"], 0):
                                continue
                        try:
                            da = float(filtri.get("da", "0") or "0")
                            a = float(filtri.get("a", "999999999") or "999999999")
                            if not (da <= float(importo) <= a):
                                continue
                        except: pass

                    emoji = "[↑]" if tipo == "entrata" else "[↓]" if tipo == "uscita" else "[=]"
                    riga = (
                        f"\n📅 {d.strftime('%d/%m/%Y')} {emoji}\n"
                        f"{'':3}Categoria   : {voce[0]}\n"
                        f"{'':3}Descrizione : {voce[1]}\n"
                        f"{'':3}Tipo        : {tipo:<10}    Importo: {float(importo):>10,.2f} €\n"
                        f"{'═'*80}\n"
                    )
                    risultati.append(riga)
                    
            area_testo.tag_config("entrata", foreground="green")
            area_testo.tag_config("uscita", foreground="red")
            area_testo.tag_config("neutro", foreground="gray")
            
            tot_entrate = 0.0
            tot_uscite = 0.0

            for riga in risultati:
                if "[↑]" in riga:
                    tot_entrate += estrai_importo(riga)
                elif "[↓]" in riga:
                    tot_uscite += estrai_importo(riga)

            # 🎯 Riepilogo dei filtri applicati
            descrizione_filtri = []

            if filtri.get("categoria", "") not in ["", "—"]:
                descrizione_filtri.append(f"Categoria: {filtri['categoria']}")
            if filtri.get("tipo", "") not in ["", "—"]:
                descrizione_filtri.append(f"Tipo: {filtri['tipo']}")
            if filtri.get("anno", "") not in ["", "—"]:
                descrizione_filtri.append(f"Anno: {filtri['anno']}")
            if filtri.get("mese", "") not in ["", "—"]:
                descrizione_filtri.append(f"Mese: {filtri['mese']}")
            if filtri.get("da") or filtri.get("a"):
                da = filtri.get("da", "")
                a = filtri.get("a", "")
                descrizione_filtri.append(f"Importo: {da} → {a} €")

            # 🔎 Genera testo riepilogativo
            testo_filtri = ", ".join(descrizione_filtri) if descrizione_filtri else "Nessun filtro"

            netto = tot_entrate - tot_uscite
            testata = (
            f"\n📊 Operazioni trovate: {len(risultati)}\n"
                f"🔎 Filtri attivi    : {testo_filtri}\n"
                f"✅ Totale entrate : {tot_entrate:,.2f} €\n"
                f"❌ Totale uscite  : {tot_uscite:,.2f} €\n"
                f"🧮 Saldo netto    : {netto:,.2f} €\n"
                f"{'═'*80}\n"
            )

            area_testo.tag_config("testata", foreground="blue")
            area_testo.insert("end", testata, "testata")
            if risultati:
                for riga in risultati:
                    if "[↑]" in riga:
                        tag = "entrata"
                    elif "[↓]" in riga:
                        tag = "uscita"
                    else:
                        tag = "neutro"
                    area_testo.insert("end", riga, tag)
            else:
                area_testo.insert("end", f"🔍 Nessuna corrispondenza per: '{parola}'", "neutro")



        campo_input.bind("<Return>", esegui_ricerca)

        def estrai_importo(riga):
            import re
            try:
                match = re.search(r"Importo:\s+([\d.,]+)\s?€", riga)
                if not match:
                    return 0.0
                valore_str = match.group(1).strip()

                # 🔍 Se contiene virgola, assumiamo formato italiano: 1.234,56
                if "," in valore_str:
                    valore_str = valore_str.replace(".", "").replace(",", ".")
                # ✅ Altrimenti lasciamo com'è (es. 110.00)

                return float(valore_str)
            except:
                return 0.0

        def esporta_risultato():
            contenuto = area_testo.get("1.0", tk.END).strip()
            if not contenuto:
                self.show_custom_warning("Esportazione", "⚠️ Nessun contenuto da salvare.")
                return
            nome_file = f"Risultati_Ricerca_{datetime.date.today():%d_%m_%Y}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=nome_file,
                title="Salva risultati ricerca",
                confirmoverwrite=False,
                parent=finestra
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio

                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto)
                    self.show_custom_warning("Esportazione completata", f"✅ Risultati salvati:\n{file}")
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
        frame_bottoni = tk.Frame(finestra)
        frame_bottoni.pack(pady=12)

        for txt, cmd, bg, fg in [
            ("🔍 Cerca", esegui_ricerca, "forestgreen", "black"),
            ("📄 Esporta", esporta_risultato, "orange", "black"),
            ("⚙️ Filtri avanzati", apri_filtri_avanzati, "forestgreen", "black"),
            ("↺ Reset campo", resetta_campo, "gold", "black"),
            ("❌ Chiudi", finestra.destroy, "red", "black")
        ]:
            tk.Button(
                frame_bottoni,
                text=txt,
                command=cmd,
                bg=bg,
                fg=fg,
                font=("Arial", 9, "bold"),
                padx=14,
                relief="raised",
                cursor="hand2"
            ).pack(side="left", padx=6)


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
            default_filename = f"Rubrica_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                title="Salva Rubrica",
                confirmoverwrite=False,
                parent=root)
 
            if path:
                if os.path.exists(path):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(path)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio
                        
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
                confirmoverwrite=False,
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
        root.bind("<Escape>", lambda e: root.destroy())  
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

        try:
            cal._header["font"] = ("Arial", 14, "bold")
        except:
            pass  
            
        def seleziona_data(event=None):
            var_data.set(cal.get_date())
            chiudi_popup_calendario()

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
        self.popup_calendario.bind("<Escape>", lambda e: chiudi_popup_calendario())

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
    
        w, h = 800, 600
        x = (popup.winfo_screenwidth() // 2) - (w // 2)
        y = (popup.winfo_screenheight() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.resizable(False, False)
    
        main_frame = ttk.Frame(popup, padding=10)
        main_frame.pack(fill="both", expand=True)
    
        bottom_buttons = ttk.Frame(popup)
        bottom_buttons.pack(fill="x", pady=10)
    
        today = datetime.date.today()
        mesi = ["Tutti"] + ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        mese_var = tk.StringVar(value="Tutti")
        anno_var = tk.StringVar(value=str(today.year))
    
        mostra_future_var = tk.BooleanVar(value=True)
    
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
    
        tk.Checkbutton(
            top_bar,
            text="Includi movimenti futuri nei totali",
            bg="yellow",
            activebackground="gold",  # colore al passaggio del mouse
            variable=mostra_future_var
        ).pack(side="left", padx=(20,0))
    
        tk.Button(
            top_bar,
            text="↺",
            bg="gold",
            fg="black",
            width=2,
            command=lambda: [
                mese_var.set("Tutti"),
                anno_var.set(str(today.year))
            ]
        ).pack(side="left", padx=(10, 0))
    
        categorie = set()
        for d, sp in self.spese.items():
            if isinstance(d, str):
                d = datetime.datetime.strptime(d, "%d-%m-%Y").date()
            for voce in sp:
                if len(voce) >= 4 and voce[3] == "Uscita":
                    categorie.add(voce[0].strip().title())
        valori_combo = ["— Nessuna —"] + sorted(categorie)
    
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
            oggi = datetime.date.today()
    
            for d, sp in self.spese.items():
                if isinstance(d, str):
                    d = datetime.datetime.strptime(d, "%d-%m-%Y").date()
                # filtro spese future
                if not mostra_future_var.get() and d > oggi:
                    continue
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

        def reset_campi():
            mese_var.set("Tutti")
            anno_var.set(str(today.year))
            mostra_future_var.set(True)
            for var in combo_vars:
                var.set("— Nessuna —")
            text_output.delete("1.0", "end")
    
        def salva():
            contenuto = text_output.get("1.0", "end").strip()
            if not contenuto:
                self.show_custom_warning("Nessun dato", "Nessun risultato da salvare.")
                return
            now = datetime.date.today()
            nome_file = f"Analisi_Categorie_{now:%d_%m_%Y}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialfile=nome_file,
                initialdir=EXPORT_FILES,
                title="Esporta risultati",
                confirmoverwrite=False,
                parent=popup
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio

                with open(file, "w", encoding="utf-8") as f:
                    f.write(contenuto)
                self.show_custom_warning("Esportazione completata", f"File salvato:\n{file}")
    
        # Rende l'analisi reattiva quando cambi la checkbox
        mostra_future_var.trace_add("write", lambda *a: analizza())
    
        tk.Button(bottom_buttons, text="📥 Analizza", command=analizza, fg="black", bg="#32CD32").pack(side="left", padx=10)
        tk.Button(bottom_buttons, text="💾 Esporta", command=salva, fg="black", bg="orange").pack(side="left", padx=10)
        tk.Button(bottom_buttons, text="🟨 Reset campi", command=reset_campi, fg="black", bg="red").pack(side="left", padx=10)
        tk.Button(bottom_buttons, text="🟨 Chiudi", command=popup.destroy, fg="black", bg="gold").pack(side="right", padx=10)
        popup.bind("<Escape>", lambda e: popup.destroy())


    def calcola_mancanti(self):
        from datetime import datetime, timedelta
        popup = tk.Toplevel()
        popup.withdraw()
        popup.title("📋 Controllo Categorie Ricorrenti")
        w, h = 580, 580
        x = (popup.winfo_screenwidth() // 2) - (w // 2)
        y = (popup.winfo_screenheight() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.resizable(False, False)
        popup.deiconify()

        mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        oggi = datetime.today().date()
        limite = oggi - timedelta(days=365) 
        def converti_data(d):
            if isinstance(d, str):
                try:
                    return datetime.strptime(d, "%d-%m-%Y").date()
                except:
                    return None
            elif isinstance(d, datetime):
                return d.date()
            return d

        anni_disponibili = sorted({
            converti_data(d).year for d in self.spese
            if converti_data(d)
        }, reverse=True)

        anno_var = tk.StringVar(value=str(oggi.year))

        top_bar = ttk.Frame(popup, padding=10)
        top_bar.pack(fill="x")
        ttk.Label(top_bar, text="Anno:").pack(side="left", padx=6)
        anno_combo = ttk.Combobox(top_bar, textvariable=anno_var,
                              values=[str(a) for a in anni_disponibili], state="readonly", width=6)
        anno_combo.pack(side="left", padx=6)

        text_output = tk.Text(popup, height=22, wrap="word", bg="#fffbe6", font=("Courier New", 10))
        text_output.pack(fill="both", expand=True, padx=10, pady=8)
        text_output.configure(state="disabled")  # 🔒 blocca modifica

        def analizza():
            text_output.configure(state="normal")
            text_output.delete("1.0", "end")
            try:
                anno = int(anno_var.get())
            except:
                self.show_custom_warning("Errore", "Anno non valido.")
                return

            risultati = {}
            importi_categoria = {}
            conteggio_categoria = {}

            for d, sp in self.spese.items():
                dd = converti_data(d)
                
                #if not dd or dd < limite: # Se invece volessi analizzare gli ultimi 365 giorni
                   #continue
 
                if not dd or dd.year != anno:
                    continue
                          
                for voce in sp:
                    if len(voce) < 1 or not voce[0].strip():
                        continue
                    cat = voce[0].strip().title()
                    importo = 0
                    if len(voce) > 2 and isinstance(voce[2], (int, float)):
                        importo = voce[2]
                    if cat not in importi_categoria:
                        importi_categoria[cat] = 0
                        conteggio_categoria[cat] = 0
                    importi_categoria[cat] += importo
                    conteggio_categoria[cat] += 1
                    if cat not in risultati:
                        risultati[cat] = set()
                    risultati[cat].add(dd.month)

            text_output.tag_config("intestazione", foreground="black", font=("Courier New", 13, "bold"))
            text_output.tag_config("categoria", foreground="purple", font=("Courier New", 10, "bold"))
            text_output.tag_config("simbolo_presente", foreground="orange", font=("Courier New", 10, "bold"))
            text_output.tag_config("simbolo_assente", foreground="red", font=("Courier New", 10, "bold"))

            text_output.insert("end", f"📅 Analisi categorie ricorrenti – Anno {anno}\n", "intestazione")
            count = 0       
           
            for cat, mesi_presenti in sorted(risultati.items()):
                # Considera solo le categorie che appaiono in almeno 2 mesi all'interno dell'anno
                # per classificarle come potenzialmente "ricorrenti" per questo report.
                spesa_totale = importi_categoria.get(cat, 0)
                n_elementi = conteggio_categoria.get(cat, 1)
                media_spesa = spesa_totale / n_elementi

                if len(mesi_presenti) < 2:
                    continue

                found_recurring_categories = True

                # Calcola l'intervallo medio tra i mesi presenti per una stima più accurata della cadenza
                sorted_months = sorted(list(mesi_presenti))
                avg_interval = 0
                if len(sorted_months) > 1:
                    intervals = [sorted_months[i] - sorted_months[i-1] for i in range(1, len(sorted_months))]
                    avg_interval = sum(intervals) / len(intervals)

                # Determina la cadenza (frequenza)
                if len(mesi_presenti) == 12:
                    cadenza = "mensile (tutti i mesi)" # Strict monthly (all 12 months)
                elif len(mesi_presenti) >= 6 and 0.8 <= avg_interval <= 1.2: # Almeno 6 mesi con intervallo ~1
                    cadenza = "mensile (regolare)"
                elif len(mesi_presenti) >= 2 and 1.5 <= avg_interval <= 2.5:
                    cadenza = "bimestrale" # Approximately every 2 months
                elif len(mesi_presenti) >= 2 and 2.5 < avg_interval <= 3.5:
                    cadenza = "trimestrale" # Approximately every 3 months
                else:
                    cadenza = "irregolare" # Other cases

                text_output.insert("end", f"\n🔸 {cat} – media: €{media_spesa:.2f}\n", "categoria")
                text_output.configure(font=("Courier New", 10))
                # 📆 Linea mesi
                text_output.insert("end", "   📆 ")
                for i, nome in enumerate(mesi):
                    nome_breve = nome[:3].ljust(5)
                    if (i + 1) == oggi.month:
                        text_output.insert("end", nome_breve, "mese_evidenziato")
                    else:
                        text_output.insert("end", nome_breve)
                text_output.insert("end", "\n")
                # ✅❌ Linea simboli
                text_output.insert("end", "     ")
                for i in range(12):
                    simbolo = "✅" if (i + 1) in mesi_presenti else "❌"
                    tag_simbolo = "simbolo_presente" if simbolo == "✅" else "simbolo_assente"
                    text_output.insert("end", simbolo.center(5), tag_simbolo)
                text_output.insert("end", "\n")
                # 🔁 Cadenza stimata
                text_output.insert("end", f"   🔁 cadenza stimata: {cadenza}\n")
                text_output.insert("end", "━" * 68 + "\n", "linea_bold")  # U+2501 ━                
                count += 1
            if count == 0:
                righe.append("🚫 Nessuna categoria ricorrente trovata.")
            text_output.tag_config("mese_evidenziato", foreground="blue", font=("Courier New", 10, "bold"))
            text_output.configure(state="disabled")
            
        anno_combo.bind("<<ComboboxSelected>>", lambda e: analizza())

        bottom_buttons = ttk.Frame(popup)
        bottom_buttons.pack(pady=8)
        tk.Button(bottom_buttons, text="💾 Esporta", command=lambda: salva(), bg="orange", fg="black").pack(side="left", padx=10)
        tk.Button(bottom_buttons, text="🟨 Chiudi", command=popup.destroy, bg="gold", fg="black").pack(side="right", padx=10)
        popup.bind("<Escape>", lambda e: popup.destroy())

        def salva():
            contenuto = text_output.get("1.0", "end").strip()
            if not contenuto:
                self.show_custom_warning("Nessun dato", "Nessun risultato da salvare.")
                return
            now = datetime.today()
            nome_file = f"Mancanze_Categorie_{now:%d_%m_%Y}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialfile=nome_file,
                initialdir=EXPORT_FILES,
                title="Esporta risultati",
                confirmoverwrite=False,
                parent=popup
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno("Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?")
                    if not conferma:
                        return
                with open(file, "w", encoding="utf-8") as f:
                    f.write(contenuto)
                self.show_custom_warning("Esportazione completata", f"File salvato:\n{file}")
        analizza()  # Mostra subito i dati correnti all'apertura

    def time_machine(self):
        popup = tk.Toplevel()
        popup.withdraw()
        popup.title("🕰️ Time Machine – Simulazione per categoria")
        w, h = 780, 620
        x = (popup.winfo_screenwidth() // 2) - (w // 2)
        y = (popup.winfo_screenheight() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.resizable(False, False)
        popup.deiconify()
    
        main = ttk.Frame(popup, padding=10)
        main.pack(fill="both", expand=True)
    
        anni_disponibili = sorted({datetime.datetime.strptime(str(d), "%d-%m-%Y").year
                                   if isinstance(d, str) else d.year for d in self.spese}, reverse=True)
        anno_var = tk.IntVar(value=datetime.date.today().year)

        mostra_future_var = tk.BooleanVar(value=True)
        top_bar = ttk.Frame(main)
        top_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(top_bar, text="Anno:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        anno_combo = ttk.Combobox(top_bar, textvariable=anno_var, values=anni_disponibili, state="readonly", width=8)
        anno_combo.pack(side="left")
    
        tk.Checkbutton(
            top_bar,
            text="Includi movimenti futuri nei totali",
            bg="yellow",
            activebackground="gold", 
            variable=mostra_future_var
        ).pack(side="left", padx=(30,0))
    
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
        text_output = tk.Text(main, height=8, wrap="word")
        text_output.pack(fill="both", expand=False, padx=5, pady=(0, 10))
        text_output.configure(font=("Courier New", 10))
    
        # Funzioni di supporto
        def aggiorna_categorie():
            anno = anno_var.get()
            contatori = {}
            oggi = datetime.date.today()
            for d, sp in self.spese.items():
                try:
                    if isinstance(d, str):
                        d_conv = datetime.datetime.strptime(d, "%d-%m-%Y").date()
                    else:
                        d_conv = d
                except:
                    continue
                # filtro spese future
                if not mostra_future_var.get() and d_conv > oggi:
                    continue
                if d_conv.year != anno:
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
    
        def aggiorna_interfaccia(*_):
            contatori = aggiorna_categorie()
            tutte_categorie = sorted(contatori.keys())
            valori_combo = ["— Nessuna —"] + tutte_categorie
    
            for var, cb in zip(combo_vars, combo_widgets):
                cb["values"] = valori_combo
                if var.get().strip().title() not in tutte_categorie:
                    var.set("— Nessuna —")
    
            for w in destra.winfo_children():
                if w != destra_label:
                    w.destroy()
    
            top_cat = sorted(contatori.items(), key=lambda x: -x[1]["totale"])[:10]
            selezioni.clear()
            for cat, dati in top_cat:
                var = tk.BooleanVar(value=False)
                selezioni[cat] = (var, dati)
                txt = f"{cat} – {dati['count']}×, {dati['totale']:.2f} €"
                chk = tk.Checkbutton(destra, text=txt, variable=var)
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

        def reset_tutto():
            anno_var.set(datetime.date.today().year)
            mostra_future_var.set(True)
            for var in combo_vars:
                var.set("— Nessuna —")
            for var, _ in selezioni.values():
                var.set(False)
            text_output.delete("1.0", tk.END)
            aggiorna_interfaccia()

        def salva_file():
            content = text_output.get("1.0", "end").strip()
            if not content:
                self.show_custom_warning("Nessun dato", "Non c'è nessuna simulazione da salvare.")
                return
            now = datetime.date.today()
            default_filename = f"Time_Machine_{now.day:02d}_{now.month:02d}_{now.year}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                title="Esporta risultato simulazione",
                confirmoverwrite=False,
                parent=popup)
 
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio
                        
                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.show_custom_warning("Esportazione completata", f"Simulazione salvata in:\n{file}")
    
        anno_combo.bind("<<ComboboxSelected>>", lambda e: aggiorna_interfaccia())
        mostra_future_var.trace_add("write", lambda *a: aggiorna_interfaccia())
        aggiorna_interfaccia()
        pulsanti = ttk.Frame(main)
        pulsanti.pack(pady=5)
        tk.Button(pulsanti, text="🟥 Simula Risparmio", command=esegui_simulazione, fg="black", bg="red", activebackground="#aa0000").pack(side="left", padx=10)
        tk.Button(pulsanti, text="💾 Esporta", command=salva_file, fg="black", bg="cadetblue", activebackground="steelblue").pack(side="left", padx=10)
        tk.Button(pulsanti, text="🔄 Reset campi", command=reset_tutto, bg="red", fg="black", activebackground="orange").pack(side="left", padx=10)
        tk.Button(pulsanti, text="🟨 Chiudi", command=popup.destroy, fg="black", bg="gold", activebackground="orange").pack(side="left", padx=10)
        btn_reset.pack(pady=(4, 8))
        popup.bind("<Escape>", lambda e: popup.destroy())

    def on_spese_mese_tree_double_click(self, event):
        item_id = self.spese_mese_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.spese_mese_tree.item(item_id, "values")
        if not values:
            return
        data_str = str(values[0]).strip()
        try:
            giorno = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except Exception:
            try:
                giorno = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            except Exception:
                return
        self.set_stats_mode("giorno")
        if hasattr(self, "cal"):
            self.cal.selection_set(giorno)
            self.cal._sel_date = giorno
        self.update_stats()

    def on_stats_table_double_click(self, event):
        mode = self.stats_mode.get()
        if mode not in ("mese", "anno", "totali"):
            return
        item_id = self.stats_table.identify_row(event.y)
        if not item_id:
            return
        values = self.stats_table.item(item_id, "values")
        if not values or len(values) < 1:
            return

        categoria = str(values[0]).strip()
        spese_categoria = []

        # Recupera la lista delle spese in base alla modalità
        if mode == "mese":
            ref = self.stats_refdate
            mese, anno = ref.month, ref.year
            for d, sp in self.spese.items():
                if d.month == mese and d.year == anno:
                    for entry in sp:
                        cat, desc, imp, tipo = entry[:4]
                        if cat == categoria:
                            spese_categoria.append((d, desc, imp, tipo))
            titolo_periodo = f"{mese:02d}-{anno}"
            testo_periodo = f"il mese {mese:02d}-{anno}"
        elif mode == "anno":
            ref = self.stats_refdate
            anno = ref.year
            for d, sp in self.spese.items():
                if d.year == anno:
                    for entry in sp:
                        cat, desc, imp, tipo = entry[:4]
                        if cat == categoria:
                            spese_categoria.append((d, desc, imp, tipo))
            titolo_periodo = f"{anno}"
            testo_periodo = f"l'anno {anno}"
        elif mode == "totali":
            for d, sp in self.spese.items():
                for entry in sp:
                    cat, desc, imp, tipo = entry[:4]
                    if cat == categoria:
                        spese_categoria.append((d, desc, imp, tipo))
            titolo_periodo = "Tutte le annualità"
            testo_periodo = "tutti gli anni"

        if not spese_categoria:
            self.show_custom_info("Nessuna spesa", f"Nessuna spesa per la categoria '{categoria}' nel periodo selezionato.")
            return

        popup = tk.Toplevel(self)
        popup.title(f"Dettaglio spese - {categoria} ({titolo_periodo})")
        popup.geometry("650x360")
        popup.transient(self)
        popup.update()  # Per evitare errori con grab_set
        popup.grab_set()  # Rende modale

        label = tk.Label(
            popup,
            text=f"Spese categoria '{categoria}' per {testo_periodo}",
            font=("Arial", 11, "bold")
        )
        label.pack(pady=8)

        columns = ("Data", "Descrizione", "Importo", "Tipo")
        tree = ttk.Treeview(popup, columns=columns, show="headings", height=10)
        tree.pack(fill="both", expand=True, padx=10, pady=6)

        # 👉 Ordinamento al clic
        def ordina_colonna(treeview, colonna, inverti):
            dati = [(treeview.set(k, colonna), k) for k in treeview.get_children("")]

            try:
                if colonna == "Data":
                    dati.sort(
                        key=lambda t: datetime.datetime.strptime(t[0], "%d-%m-%Y"),
                        reverse=inverti
                    )
                elif colonna == "Importo":
                    dati.sort(
                        key=lambda t: float(t[0].replace(",", ".").replace("€", "")),
                        reverse=inverti
                    )
                else:
                    dati.sort(key=lambda t: t[0].lower(), reverse=inverti)
            except Exception as e:
                print("Errore ordinamento:", e)

            for index, (_, k) in enumerate(dati):
                treeview.move(k, "", index)

            treeview.heading(colonna, command=lambda: ordina_colonna(treeview, colonna, not inverti))

        # 🔠 Imposta intestazioni e larghezze
        for col, w in zip(columns, (90, 230, 100, 80)):
            anchor = "w" if col == "Descrizione" else "center"
            tree.heading(col, text=col, command=lambda c=col: ordina_colonna(tree, c, False))
            tree.column(col, width=w, anchor=anchor)


        tot_entrate = tot_uscite = 0.0
        for d, desc, imp, tipo in sorted(spese_categoria, key=lambda x: x[0]):
            tree.insert("", "end", values=(d.strftime("%d-%m-%Y"), desc, f"{imp:.2f}", tipo))
            if tipo == "Entrata":
                tot_entrate += imp
            else:
                tot_uscite += imp
        saldo = tot_entrate - tot_uscite
        lbl = tk.Label(
            popup,
            text=f"Totale entrate: {tot_entrate:.2f}   Totale uscite: {tot_uscite:.2f}   Saldo: {saldo:.2f} €",
            fg="blue" if saldo >= 0 else "red",
            font=("Arial", 10, "bold")
        )
        lbl.pack(pady=7)

        # Binding: doppio click su riga del dettaglio → passa a quel giorno nella vista principale
        tree.bind("<Double-1>", lambda evt: self.goto_day_from_popup(tree, popup))

        tk.Button(popup, text="Chiudi", command=popup.destroy, bg="gold").pack(pady=4)

    def goto_day_from_popup(self, tree, popup):
        item_id = tree.focus()
        if not item_id:
            return
        vals = tree.item(item_id, "values")
        if not vals or len(vals) < 1:
            return
        data_str = vals[0]
        try:
            giorno = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except Exception:
            return
        # Imposta calendario e modalità giorno
        self.set_stats_mode("giorno")
        if hasattr(self, "cal"):
            self.cal.selection_set(giorno)
            self.cal._sel_date = giorno
        self.update_stats()
        try:
            popup.destroy()
        except Exception:
            pass

    def on_blocca_data_changed(self):
        if not self.blocca_data_var.get():
            # Se la checkbox viene DISATTIVATA, aggiorna la data a oggi
            self.data_spesa_var.set(datetime.date.today().strftime("%d-%m-%Y"))
    
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
        args = sys.argv

        def mostra_finestra_login():
            login = tk.Toplevel(self)
            login.withdraw()
            login.title(f"🔐 Accesso {NAME}")
            login.resizable(False, False)

            def chiusura():
                self.quit()
                self.destroy()

            login.protocol("WM_DELETE_WINDOW", chiusura)

            w, h = 380, 230
            x = self.winfo_screenwidth() // 2 - w // 2
            y = self.winfo_screenheight() // 2 - h // 2
            login.geometry(f"{w}x{h}+{x}+{y}")

            login.deiconify()
            login.lift()
            login.focus_force()
            login.grab_set()

            if os.path.exists(PW_FILE):
                  # Password già impostata → richiesta login
                  tk.Label(login, text=f"Utente:► {current_folder} \n\n🔑 Inserisci la password:\n", font=("Arial", 10,"bold")).pack(pady=(15, 5))
            else:
                  # Prima volta → benvenuto
                  tk.Label(login, text=f"🆕 PRIMO ACCESSO \n\n Utente:► {current_folder} \n\n🔐 Crea una nuova password per proteggere i tuoi dati.\n Premi Invio per confermare.\n", font=("Arial", 10,"bold")).pack(pady=(15, 5))
       
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
                        fg="dark green"
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
                win.geometry(f"380x230+{x}+{y}")
                win.grab_set()

                tk.Label(win, text="\nVecchia password:").pack()
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
                        mess.config(text="❌ Le Password non corrispondono.")
                    else:
                        salva_hash(nuova)
                        mess.config(text="✅ Password aggiornata.", fg="green")
                        win.after(1000, win.destroy)
                        
                tk.Button(
                    win,
                    text="💾 Salva",
                    command=conferma_cambio,
                    bg="#4CAF50",     # Colore di sfondo (verde stile "Salva")
                    fg="white",       # Colore del testo
                    activebackground="#45A049",  # Sfondo al passaggio del mouse
                    activeforeground="white",    # Testo attivo
                    relief="raised",  # Effetto bordo (opzionale)
                    font=("Arial", 10, "bold")
                ).pack(pady=8)
                
            if os.path.exists(PW_FILE):
                tk.Button(
                    login,
                    text="🔁 Cambia password",
                    command=cambia_password,
                    bg="#2196F3",            # Blu acceso stile "azione secondaria"
                    fg="white",              # Testo bianco
                    activebackground="#1976D2",  # Blu più scuro al click
                    activeforeground="white",
                    relief="raised",
                    font=("Arial", 10, "bold"),
                    cursor="hand2"
                ).pack(pady=(2, 8))

            login.wait_window()

        # ✅ Autologin da argomento
        args = sys.argv
        login_riuscito = [False]

        # ✅ Cerca "auto" tra gli argomenti
        if "noweb" not in args:
            threading.Thread(target=self.start_web_server, daemon=True).start()
            print("🌐 Server web avviato di default (nessun 'noweb' tra gli argomenti).")
        else:
            print("🛑 Server web disattivato da 'noweb'.")
        
        if "auto" in args:
            index = args.index("auto")
            arg_password = args[index + 1] if len(args) > index + 1 else ""  # anche vuota
            salvata = leggi_hash()

            if salvata and hash_pw(arg_password) == salvata:
                print("✅ Login automatico riuscito.")
                login_riuscito[0] = True
                return login_riuscito[0]
            else:
                print("❌ Password da argomento non valida. Apro GUI...")
                mostra_finestra_login()
                return login_riuscito[0]
             
        # 🖼️ Se "auto" non è presente, mostra login GUI
        mostra_finestra_login()
        return login_riuscito[0]
        
    def apri_finestra_importa(self):
        win = tk.Toplevel(self)
        win.title("Importa Spese")
        larghezza, altezza = 300, 160
        x = (win.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (win.winfo_screenheight() // 2) - (altezza // 2)
        win.geometry(f"{larghezza}x{altezza}+{x}+{y}")

        win.resizable(False, False)
        win.grab_set()
        win.configure(bg="#F9F9D1") 

        tk.Label(win, text="Seleziona la banca:", font=("Arial", 10), bg="#F9F9D1").pack(pady=(10, 4))

        banca_var = tk.StringVar()
        banca_combo = ttk.Combobox(win, textvariable=banca_var, state="readonly", values=["-- Nessuna --", "UniCredit", "Intesa", "Fineco", "Altra..."])
        banca_combo.set("-- Nessuna --")  # Valore iniziale visualizzato
        banca_combo.pack()

        frame_bottoni = tk.Frame(win, bg="#F9F9D1")
        frame_bottoni.pack(pady=10)

        # Bottoni nascosti all'inizio
        style = ttk.Style()
        style.configure("ICC.TButton", foreground="black", background="#FFA500") 
        style.map("ICC.TButton", background=[("active", "#FF8C00")])  
        style.configure("CCV.TButton", foreground="black", background="#FFA500")
        style.map("CCV.TButton", background=[("active", "#FF8C00")])

        btn_icc = ttk.Button(frame_bottoni, text="💳 ICC", width=10, style="ICC.TButton", command=lambda: [win.destroy(), self.importa_spese_csv_unicredit()])
        btn_ccv = ttk.Button(frame_bottoni, text="🏦 CCV", width=10, style="CCV.TButton", command=lambda: [win.destroy(), self.importa_spese_cc_csv_unicredit()])
        btn_icc.pack(side="left", padx=8)
        btn_ccv.pack(side="right", padx=8)
        btn_icc.pack_forget()
        btn_ccv.pack_forget()
        
        messaggio_var = tk.StringVar()
        label_messaggio = tk.Label(win, textvariable=messaggio_var, font=("Arial", 9), bg="#F9F9D1", fg="gray25")
        label_messaggio.pack(pady=(6, 2))

        # Quando selezioni la banca, mostra i bottoni
        def mostra_bottoni(event=None):
            banca = banca_var.get()
            if banca == "UniCredit":
                messaggio_var.set("✅ Importazione disponibile per UniCredit:")
                btn_icc.pack(side="left", padx=8)
                btn_ccv.pack(side="right", padx=8)
            else:
                # Nasconde i bottoni se l’utente cambia banca
                btn_icc.pack_forget()
                btn_ccv.pack_forget()
                messaggio_var.set(f"⚠️ Importazione da {banca} non ancora disponibile.")

        banca_combo.bind("<<ComboboxSelected>>", mostra_bottoni)

    def importa_spese_csv_unicredit(self):
        from datetime import datetime
        path = filedialog.askopenfilename(
            title="Seleziona Estratto CARTA UNICREDIT",
            filetypes=[("File CSV", "*.csv")]
        )
        if not path:
            return

        movimenti = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    try:
                        data = datetime.strptime(row["Data Registrazione"], "%d/%m/%Y").date()
                        descrizione = row["Descrizione"].strip()
                        importo = float(row["Importo"].replace(",", "."))
                        movimenti.append({"data": data, "descrizione": descrizione, "importo": importo})
                    except Exception as e:
                        print("Errore riga:", row, "→", e)
        except Exception as e:
            self.show_custom_warning("Errore apertura CSV", str(e))
            return

        if not movimenti:
            self.show_custom_warning("Importazione", "Nessuna spesa valida trovata.")
            return

        movimenti.sort(key=lambda m: m["data"])

        if not hasattr(self, "memoria_descrizioni_categoria"):
            self.memoria_descrizioni_categoria = {}
        memoria = self.memoria_descrizioni_categoria
    
        win = tk.Toplevel(self)
        win.resizable(False, False)
        win.title("Importa da Unicredit Credit Card")

        larghezza, altezza = 820, 600
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (win.winfo_screenheight() // 2) - (altezza // 2)
        win.geometry(f"{larghezza}x{altezza}+{x}+{y}")
        win.grab_set()

        contenitore = tk.Frame(win)
        contenitore.pack(fill="both", expand=True)

        canvas = tk.Canvas(contenitore, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenitore, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        area_dati = tk.Frame(canvas)
        canvas.create_window((0, 0), window=area_dati, anchor="nw")

        area_dati.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        pannello_aggiungi_cat = tk.Frame(area_dati)
        pannello_aggiungi_cat.pack(anchor="w", pady=(6, 6), padx=4)

        tk.Label(pannello_aggiungi_cat, text="➕ Nuova categoria:", foreground="green").pack(side="left", padx=(0, 4))

        var_nuova_cat = tk.StringVar()
        entry_nuova_cat = ttk.Entry(pannello_aggiungi_cat, textvariable=var_nuova_cat, width=20)
        entry_nuova_cat.pack(side="left")

        def aggiungi_categoria_csv():
            nome = var_nuova_cat.get().strip()
            if not nome:
                self.show_custom_warning("Attenzione", "Il nome categoria è vuoto.")
                return
            if nome in self.categorie:
                self.show_custom_warning("Attenzione", "Categoria già esistente.")
                return

            self.categorie.append(nome)
            self.categorie_tipi[nome] = "Uscita"
            memoria[nome.strip().upper()] = nome
            var_nuova_cat.set("")

            # Aggiorna tutte le combobox già presenti
            for _, _, combo in righe:
                combo["values"] = self.categorie
            self.aggiorna_combobox_categorie()
            self.show_custom_info("Categoria creata", f"Categoria '{nome}' aggiunta.")
        style = ttk.Style()
        style.configure("Verde.TButton", background="#32CD32")

        btn_aggiungi_cat = ttk.Button(
            pannello_aggiungi_cat,
            text="Aggiungi",
            command=aggiungi_categoria_csv,
            style="Verde.TButton"
        )

        btn_aggiungi_cat.pack(side="left", padx=6)

        entry_nuova_cat.bind("<Return>", lambda e: aggiungi_categoria_csv())
        
        righe = []
        seleziona_tutti_var = tk.BooleanVar(value=True)

        def toggle_tutti():
            for _, var_check, _ in righe:
                var_check.set(seleziona_tutti_var.get())

        tk.Checkbutton(area_dati, text="✔ Seleziona tutto", variable=seleziona_tutti_var, command=toggle_tutti).pack(anchor="w", pady=(5, 2))

        # Intestazioni
        header = tk.Frame(area_dati)
        header.pack(anchor="w")
        tk.Label(header, text="✔", width=2).grid(row=0, column=0)
        tk.Label(header, text="Data", width=10).grid(row=0, column=1)
        tk.Label(header, text="Descrizione", width=40, anchor="w").grid(row=0, column=2)
        tk.Label(header, text="Importo", width=12, anchor="e").grid(row=0, column=3)
        tk.Label(header, text="Categoria", width=20).grid(row=0, column=4)

        # Righe spese
        for mov in movimenti:
            riga = tk.Frame(area_dati)
            riga.pack(anchor="w", pady=1)
            #abilita_scroll(riga)

            var = tk.BooleanVar(value=True)
            tk.Checkbutton(riga, variable=var).grid(row=0, column=0)

            tk.Label(riga, text=mov["data"].strftime("%d/%m/%Y"), width=10).grid(row=0, column=1)
            tk.Label(riga, text=mov["descrizione"], width=40, anchor="w").grid(row=0, column=2)
            tk.Label(riga, text=f"{mov['importo']:.2f} €", width=12, anchor="e").grid(row=0, column=3)

            chiave = mov["descrizione"].strip().upper()
            categoria = memoria.get(chiave, "Generica")

            combo = ttk.Combobox(riga, values=self.categorie, state="readonly", width=20)
            combo.set(categoria)
            combo.grid(row=0, column=4, padx=4)

            righe.append((mov, var, combo))

        bottoni = tk.Frame(win)
        bottoni.pack(pady=10)

        def salva():
            count = 0
            duplicati = 0

            for mov, var, combo in righe:
                if var.get():
                    giorno = mov["data"]
                    descr = mov["descrizione"]
                    imp = abs(mov["importo"])
                    tipo = "Entrata" if mov["importo"] >= 0 else "Uscita"
                    cat = combo.get() or "Generica"
                    voce = (cat, descr, imp, tipo)

                    # Cerca se già esiste una voce simile (stessa categoria e tipo, importo arrotondato all'euro)
                    gia_presente = None
                    for voce_esistente in self.spese.get(giorno, []):
                        cat_es, desc_es, imp_es, tipo_es = voce_esistente
                        if (
                            cat_es == cat and
                            tipo_es == tipo and
                            round(imp_es) == round(imp)
                        ):
                            gia_presente = voce_esistente
                            break

                    if gia_presente:
                        if self.conferma_sostituzione_spesa(giorno, cat, imp_es, imp):
                                self.spese[giorno].remove(gia_presente)
                        else:
                                duplicati += 1
                                continue

                    self.spese.setdefault(giorno, []).append(voce)
                    memoria[descr.strip().upper()] = cat
                    count += 1

            self.save_db()
            self.refresh_gui()
            
            messaggio = f"{count} spese importate/salvate."

            if duplicati > 0:
                messaggio += f"\n⚠️ {duplicati} duplicate/ignorate."

            self.show_custom_warning("Completato", messaggio)
            #win.destroy()

        def chiudi():
            win.destroy()
            self.show_custom_warning("Annullato", "Importazione interrotta.")
                       
        tk.Button(bottoni, text="Salva", bg="#32CD32", width=12, command=salva).pack(side="left", padx=10)
        tk.Button(bottoni, text="Chiudi", bg="yellow", width=12, command=chiudi).pack(side="right", padx=10)

    
    def importa_spese_cc_csv_unicredit(self):
        from datetime import datetime
        path = filedialog.askopenfilename(
            title="Seleziona Estratto Conto UNICREDIT",
            filetypes=[("File CSV", "*.csv")]
        )
        if not path:
            return

        movimenti = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    try:
                        data_str = row["Data Registrazione"].strip()
                        try:
                            data = datetime.strptime(data_str, "%d/%m/%Y").date()
                        except ValueError:
                            data = datetime.strptime(data_str, "%d.%m.%Y").date()

                        descrizione = row["Descrizione"].strip()

                        importo_str = row["Importo (EUR)"].strip().replace(".", "").replace(",", ".")
                        importo = float(importo_str)

                        movimenti.append({"data": data, "descrizione": descrizione, "importo": importo})
                    except Exception as e:
                        print("Errore riga:", row, "→", e)
        except Exception as e:
            self.show_custom_warning("Errore apertura CSV", str(e))
            return

        if not movimenti:
            self.show_custom_warning("Importazione", "Nessuna spesa valida trovata.")
            return

        movimenti.sort(key=lambda m: m["data"])

        if not hasattr(self, "memoria_descrizioni_categoria"):
            self.memoria_descrizioni_categoria = {}
        memoria = self.memoria_descrizioni_categoria

        win = tk.Toplevel(self)
        win.resizable(False, False)
        win.title("Importa da Unicredit C/C")
        larghezza, altezza = 820, 600
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (win.winfo_screenheight() // 2) - (altezza // 2)
        win.geometry(f"{larghezza}x{altezza}+{x}+{y}")
        win.grab_set()

        contenitore = tk.Frame(win)
        contenitore.pack(fill="both", expand=True)

        canvas = tk.Canvas(contenitore, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenitore, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        area_dati = tk.Frame(canvas)
        canvas.create_window((0, 0), window=area_dati, anchor="nw")

        area_dati.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        pannello_aggiungi_cat = tk.Frame(area_dati)
        pannello_aggiungi_cat.pack(anchor="w", pady=(6, 6), padx=4)

        tk.Label(pannello_aggiungi_cat, text="➕ Nuova categoria:", foreground="green").pack(side="left", padx=(0, 4))

        var_nuova_cat = tk.StringVar()
        entry_nuova_cat = ttk.Entry(pannello_aggiungi_cat, textvariable=var_nuova_cat, width=20)
        entry_nuova_cat.pack(side="left")

        def aggiungi_categoria_csv():
            nome = var_nuova_cat.get().strip()
            if not nome:
                self.show_custom_warning("Attenzione", "Il nome categoria è vuoto.")
                return
            if nome in self.categorie:
                self.show_custom_warning("Attenzione", "Categoria già esistente.")
                return

            self.categorie.append(nome)
            self.categorie_tipi[nome] = "Uscita"
            memoria[nome.strip().upper()] = nome
            var_nuova_cat.set("")

            for _, _, combo in righe:
                combo["values"] = self.categorie
            self.aggiorna_combobox_categorie()
            self.show_custom_info("Categoria creata", f"Categoria '{nome}' aggiunta.")
            
        style = ttk.Style()
        style.configure("Verde.TButton", background="#32CD32")

        btn_aggiungi_cat = ttk.Button(
            pannello_aggiungi_cat,
            text="Aggiungi",
            command=aggiungi_categoria_csv,
            style="Verde.TButton"
        )
        
        btn_aggiungi_cat.pack(side="left", padx=6)

        entry_nuova_cat.bind("<Return>", lambda e: aggiungi_categoria_csv())

        righe = []
        seleziona_tutti_var = tk.BooleanVar(value=True)

        def toggle_tutti():
            for _, var_check, _ in righe:
                var_check.set(seleziona_tutti_var.get())

        tk.Checkbutton(area_dati, text="✔ Seleziona tutto", variable=seleziona_tutti_var, command=toggle_tutti).pack(anchor="w", pady=(5, 2))

        intest = tk.Frame(area_dati)
        intest.pack(anchor="w")
        tk.Label(intest, text="✔", width=2).grid(row=0, column=0)
        tk.Label(intest, text="Data", width=10).grid(row=0, column=1)
        tk.Label(intest, text="Descrizione", width=40, anchor="w").grid(row=0, column=2)
        tk.Label(intest, text="Importo", width=12, anchor="e").grid(row=0, column=3)
        tk.Label(intest, text="Categoria", width=20).grid(row=0, column=4)

        for mov in movimenti:
            riga = tk.Frame(area_dati)
            riga.pack(anchor="w", pady=1)

            var = tk.BooleanVar(value=True)
            tk.Checkbutton(riga, variable=var).grid(row=0, column=0)

            tk.Label(riga, text=mov["data"].strftime("%d/%m/%Y"), width=10).grid(row=0, column=1)
            tk.Label(riga, text=mov["descrizione"], width=40, anchor="w").grid(row=0, column=2)
            tk.Label(riga, text=f"{mov['importo']:.2f} €", width=12, anchor="e").grid(row=0, column=3)

            chiave = mov["descrizione"].strip().upper()
            categoria = memoria.get(chiave, "Generica")

            combo = ttk.Combobox(riga, values=self.categorie, state="readonly", width=20)
            combo.set(categoria)
            combo.grid(row=0, column=4, padx=4)

            righe.append((mov, var, combo))

        bottoni = tk.Frame(win)
        bottoni.pack(pady=10)

        def salva():
            count = 0
            duplicati = 0
            for mov, var, combo in righe:
                if var.get():
                    giorno = mov["data"]
                    descr = mov["descrizione"]
                    imp = abs(mov["importo"])
                    tipo = "Entrata" if mov["importo"] >= 0 else "Uscita"
                    cat = combo.get() or "Generica"
                    voce = (cat, descr, imp, tipo)

                    if voce in self.spese.get(giorno, []):
                        duplicati += 1
                        continue

                    self.spese.setdefault(giorno, []).append(voce)
                    memoria[descr.strip().upper()] = cat
                    count += 1

            self.save_db()
            self.refresh_gui()
            try:
                with open("memoria_categorie.json", "w", encoding="utf-8") as f:
                    json.dump(memoria, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print("⚠️ Impossibile salvare memoria categorie:", e)

            messaggio = f"{count} spese importate/salvate."
            if duplicati > 0:
                messaggio += f"\n⚠️ {duplicati} duplicate/ignorate."

            self.show_custom_warning("Completato", messaggio)

        def chiudi():
            win.destroy()
            self.show_custom_warning("Annullato", "Importazione interrotta.")

        tk.Button(bottoni, text="Salva", bg="#32CD32", width=12, command=salva).pack(side="left", padx=10)
        tk.Button(bottoni, text="Chiudi", bg="yellow", width=12, command=chiudi).pack(side="right", padx=10)

    def conferma_sostituzione_spesa(self, giorno, categoria, imp_esistente, imp_nuovo):
        popup = tk.Toplevel(self)
        popup.title("Sostituisci spesa?")
        popup.resizable(False, False)
        width, height = 400, 160
        popup.withdraw()
        popup.update_idletasks()

        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.configure(bg="#FFFACD")
        popup.deiconify()
        popup.grab_set()

        msg = (
            f"Esiste già una spesa nella categoria “{categoria}” il {giorno.strftime('%d/%m/%Y')} "
            f"da €{imp_esistente:.2f}.\n\nVuoi sostituirla con la nuova da €{imp_nuovo:.2f}?"
        )

        label = tk.Label(
            popup,
            text=msg,
            font=("Arial", 10),
            justify="center",
            wraplength=360,
            bg="#FFFACD"
        )
        label.pack(pady=12, padx=16)

        frame = tk.Frame(popup, bg="#FFFACD")
        frame.pack(pady=4)

        result = {"ok": False}

        def conferma():
            result["ok"] = True
            popup.destroy()

        def annulla():
            popup.destroy()

        tk.Button(frame, text="Sostituisci", bg="#32CD32", fg="white", width=12, command=conferma).pack(side="left", padx=10)
        tk.Button(frame, text="Annulla", bg="lightgray", width=12, command=annulla).pack(side="right", padx=10)

        self.wait_window(popup)
        return result["ok"]

    def calcola_statistiche_annuali(self):
        from datetime import date
        oggi = date.today()
        anno_corr = oggi.year
        anno_prec = anno_corr - 1
        mese_corr = oggi.month

        tot_mese_corr, tot_mese_prec = 0.0, 0.0
        tot_anno_corr, tot_anno_prec = 0.0, 0.0

        for giorno, voci in self.spese.items():
            for voce in voci:
                if len(voce) < 4:
                    continue
                categoria, descrizione, importo, tipo = voce[:4]
                if tipo != "Uscita":
                    continue

                if giorno.year == anno_corr and giorno.month == mese_corr:
                    tot_mese_corr += importo
                if giorno.year == anno_prec and giorno.month == mese_corr:
                    tot_mese_prec += importo
                if giorno.year == anno_corr and giorno <= oggi:
                    tot_anno_corr += importo
                if giorno.year == anno_prec and giorno <= oggi.replace(year=anno_prec):
                    tot_anno_prec += importo

        # Calcolo avanzamento temporale
        giorni_passati_corr = (oggi - date(anno_corr, 1, 1)).days + 1
        giorni_totali_corr = 365  # Anni non bisestili

        perc_corr = giorni_passati_corr / giorni_totali_corr

        # Stima spesa per fine anno corrente
        stima_2025 = tot_anno_corr / perc_corr if perc_corr else tot_anno_corr

        # Spesa totale reale dell'anno precedente
        stima_2024 = 0.0
        for giorno, voci in self.spese.items():
            if giorno.year == anno_prec:
                for voce in voci:
                    if len(voce) >= 4 and voce[3] == "Uscita":
                        stima_2024 += voce[2]
            if tot_mese_prec:
                variazione_mese_pct = (tot_mese_corr - tot_mese_prec) / tot_mese_prec * 100
            else:
                variazione_mese_pct = 0.0  # oppure 'float("nan")' se vuoi gestire caso zero

        differenza = stima_2024 - stima_2025

        # Generazione report
        report = f"""
        
    📊 REPORT PROIEZIONE SPESE – {oggi.strftime('%d/%m/%Y')}
    
    ─────────────────────────────────────────────────────────────────────────────────
    📅 Mese corrente: {mese_corr:02}/{anno_corr}
    ▸ Uscite attuali {anno_corr}     : € {tot_mese_corr:>10,.2f}
    ▸ Stesso mese {anno_prec}        : € {tot_mese_prec:>10,.2f}
    
    ▸ Variazione rispetto a {mese_corr:02}/{anno_prec} : {variazione_mese_pct:+.1f}%
    
    ─────────────────────────────────────────────────────────────────────────────────
    📆 Da inizio anno (01/01 → oggi)
    ▸ Totale uscite {anno_corr}      : € {tot_anno_corr:>10,.2f}
    ▸ Stesso periodo {anno_prec}     : € {tot_anno_prec:>10,.2f}

    ─────────────────────────────────────────────────────────────────────────────────
    📈 Spesa a confronto annuale
    ▸ Spesa effettiva {anno_prec}    : € {stima_2024:>10,.2f}
    ▸ Proiezione {anno_corr}         : € {stima_2025:>10,.2f}   (basata su {perc_corr:.1%} dell’anno trascorso)

    ─────────────────────────────────────────────────────────────────────────────────

    """

        if differenza > 0:
            report += f"\n📉 Risparmio previsto: € {differenza:,.2f} se mantieni l’andamento attuale ✨💰✨ "
        else:
            report += f"\n⚠️ Spesa stimata superiore di € {abs(differenza):,.2f} rispetto al {anno_prec} 📉🪙"

        self.mostra_report_popup(report.strip())

    def mostra_report_popup(self, testo):
   
        EXPORT_FILES = "./export"  # Puoi cambiarlo con la tua costante se diversa
        os.makedirs(EXPORT_FILES, exist_ok=True)

        preview = tk.Toplevel(self)
        preview.withdraw() 
        preview.title("📊 Report Proiezione Annuale")
        width, height = 860, 500

        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        preview.geometry(f"{width}x{height}+{x}+{y}")
        preview.deiconify()  # Mostra la finestra
        preview.configure(bg="#FDFEE0")
        preview.grab_set()
        preview.bind("<Escape>", lambda e: preview.destroy())
        text_area = tk.Text(preview, font=("Courier New", 10), bg="#FFFFF5", wrap="word")
        text_area.insert("1.0", testo)
        text_area.config(state="disabled")
        text_area.pack(fill="both", expand=True, padx=10, pady=10)

        def save_file():
            now = datetime.date.today()
            default_filename = f"Report_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                title="Salva Report",
                confirmoverwrite=False,
                parent=preview
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return  # Annulla salvataggio
                        
                with open(file, "w", encoding="utf-8") as f:
                    f.write(testo)
                preview.destroy()
                self.show_custom_warning("Esportazione completata", f"Report esportato in:\n{file}")

        frame_bottoni = tk.Frame(preview, bg="#FDFEE0")
        frame_bottoni.pack(fill="x", padx=8, pady=8)

        tk.Button(frame_bottoni, text="📄 Esporta", bg="#32CD32", fg="black", width=12, command=save_file).pack(side="left")
        tk.Button(frame_bottoni, text="Chiudi", bg="yellow", fg="black", width=12, command=preview.destroy).pack(side="right")
        preview.bind("<Escape>", lambda e: preview.destroy())

    def apri_categorie_suggerite(self):
        CATEGORIE_SUGGERITE = [
            # 🏠 Casa & Famiglia
            "🏠 Casa",
            "🏠 Affitto Immobile",
            "🏠 Mutuo Immobile",
            "🏡 Manutenzione casa",
            "💡 Utenze (Luce)",
            "🔥 Utenze (Gas)",
            "🚿 Utenze (Acqua)",
            "♨️ Caldaia",
            "🌰 Pellet",
            "🗑️ Tassa Rifiuti",
            "🏠 Pulizie domestiche",
            "🛋️ Arredamento",
            "🐾 Animali domestici",
            "🏠 Assicurazione Immobile",

            # 🍽️ Alimentari & Consumi
            "🍽️ Alimentari & Consumi",
            "🛒 Spesa supermercato",
            "🍞 Spesa Discount",
            "☕ Colazioni / Caffè fuori",
            "🍽️ Pranzi / Ristoranti",
            "🍕 Asporto / Fast food",

            # 🚗 Veicoli & Trasporti
            "🚗 Veicoli & Trasporti",
            "⛽ Carburante",
            "🛠️ Manutenzione auto",
            "📅 Bollo auto",
            "🏥 Assicurazione veicoli",
            "🚇 Trasporti pubblici",
            "🚕 Taxi / Car sharing",

            # 💡 Bollette & Abbonamenti
            "💡 Bollette & Abbonamenti",
            "📱 Telefonia / Internet",
            "📱 Telefonia / Cellulari",
            "💻 Streaming (Netflix, Prime...)",
            "🔐 Servizi cloud / backup",
            "🎮 Abbonamenti digitali",

            # 🩺 Salute & Benessere
            "🩺 Salute & Benessere",
            "💊 Farmaci",
            "👨‍⚕️ Visite mediche",
            "🏥 Dentista",
            "🧘‍♂️ Wellness / Spa",
            "🏋️‍♀️ Palestra / Fitness",

            # 🎓 Istruzione & Lavoro
            "🎓 Istruzione & Lavoro",
            "📚 Libri / Materiali",
            "🧑‍🏫 Corsi / Formazione",
            "💻 Software",
            "🗂️ Utenze professionali / Partita IVA",

            # 🎉 Tempo libero & Spese personali
            "🎉 Tempo libero & Spese personali",
            "🎁 Regali",
            "🎬 Cinema / Eventi",
            "🎮 Videogiochi",
            "🎮 Computer",
            "🧥 Abbigliamento",
            "🎁 Tabacchi",
            "💇 Parrucchiere / Estetica",
            "✈️ Viaggi / Hotel",

            # 💸 Finanza & Risparmio
            "💸 Stipendio",
            "💸 Pensione",
            "💸 Entrate Extra",
            "💸 Finanza & Risparmio",
            "🏦 Conto corrente",
            "💳 Rate / Finanziamenti",
            "💰 Commercialista",

            # 📤 Uscite straordinarie
            "📤 Uscite straordinarie",
            "🏥 Emergenze",
            "🛠️ Riparazioni impreviste",
            "📦 Spese non ricorrenti"
        ]

    
        finestra = tk.Toplevel(self)
        finestra.title("Categorie suggerite")
        finestra.configure(bg="white")
        finestra.resizable(False, False)
        finestra.bind("<Escape>", lambda e: finestra.destroy())
        finestra.geometry("500x480") 
        larghezza, altezza = 500, 480
        x = (finestra.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (finestra.winfo_screenheight() // 2) - (altezza // 2)
        finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")

        tk.Label(
            finestra,
            text="✨ Scegli categorie da aggiungere:",
            bg="white", font=("Arial", 10, "bold")
        ).pack(pady=(10, 5))

        # Canvas + scrollbar
        container = tk.Frame(finestra, bg="white")
        container.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # ⬇️ Fase delicata: frame interno + associazione corretta
        scroll_frame = tk.Frame(canvas, bg="white")
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # ⬅️ Aggiorna area scrollabile in base al contenuto
        def aggiorna_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", lambda event: canvas.itemconfig(canvas_window, width=event.width))
        scroll_frame.bind("<Configure>", aggiorna_scroll_region)

        # Checkbox dinamici
        selezioni = {}
        # 🔘 Checkbox Tutte / Nessuna
        toggle_var = tk.BooleanVar(value=False)

        def seleziona_tutto():
            stato = toggle_var.get()
            for var in selezioni.values():
                var.set(stato)

        toggle_chk = tk.Checkbutton(
            scroll_frame,
            text="✔️ Seleziona Tutte / Nessuna",
            variable=toggle_var,
            command=seleziona_tutto,
            bg="white",
            activebackground="white",
            highlightthickness=0,
            anchor="w",
            font=("Arial", 9, "bold")
        )
        toggle_chk.pack(anchor="w", pady=(6, 6), padx=4)

        for nome in CATEGORIE_SUGGERITE:
            var = tk.BooleanVar()
            
            chk = tk.Checkbutton(
                scroll_frame,
                text=nome,
                variable=var,
                bg="white",
                activebackground="white",
                highlightthickness=0,
                anchor="w"
            )

            chk.pack(anchor="w", pady=2, padx=4)
            selezioni[nome] = var

        # Bottoni fondo
        def aggiungi_categorie_scelte():
            nuove = [nome for nome, var in selezioni.items() if var.get()]
            pulite = [nome.split(" ", 1)[1] if " " in nome else nome for nome in nuove]

            if hasattr(self, "categorie"):
                for cat in pulite:
                    if cat not in self.categorie:
                        self.categorie.append(cat)

            if hasattr(self, "aggiorna_combobox_categorie"):
                self.aggiorna_combobox_categorie()

            finestra.destroy()

        btn_frame = tk.Frame(finestra, bg="white")
        btn_frame.pack(pady=(0, 12))

        tk.Button(
            btn_frame, text="➕ Aggiungi",
            command=aggiungi_categorie_scelte,
            bg="#4CAF50", fg="white",
            font=("Arial", 9, "bold"),
            relief="raised", padx=10, cursor="hand2"
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="❌ Chiudi",
            command=finestra.destroy,
            bg="#FFCC00", fg="black",
            font=("Arial", 9, "bold"),
            relief="raised", padx=10, cursor="hand2"
        ).pack(side="left", padx=8)


    def scarica_manuale(self):
        try:
            # Scarica PDF
            response = requests.get(URL_PDF)
            response.raise_for_status()
            # Crea file temporaneo
            temp_path = os.path.join(tempfile.gettempdir(), "manuale_casa_facile.pdf")
            with open(temp_path, "wb") as f:
                f.write(response.content)
            # Apri PDF con app predefinita
            webbrowser.open(f"file://{temp_path}")
        except Exception as e:
            print("Errore nel download del manuale:", e)
            self.show_custom_warning("Attenzione", "❌ Download NON completato ! \n\n Sembra ci sia stato un problema. 😕")
            
    def apri_webserver(self):
        IP = self.get_ip_locale()
        webbrowser.open(f"http://{IP}:{PORTA}")

    def apri_webserver_port(self):
        finestra = tk.Toplevel()
        finestra.withdraw() 
        finestra.title("Cambio porta Webserver")
        finestra.resizable(False, False)
        finestra.grab_set()  # Focus esclusivo
        larghezza, altezza = 320, 140
        finestra.update_idletasks()
        x = (finestra.winfo_screenwidth() // 2) - (larghezza // 2)
        y = (finestra.winfo_screenheight() // 2) - (altezza // 2)
        finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")  
        finestra.deiconify() 
        porta_corrente = "8081"  # tua logica qui
        if os.path.exists(PORTA_DB):
            try:
                with open(PORTA_DB, "r") as file:
                    porta_corrente = str(json.load(file))
            except:
                pass
        #vcmd = (finestra.register(lambda val: val.isdigit()), "%P") # Obbliga range 8000-8999
        vcmd = (finestra.register(lambda val: val.isdigit() or val == ""), "%P")

        ttk.Label(finestra, text="Porta Webserver:").pack(pady=(12, 4))
        entry_porta = ttk.Entry(finestra, justify="center", font=("Segoe UI", 12), validate="key", validatecommand=vcmd)
        entry_porta.insert(0, porta_corrente)
        entry_porta.pack(padx=20)
        btn_frame = ttk.Frame(finestra)
        btn_frame.pack(pady=16)
        def salva_porta():
            porta = entry_porta.get().strip()
            if porta.isdigit():
               with open(PORTA_DB, "w") as file:
                    json.dump(int(porta), file)
                    finestra.destroy()
        tk.Button(btn_frame, text="🟢 Salva", command=salva_porta, bg="#4CAF50", fg="white", width=10, font=("Segoe UI", 10)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🟡 Chiudi", command=finestra.destroy, bg="#FFC107", fg="black", width=10, font=("Segoe UI", 10)).pack(side="left", padx=5)



    def get_ip_locale(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP
   
    def start_web_server(self):
        server = HTTPServer(('0.0.0.0', PORTA), CasaFacileWebHandler)
        server.app = self  # collega il gestore HTTP alla tua GUI
        print("🌐 Web server pronto su http://localhost:8081")
        server.serve_forever()

    def html_login(self, path):
   
        folder = os.path.basename(os.getcwd())

        try:
            query = path.split("?", 1)[1]
            params = parse_qs(query)
            errore = "error" in params
        except:
            errore = False
        messaggio = ""
        if errore:
            messaggio = "<p style='color:red; text-align:center;'>❌ Password errata. Riprova.</p>"

        return f"""
        <!DOCTYPE html>
        <html><head><meta charset="utf-8">
        <title>🔐 Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {{
            font-family: sans-serif;
            background: #f4f4f4;
            padding: 30px;
          }}
          form {{
            max-width: 400px;
            margin: auto;
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 6px rgba(0,0,0,0.1);
          }}
          h2 {{
            text-align: center;
            margin-bottom: 10px;
          }}
          input[type="password"], button {{
            display: block;
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            box-sizing: border-box;
            font-size: 16px;
          }}
          button {{
            background: #0078D4;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
          }}
        </style>
        </head><body>
        <form method="post" action="/check_login">
          <h2>🔐 Login {NAME}</h2>
          <h2>Versione v{VERSION} @ 2025</h2>
          <p style="text-align: center; font-size: 14px; color: #555; margin-top: -5px;">{folder}</p>
          {messaggio}
          <input type="password" name="password" placeholder="Password  ⏎" autofocus>
          <button type="submit">Accedi</button>
        </form>
        </body></html>
        """

    def leggi_hash(self):
        if not os.path.exists(PW_FILE):
            return None
        try:
            with open(PW_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("hash")
        except:
            return None

    def verifica_password(self, password):
        salvato = self.leggi_hash()
        if salvato is None:
            return False  # ⛔ file non esiste, blocco accesso
        inserito = hashlib.sha256(password.encode()).hexdigest()
        return salvato == inserito

    def pagina_risultati_avanzati(self, params):
        from datetime import datetime

        categoria = params.get("categoria", [""])[0].strip().lower()
        anno = params.get("anno", [""])[0].strip()
        mese = params.get("mese", [""])[0].strip()
        tipo = params.get("tipo", [""])[0].strip().lower()  # 🔧 Aggiunto filtro tipo
        min_importo = float(params.get("min_importo", ["0"])[0] or 0)
        max_importo = float(params.get("max_importo", ["999999"])[0] or 999999)
        query = params.get("q", [""])[0].strip().lower()

        risultati_categorizzati = defaultdict(list)
        for data in sorted(self.spese.keys(), reverse=True):
            if anno and str(data.year) != anno: continue
            if mese and f"{data.month:02d}" != mese: continue

            for voce in self.spese[data]:
                if len(voce) < 4: continue
                cat, descrizione, importo, tipo_voce = voce
                if categoria and cat.strip().lower() != categoria: continue
                if tipo and tipo_voce.strip().lower() != tipo: continue  # 🔧 Applica filtro tipo
                if not (min_importo <= importo <= max_importo): continue
                if query and not (query in descrizione.lower() or query in tipo_voce.lower() or query in cat.lower() or query in str(importo)):
                    continue
                risultati_categorizzati[cat].append((
                    data.strftime("%d-%m-%Y"),
                    html_escape.escape(descrizione),
                    float(importo),
                    tipo_voce.strip()
                ))

        entrate_totali = sum(v[2] for vlist in risultati_categorizzati.values() for v in vlist if v[3].lower() == "entrata")
        uscite_totali = sum(v[2] for vlist in risultati_categorizzati.values() for v in vlist if v[3].lower() != "entrata")
        saldo = entrate_totali - uscite_totali
        colore = "#3c763d" if saldo >= 0 else "#a94442"

        schede_html = ""
        for idx, (cat, voci) in enumerate(sorted(risultati_categorizzati.items())):
            totale_cat = sum(imp if tipo_voce.lower() == "entrata" else -imp for _, _, imp, tipo_voce in voci)
            voce_html = ""
            for data, descrizione, importo, tipo_voce in voci:
                simbolo = "+" if tipo_voce.lower() == "entrata" else "−"
                colore_tipo = "#007E33" if tipo_voce.lower() == "entrata" else "#D8000C"
                voce_html += f"""
                    <li>
                        {data} • {descrizione} 
                        <span style='color:#000; font-weight:bold;'>{simbolo}€{importo:.2f}</span>
                        <strong style='color:{colore_tipo};'>[{tipo_voce}]</strong>
                    </li>
                """
            simbolo_totale = "➕" if totale_cat >= 0 else "➖"
            colore_totale = "#007E33" if totale_cat >= 0 else "#D8000C"

            schede_html += f"""
            <div class="categoria-blocco">
                <button class="toggle-btn" onclick="toggleCategoria(this)">
                    <span class="freccia">➤</span> <span class="etichetta">{html_escape.escape(cat)}</span>
                </button>

                <div class="riepilogo-riga" style="color:{colore_totale};">
                    {simbolo_totale} Totale: <strong>€{totale_cat:.2f}</strong> • Voci: <strong>{len(voci)}</strong>
                </div>
                <div class="categoria-contenuto" style="display:none;">
                    <ul>{voce_html}</ul>
                </div>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>📊 Risultati Avanzati</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                    margin: 0;
                }}
                h2 {{
                    text-align: center;
                    font-size: 1.5em;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .categoria-blocco {{
                    background: #fff;
                    border-radius: 8px;
                    box-shadow: 0 0 6px rgba(0,0,0,0.1);
                    margin: 20px auto;
                    max-width: 600px;
                    padding: 10px;
                }}
                .toggle-btn {{
                    background: none;
                    border: none;
                    font-size: 1.1em;
                    font-weight: bold;
                    width: 100%;
                    text-align: left;
                    cursor: pointer;
                    padding: 8px 0;
                    color: #0078D4;
                }}
                .categoria-contenuto ul {{
                    list-style: none;
                    padding-left: 0;
                    margin-top: 10px;
                }}
                .categoria-contenuto li {{
                    font-size: 1em;
                    margin: 8px 0;
                }}
                ul.totali {{
                    background: #fff;
                    padding: 16px;
                    border-radius: 8px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.1);
                    max-width: 600px;
                    margin: 0 auto 30px auto;
                    list-style: none;
                }}
                ul.totali li {{
                    font-size: 1.1em;
                    margin: 8px 0;
                }}
                .back {{
                    display: block;
                    text-align: center;
                    font-size: 1em;
                    text-decoration: none;
                    background: #0078D4;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    max-width: 100%;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    margin-top: 20px;
                }}
                .back:hover {{
                    background-color: #005ea6;
                }}
                .riepilogo-riga {{
                    font-size: 0.95em;
                    color: #555;
                    margin-top: 6px;
                    margin-bottom: 10px;
                    text-align: left;
                    padding-left: 4px;
                }}
                .pulsanti-finali {{
                    max-width: 600px;
                    margin: 30px auto 0 auto;
                }}

            </style>
            <script>
            function toggleCategoria(btn) {{
                const riepilogo = btn.nextElementSibling;
                const content = riepilogo.nextElementSibling;
                const isVisible = content.style.display === "block";
                content.style.display = isVisible ? "none" : "block";
                const freccia = btn.querySelector(".freccia");
                freccia.textContent = isVisible ? "➤" : "▼";
            }}
            </script>
        </head>
        <body>
            <h2>📊 Totali Esplorazione</h2>
            <ul class="totali">
                <li><strong>Entrate totali:</strong> €{entrate_totali:.2f}</li>
                <li><strong>Uscite totali:</strong> €{uscite_totali:.2f}</li>
                <li><strong style="color:{colore};">Saldo:</strong> €{saldo:.2f}</li>
            </ul>
            <h2>🔎 Risultati per Categoria</h2>
            {schede_html if schede_html else "<p style='text-align:center;'>Nessuna voce trovata per questi criteri.</p>"}
            <div class="pulsanti-finali">
                <form method="get" action="/menu_esplora">
                    <input type="submit" value="🔙 Torna al Menu Esplora"
                    style="background-color: #0078D4; color: white; border: none;
                    font-size: 1.1em; padding: 12px; border-radius: 6px;
                    cursor: pointer; width: 100%; margin-bottom: 10px;">
                </form>

                <form method="get" action="/">
                    <input type="submit" value="🏠 Torna alla Home"
                    style="background-color: #0078D4; color: white; border: none;
                    font-size: 1.1em; padding: 12px; border-radius: 6px;
                    cursor: pointer; width: 100%;">
                </form>
            </div>

        </body>
        </html>
        """
        return html

    def html_form(self):
        categorie_options = "\n".join(
            f"<option value='{c}'>{c}</option>" for c in self.categorie
        )
        today = datetime.date.today().isoformat()

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Casa Facile Web</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    margin: 0;
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f4f4f4;
                }}
                header {{
                    background: #0078D4;
                    color: white;
                    padding: 20px 0;
                    position: relative;
                }}
                .header-title {{
                    text-align: center;
                    font-size: 1.5em;
                }}
                .menu-button {{
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    font-size: 1.6em;
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                }}
                .dropdown {{
                    position: absolute;
                    top: 45px;
                    left: 10px;
                    background-color: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    border-radius: 4px;
                    display: none;
                    z-index: 999;
                }}
                .dropdown a {{
                    display: block;
                    padding: 10px 20px;
                    text-decoration: none;
                    color: #0078D4;
                    font-weight: bold;
                }}
                .dropdown a:hover {{
                    background-color: #f0f0f0;
                }}
                main {{
                    padding: 20px;
                    max-width: 600px;
                    margin: auto;
                }}
                form {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.05);
                }}
                label {{
                    display: block;
                    margin-top: 10px;
                    font-weight: bold;
                }}
                input, select {{
                    width: 100%;
                    padding: 10px;
                    margin-top: 5px;
                    margin-bottom: 15px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    box-sizing: border-box;
                }}
                input[type="submit"] {{
                    background-color: #0078D4;
                    color: white;
                    border: none;
                    cursor: pointer;
                    font-size: 1em;
                    border-radius: 6px;
                    padding: 12px;
                }}
                input[type="submit"]:hover {{
                    background-color: #005ea6;
                }}
                .input-errore {{
                    border: 2px solid red;
                }}

                .errore-msg {{
                    color: #a94442;
                    font-size: 0.95em;
                    display: none;
                    margin-top: -10px;
                    margin-bottom: 10px;
                }}

                input.input-errore + .errore-msg {{
                    display: block;
                }}
            </style>
            <script>
                function toggleMenu() {{
                    const menu = document.getElementById("extraMenu");
                    menu.style.display = (menu.style.display === "block") ? "none" : "block";
                }}
                document.addEventListener("click", function(event) {{
                    const menu = document.getElementById("extraMenu");
                    const isClickInside = event.target.closest(".menu-button, #extraMenu");
                    if (!isClickInside) {{
                        menu.style.display = "none";
                    }}
                }});
            </script>
            
            <script>
              document.addEventListener("DOMContentLoaded", function () {{
                const form = document.getElementById("spesaForm");
                const msg = document.getElementById("successMessage");

                form.addEventListener("submit", function () {{
                  // Ottieni i valori dal form
                  const categoria = form.categoria.value;
                  const importo = form.importo.value;

                  // Mostra il messaggio con categoria e importo
                  msg.textContent = `✅ Inserita: ${{categoria}} €${{importo}}`;
                  msg.style.color = "black";
                  msg.style.display = "block";

                  setTimeout(() => {{
                    msg.style.display = "none";
                  }}, 8000);
                }});
              }});
            </script>

        </head>
        <body>
            <header>
                <button class="menu-button" onclick="toggleMenu()">☰</button>
                <div id="extraMenu" class="dropdown">
                    <a href="/lista">📈 Elenca/Modifica</a>
                    <a href="/stats">📊 Report Mese</a>
                    <a href="/report_annuo">📅 Report Annuale</a>
                    <a href="/menu_esplora">🔍 Esplora</a>
                    <a href="/utenze?anno=2025">💧 Utenze</a>
                    <a href="/logoff">🔓 Logout</a>
                </div>
                <div class="header-title">🏠 Casa Facile Web</div>
            </header>
            <main>
            
                <div id="successMessage" style="display:none; color:green;">✅ Inserito</div>

                <form method="post" action="/" id="spesaForm">
                    <label for="data">Data:</label>
                    <input name="data" type="date" value="{today}">
                
                    <label for="categoria">Categoria:</label>
                    <select name="categoria">{categorie_options}</select>

                    <label for="descrizione">Descrizione:</label>
                    <input name="descrizione" placeholder="Es: Pizza o bollette">

                    <label for="importo">Importo:</label>
                    <input
                        name="importo"
                        type="number"
                        step="0.01"
                        min="0.01"
                        required
                        placeholder="Es: 12.50"
                        oninvalid="this.classList.add('input-errore')"
                        oninput="this.classList.remove('input-errore')"
                    >
                    <span class="errore-msg">⚠️ Inserisci un importo valido</span>

                    <label for="tipo">Tipo:</label>
                    <select name="tipo">
                        <option value="Uscita">Uscita</option>
                        <option value="Entrata">Entrata</option>
                    </select>

                    <input type="submit" value="➕ Aggiungi Voce">
                </form>
            </main>
        </body>
        </html>
        """


    def genera_html_utenze(self, percorso_db, anno):
        from datetime import datetime
        utenze = ["Acqua", "Luce", "Gas"]
        if not os.path.exists(percorso_db):
            return """
            <!DOCTYPE html>
            <html>
            <head><title>Errore DB</title><meta charset="utf-8"></head>
            <body style='font-family:Arial; background:#fff; padding:20px;'>
              <h2 style='color:#b00;'>❌ Errore database</h2>
              <p style='font-size:3.2em;'>⚠️ Il file <strong>UTENZE_DB</strong> non esiste o è vuoto.</p>
              <a href='/' style='display:inline-block; margin-top:20px; font-size:3em; text-decoration:none; color:#0078D4;'>🔙 Torna alla Home</a>
            </body>
            </html>
            """
        try:
            with open(percorso_db, "r", encoding="utf-8") as f:
                contenuto = f.read().strip()
                if not contenuto:
                    return "<p style='font-size: 3.3em; font-weight: bold; color: #C00;'>⚠️ Il file database è vuoto.</p>"
                data = json.loads(contenuto)
        except Exception as e:
            return f"<p>❌ Errore nel file JSON: {e}</p>"

        letture = data.get("letture_salvate", {})
        anno_corrente = datetime.now().year
        anni_disponibili = [str(anno_corrente - i) for i in range(6)]
        select_html = "<form><label for='anno'>🗓️ Scegli anno:</label> "
        select_html += "<select id='anno' onchange=\"location.href='/utenze?anno=' + this.value\">"
        for a in anni_disponibili:
            selected = " selected" if a == str(anno) else ""
            select_html += f"<option value='{a}'{selected}>{a}</option>"
        select_html += "</select></form>"

        oggi = datetime.now()

        html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
      <meta charset="utf-8">
      <title>💧 Utenze — {anno}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {{
          margin: 0;
          font-family: 'Segoe UI', sans-serif;
          background-color: #f4f4f4;
        }}
        header {{
          background: #0078D4;
          color: white;
          padding: 20px 0;
          position: relative;
        }}
        .header-title {{
          text-align: center;
          font-size: 1.5em;
        }}
        .menu-button {{
          position: absolute;
          top: 10px;
          left: 10px;
          font-size: 1.6em;
          background: none;
          border: none;
          color: white;
          cursor: pointer;
        }}
        .dropdown {{
          position: absolute;
          top: 45px;
          left: 10px;
          background-color: white;
          box-shadow: 0 4px 8px rgba(0,0,0,0.15);
          border-radius: 4px;
          display: none;
          z-index: 999;
        }}
        .dropdown a {{
          display: block;
          padding: 10px 20px;
          text-decoration: none;
          color: #0078D4;
          font-weight: bold;
        }}
        .dropdown a:hover {{
          background-color: #f0f0f0;
        }}
        main {{
          padding: 20px;
          max-width: 700px;
          margin: auto;
        }}
        .utenza-title {{
          cursor: pointer;
          padding: 10px;
          background: #0078D4;
          color: white;
          border-radius: 4px;
          margin-top: 20px;
        }}
        .utenza-content {{
          display: none;
          background: white;
          padding: 10px;
          border-radius: 6px;
          box-shadow: 0 0 4px rgba(0,0,0,0.05);
          margin-bottom: 20px;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 0.9em;
        }}
        th, td {{
          border: 1px solid #ccc;
          padding: 8px;
          text-align: center;
        }}
        th {{
          background: #0078D4;
          color: white;
        }}
        .teardown {{
          background: #f9f9f9;
          margin-top: 10px;
          font-size: 0.9em;
          padding: 8px;
          border-radius: 4px;
        }}
        .back {{
          display: block;
          text-align: center;
          font-size: 1em;
          text-decoration: none;
          background: #0078D4;
          color: white;
          padding: 10px;
          border-radius: 4px;
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
          margin: 20px auto;
          width: 200px;
        }}
        .back:hover {{
          background-color: #005ea6;
        }}
      </style>
      <script>
        function toggleMenu() {{
          const menu = document.getElementById("extraMenu");
          menu.style.display = (menu.style.display === "block") ? "none" : "block";
        }}
        function toggle(id) {{
          const el = document.getElementById(id);
          el.style.display = (el.style.display === "none") ? "block" : "none";
        }}
        document.addEventListener("click", function(event) {{
          const menu = document.getElementById("extraMenu");
          if (!event.target.closest(".menu-button, #extraMenu")) {{
            menu.style.display = "none";
          }}
        }});
      </script>
    </head>
    <body>
      <header>
        <button class="menu-button" onclick="toggleMenu()">☰</button>
        <div id="extraMenu" class="dropdown">
          <a href="/lista">📈 Elenca/Modifica</a>
          <a href="/stats">📊 Report Mese</a>
          <a href="/report_annuo">📅 Report Annuale</a>
          <a href="/menu_esplora">🔍 Esplora</a>
          <a href="/utenze?anno=2025">💧 Utenze</a>
          <a href="/logoff">🔓 Logout</a>
        </div>
        <div class="header-title">💧 Utenze — Anno {anno}</div>
      </header>
      <main>
        {select_html}
    """

        for utenza in utenze:
            righe = letture.get(utenza, {}).get(str(anno), [])
            uid = f"utenza_{utenza.lower()}"
            html += f"<div class='utenza-title' onclick=\"toggle('{uid}')\">▶️ {utenza}</div><div id='{uid}' class='utenza-content'>"
            if righe:
                total = 0.0
                consumi = []
                html += "<table><tr><th>Mese</th><th>Prec</th><th>Att</th><th>Consumo</th></tr>"
                for riga in righe:
                    try:
                        mese, prec, att, cons = riga
                        prec, att, cons = float(prec), float(att), float(cons)
                        total += cons
                        consumi.append(cons)
                        html += f"<tr><td>{mese}</td><td>{prec:.2f}</td><td>{att:.2f}</td><td>{cons:.2f}</td></tr>"
                    except:
                        html += f"<tr><td colspan='4'>⚠️ Errore dati: {riga}</td></tr>"
                media = total / len(consumi) if consumi else 0
                variazioni = [consumi[i] - consumi[i - 1] for i in range(1, len(consumi))]
                ultima = variazioni[-1] if variazioni else 0
                html += "</table>"
                html += f"""
    <div class='teardown'>
    🔢 Totale: <strong>{total:.2f}</strong><br>
    📊 Media mensile: <strong>{media:.2f}</strong><br>
    📈 Ultima variazione: <strong>{ultima:+.2f}</strong><br>
    📅 Mesi registrati: <strong>{len(consumi)}</strong>
    </div>
    """
            else:
                html += "<p><i>Nessun dato disponibile.</i></p>"
            html += "</div>"

        html += f"""
        <a href="/" class="back">🏠 Torna alla Home</a>
      </main>
    </body>
    </html>
    """
        return html
     
    def pagina_menu_esplora(self): 
        mesi = [f"{m:02d}" for m in range(1, 13)]
        categorie = sorted(set(self.categorie))
        anno_corrente = datetime.date.today().year
        anni = [str(anno) for anno in range(anno_corrente, anno_corrente - 10, -1)]
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <title>🔎 Esplorazione avanzata</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f4f4f4;
                    padding: 0;
                    margin: 0;
                }}
                header {{
                    background: #0078D4;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    font-size: 1.5em;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                }}
                main {{
                    padding: 20px;
                    max-width: 600px;
                    margin: auto;
                }}
                form {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.08);
                }}
                label {{
                    font-weight: bold;
                    display: block;
                    margin-top: 15px;
                    margin-bottom: 5px;
                }}
                input, select {{
                    width: 100%;
                    padding: 10px;
                    font-size: 1em;
                   border: 1px solid #ccc;
                    border-radius: 4px;
                    box-sizing: border-box;
                }}
                button {{
                    margin-top: 25px;
                    width: 100%;
                    background: #0078D4;
                    color: white;
                    padding: 12px;
                    font-size: 1.1em;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                }}
                button:hover {{
                    background: #005ea6;
                }}
            </style>
        </head>
        <body>
            <header>🔎 Esplorazione avanzata</header>
            <main>
                <form method='get' action='/cerca_avanzata'>

                    <label for='categoria'>Categoria:</label>
                    <select name='categoria'>
                        <option value=''>-- Qualsiasi --</option>
                        {''.join(f"<option value='{html.escape(cat)}'>{html.escape(cat)}</option>" for cat in categorie)}
                    </select>

                    <label for='tipo'>Tipo:</label>
                    <select name='tipo'>
                        <option value=''>-- Qualsiasi --</option>
                        <option value='Entrata'>Entrata</option>
                        <option value='Uscita'>Uscita</option>
                    </select>

                    <label for='anno'>Anno:</label>
                    <select name='anno'>
                        <option value=''>-- Tutti --</option>
                        {''.join(f"<option value='{html.escape(a)}'>{html.escape(a)}</option>" for a in anni)}
                    </select>

                    <label for='mese'>Mese:</label>
                    <select name='mese'>
                        <option value=''>-- Tutti --</option>
                        {''.join(f"<option value='{m}'>{m}</option>" for m in mesi)}
                    </select>

                    <label>Importo minimo (€):</label>
                    <input type='number' name='min_importo' step='0.01'>

                    <label>Importo massimo (€):</label>
                    <input type='number' name='max_importo' step='0.01'>

                    <label>Testo libero (descrizione, tipo, importo):</label>
                    <input type='text' name='q' placeholder='es: pane, bolletta, 25.00'>

                    <button type='submit'>🔍 Avvia Esplorazione</button>
                </form>
                <form method="get" action="/">
                    <input type="submit" value="🏠 Torna alla Home"
                    style="background-color: #0078D4; color: white; border: none;
                    font-size: 1.1em; padding: 12px; border-radius: 6px;
                    cursor: pointer; width: 100%; margin-top: 10px;">
                </form>
            </main>
        </body>
        </html>
        """
        return html_code

    def pagina_statistiche_annuali_web(self):
        import datetime
        oggi = datetime.date.today()
        # Calcola il report e converte in HTML
        raw = self.calcola_statistiche_annuali_pura().strip().replace("\n", "<br>")
        report = raw.replace("🔹 Mese corrente", "<strong><span style='color:#c43b2e;'>🗓️ Mese corrente</span></strong>") \
                    .replace("🔹 Da inizio anno", "<strong><span style='color:#d48300;'>📆 Da inizio anno</span></strong>") \
                    .replace("🔹 Proiezione fine anno", "<strong><span style='color:#0078D4;'>📊 Proiezione fine anno</span></strong>") \
                    .replace("✅ Risparmio previsto", "<strong><span style='color:green;'>💰 Risparmio previsto</span></strong>") \
                    .replace("⚠️ Possibile extra spesa", "<strong><span style='color:red;'>📉 Possibile extra spesa</span></strong>")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>📊 Report Annuale — {oggi.strftime('%d/%m/%Y')}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    margin: 0;
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f4f4f4;
                }}
                header {{
                    background: #0078D4;
                    color: white;
                    padding: 20px 0;
                    position: relative;
                }}
                .header-title {{
                    text-align: center;
                    font-size: 1.5em;
                }}
                .menu-button {{
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    font-size: 1.6em;
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                }}
                .dropdown {{
                    position: absolute;
                    top: 45px;
                    left: 10px;
                    background-color: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    border-radius: 4px;
                    display: none;
                    z-index: 999;
                }}
                .dropdown a {{
                    display: block;
                    padding: 10px 20px;
                    text-decoration: none;
                    color: #0078D4;
                    font-weight: bold;
                }}
                .dropdown a:hover {{
                    background-color: #f0f0f0;
                }}
                main {{
                    padding: 20px;
                    max-width: 700px;
                    margin: auto;
                }}
                .report-box {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.1);
                    white-space: pre-wrap;
                    word-break: break-word;
                    font-size: 1em;
                    line-height: 1.5em;
                    font-weight: bold;
                }}
                .back {{
                    display: block;
                    text-align: center;
                    font-size: 1em;
                    text-decoration: none;
                    background: #0078D4;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    margin: 20px auto;
                    width: 200px;
                }}
                .back:hover {{
                    background-color: #005ea6;
                }}
            </style>
            <script>
                function toggleMenu() {{
                    const menu = document.getElementById("extraMenu");
                    menu.style.display = (menu.style.display === "block") ? "none" : "block";
                }}
                document.addEventListener("click", function(event) {{
                    const menu = document.getElementById("extraMenu");
                    if (!event.target.closest(".menu-button, #extraMenu")) {{
                        menu.style.display = "none";
                    }}
                }});
            </script>
        </head>
        <body>
            <header>
                <button class="menu-button" onclick="toggleMenu()">☰</button>
                <div id="extraMenu" class="dropdown">
                    <a href="/lista">📈 Elenca/Modifica</a>
                    <a href="/stats">📊 Report Mese</a>
                    <a href="/report_annuo">📅 Report Annuale</a>
                    <a href="/menu_esplora">🔍 Esplora</a>
                    <a href="/utenze?anno=2025">💧 Utenze</a>
                    <a href="/logoff">🔓 Logout</a>
                </div>
                <div class="header-title">📊 Report del {oggi.strftime('%d/%m/%Y')}</div>
            </header>
            <main>
                <div class="report-box">{report}</div>
                <a href="/" class="back">🏠 Torna alla Home</a>
            </main>
        </body>
        </html>
        """

    def calcola_statistiche_annuali_pura(self):
        from datetime import date
        oggi = date.today()
        anno_corr = oggi.year
        anno_prec = anno_corr - 1
        mese_corr = oggi.month
        tot_mese_corr = tot_mese_prec = 0.0
        tot_anno_corr = tot_anno_prec = 0.0
        stima_anno_prec = 0.0
        for giorno, voci in self.spese.items():
            for voce in voci:
                if len(voce) < 4:
                    continue
                categoria, descrizione, importo, tipo = voce[:4]
                if tipo != "Uscita":
                    continue
                if giorno.year == anno_corr and giorno.month == mese_corr:
                    tot_mese_corr += importo
                if giorno.year == anno_prec and giorno.month == mese_corr:
                    tot_mese_prec += importo
                if giorno.year == anno_corr and giorno <= oggi:
                    tot_anno_corr += importo
                if giorno.year == anno_prec and giorno <= oggi.replace(year=anno_prec):
                    tot_anno_prec += importo
                if giorno.year == anno_prec:
                    stima_anno_prec += importo
        # Proiezione fine anno corrente
        giorni_passati = (oggi - date(anno_corr, 1, 1)).days + 1
        giorni_totali = 365
        perc_anno = giorni_passati / giorni_totali
        stima_anno_corr = tot_anno_corr / perc_anno if perc_anno else tot_anno_corr
        variazione_mese_pct = (
            (tot_mese_corr - tot_mese_prec) / tot_mese_prec * 100
            if tot_mese_prec else 0.0
        )
        differenza = stima_anno_prec - stima_anno_corr
        # Formattazione report
        report = f"""📊 Bilancio dinamico Previsionale
        
 Analisi delle spese attuali e stima
 fino a fine {anno_corr}
 
 🔹 Mese corrente ({mese_corr:02}/{anno_corr})
  • Spese {anno_corr}:  € {tot_mese_corr:,.2f}
  • Spese {anno_prec}:  € {tot_mese_prec:,.2f}
  • Variazione mensile: {variazione_mese_pct:+.1f}%

 🔹 Da inizio anno (01/01 → oggi)
  • Totale {anno_corr}:  € {tot_anno_corr:,.2f}
  • Totale {anno_prec}:  € {tot_anno_prec:,.2f}

 🔹 Proiezione fine anno
  • Spesa stimata {anno_corr}: € {stima_anno_corr:,.2f}  
  • (⏳ {perc_anno:.1%} dell’anno trascorso)
  • Spesa effettiva {anno_prec}: € {stima_anno_prec:,.2f}
    """

        if differenza > 0:
            report += f"\n✅ Risparmio previsto: € {differenza:,.2f} \n   se mantieni questo ritmo 💰"
        else:
            report += f"\n⚠️ Possibile extra spesa: € {abs(differenza):,.2f}\n   rispetto al {anno_prec} 🪙"

        return report.strip()

    def stats_mensili_html(self):
        mesi_it = {
            "January": "gennaio", "February": "febbraio", "March": "marzo",
            "April": "aprile", "May": "maggio", "June": "giugno",
            "July": "luglio", "August": "agosto", "September": "settembre",
            "October": "ottobre", "November": "novembre", "December": "dicembre"
        }

        oggi = datetime.date.today()
        mese_en = oggi.strftime('%B')
        mese_it_corrente = mesi_it.get(mese_en, mese_en)
        titolo_mese = f"{mese_it_corrente} {oggi.year}"
        entrate = 0.0
        uscite = 0.0
        entrate_categorie = {}
        uscite_categorie = {}
        entrate_dettaglio = {}
        uscite_dettaglio = {}
        for d, voci in self.spese.items():
            if d.month == oggi.month and d.year == oggi.year:
                for voce in voci:
                    categoria, descrizione, importo, tipo = voce
                    if tipo == "Entrata":
                        entrate += importo
                        entrate_categorie[categoria] = entrate_categorie.get(categoria, 0.0) + importo
                        entrate_dettaglio.setdefault(categoria, []).append((descrizione, importo))
                    else:
                        uscite += importo
                        uscite_categorie[categoria] = uscite_categorie.get(categoria, 0.0) + importo
                        uscite_dettaglio.setdefault(categoria, []).append((descrizione, importo))
        saldo = entrate - uscite
        colore = "#3c763d" if saldo >= 0 else "#a94442"

        def genera_html_categorie(categorie, dettaglio, prefix):
            html = "<ul>"
            for cat, totale in sorted(categorie.items()):
                voci = dettaglio.get(cat, [])
                dettagli_id = f"{prefix}_{cat.replace(' ', '_')}"
                toggle = f"onclick=\"document.getElementById('{dettagli_id}').classList.toggle('hidden')\""
                html += f"""
                <li>
                    <strong>{cat}:</strong> €{totale:.2f}
                    {'<button ' + toggle + '>🔽 Dettagli</button>' if len(voci) > 1 else ''}
                    <ul id="{dettagli_id}" class="hidden">
                        {''.join(f'<li>{desc} — €{imp:.2f}</li>' for desc, imp in voci)}
                    </ul>
                </li>
               """
            html += "</ul>"
            return html
        categorie_uscite_html = genera_html_categorie(uscite_categorie, uscite_dettaglio, "uscite")
        categorie_entrate_html = genera_html_categorie(entrate_categorie, entrate_dettaglio, "entrate")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Statistiche Mese Corrente</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                h2 {{
                    color: #333;
                    text-align: center;
                    font-size: 1.5em;
                   margin-bottom: 20px;
                }}
                ul {{
                    list-style-type: none;
                    padding: 0;
                    background: #fff;
                    border-radius: 8px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.1);
                    padding: 20px;
                    max-width: 100%;
                    margin-bottom: 20px;
                }}
                li {{
                    font-size: 1.1em;
                    margin: 10px 0;
                }}
                ul ul {{
                    background: #f9f9f9;
                    padding: 10px 20px;
                    border-radius: 4px;
                    margin-top: 10px;
                    margin-left: 20px;
                }}
                .hidden {{
                    display: none;
                }}
                button {{
                    margin-left: 12px;
                    font-size: 0.9em;
                    background: none;
                    border: none;
                    color: #0078D4;
                    cursor: pointer;
                }}
                button:hover {{
                    text-decoration: underline;
                }}
                a {{
                    display: block;
                    text-align: center;
                    font-size: 1em;
                    text-decoration: none;
                    background: #0078D4;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    max-width: 100%;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                a:hover {{
                    background-color: #005ea6;
                }}
            </style>
        </head>
       <body>
            <h2>📊 Statistiche di {titolo_mese}</h2>
            <ul>
                <li><strong>Entrate Totali:</strong> €{entrate:.2f}</li>
                <li><strong>Uscite Totali:</strong> €{uscite:.2f}</li>
                <li><strong style="color:{colore};">Saldo:</strong> €{saldo:.2f}</li>
            </ul>
            <h2>🧮 Uscite per Categoria</h2>
            {categorie_uscite_html}
            <h2>📥 Entrate per Categoria</h2>
            {categorie_entrate_html}
            <a href="/">🏠 Torna alla Home</a>
        </body>
        </html>
    """

    def html_lista_spese_mensili(self):
        oggi = datetime.date.today()
        mese_it = {
            "January": "gennaio", "February": "febbraio", "March": "marzo",
            "April": "aprile", "May": "maggio", "June": "giugno",
            "July": "luglio", "August": "agosto", "September": "settembre",
            "October": "ottobre", "November": "novembre", "December": "dicembre"
        }[oggi.strftime('%B')]

        schede_html = ""
        for d in sorted(self.spese.keys(), reverse=True):
            voci = self.spese[d]
            if d.month == oggi.month and d.year == oggi.year:
                for idx, voce in enumerate(voci):
                    categoria, descrizione, importo, tipo = voce
                    data_str = d.strftime('%d-%m-%Y')
                    schede_html += f"""
                    <div class="spesa">
                        <div><strong>Data:</strong> {data_str}</div>
                        <div><strong>Categoria:</strong> {categoria}</div>
                        <div><strong>Descrizione:</strong> {descrizione}</div>
                        <div><strong>Importo:</strong> €{importo:.2f}</div>
                        <div><strong>Tipo:</strong> {tipo}</div>
                        <div style="margin-top:10px; display:flex; gap:12px;">
                           <!-- Modifica -->
                           <form method="get" action="/modifica">
                               <input type="hidden" name="data" value="{data_str}">
                               <input type="hidden" name="idx" value="{idx}">
                               <button type="submit" style="color:#0078D4; background:none; border:none; font-size:1em;">✏️ Modifica</button>
                           </form>

                           <!-- Cancella -->
                           <form onsubmit="
                               event.preventDefault();
                               fetch('/cancella', {{
                                   method: 'POST',
                                   headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                                   body: 'data={data_str}&idx={idx}'
                               }}).then(function() {{
                                   window.location.href='/lista';
                               }});
                          ">
                               <button type="submit" style="color:red; background:none; border:none; font-size:1em;">❌ Cancella</button>
                           </form>
                       </div>
                    </div>
                    """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>📊 {NAME} — Spese di {mese_it} {oggi.year}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                    margin: 0;
                }}
                h2 {{
                    text-align: center;
                    font-size: 1.5em;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .spesa {{
                    background: #fff;
                    border-radius: 8px;
                    padding: 16px;
                    box-shadow: 0 0 6px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }}
                .spesa div {{
                    margin: 8px 0;
                    font-size: 1em;
                }}
                a {{
                    text-decoration: none;
                    font-size: 1.3em;
                    margin-right: 12px;
                }}
                .back {{
                    display: block;
                    text-align: center;
                    font-size: 1em;
                    text-decoration: none;
                    background: #0078D4;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    max-width: 100%;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    margin-top: 20px;
                }}
                .back:hover {{
                    background-color: #005ea6;
                }}
            </style>
        </head>
        <body>
            <h2>💰 Spese di {mese_it} {oggi.year}</h2>
            {schede_html}
            <a href="/" class="back">🔙 Torna alla Home</a>
        </body>
        </html>
        """
 
    def modifica_voce_form(self, params):
        from datetime import datetime
        data = params.get("data", [""])[0]
        idx = int(params.get("idx", ["0"])[0])
        d_obj = datetime.strptime(data, "%d-%m-%Y").date()
        voce = self.spese[d_obj][idx]
        categoria_corrente, descrizione, importo, tipo = voce

        categorie_options = "\n".join(
            f"<option value='{c}' {'selected' if c == categoria_corrente else ''}>{c}</option>"
            for c in sorted(self.categorie)
        )

        return f"""
        <html><head><meta charset="utf-8"><title>Modifica</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Segoe UI, sans-serif;
                padding: 20px;
                background: #f4f4f4;
                margin: 0;
            }}
            .container {{
                max-width: 500px;
                margin: auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 8px rgba(0,0,0,0.1);
            }}
            label {{
                display: block;
                margin: 12px 0 4px;
                font-weight: bold;
            }}
            input, select {{
                width: 100%;
                padding: 8px;
                font-size: 1em;
                margin-bottom: 12px;
                box-sizing: border-box;
            }}
            button {{
                background: #0078D4;
                color: white;
                border: none;
                padding: 10px;
                font-size: 1em;
                border-radius: 6px;
                width: 100%;
            }}
            a {{
                display: block;
                margin-top: 20px;
                text-align: center;
                text-decoration: none;
                color: #0078D4;
            }}
        </style>
        </head>
        <body>
            <div class="container">
                <h2 style="text-align:center;">✏️ Modifica voce del {data}</h2>
                <form method="post" action="/salva_modifica">
                    <input type="hidden" name="data" value="{data}">
                    <input type="hidden" name="idx" value="{idx}">

                    <label for="categoria">Categoria</label>
                    <select name="categoria" required>
                        {categorie_options}
                    </select>

                    <label for="descrizione">Descrizione</label>
                    <input name="descrizione" value="{descrizione}">

                    <label for="importo">Importo (€)</label>
                    <input name="importo" type="number" step="0.01" min="0.01" value="{importo}" required>

                    <label for="tipo">Tipo</label>
                    <select name="tipo">
                        <option value="Entrata" {"selected" if tipo == "Entrata" else ""}>Entrata</option>
                        <option value="Uscita" {"selected" if tipo != "Entrata" else ""}>Uscita</option>
                    </select>

                    <button type="submit">💾 Salva</button>
                </form>
                <a href="/lista" style="background:#0078D4;color:#fff;padding:10px;border-radius:6px;text-align:center;display:block;text-decoration:none;">🔙 Torna alla lista</a>
            </div>
        </body></html>
        """

    def salva_modifica_voce(self, params):
        from datetime import datetime
        data = params.get("data", [""])[0]
        idx = int(params.get("idx", ["0"])[0])
        cat = params.get("categoria", [""])[0]
        descr = params.get("descrizione", [""])[0]
        imp = float(params.get("importo", ["0"])[0])
        tipo = params.get("tipo", ["Uscita"])[0]
        d_obj = datetime.strptime(data, "%d-%m-%Y").date()
        self.spese[d_obj][idx] = [cat, descr, imp, tipo]

    def cancella_voce_web(self, data_str, idx):
        try:
            d_obj = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except Exception as e:
            print(f"❌ Data non valida: {data_str} → {e}")
            return

        if d_obj not in self.spese or idx >= len(self.spese[d_obj]):
            print(f"❌ Voce non trovata per cancellazione")
            return
        voce_eliminata = self.spese[d_obj].pop(idx)
        print(f"🗑️ Voce eliminata:", voce_eliminata)
        self.save_db()
        self.carica_db_web()
        self.refresh_gui()

    def aggiungi_voce_web(self, voce):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                dati = json.load(f)
        except Exception:
            dati = {"spese": []}
        try:
            d_obj = datetime.datetime.strptime(voce["date"], "%Y-%m-%d").date()
            data_str = d_obj.strftime("%d-%m-%Y")
            voce["date"] = data_str  # modifica la voce stessa
        except Exception as e:
            print(f"❌ Data non valida: {voce['date']} → {e}")
            return
        for giorno in dati["spese"]:
            if giorno["date"] == data_str:
                giorno["entries"].append(voce)
                break
        else:
            dati["spese"].append({
                "date": data_str,
                "entries": [voce]
            })
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=2, ensure_ascii=False)
        self.carica_db_web()
        self.refresh_gui()
 
    def carica_db_web(self):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                dati = json.load(f)
        except Exception as e:
            print(f"❌ Errore lettura DB: {e}")
            return

        self.spese = {}
        for giorno in dati.get("spese", []):
            try:
                d = datetime.datetime.strptime(giorno["date"], "%d-%m-%Y").date()
                entries = []
                for e in giorno["entries"]:
                    voce = (
                        e.get("categoria", ""),
                        e.get("descrizione", ""),
                        float(e.get("importo", 0.0)),
                        e.get("tipo", "Uscita"),
                        *([e["id_ricorrenza"]] if "id_ricorrenza" in e else [])
                    )
                    entries.append(voce)
                self.spese[d] = entries
            except Exception as ex:
                print(f"⚠️ Errore parsing giorno {giorno.get('date')}: {ex}")

    def refresh_gui(self):
        self.update_stats()
        self.aggiorna_combobox_categorie()
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self.update_spese_mese_corrente()
        self.colora_giorni_spese()

    def aggiorna_gui_da_db(self):
        self.spese = {}
        for giorno in self.db.get("spese", []):
            try:
                d = datetime.datetime.strptime(giorno["date"], "%d-%m-%Y").date()
                entries = []
                for e in giorno["entries"]:
                    voce = (
                        e.get("categoria", ""),
                        e.get("descrizione", ""),
                        float(e.get("importo", 0.0)),
                        e.get("tipo", "Uscita")
                    )
                    if "id_ricorrenza" in e:
                        voce += (e["id_ricorrenza"],)
                    entries.append(voce)
                self.spese[d] = entries
            except Exception as ex:
                print(f"⚠️ Errore parsing giorno: {giorno.get('date')} → {ex}")

    def save_db_web(self, db=None):
        if db is None:
            db = self.db
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            print("💾 Database salvato correttamente.")
            self.aggiorna_gui_da_db()        
        except Exception as e:
            print("❌ Errore salvataggio DB:", e)


    def _attiva_timer_inattivita(self):
        if self._timer_inattivita:
            self.after_cancel(self._timer_inattivita)
        self._timer_inattivita = self.after(self._timeout_inattivita, self._iconizza_finestra)
        # 🔄 Rileva interazione e resetta il timer
        self.bind_all("<Motion>", lambda e: self._reset_inattivita())
        self.bind_all("<Key>", lambda e: self._reset_inattivita())
        self.bind_all("<Button>", lambda e: self._reset_inattivita())
    def _attiva_timer_inattivita(self):
        if self._timer_inattivita:
            self.after_cancel(self._timer_inattivita)
        self._timer_inattivita = self.after(self._timeout_inattivita, self._iconizza_finestra)
        # 🔄 Rileva interazione e resetta il timer
        self.bind_all("<Motion>", lambda e: self._reset_inattivita())
        self.bind_all("<Key>", lambda e: self._reset_inattivita())
        self.bind_all("<Button>", lambda e: self._reset_inattivita())
    def _reset_inattivita(self):
        if self.state() == "iconic":
            self.deiconify()  # 👈 se era minimizzata, torna visibile
        self._attiva_timer_inattivita()  # 🔁 riparte il ciclo
    def _iconizza_finestra(self):
        #print("💤 Inattività: finestra iconificata.")
        self.iconify()
        self.mostra_avviso_iconizzata()
        self._attiva_timer_inattivita()  # 🔁 riattiva il ciclo
    def mostra_avviso_iconizzata(self):
        splash = tk.Toplevel()
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        width, height = 400, 130
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = screen_width - width - 1  # ↪ angolo in alto a destra
        y = 30
        splash.geometry(f"{width}x{height}+{x}+{y}")
        splash.configure(bg="#7fc2c7")
        label = tk.Label(
            splash,
            text = f"💤 {NAME} v.{VERSION}\n\nFinestra minimizzata per inattività.\n\nPassa il mouse qui o clicca l’icona sulla barra per riaprirla.",
            font=("Arial", 9, "bold"),
            bg="#7fc2c7"
        )
        label.pack(expand=True, pady=30)
        splash.update()
        splash.after(3000, splash.destroy)  # ❌ Chiude dopo 3 secondi

    def check_aggiornamento_con_api(self):
        from datetime import datetime, timedelta
        try:
            # ⏳ Controllo rimando
            if os.path.exists(RIMANDA_FILE):
                with open(RIMANDA_FILE, "r") as f:
                    data = json.load(f)
                    rimanda = datetime.strptime(data.get("rimanda_fino", ""), "%Y-%m-%d")
                    if datetime.today() < rimanda:
                        print(f"⏳ Rimandato fino al {rimanda.date()}")
                        return

            # 🌐 Controllo API GitHub
            api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
            params = {"path": NOME_FILE}
            response = requests.get(api_url, params=params, timeout=5)
            response.raise_for_status()

            commit_date = response.json()[0]["commit"]["committer"]["date"]
            remote_time = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(microsecond=0)
    
            if not os.path.exists(NOME_FILE):
                self.show_custom_warning("File mancante", "⚠️ Il file locale non esiste. Aggiornamento consigliato.")
                return

            local_time = datetime.utcfromtimestamp(os.path.getmtime(NOME_FILE)).replace(microsecond=0)

            # 📅 Se serve aggiornare, mostra finestra
            if remote_time.date() > local_time.date():
                win = tk.Toplevel(self)
                win.title("🔄 Aggiornamento disponibile")
                win.bind("<Escape>", lambda e: win.destroy())
                win.resizable(False, False)
                # ⏱️ Etichetta del countdown
                label_timer = tk.Label(win, text="⏱️ Chiusura automatica tra 60 secondi", fg="gray", font=("Helvetica", 10, "bold"))
                label_timer.pack()
                msg = (
                    "🆕 È stato rilevato un possibile aggiornamento.\n\n"
                    f"📡 Ultima versione online: {remote_time}\n"
                    f"🖥️ Versione attuale locale: {local_time}\n\n"
                    "👉 Vuoi procedere con l'aggiornamento adesso?"
                )
                tk.Label(win, text=msg, wraplength=360, padx=20, pady=10).pack()

                frame_bottoni = tk.Frame(win)
                frame_bottoni.pack(pady=10)

                stile = dict(width=12, padx=8, pady=6, fg="black")



                # ⏱️ Funzione countdown con colore dinamico
                def aggiorna_timer(secondi_rimasti):
                    if secondi_rimasti > 0:
                        colore = "red" if secondi_rimasti <= 10 else "gray"
                        label_timer.config(text=f"⏱️ Chiusura automatica tra {secondi_rimasti} secondi", fg=colore)
                        win.after(1000, aggiorna_timer, secondi_rimasti - 1)
                    else:
                        label_timer.config(text="⏱️ Chiusura automatica...")
            
                timeout_id = win.after(60000, win.destroy)
                aggiorna_timer(60)

                def annulla_timeout():
                    win.after_cancel(timeout_id)

                def aggiorna():
                    annulla_timeout()
                    win.destroy()
                    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{NOME_FILE.replace(' ', '%20')}"
                    self.aggiorna(url, NOME_FILE)
                    # 🧹 Eliminazione del file rimando
                    if os.path.exists(RIMANDA_FILE):
                        try:
                            os.remove(RIMANDA_FILE)
                            print("🧹 File rimando eliminato dopo aggiornamento.")
                        except Exception as err:
                            print(f"⚠️ Errore durante l'eliminazione del file rimando: {err}")

                def chiudi():
                    annulla_timeout()
                    win.destroy()

                def rimanda():
                    annulla_timeout()
                    nuova_data = datetime.today() + timedelta(days=15)
                    with open(RIMANDA_FILE, "w") as f:
                       json.dump({"rimanda_fino": nuova_data.strftime("%Y-%m-%d")}, f)
                    print(f"⏳ Rimandato fino al {nuova_data.date()}")
                    data_formattata = nuova_data.date().strftime("%d/%m/%Y")
                    self.show_custom_warning("Aggiornamento Rimandato", f"⏳ Aggiornamento Rimandato fino al {data_formattata}")
                    win.destroy()

                tk.Button(frame_bottoni, text="🔄 AGGIORNA", command=aggiorna, bg="#A9DFBF", **stile).pack(side="left", padx=5)
                tk.Button(frame_bottoni, text="❌ CHIUDI", command=chiudi, bg="#F5B7B1", **stile).pack(side="left", padx=5)
                tk.Button(frame_bottoni, text="⏳ RIMANDA", command=rimanda, bg="#F9E79F", **stile).pack(side="left", padx=5)

                win.withdraw()
                win.update_idletasks()
                min_w, min_h = 460, 210
                w = max(win.winfo_width(), min_w)
                h = max(win.winfo_height(), min_h)
                x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
                y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
                win.geometry(f"{w}x{h}+{x}+{y}")

                if self.winfo_exists():
                    win.after(100, lambda: win.grab_set())

                win.transient(self)
                win.focus_set()
                win.deiconify()
                win.wait_window()

        except ConnectionError:
            print("🌐 Connessione assente o GitHub non raggiungibile.")
        except RequestException as e:
            print(f"⚠️ Errore HTTP: {e}")
        except Exception as e:
            print(f"⚠️ Errore generico: {e}")

    def cambio_modalita(self, messaggio="⚠️ Riavvio l’interfaccia!"):
        if hasattr(self, "popup_avviso") and self.popup_avviso and self.popup_avviso.winfo_exists():
            return  # Se già aperto

        self.popup_avviso = tk.Toplevel(self)
        self.popup_avviso.title("Avviso")
        self.popup_avviso.resizable(False, False)

        larghezza_popup = 360
        altezza_popup = 100
        schermo_larghezza = self.winfo_screenwidth()
        schermo_altezza = self.winfo_screenheight()
        pos_x = (schermo_larghezza // 2) - (larghezza_popup // 2)
        pos_y = (schermo_altezza // 2) - (altezza_popup // 2)

        self.popup_avviso.geometry(f"{larghezza_popup}x{altezza_popup}+{pos_x}+{pos_y}")
        self.popup_avviso.configure(bg="#AA0000")
        self.popup_avviso.transient(self)
        self.popup_avviso.grab_set()

        label = tk.Label(
            self.popup_avviso,
            text=messaggio,
            bg="#AA0000",
            fg="white",
            font=("Arial", 11, "bold"),
            wraplength=320,
            justify="center"
        )
        label.pack(expand=True, fill="both", padx=20, pady=16)

        self.popup_avviso.bind("<Escape>", lambda e: self.popup_avviso.destroy())
        self.popup_avviso.after(3000, self.popup_avviso.destroy)

        self.popup_avviso.update()  # 🔧 Forza il rendering
        self.popup_avviso.wait_window()

def leggi_modalita():
    # Se il file non esiste, crealo con modalità semplice
    if not os.path.exists(CONFIG):
        try:
            with open(CONFIG, "w") as f:
                json.dump({"modalita": "semplice"}, f)
        except:
            return "semplice"
    # Leggi la modalità dal file
    try:
        with open(CONFIG, "r") as f:
            dati = json.load(f)
            return dati.get("modalita", "semplice")
    except:
        return "semplice"
def salva_modalita(modalita):
    try:
        with open(CONFIG, "w") as f:
            json.dump({"modalita": modalita}, f)
    except Exception as e:
        print("Errore nel salvataggio:", e)


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

def mostra_splash_dipendenze():
    splash = tk.Tk()
    splash.overrideredirect(True)
    width, height = 360, 110
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    splash.configure(bg="white")

    label = tk.Label(splash, text="Controllo delle dipendenze in corso...",
                     font=("Arial", 12), bg="white")
    label.pack(expand=True, pady=30)
    splash.update()
    return splash

def install_tkcalendar():
    """Controlla se tkcalendar è installato e, se mancante, lo installa automaticamente, quindi restituisce Calendar e DateEntry"""
    package_name = "tkcalendar"
    try:
        from tkcalendar import Calendar, DateEntry
    except ImportError:
        print(f"{package_name} non è installato. Installazione in corso...")
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        print(f"{package_name} installato con successo!")
        from tkcalendar import Calendar, DateEntry
    return Calendar, DateEntry

def install_psutil():
    try:
        import psutil
    except ImportError:
        print("psutil non trovato. Installazione in corso...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
        import psutil
    return psutil
psutil = install_psutil()

def install_requests():
    try:
        import requests
    except ImportError:
        print("requests non trovato. Installazione in corso...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
        import requests
    return requests
requests = install_requests()
from requests.exceptions import ConnectionError, RequestException

def install_win32_libraries():
    """Installa pywin32 su Windows se necessario e restituisce i moduli win32 richiesti"""
    if platform.system() != "Windows":
        print("Sistema operativo non Windows: installazione non necessaria.")
        return None, None, None

    try:
        import win32print
        import win32api
        import win32con
    except ImportError:
        print("Moduli win32 non trovati. Installazione di pywin32 in corso...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pywin32"], check=True)
        print("pywin32 installato con successo.")
        #import win32print
        #import win32api
        #import win32con

    #return win32print, win32api, win32con #carica all'occorrenza

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
    splash = tk.Tk()
    splash.overrideredirect(True)
    width, height = 360, 110
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    splash.configure(bg="white")
    label = tk.Label(
        splash,
        text= f"{NAME}\nApp già in esecuzione!",
        font=("Arial", 12, "bold"),
        fg="white",
        bg="#b22222",
        justify="center"
    )
    label.pack(expand=True, fill="both")  # 🔺 Occupa tutto lo spazio
    splash.after(5000, splash.destroy)
    splash.mainloop()
    return splash


if __name__ == "__main__":
    # 🔧 Prepara tutto PRIMA dello splash
    # stderr per far partire webserver su win (bastardo)
    try:
        sys.stderr = open(os.devnull, 'w')
    except Exception:
        pass
        
    print(f"""
    📘 {NAME} — Guida agli argomenti da riga di comando
    
    ▶ auto       Avvio automatico con impostazione password:

      • auto <password>   → usa la password specificata
      • auto ""           → imposta una password vuota
      • auto              → usa la password predefinita (es. "return")

    ▶ noweb      Avvia senza interfaccia web (disabilita server locale)

    Esempi:
    {NAME}.pyw auto 1234      # imposta password “1234”
    {NAME}.pyw auto ""       # password vuota
    {NAME}.pyw auto          # password automatica (definita da utente)
    {NAME}.pyw noweb         # GUI senza web server
    {NAME}.pyw auto "" noweb # password vuota + niente web

    """)

    popup = mostra_splash_dipendenze()
    Calendar, DateEntry = install_tkcalendar()
    install_psutil()
    install_requests()
    install_win32_libraries()
    popup.after(1, popup.destroy)
    check_single_instance()
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
            
    #Porta WebServer
    if not os.path.exists(PORTA_DB):
        with open(PORTA_DB, "w") as file:
            file.write("8081")
        PORTA = 8081
    else:
        with open(PORTA_DB, "r") as file:
            PORTA = int(file.read().strip())
            
    def avvia_app(splash):
        splash.destroy()
        app = GestioneSpese()
        app.mainloop()

    splash = tk.Tk()
    splash.overrideredirect(True)
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    width = 360
    height = 110
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    label = tk.Label(splash, text=f"Caricamento {NAME}...", font=("Arial", 12))
    label.pack(expand=True)
    splash.after(800, lambda: avvia_app(splash))
    splash.mainloop()

