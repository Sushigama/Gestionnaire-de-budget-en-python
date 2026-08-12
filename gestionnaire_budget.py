import json
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import calendar


FICHIER = "budget.json"

payes = []
achats = []
deductions = []

historique_entrees_indices = []
historique_sorties_indices = []


def charger_donnees():
    global payes, achats, deductions

    if os.path.exists(FICHIER):
        try:
            with open(FICHIER, "r", encoding="utf-8") as fichier:
                donnees = json.load(fichier)

            payes = donnees.get("payes", [])
            achats = donnees.get("achats", [])
            deductions = donnees.get("deductions", [])

        except (json.JSONDecodeError, OSError):
            payes = []
            achats = []
            deductions = []
    else:
        payes = []
        achats = []
        deductions = []


def sauvegarder_donnees():
    with open(FICHIER, "w", encoding="utf-8") as fichier:
        json.dump(
            {
                "payes": payes,
                "achats": achats,
                "deductions": deductions
            },
            fichier,
            indent=4,
            ensure_ascii=False
        )


def ajouter_somme():
    description = entree_description.get().strip()

    if not description:
        messagebox.showerror(
            "Erreur",
            "La description est obligatoire."
        )
        return

    try:
        montant = float(
            entree_montant.get().replace(",", ".")
        )

        if montant <= 0:
            messagebox.showerror(
                "Erreur",
                "Le montant doit être positif."
            )
            return

    except ValueError:
        messagebox.showerror(
            "Erreur",
            "Le montant doit être un nombre."
        )
        return

    date = datetime.now().strftime("%Y-%m-%d")

    if est_une_paye.get():

        payes.append({
            "description": description,
            "montant": montant,
            "date": date
        })

        total_deductions = 0

        for deduction in deductions:

            if not deduction.get("active", True):
                continue

            nom = deduction["nom"]
            type_deduction = deduction["type"]
            valeur = deduction["valeur"]

            if type_deduction == "pourcentage":
                montant_deduit = montant * valeur / 100
            else:
                montant_deduit = valeur

            montant_deduit = min(
                montant_deduit,
                montant - total_deductions
            )

            if montant_deduit <= 0:
                continue

            total_deductions += montant_deduit

            achats.append({
                "description": f"{nom} (déduction paye)",
                "montant": montant_deduit,
                "date": date,
                "automatique": True
            })

        net = montant - total_deductions

        sauvegarder_donnees()
        vider_champs()
        afficher_tout()

        messagebox.showinfo(
            "Paye ajoutée",
            f"Paye brute : {montant:.2f} €\n"
            f"Déductions : {total_deductions:.2f} €\n"
            f"Net : {net:.2f} €"
        )

    else:

        payes.append({
            "description": description,
            "montant": montant,
            "date": date
        })

        sauvegarder_donnees()
        vider_champs()
        afficher_tout()

        messagebox.showinfo(
            "Succès",
            "Somme ajoutée !"
        )


def ajouter_achat():
    description = entree_description.get().strip()

    if not description:
        messagebox.showerror(
            "Erreur",
            "La description est obligatoire."
        )
        return

    try:
        montant = float(
            entree_montant.get().replace(",", ".")
        )

        if montant <= 0:
            messagebox.showerror(
                "Erreur",
                "Le montant doit être positif."
            )
            return

    except ValueError:
        messagebox.showerror(
            "Erreur",
            "Le montant doit être un nombre."
        )
        return

    achats.append({
        "description": description,
        "montant": montant,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "automatique": False
    })

    sauvegarder_donnees()
    vider_champs()
    afficher_tout()

    messagebox.showinfo(
        "Succès",
        "Achat ajouté !"
    )


def calculer_deductions_paye(montant):
    total = 0

    for deduction in deductions:

        if not deduction.get("active", True):
            continue

        if deduction["type"] == "pourcentage":
            total += montant * deduction["valeur"] / 100
        else:
            total += deduction["valeur"]

    return min(total, montant)


def obtenir_bilan_mois(annee, mois):
    revenus = 0
    depenses = 0
    deductions_mois = 0

    for p in payes:
        try:
            date = datetime.strptime(
                p["date"],
                "%Y-%m-%d"
            )

            if date.year == annee and date.month == mois:
                revenus += p["montant"]

        except (ValueError, KeyError):
            continue

    for a in achats:
        try:
            date = datetime.strptime(
                a["date"],
                "%Y-%m-%d"
            )

            if date.year == annee and date.month == mois:

                depenses += a["montant"]

                if a.get("automatique", False):
                    deductions_mois += a["montant"]

        except (ValueError, KeyError):
            continue

    solde = revenus - depenses

    return revenus, depenses, deductions_mois, solde


