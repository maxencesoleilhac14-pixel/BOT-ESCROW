"""
╔══════════════════════════════════════════════════════════════╗
║              🔐 BOT ESCROW TELEGRAM                         ║
║  Dépendances : voir requirements.txt                        ║
╚══════════════════════════════════════════════════════════════╝
"""

import logging, uuid, aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ──────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────
BOT_TOKEN      = "8942358282:AAG51UhEFyfF3xknj0mTEveTLYjs054wLwg"
ADMIN_ID       = 8567294409
FEES_PCT       = 0.10
OXAPAY_KEY     = "0GIV9Q-UK4W7X-VWK6UI-Y7YDQE"
OXAPAY_API     = "https://api.oxapay.com/merchants/request"
PAYPAL_URL     = "https://www.paypal.me/crz843026"
SERVER_LINK    = "https://t.me/+xKS4m2oPM_IyZGE0"

# ──────────────────────────────────────────────
#  ÉTAT GLOBAL
# ──────────────────────────────────────────────
bot_online  : bool = True
all_users   : set  = set()
user_lang   : dict = {}
sessions    : dict = {}
user_sessions: dict = {}
scam_list   : list = []   # [{"username": "@x", "id": 123, "reason": "...", "date": "..."}]

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  TRADUCTIONS
# ──────────────────────────────────────────────
LANG = {
"fr": {
"choose_lang":    "🌍 *Choisis ta langue :*",
"welcome":        "👋 *Salut {name} !*\n\n🔐 *Bienvenue sur EscrowBot*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nJe suis ton intermédiaire de confiance pour sécuriser tes transactions en ligne.\n\n✅ L'argent est bloqué jusqu'à la livraison\n🔍 Chaque livraison est vérifiée par un admin\n💸 Frais : seulement *10%* sur le montant\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👇 *Que veux-tu faire ?*",
"bot_offline":    "🔴 *EscrowBot est temporairement hors ligne.*\n\nAucun admin n'est disponible.\n\n⏳ _Reviens plus tard !_",
"btn_create":     "🛒  Créer une session  ·  Acheteur",
"btn_join":       "🔑  Rejoindre une session  ·  Vendeur",
"btn_sessions":   "📋  Mes sessions",
"btn_howto":      "ℹ️  Comment ça marche ?",
"btn_server":     "💬  Rejoindre le serveur",
"btn_scamlist":   "🚫  Scam List",
"btn_admin":      "👑  Panel Admin",
"btn_back":       "⬅️  Retour au menu",
"howto":          "ℹ️ *Comment fonctionne EscrowBot ?*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n1️⃣ *L'acheteur* crée une session\n2️⃣ *Un code unique* est partagé au vendeur\n3️⃣ *Le vendeur* rejoint avec ce code\n4️⃣ *L'acheteur* définit les conditions\n5️⃣ *L'acheteur* paie via le lien sécurisé\n6️⃣ *L'admin* valide le paiement ✅\n7️⃣ *Le vendeur* dépose la livraison\n8️⃣ *L'admin* vérifie et valide 🔍\n9️⃣ *Le vendeur* reçoit son paiement 💰\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💸 Frais : *10%* à la charge de l'acheteur\n🔒 *Aucun argent ne part sans validation admin !*",
"scamlist_empty": "🚫 *Scam List*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Aucun scammeur répertorié pour le moment.\n\n_La liste est mise à jour par l'admin._",
"scamlist_title": "🚫 *Scam List — Personnes à éviter*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ _Ces personnes ont été signalées pour escroquerie._\n\n",
"step1":          "🛒 *Créer une session Escrow*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📝 *Étape 1 sur 5 — Article*\n\nQuel est le nom ou la description de l'article que tu achètes ?",
"step2":          "📬 *Étape 2 sur 5 — Type de livraison*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Article : *{item}*\n\nQuel type de livraison attends-tu du vendeur ?",
"step3":          "💵 *Étape 3 sur 5 — Prix*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Livraison : *{dtype}*\n\nÀ quel montant le vendeur doit-il être payé ?\n\n💡 _Tape le montant en chiffres (ex: 50 ou 49.99)_\n⚠️ _Les frais de 10% seront ajoutés automatiquement_",
"step4":          "💳 *Étape 4 sur 5 — Paiement*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💰 *Récapitulatif :*\n\n  💵 Prix vendeur  → `{seller} €`\n  📊 Frais (10%)   → `{fees} €`\n  ━━━━━━━━━━━━━━━━━\n  💳 *Total        → `{total} €`*\n\nQuelle méthode de paiement ?",
"step5":          "📋 *Étape 5 sur 5 — Conditions*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚖️ Tu peux définir ici les conditions de la transaction.\n\nCes conditions seront inscrites sur le *contrat de session* et visibles par le vendeur et l'admin.\n\n✍️ *Écris tes conditions* ou clique sur *Ignorer* pour continuer sans.\n\n💡 _Les conditions doivent être convenues en amont avec le vendeur en privé avant d'être inscrites ici._",
"btn_skip_cond":  "⏩  Ignorer les conditions",
"session_created":"🎉 *Session créée avec succès !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{summary}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📤 *Partage ce code au vendeur :*\n\n```\n{code}\n```\n\n⏳ _En attente que le vendeur rejoigne…_",
"join_prompt":    "🔑 *Rejoindre une session Escrow*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nEntre le code de session que l'acheteur t'a transmis :",
"code_not_found": "❌ *Code introuvable !*\n\nVérifie bien le code et réessaie.",
"code_used":      "⛔ *Ce code est déjà utilisé !*\n\nUn vendeur a déjà rejoint cette session.",
"joined_ok":      "✅ *Tu as rejoint la session avec succès !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{summary}\n\n⏳ *En attente que l'acheteur effectue son paiement…*\n🔔 Tu recevras une notification dès confirmation.",
"pay_crypto_msg": "🔔 *Le vendeur a rejoint ta session !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🧑‍💼 *Vendeur :* {seller}\n\n💰 *Montant à payer : `{total} €`*\n🪙 *Méthode : Crypto (Multi-devises)*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔗 Clique sur le bouton ci-dessous pour payer.\n\n⚠️ *IMPORTANT : Ne quitte PAS la page de paiement avant que le bot confirme la transaction ou que la blockchain la valide. Même l'admin n'aura pas accès aux fonds avant confirmation. Reste sur la page jusqu'au retour du bot.*",
"pay_paypal_msg": "🔔 *Le vendeur a rejoint ta session !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🧑‍💼 *Vendeur :* {seller}\n\n💰 *Montant à payer : `{total} €`*\n💳 *Méthode : PayPal*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n1️⃣ Clique sur le bouton ci-dessous pour payer\n   ↳ Envoie exactement *{total} €*\n2️⃣ Reviens ici et envoie une *capture d'écran* de la confirmation\n\n⚠️ _Sans preuve, la transaction ne peut pas être validée._",
"pay_link_error": "⚠️ Erreur lors de la génération du lien de paiement. Contacte l'admin.",
"send_proof":     "📸 *Envoie une capture d'écran* de ta confirmation PayPal pour validation.",
"proof_sent":     "📤 *Preuve de paiement envoyée à l'admin !*\n\n⏳ En attente de validation…\n🔔 Tu seras notifié dès confirmation.",
"payment_ok_buyer":"✅ *Ton paiement a été validé !*\n\n🔔 Le vendeur va maintenant déposer ta livraison.",
"payment_ok_seller":"💰 *Le paiement est confirmé !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📦 *Article :* {item}\n📬 *Type :* {dtype}\n\n➡️ *Envoie maintenant ta livraison ici.*\n📎 _Fichier, lien, image ou texte_",
"payment_rejected":"❌ *Paiement non reçu.*\n\nEffectue le virement et renvoie une capture d'écran claire.",
"delivery_sent":  "📤 *Livraison envoyée à l'admin !*\n\n🔍 En cours de vérification…",
"delivery_ok_buyer":"✅ *Ta livraison est arrivée !*\n📦 Article : *{item}*",
"tx_complete_buyer":"🎉 *Transaction terminée avec succès !*\n\nMerci d'avoir utilisé *EscrowBot* ! 🙌",
"delivery_rejected":"❌ *Ta livraison a été rejetée.*\n\n🚫 Le contenu ne correspond pas.\n➡️ Renvoie la bonne livraison.",
"withdraw_prompt_crypto":"🪙 *Retrait en Crypto*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nIndique ton adresse de réception :\n• USDT TRC20 / ERC20\n• BTC / ETH / SOL…\n\n📋 _Copie-colle ton adresse ici_",
"withdraw_prompt_paypal":"💳 *Retrait via PayPal*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nIndique ton lien PayPal.me ou email PayPal :\n\n📧 _Ex : paypal.me/tonnom_",
"withdraw_registered":"✅ *Adresse enregistrée !*\n\n💰 `{amount} €`\n📲 {method}\n📋 `{address}`\n\n⏳ L'admin traite ton retrait sous peu.",
"payout_sent":    "💰 *Ton paiement a été envoyé !*\n\n✅ *{amount} €* virés sur ton compte.\n\nMerci d'avoir utilisé *EscrowBot* ! 🙌",
"refund_prompt":  "💸 *Demande de remboursement*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ Tu es sur le point de demander un remboursement.\n\n🔒 *Protection anti-escroquerie / anti-blanchiment :*\nLe remboursement sera effectué *uniquement sur le compte ayant servi au paiement*. Aucune exception.\n\n❓ *Confirmes-tu ta demande ?*",
"btn_refund_yes": "✅  Oui, demander le remboursement",
"btn_refund_no":  "❌  Non, annuler",
"refund_sent":    "📨 *Demande envoyée à l'admin.*\n\n⏳ Remboursement sur ton compte d'origine.",
"refund_done":    "💸 *Ton remboursement est en cours !*\n\nTu recevras la somme sur le compte de paiement initial. 🙏",
"no_sessions":    "😕 Tu n'as pas encore de sessions.",
"invalid_amount": "❌ *Montant invalide !*\n\nEntre un nombre positif. Ex: `50` ou `49.99`",
"announce_off":   "🔴 *EscrowBot — Hors ligne*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nL'admin n'est plus disponible.\n\n⏳ _Transactions suspendues. Reviens bientôt !_",
"announce_on":    "🟢 *EscrowBot — De retour en ligne !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Un admin est disponible.\n\n👇 Tu peux reprendre tes échanges !",
},
"en": {
"choose_lang":    "🌍 *Choose your language:*",
"welcome":        "👋 *Hello {name}!*\n\n🔐 *Welcome to EscrowBot*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nYour trusted middleman for secure transactions.\n\n✅ Funds held until delivery\n🔍 Every delivery verified by admin\n💸 Fee: only *10%*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👇 *What do you want to do?*",
"bot_offline":    "🔴 *EscrowBot is temporarily offline.*\n\nNo admin available.\n\n⏳ _Come back later!_",
"btn_create":     "🛒  Create a session  ·  Buyer",
"btn_join":       "🔑  Join a session  ·  Seller",
"btn_sessions":   "📋  My sessions",
"btn_howto":      "ℹ️  How does it work?",
"btn_server":     "💬  Join the server",
"btn_scamlist":   "🚫  Scam List",
"btn_admin":      "👑  Admin Panel",
"btn_back":       "⬅️  Back to menu",
"howto":          "ℹ️ *How does EscrowBot work?*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n1️⃣ *Buyer* creates a session\n2️⃣ *Unique code* shared with seller\n3️⃣ *Seller* joins with the code\n4️⃣ *Buyer* sets conditions\n5️⃣ *Buyer* pays via secure link\n6️⃣ *Admin* validates payment ✅\n7️⃣ *Seller* delivers\n8️⃣ *Admin* checks & validates 🔍\n9️⃣ *Seller* receives payment 💰\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💸 Fee: *10%* charged to buyer\n🔒 *No money moves without admin approval!*",
"scamlist_empty": "🚫 *Scam List*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ No scammers listed yet.\n\n_List is updated by the admin._",
"scamlist_title": "🚫 *Scam List — People to avoid*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ _These people have been reported for scamming._\n\n",
"step1":          "🛒 *Create an Escrow session*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📝 *Step 1 of 5 — Item*\n\nWhat is the name/description of the item?",
"step2":          "📬 *Step 2 of 5 — Delivery type*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Item: *{item}*\n\nWhat delivery type do you expect?",
"step3":          "💵 *Step 3 of 5 — Price*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Delivery: *{dtype}*\n\nHow much should the seller be paid?\n\n💡 _Just type the amount (ex: 50 or 49.99)_\n⚠️ _10% fee added automatically_",
"step4":          "💳 *Step 4 of 5 — Payment*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💰 *Summary:*\n\n  💵 Seller price  → `{seller} €`\n  📊 Fee (10%)     → `{fees} €`\n  ━━━━━━━━━━━━━━━━━\n  💳 *Total        → `{total} €`*\n\nPayment method?",
"step5":          "📋 *Step 5 of 5 — Conditions*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚖️ Set the conditions for this transaction.\n\nThese will be written on the *session contract*, visible to seller and admin.\n\n✍️ *Write your conditions* or click *Skip.*\n\n💡 _Conditions must be agreed upon in advance with the seller in private._",
"btn_skip_cond":  "⏩  Skip conditions",
"session_created":"🎉 *Session created!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{summary}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📤 *Share this code with the seller:*\n\n```\n{code}\n```\n\n⏳ _Waiting for the seller to join…_",
"join_prompt":    "🔑 *Join an Escrow session*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nEnter the session code the buyer gave you:",
"code_not_found": "❌ *Code not found!*\n\nCheck the code and try again.",
"code_used":      "⛔ *This code is already used!*",
"joined_ok":      "✅ *You joined the session!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{summary}\n\n⏳ *Waiting for buyer's payment…*\n🔔 You'll be notified once confirmed.",
"pay_crypto_msg": "🔔 *The seller has joined your session!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🧑‍💼 *Seller:* {seller}\n\n💰 *Amount: `{total} €`*\n🪙 *Method: Crypto (Multi-currency)*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔗 Click the button below to pay.\n\n⚠️ *IMPORTANT: Do NOT leave the payment page until the bot confirms or the blockchain validates the transaction. Even the admin won't have access to the funds before confirmation. Stay on the page until the bot responds.*",
"pay_paypal_msg": "🔔 *The seller has joined your session!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🧑‍💼 *Seller:* {seller}\n\n💰 *Amount: `{total} €`*\n💳 *Method: PayPal*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n1️⃣ Click button to pay via PayPal\n2️⃣ Come back and send a *screenshot* of the confirmation\n\n⚠️ _Without proof, transaction cannot be validated._",
"pay_link_error": "⚠️ Payment link generation error. Contact admin.",
"send_proof":     "📸 *Send a screenshot* of your PayPal confirmation.",
"proof_sent":     "📤 *Proof sent to admin!*\n\n⏳ Waiting for validation…",
"payment_ok_buyer":"✅ *Your payment has been validated!*\n\n🔔 The seller will now deliver.",
"payment_ok_seller":"💰 *Payment confirmed!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📦 *Item:* {item}\n📬 *Type:* {dtype}\n\n➡️ *Send your delivery here now.*",
"payment_rejected":"❌ *Payment not received.*\n\nMake the transfer and send a clear screenshot.",
"delivery_sent":  "📤 *Delivery sent to admin!*\n\n🔍 Under review…",
"delivery_ok_buyer":"✅ *Your delivery has arrived!*\n📦 Item: *{item}*",
"tx_complete_buyer":"🎉 *Transaction complete!*\n\nThank you for using *EscrowBot*! 🙌",
"delivery_rejected":"❌ *Your delivery was rejected.*\n\n🚫 Content doesn't match.\n➡️ Send the correct delivery.",
"withdraw_prompt_crypto":"🪙 *Crypto Withdrawal*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nEnter your receiving address:\n• USDT TRC20 / ERC20\n• BTC / ETH / SOL…",
"withdraw_prompt_paypal":"💳 *PayPal Withdrawal*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nEnter your PayPal.me link or email:",
"withdraw_registered":"✅ *Address registered!*\n\n💰 `{amount} €`\n📲 {method}\n📋 `{address}`\n\n⏳ Admin will process shortly.",
"payout_sent":    "💰 *Your payment has been sent!*\n\n✅ *{amount} €* to your account.\n\nThank you for using *EscrowBot*! 🙌",
"refund_prompt":  "💸 *Refund Request*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ You're about to request a refund.\n\n🔒 *Anti-fraud protection:*\nRefund will be sent *only to the original payment account*.\n\n❓ *Confirm?*",
"btn_refund_yes": "✅  Yes, request refund",
"btn_refund_no":  "❌  No, cancel",
"refund_sent":    "📨 *Refund request sent to admin.*\n\n⏳ You'll be refunded to your original account.",
"refund_done":    "💸 *Your refund is being processed!* 🙏",
"no_sessions":    "😕 You don't have any sessions yet.",
"invalid_amount": "❌ *Invalid amount!*\n\nEnter a positive number. Ex: `50`",
"announce_off":   "🔴 *EscrowBot — Offline*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nAdmin unavailable.\n\n⏳ _Transactions suspended. Come back soon!_",
"announce_on":    "🟢 *EscrowBot — Back online!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Admin is available.\n\n👇 You can now trade safely!",
},
"ru": {
"choose_lang":    "🌍 *Выберите язык:*",
"welcome":        "👋 *Привет, {name}!*\n\n🔐 *Добро пожаловать в EscrowBot*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nВаш надёжный посредник.\n\n✅ Средства заморожены до получения\n🔍 Каждая поставка проверяется\n💸 Комиссия: *10%*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👇 *Что вы хотите сделать?*",
"bot_offline":    "🔴 *EscrowBot временно не работает.*\n\n⏳ _Вернитесь позже!_",
"btn_create":     "🛒  Создать сессию  ·  Покупатель",
"btn_join":       "🔑  Присоединиться  ·  Продавец",
"btn_sessions":   "📋  Мои сессии",
"btn_howto":      "ℹ️  Как это работает?",
"btn_server":     "💬  Присоединиться к серверу",
"btn_scamlist":   "🚫  Список скамеров",
"btn_admin":      "👑  Панель администратора",
"btn_back":       "⬅️  Назад в меню",
"howto":          "ℹ️ *Как работает EscrowBot?*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n1️⃣ Покупатель создаёт сессию\n2️⃣ Код передаётся продавцу\n3️⃣ Продавец присоединяется\n4️⃣ Покупатель задаёт условия\n5️⃣ Покупатель оплачивает\n6️⃣ Админ подтверждает оплату\n7️⃣ Продавец отправляет товар\n8️⃣ Админ проверяет и подтверждает\n9️⃣ Продавец получает оплату\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💸 Комиссия: *10%*\n🔒 Деньги не переводятся без одобрения!",
"scamlist_empty": "🚫 *Список скамеров*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Список пуст.\n\n_Обновляется администратором._",
"scamlist_title": "🚫 *Список скамеров*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ _Эти люди были замечены в мошенничестве._\n\n",
"step1":          "🛒 *Создать сессию Escrow*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📝 *Шаг 1 из 5 — Товар*\n\nКакой товар вы покупаете?",
"step2":          "📬 *Шаг 2 из 5 — Тип доставки*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Товар: *{item}*\n\nКакой тип доставки ожидаете?",
"step3":          "💵 *Шаг 3 из 5 — Цена*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Доставка: *{dtype}*\n\nСколько получит продавец?\n\n💡 _Введите сумму (пример: 50)_\n⚠️ _Комиссия 10% добавится автоматически_",
"step4":          "💳 *Шаг 4 из 5 — Оплата*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💰 *Итого:*\n\n  💵 Продавец   → `{seller} €`\n  📊 Комиссия   → `{fees} €`\n  ━━━━━━━━━━━━━━━━━\n  💳 *Итого     → `{total} €`*\n\nСпособ оплаты?",
"step5":          "📋 *Шаг 5 из 5 — Условия*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚖️ Укажите условия сделки.\n\nОни будут записаны в *контракт сессии*.\n\n✍️ *Напишите условия* или нажмите *Пропустить.*\n\n💡 _Условия согласовываются заранее в личных сообщениях._",
"btn_skip_cond":  "⏩  Пропустить условия",
"session_created":"🎉 *Сессия создана!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{summary}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📤 *Передайте код продавцу:*\n\n```\n{code}\n```\n\n⏳ _Ожидание продавца…_",
"join_prompt":    "🔑 *Присоединиться к сессии*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nВведите код сессии:",
"code_not_found": "❌ *Код не найден!*\n\nПроверьте код и попробуйте снова.",
"code_used":      "⛔ *Этот код уже используется!*",
"joined_ok":      "✅ *Вы вошли в сессию!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{summary}\n\n⏳ *Ожидание оплаты…*\n🔔 Уведомление после подтверждения.",
"pay_crypto_msg": "🔔 *Продавец присоединился!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🧑‍💼 *Продавец:* {seller}\n\n💰 *Сумма: `{total} €`*\n🪙 *Метод: Крипто*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔗 Нажмите кнопку для оплаты.\n\n⚠️ *ВАЖНО: Не покидайте страницу до подтверждения ботом или блокчейном. Оставайтесь на странице до ответа бота.*",
"pay_paypal_msg": "🔔 *Продавец присоединился!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🧑‍💼 *Продавец:* {seller}\n\n💰 *Сумма: `{total} €`*\n💳 *Метод: PayPal*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n1️⃣ Нажмите кнопку для оплаты\n2️⃣ Отправьте скриншот подтверждения",
"pay_link_error": "⚠️ Ошибка генерации ссылки. Обратитесь к администратору.",
"send_proof":     "📸 *Отправьте скриншот* подтверждения PayPal.",
"proof_sent":     "📤 *Доказательство отправлено!*\n\n⏳ Ожидание подтверждения…",
"payment_ok_buyer":"✅ *Оплата подтверждена!*\n\n🔔 Продавец скоро отправит товар.",
"payment_ok_seller":"💰 *Оплата подтверждена!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📦 *Товар:* {item}\n📬 *Тип:* {dtype}\n\n➡️ *Отправьте товар сюда.*",
"payment_rejected":"❌ *Оплата не получена.*\n\nВыполните перевод и отправьте скриншот.",
"delivery_sent":  "📤 *Товар отправлен на проверку!*\n\n🔍 Проверяется…",
"delivery_ok_buyer":"✅ *Ваш товар получен!*\n📦 Товар: *{item}*",
"tx_complete_buyer":"🎉 *Сделка завершена!*\n\nСпасибо за использование *EscrowBot*! 🙌",
"delivery_rejected":"❌ *Товар отклонён.*\n\n🚫 Содержимое не соответствует.\n➡️ Отправьте правильный товар.",
"withdraw_prompt_crypto":"🪙 *Вывод в крипто*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nУкажите адрес получения.",
"withdraw_prompt_paypal":"💳 *Вывод через PayPal*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nУкажите PayPal.me или email.",
"withdraw_registered":"✅ *Адрес зарегистрирован!*\n\n💰 `{amount} €`\n📲 {method}\n📋 `{address}`\n\n⏳ Обрабатывается.",
"payout_sent":    "💰 *Платёж отправлен!*\n\n✅ *{amount} €* на ваш счёт. 🙌",
"refund_prompt":  "💸 *Запрос на возврат*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ Возврат только на исходный счёт.\n\n❓ *Подтвердить?*",
"btn_refund_yes": "✅  Да, запросить возврат",
"btn_refund_no":  "❌  Нет, отмена",
"refund_sent":    "📨 *Запрос отправлен администратору.*\n\n⏳ Возврат на исходный счёт.",
"refund_done":    "💸 *Возврат обрабатывается!* 🙏",
"no_sessions":    "😕 У вас нет сессий.",
"invalid_amount": "❌ *Неверная сумма!*\n\nВведите положительное число.",
"announce_off":   "🔴 *EscrowBot — Не в сети*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⏳ _Сделки приостановлены. Скоро вернёмся!_",
"announce_on":    "🟢 *EscrowBot — Снова в сети!*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Администратор доступен.",
},
}

