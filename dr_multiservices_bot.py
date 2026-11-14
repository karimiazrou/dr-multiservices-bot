import os
import json
import logging
import asyncio
import re
import tempfile
from pathlib import Path
from time import monotonic
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

client = None
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

DR_MULTISERVICES_INFO = """
Vous êtes l'assistant de DR MULTISERVICES.
Basés à Marrakech • Interventions partout au Maroc.
Services : climatisation, chauffage, électricité, solaire, sécurité, chambres froides,
rénovation et CVC intelligent. Téléphone : +212 6 61 84 46 73.
Site : https://dr-multiservices.com/ ; email : karimi@dr-multiservices.com.
Répondez naturellement en français, arabe ou darija selon le client, en texte brut.
Ne donnez aucun prix, aucune certification, garantie ou délai non confirmé.
Pour un devis, invitez à utiliser /devis. Un rendez-vous est une demande à confirmer.
Ne demandez jamais de mot de passe. Ne guidez pas de manipulation électrique sous tension
ni de manipulation de fluide frigorigène : proposez un diagnostic par un technicien.
"""

SERVICE_DETAILS = {
    'climatisation': {
        'emoji': '🌀', 'title': 'Climatisation',
        'description': (
            "Chez DR MULTISERVICES, nous vous offrons des solutions completes de climatisation pour un confort optimal ! "
            "Nos services incluent l'installation, la maintenance preventive, le depannage rapide et la reparation de tous types de systemes. "
            "Nous intervenons sur les splits muraux, multi-splits, VRV/VRF, systemes centralises, cassettes et gainables. "
            "Nous travaillons avec les plus grandes marques : Daikin, Mitsubishi Electric, LG, Samsung, Carrier, Toshiba. "
            "Devis personnalisé après étude de votre besoin.\n\n"
            "Un diagnostic permet de préparer un devis adapté à votre installation."
        ),
        'quote_callback': 'request_quote_climatisation'
    },
    'chauffage': {
        'emoji': '🔥', 'title': 'Chauffage',
        'description': (
            "Restez au chaud avec nos solutions de chauffage performantes et economiques ! "
            "DR MULTISERVICES installe et entretient vos pompes a chaleur (air/eau, air/air), chaudieres (gaz, fioul), systemes de chauffage central, planchers chauffants et radiateurs. "
            "Nous collaborons avec des marques de renom : Bosch, Viessmann, Atlantic, De Dietrich, Vaillant. "
            "Devis personnalisé après étude de votre besoin.\n\n"
        ),
        'quote_callback': 'request_quote_chauffage'
    },
    'electricite': {
        'emoji': '⚡', 'title': 'Electricite',
        'description': (
            "Pour une installation electrique sure et conforme, faites confiance a DR MULTISERVICES ! "
            "Nous realisons l'installation complete, la mise aux normes, l'installation de tableaux electriques, la domotique et maison connectee, l'eclairage LED et le cablage reseau. "
            "Nos electriciens qualifies vous garantissent un travail impeccable. "
            "Devis personnalisé après étude de votre besoin.\n\n"
        ),
        'quote_callback': 'request_quote_electricite'
    },
    'energies_renouvelables': {
        'emoji': '☀️', 'title': 'Energies Renouvelables',
        'description': (
            "Passez a l'energie verte avec DR MULTISERVICES ! "
            "Nous installons des panneaux solaires photovoltaiques, des chauffe-eau solaires, et vous accompagnons pour l'autoconsommation et l'injection reseau. "
            "Nous utilisons des marques leaders : SunPower, LG, Jinko Solar, Canadian Solar. "
            "Devis personnalisé après étude de votre besoin.\n\n"
            "Un diagnostic permet de préparer un devis adapté à votre installation."
        ),
        'quote_callback': 'request_quote_energies_renouvelables'
    },
    'securite': {
        'emoji': '🔒', 'title': 'Securite',
        'description': (
            "Protegez vos biens et vos proches avec nos solutions de securite avancees ! "
            "DR MULTISERVICES propose l'installation de videosurveillance HD/4K, systemes d'alarmes, controle d'acces biometrique et par badge, interphones et videophones, et detection incendie. "
            "Nous travaillons avec des marques fiables : Hikvision, Dahua, Axis, Honeywell. "
            "Devis personnalisé après étude de votre besoin.\n\n"
        ),
        'quote_callback': 'request_quote_securite'
    },
    'chambre_froide': {
        'emoji': '❄️', 'title': 'Chambre Froide',
        'description': (
            "Pour vos besoins en froid professionnel, DR MULTISERVICES est votre expert ! "
            "Nous concevons, installons et maintenons des chambres froides positives et negatives, ainsi que des systemes de refrigeration industrielle et commerciale. "
            "Nous assurons le depannage et la conformite aux normes HACCP. "
            "Devis personnalisé après étude de votre besoin.\n\n"
        ),
        'quote_callback': 'request_quote_chambre_froide'
    },
    'renovation': {
        'emoji': '🎨', 'title': 'Renovation & Peinture',
        'description': (
            "Transformez vos espaces avec DR MULTISERVICES ! "
            "Nos services incluent la peinture interieure et exterieure, la platrerie et faux plafonds, l'isolation thermique et acoustique, la pose de revetements muraux et la decoration. "
            "Nous donnons vie a vos projets avec professionnalisme et creativite. "
            "Devis personnalisé après étude de votre besoin.\n\n"
        ),
        'quote_callback': 'request_quote_renovation'
    },
    'cvc_intelligent': {
        'emoji': '🏢', 'title': 'CVC Intelligent',
        'description': (
            "Optimisez la gestion de votre batiment avec nos solutions CVC intelligentes ! "
            "DR MULTISERVICES propose la gestion centralisee du chauffage, de la ventilation et de la climatisation, l'automation et la domotique, l'integration de capteurs IoT pour un monitoring en temps reel, l'optimisation energetique et le pilotage a distance via smartphone. "
            "Rendez votre batiment plus performant et econome. "
            "Devis personnalisé après étude de votre besoin.\n\n"
        ),
        'quote_callback': 'request_quote_cvc_intelligent'
    }
}

