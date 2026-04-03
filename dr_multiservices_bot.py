import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from openai import OpenAI

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

client = OpenAI()

DR_MULTISERVICES_INFO = """
Vous etes un assistant IA pour DR MULTISERVICES, une entreprise marocaine specialisee dans les solutions professionnelles pour batiments intelligents.

Informations cles sur DR MULTISERVICES :
- Activite : Solutions professionnelles en climatisation, chauffage, electricite, energies renouvelables, securite, chambre froide, renovation/peinture, CVC intelligent.
- Slogan : "Votre partenaire de confiance pour batiments intelligents"
- Telephone : +212 6 61 84 46 73 (7j/7, urgences 24h/24)
- Email : karimi@dr-multiservices.com
- Site web : https://dr-multiservices.com/
- Horaires : Lundi-Samedi 8h-18h, Dimanche sur RDV, Urgences 24h/7
- Zone : Tout le Maroc
- Experience : +20 ans, certifie ISO, +450 clients satisfaits
- Tarifs indicatifs :
    - Split 9000 BTU: 4500-7000 DH
    - Split 12000 BTU: 5500-8500 DH
    - Split 18000 BTU: 7000-11000 DH
    - Multi-Split 2 unites: 12000-18000 DH
    - Multi-Split 3 unites: 16000-24000 DH
    - VRV/VRF: a partir de 50000 DH
    - Solaire 3kWc: 30000-38000 DH
    - Solaire 5kWc: 45000-58000 DH
    - Solaire 10kWc: 85000-110000 DH
    - Solaire 20kWc: 160000-200000 DH
- Garanties : 2 ans travaux, constructeur 2-5 ans, compresseur jusqu'a 10 ans, panneaux solaires 25 ans
- Marques : Daikin, Mitsubishi Electric, LG, Samsung, Carrier, Toshiba, Bosch, Viessmann, Atlantic, Hikvision, Dahua, SunPower, Jinko Solar

Repondez aux questions des clients de maniere professionnelle, chaleureuse et informative. Ne pas utiliser de Markdown. Texte brut uniquement.
"""

