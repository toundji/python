from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import logging
from functools import wraps

app = Flask(__name__)
app.jinja_env.globals.update(getattr=getattr)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'eglise_benin_2026_pro_secure')

# Configuration de la base de données : PostgreSQL en production, SQLite en développement
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Render fournit postgres://, mais SQLAlchemy nécessite postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # En local, utiliser SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paroisses.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration du dossier uploads
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')

db = SQLAlchemy(app)

# ==========================================
# UTILITAIRES DYNAMIQUES
# ==========================================
def generer_paroisses_data():
    """Récupère dynamiquement les horaires pour le JavaScript du formulaire"""
    paroisses = Paroisse.query.all()
    data = {}
    for p in paroisses:
        data[str(p.id)] = {
            "0": p.h_dimanche or "À préciser",
            "1": p.h_lundi or "À préciser",
            "2": p.h_mardi or "À préciser",
            "3": p.h_mercredi or "À préciser",
            "4": p.h_jeudi or "À préciser",
            "5": p.h_vendredi or "À préciser",
            "6": p.h_samedi or "À préciser"
        }
    return data

# ==========================================
# MODÈLES DE DONNÉES (DYNAMIC SCHEMA)
# ==========================================
class Paroisse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    ville = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20))
    code = db.Column(db.String(20), nullable=False, unique=True)
    annonce = db.Column(db.Text, default="")
    num_mtn = db.Column(db.String(20), nullable=True)
    num_moov = db.Column(db.String(20), nullable=True)
    num_celtiis = db.Column(db.String(20), nullable=True)
    # Horaires dynamiques
    h_lundi = db.Column(db.String(100), default="À préciser")
    h_mardi = db.Column(db.String(100), default="À préciser")
    h_mercredi = db.Column(db.String(100), default="À préciser")
    h_jeudi = db.Column(db.String(100), default="À préciser")
    h_vendredi = db.Column(db.String(100), default="À préciser")
    h_samedi = db.Column(db.String(100), default="À préciser")
    h_dimanche = db.Column(db.String(100), default="À préciser")
    evenement_special = db.Column(db.String(100), nullable=True)
    date_limite_special = db.Column(db.DateTime, nullable=True)
    # Relation pour faciliter les requêtes
    intentions = db.relationship('Intention', backref='paroisse', lazy=True, cascade="all, delete-orphan")

class Intention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donateur = db.Column(db.String(100))
    paroisse_id = db.Column(db.Integer, db.ForeignKey('paroisse.id'))
    date_messe = db.Column(db.String(20)) 
    heure_messe = db.Column(db.String(10))
    type_messe = db.Column(db.String(50))
    texte = db.Column(db.Text)
    id_transaction = db.Column(db.String(100), unique=False, nullable=True)
    preuve_paiement = db.Column(db.String(200), nullable=True)
    paye = db.Column(db.Boolean, default=False)
    telephone = db.Column(db.String(20)) 
    nature_id = db.Column(db.String(10))
    groupe_id = db.Column(db.String(50))