def obtenir_bilan_annee(annee):
    revenus = 0
    depenses = 0
    deductions_annee = 0

    for p in payes:
        try:
            date = datetime.strptime(
                p["date"],
                "%Y-%m-%d"
            )

            if date.year == annee:
                revenus += p["montant"]

        except (ValueError, KeyError):
            continue

    for a in achats:
        try:
            date = datetime.strptime(
                a["date"],
                "%Y-%m-%d"
            )

            if date.year == annee:

                depenses += a["montant"]

                if a.get("automatique", False):
                    deductions_annee += a["montant"]

        except (ValueError, KeyError):
            continue

    solde = revenus - depenses

    return revenus, depenses, deductions_annee, solde


def afficher_budget():
    total_payes = sum(
        p["montant"]
        for p in payes
    )

    total_achats = sum(
        a["montant"]
        for a in achats
    )

    solde = total_payes - total_achats

    label_revenus.config(
        text=f"Revenus : {total_payes:.2f} €"
    )

    label_depenses.config(
        text=f"Dépenses : {total_achats:.2f} €"
    )

    couleur = GREEN if solde >= 0 else RED

    label_solde.config(
        text=f"Solde : {solde:.2f} €",
        fg=couleur
    )


def afficher_historique():
    global historique_entrees_indices
    global historique_sorties_indices

    liste_entrees.delete(0, tk.END)
    liste_sorties.delete(0, tk.END)

    historique_entrees_indices = []
    historique_sorties_indices = []

    historique_entrees = []

    for index, p in enumerate(payes):
        historique_entrees.append({
            "index": index,
            "description": p["description"],
            "montant": p["montant"],
            "date": p["date"]
        })

    historique_entrees.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    for entree in historique_entrees:

        historique_entrees_indices.append(
            entree["index"]
        )

        liste_entrees.insert(
            tk.END,
            f'{entree["date"]}  💰  '
            f'{entree["description"]} : '
            f'+{entree["montant"]:.2f} €'
        )

    historique_sorties = []

    for index, a in enumerate(achats):

        type_achat = (
            "📉"
            if a.get("automatique", False)
            else "🛒"
        )

        historique_sorties.append({
            "index": index,
            "type": type_achat,
            "description": a["description"],
            "montant": a["montant"],
            "date": a["date"]
        })

    historique_sorties.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    for sortie in historique_sorties:

        historique_sorties_indices.append(
            sortie["index"]
        )

        liste_sorties.insert(
            tk.END,
            f'{sortie["date"]}  {sortie["type"]}  '
            f'{sortie["description"]} : '
            f'-{sortie["montant"]:.2f} €'
        )


def supprimer_entree():
    selection = liste_entrees.curselection()

    if not selection:
        messagebox.showwarning(
            "Attention",
            "Sélectionne une entrée à supprimer."
        )
        return

    ligne = selection[0]
    index = historique_entrees_indices[ligne]
    transaction = payes[index]

    confirmation = messagebox.askyesno(
        "Confirmation",
        f'Supprimer cette entrée ?\n\n'
        f'{transaction["description"]}\n'
        f'+{transaction["montant"]:.2f} €\n'
        f'{transaction["date"]}'
    )

    if not confirmation:
        return

    payes.pop(index)

    sauvegarder_donnees()
    afficher_tout()

    messagebox.showinfo(
        "Suppression",
        "L'entrée a été supprimée."
    )


def supprimer_sortie():
    selection = liste_sorties.curselection()

    if not selection:
        messagebox.showwarning(
            "Attention",
            "Sélectionne une sortie à supprimer."
        )
        return

    ligne = selection[0]
    index = historique_sorties_indices[ligne]
    transaction = achats[index]

    confirmation = messagebox.askyesno(
        "Confirmation",
        f'Supprimer cette sortie ?\n\n'
        f'{transaction["description"]}\n'
        f'-{transaction["montant"]:.2f} €\n'
        f'{transaction["date"]}'
    )

    if not confirmation:
        return

    achats.pop(index)

    sauvegarder_donnees()
    afficher_tout()

    messagebox.showinfo(
        "Suppression",
        "La sortie a été supprimée."
    )


def bilan_mensuel():
    aujourd_hui = datetime.now()

    return obtenir_bilan_mois(
        aujourd_hui.year,
        aujourd_hui.month
    )


def bilan_annuel():
    aujourd_hui = datetime.now()

    return obtenir_bilan_annee(
        aujourd_hui.year
    )


def afficher_bilans():
    rm, dm, dedm, sm = bilan_mensuel()
    ra, da, deda, sa = bilan_annuel()

    label_bilan_mois.config(
        text=(
            f"Mois : +{rm:.2f} €   "
            f"-{dm:.2f} €   "
            f"= {sm:.2f} €"
        )
    )

    label_bilan_annee.config(
        text=(
            f"Année : +{ra:.2f} €   "
            f"-{da:.2f} €   "
            f"= {sa:.2f} €"
        )
    )