(APPOINTMENT_NAME, APPOINTMENT_PHONE, APPOINTMENT_SERVICE, APPOINTMENT_ADDRESS, APPOINTMENT_DATE, APPOINTMENT_DESCRIPTION) = range(6)
(QUOTE_NAME, QUOTE_PHONE, QUOTE_EMAIL, QUOTE_SERVICE, QUOTE_SURFACE, QUOTE_ADDRESS, QUOTE_DETAILS) = range(6, 13)

DATA_DIR = Path(os.getenv("DATA_DIR", "."))
APPOINTMENTS_FILE = DATA_DIR / 'appointments.json'
QUOTES_FILE = DATA_DIR / 'quotes.json'

def valid_phone(value):
    return bool(re.fullmatch(r"\+?[0-9]{8,15}", re.sub(r"[\s().-]", "", value)))


def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(filename, data):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         delete=False) as handle:
            temporary = handle.name
            json.dump(data, handle, indent=2, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


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
        "/tarifs - Informations sur les devis\n"
        "/devis - Demander un devis personnalisé\n"
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
        "Basés à Marrakech • Interventions partout au Maroc\n"
        "Devis personnalisé après étude de votre besoin.\n"
        "Tel : +212 6 61 84 46 73\n"
        "Site : https://dr-multiservices.com/"
    )
    await update.message.reply_text(services_text)

async def tarifs_command(update: Update, context) -> None:
    await update.message.reply_text(
        "Chaque installation nécessite une étude. Nous préparons un devis personnalisé. "
        "Utilisez /devis ou contactez le +212 6 61 84 46 73.")

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

async def devis_command(update: Update, context) -> int:
    context.user_data.pop('prefilled_service', None)
    await update.message.reply_text("Demande de devis : vos coordonnées seront enregistrées pour traiter votre demande. /cancel pour annuler. Quel est votre nom complet ?")
    return QUOTE_NAME

