"""Tableau de bord des ventes d'une boutique de vêtements (données fictives).

Lancer : streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Tableau de bord des ventes", page_icon="📊", layout="wide")

COULEURS = {"Boutique": "#2563eb", "En ligne": "#f59e0b"}
MOIS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
           "juil.", "août", "sept.", "oct.", "nov.", "déc."]


@st.cache_data
def charger_donnees(chemin: Path) -> pd.DataFrame:
    df = pd.read_csv(chemin, parse_dates=["date"])
    df["mois"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["jour_semaine"] = df["date"].dt.dayofweek
    return df


def euros(x: float) -> str:
    return f"{x:,.0f} €".replace(",", " ")


def mois_label(ts: pd.Timestamp) -> str:
    return f"{MOIS_FR[ts.month - 1]} {ts.year}"


# ---------- Données ----------
fichier = Path(__file__).parent / "ventes_boutique_demo.csv"
if not fichier.exists():
    st.error("Fichier ventes_boutique_demo.csv introuvable : place-le dans le même dossier que app.py.")
    st.stop()
df = charger_donnees(fichier)

# ---------- Filtres ----------
st.sidebar.header("Filtres")
dmin, dmax = df["date"].min().date(), df["date"].max().date()
periode = st.sidebar.date_input("Période", value=(dmin, dmax), min_value=dmin, max_value=dmax)
if isinstance(periode, tuple) and len(periode) == 2:
    debut, fin = periode
else:
    debut, fin = dmin, dmax

categories = sorted(df["categorie"].unique())
cats = st.sidebar.multiselect("Catégories", categories, default=categories)
canaux = st.sidebar.multiselect("Canal de vente", ["Boutique", "En ligne"], default=["Boutique", "En ligne"])

f = df[(df["date"].dt.date >= debut) & (df["date"].dt.date <= fin)
       & df["categorie"].isin(cats) & df["canal"].isin(canaux)]

st.title("📊 Tableau de bord des ventes")
st.caption("Boutique de vêtements fictive · données de démonstration")

if f.empty:
    st.warning("Aucune vente pour ces filtres.")
    st.stop()

# ---------- Chiffres clés ----------
ca = f["montant"].sum()
nb_cmd = f["id_commande"].nunique()
panier = ca / nb_cmd
part_web = f.loc[f["canal"] == "En ligne", "montant"].sum() / ca
nb_clients = f["id_client"].nunique()

# Comparaison avec la même durée juste avant
duree = pd.Timestamp(fin) - pd.Timestamp(debut)
avant = df[(df["date"] < pd.Timestamp(debut)) & (df["date"] >= pd.Timestamp(debut) - duree - pd.Timedelta(days=1))
           & df["categorie"].isin(cats) & df["canal"].isin(canaux)]
delta_ca = None
if not avant.empty and len(avant["mois"].unique()) > 0:
    delta_ca = f"{(ca / avant['montant'].sum() - 1) * 100:+.1f} % vs période précédente"

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Chiffre d'affaires", euros(ca), delta_ca)
c2.metric("Commandes", f"{nb_cmd:,}".replace(",", " "))
c3.metric("Panier moyen", f"{panier:.2f} €")
c4.metric("Part des ventes en ligne", f"{part_web:.0%}")
c5.metric("Clients uniques", f"{nb_clients:,}".replace(",", " "))

st.divider()

# ---------- Évolution mensuelle ----------
st.subheader("Évolution du chiffre d'affaires par mois")
mensuel = f.groupby(["mois", "canal"], as_index=False)["montant"].sum()
fig = px.bar(mensuel, x="mois", y="montant", color="canal", color_discrete_map=COULEURS,
             labels={"mois": "", "montant": "Chiffre d'affaires (€)", "canal": "Canal"})
fig.update_layout(legend=dict(orientation="h", y=1.1), margin=dict(t=10, b=10), hovermode="x unified")
fig.update_xaxes(dtick="M1", tickformat="%b %Y")
st.plotly_chart(fig, width="stretch")

meilleur = f.groupby("mois")["montant"].sum().idxmax()
st.caption(f"Meilleur mois : **{mois_label(meilleur)}**. "
           "Le pic de fin d'année (Black Friday, Noël) est le moment de renforcer le stock et la pub.")

# ---------- Catégories & produits ----------
g, d = st.columns(2)
with g:
    st.subheader("Ventes par catégorie")
    par_cat = f.groupby("categorie", as_index=False)["montant"].sum().sort_values("montant")
    fig = px.bar(par_cat, x="montant", y="categorie", orientation="h",
                 labels={"montant": "Chiffre d'affaires (€)", "categorie": ""},
                 color_discrete_sequence=["#2563eb"])
    fig.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

with d:
    st.subheader("Top 10 des produits")
    top = (f.groupby("produit", as_index=False)
             .agg(ca=("montant", "sum"), quantite=("quantite", "sum"))
             .nlargest(10, "ca").sort_values("ca"))
    fig = px.bar(top, x="ca", y="produit", orientation="h",
                 hover_data={"quantite": True},
                 labels={"ca": "Chiffre d'affaires (€)", "produit": "", "quantite": "Unités vendues"},
                 color_discrete_sequence=["#16a34a"])
    fig.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

# ---------- Saisonnalité par catégorie ----------
st.subheader("Quelle catégorie se vend quand ?")
saison = f.assign(m=f["date"].dt.month).groupby(["categorie", "m"])["montant"].sum().reset_index()
saison["part"] = saison["montant"] / saison.groupby("categorie")["montant"].transform("sum")
pivot = saison.pivot(index="categorie", columns="m", values="part").reindex(columns=range(1, 13))
pivot.columns = MOIS_FR
fig = px.imshow(pivot, color_continuous_scale="Blues", aspect="auto",
                labels={"color": "Part des ventes annuelles"})
fig.update_traces(hovertemplate="%{y} · %{x} : %{z:.1%}<extra></extra>")
fig.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
st.plotly_chart(fig, width="stretch")
st.caption("Plus la case est foncée, plus la catégorie vend ce mois-là : utile pour planifier les commandes de stock.")

# ---------- Clients & jours ----------
g, d = st.columns(2)
with g:
    st.subheader("Clients fidèles")
    ca_client = f.groupby("id_client")["montant"].sum().sort_values(ascending=False)
    n_top = max(1, round(len(ca_client) * 0.2))
    part_top = ca_client.iloc[:n_top].sum() / ca
    st.metric("Part du CA réalisée par les 20 % meilleurs clients", f"{part_top:.0%}")
    st.metric("Dépense moyenne d'un de ces clients", euros(ca_client.iloc[:n_top].mean()))
    st.caption("Une petite partie des clients pèse lourd : un programme de fidélité les garderait.")

with d:
    st.subheader("Ventes par jour de la semaine")
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    par_jour = f.groupby("jour_semaine")["montant"].sum().reindex(range(7), fill_value=0)
    fig = px.bar(x=jours, y=par_jour.values, labels={"x": "", "y": "Chiffre d'affaires (€)"},
                 color_discrete_sequence=["#2563eb"])
    fig.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

# ---------- Détail ----------
with st.expander("Voir les données détaillées"):
    st.dataframe(f.drop(columns=["mois", "jour_semaine"]).sort_values("date", ascending=False),
                 width="stretch", hide_index=True)
    st.download_button("Télécharger en CSV", f.to_csv(index=False).encode("utf-8"),
                       "ventes_filtrees.csv", "text/csv")
