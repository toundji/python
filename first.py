import datetime
import flet as ft
import urllib.parse
import webbrowser

# --- 1. BASE DE DONNÉES DES PAROISSES ---
paroisses_db = {
    "St-Michel de Cotonou": {"horaires": ["06h30", "08h30", "11h00", "18h30"], "demandes": []},
    "Ste-Anne": {"horaires": ["07h00", "19h00"], "demandes": []},
    "Sacré-Cœur de Akpakpa": {"horaires": ["06h30", "08h30", "18h30"], "demandes": []},
    "St Pierre de Tokan": {"horaires": ["06h30", "08h30", "18h30"], "demandes": []},
    "Bon Pasteur de COTONOU": {"horaires": ["06h30", "08h30", "18h30"], "demandes": []},
}

# --- 2. LOGIQUE DE GÉNÉRATION DU REÇU ---
def generer_recu(nom, prenom, paroisse, type_messe, detail, montant=2000):
    date_actuelle = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    prix_messe = montant
    frais_retrait = 125
    frais_app = 5
    total_a_payer = prix_messe + frais_retrait + frais_app
    
    recu = f"""
{"="*40}
   RECU DE DEMANDE DE MESSE
{"-"*40}
Date       : {date_actuelle}
Paroisse   : {paroisse}
Fidèle     : {prenom} {nom}
Type       : {type_messe}
Intention  : {detail}
----------------------------------------
DÉTAILS DES FRAIS :
- Messe            : {prix_messe} FCFA
- Frais de retrait : {frais_retrait} FCFA
- Service App      : {frais_app} FCFA

TOTAL À PAYER      : {total_a_payer} FCFA
{"="*40}
Merci pour votre foi et votre soutien.
"""
    return recu

# --- 3. INTERFACE GRAPHIQUE (FLET) ---
def main(page: ft.Page):
    page.title = "Ma Paroisse - Demande de Messe"
    page.window_width = 450
    page.window_height = 850
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- ÉLÉMENTS DU FORMULAIRE ---
    nom_input = ft.TextField(label="Nom du Fidèle", prefix_icon=ft.Icons.PERSON)
    prenom_input = ft.TextField(label="Prénom du Fidèle")
    
    paroisse_dropdown = ft.Dropdown(
        label="Choisir la Paroisse",
        options=[ft.dropdown.Option(p) for p in paroisses_db.keys()],
        value="St-Michel de Cotonou"
    )
    
    type_messe = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="Action de grâce", label="Action de grâce"),
        ft.Radio(value="Repos de l'âme", label="Repos de l'âme"),
    ]))
    
    intention_input = ft.TextField(
        label="Intention détaillée", 
        multiline=True, 
        min_lines=3,
        hint_text="Décrivez votre intention ici..."
    )

    affichage_recu = ft.Text(value="", font_family="Courier", size=12)

    # --- ACTIONS ---
    def valider_demande(e):
        if not nom_input.value or not intention_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("Veuillez remplir tous les champs !"))
            page.snack_bar.open = True
            page.update()
            return

        texte = generer_recu(
            nom=nom_input.value.upper(),
            prenom=prenom_input.value.capitalize(),
            paroisse=paroisse_dropdown.value,
            type_messe=type_messe.value if type_messe.value else "Ordinaire",
            detail=intention_input.value
        )
        affichage_recu.value = texte
        page.update()

    def partager_whatsapp(e):
        if affichage_recu.value:
            message = urllib.parse.quote(affichage_recu.value)
            webbrowser.open(f"https://wa.me/?text={message}")

    def nouvelle_demande(e):
        nom_input.value = ""
        prenom_input.value = ""
        intention_input.value = ""
        affichage_recu.value = ""
        page.update()

    # --- MISE EN PAGE ---
    page.add(
        ft.Text("DEMANDE DE MESSE EN LIGNE", size=24, weight="bold", color="blue"),
        ft.Divider(),
        nom_input,
        prenom_input,
        paroisse_dropdown,
        ft.Text("Type de messe :", weight="bold"),
        type_messe,
        intention_input,
        ft.Row([
            ft.ElevatedButton(
                "Générer le reçu", 
                icon=ft.Icons.RECEIPT_LONG, 
                on_click=valider_demande,
                style=ft.ButtonStyle(bgcolor="blue", color="white")
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH, 
                on_click=nouvelle_demande,
                tooltip="Nouvelle demande"
            ),
        ], alignment=ft.MainAxisAlignment.CENTER),
        
        ft.Divider(),
        
        ft.Text("VOTRE REÇU GÉNÉRÉ :", weight="bold"),
        ft.Container(
            content=affichage_recu,
            bgcolor="#f4f4f4",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#cccccc")
        ),
        
        ft.ElevatedButton(
            "Envoyer via WhatsApp", 
            icon=ft.Icons.SHARE, 
            on_click=partager_whatsapp,
            style=ft.ButtonStyle(bgcolor="green", color="white")
        )
    )

# --- 4. LANCEMENT ---
if __name__ == "__main__":
    ft.app(target=main)