async def rdv_command(update: Update, context) -> int:
    await update.message.reply_text("Demande de rendez-vous à confirmer par notre équipe. Vos coordonnées seront enregistrées pour traiter votre demande. /cancel pour annuler. Quel est votre nom complet ?")
    return APPOINTMENT_NAME

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
    now = monotonic()
    if now - context.user_data.get('last_ai_request', -100) < 5:
        await update.message.reply_text("Veuillez patienter quelques secondes avant une nouvelle question.")
        return
    context.user_data['last_ai_request'] = now
    if len(user_message) > 3000:
        await update.message.reply_text("Merci de limiter votre question à 3 000 caractères.")
        return
    if client is None:
        await update.message.reply_text("Pour votre demande, utilisez /devis, /rdv ou /contact.")
        return
    try:
        response = await asyncio.to_thread(client.chat.completions.create,
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            max_tokens=600,
            messages=[
                {"role": "system", "content": DR_MULTISERVICES_INFO},
                {"role": "user", "content": user_message}
            ]
        )
        ai_response = response.choices[0].message.content
        for offset in range(0, len(ai_response or ""), 4000):
            await update.message.reply_text(ai_response[offset:offset + 4000])
    except Exception as e:
        logger.error("Échec IA (%s)", type(e).__name__)
        await update.message.reply_text(
            "Desole, je rencontre un probleme pour traiter votre demande. "
            "Veuillez reessayer ou nous contacter au +212 6 61 84 46 73."
        )

