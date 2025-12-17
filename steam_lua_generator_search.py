import json
import requests
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time

class SteamDepotLuaGenerator:
    def __init__(self, depot_keys_url: str, appid_list_url: str):
        self.depot_keys_url = depot_keys_url
        self.appid_list_url = appid_list_url
        self.depot_keys = {}
        self.app_list = {}
        self.app_names = {}
        self.app_depots = {} # Stockage du mapping
        self.cancelled = False
        
    def load_essential_data(self, progress_callback=None):
        """Charge les données nécessaires pour la recherche"""
        if progress_callback: progress_callback("📥 Chargement des clés...", 10)
        self.depot_keys = requests.get(self.depot_keys_url).json()
        
        if progress_callback: progress_callback("📥 Chargement des AppIDs...", 30)
        data = requests.get(self.appid_list_url).json()
        for app in data['applist']['apps']:
            self.app_list[app['appid']] = app['name']
            self.app_names[app['appid']] = app['name']
            
        if progress_callback: progress_callback("🔗 Création du mapping...", 60)
        self.app_depots = self.smart_depot_mapping(progress_callback=progress_callback)
        if progress_callback: progress_callback("✅ Prêt", 100)

    def find_best_appid_for_depot(self, depot_id: int) -> Optional[int]:
        if depot_id in self.app_list: return depot_id
        search_range = range(max(1, depot_id - 50), depot_id + 10)
        best_appid, min_distance = None, float('inf')
        for appid in search_range:
            if appid in self.app_list:
                distance = abs(depot_id - appid)
                if appid <= depot_id: distance *= 0.8
                if distance < min_distance:
                    min_distance, best_appid = distance, appid
        return best_appid

    def smart_depot_mapping(self, max_gap: int = 50, progress_callback=None) -> Dict[int, List[int]]:
        depot_ids = sorted([int(did) for did in self.depot_keys.keys()])
        app_depots = defaultdict(list)
        valid_depots = [did for did in depot_ids if self.depot_keys[str(did)]]
        
        for i, depot_id in enumerate(valid_depots):
            appid = self.find_best_appid_for_depot(depot_id)
            if appid: app_depots[appid].append(depot_id)
        return dict(app_depots)
    
    def generate_lua_file(self, app_id: int, depot_list: List[int], output_dir: str = "lua_output") -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        lua_content = [f"addappid({app_id})"]
        for depot_id in sorted(depot_list):
            key = self.depot_keys.get(str(depot_id))
            if key: lua_content.append(f'addappid({depot_id},0,"{key}")')
        
        output_file = Path(output_dir) / f"{app_id}.lua"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lua_content))
        return str(output_file)

class SteamDepotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Steam Depot Keys to Lua Generator")
        self.root.geometry("800x750") # Légèrement plus grand pour la liste
        self.root.resizable(False, False)
        
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#0078d4"
        self.root.configure(bg=self.bg_color)
        
        self.generator = SteamDepotLuaGenerator(
            "https://raw.githubusercontent.com/SteamAutoCracks/ManifestHub/refs/heads/main/depotkeys.json",
            "https://raw.githubusercontent.com/dgibbs64/SteamCMD-AppID-List/refs/heads/main/steamcmd_appid.json"
        )
        
        self.setup_ui()
        # Charger les données en arrière-plan au démarrage
        threading.Thread(target=lambda: self.generator.load_essential_data(self.update_progress), daemon=True).start()
        
    def setup_ui(self):
        # Header (Identique)
        header_frame = tk.Frame(self.root, bg="#2d2d2d", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🎮 Steam Depot Keys to Lua Generator", font=("Segoe UI", 18, "bold"), bg="#2d2d2d", fg=self.fg_color).pack(pady=10)
        
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # --- SECTION RECHERCHE (Nouveau) ---
        search_frame = tk.LabelFrame(content_frame, text=" 🔍 Recherche & Sélection Rapide ", font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.fg_color, relief=tk.FLAT)
        search_frame.pack(fill=tk.X, pady=(0, 15))

        search_input_frame = tk.Frame(search_frame, bg=self.bg_color)
        search_input_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        tk.Entry(search_input_frame, textvariable=self.search_var, font=("Segoe UI", 10), bg="#2d2d2d", fg="white", insertbackground="white", relief=tk.FLAT).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.btn_gen_sel = tk.Button(search_input_frame, text="Générer Sélection", font=("Segoe UI", 9, "bold"), bg=self.accent_color, fg="white", relief=tk.FLAT, command=self.generate_selected, cursor="hand2")
        self.btn_gen_sel.pack(side=tk.RIGHT, padx=(10, 0))

        self.results_list = tk.Listbox(search_frame, height=4, font=("Segoe UI", 9), bg="#1a1a1a", fg="#00ff00", selectbackground=self.accent_color, relief=tk.FLAT, bd=5)
        self.results_list.pack(fill=tk.X, padx=15, pady=5)

        # --- OPTIONS (Identique) ---
        options_frame = tk.LabelFrame(content_frame, text=" ⚙️ Options ", font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.fg_color, relief=tk.FLAT)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Champ Dossier
        dir_frame = tk.Frame(options_frame, bg=self.bg_color)
        dir_frame.pack(fill=tk.X, padx=15, pady=5)
        self.output_dir_var = tk.StringVar(value="lua_output")
        tk.Entry(dir_frame, textvariable=self.output_dir_var, font=("Segoe UI", 10), bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- PROGRESSION & LOGS (Identique) ---
        progress_frame = tk.LabelFrame(content_frame, text=" 📊 État ", font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.fg_color, relief=tk.FLAT)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.status_label = tk.Label(progress_frame, text="Chargement des données...", bg=self.bg_color, fg=self.fg_color, anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=15, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=15, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=8, font=("Consolas", 9), bg="#1a1a1a", fg="#00ff00", relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # --- BOUTONS (Identique) ---
        button_frame = tk.Frame(content_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X)
        self.start_button = tk.Button(button_frame, text="🚀 Tout Générer (En masse)", font=("Segoe UI", 11, "bold"), bg=self.accent_color, fg=self.fg_color, relief=tk.FLAT, pady=10, command=self.start_bulk)
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def update_progress(self, status, progress):
        self.status_label.config(text=status)
        self.progress_bar['value'] = progress
        self.root.update_idletasks()

    def on_search_change(self, *args):
        query = self.search_var.get().lower()
        self.results_list.delete(0, tk.END)
        if len(query) < 2: return
        count = 0
        for appid, depots in self.generator.app_depots.items():
            name = self.generator.app_names.get(appid, "Inconnu")
            if query in name.lower() or query in str(appid):
                self.results_list.insert(tk.END, f"{appid} | {name}")
                count += 1
            if count > 50: break

    def generate_selected(self):
        selection = self.results_list.curselection()
        if not selection: return
        item = self.results_list.get(selection[0])
        appid = int(item.split(" | ")[0])
        depots = self.generator.app_depots.get(appid)
        path = self.generator.generate_lua_file(appid, depots, self.output_dir_var.get())
        self.log(f"✅ Généré : {path}")

    def start_bulk(self):
        self.log("🎬 Démarrage de la génération totale...")
        threading.Thread(target=self.run_bulk_task, daemon=True).start()

    def run_bulk_task(self):
        total = len(self.generator.app_depots)
        for i, (appid, depots) in enumerate(self.generator.app_depots.items()):
            self.generator.generate_lua_file(appid, depots, self.output_dir_var.get())
            if i % 100 == 0:
                self.update_progress(f"Génération : {i}/{total}", (i/total)*100)
        self.update_progress("✅ Terminé !", 100)
        messagebox.showinfo("Succès", "Tous les fichiers ont été générés.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamDepotGUI(root)
    root.mainloop()