def t(uid: int, key: str, **kw) -> str:
    lang = user_lang.get(uid, "fr")
    text = LANG.get(lang, LANG["fr"]).get(key, LANG["fr"].get(key, key))
    return text.format(**kw) if kw else text

# ──────────────────────────────────────────────
#  ÉTATS
# ──────────────────────────────────────────────
(CHOOSE_LANG, BUY_ITEM_NAME, BUY_DELIVERY_TYPE,
 BUY_PRICE, BUY_PAYMENT_METHOD, BUY_CONDITIONS,
 SELLER_ENTER_CODE) = range(7)

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def gen_code(username: str) -> str:
    tag   = (username or "USER")[:8].upper()
    short = str(uuid.uuid4())[:6].upper()
    return f"{tag}-{short}"

def fmt(v: float) -> str:
    return f"{v:.2f}"

def session_summary(s: dict) -> str:
    de = {"Lien URL":"🔗","PDF":"📄","Image":"🖼️","Texte / Code":"📝"}.get(s.get("delivery_type",""),"📦")
    pe = "🪙" if "Crypto" in s.get("payment_method","") else "💳"
    cond      = s.get("conditions","")
    cond_line = f"\n📋 *Conditions :* _{cond}_" if cond else ""
    return (
        f"╔══════════════════════════╗\n"
        f"        📋 *SESSION ESCROW*\n"
        f"╚══════════════════════════╝\n\n"
        f"🔑 *Code :* `{s['code']}`\n"
        f"🛒 *Article :* {s['item_name']}\n"
        f"{de} *Livraison :* {s['delivery_type']}\n"
        f"💵 *Prix vendeur :* `{fmt(s['seller_price'])} €`\n"
        f"💰 *Total (frais inclus) :* `{fmt(s['total_price'])} €`\n"
        f"{pe} *Paiement :* {s['payment_method']}\n"
        f"👤 *Acheteur :* {s.get('buyer_name','?')} | ID: `{s.get('buyer_id','?')}`\n"
        f"🧑‍💼 *Vendeur :* {s.get('seller_name','⏳')} | ID: `{s.get('seller_id','—')}`\n"
        f"📊 *Statut :* {s['status']}\n"
        f"🕒 *Créée le :* {s.get('created_at','?')[:10]}"
        f"{cond_line}\n"
    )

