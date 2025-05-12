import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# Date de début pour avoir suffisamment de données pour la normalisation et la MM7ans
start_date = "1990-01-01" # Essayons de garder une date de début lointaine
normalization_date_str = "2000-01-01"

# Téléchargement des données
try:
    sp500_tr_data = yf.download('^SP500TR', start=start_date, progress=False, auto_adjust=True)
    gold_data = yf.download('GC=F', start=start_date, progress=False, auto_adjust=True)

    if sp500_tr_data.empty:
        print("Impossible de télécharger les données pour le S&P 500 TR (^SP500TR).")
        exit()
    if gold_data.empty:
        print("Impossible de télécharger les données pour l'Or (GC=F).")
        exit()

except Exception as e:
    print(f"Une erreur est survenue lors du téléchargement des données: {e}")
    exit()

# Sélectionner la colonne 'Close' et la renommer.
if 'Close' not in sp500_tr_data.columns:
    print("La colonne 'Close' est manquante pour le S&P 500 TR.")
    exit()
sp500_close_raw = sp500_tr_data['Close']
if isinstance(sp500_close_raw, pd.DataFrame):
    print("Avertissement: Plusieurs colonnes 'Close' trouvées pour S&P 500 TR (^SP500TR), utilisation de la première.")
    sp500_series = sp500_close_raw.iloc[:, 0].rename('SP500_TR')
else:
    sp500_series = sp500_close_raw.rename('SP500_TR')

if 'Close' not in gold_data.columns:
    print("La colonne 'Close' est manquante pour l'Or.")
    exit()
gold_close_raw = gold_data['Close']
if isinstance(gold_close_raw, pd.DataFrame):
    print("Avertissement: Plusieurs colonnes 'Close' trouvées pour l'Or (GC=F), utilisation de la première.")
    gold_series = gold_close_raw.iloc[:, 0].rename('Gold')
else:
    gold_series = gold_close_raw.rename('Gold')

df = pd.DataFrame({'SP500_TR': sp500_series, 'Gold': gold_series})
df.dropna(inplace=True)

if df.empty:
    print("Aucune donnée commune trouvée après la fusion et suppression des NaN. Vérifiez les tickers ou la période.")
    exit()

df['Ratio_SP500TR_Gold'] = df['SP500_TR'] / df['Gold']

# Normalisation base 100
try:
    normalization_date = pd.to_datetime(normalization_date_str)
    
    # Si la date de normalisation demandée est avant la première date disponible dans df
    if normalization_date < df.index.min():
        actual_normalization_date = df.index.min()
        print(f"La date de normalisation {normalization_date_str} est antérieure aux données disponibles. Utilisation de la première date disponible : {actual_normalization_date.strftime('%Y-%m-%d')}")
    # Si la date de normalisation demandée est après la dernière date disponible dans df (moins probable ici)
    elif normalization_date > df.index.max():
        actual_normalization_date = df.index.max() # ou une autre logique si cela arrive
        print(f"La date de normalisation {normalization_date_str} est postérieure aux données disponibles. Utilisation de la dernière date disponible : {actual_normalization_date.strftime('%Y-%m-%d')}")
    else:
        # Comportement existant pour trouver la date la plus proche
        try:
            idx_loc = df.index.get_loc(normalization_date)
            actual_normalization_date = df.index[idx_loc]
        except KeyError:
            idx_loc = df.index.get_loc(normalization_date, method='nearest')
            actual_normalization_date = df.index[idx_loc]
            print(f"Note: La date exacte {normalization_date_str} n'a pas de données. Utilisation de {actual_normalization_date.strftime('%Y-%m-%d')} pour la normalisation.")

    ratio_at_normalization_date = df.loc[actual_normalization_date, 'Ratio_SP500TR_Gold']

    if pd.isna(ratio_at_normalization_date) or ratio_at_normalization_date == 0:
        print(f"Valeur du ratio non valide ({ratio_at_normalization_date}) à la date de normalisation {actual_normalization_date.strftime('%Y-%m-%d')}. Impossible de normaliser.")
        exit()

    df['Ratio_Normalized'] = (df['Ratio_SP500TR_Gold'] / ratio_at_normalization_date) * 100
