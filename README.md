# 🤖 Chatbot Vendedor IA

Bot de ventas inteligente con Claude AI para Facebook Marketplace, WhatsApp e Instagram.
Responde como tú, recuerda a todos tus clientes, aprende con cada conversación.

---

## ⚡ Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar (crea .env, inicializa base de datos)
python setup.py

# 3. Editar .env con tus tokens reales
# (ver sección Configuración más abajo)

# 4. Editar archivos de conocimiento (tu negocio)
# knowledge/products.json   → tus productos
# knowledge/faqs.json       → preguntas frecuentes
# knowledge/policies.json   → info del negocio
# knowledge/style_examples.json → cómo respondes tú

# 5. Arrancar el bot
python main.py
```

---

## 📁 Estructura del Proyecto

```
chatbot/
├── main.py                     # Punto de entrada
├── setup.py                    # Configuración inicial (correr una vez)
├── requirements.txt
├── .env                        # Tokens secretos (NO subir a git)
│
├── config/
│   └── settings.py             # Todas las variables de entorno
│
├── knowledge/                  # 🧠 AQUÍ CONFIGURAS TU NEGOCIO
│   ├── products.json           # Tus productos y precios
│   ├── faqs.json               # Preguntas frecuentes
│   ├── policies.json           # Políticas y info del negocio
│   └── style_examples.json     # Cómo tú responderías
│
├── core/
│   ├── ai/
│   │   ├── claude_client.py    # Conexión con Claude AI
│   │   ├── prompts.py          # Personalidad del bot
│   │   └── response_engine.py  # Motor principal (orquesta todo)
│   ├── memory/
│   │   ├── knowledge_base.py   # Gestión de conocimiento
│   │   └── customer_profiles.py # Perfiles de clientes
│   └── personality/
│       └── style.py            # Aprende tu estilo
│
├── platforms/
│   ├── base_platform.py        # Clase base
│   ├── facebook/handler.py     # Facebook Messenger + Marketplace
│   ├── whatsapp/handler.py     # WhatsApp Business
│   └── instagram/handler.py    # Instagram DM
│
├── server/
│   ├── app.py                  # Servidor FastAPI
│   └── routes/
│       ├── facebook.py         # Webhook Facebook
│       ├── whatsapp.py         # Webhook WhatsApp
│       ├── instagram.py        # Webhook Instagram
│       └── admin.py            # Panel de administración
│
├── database/
│   ├── models.py               # Estructura de la BD
│   └── manager.py              # Operaciones de BD
│
└── training/
    ├── import_conversations.py # Importar chats pasados
    └── style_trainer.py        # Entrenar el estilo
```

---

## 🔑 Configuración

### 1. Variables de entorno (.env)

Las más importantes:

```env
ANTHROPIC_API_KEY=sk-ant-...        # En console.anthropic.com
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...   # En developers.facebook.com
FACEBOOK_VERIFY_TOKEN=cualquier_texto_secreto
BUSINESS_NAME=El Nombre de Tu Negocio
OWNER_NAME=Tu Nombre
```

### 2. Configurar tu negocio (knowledge/)

**products.json** — Lista todos tus productos:
```json
{
  "products": [
    {
      "name": "iPhone 14 Pro",
      "price": "18500",
      "description": "128GB, Negro, caja original",
      "availability": "disponible"
    }
  ]
}
```

**faqs.json** — Preguntas que siempre te hacen:
```json
{
  "faqs": [
    {
      "question": "¿Hacen envíos?",
      "answer": "Sí, enviamos a todo México por paquetería."
    }
  ]
}
```

**style_examples.json** — Cómo TÚ responderías:
```json
{
  "examples": [
    {
      "customer": "¿Cuánto cuesta?",
      "response": "Hola! $18,500 todo incluido 😊 ¿Te interesa?"
    }
  ]
}
```

---

## 🌐 Conectar con Facebook

1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Crea una app → Messenger → Configuración de webhooks
3. URL del webhook: `https://tu-dominio.com/webhook/facebook`
4. Token de verificación: el mismo que pusiste en `FACEBOOK_VERIFY_TOKEN`
5. Suscríbete a `messages` y `messaging_postbacks`

> **Para pruebas locales:** usa [ngrok](https://ngrok.com) para exponer tu puerto local:
> ```bash
> ngrok http 8000
> # Copia la URL https://xxxx.ngrok.io y úsala como webhook
> ```

---

## 📱 Conectar con WhatsApp

1. En developers.facebook.com → WhatsApp → Configuración
2. URL webhook: `https://tu-dominio.com/webhook/whatsapp`
3. Agrega tu número en la sandbox para pruebas
4. Copia el `WHATSAPP_ACCESS_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID`

---

## 🛠 Panel de Administración

Con el bot corriendo, accede a:

- **Docs interactivas:** http://localhost:8000/docs
- **Estado:** GET http://localhost:8000/admin/status
- **Probar bot:** POST http://localhost:8000/admin/test
  ```json
  {"message": "Hola, ¿tienen el producto X?", "platform": "facebook"}
  ```
- **Ver conocimiento:** GET http://localhost:8000/admin/knowledge
- **Agregar conocimiento:** POST http://localhost:8000/admin/knowledge
- **Corregir respuesta:** POST http://localhost:8000/admin/correct

---

## 📚 Entrenar el Bot

```bash
# Importar conversaciones pasadas de WhatsApp/Facebook
python -m training.import_conversations --conversations mis_chats.json

# Agregar ejemplo de estilo manualmente
python -m training.style_trainer --add-example \
  "¿Tienen el modelo negro?" \
  "Sí! Tenemos negro y gris disponibles 😊 ¿Cuál prefieres?"

# Analizar export de WhatsApp (exporta el chat desde la app)
python -m training.style_trainer --analyze chat_exportado.txt
```

---

## 💡 Tips

- **Actualiza el conocimiento** editando los JSON en `knowledge/` — el bot lo lee automáticamente
- **Después de editar JSONs**, limpia el cache: `DELETE http://localhost:8000/admin/cache`
- **Agrega más ejemplos** a `style_examples.json` para que el bot suene más como tú
- **Monitorea conversaciones** viendo la base de datos en `database/chatbot.db`

---

## 🔒 Seguridad

- **Nunca subas `.env` a git** — ya está en `.gitignore`
- Cambia `SECRET_KEY` en `.env` a algo único y largo
- En producción, usa HTTPS siempre
