# Darcy Chatbot Testing Project

Este projeto foi criado para testar o chatbot Darcy no ambiente de teste da UnB: https://aprender2teste.unb.br/my/

## 🎯 Objetivo

Fornecer ferramentas automatizadas para testar e validar as funcionalidades do chatbot Darcy, incluindo:

- Testes de interface web usando Selenium WebDriver
- Testes de conversação e respostas
- Validação de funcionalidades específicas do ambiente acadêmico
- Relatórios de teste automatizados

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Google Chrome ou Chromium (para testes web)
- ChromeDriver (será baixado automaticamente via webdriver-manager)

## 🚀 Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:
```bash
py -m pip install -r requirements.txt
```

Ou instale as dependências principais manualmente:

```bash
py -m pip install selenium pytest requests webdriver-manager
```

## 📁 Estrutura do Projeto

```
bot-test/
├── src/                    # Código fonte principal
│   ├── __init__.py
│   └── darcy_tester.py    # Classe principal para testes do chatbot
├── tests/                 # Testes automatizados
│   ├── __init__.py
│   └── test_darcy_chatbot.py
├── example_test.py        # Script de exemplo
├── requirements.txt       # Dependências Python
├── pytest.ini           # Configuração do pytest
├── pyproject.toml        # Configuração do projeto
└── README.md            # Este arquivo
```

## 🔧 Como Usar

### Teste Básico Automatizado

Execute o script de exemplo para uma demonstração rápida:

```bash
py example_test.py
```

### Teste Interativo

Para uma sessão interativa onde você pode digitar mensagens:

```bash
py example_test.py interactive
```

### Executar Testes com Pytest

```bash
# Executar todos os testes
py -m pytest tests/ -v

# Executar testes específicos
py -m pytest tests/test_darcy_chatbot.py::TestDarcyChatbot::test_simple_greeting -v

# Executar com relatório HTML
py -m pip install pytest-html  # se ainda não instalado
py -m pytest tests/ -v --html=reports/report.html --self-contained-html
```

## 🤖 Stress Bot (Envio Contínuo)

Agora o projeto inclui um "stress bot" que envia perguntas aleatórias para o chatbot Darcy a cada ~3 segundos (com jitter configurável) de forma contínua. Ele roda localmente e pode ser controlado via:

1. Interface Web (API Flask) em `http://localhost:5000`
2. Página estática (pode ser hospedada no GitHub Pages) que acessa a API local
3. Execução direta em terminal

### Iniciar API Web de Controle

```bash
py -m pip install -r requirements.txt
py src/web_app.py
```

Endpoints expostos:
```
GET  /api/status    -> status atual do loop/bot
GET  /api/metrics   -> métricas agregadas (uptime, msgs/min, etc.)
POST /api/start     -> inicia o loop de envio
POST /api/stop      -> interrompe o loop
POST /api/config    -> altera config dinâmica (interval_seconds, jitter)
```

### Página de Controle (Static / GitHub Pages)

Arquivos: `static_control_page.html` (uso local) e `docs/index.html` (publicado em GitHub Pages).

Funcionalidades principais da página em `docs/index.html`:
* Campo para host + persistência em `localStorage`
* Campo de API Key (se configurada em `config.yaml`)
* Botões: Iniciar, Parar, Atualizar Status, Salvar Config
* Indicador de conectividade (ONLINE/OFFLINE)
* Tabela de Status
* Tabela de Métricas (atualiza a cada 5s) consumindo `/api/metrics`
* Aviso automático se a página (HTTPS) estiver apontando para um host HTTP (mixed content)
* Suporte a query params (`?host=` e `?key=`) para preencher campos automaticamente

Publicação em Pages: basta manter este repositório com a pasta `docs/` na branch principal e habilitar Pages -> Source: `docs/`.

IMPORTANTE: A automação Selenium NÃO roda na página do GitHub Pages. Ela sempre roda localmente onde você executa `py src/web_app.py`. A página apenas envia comandos REST para seu host. Como o Pages roda em HTTPS, exponha a API via HTTPS (veja seção "HTTPS para uso com GitHub Pages") para evitar bloqueio pelo navegador.

### Configuração

