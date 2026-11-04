from collections import defaultdict
from decimal import Decimal

from django.core.paginator import Paginator
from django.shortcuts import render

from .data import charger_ecritures

CLASSES = {
    "1": "Capitaux",
    "2": "Immobilisations",
    "3": "Stocks",
    "4": "Tiers",
    "5": "Financier",
    "6": "Charges",
    "7": "Produits",
}
ZERO = Decimal("0")


def _totaux_par_compte(rows):
    comptes = {}
    for e in rows:
        c = comptes.setdefault(
            e.compte, {"compte": e.compte, "intitule": e.intitule,
                       "debit": ZERO, "credit": ZERO}
        )
        c["debit"] += e.debit
        c["credit"] += e.credit
    for c in comptes.values():
        c["solde"] = c["debit"] - c["credit"]
    return sorted(comptes.values(), key=lambda c: c["compte"])


def dashboard(request):
    rows = charger_ecritures()
    comptes = _totaux_par_compte(rows)

    par_classe = defaultdict(lambda: {"debit": ZERO, "credit": ZERO})
    for c in comptes:
        k = par_classe[c["compte"][:1]]
        k["debit"] += c["debit"]
        k["credit"] += c["credit"]
    classes = [
        {"classe": k, "libelle": CLASSES.get(k, "Autres"), **v,
         "solde": v["debit"] - v["credit"]}
        for k, v in sorted(par_classe.items())
    ]

    mensuel = defaultdict(lambda: {"charges": ZERO, "produits": ZERO})
    for e in rows:
        if e.compte.startswith("6"):
            mensuel[e.date.strftime("%Y-%m")]["charges"] += e.debit - e.credit
        elif e.compte.startswith("7"):
            mensuel[e.date.strftime("%Y-%m")]["produits"] += e.credit - e.debit
    mois = [{"mois": m, **v} for m, v in sorted(mensuel.items())]
    maxi = max((max(m["charges"], m["produits"]) for m in mois),
               default=ZERO) or Decimal("1")
    for m in mois:
        m["pc_charges"] = int(max(m["charges"], ZERO) * 100 / maxi)
        m["pc_produits"] = int(max(m["produits"], ZERO) * 100 / maxi)

    total_charges = sum((m["charges"] for m in mois), ZERO)
    total_produits = sum((m["produits"] for m in mois), ZERO)
    return render(request, "comptabilite/dashboard.html", {
        "nb_ecritures": len(rows),
        "nb_comptes": len(comptes),
        "total_debit": sum((e.debit for e in rows), ZERO),
        "total_credit": sum((e.credit for e in rows), ZERO),
        "total_charges": total_charges,
        "total_produits": total_produits,
        "resultat": total_produits - total_charges,
        "classes": classes,
        "mois": mois,
        "menu": "dashboard",
    })


def balance(request):
    classe = request.GET.get("classe", "")
    q = request.GET.get("q", "").strip().lower()
    comptes = _totaux_par_compte(charger_ecritures())
    if classe:
        comptes = [c for c in comptes if c["compte"].startswith(classe)]
    if q:
        comptes = [c for c in comptes if q in c["compte"] or
                   q in c["intitule"].lower()]
    return render(request, "comptabilite/balance.html", {
        "comptes": comptes,
        "total_debit": sum((c["debit"] for c in comptes), ZERO),
        "total_credit": sum((c["credit"] for c in comptes), ZERO),
        "classes": CLASSES,
        "classe": classe,
        "q": request.GET.get("q", ""),
        "menu": "balance",
    })


def _compte_resultat(rows):
    mois = sorted({e.date.strftime("%Y-%m") for e
                   in rows if e.compte[:1] in "67"})
    idx = {m: i for i, m in enumerate(mois)}

    sections = []
    for classe, titre, sens in (("7", "Produits", 1), ("6", "Charges", -1)):
        comptes = {}
        for e in rows:
            if not e.compte.startswith(classe):
                continue
            code = e.compte[:4]
            c = comptes.setdefault(code, {
                "compte": code, "intitule": e.intitule, "min": e.compte,
                "valeurs": [ZERO] * len(mois),
            })
            if e.compte < c["min"]:
                c["min"], c["intitule"] = e.compte, e.intitule
            c["valeurs"][idx[e.date.strftime("%Y-%m")]] +=\
                (e.credit - e.debit) * sens
        lignes = sorted(comptes.values(), key=lambda c: c["compte"])
        totaux = [sum((ligne["valeurs"][i] for ligne in lignes),
                      ZERO) for i in range(len(mois))]
        for ligne in lignes:
            ligne["total"] = sum(ligne["valeurs"], ZERO)
        groupes = []
        for ligne in lignes:
            if not groupes or groupes[-1]["code"] != ligne["compte"][:2]:
                groupes.append({"code": ligne["compte"][:2], "lignes": []})
            groupes[-1]["lignes"].append(ligne)
        for g in groupes:
            g["totaux"] = [sum((ligne["valeurs"][i] for ligne in g["lignes"]),
                               ZERO) for i in range(len(mois))]
            g["total"] = sum(g["totaux"], ZERO)
        sections.append({
            "titre": titre, "groupes": groupes, "totaux": totaux,
            "total": sum(totaux, ZERO), "sens": sens,
        })

    produits, charges = sections
    resultats = [p - c for p, c in zip(produits["totaux"], charges["totaux"])]
    return {
        "mois": mois,
        "sections": sections,
        "resultats": resultats,
        "resultat_total": produits["total"] - charges["total"],
    }


