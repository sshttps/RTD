import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread

# ---------------------------
# SERVIDOR FLASK
# ---------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "¡El bot está corriendo correctamente!"

def run_server():
    port = int(os.environ.get("PORT", 8080))  # Render asigna dinámicamente este puerto
    app.run(host="0.0.0.0", port=port)

Thread(target=run_server).start()

# ---------------------------
# CONFIGURACIÓN DE LOGGING
# ---------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------------------
# BASE DE DATOS JSON PARA USUARIOS AUTORIZADOS
# ---------------------------
USERS_DB_FILE = "usuarios.json"
ADMIN_ID = 7293647496  # ID del administrador

def load_users() -> list:
    if os.path.exists(USERS_DB_FILE):
        with open(USERS_DB_FILE, "r") as f:
            return json.load(f)
    else:
        return [ADMIN_ID]

def save_users(users: list) -> None:
    with open(USERS_DB_FILE, "w") as f:
        json.dump(users, f)

USUARIOS_AUTORIZADOS = load_users()
FREE_MODE = False  # Flag para acceso libre

# ---------------------------
# CONFIGURACIÓN DE COMPROBANTES
# ---------------------------
FONT_PATH = "fuente.ttf"  # Asegúrate de que la ruta sea correcta
FONT_MOVIMIENTOS_PATH = "fuente.ttf"

COMPROBANTES = {
    "comprobante1": {
        "template": "plantilla1.jpg",
        "output": "comprobante1_generado.png",
        "styles": {
            "nombre": {"size": 40, "color": "#1b0b19", "pos": (100, 885)},
            "telefono": {"size": 40, "color": "#1b0b19", "pos": (200, 1080)},
            "valor1": {"size": 40, "color": "#1b0b19", "pos": (300, 980)},
            "fecha": {"size": 40, "color": "#1b0b19", "pos": (60, 1200)},
        },
    },
    "comprobante2": {
        "template": "plantilla2.jpeg",
        "output": "comprobante2_generado.png",
        "styles": {
            "nombre": {"size": 28, "color": "#1b0b19", "pos": (86, 575)},
            "telefono": {"size": 28, "color": "#1b0b19", "pos": (86, 735)},
            "valor1": {"size": 28, "color": "#1b0b19", "pos": (86, 670)},
            "fecha": {"size": 28, "color": "#1b0b19", "pos": (86, 820)},
        },
    },
    "comprobante3": {
        "template": "plantilla3.jpeg",
        "output": "comprobante3_generado.png",
        "styles": {
            "nombre": {"size": 30, "color": "#1b0b19", "pos": (-8000, 795)},
            "telefono": {"size": 30, "color": "#1b0b19", "pos": (500, 895)},
            "valor1": {"size": 30, "color": "#1b0b19", "pos": (50, 845)},
            "fecha": {"size": 30, "color": "#1b0b19", "pos": (50, 970)},
        },
    },
    "comprobante4": {  # Se solicitan solo teléfono y valor; se incluye la fecha
        "template": "plantilla4.jpg",
        "output": "comprobante4_generado.png",
        "styles": {
            "nombre": {"size": 23, "color": "#1b0b19", "pos": (9999, 99999)},  # No se muestra
            "telefono": {"size": 23, "color": "#1b0b19", "pos": (1000, 490)},
            "valor1": {"size": 23, "color": "#1b0b19", "pos": (2000, 540)},
            "fecha": {"size": 23, "color": "#1b0b19", "pos": (3000, 620)}
        },
    },
    "comprobante5": {
        "template": "plantilla5.jpg",
        "output": "comprobante5_generado.png",
        "styles": {
            "nombre": {"size": 22, "color": "#1b0b19", "pos": (230, 430)},
            "telefono": {"size": 22, "color": "#1b0b19", "pos": (200, 604)},
            "valor1": {"size": 22, "color": "#1b0b19", "pos": (200, 700)},
            "fecha": {"size": 22, "color": "#1b0b19", "pos": (200, 960)},  # No se dibuja en comprobante5
            "cc": {"size": 22, "color": "#1b0b19", "pos": (200, 800)},     # Alineado con los demás campos
        },
    },
    "movimientos": {
        "template": "movimientos.jpg",
        "output": "movimiento_generado.png",
        "styles": {
            "nombre": {"size": 30, "color": "#1b0b19", "pos": (40, 465)},
            "valor1": {"size": 30, "color": "#007500", "pos": (10, 45)},
        },
    },
}