def main_kb(uid: int) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(t(uid,"btn_create"),   callback_data="create_session")],
        [InlineKeyboardButton(t(uid,"btn_join"),     callback_data="join_session")],
        [InlineKeyboardButton(t(uid,"btn_sessions"), callback_data="my_sessions")],
        [InlineKeyboardButton(t(uid,"btn_howto"),    callback_data="how_it_works")],
        [
            InlineKeyboardButton(t(uid,"btn_server"),   url=SERVER_LINK),
            InlineKeyboardButton(t(uid,"btn_scamlist"), callback_data="scam_list"),
        ],
    ]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton(t(uid,"btn_admin"), callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

async def generate_oxapay_link(amount_eur: float, order_id: str) -> str | None:
    """Génère un lien de paiement OxaPay via l'API."""
    payload = {
        "merchant":   OXAPAY_KEY,
        "amount":     amount_eur,
        "currency":   "EUR",
        "lifeTime":   30,
        "orderId":    order_id,
        "description": f"EscrowBot — Session {order_id}",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OXAPAY_API, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get("result") == 100:
                    return data.get("payLink")
    except Exception as e:
        logger.error(f"OxaPay error: {e}")
    return None

# ══════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    all_users.add(uid)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇫🇷  Français", callback_data="lang_fr")],
        [InlineKeyboardButton("🇬🇧  English",  callback_data="lang_en")],
        [InlineKeyboardButton("🇷🇺  Русский",  callback_data="lang_ru")],
    ])
    await update.message.reply_text("🌍 Choisis ta langue / Choose your language / Выберите язык :", reply_markup=kb)
    return CHOOSE_LANG

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid  = q.from_user.id
    name = q.from_user.first_name or ""
    user_lang[uid] = q.data.replace("lang_","")
    if not bot_online and uid != ADMIN_ID:
        await q.edit_message_text(t(uid,"bot_offline"), parse_mode="Markdown")
        return ConversationHandler.END
    await q.edit_message_text(t(uid,"welcome",name=name), parse_mode="Markdown", reply_markup=main_kb(uid))
    return ConversationHandler.END

