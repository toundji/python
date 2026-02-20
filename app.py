from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'eglise_benin_2026_pro_secure')

# Configuration de la base de données : PostgreSQL en production, SQLite en développement
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Render fournit postgres://, mais SQLAlchemy nécessite postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paroisses.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================================
# MODÈLES DE DONNÉES
# ==========================================
class Paroisse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    ville = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20))
    code = db.Column(db.String(20), nullable=False, unique=True)
    annonce = db.Column(db.Text, default="")
    h_lundi = db.Column(db.String(100), default="À préciser")
    h_mardi = db.Column(db.String(100), default="À préciser")
    h_mercredi = db.Column(db.String(100), default="À préciser")
    h_jeudi = db.Column(db.String(100), default="À préciser")
    h_vendredi = db.Column(db.String(100), default="À préciser")
    h_samedi = db.Column(db.String(100), default="À préciser")
    h_dimanche = db.Column(db.String(100), default="À préciser")

class Intention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donateur = db.Column(db.String(100))
    paroisse_id = db.Column(db.Integer, db.ForeignKey('paroisse.id'))
    date_messe = db.Column(db.String(20)) # Format DD/MM/YYYY
    heure_messe = db.Column(db.String(10))
    type_messe = db.Column(db.String(50))
    texte = db.Column(db.Text)

@app.route('/favicon.ico')
def favicon():
    return "", 204

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/liste')
def liste():
    paroisses = Paroisse.query.all()
    return render_template('liste.html', paroisses=paroisses)

@app.route('/paroisse/<int:id>')
def details_paroisse(id):
    paroisse = db.session.get(Paroisse, id)
    if not paroisse:
        flash("Paroisse introuvable")
        return redirect(url_for('liste'))
    return render_template('details.html', paroisse=paroisse, getattr=getattr)

# ==========================================
# ROUTE DEMANDE DE MESSE (BOUCLE DE FIXATION)
# ==========================================
@app.route('/demande', methods=['GET', 'POST'])
def demande():
    paroisses = Paroisse.query.all()
    paroisses_data = {
        str(p.id): {
            "0": p.h_dimanche, "1": p.h_lundi, "2": p.h_mardi,
            "3": p.h_mercredi, "4": p.h_jeudi, "5": p.h_vendredi, "6": p.h_samedi
        } for p in paroisses
    }

    if request.method == 'POST':
        p_id_raw = request.form.get('paroisse_id')
        type_m = request.form.get('type_messe', 'simple').lower()
        nom_donateur = request.form.get('nom')
        
        # Définition du nombre de boucles à effectuer
        dico_jours = {'simple': 1, 'triduum': 3, 'neuvaine': 9, 'trentain': 30}
        nb_jours = dico_jours.get(type_m, 1)
        
        try:
            p_id = int(p_id_raw)
            paroisse_obj = db.session.get(Paroisse, p_id)
            maintenant = datetime.now()

            # On boucle sur chaque champ envoyé par le JavaScript
            for i in range(1, nb_jours + 1):
                d_brute = request.form.get(f'date_{i}')
                h_brute = request.form.get(f'heure_{i}')
                t_txt = request.form.get(f'texte_{i}')

                if d_brute and h_brute:
                    # Nettoyage et conversion
                    h_propre = h_brute.replace('h', ':').replace('H', ':')
                    # Conversion de la date AAAA-MM-JJ en JJ/MM/AAAA
                    date_objet = datetime.strptime(d_brute, '%Y-%m-%d')
                    date_fr = date_objet.strftime('%d/%m/%Y')

                    # Vérification 2h (uniquement sur le premier jour pour ne pas bloquer les suivants)
                    if i == 1:
                        moment_messe = datetime.strptime(f"{d_brute} {h_propre}", "%Y-%m-%d %H:%M")
                        if moment_messe < maintenant + timedelta(hours=2):
                            flash("La première messe doit être dans au moins 2 heures.")
                            return redirect(url_for('demande'))

                    # Création d'une nouvelle ligne d'intention pour chaque jour
                    nouvelle_intention = Intention(
                        donateur=nom_donateur,
                        paroisse_id=p_id,
                        date_messe=date_fr,
                        heure_messe=h_propre,
                        type_messe=type_m.capitalize(),
                        texte=t_txt if t_txt else f"Intention pour le jour {i}"
                    )
                    db.session.add(nouvelle_intention)
            
            # On valide tous les enregistrements d'un coup
            db.session.commit()

            # Tarifs pour le reçu
            tarifs = {'simple': 2000, 'triduum': 6000, 'neuvaine': 18000, 'trentain': 60000}
            prix_offrande = tarifs.get(type_m, 2000)

            return render_template('recu.html', recu={
                'donateur': nom_donateur,
                'paroisse': paroisse_obj.nom,
                'type_messe': type_m.capitalize(),
                'offrande': prix_offrande,
                'service': 50,
                'total': prix_offrande + 50,
                'date_reçu': maintenant.strftime('%d/%m/%Y à %H:%M')
            })

        except Exception as e:
            db.session.rollback()
            print(f"ERREUR : {e}")
            flash("Une erreur est survenue lors de l'enregistrement.")
            return redirect(url_for('demande'))

    return render_template('demande.html', paroisses=paroisses, paroisses_data=paroisses_data)

# ==========================================
# ESPACE PAROISSE & ADMIN (INCHANGÉS)
# ==========================================
@app.route('/espace-paroisse', methods=['GET', 'POST'])
def login_paroisse():
    if request.method == 'POST':
        code_saisi = request.form.get('code_admin')
        paroisse = Paroisse.query.filter_by(code=code_saisi).first()
        if paroisse:
            return render_template('gestion_paroisse.html', paroisse=paroisse, getattr=getattr)
        flash("Code secret incorrect")
    return render_template('espace_paroisse.html')

@app.route('/espace-paroisse/intentions/<int:paroisse_id>')
def gestion_intentions(paroisse_id):
    paroisse = db.session.get(Paroisse, paroisse_id)
    if not paroisse: return "404", 404
    date_html = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        date_db = datetime.strptime(date_html, '%Y-%m-%d').strftime('%d/%m/%Y')
    except:
        date_db = datetime.now().strftime('%d/%m/%Y')
    intentions = Intention.query.filter_by(paroisse_id=paroisse_id, date_messe=date_db).all()
    intentions_par_heure = {}
    for i in intentions:
        intentions_par_heure.setdefault(i.heure_messe, []).append(i)
    return render_template('intention_paroisse.html', intentions_par_heure=intentions_par_heure, paroisse=paroisse, date_selectionnee=date_html)

@app.route('/modifier-paroisse/<int:id>', methods=['POST'])
def update_paroisse(id):
    paroisse = db.session.get(Paroisse, id)
    if paroisse:
        paroisse.annonce = request.form.get('annonce')
        paroisse.telephone = request.form.get('telephone')
        for j in ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']:
            setattr(paroisse, f'h_{j}', request.form.get(f'h_{j}'))
        db.session.commit()
        flash("Mise à jour réussie !")
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        try:
            p = Paroisse(nom=request.form.get('nom'), ville=request.form.get('ville'), code=request.form.get('code'), telephone=request.form.get('telephone'))
            db.session.add(p)
            db.session.commit()
            flash(f"Paroisse {p.nom} ajoutée.")
        except:
            db.session.rollback()
            flash("Erreur : Le code doit être unique.")
        return redirect(url_for('admin'))
    return render_template('admin.html', paroisses=Paroisse.query.all())

# Initialisation de la base de données
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