def ouvrir_bilan_mois(annee, mois):
    fenetre_mois = tk.Toplevel(fenetre)

    noms_mois = [
        "",
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre"
    ]

    fenetre_mois.title(
        f"Bilan de {noms_mois[mois]} {annee}"
    )

    fenetre_mois.geometry(
        "600x600"
    )

    fenetre_mois.configure(
        bg=BG
    )

    revenus, depenses, deductions_mois, solde = (
        obtenir_bilan_mois(
            annee,
            mois
        )
    )

    tk.Label(
        fenetre_mois,
        text=f"Bilan de {noms_mois[mois]} {annee}",
        bg=BG,
        fg=TEXT,
        font=("Helvetica", 20, "bold")
    ).pack(
        pady=20
    )

    frame_resume = tk.Frame(
        fenetre_mois,
        bg=CARD,
        bd=1,
        relief="solid"
    )

    frame_resume.pack(
        fill="x",
        padx=25,
        pady=10
    )

    tk.Label(
        frame_resume,
        text=f"💰 Revenus : +{revenus:.2f} €",
        bg=CARD,
        fg=GREEN,
        font=("Helvetica", 13, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=10
    )

    tk.Label(
        frame_resume,
        text=f"📉 Déductions : -{deductions_mois:.2f} €",
        bg=CARD,
        fg=BLUE,
        font=("Helvetica", 12)
    ).pack(
        anchor="w",
        padx=20,
        pady=5
    )

    depenses_reelles = depenses - deductions_mois

    tk.Label(
        frame_resume,
        text=f"🛒 Dépenses réelles : -{depenses_reelles:.2f} €",
        bg=CARD,
        fg=RED,
        font=("Helvetica", 12)
    ).pack(
        anchor="w",
        padx=20,
        pady=5
    )

    tk.Label(
        frame_resume,
        text=f"Dépenses totales : -{depenses:.2f} €",
        bg=CARD,
        fg=TEXT,
        font=("Helvetica", 11)
    ).pack(
        anchor="w",
        padx=20,
        pady=5
    )

    tk.Label(
        frame_resume,
        text=f"Solde : {solde:+.2f} €",
        bg=CARD,
        fg=GREEN if solde >= 0 else RED,
        font=("Helvetica", 16, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=15
    )

    frame_transactions = tk.LabelFrame(
        fenetre_mois,
        text="Transactions du mois",
        bg=BG,
        fg=TEXT,
        font=("Helvetica", 11, "bold")
    )

    frame_transactions.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=15
    )

    liste = tk.Listbox(
        frame_transactions,
        font=("Helvetica", 10)
    )

    liste.pack(
        fill="both",
        expand=True,
        padx=8,
        pady=8
    )

    transactions = []

    for p in payes:
        try:
            date = datetime.strptime(
                p["date"],
                "%Y-%m-%d"
            )

            if date.year == annee and date.month == mois:
                transactions.append({
                    "date": p["date"],
                    "texte": (
                        f'{p["date"]}  💰  '
                        f'{p["description"]} : '
                        f'+{p["montant"]:.2f} €'
                    )
                })

        except (ValueError, KeyError):
            continue

    for a in achats:
        try:
            date = datetime.strptime(
                a["date"],
                "%Y-%m-%d"
            )

            if date.year == annee and date.month == mois:

                icone = (
                    "📉"
                    if a.get("automatique", False)
                    else "🛒"
                )

                transactions.append({
                    "date": a["date"],
                    "texte": (
                        f'{a["date"]}  {icone}  '
                        f'{a["description"]} : '
                        f'-{a["montant"]:.2f} €'
                    )
                })

        except (ValueError, KeyError):
            continue

    transactions.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    for transaction in transactions:
        liste.insert(
            tk.END,
            transaction["texte"]
        )


def ouvrir_bilan_annee(annee):
    fenetre_annee = tk.Toplevel(fenetre)

    fenetre_annee.title(
        f"Bilan annuel {annee}"
    )

    fenetre_annee.geometry(
        "600x500"
    )

    fenetre_annee.configure(
        bg=BG
    )

    revenus, depenses, deductions_annee, solde = (
        obtenir_bilan_annee(annee)
    )

    tk.Label(
        fenetre_annee,
        text=f"🏆 Bilan annuel {annee}",
        bg=BG,
        fg=TEXT,
        font=("Helvetica", 20, "bold")
    ).pack(
        pady=20
    )

    frame = tk.Frame(
        fenetre_annee,
        bg=CARD,
        bd=1,
        relief="solid"
    )

    frame.pack(
        fill="x",
        padx=25,
        pady=10
    )

    tk.Label(
        frame,
        text=f"💰 Revenus : +{revenus:.2f} €",
        bg=CARD,
        fg=GREEN,
        font=("Helvetica", 13, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=10
    )

    tk.Label(
        frame,
        text=f"📉 Déductions : -{deductions_annee:.2f} €",
        bg=CARD,
        fg=BLUE,
        font=("Helvetica", 12)
    ).pack(
        anchor="w",
        padx=20,
        pady=5
    )

    depenses_reelles = depenses - deductions_annee

    tk.Label(
        frame,
        text=f"🛒 Dépenses réelles : -{depenses_reelles:.2f} €",
        bg=CARD,
        fg=RED,
        font=("Helvetica", 12)
    ).pack(
        anchor="w",
        padx=20,
        pady=5
    )

    tk.Label(
        frame,
        text=f"Dépenses totales : -{depenses:.2f} €",
        bg=CARD,
        fg=TEXT,
        font=("Helvetica", 11)
    ).pack(
        anchor="w",
        padx=20,
        pady=5
    )

    tk.Label(
        frame,
        text=f"Solde annuel : {solde:+.2f} €",
        bg=CARD,
        fg=GREEN if solde >= 0 else RED,
        font=("Helvetica", 17, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=15
    )

    frame_mois = tk.LabelFrame(
        fenetre_annee,
        text="Résultat par mois",
        bg=BG,
        fg=TEXT
    )

    frame_mois.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=15
    )

    liste_mois = tk.Listbox(
        frame_mois,
        font=("Helvetica", 10)
    )

    liste_mois.pack(
        fill="both",
        expand=True,
        padx=8,
        pady=8
    )

    noms_mois = [
        "",
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre"
    ]

    for mois in range(1, 13):
        _, _, _, solde_mois = obtenir_bilan_mois(
            annee,
            mois
        )

        liste_mois.insert(
            tk.END,
            f"{noms_mois[mois]:<12} "
            f"{solde_mois:+.2f} €"
        )


def ouvrir_calendrier():
    fenetre_calendrier = tk.Toplevel(fenetre)

    fenetre_calendrier.title(
        "Calendrier"
    )

    fenetre_calendrier.geometry(
        "1050x850"
    )

    fenetre_calendrier.configure(
        bg=BG
    )

    fenetre_calendrier.resizable(
        True,
        True
    )

    annee_selectionnee = datetime.now().year

    noms_mois = [
        "",
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre"
    ]

    def changer_annee(valeur):
        nonlocal annee_selectionnee

        annee_selectionnee += valeur

        afficher_calendrier()

    def afficher_calendrier():

        for widget in frame_contenu.winfo_children():
            widget.destroy()

        label_annee.config(
            text=str(annee_selectionnee)
        )

        revenus_annee, depenses_annee, deductions_annee, solde_annee = (
            obtenir_bilan_annee(
                annee_selectionnee
            )
        )

        frame_annuel = tk.Frame(
            frame_contenu,
            bg=CARD,
            bd=1,
            relief="solid"
        )

        frame_annuel.pack(
            fill="x",
            padx=15,
            pady=(5, 15)
        )

        bouton_annuel = tk.Button(
            frame_annuel,
            text=f"🏆 BILAN ANNUEL {annee_selectionnee}",
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            font=("Helvetica", 15, "bold"),
            cursor="hand2",
            command=lambda a=annee_selectionnee:
                ouvrir_bilan_annee(a)
        )

        bouton_annuel.pack(
            pady=(12, 5)
        )

        tk.Label(
            frame_annuel,
            text=(
                f"Revenus : +{revenus_annee:.2f} €    "
                f"Déductions : -{deductions_annee:.2f} €    "
                f"Dépenses : -{depenses_annee:.2f} €"
            ),
            bg=CARD,
            fg=TEXT,
            font=("Helvetica", 10)
        ).pack(
            pady=3
        )

        tk.Label(
            frame_annuel,
            text=f"Solde annuel : {solde_annee:+.2f} €",
            bg=CARD,
            fg=GREEN if solde_annee >= 0 else RED,
            font=("Helvetica", 14, "bold")
        ).pack(
            pady=(3, 12)
        )

        frame_grille = tk.Frame(
            frame_contenu,
            bg=BG
        )

        frame_grille.pack(
            fill="both",
            expand=True,
            padx=10
        )

        for colonne in range(3):
            frame_grille.grid_columnconfigure(
                colonne,
                weight=1
            )

        for ligne in range(4):
            frame_grille.grid_rowconfigure(
                ligne,
                weight=1
            )

        for mois in range(1, 13):

            ligne = (mois - 1) // 3
            colonne = (mois - 1) % 3

            revenus, depenses, deductions, solde = (
                obtenir_bilan_mois(
                    annee_selectionnee,
                    mois
                )
            )

            frame_mois = tk.Frame(
                frame_grille,
                bg=CARD,
                bd=1,
                relief="solid"
            )

            frame_mois.grid(
                row=ligne,
                column=colonne,
                padx=6,
                pady=6,
                sticky="nsew"
            )

            bouton_mois = tk.Button(
                frame_mois,
                text=noms_mois[mois],
                bg=CARD,
                fg=BLUE,
                activebackground=CARD,
                activeforeground=PURPLE,
                relief="flat",
                bd=0,
                font=("Helvetica", 11, "bold"),
                cursor="hand2",
                command=lambda
                a=annee_selectionnee,
                m=mois:
                ouvrir_bilan_mois(a, m)
            )

            bouton_mois.grid(
                row=0,
                column=0,
                columnspan=7,
                pady=(7, 5)
            )

            jours = [
                "L",
                "M",
                "M",
                "J",
                "V",
                "S",
                "D"
            ]

            for jour_index, jour_nom in enumerate(jours):

                tk.Label(
                    frame_mois,
                    text=jour_nom,
                    bg=CARD,
                    fg=SECONDARY,
                    font=("Helvetica", 7, "bold"),
                    width=3
                ).grid(
                    row=1,
                    column=jour_index,
                    padx=1,
                    pady=1
                )

            calendrier = calendar.monthcalendar(
                annee_selectionnee,
                mois
            )

            dernier_jour = calendar.monthrange(
                annee_selectionnee,
                mois
            )[1]

            for semaine_index, semaine in enumerate(calendrier):

                for jour_index, jour in enumerate(semaine):

                    if jour == 0:
                        tk.Label(
                            frame_mois,
                            text="",
                            bg=CARD,
                            width=3
                        ).grid(
                            row=semaine_index + 2,
                            column=jour_index,
                            padx=1,
                            pady=1
                        )

                        continue

                    couleur_fond = "#F5F5F7"
                    couleur_texte = TEXT

                    if jour == dernier_jour:

                        if solde > 0:
                            couleur_fond = "#DFF7E5"
                            couleur_texte = "#168A36"

                        elif solde < 0:
                            couleur_fond = "#FFE1DF"
                            couleur_texte = "#D93025"

                        else:
                            couleur_fond = "#E5E5EA"

                        if mois == 12:
                            couleur_fond = "#FFF0C2"

                    bouton_jour = tk.Button(
                        frame_mois,
                        text=str(jour),
                        width=3,
                        height=1,
                        bg=couleur_fond,
                        fg=couleur_texte,
                        activebackground=couleur_fond,
                        activeforeground=couleur_texte,
                        relief="flat",
                        bd=0,
                        font=(
                            "Helvetica",
                            8,
                            "bold"
                        )
                        if jour == dernier_jour
                        else (
                            "Helvetica",
                            8
                        ),
                        command=lambda
                        a=annee_selectionnee,
                        m=mois,
                        j=jour:
                        ouvrir_bilan_mois(a, m)
                    )

                    bouton_jour.grid(
                        row=semaine_index + 2,
                        column=jour_index,
                        padx=1,
                        pady=1
                    )

            couleur_solde = (
                GREEN
                if solde >= 0
                else RED
            )

            tk.Label(
                frame_mois,
                text=f"{solde:+.2f} €",
                bg=CARD,
                fg=couleur_solde,
                font=("Helvetica", 9, "bold")
            ).grid(
                row=9,
                column=0,
                columnspan=7,
                pady=(4, 7)
            )

            if mois == 12:

                tk.Label(
                    frame_mois,
                    text="🏆 FIN D'ANNÉE",
                    bg=CARD,
                    fg="#C78A00",
                    font=("Helvetica", 8, "bold")
                ).grid(
                    row=10,
                    column=0,
                    columnspan=7,
                    pady=(0, 6)
                )

    frame_entete = tk.Frame(
        fenetre_calendrier,
        bg=BG
    )

    frame_entete.pack(
        fill="x",
        padx=20,
        pady=15
    )

    tk.Button(
        frame_entete,
        text="‹",
        bg=BLUE,
        fg="white",
        activebackground=BLUE,
        relief="flat",
        bd=0,
        font=("Helvetica", 16, "bold"),
        width=3,
        cursor="hand2",
        command=lambda: changer_annee(-1)
    ).pack(
        side="left"
    )

    label_annee = tk.Label(
        frame_entete,
        text=str(annee_selectionnee),
        bg=BG,
        fg=TEXT,
        font=("Helvetica", 20, "bold")
    )

    label_annee.pack(
        side="left",
        expand=True
    )

    tk.Button(
        frame_entete,
        text="›",
        bg=BLUE,
        fg="white",
        activebackground=BLUE,
        relief="flat",
        bd=0,
        font=("Helvetica", 16, "bold"),
        width=3,
        cursor="hand2",
        command=lambda: changer_annee(1)
    ).pack(
        side="right"
    )

    frame_legende = tk.Frame(
        fenetre_calendrier,
        bg=BG
    )

    frame_legende.pack(
        pady=(0, 10)
    )

    tk.Label(
        frame_legende,
        text="🟢 Positif",
        bg=BG,
        fg=GREEN
    ).pack(
        side="left",
        padx=8
    )

    tk.Label(
        frame_legende,
        text="🔴 Négatif",
        bg=BG,
        fg=RED
    ).pack(
        side="left",
        padx=8
    )

    tk.Label(
        frame_legende,
        text="🟡 Fin d'année",
        bg=BG,
        fg="#C78A00"
    ).pack(
        side="left",
        padx=8
    )

    frame_contenu = tk.Frame(
        fenetre_calendrier,
        bg=BG
    )

    frame_contenu.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=5
    )

    afficher_calendrier()


def ouvrir_deductions():
    fenetre_deductions = tk.Toplevel(fenetre)

    fenetre_deductions.title(
        "Gestion des déductions"
    )

    fenetre_deductions.geometry(
        "600x500"
    )

    fenetre_deductions.configure(
        bg=BG
    )

    tk.Label(
        fenetre_deductions,
        text="Déductions automatiques",
        font=("Helvetica", 16, "bold"),
        bg=BG,
        fg=TEXT
    ).pack(pady=15)

    tk.Label(
        fenetre_deductions,
        text=(
            "Ces déductions seront appliquées "
            "automatiquement lorsque tu coches "
            "« Appliquer les déductions »."
        ),
        bg=BG,
        fg=SECONDARY,
        wraplength=500
    ).pack(pady=5)

    frame_liste = tk.Frame(
        fenetre_deductions,
        bg=CARD,
        bd=1,
        relief="solid"
    )

    frame_liste.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=15
    )

    liste_deductions = tk.Listbox(
        frame_liste,
        font=("Helvetica", 11)
    )

    liste_deductions.pack(
        fill="both",
        expand=True,
        padx=5,
        pady=5
    )

    def actualiser_liste():
        liste_deductions.delete(
            0,
            tk.END
        )

        for deduction in deductions:

            statut = (
                "✓"
                if deduction.get("active", True)
                else "✗"
            )

            if deduction["type"] == "pourcentage":
                valeur = f'{deduction["valeur"]:.2f} %'
            else:
                valeur = f'{deduction["valeur"]:.2f} €'

            liste_deductions.insert(
                tk.END,
                f'{statut} {deduction["nom"]} — {valeur}'
            )

    def ajouter_deduction():
        popup = tk.Toplevel(
            fenetre_deductions
        )

        popup.title(
            "Nouvelle déduction"
        )

        popup.geometry(
            "400x300"
        )

        popup.configure(
            bg=BG
        )

        tk.Label(
            popup,
            text="Nom",
            bg=BG
        ).pack(pady=(15, 3))

        entree_nom = tk.Entry(
            popup,
            width=35
        )

        entree_nom.pack()

        tk.Label(
            popup,
            text="Type",
            bg=BG
        ).pack(pady=(15, 3))

        type_var = tk.StringVar(
            value="pourcentage"
        )

        frame_type = tk.Frame(
            popup,
            bg=BG
        )

        frame_type.pack()

        tk.Radiobutton(
            frame_type,
            text="Pourcentage",
            variable=type_var,
            value="pourcentage",
            bg=BG
        ).pack(
            side="left",
            padx=10
        )

        tk.Radiobutton(
            frame_type,
            text="Montant fixe",
            variable=type_var,
            value="fixe",
            bg=BG
        ).pack(
            side="left",
            padx=10
        )

        tk.Label(
            popup,
            text="Valeur",
            bg=BG
        ).pack(pady=(15, 3))

        entree_valeur = tk.Entry(
            popup,
            width=20
        )

        entree_valeur.pack()

        tk.Label(
            popup,
            text="% pourcentage / € fixe",
            bg=BG,
            fg=SECONDARY
        ).pack(pady=5)

        def enregistrer():
            nom = entree_nom.get().strip()

            if not nom:
                messagebox.showerror(
                    "Erreur",
                    "Le nom est obligatoire.",
                    parent=popup
                )
                return

            try:
                valeur = float(
                    entree_valeur.get().replace(",", ".")
                )

                if valeur <= 0:
                    raise ValueError

            except ValueError:
                messagebox.showerror(
                    "Erreur",
                    "La valeur doit être positive.",
                    parent=popup
                )
                return

            if (
                type_var.get() == "pourcentage"
                and valeur > 100
            ):
                messagebox.showerror(
                    "Erreur",
                    "Un pourcentage ne peut pas dépasser 100 %.",
                    parent=popup
                )
                return

            deductions.append({
                "nom": nom,
                "type": type_var.get(),
                "valeur": valeur,
                "active": True
            })

            sauvegarder_donnees()
            actualiser_liste()

            popup.destroy()

        tk.Button(
            popup,
            text="Ajouter",
            bg=BLUE,
            fg="white",
            relief="flat",
            padx=25,
            pady=8,
            command=enregistrer
        ).pack(pady=15)

    def supprimer_deduction():
        selection = liste_deductions.curselection()

        if not selection:
            messagebox.showwarning(
                "Attention",
                "Sélectionne une déduction."
            )
            return

        index = selection[0]
        nom = deductions[index]["nom"]

        confirmation = messagebox.askyesno(
            "Confirmation",
            f'Supprimer "{nom}" ?',
            parent=fenetre_deductions
        )

        if confirmation:
            deductions.pop(index)
            sauvegarder_donnees()
            actualiser_liste()

    def activer_desactiver():
        selection = liste_deductions.curselection()

        if not selection:
            messagebox.showwarning(
                "Attention",
                "Sélectionne une déduction."
            )
            return

        index = selection[0]

        deductions[index]["active"] = not deductions[
            index
        ].get("active", True)

        sauvegarder_donnees()
        actualiser_liste()

    frame_boutons = tk.Frame(
        fenetre_deductions,
        bg=BG
    )

    frame_boutons.pack(pady=10)

    tk.Button(
        frame_boutons,
        text="Ajouter",
        bg=GREEN,
        fg="white",
        relief="flat",
        padx=15,
        pady=8,
        command=ajouter_deduction
    ).grid(
        row=0,
        column=0,
        padx=5
    )

    tk.Button(
        frame_boutons,
        text="Activer / Désactiver",
        bg=BLUE,
        fg="white",
        relief="flat",
        padx=15,
        pady=8,
        command=activer_desactiver
    ).grid(
        row=0,
        column=1,
        padx=5
    )

    tk.Button(
        frame_boutons,
        text="Supprimer",
        bg=RED,
        fg="white",
        relief="flat",
        padx=15,
        pady=8,
        command=supprimer_deduction
    ).grid(
        row=0,
        column=2,
        padx=5
    )

    actualiser_liste()


