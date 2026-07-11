#!/bin/bash
set -e

echo "========================================="
echo "  MISIÓN COMPLETA - SETUP SERVIDOR"
echo "========================================="

# --- 1. INSTALAR DEPENDENCIAS BASE ---
echo ""
echo "[1/9] Instalando dependencias del sistema..."
sudo apt-get update -qq
sudo dpkg --configure -a
sudo apt-get install -f -y -qq
sudo apt-get install -y -qq git curl wget build-essential python3-pip python3-venv docker.io jq

# Asegurar que Docker funcione
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# --- 2. INSTALAR NODE.JS (v20 LTS) ---
echo ""
echo "[2/9] Instalando Node.js 20..."
if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d 'v') -lt 20 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y -qq nodejs
fi
echo "Node: $(node -v) | npm: $(npm -v)"

# --- 3. INSTALAR HERRAMIENTAS GLOBALES NPM ---
echo ""
echo "[3/9] Instalando herramientas globales..."
sudo npm install -g @anthropic-ai/claude-flow 2>/dev/null || echo "claude-flow: not available or failed"
sudo npm install -g opencode-ai 2>/dev/null || echo "opencode-ai: not available or failed"
sudo npm install -g @google/gemini-cli 2>/dev/null || echo "gemini-cli: not available or failed"
sudo npm install -g @openai/codex 2>/dev/null || echo "codex: not available or failed"

# --- 4. CLONAR REPOSITORIOS ---
echo ""
echo "[4/9] Preparando estructura de directorios..."

# Si hay repos que clonar desde GitHub, los ponemos aquí
# Por ahora creamos la estructura base
mkdir -p ~/melissa
mkdir -p ~/nova
mkdir -p ~/omnisync
mkdir -p ~/whatsapp-bridge
mkdir -p ~/eco-nova
mkdir -p ~/.n8n

# --- 5. N8N CON DOCKER ---
echo ""
echo "[5/9] Configurando n8n..."
cat > ~/eco-nova/docker-compose.yml << 'DOCKER'
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=3.130.46.55
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://3.130.46.55:5678/
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
    volumes:
      - ~/.n8n:/home/node/.n8n
DOCKER

cd ~/eco-nova
sudo docker compose up -d
echo "n8n levantado en http://3.130.46.55:5678"

# --- 6. WHATSAPP BRIDGE ---
echo ""
echo "[6/9] Preparando WhatsApp Bridge..."
cat > ~/whatsapp-bridge/package.json << 'PKG'
{
  "name": "whatsapp-bridge",
  "version": "1.0.0",
  "description": "WhatsApp Bridge for Melissa",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "whatsapp-web.js": "^1.23.0",
    "express": "^4.18.2",
    "axios": "^1.6.0",
    "qrcode-terminal": "^0.12.0"
  }
}
PKG

cat > ~/whatsapp-bridge/index.js << 'BRIDGE'
const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const axios = require('axios');
const qrcode = require('qrcode-terminal');

const app = express();
app.use(express.json());

const MELISSA_URL = process.env.MELISSA_URL || 'http://3.130.46.55:8000';
const PORT = process.env.PORT || 3001;

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: { headless: true, args: ['--no-sandbox'] }
});

client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    console.log('Scan QR code above to connect WhatsApp');
});

client.on('ready', () => {
    console.log('WhatsApp client ready!');
});

client.on('message', async (msg) => {
    try {
        const response = await axios.post(`${MELISSA_URL}/webhook/whatsapp`, {
            from: msg.from,
            body: msg.body,
            timestamp: msg.timestamp
        });
        if (response.data.reply) {
            await msg.reply(response.data.reply);
        }
    } catch (err) {
        console.error('Error forwarding to Melissa:', err.message);
    }
});