SERVICE_DETAILS = {
    'climatisation': {
        'emoji': '🌀', 'title': 'Climatisation',
        'description': (
            "Chez DR MULTISERVICES, nous vous offrons des solutions completes de climatisation pour un confort optimal ! "
            "Nos services incluent l'installation, la maintenance preventive, le depannage rapide et la reparation de tous types de systemes. "
            "Nous intervenons sur les splits muraux, multi-splits, VRV/VRF, systemes centralises, cassettes et gainables. "
            "Nous travaillons avec les plus grandes marques : Daikin, Mitsubishi Electric, LG, Samsung, Carrier, Toshiba. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Tarifs indicatifs (installation incluse) :\n"
            "  - Split 9000 BTU: 4500-7000 DH\n"
            "  - Split 12000 BTU: 5500-8500 DH\n"
            "  - Split 18000 BTU: 7000-11000 DH\n"
            "  - Multi-Split 2 unites: 12000-18000 DH\n"
            "  - Multi-Split 3 unites: 16000-24000 DH\n"
            "  - VRV/VRF: a partir de 50000 DH\n\n"
            "Nos garanties : 2 ans sur les travaux, 2-5 ans constructeur, jusqu'a 10 ans sur le compresseur."
        ),
        'quote_callback': 'request_quote_climatisation'
    },
    'chauffage': {
        'emoji': '🔥', 'title': 'Chauffage',
        'description': (
            "Restez au chaud avec nos solutions de chauffage performantes et economiques ! "
            "DR MULTISERVICES installe et entretient vos pompes a chaleur (air/eau, air/air), chaudieres (gaz, fioul), systemes de chauffage central, planchers chauffants et radiateurs. "
            "Nous collaborons avec des marques de renom : Bosch, Viessmann, Atlantic, De Dietrich, Vaillant. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Nos garanties : 2 ans sur les travaux, 2-5 ans constructeur."
        ),
        'quote_callback': 'request_quote_chauffage'
    },
    'electricite': {
        'emoji': '⚡', 'title': 'Electricite',
        'description': (
            "Pour une installation electrique sure et conforme, faites confiance a DR MULTISERVICES ! "
            "Nous realisons l'installation complete, la mise aux normes, l'installation de tableaux electriques, la domotique et maison connectee, l'eclairage LED et le cablage reseau. "
            "Nos electriciens qualifies vous garantissent un travail impeccable. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Nos garanties : 2 ans sur les travaux."
        ),
        'quote_callback': 'request_quote_electricite'
    },
    'energies_renouvelables': {
        'emoji': '☀️', 'title': 'Energies Renouvelables',
        'description': (
            "Passez a l'energie verte avec DR MULTISERVICES ! "
            "Nous installons des panneaux solaires photovoltaiques, des chauffe-eau solaires, et vous accompagnons pour l'autoconsommation et l'injection reseau. "
            "Nous utilisons des marques leaders : SunPower, LG, Jinko Solar, Canadian Solar. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Tarifs indicatifs (installation incluse) :\n"
            "  - 3kWc residentiel: 30000-38000 DH\n"
            "  - 5kWc villa: 45000-58000 DH\n"
            "  - 10kWc commerce: 85000-110000 DH\n"
            "  - 20kWc industrie: 160000-200000 DH\n\n"
            "Nos garanties : 2 ans sur les travaux, 25 ans sur les panneaux solaires, 2-5 ans constructeur sur les onduleurs."
        ),
        'quote_callback': 'request_quote_energies_renouvelables'
    },
    'securite': {
        'emoji': '🔒', 'title': 'Securite',
        'description': (
            "Protegez vos biens et vos proches avec nos solutions de securite avancees ! "
            "DR MULTISERVICES propose l'installation de videosurveillance HD/4K, systemes d'alarmes, controle d'acces biometrique et par badge, interphones et videophones, et detection incendie. "
            "Nous travaillons avec des marques fiables : Hikvision, Dahua, Axis, Honeywell. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Nos garanties : 2 ans sur les travaux, 2-5 ans constructeur."
        ),
        'quote_callback': 'request_quote_securite'
    },
    'chambre_froide': {
        'emoji': '❄️', 'title': 'Chambre Froide',
        'description': (
            "Pour vos besoins en froid professionnel, DR MULTISERVICES est votre expert ! "
            "Nous concevons, installons et maintenons des chambres froides positives et negatives, ainsi que des systemes de refrigeration industrielle et commerciale. "
            "Nous assurons le depannage et la conformite aux normes HACCP. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Nos garanties : 2 ans sur les travaux, 2-5 ans constructeur."
        ),
        'quote_callback': 'request_quote_chambre_froide'
    },
    'renovation': {
        'emoji': '🎨', 'title': 'Renovation & Peinture',
        'description': (
            "Transformez vos espaces avec DR MULTISERVICES ! "
            "Nos services incluent la peinture interieure et exterieure, la platrerie et faux plafonds, l'isolation thermique et acoustique, la pose de revetements muraux et la decoration. "
            "Nous donnons vie a vos projets avec professionnalisme et creativite. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Nos garanties : 2 ans sur les travaux."
        ),
        'quote_callback': 'request_quote_renovation'
    },
    'cvc_intelligent': {
        'emoji': '🏢', 'title': 'CVC Intelligent',
        'description': (
            "Optimisez la gestion de votre batiment avec nos solutions CVC intelligentes ! "
            "DR MULTISERVICES propose la gestion centralisee du chauffage, de la ventilation et de la climatisation, l'automation et la domotique, l'integration de capteurs IoT pour un monitoring en temps reel, l'optimisation energetique et le pilotage a distance via smartphone. "
            "Rendez votre batiment plus performant et econome. "
            "Deplacement et devis GRATUIT sous 24h !\n\n"
            "Nos garanties : 2 ans sur les travaux, 2-5 ans constructeur."
        ),
        'quote_callback': 'request_quote_cvc_intelligent'
    }
}