except KeyError as e:
    print(f"Erreur de clé lors de la recherche de la date de normalisation: {e}. ")
    exit()
except Exception as e:
    print(f"Erreur lors de la normalisation : {e}")
    exit()

# Calcul de la moyenne mobile à 7 ans
window_7_years = 7 * 252
df['MA_7_ans'] = df['Ratio_Normalized'].rolling(window=window_7_years).mean()

# Tracé du graphique
plt.figure(figsize=(14, 8))
plt.plot(df.index, df['Ratio_Normalized'], label=f'Ratio S&P500 TR / Or (Base 100 au {actual_normalization_date.strftime("%d/%m/%Y")})', color='navy', zorder=2)
plt.plot(df.index, df['MA_7_ans'], label='Moyenne Mobile 7 ans du ratio', color='orange', zorder=2)

# Hachurage des périodes
# Trouver le premier index valide pour la moyenne mobile pour commencer le hachurage
first_valid_ma_iloc = df['MA_7_ans'].first_valid_index()
if first_valid_ma_iloc is not pd.NaT: # S'assurer qu'il y a des valeurs valides pour la MA
    start_iloc = df.index.get_loc(first_valid_ma_iloc)

    # Périodes pour privilégier S&P 500 (Ratio > MA) - Vert
    start_period_iloc = 0 
    in_period = False
    for i in range(start_iloc, len(df)):
        ratio_val = df['Ratio_Normalized'].iloc[i]
        ma_val = df['MA_7_ans'].iloc[i]
        
        if pd.isna(ratio_val) or pd.isna(ma_val): # Passer si l'une des valeurs est NaN
            if in_period: # Si on était dans une période, la terminer
                 plt.axvspan(df.index[start_period_iloc], df.index[i-1], facecolor='green', alpha=0.2, zorder=1)
                 in_period = False
            continue

        if not in_period:
            if ratio_val > ma_val:
                start_period_iloc = i
                in_period = True
        else: # in_period == True
            if ratio_val < ma_val:
                plt.axvspan(df.index[start_period_iloc], df.index[i-1], facecolor='green', alpha=0.2, zorder=1)
                in_period = False
    if in_period: # Si la période continue jusqu'à la fin
        plt.axvspan(df.index[start_period_iloc], df.index[-1], facecolor='green', alpha=0.2, zorder=1)

    # Périodes pour privilégier l'Or (Ratio < MA) - Jaune
    start_period_iloc = 0
    in_period = False
    for i in range(start_iloc, len(df)):
        ratio_val = df['Ratio_Normalized'].iloc[i]
        ma_val = df['MA_7_ans'].iloc[i]

        if pd.isna(ratio_val) or pd.isna(ma_val):
            if in_period:
                 plt.axvspan(df.index[start_period_iloc], df.index[i-1], facecolor='yellow', alpha=0.2, zorder=1)
                 in_period = False
            continue
            
        if not in_period:
            if ratio_val < ma_val:
                start_period_iloc = i
                in_period = True
        else: # in_period == True
            if ratio_val > ma_val:
                plt.axvspan(df.index[start_period_iloc], df.index[i-1], facecolor='yellow', alpha=0.2, zorder=1)
                in_period = False
    if in_period: # Si la période continue jusqu'à la fin
        plt.axvspan(df.index[start_period_iloc], df.index[-1], facecolor='yellow', alpha=0.2, zorder=1)

plt.title('Ratio S&P 500 (Dividendes Réinvestis) / Or vs. Moyenne Mobile 7 ans')
plt.xlabel('Date\nPériode verte: privilégier S&P500 TR | Période jaune: privilégier Or')
plt.ylabel(f'Valeur du ratio (Base 100 au {actual_normalization_date.strftime("%d/%m/%Y")})')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()