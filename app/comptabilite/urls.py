from django.urls import path

from . import views

app_name = "comptabilite"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("balance/", views.balance, name="balance"),
    path("compte-de-resultat/", views.compte_resultat, name="compte_resultat"),
    path("soldes-intermediaires/",
         views.soldes_intermediaires, name="soldes_intermediaires"),
    path("compte-de-resultat/analytique/", views.compte_resultat_analytique,
         name="analytique"),
    path("tresorerie/", views.tresorerie, name="tresorerie"),
    path("journaux/", views.journaux, name="journaux"),
    path("grand-livre/", views.grand_livre, name="grand_livre"),
]
