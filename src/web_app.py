import logging
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from bot_manager import BotManager
import yaml
from pathlib import Path
from typing import Optional, Tuple, Union

CONFIG_PATH = Path("config.yaml")
DEFAULT_CONFIG = {
    'url': 'https://aprender2teste.unb.br/my/',
    'questions_file': 'questions.txt',
    'interval_seconds': 3.0,
    'jitter': 0.5,
    'restart_delay': 10.0,
    'headless': False,
    'wait_for_manual_login': True,
    'manual_login_wait_seconds': 120,
    'capture_responses': True,
    'log_dir': 'logs',
    'messages_csv': 'messages.csv',
    'port': 5000,
    'selectors': {
        'iframe_id': 'tool_content',
        'input_tag': 'textarea'
    },
    'ssl': {
        'enabled': False,
        'mode': 'adhoc',  # adhoc | cert
        'cert': '',
        'key': ''
    }
}

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger("web")

app = Flask(__name__)
CORS(app)


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                cfg = {**DEFAULT_CONFIG, **data}
                return cfg
        except Exception as e:
            logger.error(f"Failed to load config.yaml: {e}")
    return DEFAULT_CONFIG

cfg = load_config()
API_KEY = cfg.get('api_key') or None
manager = BotManager(
    url=cfg['url'],
    questions_file=cfg['questions_file'],
    interval_seconds=cfg['interval_seconds'],
                ssl_data = data.get('ssl') or {}
                cfg['ssl'] = {**DEFAULT_CONFIG['ssl'], **ssl_data}
    jitter=cfg['jitter'],
    restart_delay=cfg['restart_delay'],
    headless=cfg.get('headless', False),
    wait_for_manual_login=cfg.get('wait_for_manual_login', True),
    manual_login_wait_seconds=cfg.get('manual_login_wait_seconds', 120),
    capture_responses=cfg.get('capture_responses', True),
    log_dir=cfg.get('log_dir', 'logs'),
SSL_CONTEXT = None


def resolve_ssl_context(ssl_cfg: Optional[dict]) -> Optional[Union[str, Tuple[str, str]]]:
    if not isinstance(ssl_cfg, dict):
        return None
    if not ssl_cfg.get('enabled'):
        return None
    mode = (ssl_cfg.get('mode') or 'adhoc').lower()
    if mode == 'adhoc':
        logger.info("SSL habilitado com modo 'adhoc' (certificado autoassinado)")
        return 'adhoc'
    cert, key = ssl_cfg.get('cert'), ssl_cfg.get('key')
    if cert and key:
        logger.info("SSL habilitado com certificado fornecido")
        return (cert, key)
    logger.warning("SSL habilitado mas sem cert/key válidos; caindo para 'adhoc'.")
    return 'adhoc'


SSL_CONTEXT = resolve_ssl_context(cfg.get('ssl'))
    messages_csv=cfg.get('messages_csv', 'messages.csv'),
    selectors=cfg.get('selectors', {})
)

def _check_key():
    if API_KEY:
        provided = request.headers.get('X-API-KEY') or request.args.get('api_key')
        if provided != API_KEY:
            abort(401)

@app.get('/api/status')
def status():
    _check_key()
    return jsonify(manager.status())

@app.post('/api/start')
def start():
    _check_key()
    if manager.start():
        return jsonify({"ok": True, "status": manager.status()})
    return jsonify({"ok": False, "error": "Already running"}), 400

@app.post('/api/stop')
def stop():
    _check_key()
    manager.stop()
    return jsonify({"ok": True, "status": manager.status()})

@app.post('/api/config')
def update_config():
    _check_key()
    data = request.json or {}
    global cfg
    cfg.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
    if 'ssl' in data:
        cfg['ssl'] = {**DEFAULT_CONFIG['ssl'], **(data.get('ssl') or {})}
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.safe_dump(cfg, f, allow_unicode=True)
    except Exception as e:
        logger.error(f"Failed saving config: {e}")
    global API_KEY, SSL_CONTEXT
    API_KEY = cfg.get('api_key') or None
    SSL_CONTEXT = resolve_ssl_context(cfg.get('ssl'))
    manager.interval_seconds = cfg['interval_seconds']
    manager.jitter = cfg['jitter']
    return jsonify({"ok": True, "config": cfg})

@app.get('/')
def root():
    public = {k: v for k, v in cfg.items() if k not in ('api_key',)}
    return jsonify({
        "message": "Darcy Stress Bot Control API",
        "secured": bool(API_KEY),
        "config": public,
        "endpoints": [
            "/api/status",
            "/api/metrics",
            "/api/start",
            "/api/stop",
            "/api/config"
        ]
    })

@app.get('/api/metrics')
def metrics():
    _check_key()
    return jsonify(manager.metrics())

if __name__ == '__main__':
    if cfg.get('autostart'):
        logger.info("Autostart habilitado - iniciando bot...")
        manager.start()
    port = cfg.get('port', 5000)
    app.run(host='0.0.0.0', port=port, ssl_context=SSL_CONTEXT)