# ---------------------------
# CONFIGURACIÓN DE LOS CAMPOS DE CONVERSACIÓN
# ---------------------------
conversation_fields = {
    "comprobante1": [
        ("name", "👤 Digite el nombre:"),
        ("phone", "📞 Digite el número:"),
        ("value", "🏦 Digite el valor:")
    ],
    "comprobante2": [
        ("name", "👤 Digite el nombre:"),
        ("phone", "📞 Digite el número:"),
        ("value", "💸 Digite el valor:")
    ],
    "comprobante3": [
        ("name", "👤 Digite el nombre:"),
        ("phone", "📞 Digite el número:"),
        ("value", "💸 Digite el valor:")
    ],
    "comprobante4": [
        ("phone", "📞 Digite el número:"),
        ("value", "💸 Digite el valor:")
    ],
    "comprobante5": [
        ("name", "👤 Digite el nombre:"),
        ("phone", "📞 Digite el número:"),
        ("value", "💸 Digite el valor:"),
        ("cc", "🎫 Digite el CC:")
    ],
    "movimientos": [
        ("name", "👤 Digite el nombre:"),
        ("value", "💸 Comprobante el valor:")
    ]
}

# Para mostrar títulos bonitos en el prompt inicial de cada comprobante
comprobante_titles = {
    "comprobante1": "1️⃣",
    "comprobante2": "2️⃣",
    "comprobante3": "3️⃣",
    "comprobante4": "4️⃣",
    "comprobante5": "5️⃣",
    "movimientos": "📌"
}

# -------------------------FUNCIONESIONES AUXILIARES
# ---------------------------
def validar_archivo(path: str) -> bool:
    if not os.path.exists(path):
        logging.error(f"Archivo no encontrado: {path}")
        return False
    return True

def obtener_fecha_general() -> tuple[str, str]:
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    utc_now = datetime.now(pytz.utc)
    colombia_tz = pytz.timezone("America/Bogota")
    hora_colombiana = utc_now.astimezone(colombia_tz)
    dia = f"{hora_colombiana.day:02d}"
    mes = meses[hora_colombiana.month - 1]
    anio = hora_colombiana.year
    hora = hora_colombiana.strftime("%I:%M %p").lower()
    hora = hora.replace("am", "a. m.").replace("pm", "p. m.")
    linea_fecha = f"{dia} de {mes} de {anio}"
    linea_hora = f"a las {hora}"
    return linea_fecha, linea_hora

def formatear_nombre(nombre: str, comprobante: str) -> str:
    return nombre.title()

def formatear_telefono(telefono: str, comprobante: str) -> str:
    # Elimina espacios y luego formatea a "300 335 7510"
    telefono = telefono.replace(" ", "")
    if len(telefono) == 10:
        return f"{telefono[:3]} {telefono[3:6]} {telefono[6:]}"
    return telefono