# ==========================================
# SÉCURITÉ & AUTH
# ==========================================
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == "Colas" and auth.password == "kolawole@1996"):
            return Response('Accès réservé au panneau de configuration MESHORA.', 401, 
                            {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

# ==========================================
# ROUTES PUBLIQUES (DYNAMIQUES)
# ==========================================
@app.route('/')
def index():
    paroisses = Paroisse.query.all()
    return render_template('index.html', paroisses=paroisses)

@app.route('/liste')
def liste():
    paroisses = Paroisse.query.all()
    return render_template('liste.html', paroisses=paroisses)

@app.route('/paroisse/<int:id>')
def details_paroisse(id):
    paroisse = db.session.get(Paroisse, id)
    if not paroisse:
        flash("Paroisse introuvable", "danger")
        return redirect(url_for('liste'))
    return render_template('details.html', paroisse=paroisse)

@app.route('/demande', methods=['GET', 'POST'])
def demande():
    paroisses = Paroisse.query.all()
    if request.method == 'POST':
        return traiter_demande_post()
    return render_template('demande.html', 
                           paroisses=paroisses, 
                           paroisses_data=generer_paroisses_data(),
                           paroisse=None, 
                           special_disponible=False)

@app.route('/demande-messe/<int:paroisse_id>', methods=['GET', 'POST'])
def demande_messe(paroisse_id):
    paroisse = Paroisse.query.get_or_404(paroisse_id)
    maintenant = datetime.now()
    if request.method == 'POST':
        return traiter_demande_post()

    special_disponible = False
    if paroisse.date_limite_special and maintenant <= paroisse.date_limite_special:
        special_disponible = True

    return render_template('demande.html', 
                           paroisse=paroisse, 
                           paroisses=[paroisse], 
                           special_disponible=special_disponible,
                           paroisses_data=generer_paroisses_data())

def traiter_demande_post():
    p_id_raw = request.form.get('paroisse_id')
    type_m = request.form.get('type_messe', 'Simple')
    
    # --- CONVERSION DE LA NATURE EN CODE ID ---
    nature_brute = request.form.get('nature', '')
    
    if "Grâce" in nature_brute:
        n_id = "MAG"
    elif "Repos" in nature_brute or "âme" in nature_brute:
        n_id = "MRA"
    else:
        n_id = "IS"

    nom_donateur = request.form.get('nom')
    tel_donateur = request.form.get('telephone')
    groupe_unique_id = str(uuid.uuid4())[:8]

    dico_jours = {'Simple': 1, 'Triduum': 3, 'Neuvaine': 9, 'Trentain': 30, 'special': 1}
    nb_jours = dico_jours.get(type_m, 1)

    try:
        p_id = int(p_id_raw)
        for i in range(1, nb_jours + 1):
            d_brute = request.form.get(f'date_{i}')
            h_brute = request.form.get(f'heure_{i}')
            t_txt = request.form.get(f'texte_{i}')

            if d_brute and h_brute:
                date_obj = datetime.strptime(d_brute, '%Y-%m-%d')
                date_fr = date_obj.strftime('%d/%m/%Y')
                
                nouvelle_intention = Intention(
                    donateur=nom_donateur,
                    telephone=tel_donateur,
                    paroisse_id=p_id,
                    date_messe=date_fr,
                    heure_messe=h_brute,
                    type_messe=type_m,
                    nature_id=n_id,
                    texte=t_txt,
                    groupe_id=groupe_unique_id
                )
                db.session.add(nouvelle_intention)

        db.session.commit()
        return redirect(url_for('etape_paiement', groupe_id=groupe_unique_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'enregistrement : {str(e)}", "danger")
        return redirect(url_for('demande'))

@app.route('/paiement/<groupe_id>', methods=['GET', 'POST'])
def etape_paiement(groupe_id):
    intentions = Intention.query.filter_by(groupe_id=groupe_id).all()
    if not intentions: 
        return redirect(url_for('demande'))
    
    paroisse_obj = db.session.get(Paroisse, intentions[0].paroisse_id)
    tarifs = {'Simple': 2000, 'Triduum': 6000, 'Neuvaine': 18000, 'Trentain': 60000, 'special': 500}
    prix_base = tarifs.get(intentions[0].type_messe, 2000)

    if request.method == 'POST':
        id_transac = request.form.get('id_transaction')
        photo = request.files.get('preuve_paiement')
        
        if photo and id_transac:
            # Sécurité : vérifier si l'ID transaction existe déjà pour un AUTRE groupe
            deja_utilise = Intention.query.filter(
                Intention.id_transaction == id_transac, 
                Intention.groupe_id != groupe_id
            ).first()
            
            if deja_utilise:
                flash("Ce code de transaction a déjà été validé pour une autre demande.", "warning")
                return redirect(request.url)

            filename = secure_filename(f"pay_{groupe_id}_{id_transac}.jpg")
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            for intention in intentions:
                intention.id_transaction = id_transac
                intention.preuve_paiement = filename
                intention.paye = True
            
            db.session.commit()
            
            donnees_recu = {
                'donateur': intentions[0].donateur, 
                'paroisse': paroisse_obj.nom,
                'date_messe': intentions[0].date_messe, 
                'telephone': intentions[0].telephone,   
                'type_messe': intentions[0].type_messe, 
                'intention': intentions[0].texte,
                'offrande': prix_base, 
                'service': 50, 
                'total': prix_base + 50, 
                'date_recu': datetime.now().strftime('%d/%m/%Y à %H:%M')
            }
            return render_template('recu.html', recu=donnees_recu)
            
    return render_template('paiement.html', intentions=intentions, paroisse=paroisse_obj, prix=prix_base)

# ==========================================
# ESPACE PAROISSE (AUTHENTIFICATION)
# ==========================================
@app.route('/espace-paroisse', methods=['GET', 'POST'])
def login_paroisse():
    if request.method == 'POST':
        code_saisi = request.form.get('code_admin')
        paroisse = Paroisse.query.filter_by(code=code_saisi).first()
        if paroisse:
            return redirect(url_for('update_paroisse', id=paroisse.id))
        flash("Code secret incorrect", "danger")
    return render_template('espace_paroisse.html')

@app.route('/modifier-paroisse/<int:id>', methods=['GET', 'POST'])
def update_paroisse(id):
    paroisse = db.session.get(Paroisse, id)
    if not paroisse: 
        return redirect(url_for('login_paroisse'))

    if request.method == 'POST':
        try:
            # Mise à jour dynamique de tous les champs
            for field in ['annonce', 'telephone', 'num_mtn', 'num_moov', 'num_celtiis', 
                          'h_lundi', 'h_mardi', 'h_mercredi', 'h_jeudi', 'h_vendredi', 
                          'h_samedi', 'h_dimanche', 'evenement_special']:
                setattr(paroisse, field, request.form.get(field))
            
            limite = request.form.get('date_limite_special')
            paroisse.date_limite_special = datetime.strptime(limite, '%Y-%m-%d') if limite else None
                
            db.session.commit()
            flash("Mise à jour réussie !", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for('update_paroisse', id=id))
        
    return render_template('gestion_paroisse.html', paroisse=paroisse)

@app.route('/modifier-code-secret/<int:id>', methods=['POST'])
def changer_code_paroisse(id):
    paroisse = db.session.get(Paroisse, id)
    ancien = request.form.get('ancien_code')
    nouveau = request.form.get('nouveau_code')
    confirme = request.form.get('confirmation_code')

    if paroisse and paroisse.code == ancien:
        if nouveau == confirme and len(nouveau) >= 4:
            paroisse.code = nouveau
            db.session.commit()
            flash("🔐 Code secret mis à jour !", "success")
        else:
            flash("⚠️ Erreur de confirmation ou code trop court.", "warning")
    else:
        flash("⚠️ Ancien code incorrect.", "danger")
    
    return redirect(url_for('update_paroisse', id=id))

# ==========================================
# GESTION INTENTIONS & PAIEMENTS
# ==========================================
@app.route('/espace-paroisse/intentions/<int:paroisse_id>')
def gestion_intentions(paroisse_id):
    paroisse = db.session.get(Paroisse, paroisse_id)
    date_html = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    date_db = datetime.strptime(date_html, '%Y-%m-%d').strftime('%d/%m/%Y')

    intentions = Intention.query.filter_by(
        paroisse_id=paroisse_id, 
        date_messe=date_db, 
        paye=True
    ).all()

    intentions_par_heure = {}
    for i in intentions:
        intentions_par_heure.setdefault(i.heure_messe, []).append(i)
        
    return render_template('intention_paroisse.html', 
                           intentions_par_heure=intentions_par_heure, 
                           paroisse=paroisse, 
                           date_selectionnee=date_html)

@app.route('/espace-paroisse/paiements/<int:paroisse_id>')
def gestion_paiements(paroisse_id):
    paroisse = db.session.get(Paroisse, paroisse_id)
    paiements = Intention.query.filter_by(paroisse_id=paroisse_id, paye=True).order_by(Intention.id.desc()).all()
    return render_template('paiements_paroisse.html', paiements=paiements, paroisse=paroisse)

# ==========================================
# PANNEAU ADMIN GÉNÉRAL (MESHORA ADMIN)
# ==========================================
@app.route('/panneau-secret-meshora-2026', methods=['GET', 'POST'], endpoint='admin_prive')
@requires_auth
def admin_prive():
    if request.method == 'POST':
        p = Paroisse(
            nom=request.form.get('nom'), 
            ville=request.form.get('ville'),
            code=request.form.get('code'), 
            num_mtn=request.form.get('num_mtn'),
            num_moov=request.form.get('num_moov'), 
            num_celtiis=request.form.get('num_celtiis')
        )
        db.session.add(p)
        db.session.commit()
        flash("Nouvelle paroisse ajoutée au réseau MESHORA", "success")
        return redirect(url_for('admin_prive'))
        
    paroisses = Paroisse.query.all()
    return render_template('admin.html', paroisses=paroisses)

@app.route('/delete_paroisse/<int:id>')
@requires_auth
def delete_paroisse(id):
    p = db.session.get(Paroisse, id)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash("Paroisse supprimée.", "info")
    return redirect(url_for('admin_prive'))

# ==========================================
# INITIALISATION ET LANCEMENT
# ==========================================
# Initialisation de la base de données
with app.app_context():
    # Création du dossier uploads s'il n'existe pas
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)