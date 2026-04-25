import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration des dossiers
SOURCE_DIR = Path("results_valide/results_csv/final")
FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

def load_data():
    all_data = []
    # Attention : j'ai corrigé "pluto_static" en "pluto_statique" selon tes dossiers précédents
    categories = ["raw", "pluto_dynamic", "pluto_static"]
    
    for cat in categories:
        cat_path = SOURCE_DIR / cat
        if not cat_path.exists():
            print(f"Attention : Le dossier {cat_path} n'existe pas.")
            continue
            
        for csv_file in cat_path.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                # Nettoyage immédiat des noms de colonnes pour éviter les erreurs d'espaces
                df.columns = df.columns.str.strip()
                
                if not df.empty:
                    program_name = csv_file.stem
                    row = df.iloc[0].to_dict()
                    row['program'] = program_name
                    row['method'] = cat
                    all_data.append(row)
            except Exception as e:
                print(f"Erreur sur {csv_file.name}: {e}")
                
    return pd.DataFrame(all_data)

def calculate_speedup(df):
    """Calcule le speedup par rapport à la méthode 'raw' pour chaque programme"""
    # 1. On sépare les temps 'raw' dans un dictionnaire {programme: temps_raw}
    raw_times = df[df['method'] == 'raw'].set_index('program')['score'].to_dict()
    
    def get_speedup(row):
        base_time = raw_times.get(row['program'])
        if base_time and row['score'] > 0:
            return base_time / row['score']
        return 1.0 # Par défaut si raw manquant

    df['speedup'] = df.apply(get_speedup, axis=1)
    return df

def plot_speedup_comparison(df):
    """Trace l'histogramme du Speedup"""
    plt.figure(figsize=(14, 8))
    sns.set_style("whitegrid")
    
    # Ordre explicite des barres pour chaque programme
    method_order = ["raw", "pluto_statique", "pluto_dynamique"]
    
    # Création du barplot
    # hue_order garantit que pour chaque programme, on a Raw, puis Static, puis Dynamic
    ax = sns.barplot(
        data=df, 
        x='program', 
        y='speedup', 
        hue='method', 
        hue_order=method_order,
        palette="viridis"
    )
    
    # Ajouter une ligne horizontale au niveau 1.0 (le seuil de référence raw)
    plt.axhline(1.0, color='red', linestyle='--', linewidth=1, label="Référence Raw")
    
    plt.title("Speedup par rapport à la version Raw (Plus haut est mieux)", fontsize=16)
    plt.ylabel("Speedup (Temps_Raw / Temps_Méthode)", fontsize=12)
    plt.xlabel("Programmes", fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(title="Méthode")
    
    # Ajouter les valeurs au-dessus des barres pour plus de clarté
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2fx', padding=3, fontsize=9)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "speedup_comparison.png")
    print("Graphique de speedup sauvegardé.")

def main():
    print("Chargement des données...")
    df = load_data()
    
    if df.empty:
        print("Aucune donnée trouvée. Vérifiez vos fichiers CSV.")
        return

    print("Calcul du speedup...")
    df = calculate_speedup(df)
    
    print(f"Génération du graphique pour {df['program'].nunique()} programmes...")
    plot_speedup_comparison(df)
    
    print(f"\nSuccès ! Le graphique est dans '{FIGURES_DIR}/speedup_comparison.png'.")

if __name__ == "__main__":
    main()