# ══════════════════════════════════════════════
#  SCAM LIST
# ══════════════════════════════════════════════

async def show_scam_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    kb  = InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,"btn_back"), callback_data="back_start")]])
    if not scam_list:
        await q.edit_message_text(t(uid,"scamlist_empty"), parse_mode="Markdown", reply_markup=kb)
        return
    txt = t(uid,"scamlist_title")
    for i, entry in enumerate(scam_list, 1):
        txt += (
            f"*{i}.* 👤 {entry['username']} | ID: `{entry['id']}`\n"
            f"   📅 {entry['date']}\n"
            f"   ❗ _{entry['reason']}_\n\n"
        )
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=kb)

async def cmd_addscam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /addscam @pseudo ID Raison"""
    if update.effective_user.id != ADMIN_ID:
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "❌ Usage : `/addscam @pseudo ID raison`\n_Ex: /addscam @jean123 987654321 A scammé 50€_",
            parse_mode="Markdown"); return
    username = args[0]
    uid_scam = args[1]
    reason   = " ".join(args[2:])
    scam_list.append({
        "username": username,
        "id":       uid_scam,
        "reason":   reason,
        "date":     datetime.now().strftime("%d/%m/%Y"),
    })
    await update.message.reply_text(
        f"✅ *{username}* ajouté à la Scam List.\n❗ Raison : _{reason}_",
        parse_mode="Markdown")

async def cmd_removescam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /removescam @pseudo"""
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❌ Usage : `/removescam @pseudo`", parse_mode="Markdown"); return
    username = context.args[0]
    before   = len(scam_list)
    scam_list[:] = [e for e in scam_list if e["username"] != username]
    if len(scam_list) < before:
        await update.message.reply_text(f"✅ *{username}* retiré de la Scam List.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ *{username}* non trouvé.", parse_mode="Markdown")