(APPOINTMENT_NAME, APPOINTMENT_PHONE, APPOINTMENT_SERVICE, APPOINTMENT_ADDRESS, APPOINTMENT_DATE, APPOINTMENT_DESCRIPTION) = range(6)
(QUOTE_NAME, QUOTE_PHONE, QUOTE_EMAIL, QUOTE_SERVICE, QUOTE_SURFACE, QUOTE_ADDRESS, QUOTE_DETAILS) = range(6, 13)

APPOINTMENTS_FILE = 'appointments.json'
QUOTES_FILE = 'quotes.json'

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def start(update: Update, context) -> None:
    user = update.effective_user
    welcome_message = (
        f"Bonjour {user.mention_html()} !\n\n"
        "Bienvenue chez DR MULTISERVICES, votre partenaire de confiance pour batiments intelligents au Maroc.\n"
        "Nous offrons des solutions professionnelles en climatisation, chauffage, electricite, energies renouvelables, securite, chambre froide, renovation/peinture et CVC intelligent.\n\n"
        "Comment puis-je vous aider aujourd'hui ?"
    )
    keyboard = [
        [InlineKeyboardButton("🌀 Climatisation", callback_data='service_climatisation'),
         InlineKeyboardButton("🔥 Chauffage", callback_data='service_chauffage')],
        [InlineKeyboardButton("⚡ Electricite", callback_data='service_electricite'),
         InlineKeyboardButton("☀️ Energies Renouvelables", callback_data='service_energies_renouvelables')],
        [InlineKeyboardButton("🔒 Securite", callback_data='service_securite'),
         InlineKeyboardButton("❄️ Chambre Froide", callback_data='service_chambre_froide')],
        [InlineKeyboardButton("🎨 Renovation & Peinture", callback_data='service_renovation'),
         InlineKeyboardButton("🏢 CVC Intelligent", callback_data='service_cvc_intelligent')],
        [InlineKeyboardButton("💰 Nos Tarifs", callback_data='show_tarifs')],
        [InlineKeyboardButton("📞 Nous Contacter", callback_data='contact_us')],
        [InlineKeyboardButton("📋 Demander un Devis", callback_data='request_quote_general')],
        [InlineKeyboardButton("🗓️ Prendre un Rendez-vous", callback_data='request_appointment')],
        [InlineKeyboardButton("🆘 Urgence 24h/24", callback_data='emergency')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_html(welcome_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_message, reply_markup=reply_markup, parse_mode='HTML')

async def help_command(update: Update, context) -> None:
    help_text = (
        "DR MULTISERVICES - Aide\n\n"
        "Commandes disponibles :\n"
        "/start - Menu principal\n"
        "/services - Voir tous nos services\n"
        "/tarifs - Voir nos tarifs\n"
        "/devis - Demander un devis gratuit\n"
        "/rdv - Prendre un rendez-vous\n"
        "/contact - Nous contacter\n"
        "/urgence - Urgence 24h/24\n"
        "/cancel - Annuler une operation en cours\n\n"
        "Vous pouvez aussi me poser des questions directement !"
    )
    await update.message.reply_text(help_text)

async def services_command(update: Update, context) -> None:
    services_text = (
        "DR MULTISERVICES - Nos Services\n\n"
        "🌀 Climatisation - Installation, maintenance, depannage (splits, multi-splits, VRV/VRF, centralises)\n"
        "🔥 Chauffage - Pompes a chaleur, chaudieres, chauffage central, plancher chauffant\n"
        "⚡ Electricite - Installation complete, mise aux normes, domotique, tableaux electriques\n"
        "☀️ Energies Renouvelables - Panneaux solaires, chauffe-eau solaire\n"
        "🔒 Securite - Videosurveillance, alarmes, controle d'acces, interphones\n"
        "❄️ Chambre Froide - Refrigeration industrielle et commerciale\n"
        "🎨 Renovation & Peinture - Peinture, platrerie, isolation thermique\n"
        "🏢 CVC Intelligent - Gestion centralisee, automation, IoT\n\n"
        "+20 ans d'experience | Certifie ISO | +450 clients satisfaits\n"
        "Deplacement et devis GRATUIT sous 24h !\n"
        "Tel : +212 6 61 84 46 73\n"
        "Site : https://dr-multiservices.com/"
    )
    await update.message.reply_text(services_text)

async def tarifs_command(update: Update, context) -> None:
    tarifs_text = (
        "DR MULTISERVICES - Tarifs Indicatifs (DH)\n\n"
        "Climatisation :\n"
        "- Split 9000 BTU : 4 500 - 7 000\n"
        "- Split 12000 BTU : 5 500 - 8 500\n"
        "- Split 18000 BTU : 7 000 - 11 000\n"
        "- Multi-Split 2 unites : 12 000 - 18 000\n"
        "- Multi-Split 3 unites : 16 000 - 24 000\n"
        "- VRV/VRF : a partir de 50 000\n\n"
        "Energies Renouvelables (Solaire) :\n"
        "- 3 kWc residentiel : 30 000 - 38 000\n"
        "- 5 kWc villa : 45 000 - 58 000\n"
        "- 10 kWc commerce/PME : 85 000 - 110 000\n"
        "- 20 kWc industrie : 160 000 - 200 000\n\n"
        "Ces tarifs sont indicatifs (installation incluse). Contactez-nous pour un devis personnalise !\n"
        "Tel : +212 6 61 84 46 73"
    )
    await update.message.reply_text(tarifs_text)

async def contact_command(update: Update, context) -> None:
    contact_text = (
        "DR MULTISERVICES - Nous Contacter\n\n"
        "Tel : +212 6 61 84 46 73 (7j/7, urgences 24h/24)\n"
        "Email : karimi@dr-multiservices.com (reponse sous 24h)\n"
        "Site web : https://dr-multiservices.com/\n\n"
        "Horaires :\n"
        "Lundi - Samedi : 8h - 18h\n"
        "Dimanche : Sur RDV\n"
        "Urgences : 24h/24 7j/7\n\n"
        "Zone : Tout le Maroc (Marrakech, Casablanca, Rabat, Agadir, Tanger, Fes et toutes les regions)"
    )
    await update.message.reply_text(contact_text)

async def urgence_command(update: Update, context) -> None:
    urgence_text = (
        "🆘 URGENCE 24h/24 et 7j/7 !\n\n"
        "En cas d'urgence, appelez immediatement :\n"
        "+212 6 61 84 46 73\n\n"
        "Notre equipe est prete a intervenir rapidement sur tout le Maroc."
    )
    await update.message.reply_text(urgence_text)

async def devis_command(update: Update, context) -> None:
    await start(update, context)

async def rdv_command(update: Update, context) -> None:
    await start(update, context)

async def welcome_new_members(update: Update, context) -> None:
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text(
                "Merci de m'avoir ajoute ! Je suis le bot officiel DR MULTISERVICES.\n"
                "Tapez /start pour decouvrir nos services ou /help pour voir les commandes disponibles."
            )
        else:
            await update.message.reply_text(
                f"Bienvenue {member.first_name} dans le groupe DR MULTISERVICES !\n"
                "Votre partenaire de confiance pour batiments intelligents au Maroc.\n\n"
                "Pour toute demande, contactez notre bot @DRMultiservices_bot ou appelez le +212 6 61 84 46 73\n"
                "Tapez /services pour voir nos prestations."
            )

async def handle_message(update: Update, context) -> None:
    user_message = update.message.text
    logger.info(f"Message recu de {update.effective_user.first_name}: {user_message}")
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": DR_MULTISERVICES_INFO},
                {"role": "user", "content": user_message}
            ]
        )
        ai_response = response.choices[0].message.content
        await update.message.reply_text(ai_response)
    except Exception as e:
        logger.error(f"Erreur lors de l'appel a OpenAI: {e}")
        await update.message.reply_text(
            "Desole, je rencontre un probleme pour traiter votre demande. "
            "Veuillez reessayer ou nous contacter au +212 6 61 84 46 73."
        )