def reset_budget():
    global payes, achats, deductions

    if messagebox.askyesno(
        "Confirmation",
        "Supprimer toutes les données ?"
    ):
        payes.clear()
        achats.clear()
        deductions.clear()

        sauvegarder_donnees()
        afficher_tout()


def vider_champs():
    entree_description.delete(
        0,
        tk.END
    )

    entree_montant.delete(
        0,
        tk.END
    )

    est_une_paye.set(False)


def afficher_tout():
    afficher_budget()
    afficher_historique()
    afficher_bilans()


charger_donnees()

fenetre = tk.Tk()

BG = "#F5F5F7"
CARD = "#FFFFFF"
BLUE = "#007AFF"
RED = "#FF3B30"
GREEN = "#34C759"
TEXT = "#1D1D1F"
SECONDARY = "#8E8E93"
PURPLE = "#5856D6"

fenetre.configure(
    bg=BG
)

fenetre.title(
    "Gestionnaire de Budget"
)

fenetre.minsize(
    600,
    700
)

fenetre.resizable(
    True,
    True
)


titre = tk.Label(
    fenetre,
    text="Gestionnaire de Budget",
    font=("Helvetica", 20, "bold"),
    bg=BG,
    fg=TEXT
)

titre.pack(pady=15)


tk.Label(
    fenetre,
    text="Description",
    bg=BG,
    fg=TEXT
).pack()