def compte_resultat(request):
    ctx = _compte_resultat(charger_ecritures())
    return render(request, "comptabilite/compte_resultat.html",
                  {**ctx, "menu": "compte_resultat"})


def _soldes_intermediaires(rows):
    mois = sorted({e.date.strftime("%Y-%m") for e in rows
                   if e.compte[:1] in "67"})
    comptes = defaultdict(lambda: defaultdict(lambda: ZERO))
    for e in rows:
        if e.compte[:1] in "67":
            comptes[e.date.strftime("%Y-%m")][e.compte] += e.credit - e.debit

    def somme(m, predicate):
        return sum((solde for compte, solde in comptes[m].items()
                    if predicate(compte)), ZERO)

    def prefixes(*codes):
        return lambda compte: compte.startswith(codes)

    soldes_mensuels = []
    for m in mois:
        marge = somme(m, prefixes("707", "7097")) + somme(
            m, prefixes("607", "6037")
        )
        production = somme(
            m, lambda c: c.startswith("70")
            and not c.startswith(("707", "7097"))
        ) + somme(m, prefixes("71", "72"))
        valeur_ajoutee = marge + production + somme(
            m, lambda c: (
                c.startswith("60") and not c.startswith(("607", "6037"))
            ) or c.startswith(("61", "62"))
        )
        ebe = valeur_ajoutee + somme(m, prefixes("74", "63", "64"))
        exploitation = ebe + somme(
            m, prefixes("75", "65", "681", "781", "791")
        )
        courant = exploitation + somme(
            m, prefixes("66", "76", "686", "786", "796")
        )
        exceptionnel = somme(
            m, prefixes("67", "77", "687", "787", "797")
        )
        soldes_mensuels.append({
            "mois": m,
            "valeurs": (
                marge, production, valeur_ajoutee, ebe, exploitation,
                courant, exceptionnel, courant + exceptionnel + somme(
                    m, prefixes("69")
                ),
            ),
        })

    libelles = (
        ("Marge commerciale", "707/7097 − achats consommés (607/6037)"),
        ("Production de l'exercice", "Production vendue, stockée et immobilisée"),
        ("Valeur ajoutée", "Marge commerciale + production − consommations de tiers"),
        ("Excédent brut d'exploitation (EBE)", "Valeur ajoutée + 74 − 63 − 64"),
        ("Résultat d'exploitation", "EBE + 75 − 65 + 781/791 − 681"),
        ("Résultat courant avant impôts", "Résultat d'exploitation + 76 − 66 + 786/796 − 686"),
        ("Résultat exceptionnel", "77 − 67 + 787/797 − 687"),
        ("Résultat net", "Résultat courant + résultat exceptionnel − 69"),
    )
    soldes = []
    for i, (libelle, formule) in enumerate(libelles):
        valeurs = [m["valeurs"][i] for m in soldes_mensuels]
        soldes.append({
            "libelle": libelle,
            "formule": formule,
            "valeurs": valeurs,
            "total": sum(valeurs, ZERO),
        })
    return {"mois": mois, "soldes": soldes}


def soldes_intermediaires(request):
    ctx = _soldes_intermediaires(charger_ecritures())
    return render(request, "comptabilite/soldes_intermediaires.html",
                  {**ctx, "menu": "soldes_intermediaires"})