# ══════════════════════════════════════════════
#  COMMENT ÇA MARCHE
# ══════════════════════════════════════════════

async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    await q.edit_message_text(t(uid,"howto"), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,"btn_back"), callback_data="back_start")]]))

# ══════════════════════════════════════════════
#  CRÉER SESSION
# ══════════════════════════════════════════════

async def create_session_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    if not bot_online and uid != ADMIN_ID:
        await q.edit_message_text(t(uid,"bot_offline"), parse_mode="Markdown")
        return ConversationHandler.END
    await q.edit_message_text(t(uid,"step1"), parse_mode="Markdown")
    return BUY_ITEM_NAME

async def buy_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    context.user_data["item_name"] = update.message.text.strip()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗  Lien URL",             callback_data="del_url")],
        [InlineKeyboardButton("📄  Fichier PDF",          callback_data="del_pdf")],
        [InlineKeyboardButton("🖼️  Image / Photo",        callback_data="del_image")],
        [InlineKeyboardButton("📝  Texte / Code / Accès", callback_data="del_text")],
    ])
    await update.message.reply_text(t(uid,"step2",item=context.user_data["item_name"]),
        parse_mode="Markdown", reply_markup=kb)
    return BUY_DELIVERY_TYPE

async def buy_delivery_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    context.user_data["delivery_type"] = {
        "del_url":"Lien URL","del_pdf":"PDF","del_image":"Image","del_text":"Texte / Code"
    }[q.data]
    await q.edit_message_text(t(uid,"step3",dtype=context.user_data["delivery_type"]),parse_mode="Markdown")
    return BUY_PRICE

async def buy_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        sp = float(update.message.text.replace(",",".").strip())
        if sp <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text(t(uid,"invalid_amount"),parse_mode="Markdown")
        return BUY_PRICE
    total = sp * (1 + FEES_PCT)
    context.user_data["seller_price"] = sp
    context.user_data["total_price"]  = total
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙  Crypto (Multi-devises)", callback_data="pay_crypto")],
        [InlineKeyboardButton("💳  PayPal",                 callback_data="pay_paypal")],
    ])
    await update.message.reply_text(
        t(uid,"step4",seller=fmt(sp),fees=fmt(sp*FEES_PCT),total=fmt(total)),
        parse_mode="Markdown", reply_markup=kb)
    return BUY_PAYMENT_METHOD

async def buy_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    context.user_data["payment_method"] = "Crypto" if q.data=="pay_crypto" else "PayPal"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,"btn_skip_cond"), callback_data="skip_conditions")]])
    await q.edit_message_text(t(uid,"step5"),parse_mode="Markdown",reply_markup=kb)
    return BUY_CONDITIONS

async def buy_conditions_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = update.effective_user
    context.user_data["conditions"] = update.message.text.strip()
    await finalize_session(uid, user, context, update.message.reply_text)
    return ConversationHandler.END

async def buy_conditions_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid  = q.from_user.id
    user = q.from_user
    context.user_data["conditions"] = ""
    await finalize_session(uid, user, context, q.edit_message_text)
    return ConversationHandler.END