entree_description = tk.Entry(
    fenetre,
    width=40,
    relief="flat",
    bg="white",
    font=("Helvetica", 12),
    highlightthickness=1,
    highlightbackground="#D1D1D6"
)

entree_description.pack(
    pady=5
)


tk.Label(
    fenetre,
    text="Montant (€)",
    bg=BG,
    fg=TEXT
).pack()


entree_montant = tk.Entry(
    fenetre,
    width=40,
    relief="flat",
    bg="white",
    font=("Helvetica", 12),
    highlightthickness=1,
    highlightbackground="#D1D1D6"
)

entree_montant.pack(
    pady=5
)


est_une_paye = tk.BooleanVar(
    value=False
)

checkbox_paye = tk.Checkbutton(
    fenetre,
    text="Appliquer les déductions",
    variable=est_une_paye,
    bg=BG,
    fg=TEXT,
    activebackground=BG,
    font=("Helvetica", 11, "bold")
)

checkbox_paye.pack(
    pady=8
)


frame_boutons = tk.Frame(
    fenetre,
    bg=BG
)

frame_boutons.pack(
    pady=10
)


btn_paye = tk.Button(
    frame_boutons,
    text="Ajouter une somme",
    bg=GREEN,
    fg="white",
    activebackground=GREEN,
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    font=("Helvetica", 11, "bold"),
    cursor="hand2",
    command=ajouter_somme
)