def formatear_valor(valor: int) -> str:
    # Formato: "$ 18.000,00"
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generar_comprobante(nombre: str, telefono: str, valor: int, config: dict, ajuste_x: int = 0, cc: str = "") -> str:
    template_path = config["template"]
    output_path = config["output"]
    styles = config["styles"]

    if not os.path.exists(template_path) or not os.path.exists(FONT_PATH):
        raise FileNotFoundError("Archivo de plantilla o fuente no encontrado")

    escala = 3  # Resolución alta
    img = Image.open(template_path)
    img = img.resize((img.width * escala, img.height * escala), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)

    fecha_linea1, fecha_linea2 = obtener_fecha_general()
    valor_formateado = formatear_valor(valor)
    ajuste_fecha_y = -25

    for key, style in styles.items():
        font = ImageFont.truetype(FONT_PATH, size=style["size"] * escala)
        # Para comprobante5, se omite la fecha; en comprobante4 se dibuja la fecha
        if key == "fecha":
            if output_path == "comprobante5_generado.png":
                continue
            pos_y_base = style["pos"][1] * escala + ajuste_fecha_y * escala
            bbox1 = draw.textbbox((0, 0), fecha_linea1, font=font)
            text_width1 = bbox1[2] - bbox1[0]
            pos_x1 = img.width - text_width1 - 20 + ajuste_x
            draw.text((pos_x1, pos_y_base), fecha_linea1, font=font, fill=style["color"])
            bbox2 = draw.textbbox((0, 0), fecha_linea2, font=font)
            text_width2 = bbox2[2] - bbox2[0]
            pos_x2 = img.width - text_width2 - 20 + ajuste_x
            pos_y2 = pos_y_base + font.size + 5
            draw.text((pos_x2, pos_y2), fecha_linea2, font=font, fill=style["color"])
            continue

        if key == "nombre":
            texto = formatear_nombre(nombre, "comprobante")
        elif key == "telefono":
            texto = formatear_telefono(telefono, "comprobante")
        elif key == "valor1":
            texto = valor_formateado
        else:
            conimport
        bbox = draw.textbbox((0, 0), texto, font=font)
        text_width = bbox[2] - bbox[0]
        pos_x = img.width - text_width - 20 + ajuste_x
        pos_y = style["pos"][1] * escala
        draw.text((pos_x, pos_y), texto, font=font, fill=style["color"])

    # Para comprobante5, dibuja el campo "cc" manualmente
    if output_path == "comprobante5_generado.png":
        cc_style = styles.get("cc")
        if cc_style:
            font = ImageFont.truetype(FONT_PATH, size=cc_style["size"] * escala)
            pos_x = cc_style["pos"][0] * escala + ajuste_x
            pos_y = cc_style["pos"][1] * escala
            draw.text((pos_x, pos_y), cc, font=font, fill=cc_style["color"])

    img.save(output_path, quality=99)
    return output_path

async def verificar_acceso(update: Update) -> bool:
    global FREE_MODE
    if FREE_MODE:
        return True
    user_id = update.effective_user.id
    if user_id not in USUARIOS_AUTORIZADOS:
        await update.message.reply_text("❌ Acceso denegado. No estás autorizado para usar este bot.")
        return False
    return True

# ---------------------------
# COMANDOS DEL BOT
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("💡 Cómo usar", callback_data="how_to")],
        [InlineKeyboardButton("👤 Creador", callback_data="creator")],
        [InlineKeyboardButton("🔒 Admins", callback_data="admins")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👨🏻‍💻 ¡Bienvenido al bot de comprobantes!\nSelecciona una opción:",
        reply_markup=reply_markup
    )

async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("1️⃣", callback_data="comprobante1")],
        [InlineKeyboardButton("2️⃣", callback_data="comprobante2")],
        [InlineKeyboardButton("3️⃣", callback_data="comprobante3")],
        [InlineKeyboardButton("4️⃣", callback_data="comprobante4")],
        [InlineKeyboardButton("5️⃣", callback_data="comprobante5")],
        [InlineKeyboardButton("📌", callback_data="movimientos")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🍀 Selecciona el comprobante que deseas generar:",
        reply_markup=reply_markup
    )

# Mensajes informativos para otros comprobantes
async def comprobante2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Para Comprobante 2 se realizará un flujo interactivo similar.")
async def comprobante3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Para Comprobante 3 se realizará un flujo interactivo similar.")
async def comprobante4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Para Comprobante 4 se realizará un flujo interactivo que solicitará el número y el valor (se incluirá la fecha).")
async def comprobante5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Para Comprobante 5 se realizará un flujo interactivo similar.")
async def movimientos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Para Movimientos se realizará un flujo interactivo similar.")