def compte_resultat_analytique(request):
    rows = charger_ecritures()
    plan = request.GET.get("plan", "")
    poste = request.GET.get("poste", "")

    postes_par_plan = defaultdict(set)
    for e in rows:
        if e.compte[:1] in "67":
            postes_par_plan[e.plan].add(e.poste)
    plans = sorted(postes_par_plan)
    postes = sorted(postes_par_plan.get(plan, set())) if plan else []
    if poste not in postes:
        poste = ""

    filtrees = [e for e in rows if e.compte[:1] in "67"
                and (not plan or e.plan == plan) and (
                    not poste or e.poste == poste)]
    ctx = _compte_resultat(filtrees)

    # Synthèse par plan / poste
    synthese = {}
    for e in filtrees:
        s = synthese.setdefault((e.plan, e.poste),
                                {"plan": e.plan, "poste": e.poste,
                                 "produits": ZERO, "charges": ZERO})
        if e.compte.startswith("7"):
            s["produits"] += e.credit - e.debit
        else:
            s["charges"] += e.debit - e.credit
    par_plan = []
    for (p, _), s in sorted(synthese.items()):
        s["resultat"] = s["produits"] - s["charges"]
        if not par_plan or par_plan[-1]["plan"] != p:
            par_plan.append({"plan": p, "postes": [],
                             "produits": ZERO, "charges": ZERO})
        g = par_plan[-1]
        g["postes"].append(s)
        g["produits"] += s["produits"]
        g["charges"] += s["charges"]
    for g in par_plan:
        g["resultat"] = g["produits"] - g["charges"]

    return render(request, "comptabilite/compte_resultat_analytique.html", {
        **ctx,
        "plans": plans,
        "postes": postes,
        "plan": plan,
        "poste": poste,
        "par_plan": par_plan,
        "menu": "analytique",
    })


def tresorerie(request):
    mouvements = defaultdict(lambda: ZERO)
    for e in charger_ecritures():
        if e.compte.startswith("5"):
            mouvements[e.date] += e.debit - e.credit

    cumul, points = ZERO, []
    for d in sorted(mouvements):
        cumul += mouvements[d]
        points.append((d, cumul))

    l, h, mg_g, mg_v = 1000, 320, 90, 20
    graphique = None
    if points:
        t0, t1 = points[0][0].toordinal(), points[-1][0].toordinal()
        vmin = min(min(v for _, v in points), ZERO)
        vmax = max(max(v for _, v in points), ZERO)
        plage = (vmax - vmin) or Decimal("1")

        def x(d):
            return mg_g + (l - mg_g - mg_v) *\
                (d.toordinal() - t0) / ((t1 - t0) or 1)

        def y(v):
            return mg_v + (h - 2 * mg_v) * float((vmax - v) / plage)

        fin_mois = {}
        for d, v in points:
            fin_mois[d.strftime("%Y-%m")] = (d, v)
        graphique = {
            "largeur": l, "hauteur": h,
            "ligne": " ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in points),
            "axe_x": mg_g, "fin_x": l - mg_v, "zero_y": f"{y(ZERO):.1f}",
            "graduations": [
                {"y": f"{y(v):.1f}", "valeur": v}
                for v in (vmin + plage * i / 4 for i in range(5))
            ],
            "mois": [
                {"x": f"{x(d):.1f}", "y": f"{y(v):.1f}",
                 "label": m, "valeur": v}
                for m, (d, v) in sorted(fin_mois.items())
            ],
        }
    return render(request, "comptabilite/tresorerie.html", {
        "graphique": graphique,
        "solde": points[-1][1] if points else ZERO,
        "minimum": min((v for _, v in points), default=ZERO),
        "maximum": max((v for _, v in points), default=ZERO),
        "menu": "tresorerie",
    })


def journaux(request):
    stats = {}
    for e in charger_ecritures():
        j = stats.setdefault(e.journal, {
            "code": e.journal, "libelle": e.journal_libelle,
            "nb": 0, "debit": ZERO, "credit": ZERO,
        })
        j["nb"] += 1
        j["debit"] += e.debit
        j["credit"] += e.credit
    return render(request, "comptabilite/journaux.html", {
        "journaux": sorted(stats.values(), key=lambda j: j["code"]),
        "menu": "journaux",
    })


def grand_livre(request):
    rows = charger_ecritures()
    comptes = _totaux_par_compte(rows)
    compte = request.GET.get("compte", "")
    totaux, page = None, None
    if compte:
        lignes, cumul = [], ZERO
        for e in sorted((e for e in rows if e.compte == compte),
                        key=lambda e: e.date):
            cumul += e.debit - e.credit
            lignes.append({"e": e, "cumul": cumul})
        totaux = next((c for c in comptes if c["compte"] == compte), None)
        page = Paginator(lignes, 100).get_page(request.GET.get("page"))
    return render(request, "comptabilite/grand_livre.html", {
        "comptes": comptes,
        "compte": compte,
        "page": page,
        "totaux": totaux,
        "menu": "grand_livre",
    })