btn_paye.grid(
    row=0,
    column=0,
    padx=5
)


btn_achat = tk.Button(
    frame_boutons,
    text="Ajouter un achat",
    bg=RED,
    fg="white",
    activebackground=RED,
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    font=("Helvetica", 11, "bold"),
    cursor="hand2",
    command=ajouter_achat
)

btn_achat.grid(
    row=0,
    column=1,
    padx=5
)


btn_deductions = tk.Button(
    frame_boutons,
    text="⚙ Déductions",
    bg=BLUE,
    fg="white",
    activebackground=BLUE,
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    font=("Helvetica", 11, "bold"),
    cursor="hand2",
    command=ouvrir_deductions
)

btn_deductions.grid(
    row=0,
    column=2,
    padx=5
)


btn_reset = tk.Button(
    frame_boutons,
    text="Réinitialiser",
    bg=SECONDARY,
    fg="white",
    activebackground=SECONDARY,
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    font=("Helvetica", 11, "bold"),
    cursor="hand2",
    command=reset_budget
)

btn_reset.grid(
    row=0,
    column=3,
    padx=5
)


btn_calendrier = tk.Button(
    frame_boutons,
    text="📅 Calendrier",
    bg=PURPLE,
    fg="white",
    activebackground=PURPLE,
    relief="flat",
    bd=0,
    padx=25,
    pady=10,
    font=("Helvetica", 11, "bold"),
    cursor="hand2",
    command=ouvrir_calendrier
)