# Comando administrativo
async def add_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para usar este comando.")
        return
    try:
        if context.args:
            new_id = int(context.args[0])
            if new_id not in USUARIOS_AUTORIZADOS:
                USUARIOS_AUTORIZADOS.append(new_id)
                save_users(USUARIOS_AUTORIZADOS)
                await update.message.reply_text(f"✅ Acceso añadido para ID: {new_id}")
            else:
                await update.message.reply_text("ℹ️ El ID ya tiene acceso.")
        else:
            await update.message.reply_text("Por favor proporciona un ID.\nEjemplo: /add 123456789")
    except Exception as e:
        logging.error(f"Error en /add: {e}")
        await update.message.reply_text("Error al procesar el comando.")

async def free_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para usar este comando.")
        return
    global FREE_MODE
    FREE_MODE = True
    await update.message.reply_text("✅ El bot ahora es libre para todos.")

async def close_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para usar este comando.")
        return
    global FREE_MODE
    FREE_MODE = False
    await update.message.reply_text("✅ El bot ahora está restringido a usuarios autorizados.")

# ---------------------------
# MANEJADOR DE BOTONES (CallbackQuery)
# ---------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global FREE_MODE
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "how_to":
        text = (
            "📖 *Cómo usar el bot:*\n\n"
            "• Usa el comando /cmds para ver los comprobantes disponibles.\n"
            "• Selecciona el comprobante deseado y sigue las instrucciones.\n"
            "• Cada comprobante se creará de forma interactiva, preguntándote cada dato."
        )
        await query.edit_message_text(text=text, parse_mode="Markdown")
    elif data == "creator":
        text = "👤 *Creador:*\n\nEste bot fue creado por [tu nombre]."
        await query.edit_message_text(text=text, parse_mode="Markdown")
    elif data == "admins":
        user_id = query.from_user.id
        if user_id != ADMIN_ID:
            await query.edit_message_text(text="❌ Acceso denegado. No eres admin.")
        else:
            keyboard = [
                [InlineKeyboardButton("🔓 Modo Libre", callback_data="admin_free")],
                [InlineKeyboardButton("🔒 Modo Restringido", callback_data="admin_close")],
                [InlineKeyboardButton("➕ Agregar Usuario", callback_data="admin_add")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = (
                "⚙️ *Panel de Administración:*\n\n"
                "Usa los botones para cambiar el modo del bot o para ver cómo agregar un nuevo usuario.\n"
                "Para agregar un usuario, utiliza el comando:\n`/add <ID>`"
            )
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)
    elif data in conversation_fields.keys():
        # Inicia la conversación interactiva para el comprobante seleccionado
        context.user_data["current_comprobante"] = data
        context.user_data["step"] = 0
        title = comprobante_titles.get(data, data)
        prompt = conversation_fields[data][0][1]
        await query.edit_message_text(text=f"✍️ *{title}*\n\n{prompt}", parse_mode="Markdown")
    elif data == "admin_free":
        if query.from_user.id != ADMIN_ID:
            await query.edit_message_text(text="❌ Acceso denegado. No eres admin.")
        else:
            FREE_MODE = True
            await query.edit_message_text(text="✅ Modo libre activado.")
    elif data == "admin_close":
        if query.from_user.id != ADMIN_ID:
            await query.edit_message_text(text="❌ Acceso denegado. No eres admin.")
        else:
            FREE_MODE = False
            await query.edit_message_text(text="✅ Modo restringido activado.")
    elif data == "admin_add":
        if query.from_user.id != ADMIN_ID:
            await query.edit_message_text(text="❌ Acceso denegado. No eres admin.")
        else:
            text = (
                "Para agregar un usuario, utiliza el comando:\n"
                "`/add <ID>`\n\n"
                "Ejemplo:\n`/add 123456789`"
            )
            await query.edit_message_text(text=text, parse_mode="Markdown")

# ---------------------------
# MANEJADOR DE LA CONVERSACIÓN INTERACTIVA
# ---------------------------
             

# ---------------------------
# MANEJADOR DE LA CONVERSACIÓN INTERACTIVA
# ---------------------------
async def handle_comprobante_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "current_comprobante" not in context.user_data:
        return

    comp = context.user_data["current_comprobante"]
    steps = conversation_fields.get(comp)
    step_index = context.user_data.get("step", 0)
    current_field = steps[step_index][0]
    text = update.message.text.strip()

    # Validación para campos numéricos
    if current_field == "phone":
        if not text.replace(" ", "").isdigit():
            await update.message.reply_text("⚠️ El número debe ser numérico. Intente de nuevo:")
            return
    if current_field in ("value", "cc"):
        if not text.isdigit():
            await update.message.reply_text(f"⚠️ El campo {current_field} debe ser numérico. Intente de nuevo:")
            return

    context.user_data[current_field] = text
    step_index += 1
    context.user_data["step"] = step_index

    if step_index < len(steps):
        next_prompt = steps[step_index][1]
        await update.message.reply_text(next_prompt)
    else:
        try:
            if comp == "comprobante1":
                name = context.user_data["name"]
                phone = context.user_data["phone"]
                value = int(context.user_data["value"])
                # Se usa un ajuste fijo para desplazar el texto más a la izquierda (por ejemplo, -200)
                config = COMPROBANTES[comp]
                comprobante_path = generar_comprobante(name, phone, value, config, ajuste_x=-200)
            elif comp in ("comprobante2", "comprobante3"):
                name = context.user_data["name"]
                phone = context.user_data["phone"]
                value = int(context.user_data["value"])
                config = COMPROBANTES[comp]
                comprobante_path = generar_comprobante(name, phone, value, config, ajuste_x=-140)
            elif comp == "comprobante4":
                phone = context.user_data["phone"]
                value = int(context.user_data["value"])
                config = COMPROBANTES["comprobante4"]
                # Se usa un ajuste fijo para desplazar un poquito a la derecha (por ejemplo, -100)
                comprobante_path = generar_comprobante("", phone, value, config, ajuste_x=-100)
            elif comp == "comprobante5":
                name = context.user_data["name"]
                phone = context.user_data["phone"]
                value = int(context.user_data["value"])
                cc = context.user_data["cc"]
                config = COMPROBANTES["comprobante5"]
                comprobante_path = generar_comprobante(name, phone, value, config, ajuste_x=-140, cc=cc)
            elif comp == "movimientos":
                name = context.user_data["name"]
                value = int(context.user_data["value"])
                config = COMPROBANTES["movimientos"]
                comprobante_path = generar_comprobante(name, "", value, config)
            else:
                await update.message.reply_text("❌ Comprobante no reconocido.")
                return

            with open(comprobante_path, "rb") as comprobante_file:
                await update.message.reply_photo(photo=comprobante_file, caption="✅ Se creó el comprobante correctamente.")
        except Exception as e:
            logging.error(f"Error al generar comprobante: {e}")
            await update.message.reply_text("❌ Error al generar el comprobante.")
        for key in ("current_comprobante", "step", "name", "phone", "value", "ajuste_x", "cc"):
            context.user_data.pop(key, None)

# ---------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------
def main() -> None:
    TOKEN = "8189575388:AAHvLEjJwlKx53yhGVywPKpRDPd_80Qwmp0"  # Reemplaza con tu token real
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cmds", cmds))
    application.add_handler(CommandHandler("comprobante2", comprobante2))
    application.add_handler(CommandHandler("comprobante3", comprobante3))
    application.add_handler(CommandHandler("comprobante4", comprobante4))
    application.add_handler(CommandHandler("comprobante5", comprobante5))
    application.add_handler(CommandHandler("movimientos", movimientos))
    application.add_handler(CommandHandler("add", add_access))
    application.add_handler(CommandHandler("free", free_mode_cmd))
    application.add_handler(CommandHandler("close", close_mode_cmd))

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comprobante_input))

    application.run_polling()

if __name__ == "__main__":
    main()
    