async def button_callback(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith('request_') and update.effective_chat.type != 'private':
        await query.message.reply_text("Pour protéger vos coordonnées, ouvrez une conversation privée avec le bot puis utilisez /devis ou /rdv.")
        return ConversationHandler.END

    if data.startswith('service_'):
        service_key = data.replace('service_', '')
        service_info = SERVICE_DETAILS.get(service_key)
        if service_info:
            message_text = f"{service_info['emoji']} {service_info['title']}\n\n{service_info['description']}"
            keyboard = [
                [InlineKeyboardButton(f"📋 Demander un devis {service_info['title']}", callback_data=service_info['quote_callback'])],
                [InlineKeyboardButton("💬 WhatsApp", url="https://wa.me/212661844673")],
                [InlineKeyboardButton("⬅️ Retour au menu", callback_data='back_to_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=message_text, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="Service non trouve.")

    elif data == 'show_tarifs':
        tarifs_message = "Devis personnalisé après étude. Utilisez /devis ou contactez le +212 6 61 84 46 73."
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
        context.user_data.pop('prefilled_service', None)
        service_key = data.replace('request_quote_', '')
        if service_key == 'general':
            await query.edit_message_text(text="Pour une demande de devis, vos coordonnées seront enregistrées pour traiter votre demande. /cancel pour annuler. Quel est votre nom complet ?")
        else:
            service_title = SERVICE_DETAILS.get(service_key, {}).get('title', service_key.replace('_', ' ').title())
            context.user_data['prefilled_service'] = service_title
            await query.edit_message_text(text=f"Pour une demande de devis pour le service {service_title}, vos coordonnées seront enregistrées pour traiter votre demande. /cancel pour annuler. Quel est votre nom complet ?")
        return QUOTE_NAME

    elif data == 'request_appointment':
        await query.edit_message_text(text="Pour prendre un rendez-vous, vos coordonnées seront enregistrées pour traiter votre demande. /cancel pour annuler. Quel est votre nom complet ?")
        return APPOINTMENT_NAME

    return ConversationHandler.END

async def appointment_get_name(update: Update, context) -> int:
    context.user_data['appointment'] = {'user_id': update.effective_user.id, 'username': update.effective_user.username}
    context.user_data['appointment']['name'] = update.message.text
    await update.message.reply_text("Merci. Quel est votre numero de telephone ?")
    return APPOINTMENT_PHONE

async def appointment_get_phone(update: Update, context) -> int:
    if not valid_phone(update.message.text):
        await update.message.reply_text("Numéro invalide. Exemple : +212661234567.")
        return APPOINTMENT_PHONE
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
        "Demande de rendez-vous enregistrée — confirmation nécessaire.\n\n"
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
    context.user_data.pop('appointment', None)
    context.user_data.pop('quote', None)
    return ConversationHandler.END

async def cancel_conversation(update: Update, context) -> int:
    for key in ('appointment', 'quote', 'prefilled_service'):
        context.user_data.pop(key, None)
    await update.message.reply_text("Operation annulee. Tapez /start pour revenir au menu principal.")
    return ConversationHandler.END

async def quote_get_name(update: Update, context) -> int:
    context.user_data['quote'] = {'user_id': update.effective_user.id, 'username': update.effective_user.username}
    context.user_data['quote']['name'] = update.message.text
    await update.message.reply_text("Merci. Quel est votre numero de telephone ?")
    return QUOTE_PHONE

async def quote_get_phone(update: Update, context) -> int:
    if not valid_phone(update.message.text):
        await update.message.reply_text("Numéro invalide. Exemple : +212661234567.")
        return QUOTE_PHONE
    context.user_data['quote']['phone'] = update.message.text
    await update.message.reply_text("Quelle est votre adresse e-mail ?")
    return QUOTE_EMAIL

async def quote_get_email(update: Update, context) -> int:
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", update.message.text):
        await update.message.reply_text("Merci de saisir une adresse e-mail valide.")
        return QUOTE_EMAIL
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
        "Devis personnalisé après étude de votre besoin.\n"
        "Merci de faire confiance a DR MULTISERVICES !"
    ).format(**context.user_data['quote'])
    await update.message.reply_text(confirmation_message)
    context.user_data.pop('appointment', None)
    context.user_data.pop('quote', None)
    return ConversationHandler.END

async def reset_menu(update, context):
    for key in ('appointment', 'quote', 'prefilled_service'):
        context.user_data.pop(key, None)
    if update.callback_query:
        await update.callback_query.answer()
    await start(update, context)
    return ConversationHandler.END


async def error_handler(update, context):
    logger.error("Échec du traitement (%s)", type(context.error).__name__)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Votre demande n'a pas pu être traitée. Réessayez ou contactez le +212 6 61 84 46 73.")


def build_application():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("La variable TELEGRAM_BOT_TOKEN est requise.")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).concurrent_updates(False).build()
    text = filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND
    conversation = ConversationHandler(
        entry_points=[
            CommandHandler('devis', devis_command, filters=filters.ChatType.PRIVATE),
            CommandHandler('rdv', rdv_command, filters=filters.ChatType.PRIVATE),
            CallbackQueryHandler(button_callback, pattern='^request_(quote_.+|appointment)$'),
        ],
        states={
            APPOINTMENT_NAME: [MessageHandler(text, appointment_get_name)],
            APPOINTMENT_PHONE: [MessageHandler(text, appointment_get_phone)],
            APPOINTMENT_SERVICE: [CallbackQueryHandler(appointment_get_service, pattern='^app_service_')],
            APPOINTMENT_ADDRESS: [MessageHandler(text, appointment_get_address)],
            APPOINTMENT_DATE: [MessageHandler(text, appointment_get_date)],
            APPOINTMENT_DESCRIPTION: [MessageHandler(text, appointment_get_description)],
            QUOTE_NAME: [MessageHandler(text, quote_get_name)],
            QUOTE_PHONE: [MessageHandler(text, quote_get_phone)],
            QUOTE_EMAIL: [MessageHandler(text, quote_get_email)],
            QUOTE_SERVICE: [CallbackQueryHandler(quote_get_service, pattern='^quote_service_')],
            QUOTE_SURFACE: [MessageHandler(text, quote_get_surface)],
            QUOTE_ADDRESS: [MessageHandler(text, quote_get_address)],
            QUOTE_DETAILS: [MessageHandler(text, quote_get_details)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation),
                   CommandHandler('start', reset_menu),
                   CallbackQueryHandler(reset_menu, pattern='^back_to_main_menu$')],
        allow_reentry=True,
    )
    application.add_handler(conversation)
    for command, callback in [('start', start), ('help', help_command),
                              ('services', services_command), ('tarifs', tarifs_command),
                              ('contact', contact_command), ('urgence', urgence_command),
                              ('cancel', cancel_conversation)]:
        application.add_handler(CommandHandler(command, callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^(service_|show_tarifs|contact_us|emergency|back_to_main_menu)'))
    application.add_handler(MessageHandler(text, handle_message))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    global client
    if OPENAI_API_KEY:
        client = OpenAI(timeout=20.0, max_retries=1)
    application = build_application()
    logger.info("Bot DR MULTISERVICES demarre...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