btn_calendrier.grid(
    row=1,
    column=0,
    columnspan=4,
    pady=(8, 0)
)


frame_budget = tk.Frame(
    fenetre,
    bg=CARD,
    bd=1,
    relief="solid"
)

frame_budget.pack(
    fill="x",
    padx=20,
    pady=15
)


label_revenus = tk.Label(
    frame_budget,
    text="",
    bg=CARD,
    fg=BLUE
)

label_revenus.pack(
    anchor="w",
    padx=10,
    pady=3
)


label_depenses = tk.Label(
    frame_budget,
    text="",
    bg=CARD,
    fg=TEXT
)

label_depenses.pack(
    anchor="w",
    padx=10,
    pady=3
)


label_solde = tk.Label(
    frame_budget,
    text="",
    bg=CARD,
    font=("Helvetica", 12, "bold")
)

label_solde.pack(
    anchor="w",
    padx=10,
    pady=5
)


frame_historique = tk.LabelFrame(
    fenetre,
    text="Historique",
    bg=BG,
    fg=TEXT,
    font=("Helvetica", 11, "bold")
)

frame_historique.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)


frame_historiques = tk.Frame(
    frame_historique,
    bg=BG
)

frame_historiques.pack(
    fill="both",
    expand=True,
    padx=5,
    pady=5
)


