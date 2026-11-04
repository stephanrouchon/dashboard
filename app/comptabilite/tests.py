from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse

from .data import Ecriture
from .views import _soldes_intermediaires


def ecriture(compte, debit="0", credit="0", mois=1, jour=1):
    return Ecriture(
        journal="VE", journal_libelle="Ventes", date=date(2026, mois, jour),
        compte=compte, intitule="", auxiliaire="", piece="", libelle="",
        debit=Decimal(debit), credit=Decimal(credit), plan="", poste="",
    )


class SoldesIntermediairesTests(SimpleTestCase):
    @patch("app.comptabilite.views.charger_ecritures", return_value=[])
    def test_page_sans_ecritures(self, _charger_ecritures):
        response = self.client.get(
            reverse("comptabilite:soldes_intermediaires")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucune écriture de charges ou de produits.")

    def test_calculs_sig_et_cumul(self):
        rows = [
            ecriture("707", credit="100"),
            ecriture("607", debit="40"),
            ecriture("6037", debit="5"),
            ecriture("701", credit="30"),
            ecriture("713", credit="10"),
            ecriture("72", credit="4"),
            ecriture("601", debit="8"),
            ecriture("61", debit="3"),
            ecriture("74", credit="2"),
            ecriture("63", debit="1"),
            ecriture("64", debit="4"),
            ecriture("75", credit="1"),
            ecriture("65", debit="1"),
            ecriture("681", debit="2"),
            ecriture("76", credit="3"),
            ecriture("66", debit="1"),
            ecriture("77", credit="5"),
            ecriture("67", debit="2"),
            ecriture("69", debit="1"),
        ]

        result = _soldes_intermediaires(rows)

        self.assertEqual(result["mois"], ["2026-01"])
        self.assertEqual(
            [solde["total"] for solde in result["soldes"]],
            [Decimal(value) for value in ("55", "44", "88", "85", "83", "85", "3", "87")],
        )

    def test_separe_les_mois(self):
        rows = [
            ecriture("707", credit="100"),
            ecriture("707", credit="50", mois=2),
        ]

        result = _soldes_intermediaires(rows)

        self.assertEqual(result["mois"], ["2026-01", "2026-02"])
        self.assertEqual(
            result["soldes"][0]["valeurs"],
            [Decimal("100"), Decimal("50")],
        )
        self.assertEqual(result["soldes"][0]["total"], Decimal("150"))