async def button_callback(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('service_'):
        service_key = data.replace('service_', '')
        service_info = SERVICE_DETAILS.get(service_key)
        if service_info:
            message_text = f"{service_info['emoji']} {service_info['title']}\n\n{service_info['description']}"
            keyboard = [
                [InlineKeyboardButton(f"📋 Demander un devis {service_info['title']}", callback_data=service_info['quote_callback'])],
                [InlineKeyboardButton("📞 Nous appeler", url="tel:+212661844673")],
                [InlineKeyboardButton("⬅️ Retour au menu", callback_data='back_to_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=message_text, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="Service non trouve.")

    elif data == 'show_tarifs':
        tarifs_message = (
            "Nos Tarifs Indicatifs (DH) :\n\n"
            "Climatisation :\n"
            "- Split 9000 BTU : 4 500 - 7 000\n"
            "- Split 12000 BTU : 5 500 - 8 500\n"
            "- Split 18000 BTU : 7 000 - 11 000\n"
            "- Multi-Split 2 unites : 12 000 - 18 000\n"
            "- Multi-Split 3 unites : 16 000 - 24 000\n"
            "- VRV/VRF : a partir de 50 000\n\n"
            "Energies Renouvelables (Solaire) :\n"
            "- 3 kWc : 30 000 - 38 000\n"
            "- 5 kWc : 45 000 - 58 000\n"
            "- 10 kWc : 85 000 - 110 000\n"
            "- 20 kWc : 160 000 - 200 000\n\n"
            "Ces tarifs sont indicatifs. Contactez-nous pour un devis personnalise !"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Retour au menu", callback_data='back_to_main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=tarifs_message, reply_markup=reply_markup)

    elif data == 'contact_us':
        contact_message = (
            "Nous Contacter :\n\n"
            "Tel : +212 6 61 84 46 73 (7j/7, urgences 24h/24)\n"
            "Email : karimi@dr-multiservices.com\n"
            "Site web : https://dr-multiservices.com/\n"
            "Horaires : Lundi-Samedi 8h-18h, Dimanche sur RDV\n\n"
            "N'hesitez pas a nous joindre pour toute question ou demande !"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Retour au menu", callback_data='back_to_main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=contact_message, reply_markup=reply_markup)

    elif data == 'emergency':
        emergency_message = (
            "🆘 URGENCE 24h/24 et 7j/7 !\n\n"
            "En cas d'urgence, appelez immediatement :\n"
            "+212 6 61 84 46 73\n\n"
            "Notre equipe est prete a intervenir rapidement."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Retour au menu", callback_data='back_to_main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=emergency_message, reply_markup=reply_markup)

    elif data == 'back_to_main_menu':
        await start(update, context)

    elif data.startswith('request_quote_'):
        service_key = data.replace('request_quote_', '')
        if service_key == 'general':
            await query.edit_message_text(text="Pour une demande de devis, veuillez me donner votre nom complet.")
        else:
            service_title = SERVICE_DETAILS.get(service_key, {}).get('title', service_key.replace('_', ' ').title())
            context.user_data['prefilled_service'] = service_title
            await query.edit_message_text(text=f"Pour une demande de devis pour le service {service_title}, veuillez me donner votre nom complet.")
        return QUOTE_NAME

    elif data == 'request_appointment':
        await query.edit_message_text(text="Pour prendre un rendez-vous, veuillez me donner votre nom complet.")
        return APPOINTMENT_NAME

    return ConversationHandler.END

async def appointment_get_name(update: Update, context) -> int:
    context.user_data['appointment'] = {'user_id': update.effective_user.id, 'username': update.effective_user.username}
    context.user_data['appointment']['name'] = update.message.text
    await update.message.reply_text("Merci. Quel est votre numero de telephone ?")
    return APPOINTMENT_PHONE

async def appointment_get_phone(update: Update, context) -> int:
    context.user_data['appointment']['phone'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("🌀 Climatisation", callback_data='app_service_climatisation')],
        [InlineKeyboardButton("🔥 Chauffage", callback_data='app_service_chauffage')],
        [InlineKeyboardButton("⚡ Electricite", callback_data='app_service_electricite')],
        [InlineKeyboardButton("☀️ Energies Renouvelables", callback_data='app_service_energies_renouvelables')],
        [InlineKeyboardButton("🔒 Securite", callback_data='app_service_securite')],
        [InlineKeyboardButton("❄️ Chambre Froide", callback_data='app_service_chambre_froide')],
        [InlineKeyboardButton("🎨 Renovation & Peinture", callback_data='app_service_renovation')],
        [InlineKeyboardButton("🏢 CVC Intelligent", callback_data='app_service_cvc_intelligent')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Quel type de service vous interesse ?", reply_markup=reply_markup)
    return APPOINTMENT_SERVICE

async def appointment_get_service(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['appointment']['service'] = query.data.replace('app_service_', '').replace('_', ' ').title()
    await query.edit_message_text(text="Quelle est l'adresse d'intervention ?")
    return APPOINTMENT_ADDRESS

async def appointment_get_address(update: Update, context) -> int:
    context.user_data['appointment']['address'] = update.message.text
    await update.message.reply_text("Quelle date et heure souhaiteriez-vous ? (ex: 2026-04-15 10h00)")
    return APPOINTMENT_DATE

async def appointment_get_date(update: Update, context) -> int:
    context.user_data['appointment']['date'] = update.message.text
    await update.message.reply_text("Decrivez brievement votre besoin ou le probleme a resoudre.")
    return APPOINTMENT_DESCRIPTION

async def appointment_get_description(update: Update, context) -> int:
    context.user_data['appointment']['description'] = update.message.text
    context.user_data['appointment']['timestamp'] = datetime.now().isoformat()
    appointments = load_data(APPOINTMENTS_FILE)
    appointments.append(context.user_data['appointment'])
    save_data(APPOINTMENTS_FILE, appointments)
    confirmation_message = (
        "Rendez-vous enregistre !\n\n"
        "Nom : {name}\n"
        "Telephone : {phone}\n"
        "Service : {service}\n"
        "Adresse : {address}\n"
        "Date souhaitee : {date}\n"
        "Description : {description}\n\n"
        "Notre equipe vous contactera tres prochainement pour confirmer les details.\n"
        "Merci de faire confiance a DR MULTISERVICES !"
    ).format(**context.user_data['appointment'])
    await update.message.reply_text(confirmation_message)
    return ConversationHandler.END

async def cancel_conversation(update: Update, context) -> int:
    await update.message.reply_text("Operation annulee. Tapez /start pour revenir au menu principal.")
    return ConversationHandler.END

async def quote_get_name(update: Update, context) -> int:
    context.user_data['quote'] = {'user_id': update.effective_user.id, 'username': update.effective_user.username}
    context.user_data['quote']['name'] = update.message.text
    await update.message.reply_text("Merci. Quel est votre numero de telephone ?")
    return QUOTE_PHONE

async def quote_get_phone(update: Update, context) -> int:
    context.user_data['quote']['phone'] = update.message.text
    await update.message.reply_text("Quelle est votre adresse e-mail ?")
    return QUOTE_EMAIL

async def quote_get_email(update: Update, context) -> int:
    context.user_data['quote']['email'] = update.message.text
    if 'prefilled_service' in context.user_data:
        service_title = context.user_data.pop('prefilled_service')
        context.user_data['quote']['service'] = service_title
        await update.message.reply_text(f"Vous avez demande un devis pour : {service_title}. Quelle est la surface ou le nombre de pieces concernees ? (ex: 100m2, 4 pieces)")
        return QUOTE_SURFACE
    else:
        keyboard = [
            [InlineKeyboardButton("🌀 Climatisation", callback_data='quote_service_climatisation')],
            [InlineKeyboardButton("🔥 Chauffage", callback_data='quote_service_chauffage')],
            [InlineKeyboardButton("⚡ Electricite", callback_data='quote_service_electricite')],
            [InlineKeyboardButton("☀️ Energies Renouvelables", callback_data='quote_service_energies_renouvelables')],
            [InlineKeyboardButton("🔒 Securite", callback_data='quote_service_securite')],
            [InlineKeyboardButton("❄️ Chambre Froide", callback_data='quote_service_chambre_froide')],
            [InlineKeyboardButton("🎨 Renovation & Peinture", callback_data='quote_service_renovation')],
            [InlineKeyboardButton("🏢 CVC Intelligent", callback_data='quote_service_cvc_intelligent')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Pour quel type de service souhaitez-vous un devis ?", reply_markup=reply_markup)
        return QUOTE_SERVICE

async def quote_get_service(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['quote']['service'] = query.data.replace('quote_service_', '').replace('_', ' ').title()
    await query.edit_message_text(text="Quelle est la surface ou le nombre de pieces concernees ? (ex: 100m2, 4 pieces)")
    return QUOTE_SURFACE

async def quote_get_surface(update: Update, context) -> int:
    context.user_data['quote']['surface'] = update.message.text
    await update.message.reply_text("Quelle est l'adresse du projet ?")
    return QUOTE_ADDRESS

async def quote_get_address(update: Update, context) -> int:
    context.user_data['quote']['address'] = update.message.text
    await update.message.reply_text("Decrivez plus en detail votre besoin pour le devis.")
    return QUOTE_DETAILS

async def quote_get_details(update: Update, context) -> int:
    context.user_data['quote']['details'] = update.message.text
    context.user_data['quote']['timestamp'] = datetime.now().isoformat()
    quotes = load_data(QUOTES_FILE)
    quotes.append(context.user_data['quote'])
    save_data(QUOTES_FILE, quotes)
    confirmation_message = (
        "Demande de devis enregistree !\n\n"
        "Nom : {name}\n"
        "Telephone : {phone}\n"
        "Email : {email}\n"
        "Service : {service}\n"
        "Surface/Pieces : {surface}\n"
        "Adresse : {address}\n"
        "Details : {details}\n\n"
        "Notre equipe commerciale vous contactera par telephone ou e-mail tres prochainement.\n"
        "Deplacement et devis GRATUIT sous 24h !\n"
        "Merci de faire confiance a DR MULTISERVICES !"
    ).format(**context.user_data['quote'])
    await update.message.reply_text(confirmation_message)
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("services", services_command))
    application.add_handler(CommandHandler("tarifs", tarifs_command))
    application.add_handler(CommandHandler("contact", contact_command))
    application.add_handler(CommandHandler("urgence", urgence_command))
    application.add_handler(CommandHandler("devis", devis_command))
    application.add_handler(CommandHandler("rdv", rdv_command))

    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))

    application.add_handler(CallbackQueryHandler(button_callback, pattern='^(service_|show_tarifs|contact_us|emergency|back_to_main_menu)'))

    appointment_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern='^request_appointment$')],
        states={
            APPOINTMENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, appointment_get_name)],
            APPOINTMENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, appointment_get_phone)],
            APPOINTMENT_SERVICE: [CallbackQueryHandler(appointment_get_service, pattern='^app_service_')],
            APPOINTMENT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, appointment_get_address)],
            APPOINTMENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, appointment_get_date)],
            APPOINTMENT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, appointment_get_description)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )
    application.add_handler(appointment_conv_handler)

    quote_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern='^request_quote_')],
        states={
            QUOTE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_get_name)],
            QUOTE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_get_phone)],
            QUOTE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_get_email)],
            QUOTE_SERVICE: [CallbackQueryHandler(quote_get_service, pattern='^quote_service_')],
            QUOTE_SURFACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_get_surface)],
            QUOTE_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_get_address)],
            QUOTE_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_get_details)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )
    application.add_handler(quote_conv_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot DR MULTISERVICES demarre...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
