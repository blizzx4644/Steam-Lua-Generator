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
        """
        Génère des fichiers .lua en utilisant la liste officielle des AppIDs Steam
        """
        self.depot_keys_url = depot_keys_url
        self.appid_list_url = appid_list_url
        self.depot_keys = {}
        self.app_list = {}
        self.app_names = {}
        self.cancelled = False
        
    def load_depot_keys(self, progress_callback=None) -> Dict[str, str]:
        """Charge les depot keys"""
        if progress_callback:
            progress_callback("📥 Chargement des depot keys...", 0)
        
        response = requests.get(self.depot_keys_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunks = []
        
        for chunk in response.iter_content(chunk_size=8192):
            if self.cancelled:
                return {}
            chunks.append(chunk)
            downloaded += len(chunk)
            if progress_callback and total_size > 0:
                progress = (downloaded / total_size) * 100
                progress_callback(f"📥 Téléchargement depot keys: {downloaded//1024}KB / {total_size//1024}KB", progress)
        
        self.depot_keys = json.loads(b''.join(chunks))
        
        if progress_callback:
            progress_callback(f"✅ {len(self.depot_keys):,} depot keys chargées", 100)
        
        return self.depot_keys
    
    def load_appid_list(self, progress_callback=None) -> Dict[int, str]:
        """Charge la liste officielle des AppIDs Steam"""
        if progress_callback:
            progress_callback("📥 Chargement de la liste AppIDs Steam...", 0)
        
        response = requests.get(self.appid_list_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunks = []
        
        for chunk in response.iter_content(chunk_size=8192):
            if self.cancelled:
                return {}
            chunks.append(chunk)
            downloaded += len(chunk)
            if progress_callback and total_size > 0:
                progress = (downloaded / total_size) * 100
                progress_callback(f"📥 Téléchargement AppIDs: {downloaded//1024}KB / {total_size//1024}KB", progress)
        
        data = json.loads(b''.join(chunks))
        
        for app in data['applist']['apps']:
            self.app_list[app['appid']] = app['name']
            self.app_names[app['appid']] = app['name']
        
        if progress_callback:
            progress_callback(f"✅ {len(self.app_list):,} applications Steam chargées", 100)
        
        return self.app_list
    
    def find_best_appid_for_depot(self, depot_id: int) -> Optional[int]:
        """
        Trouve le meilleur AppID pour un depot
        
        Règles:
        1. Cherche un AppID exactement égal au depot (rare mais existe)
        2. Cherche l'AppID dans un range de -10 à +50 du depot
        3. Priorité aux AppIDs plus proches
        4. Ignore l'AppID 0 qui est invalide
        """
        # Vérifier si le depot lui-même est un AppID
        if depot_id in self.app_list and depot_id > 0:
            return depot_id
        
        best_appid = None
        min_distance = float('inf')
        
        # Chercher dans un range raisonnable
        search_range = range(max(1, depot_id - 50), depot_id + 10)
        
        for appid in search_range:
            if appid in self.app_list and appid > 0:  # Ignorer AppID 0
                distance = abs(depot_id - appid)
                
                # Privilégier les AppIDs inférieurs au depot (plus logique)
                if appid <= depot_id:
                    distance = distance * 0.8  # Bonus pour AppID inférieur
                
                if distance < min_distance:
                    min_distance = distance
                    best_appid = appid
        
        return best_appid
    
    def smart_depot_mapping(self, max_gap: int = 50, progress_callback=None) -> Dict[int, List[int]]:
        """
        Mappe intelligemment les depots aux AppIDs
        """
        if progress_callback:
            progress_callback("🔗 Mapping intelligent des depots...", 0)
        
        depot_ids = sorted([int(did) for did in self.depot_keys.keys()])
        app_depots = defaultdict(list)
        
        # Filtrer les depots avec clé vide
        valid_depots = [
            did for did in depot_ids 
            if self.depot_keys[str(did)] and self.depot_keys[str(did)].strip()
        ]
        
        if progress_callback:
            progress_callback(f"🔍 {len(valid_depots):,} depots valides à traiter", 5)
        
        # Traiter depot par depot avec recherche individuelle
        mapped_count = 0
        unmapped_depots = []
        total = len(valid_depots)
        
        for i, depot_id in enumerate(valid_depots):
            if self.cancelled:
                return {}
            
            # Trouver le meilleur AppID pour ce depot
            appid = self.find_best_appid_for_depot(depot_id)
            
            if appid and appid > 0:
                app_depots[appid].append(depot_id)
                mapped_count += 1
            else:
                unmapped_depots.append(depot_id)
            
            if progress_callback and i % 1000 == 0:
                progress = 5 + (i / total) * 90
                progress_callback(f"🔗 Mapping: {i:,}/{total:,} depots traités", progress)
        
        # Regrouper les depots non mappés par proximité
        if unmapped_depots and progress_callback:
            progress_callback("🔧 Regroupement des depots sans AppID...", 95)
        
        if unmapped_depots:
            unmapped_depots.sort()
            current_group = [unmapped_depots[0]]
            
            for i in range(1, len(unmapped_depots)):
                if unmapped_depots[i] - unmapped_depots[i-1] <= max_gap:
                    current_group.append(unmapped_depots[i])
                else:
                    # Utiliser le plus petit ID du groupe comme AppID
                    group_appid = min(current_group)
                    if group_appid > 0:  # Ne pas créer de groupe avec AppID 0
                        app_depots[group_appid].extend(current_group)
                    current_group = [unmapped_depots[i]]
            
            # Dernier groupe
            if current_group:
                group_appid = min(current_group)
                if group_appid > 0:
                    app_depots[group_appid].extend(current_group)
        
        if progress_callback:
            msg = f"✅ Mapping terminé: {mapped_count:,} depots mappés, {len(app_depots):,} apps"
            progress_callback(msg, 100)
        
        return dict(app_depots)
    
    def generate_lua_file(self, app_id: int, depot_list: List[int], 
                         output_dir: str = "lua_output") -> str:
        """Génère un fichier .lua pour un AppID"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        lua_content = []
        lua_content.append(f"addappid({app_id})")
        
        # Trier les depots
        sorted_depots = sorted(depot_list)
        
        for depot_id in sorted_depots:
            key = self.depot_keys[str(depot_id)]
            # Ne pas ajouter les clés vides
            if key and key.strip():
                lua_content.append(f'addappid({depot_id},0,"{key}")')
        
        output_file = Path(output_dir) / f"{app_id}.lua"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lua_content))
        
        return str(output_file)
    
    def generate_all_lua_files(self, output_dir: str = "lua_output", 
                               max_gap: int = 50,
                               skip_unknown: bool = False,
                               save_mapping: bool = True,
                               progress_callback=None):
        """Génère tous les fichiers .lua avec mapping intelligent"""
        
        # Charger les données
        self.load_depot_keys(progress_callback)
        if self.cancelled:
            return None
        
        self.load_appid_list(progress_callback)
        if self.cancelled:
            return None
        
        # Créer le mapping
        app_depots = self.smart_depot_mapping(max_gap=max_gap, progress_callback=progress_callback)
        if self.cancelled:
            return None
        
        # Supprimer l'AppID 0 s'il existe
        if 0 in app_depots:
            del app_depots[0]
        
        # Générer les fichiers
        if progress_callback:
            progress_callback(f"📝 Génération des fichiers .lua...", 0)
        
        generated = 0
        skipped = 0
        total_depots = 0
        total = len(app_depots)
        
        mapping_data = {}
        stats = {
            'known_apps': 0,
            'unknown_apps': 0,
            'skipped_unknown': 0,
            'total_depots': 0
        }
        
        for app_id, depot_list in sorted(app_depots.items()):
            if self.cancelled:
                return None
            
            # Ne générer que si on a des depots valides
            valid_depots = [
                d for d in depot_list 
                if self.depot_keys[str(d)] and self.depot_keys[str(d)].strip()
            ]
            
            if not valid_depots:
                continue
            
            app_name = self.app_names.get(app_id, f"Unknown Game {app_id}")
            is_known = app_id in self.app_names
            
            should_generate = True
            if skip_unknown and not is_known:
                should_generate = False
                stats['skipped_unknown'] += 1
                skipped += 1
            else:
                self.generate_lua_file(app_id, valid_depots, output_dir)
                generated += 1
            
            if is_known:
                stats['known_apps'] += 1
            else:
                stats['unknown_apps'] += 1
            
            stats['total_depots'] += len(valid_depots)
            
            # On garde tout dans le mapping JSON pour référence, même si non généré
            mapping_data[str(app_id)] = {
                'name': app_name,
                'depots': [str(d) for d in valid_depots],
                'depot_count': len(valid_depots),
                'is_known_app': is_known,
                'file_generated': should_generate
            }
            
            total_depots += len(valid_depots)
            
            if progress_callback and (generated + skipped) % 100 == 0:
                progress = ((generated + skipped) / total) * 100
                progress_callback(f"📝 Traitement: {generated + skipped:,}/{total:,} apps", progress)
        
        # Sauvegarder le mapping
        if save_mapping:
            if progress_callback:
                progress_callback("💾 Sauvegarde du mapping...", 95)
            
            mapping_file = Path(output_dir) / "depot_mapping.json"
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)
            
            # Statistiques détaillées
            stats_file = Path(output_dir) / "statistics.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            readme_file = Path(output_dir) / "README.txt"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("FICHIERS LUA GÉNÉRÉS - STEAM DEPOT KEYS\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Fichiers générés: {generated:,}\n")
                f.write(f"Fichiers ignorés (Inconnus): {stats['skipped_unknown']:,}\n")
                f.write(f"Total apps trouvées: {len(app_depots):,}\n")
                f.write(f"  - Applications Steam connues: {stats['known_apps']:,}\n")
                f.write(f"  - Groupes non identifiés: {stats['unknown_apps']:,}\n")
                f.write(f"Total de depots: {stats['total_depots']:,}\n\n")
                
                f.write("QUALITÉ DU MAPPING:\n")
                f.write("-" * 80 + "\n")
                total_processed = generated + skipped
                if total_processed > 0:
                    quality = (stats['known_apps'] / total_processed) * 100
                    f.write(f"Précision: {quality:.1f}% des fichiers correspondent à des jeux connus\n\n")
                
                f.write("STRUCTURE DES FICHIERS:\n")
                f.write("-" * 80 + "\n")
                f.write("Chaque fichier {appid}.lua contient:\n")
                f.write("  - addappid({appid})          # ID de l'application\n")
                f.write("  - addappid({depot},0,\"key\")  # Chaque depot avec sa clé\n\n")
                
                f.write("TOP 30 DES APPLICATIONS AVEC LE PLUS DE DEPOTS:\n")
                f.write("-" * 80 + "\n")
                
                # Trier par nombre de depots
                sorted_apps = sorted(
                    mapping_data.items(),
                    key=lambda x: x[1]['depot_count'],
                    reverse=True
                )[:30]
                
                for app_id, info in sorted_apps:
                    known = "✓" if info['is_known_app'] else "?"
                    gen_status = "Généré" if info['file_generated'] else "Ignoré"
                    name = info['name'][:40]  # Limiter la longueur
                    f.write(f"[{known}] {app_id:<10} | {info['depot_count']:>3} depots | [{gen_status}] {name}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("Légende: [✓] = Jeu Steam connu | [?] = Groupe non identifié\n")
        
        if progress_callback:
            msg = f"✅ TERMINÉ! {generated:,} fichiers générés ({stats['skipped_unknown']:,} ignorés)"
            progress_callback(msg, 100)
        
        return mapping_data


class SteamDepotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Steam Depot Keys to Lua Generator")
        self.root.geometry("800x680")  # Hauteur légèrement augmentée pour la nouvelle option
        self.root.resizable(False, False)
        
        # Couleurs
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#0078d4"
        
        self.root.configure(bg=self.bg_color)
        
        self.generator = None
        self.generation_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2d2d2d", height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🎮 Steam Depot Keys to Lua Generator",
            font=("Segoe UI", 18, "bold"),
            bg="#2d2d2d",
            fg=self.fg_color
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Génération automatique avec mapping officiel des AppIDs Steam",
            font=("Segoe UI", 10),
            bg="#2d2d2d",
            fg="#888888"
        )
        subtitle_label.pack()
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Options
        options_frame = tk.LabelFrame(
            content_frame,
            text=" ⚙️ Options ",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            relief=tk.FLAT,
            bd=2
        )
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Output directory
        dir_frame = tk.Frame(options_frame, bg=self.bg_color)
        dir_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            dir_frame,
            text="Dossier de sortie:",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(side=tk.LEFT)
        
        self.output_dir_var = tk.StringVar(value="lua_output")
        output_entry = tk.Entry(
            dir_frame,
            textvariable=self.output_dir_var,
            font=("Segoe UI", 10),
            width=30,
            bg="#2d2d2d",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            bd=5
        )
        output_entry.pack(side=tk.LEFT, padx=10)
        
        # Max gap
        gap_frame = tk.Frame(options_frame, bg=self.bg_color)
        gap_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(
            gap_frame,
            text="Gap maximum entre depots:",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(side=tk.LEFT)
        
        self.max_gap_var = tk.IntVar(value=50)
        gap_spinbox = tk.Spinbox(
            gap_frame,
            from_=10,
            to=200,
            textvariable=self.max_gap_var,
            font=("Segoe UI", 10),
            width=10,
            bg="#2d2d2d",
            fg=self.fg_color,
            buttonbackground="#2d2d2d",
            relief=tk.FLAT,
            bd=5
        )
        gap_spinbox.pack(side=tk.LEFT, padx=10)

        # Skip unknown apps checkbox
        skip_frame = tk.Frame(options_frame, bg=self.bg_color)
        skip_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.skip_unknown_var = tk.BooleanVar(value=False)
        skip_check = tk.Checkbutton(
            skip_frame,
            text="Ne pas générer les fichiers pour les applications inconnues",
            variable=self.skip_unknown_var,
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor="#2d2d2d",
            activebackground=self.bg_color,
            activeforeground=self.fg_color
        )
        skip_check.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = tk.LabelFrame(
            content_frame,
            text=" 📊 Progression ",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            relief=tk.FLAT,
            bd=2
        )
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Status label
        self.status_label = tk.Label(
            progress_frame,
            text="Prêt à démarrer",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#2d2d2d',
            background=self.accent_color,
            darkcolor=self.accent_color,
            lightcolor=self.accent_color,
            bordercolor='#2d2d2d',
            thickness=25
        )
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="Custom.Horizontal.TProgressbar",
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Log
        log_label = tk.Label(
            progress_frame,
            text="📋 Journal:",
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        log_label.pack(fill=tk.X, padx=15, pady=(5, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            progress_frame,
            height=12,
            font=("Consolas", 9),
            bg="#1a1a1a",
            fg="#00ff00",
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            bd=5
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X)
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Démarrer la génération",
            font=("Segoe UI", 11, "bold"),
            bg=self.accent_color,
            fg=self.fg_color,
            activebackground="#005a9e",
            activeforeground=self.fg_color,
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.start_generation
        )
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.cancel_button = tk.Button(
            button_frame,
            text="❌ Annuler",
            font=("Segoe UI", 11, "bold"),
            bg="#d41e1e",
            fg=self.fg_color,
            activebackground="#a00000",
            activeforeground=self.fg_color,
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.cancel_generation,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        
    def log(self, message):
        """Ajoute un message au journal"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_progress(self, status, progress):
        """Met à jour la barre de progression et le statut"""
        self.status_label.config(text=status)
        self.progress_bar['value'] = progress
        self.log(status)
        
    def start_generation(self):
        """Démarre la génération dans un thread séparé"""
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        
        output_dir = self.output_dir_var.get()
        max_gap = self.max_gap_var.get()
        skip_unknown = self.skip_unknown_var.get()
        
        self.log("🎬 Démarrage de la génération...")
        self.log(f"📁 Dossier de sortie: {output_dir}")
        self.log(f"⚙️  Gap maximum: {max_gap}")
        self.log(f"👻 Ignorer applis inconnues: {'Oui' if skip_unknown else 'Non'}")
        self.log("")
        
        depot_keys_url = "https://raw.githubusercontent.com/SteamAutoCracks/ManifestHub/refs/heads/main/depotkeys.json"
        appid_list_url = "https://raw.githubusercontent.com/dgibbs64/SteamCMD-AppID-List/refs/heads/main/steamcmd_appid.json"
        
        self.generator = SteamDepotLuaGenerator(depot_keys_url, appid_list_url)
        
        def generation_task():
            try:
                result = self.generator.generate_all_lua_files(
                    output_dir=output_dir,
                    max_gap=max_gap,
                    skip_unknown=skip_unknown,
                    save_mapping=True,
                    progress_callback=self.update_progress
                )
                
                if result and not self.generator.cancelled:
                    self.log("")
                    self.log("=" * 60)
                    self.log("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
                    self.log("=" * 60)
                    messagebox.showinfo("Succès", f"Génération terminée!\n\nFichiers créés dans: {output_dir}/")
                elif self.generator.cancelled:
                    self.log("")
                    self.log("⚠️  Génération annulée par l'utilisateur")
                    messagebox.showwarning("Annulé", "La génération a été annulée.")
                    
            except Exception as e:
                self.log(f"\n❌ ERREUR: {str(e)}")
                messagebox.showerror("Erreur", f"Une erreur s'est produite:\n{str(e)}")
            
            finally:
                self.start_button.config(state=tk.NORMAL)
                self.cancel_button.config(state=tk.DISABLED)
        
        self.generation_thread = threading.Thread(target=generation_task, daemon=True)
        self.generation_thread.start()
        
    def cancel_generation(self):
        """Annule la génération en cours"""
        if self.generator:
            self.generator.cancelled = True
            self.log("\n⏳ Annulation en cours...")
            self.cancel_button.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = SteamDepotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()