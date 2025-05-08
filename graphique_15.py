import yfinance as yfinance
import matplotlib.pyplot as pyplot

gold = yfinance.download('GC=F', period="max")
tbond = yfinance.download('ZN=F', period="max")

goldvstbond = gold.div(tbond.rename(columns={'ZN=F': 'GC=F'}), fill_value=None).dropna()*36.98;

goldvstbond['MA7an'] = goldvstbond['Close'].rolling(window=1750).mean()

pyplot.figure(figsize=(12.8, 7.2))

pyplot.plot(goldvstbond['Close'], color='red', label='Ratio or et marché obligataire US (base 100 au 21/09/2000)')
pyplot.plot(goldvstbond['MA7an'], color='blue', label='Moyenne mobile à 7 ans du ratio')

pyplot.title('Graphique n°15 - Règle de décision or ou marché obligataire')
pyplot.legend()
pyplot.grid(True)
pyplot.xlabel("En période jaune il privilégier l\'or, en période bleu il faut privilégier les obligations américaines à 10 ans", color='grey')


start = 0
writing = 0
for i in range( 0, len(goldvstbond)-1 ):
        if writing:
            if goldvstbond.iloc[i,5] > goldvstbond.iloc[i,0] :
                pyplot.axvspan(goldvstbond.index[start], goldvstbond.index[i], facecolor='yellow', alpha=0.2)
                writing = 0
        else:
            if goldvstbond.iloc[i,5] < goldvstbond.iloc[i,0] :  
                start = i
                writing = 1
if writing == 1:
    pyplot.axvspan(goldvstbond.index[start], goldvstbond.index[i], facecolor='yellow', alpha=0.2)
    
start = 0
writing = 0
for i in range( 0, len(goldvstbond)-1 ):
        if writing:
            if goldvstbond.iloc[i,5] < goldvstbond.iloc[i,0] :
                pyplot.axvspan(goldvstbond.index[start], goldvstbond.index[i], facecolor='blue', alpha=0.2)
                writing = 0
        else:
            if goldvstbond.iloc[i,5] > goldvstbond.iloc[i,0] :  
                start = i
                writing = 1
if writing == 1:
    pyplot.axvspan(goldvstbond.index[start], goldvstbond.index[i], facecolor='blue', alpha=0.2)

#print (goldvstbond['Close'].iloc[0]) # pour vérifier le premier point à la bonne date et à la base 100

pyplot.show()