async def finalize_session(uid, user, context, reply_fn):
    ud    = context.user_data
    code  = gen_code(user.username or str(uid))
    uname = f"@{user.username}" if user.username else user.first_name
    s = {
        "code":           code,
        "item_name":      ud["item_name"],
        "delivery_type":  ud["delivery_type"],
        "seller_price":   ud["seller_price"],
        "total_price":    ud["total_price"],
        "payment_method": ud["payment_method"],
        "conditions":     ud.get("conditions",""),
        "buyer_id":       uid,
        "buyer_name":     uname,
        "seller_id":      None,
        "seller_name":    None,
        "status":         "⏳ En attente du vendeur",
        "delivery_file":  None,
        "payment_proof":  None,
        "created_at":     datetime.now().isoformat(),
    }
    sessions[code]     = s
    user_sessions[uid] = code
    await reply_fn(t(uid,"session_created",summary=session_summary(s),code=code),parse_mode="Markdown")
    await context.bot.send_message(chat_id=ADMIN_ID,
        text=f"🆕 *Nouvelle session !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{session_summary(s)}",
        parse_mode="Markdown")

# ══════════════════════════════════════════════
#  REJOINDRE SESSION
# ══════════════════════════════════════════════

async def join_session_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    if not bot_online and uid != ADMIN_ID:
        await q.edit_message_text(t(uid,"bot_offline"),parse_mode="Markdown")
        return ConversationHandler.END
    await q.edit_message_text(t(uid,"join_prompt"),parse_mode="Markdown")
    return SELLER_ENTER_CODE

async def seller_enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = update.effective_user
    code = update.message.text.strip().upper()
    s    = sessions.get(code)
    if not s:
        await update.message.reply_text(t(uid,"code_not_found"),parse_mode="Markdown")
        return SELLER_ENTER_CODE
    if s["seller_id"] is not None:
        await update.message.reply_text(t(uid,"code_used"),parse_mode="Markdown")
        return ConversationHandler.END

    s["seller_id"]     = uid
    s["seller_name"]   = f"@{user.username}" if user.username else user.first_name
    s["status"]        = "⏳ En attente du paiement acheteur"
    user_sessions[uid] = code

    await update.message.reply_text(t(uid,"joined_ok",summary=session_summary(s)),parse_mode="Markdown")

    buid  = s["buyer_id"]
    total = fmt(s["total_price"])

    if s["payment_method"] == "Crypto":
        pay_link = await generate_oxapay_link(s["total_price"], code)
        if pay_link:
            pay_txt = t(buid,"pay_crypto_msg",seller=s["seller_name"],total=total)
            kb = [
                [InlineKeyboardButton(f"🪙  Payer {total} € en Crypto", url=pay_link)],
                [InlineKeyboardButton("💸  Demande de remboursement", callback_data=f"refund_ask_{code}")],
            ]
        else:
            pay_txt = t(buid,"pay_link_error")
            kb = [[InlineKeyboardButton("💸  Remboursement", callback_data=f"refund_ask_{code}")]]
    else:
        pay_txt = t(buid,"pay_paypal_msg",seller=s["seller_name"],total=total)
        kb = [
            [InlineKeyboardButton(f"💳  Payer {total} € via PayPal", url=f"{PAYPAL_URL}/{total}EUR")],
            [InlineKeyboardButton("💸  Demande de remboursement", callback_data=f"refund_ask_{code}")],
        ]

    await context.bot.send_message(chat_id=buid, text=pay_txt, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb))
    await context.bot.send_message(chat_id=ADMIN_ID,
        text=f"👥 *Vendeur rejoint !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{session_summary(s)}",
        parse_mode="Markdown")
    return ConversationHandler.END

# ══════════════════════════════════════════════
#  REMBOURSEMENT
# ══════════════════════════════════════════════

async def refund_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid  = q.from_user.id
    code = q.data.replace("refund_ask_","")
    kb   = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,"btn_refund_yes"), callback_data=f"refund_confirm_{code}")],
        [InlineKeyboardButton(t(uid,"btn_refund_no"),  callback_data="back_start")],
    ])
    await q.edit_message_text(t(uid,"refund_prompt"),parse_mode="Markdown",reply_markup=kb)

async def refund_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid  = q.from_user.id
    code = q.data.replace("refund_confirm_","")
    s    = sessions.get(code)
    if not s:
        await q.edit_message_text("❌ Session introuvable."); return

    proof     = s.get("payment_proof")
    admin_txt = (
        f"💸 *DEMANDE DE REMBOURSEMENT !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{session_summary(s)}\n"
        f"👤 Acheteur : {s['buyer_name']} | ID: `{s['buyer_id']}`\n"
        f"💳 Méthode : {s['payment_method']}\n\n"
        f"⚠️ _Rembourser uniquement sur le compte d'origine._"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅  J'ai remboursé !", callback_data=f"admin_refunded_{code}_{uid}")]])

    if proof:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=proof, caption=admin_txt, parse_mode="Markdown", reply_markup=kb)
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_txt, parse_mode="Markdown", reply_markup=kb)

    sessions.pop(code, None)
    user_sessions.pop(uid, None)
    if s.get("seller_id") and user_sessions.get(s["seller_id"]) == code:
        user_sessions.pop(s["seller_id"], None)

    await q.edit_message_text(t(uid,"refund_sent"),parse_mode="Markdown")

async def admin_refunded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    parts     = q.data.replace("admin_refunded_","").rsplit("_",1)
    buyer_uid = int(parts[-1])
    await context.bot.send_message(chat_id=buyer_uid, text=t(buyer_uid,"refund_done"),parse_mode="Markdown")
    await q.edit_message_text("✅ *Remboursement confirmé.*",parse_mode="Markdown")

# ══════════════════════════════════════════════
#  PREUVE PAIEMENT PAYPAL
# ══════════════════════════════════════════════

async def handle_buyer_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = user_sessions.get(uid)
    if not code: return
    s = sessions.get(code)
    if not s or s["buyer_id"] != uid: return
    if s["status"] != "⏳ En attente du paiement acheteur": return
    if s["payment_method"] != "PayPal": return

    if not update.message.photo:
        await update.message.reply_text(t(uid,"send_proof"),parse_mode="Markdown"); return

    fid = update.message.photo[-1].file_id
    s["payment_proof"] = fid
    s["status"]        = "🔍 Preuve de paiement en attente"

    await update.message.forward(chat_id=ADMIN_ID)
    await context.bot.send_message(chat_id=ADMIN_ID,
        text=(f"💳 *Preuve PayPal reçue !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
              f"{session_summary(s)}\n"
              f"👤 {s['buyer_name']} | ID: `{s['buyer_id']}`"),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅  Paiement reçu !", callback_data=f"admin_pay_ok_{code}"),
            InlineKeyboardButton("❌  Pas reçu",        callback_data=f"admin_pay_rej_{code}"),
        ]]))
    await update.message.reply_text(t(uid,"proof_sent"),parse_mode="Markdown")