Arquivo: `config.yaml` (expandido):
```
url: "https://aprender2teste.unb.br/my/"
questions_file: "questions.txt"
interval_seconds: 3.0        # intervalo base (s)
jitter: 0.5                  # variação aleatória +/-
restart_delay: 10.0          # espera em segundos antes de tentar reiniciar webdriver
port: 5000                   # porta do Flask
headless: false              # executar sem janela? (true/false)
wait_for_manual_login: true  # pausa para login manual antes de iniciar loop
manual_login_wait_seconds: 120
capture_responses: true      # tenta capturar resposta do chatbot
log_dir: "logs"
messages_csv: "messages.csv" # CSV dentro de log_dir
selectors:                   # seletores experimentais
    iframe_id: "tool_content"
    input_tag: "textarea"
    messages_container_css: ".chat-messages, .messages, .conversation"
    message_item_css: ".message, .chat-message"
ssl:                         # HTTPS para acesso via GitHub Pages
    enabled: false
    mode: "adhoc"            # adhoc = certificado autoassinado; cert = usar arquivos
    cert: ""
    key: ""
```

Você pode alterar dinamicamente `interval_seconds` e `jitter` via `/api/config`. Para mudanças em headless ou login manual, reinicie o processo.

### Execução headless (opcional)

Se quiser adaptar para rodar sem abrir a janela do Chrome, ajuste `chatbot_automator.py` para adicionar a opção headless no ChromeOptions.

### Logs

Adicionar (se desejar) ao iniciar o processo:
```bash
py src/web_app.py > bot.log 2>&1
```

### Captura de Respostas

Quando `capture_responses: true`, o bot tenta identificar a última mensagem no container configurado e grava no CSV:

`logs/messages.csv` => colunas: `timestamp_utc,message,response`

Se os seletores não corresponderem ao DOM real, a coluna de resposta ficará vazia. Ajuste os seletores conforme a estrutura real do chatbot.

### Métricas (`/api/metrics`)

Endpoint retorna JSON semelhante a:
```json
{
    "uptime_seconds": 4523.12,
    "last_sent_at": "2024-03-22T15:42:10.123456Z",
    "messages_sent": 1502,
    "errors_count": 3,
    "messages_per_min": 19.9,
    "avg_interval_seconds": 3.01
}
```
Uso prático:
* `uptime_seconds`: tempo desde que o loop iniciou
* `messages_per_min`: taxa efetiva; se cair muito, investigar
* `avg_interval_seconds`: média real incluindo jitter e eventuais esperas
* `errors_count`: quantidade de exceções/reinicializações (para observar estabilidade)

Essas métricas são mostradas automaticamente na página `docs/index.html`.

### HTTPS para uso com GitHub Pages

Quando a página está hospedada em `https://tauanribeiro.github.io/bot-test/`, o navegador bloqueia chamadas para `http://...`. Para evitar isso, execute a API em HTTPS:

1. Ative a opção `ssl.enabled: true` no `config.yaml`.
2. Se quiser algo rápido, mantenha `mode: "adhoc"` (gera certificado autoassinado). Na primeira vez o navegador pedirá para confiar.
3. Para usar um certificado próprio, troque para `mode: "cert"` e preencha os caminhos de `cert` e `key`.
4. (Opcional) Ajuste `port` se preferir outra porta segura (ex.: 5443) e atualize o campo Host na página.

Ao iniciar com HTTPS habilitado:
```bash
py src/web_app.py
```
O log indicará o modo SSL ativo. A página do GitHub Pages deve apontar para `https://SEU_IP:PORTA`.

### Headless

Para rodar sem abrir a janela do Chrome defina `headless: true` em `config.yaml`. (Se o site exigir login que depende de interação, mantenha visível para primeiro login.)

### Uso Programático (darcy_tester clássico)

```python
from src.darcy_tester import DarcyChatbotTester

# Criar instância do testador
with DarcyChatbotTester(headless=True) as tester:
    # Navegar para o chatbot
    tester.navigate_to_chatbot()
    
    # Enviar mensagem
    tester.send_message_to_chatbot("Olá, Darcy!")
    
    # Obter resposta
    response = tester.get_chatbot_response()
    print(f"Resposta: {response}")
    
    # Testar conversação completa
    messages = ["Oi!", "Como posso me matricular?", "Obrigado!"]
    results = tester.test_chatbot_conversation(messages)
    print(f"Sucesso: {results['success']}")
```