frame_entrees = tk.LabelFrame(
    frame_historiques,
    text="💰 Entrées",
    bg=BG,
    fg=GREEN,
    font=("Helvetica", 10, "bold")
)

frame_entrees.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(0, 5)
)


scrollbar_entrees = tk.Scrollbar(
    frame_entrees
)

liste_entrees = tk.Listbox(
    frame_entrees,
    height=8,
    yscrollcommand=scrollbar_entrees.set,
    font=("Helvetica", 10),
    fg=GREEN
)

scrollbar_entrees.config(
    command=liste_entrees.yview
)

liste_entrees.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar_entrees.pack(
    side="right",
    fill="y"
)


btn_supprimer_entree = tk.Button(
    frame_entrees,
    text="Supprimer l'entrée",
    bg=RED,
    fg="white",
    activebackground=RED,
    relief="flat",
    bd=0,
    padx=10,
    pady=6,
    font=("Helvetica", 10, "bold"),
    cursor="hand2",
    command=supprimer_entree
)

btn_supprimer_entree.pack(
    pady=8
)


frame_sorties = tk.LabelFrame(
    frame_historiques,
    text="🛒 Sorties",
    bg=BG,
    fg=RED,
    font=("Helvetica", 10, "bold")
)

frame_sorties.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(5, 0)
)


scrollbar_sorties = tk.Scrollbar(
    frame_sorties
)

liste_sorties = tk.Listbox(
    frame_sorties,
    height=8,
    yscrollcommand=scrollbar_sorties.set,
    font=("Helvetica", 10),
    fg=RED
)

scrollbar_sorties.config(
    command=liste_sorties.yview
)

liste_sorties.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar_sorties.pack(
    side="right",
    fill="y"
)


btn_supprimer_sortie = tk.Button(
    frame_sorties,
    text="🗑 Supprimer la sortie",
    bg=RED,
    fg="white",
    activebackground=RED,
    relief="flat",
    bd=0,
    padx=10,
    pady=6,
    font=("Helvetica", 10, "bold"),
    cursor="hand2",
    command=supprimer_sortie
)

btn_supprimer_sortie.pack(
    pady=8
)


frame_bilan = tk.LabelFrame(
    fenetre,
    text="Bilans",
    bg=BG,
    fg=TEXT
)

frame_bilan.pack(
    fill="x",
    padx=20,
    pady=10
)


label_bilan_mois = tk.Label(
    frame_bilan,
    bg=BG,
    fg=TEXT
)

label_bilan_mois.pack(
    anchor="w",
    padx=10,
    pady=3
)


label_bilan_annee = tk.Label(
    frame_bilan,
    bg=BG,
    fg=TEXT
)

label_bilan_annee.pack(
    anchor="w",
    padx=10,
    pady=3
)


afficher_tout()

fenetre.mainloop()