// API endpoint to send messages
app.post('/send', async (req, res) => {
    const { to, message } = req.body;
    try {
        await client.sendMessage(to, message);
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/health', (req, res) => res.json({ status: 'ok' }));

client.initialize();
app.listen(PORT, () => console.log(`WhatsApp Bridge API on port ${PORT}`));
BRIDGE

cd ~/whatsapp-bridge
npm install 2>/dev/null || echo "npm install pending (needs network)"

# --- 7. MELISSA BASE ---
echo ""
echo "[7/9] Preparando Melissa..."
cat > ~/melissa/requirements.txt << 'REQ'
fastapi>=0.104.0
uvicorn>=0.24.0
python-dotenv>=1.0.0
httpx>=0.25.0
pydantic>=2.5.0
openai>=1.6.0
anthropic>=0.40.0
sqlalchemy>=2.0.0
alembic>=1.13.0
redis>=5.0.0
celery>=5.3.0
websockets>=12.0
python-multipart>=0.0.6
jinja2>=3.1.0
REQ

cat > ~/melissa/.env << 'ENV'
# Melissa Configuration
HOST=0.0.0.0
PORT=8000
SERVER_IP=3.130.46.55
N8N_URL=http://3.130.46.55:5678
WHATSAPP_BRIDGE_URL=http://3.130.46.55:3001
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
DATABASE_URL=sqlite:///./melissa.db
ENV

pip3 install -r ~/melissa/requirements.txt --break-system-packages 2>/dev/null || echo "pip install: some packages may need venv"

# --- 8. OMNISYNC ---
echo ""
echo "[8/9] Preparando OmniSync..."
cat > ~/omnisync/package.json << 'PKG'
{
  "name": "omnisync",
  "version": "1.0.0",
  "description": "OmniSync - Migration & Sync Control Plane",
  "main": "index.js",
  "bin": {
    "omni": "./index.js"
  },
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "commander": "^11.1.0",
    "chalk": "^5.3.0",
    "ora": "^7.0.1"
  }
}
PKG

cd ~/omnisync
npm install 2>/dev/null || echo "omnisync npm install pending"
sudo npm link 2>/dev/null || echo "omnisync link pending"

# --- 9. VERIFICACIÓN FINAL ---
echo ""
echo "========================================="
echo "  VERIFICACIÓN FINAL"
echo "========================================="
echo ""
echo "Node.js:     $(node -v 2>/dev/null || echo 'NOT INSTALLED')"
echo "npm:         $(npm -v 2>/dev/null || echo 'NOT INSTALLED')"
echo "Python:      $(python3 --version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Docker:      $(docker --version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Git:         $(git --version 2>/dev/null || echo 'NOT INSTALLED')"
echo ""
echo "--- Servicios ---"
echo "n8n:         $(sudo docker ps --filter name=n8n --format '{{.Status}}' 2>/dev/null || echo 'NOT RUNNING')"
echo ""
echo "--- Directorios ---"
ls -la ~/melissa/ 2>/dev/null && echo "✓ melissa OK" || echo "✗ melissa MISSING"
ls -la ~/omnisync/ 2>/dev/null && echo "✓ omnisync OK" || echo "✗ omnisync MISSING"
ls -la ~/whatsapp-bridge/ 2>/dev/null && echo "✓ whatsapp-bridge OK" || echo "✗ whatsapp-bridge MISSING"
ls -la ~/eco-nova/ 2>/dev/null && echo "✓ eco-nova OK" || echo "✗ eco-nova MISSING"
echo ""
echo "--- NPM Global ---"
npm list -g --depth=0 2>/dev/null
echo ""
echo "--- PENDIENTE MANUAL ---"
echo "1. Agregar API keys reales en ~/melissa/.env"
echo "2. Conectar WhatsApp (escanear QR): cd ~/whatsapp-bridge && npm start"
echo "3. Cambiar password de n8n en ~/eco-nova/docker-compose.yml"
echo "4. Si tienes repos en GitHub, clonarlos a ~/melissa y ~/omnisync"
echo "5. Reiniciar claude code para que Bash tool funcione"
echo ""
echo "IP configurada: 3.130.46.55"
echo "n8n: http://3.130.46.55:5678"
echo "========================================="
echo "  MISIÓN COMPLETADA"
echo "========================================="