# ══════════════════════════════════════════════
#  ADMIN PAIEMENT
# ══════════════════════════════════════════════

async def admin_pay_ok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    code = q.data.replace("admin_pay_ok_","")
    s    = sessions.get(code)
    if not s: await q.edit_message_text("❌ Session introuvable."); return
    s["status"] = "⏳ En attente de la livraison vendeur"
    await context.bot.send_message(chat_id=s["buyer_id"],  text=t(s["buyer_id"],"payment_ok_buyer"),parse_mode="Markdown")
    await context.bot.send_message(chat_id=s["seller_id"], text=t(s["seller_id"],"payment_ok_seller",item=s["item_name"],dtype=s["delivery_type"]),parse_mode="Markdown")
    await q.edit_message_text(f"✅ Paiement validé — `{code}`.",parse_mode="Markdown")

async def admin_pay_rej(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    code = q.data.replace("admin_pay_rej_","")
    s    = sessions.get(code)
    if not s: await q.edit_message_text("❌ Session introuvable."); return
    s["status"] = "⏳ En attente du paiement acheteur"
    await context.bot.send_message(chat_id=s["buyer_id"], text=t(s["buyer_id"],"payment_rejected"),parse_mode="Markdown")
    await q.edit_message_text(f"❌ Paiement rejeté — `{code}`.",parse_mode="Markdown")

async def cmd_cryptook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Usage : /cryptook CODE"); return
    code = context.args[0].upper()
    s    = sessions.get(code)
    if not s:
        await update.message.reply_text("❌ Session introuvable."); return
    s["status"] = "⏳ En attente de la livraison vendeur"
    await context.bot.send_message(chat_id=s["buyer_id"],  text=t(s["buyer_id"],"payment_ok_buyer"),parse_mode="Markdown")
    await context.bot.send_message(chat_id=s["seller_id"], text=t(s["seller_id"],"payment_ok_seller",item=s["item_name"],dtype=s["delivery_type"]),parse_mode="Markdown")
    await update.message.reply_text(f"✅ Crypto validé — `{code}`.",parse_mode="Markdown")

# ══════════════════════════════════════════════
#  LIVRAISON VENDEUR
# ══════════════════════════════════════════════

async def seller_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = user_sessions.get(uid)
    if not code: return
    s = sessions.get(code)
    if not s or s["seller_id"] != uid: return
    if s["status"] != "⏳ En attente de la livraison vendeur": return

    msg = update.message
    if msg.document: di = {"type":"document","file_id":msg.document.file_id}
    elif msg.photo:  di = {"type":"photo","file_id":msg.photo[-1].file_id}
    elif msg.text:   di = {"type":"text","content":msg.text}
    else: return

    s["delivery_file"] = di
    s["status"]        = "🔍 En attente validation livraison"

    await msg.forward(chat_id=ADMIN_ID)
    await context.bot.send_message(chat_id=ADMIN_ID,
        text=f"📦 *Livraison reçue !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{session_summary(s)}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅  Valider la livraison", callback_data=f"admin_approve_{code}"),
            InlineKeyboardButton("❌  Rejeter",              callback_data=f"admin_reject_{code}"),
        ]]))
    await msg.reply_text(t(uid,"delivery_sent"),parse_mode="Markdown")

# ══════════════════════════════════════════════
#  ADMIN LIVRAISON
# ══════════════════════════════════════════════

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    code = q.data.replace("admin_approve_","")
    s    = sessions.get(code)
    if not s: await q.edit_message_text("❌ Session introuvable."); return

    s["status"] = "⏳ En attente adresse retrait vendeur"
    buid = s["buyer_id"]
    di   = s.get("delivery_file",{})
    cap  = t(buid,"delivery_ok_buyer",item=s["item_name"])

    if di.get("type")=="document":
        await context.bot.send_document(chat_id=buid,document=di["file_id"],caption=cap,parse_mode="Markdown")
    elif di.get("type")=="photo":
        await context.bot.send_photo(chat_id=buid,photo=di["file_id"],caption=cap,parse_mode="Markdown")
    elif di.get("type")=="text":
        await context.bot.send_message(chat_id=buid,text=f"{cap}\n\n📝 *Contenu :*\n\n{di['content']}",parse_mode="Markdown")

    await context.bot.send_message(chat_id=buid,text=t(buid,"tx_complete_buyer"),parse_mode="Markdown")

    suid = s["seller_id"]
    wp   = t(suid,"withdraw_prompt_crypto") if s["payment_method"]=="Crypto" else t(suid,"withdraw_prompt_paypal")
    await context.bot.send_message(chat_id=suid,
        text=f"🎉 *Livraison validée !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💵 Tu vas recevoir *{fmt(s['seller_price'])} €*\n\n{wp}",
        parse_mode="Markdown")
    await q.edit_message_text(f"✅ Livraison validée — `{code}`.",parse_mode="Markdown")

async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    code = q.data.replace("admin_reject_","")
    s    = sessions.get(code)
    if not s: await q.edit_message_text("❌ Session introuvable."); return
    s["status"] = "⏳ En attente de la livraison vendeur"
    await context.bot.send_message(chat_id=s["seller_id"],text=t(s["seller_id"],"delivery_rejected"),parse_mode="Markdown")
    await q.edit_message_text(f"❌ Livraison rejetée — `{code}`.",parse_mode="Markdown")

# ══════════════════════════════════════════════
#  RETRAIT VENDEUR
# ══════════════════════════════════════════════

async def seller_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = user_sessions.get(uid)
    if not code: return
    s = sessions.get(code)
    if not s or s["seller_id"] != uid: return
    if s["status"] != "⏳ En attente adresse retrait vendeur": return

    address = update.message.text.strip()
    s["withdraw_address"] = address
    s["status"]           = "⏳ Retrait en cours"
    ml = "🪙 Crypto" if s["payment_method"]=="Crypto" else "💳 PayPal"

    await update.message.reply_text(t(uid,"withdraw_registered",amount=fmt(s["seller_price"]),method=ml,address=address),parse_mode="Markdown")
    await context.bot.send_message(chat_id=ADMIN_ID,
        text=(f"💸 *Demande de retrait !*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
              f"🔑 `{code}`\n"
              f"🧑‍💼 {s['seller_name']} | ID: `{s['seller_id']}`\n"
              f"📲 {ml}\n📋 `{address}`\n"
              f"💰 *{fmt(s['seller_price'])} €*"),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅  J'ai envoyé !", callback_data=f"admin_paid_{code}")]]))

async def admin_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    code = q.data.replace("admin_paid_","")
    s    = sessions.get(code)
    if not s: await q.edit_message_text("❌ Session introuvable."); return
    s["status"] = "✅ Transaction complète"
    suid = s["seller_id"]
    await context.bot.send_message(chat_id=suid,text=t(suid,"payout_sent",amount=fmt(s["seller_price"])),parse_mode="Markdown")
    await q.edit_message_text(f"✅ Session `{code}` clôturée.",parse_mode="Markdown")

# ══════════════════════════════════════════════
#  MES SESSIONS
# ══════════════════════════════════════════════

async def my_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    us  = [s for s in sessions.values() if s["buyer_id"]==uid or s["seller_id"]==uid]
    kb  = InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,"btn_back"),callback_data="back_start")]])
    if not us:
        await q.edit_message_text(t(uid,"no_sessions"),parse_mode="Markdown",reply_markup=kb); return
    txt = "📋 *Tes sessions :*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for s in us[-5:]:
        role = "🛒" if s["buyer_id"]==uid else "🧑‍💼"
        txt += f"{role} `{s['code']}` — {s['item_name']}\n{s['status']}\n\n"
    await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=kb)

