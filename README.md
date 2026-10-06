# Tableau de bord des ventes — boutique de vêtements

Dashboard interactif construit avec **Python, pandas, Plotly et Streamlit**, à partir des ventes (fictives) d'une boutique de vêtements sur 21 mois.

## Ce qu'il montre
- Chiffres clés : chiffre d'affaires, commandes, panier moyen, part des ventes en ligne, clients uniques
- Évolution mensuelle du chiffre d'affaires, boutique vs en ligne
- Ventes par catégorie et top 10 des produits
- Saisonnalité : quelle catégorie se vend quel mois (aide à planifier le stock)
- Poids des meilleurs clients et ventes par jour de la semaine
- Filtres par période, catégorie et canal ; export CSV des données filtrées

## Lancer en local
```bash
python3 -m venv env && source env/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Le dashboard s'ouvre sur http://localhost:8501.

## Auteur
Elvis Agbo Komlavi — Étudiant M1 Data Science & IA (Coda)