## 📊 Tipos de Teste Disponíveis

### 1. Testes de Navegação
- Verificação se o site está acessível
- Validação da página do chatbot

### 2. Testes de Interação Básica
- Envio de mensagens simples
- Verificação de recebimento de respostas
- Testes de saudações e despedidas

### 3. Testes Acadêmicos
- Perguntas sobre matrícula
- Informações sobre bibliotecas
- Consultas sobre horários e sistemas da UnB

### 4. Testes de Funcionalidade
- Comandos de ajuda
- Tratamento de erros
- Mensagens longas ou vazias

### 5. Testes de API (Experimental)
- Descoberta de endpoints
- Testes de conectividade

## ⚙️ Configuração

### Selenium WebDriver

O projeto usa webdriver-manager para baixar automaticamente o ChromeDriver apropriado. Para customizar:

```python
# Executar em modo headless (sem interface gráfica)
tester = DarcyChatbotTester(headless=True)

# Executar com browser visível (útil para debug)
tester = DarcyChatbotTester(headless=False)

# Timeout customizado
tester = DarcyChatbotTester(timeout=20)
```

### Pytest

Configure testes personalizados editando `pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = --verbose --tb=short
markers = 
    slow: testes demorados
    integration: testes de integração
```

## 🐛 Solução de Problemas

### API Flask não responde
* Verifique se está rodando: `py src/web_app.py`
* Porta ocupada? Use outra porta modificando `app.run(..., port=5001)`
* CORS bloqueado? A página inclui `flask-cors` para permitir acesso da página estática.

### Página estática não controla o bot
* Certifique-se que o host configurado aponta para sua máquina: `http://127.0.0.1:5000` ou IP na rede
* Verifique firewall do Windows permitindo acesso à porta 5000

### Chrome fecha sozinho após horas
* O gerenciador reinicia o driver se ocorrer exceção. Veja `bot_manager.py` para lógica de retry.
* Aumente `restart_delay` no `config.yaml` se necessário.

### Quero executar 24/7
* Mantenha o computador ligado, desabilite suspensão automática nas configurações de energia
* Use `py src/web_app.py > bot.log 2>&1` para capturar logs
* Verifique o arquivo de log periodicamente
* Considere criar tarefa agendada do Windows para reiniciar em caso de reboot

### ChromeDriver não encontrado
```bash
py -m pip install webdriver-manager
```

### Selenium não instalado
```bash
py -m pip install selenium
```

### Site não carrega
- Verifique sua conexão com a internet
- Confirme se https://aprender2teste.unb.br/my/ está acessível
- Verifique se não há firewall bloqueando

### Elementos não encontrados
- O chatbot pode ter mudado de interface
- Execute com `headless=False` para ver o que está acontecendo
- Atualize os seletores CSS no arquivo `darcy_tester.py`

## 📝 Tasks do VS Code

O projeto inclui tasks configuradas:

- **Run Example Test**: Executa o exemplo básico
- **Run Darcy Chatbot Tests**: Executa todos os testes com pytest

Acesse via `Ctrl+Shift+P` → "Tasks: Run Task"

## 🔄 Atualizações e Melhorias

Para contribuir com melhorias:

1. Identifique novos seletores do chatbot se a interface mudar
2. Adicione novos casos de teste em `tests/test_darcy_chatbot.py`
3. Melhore os métodos de detecção de resposta em `darcy_tester.py`
4. Adicione suporte para novos tipos de teste

### Ideias Futuras
* Latência detalhada: medir tempo entre envio e resposta (coluna extra no CSV)
* Exportação JSON e endpoint `/api/history` para últimos N envios
* Dashboard com gráficos em tempo real (WebSocket ou SSE)
* Rotação automática de API Key / autenticação baseada em token temporário
* Notificações (ex: Telegram/Email) em caso de quedas frequentes

## 📜 Licença

Este projeto é para fins educacionais e de teste do ambiente acadêmico da UnB.

## 🎓 Sobre o Chatbot Darcy

Darcy é o assistente virtual da Universidade de Brasília, projetado para ajudar estudantes, professores e servidores com informações e serviços acadêmicos.

**Ambiente de Teste**: https://aprender2teste.unb.br/my/