# ══════════════════════════════════════════════
#  PANEL ADMIN
# ══════════════════════════════════════════════

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    total     = len(sessions)
    completed = sum(1 for s in sessions.values() if "complète" in s["status"])
    pending   = sum(1 for s in sessions.values() if "attente" in s["status"].lower())
    revenue   = sum(s["total_price"]-s["seller_price"] for s in sessions.values() if "complète" in s["status"])
    scams     = len(scam_list)
    sl        = "🟢 EN LIGNE" if bot_online else "🔴 HORS LIGNE"
    btn_tog   = "🔴  Mettre HORS LIGNE" if bot_online else "🟢  Mettre EN LIGNE"
    await q.edit_message_text(
        f"👑 *Panel Admin — EscrowBot*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📡 *Statut :* {sl}\n\n"
        f"📊 Sessions totales : *{total}*\n"
        f"✅ Complètes : *{completed}*\n"
        f"⏳ En cours : *{pending}*\n"
        f"🚫 Scam List : *{scams}* entrées\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Revenus (10%) :* `{fmt(revenue)} €`\n\n"
        f"*Commandes admin :*\n"
        f"• `/cryptook CODE` — Valider paiement crypto\n"
        f"• `/addscam @pseudo ID raison` — Ajouter scam\n"
        f"• `/removescam @pseudo` — Retirer scam",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(btn_tog, callback_data="toggle_bot")],
            [InlineKeyboardButton("⬅️  Retour", callback_data="back_start")],
        ]))

async def toggle_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_online
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    bot_online = not bot_online
    key = "announce_on" if bot_online else "announce_off"
    for uid in list(all_users):
        if uid == ADMIN_ID: continue
        lang = user_lang.get(uid,"fr")
        try:
            await context.bot.send_message(chat_id=uid,text=LANG[lang][key],parse_mode="Markdown")
        except Exception: pass
    sl      = "🟢 EN LIGNE" if bot_online else "🔴 HORS LIGNE"
    btn_tog = "🔴  Mettre HORS LIGNE" if bot_online else "🟢  Mettre EN LIGNE"
    await q.edit_message_text(
        f"👑 *Panel Admin*\n\n📡 *Statut :* {sl}\n\n✅ Annonce envoyée à tous.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(btn_tog, callback_data="toggle_bot")],
            [InlineKeyboardButton("⬅️  Retour", callback_data="back_start")],
        ]))

# ══════════════════════════════════════════════
#  RETOUR MENU
# ══════════════════════════════════════════════

async def back_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid  = q.from_user.id
    name = q.from_user.first_name or ""
    if not bot_online and uid != ADMIN_ID:
        await q.edit_message_text(t(uid,"bot_offline"),parse_mode="Markdown"); return
    await q.edit_message_text(t(uid,"welcome",name=name),parse_mode="Markdown",reply_markup=main_kb(uid))

# ══════════════════════════════════════════════
#  ROUTEUR MESSAGES
# ══════════════════════════════════════════════

async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = user_sessions.get(uid)
    if not code: return
    s = sessions.get(code)
    if not s: return
    st = s["status"]
    if s["buyer_id"]==uid  and st=="⏳ En attente du paiement acheteur":
        await handle_buyer_proof(update, context)
    elif s["seller_id"]==uid and st=="⏳ En attente de la livraison vendeur":
        await seller_delivery(update, context)
    elif s["seller_id"]==uid and st=="⏳ En attente adresse retrait vendeur":
        await seller_withdraw(update, context)

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    lang_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={CHOOSE_LANG: [CallbackQueryHandler(set_lang, pattern="^lang_")]},
        fallbacks=[CommandHandler("start", start)],
    )
    create_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_session_start, pattern="^create_session$")],
        states={
            BUY_ITEM_NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_item_name)],
            BUY_DELIVERY_TYPE:  [CallbackQueryHandler(buy_delivery_type, pattern="^del_")],
            BUY_PRICE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_price)],
            BUY_PAYMENT_METHOD: [CallbackQueryHandler(buy_payment_method, pattern="^pay_")],
            BUY_CONDITIONS:     [
                MessageHandler(filters.TEXT & ~filters.COMMAND, buy_conditions_text),
                CallbackQueryHandler(buy_conditions_skip, pattern="^skip_conditions$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    join_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(join_session_start, pattern="^join_session$")],
        states={SELLER_ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_enter_code)]},
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(lang_conv)
    app.add_handler(create_conv)
    app.add_handler(join_conv)

    for cmd, fn in [
        ("cryptook",    cmd_cryptook),
        ("addscam",     cmd_addscam),
        ("removescam",  cmd_removescam),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    for pat, fn in [
        ("^how_it_works$",   how_it_works),
        ("^my_sessions$",    my_sessions),
        ("^admin_panel$",    admin_panel),
        ("^back_start$",     back_start),
        ("^toggle_bot$",     toggle_bot),
        ("^scam_list$",      show_scam_list),
        ("^refund_ask_",     refund_ask),
        ("^refund_confirm_", refund_confirm),
        ("^admin_refunded_", admin_refunded),
        ("^admin_pay_ok_",   admin_pay_ok),
        ("^admin_pay_rej_",  admin_pay_rej),
        ("^admin_approve_",  admin_approve),
        ("^admin_reject_",   admin_reject),
        ("^admin_paid_",     admin_paid),
    ]:
        app.add_handler(CallbackQueryHandler(fn, pattern=pat))

    app.add_handler(MessageHandler(
        (filters.TEXT | filters.Document.ALL | filters.PHOTO) & ~filters.COMMAND,
        route_message,
    ))

    logger.info("🤖 EscrowBot démarré !")
    app.run_polling()

if __name__ == "__main__":
    main()
