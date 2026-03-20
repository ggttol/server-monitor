from flask import Flask, render_template_string, jsonify, request
import yaml
import time
import threading

app = Flask(__name__)

_monitor_config = None
_refresh_interval = 30
_last_update = None
_server_data = {}

def load_config(config_path):
    global _monitor_config
    with open(config_path, 'r') as f:
        _monitor_config = yaml.safe_load(f)

def fetch_all_server_data():
    global _server_data, _last_update
    servers_data = []

    if not _monitor_config or 'servers' not in _monitor_config:
        return {'servers': [], 'timestamp': time.time(), 'error': 'No config loaded'}

    from sshsysmon.lib.monitor.server import Server

    for server_name, server_config in _monitor_config['servers'].items():
        try:
            server = Server(server_name, server_config)
            summary = server.getSummary()
            servers_data.append(summary)
        except Exception as e:
            servers_data.append({
                'name': server_name,
                'error': str(e),
                'inspectors': [],
                'errors': [str(e)]
            })

    _server_data = serialize_value({
        'servers': servers_data,
        'timestamp': time.time(),
        'meta': _monitor_config.get('meta', {})
    })
    _last_update = time.time()
    return _server_data

def serialize_value(val):
    if hasattr(val, '__json__'):
        return val.__json__()
    elif hasattr(val, 'bytes'):
        return val.bytes
    elif hasattr(val, '_seconds'):
        return val._seconds
    elif hasattr(val, 'str'):
        return val.str
    elif isinstance(val, (int, float, str, bool, type(None))):
        return val
    elif isinstance(val, dict):
        return {k: serialize_value(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [serialize_value(v) for v in val]
    return str(val)

def background_refresh(interval=30):
    while True:
        time.sleep(interval)
        fetch_all_server_data()

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML,
                                 meta=_monitor_config.get('meta', {}) if _monitor_config else {},
                                 refresh_interval=_refresh_interval)

@app.route('/api/data')
def api_data():
    force = request.args.get('force', 'false').lower() == 'true'
    if force or time.time() - (_last_update or 0) > _refresh_interval:
        return jsonify(fetch_all_server_data())
    return jsonify(_server_data)

@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'ok',
        'uptime': time.time() - (_last_update or time.time()),
        'servers': len(_server_data.get('servers', [])),
        'last_update': _last_update
    })

@app.route('/api/refresh')
def api_refresh():
    return jsonify(fetch_all_server_data())

@app.route('/api/servers', methods=['GET'])
def api_get_servers():
    if not _monitor_config or 'servers' not in _monitor_config:
        return jsonify({'servers': []})
    servers_list = []
    for name, config in _monitor_config.get('servers', {}).items():
        servers_list.append({
            'name': name,
            'host': config.get('config', {}).get('host', ''),
            'port': config.get('config', {}).get('port', 22),
            'username': config.get('config', {}).get('username', '')
        })
    return jsonify({'servers': servers_list})

@app.route('/api/servers', methods=['POST'])
def api_add_server():
    global _monitor_config
    data = request.get_json()

    if not data or not data.get('name') or not data.get('host'):
        return jsonify({'error': 'Name and host are required'}), 400

    new_server = {
        'driver': 'ssh',
        'config': {
            'host': data.get('host'),
            'username': data.get('username', ''),
            'password': data.get('password', ''),
            'port': data.get('port', 22)
        },
        'channels': [{'type': 'stdout'}],
        'monitors': [
            {'type': 'memory'},
            {'type': 'disk'},
            {'type': 'loadavg'},
            {'type': 'system'},
            {'type': 'network', 'config': {'match': 'ens*'}, 'summarize': True}
        ]
    }

    if 'servers' not in _monitor_config:
        _monitor_config['servers'] = {}

    _monitor_config['servers'][data['name']] = new_server
    save_config()
    fetch_all_server_data()

    return jsonify({'success': True, 'message': 'Server added successfully'})

@app.route('/api/servers/<server_name>', methods=['DELETE'])
def api_delete_server(server_name):
    global _monitor_config

    if not _monitor_config or 'servers' not in _monitor_config:
        return jsonify({'error': 'No servers configured'}), 400

    if server_name not in _monitor_config['servers']:
        return jsonify({'error': 'Server not found'}), 404

    del _monitor_config['servers'][server_name]
    save_config()
    fetch_all_server_data()

    return jsonify({'success': True, 'message': 'Server deleted successfully'})

def save_config():
    global _monitor_config
    try:
        config_path = '/Users/gaotao/code/sshsysmon/servers.yml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(_monitor_config, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"Error saving config: {e}")

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ meta.get('title', '实时服务器监控') }}</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }

        [data-theme="dark"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --accent-color: #60a5fa;
            --success-color: #34d399;
            --warning-color: #fbbf24;
            --danger-color: #f87171;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        .header {
            background: linear-gradient(135deg, var(--accent-color) 0%, #8b5cf6 100%);
            color: white;
            padding: 1.5rem 0;
            margin-bottom: 1.5rem;
        }

        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .status-info {
            background: rgba(255,255,255,0.2);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
            animation: pulse 2s infinite;
        }

        .status-dot.online { background: #10b981; }
        .status-dot.offline { background: #ef4444; }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .theme-toggle {
            display: flex;
            gap: 0.25rem;
            background: rgba(255, 255, 255, 0.2);
            padding: 0.25rem;
            border-radius: 9999px;
        }

        .theme-btn {
            padding: 0.4rem 0.8rem;
            border: none;
            background: transparent;
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
            transition: all 0.2s;
        }

        .theme-btn.active {
            background: white;
            color: #1e293b;
        }

        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem 2rem;
        }

        .server-section {
            margin-bottom: 2rem;
        }

        .server-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--border-color);
        }

        .server-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        .server-name {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .server-status {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .last-update {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .status-ok { background: rgba(16, 185, 129, 0.1); color: var(--success-color); }
        .status-warning { background: rgba(245, 158, 11, 0.1); color: var(--warning-color); }
        .status-danger { background: rgba(239, 68, 68, 0.1); color: var(--danger-color); }

        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
        }

        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }

        .card-icon {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
        }

        .icon-memory { background: linear-gradient(135deg, #3b82f6, #60a5fa); }
        .icon-disk { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
        .icon-cpu { background: linear-gradient(135deg, #ef4444, #f87171); }
        .icon-network { background: linear-gradient(135deg, #10b981, #34d399); }

        .card-title {
            font-size: 0.875rem;
            font-weight: 600;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }

        .metric-item {
            text-align: center;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border-radius: 8px;
        }

        .metric-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .metric-label {
            font-size: 0.625rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.25rem;
        }

        .progress-container {
            margin-top: 0.75rem;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            margin-bottom: 0.25rem;
        }

        .progress-bar {
            height: 6px;
            background: var(--bg-secondary);
            border-radius: 3px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }

        .progress-success { background: var(--success-color); }
        .progress-warning { background: var(--warning-color); }
        .progress-danger { background: var(--danger-color); }

        .footer {
            text-align: center;
            padding: 1.5rem;
            color: var(--text-secondary);
            font-size: 0.75rem;
            border-top: 1px solid var(--border-color);
            margin-top: 2rem;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }

        .refresh-btn {
            padding: 0.5rem 1rem;
            border: none;
            background: rgba(255,255,255,0.2);
            color: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }

        .refresh-btn:hover {
            background: rgba(255,255,255,0.3);
        }

        .add-server-btn {
            padding: 0.5rem 1rem;
            border: 2px solid rgba(255,255,255,0.5);
            background: transparent;
            color: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
        }

        .add-server-btn:hover {
            background: rgba(255,255,255,0.2);
            border-color: white;
        }

        .refresh-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        @media (max-width: 768px) {
            .header-content { flex-direction: column; text-align: center; }
            .header-right { width: 100%; justify-content: center; }
            .server-header { flex-wrap: wrap; }
            .server-status { margin-left: 0; width: 100%; justify-content: space-between; }
        }

        /* 模态对话框样式 */
        .modal {
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            backdrop-filter: blur(4px);
        }

        .modal-content {
            background: var(--bg-card);
            margin: 5% auto;
            padding: 0;
            border-radius: 16px;
            width: 90%;
            max-width: 600px;
            max-height: 85vh;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
        }

        .modal-header {
            background: linear-gradient(135deg, var(--accent-color) 0%, #8b5cf6 100%);
            color: white;
            padding: 1.25rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h2 {
            margin: 0;
            font-size: 1.25rem;
        }

        .modal-close {
            font-size: 1.5rem;
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.2s;
        }

        .modal-close:hover {
            opacity: 1;
        }

        .modal-body {
            padding: 1.5rem;
            overflow-y: auto;
            max-height: calc(85vh - 80px);
        }

        .modal-section {
            margin-bottom: 1.5rem;
        }

        .modal-section h3 {
            font-size: 1rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border-color);
        }

        .form-group {
            margin-bottom: 1rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            font-size: 0.875rem;
            color: var(--text-primary);
        }

        .form-group input {
            width: 100%;
            padding: 0.625rem 0.875rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.875rem;
            background: var(--bg-secondary);
            color: var(--text-primary);
            transition: border-color 0.2s;
        }

        .form-group input:focus {
            outline: none;
            border-color: var(--accent-color);
        }

        .btn {
            padding: 0.625rem 1.25rem;
            border: none;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-color) 0%, #8b5cf6 100%);
            color: white;
            width: 100%;
        }

        .btn-primary:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        .btn-danger {
            background: var(--danger-color);
            color: white;
            padding: 0.375rem 0.75rem;
            font-size: 0.75rem;
        }

        .btn-danger:hover {
            opacity: 0.8;
        }

        .server-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .server-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.875rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            border-left: 4px solid var(--accent-color);
        }

        .server-info {
            flex: 1;
        }

        .server-name-display {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .server-details {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .loading {
            text-align: center;
            padding: 1rem;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1>📊 {{ meta.get('title', '实时服务器监控') }}</h1>
            <div class="header-right">
                <div class="status-info">
                    <span class="status-dot online" id="statusDot"></span>
                    <span id="statusText">正在连接...</span>
                </div>
                <button class="refresh-btn" onclick="manualRefresh()" id="refreshBtn">🔄 刷新</button>
                <button class="add-server-btn" onclick="openServerModal()">➕ 添加服务器</button>
                <div class="theme-toggle">
                    <button class="theme-btn active" onclick="setTheme('light')" id="lightBtn">☀️</button>
                    <button class="theme-btn" onclick="setTheme('dark')" id="darkBtn">🌙</button>
                </div>
            </div>
        </div>
    </header>

    <main class="main-content" id="mainContent">
        <div class="loading">正在加载监控数据...</div>
    </main>

    <!-- 添加/删除服务器模态对话框 -->
    <div id="serverModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h2>🖥️ 服务器管理</h2>
                <span class="modal-close" onclick="closeServerModal()">&times;</span>
            </div>
            <div class="modal-body">
                <!-- 添加新服务器 -->
                <div class="modal-section">
                    <h3>➕ 添加新服务器</h3>
                    <form id="addServerForm" onsubmit="addServer(event)">
                        <div class="form-group">
                            <label>服务器名称 *</label>
                            <input type="text" id="serverName" placeholder="例如：Web服务器" required>
                        </div>
                        <div class="form-group">
                            <label>主机地址 *</label>
                            <input type="text" id="serverHost" placeholder="例如：192.168.1.100" required>
                        </div>
                        <div class="form-group">
                            <label>SSH端口</label>
                            <input type="number" id="serverPort" value="22" placeholder="22">
                        </div>
                        <div class="form-group">
                            <label>SSH用户名</label>
                            <input type="text" id="serverUsername" placeholder="用户名">
                        </div>
                        <div class="form-group">
                            <label>SSH密码</label>
                            <input type="password" id="serverPassword" placeholder="密码">
                        </div>
                        <button type="submit" class="btn btn-primary">✅ 添加服务器</button>
                    </form>
                </div>

                <!-- 服务器列表 -->
                <div class="modal-section">
                    <h3>📋 服务器列表</h3>
                    <div id="serverList" class="server-list">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="footer">
        <p>自动刷新间隔: {{ refresh_interval }}秒</p>
        <p id="lastUpdateTime"></p>
    </footer>

    <script>
        let autoRefreshInterval = {{ refresh_interval }};
        let lastUpdate = null;
        let charts = {};

        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('dashboard-theme', theme);
            if (theme === 'dark') {
                document.getElementById('darkBtn').classList.add('active');
                document.getElementById('lightBtn').classList.remove('active');
            } else {
                document.getElementById('lightBtn').classList.add('active');
                document.getElementById('darkBtn').classList.remove('active');
            }
        }

        function updateStatus(status, text) {
            const dot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            dot.className = 'status-dot ' + status;
            statusText.textContent = text;
        }

        function formatBytes(bytes) {
            if (typeof bytes === 'number') {
                const gb = bytes / (1024 * 1024 * 1024);
                if (gb >= 1) return gb.toFixed(1) + ' GB';
                const mb = bytes / (1024 * 1024);
                return mb.toFixed(0) + ' MB';
            }
            return bytes;
        }

        function formatUptime(seconds) {
            if (typeof seconds !== 'number' || seconds <= 0) return 'N/A';
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const parts = [];
            if (days > 0) parts.push(days + '天');
            if (hours > 0) parts.push(hours + '小时');
            if (minutes > 0) parts.push(minutes + '分');
            if (parts.length === 0) parts.push(Math.floor(seconds) + '秒');
            return parts.join(' ');
        }

        function renderDashboard(data) {
            const container = document.getElementById('mainContent');
            let html = '';

            data.servers.forEach(server => {
                if (server.error) {
                    html += `
                        <section class="server-section">
                            <div class="server-header">
                                <div class="server-icon">⚠️</div>
                                <h2 class="server-name">${server.name}</h2>
                                <div class="server-status">
                                    <span class="status-badge status-danger">连接失败</span>
                                </div>
                            </div>
                            <div class="card">
                                <p style="color: var(--danger-color);">错误: ${server.error}</p>
                            </div>
                        </section>
                    `;
                    return;
                }

                // Find system uptime for server header
                let serverUptime = null;
                server.inspectors.forEach(insp => {
                    if (insp.type === 'system' && insp.metrics && insp.metrics.uptime) {
                        serverUptime = formatUptime(insp.metrics.uptime);
                    }
                });

                html += `
                    <section class="server-section">
                        <div class="server-header">
                            <div class="server-icon">🖥️</div>
                            <h2 class="server-name">${server.name}${serverUptime ? ' <span style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 400;">🕐 ' + serverUptime + '</span>' : ''}</h2>
                            <div class="server-status">
                                <span class="last-update">最后更新: ${new Date(data.timestamp * 1000).toLocaleTimeString()}</span>
                                <span class="status-badge status-ok">✅ 正常</span>
                            </div>
                        </div>
                        <div class="grid-container">
                `;

                server.inspectors.forEach(insp => {
                    if (insp.type === 'memory' && insp.metrics) {
                        html += `
                            <div class="card">
                                <div class="card-header">
                                    <span class="card-icon icon-memory">💾</span>
                                    <span class="card-title">内存</span>
                                </div>
                                <div class="metric-grid">
                                    <div class="metric-item">
                                        <div class="metric-value">${formatBytes(insp.metrics.mem_total)}</div>
                                        <div class="metric-label">总内存</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-value">${formatBytes(insp.metrics.mem_free)}</div>
                                        <div class="metric-label">空闲</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-value">${formatBytes(insp.metrics.cached)}</div>
                                        <div class="metric-label">缓存</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-value">${formatBytes(insp.metrics.swap_free)}</div>
                                        <div class="metric-label">Swap空闲</div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }

                    if (insp.type === 'disk' && insp.metrics) {
                        const percent = insp.metrics.percent_full || 0;
                        const colorClass = percent > 90 ? 'danger' : percent > 70 ? 'warning' : 'success';
                        html += `
                            <div class="card">
                                <div class="card-header">
                                    <span class="card-icon icon-disk">💿</span>
                                    <span class="card-title">磁盘 ${insp.name.replace('Disk Space: ', '')}</span>
                                </div>
                                <div class="metric-grid">
                                    <div class="metric-item">
                                        <div class="metric-value">${formatBytes(insp.metrics.size)}</div>
                                        <div class="metric-label">总容量</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-value">${formatBytes(insp.metrics.available)}</div>
                                        <div class="metric-label">可用</div>
                                    </div>
                                </div>
                                <div class="progress-container">
                                    <div class="progress-header">
                                        <span>使用率</span>
                                        <span>${percent}%</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress-fill progress-${colorClass}" style="width: ${percent}%"></div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }

                    if (insp.type === 'loadavg' && insp.metrics) {
                        html += `
                            <div class="card">
                                <div class="card-header">
                                    <span class="card-icon icon-cpu">⚡</span>
                                    <span class="card-title">CPU负载</span>
                                </div>
                                <div class="metric-grid">
                                    <div class="metric-item">
                                        <div class="metric-value">${insp.metrics.load_1m || 0}</div>
                                        <div class="metric-label">1分钟</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-value">${insp.metrics.load_5m || 0}</div>
                                        <div class="metric-label">5分钟</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-value">${insp.metrics.load_15m || 0}</div>
                                        <div class="metric-label">15分钟</div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }

                    if (insp.type === 'network' && insp.metrics) {
                        const totals = insp.metrics.totals || {};
                        const interfaces = insp.metrics.interfaces || {};

                        let interfaceHtml = '';
                        for (const [name, data] of Object.entries(interfaces)) {
                            interfaceHtml += `
                                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color);">
                                    <div style="font-size: 0.75rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-secondary);">${name}</div>
                                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
                                        <div class="metric-item" style="padding: 0.5rem;">
                                            <div class="metric-value" style="font-size: 0.875rem;">↓ ${formatBytes(data.receive.bytes)}</div>
                                            <div class="metric-label">接收</div>
                                        </div>
                                        <div class="metric-item" style="padding: 0.5rem;">
                                            <div class="metric-value" style="font-size: 0.875rem;">↑ ${formatBytes(data.transmit.bytes)}</div>
                                            <div class="metric-label">发送</div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }

                        html += `
                            <div class="card">
                                <div class="card-header">
                                    <span class="card-icon icon-network">🌐</span>
                                    <span class="card-title">网络流量</span>
                                </div>
                                <div class="metric-grid">
                                    <div class="metric-item">
                                        <div class="metric-value" style="font-size: 1rem;">↓ ${formatBytes(totals.received)}</div>
                                        <div class="metric-label">总接收</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-value" style="font-size: 1rem;">↑ ${formatBytes(totals.transmitted)}</div>
                                        <div class="metric-label">总发送</div>
                                    </div>
                                </div>
                                ${interfaceHtml}
                            </div>
                        `;
                    }
                });

                html += '</div></section>';
            });

            container.innerHTML = html;
            lastUpdate = data.timestamp;
            updateStatus('online', `已连接 | ${data.servers.length}台服务器`);
        }

        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();
                renderDashboard(data);
                document.getElementById('lastUpdateTime').textContent =
                    `数据更新时间: ${new Date(data.timestamp * 1000).toLocaleString()}`;
            } catch (error) {
                console.error('Error fetching data:', error);
                updateStatus('offline', '连接失败');
            }
        }

        function manualRefresh() {
            const btn = document.getElementById('refreshBtn');
            btn.disabled = true;
            btn.textContent = '🔄 刷新中...';
            fetchData().then(() => {
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = '🔄 刷新';
                }, 500);
            });
        }

        // 模态对话框函数
        function openServerModal() {
            const modal = document.getElementById('serverModal');
            modal.style.display = 'block';
            loadServerList();
        }

        function closeServerModal() {
            const modal = document.getElementById('serverModal');
            modal.style.display = 'none';
        }

        // 点击模态对话框外部关闭
        window.onclick = function(event) {
            const modal = document.getElementById('serverModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }

        // 加载服务器列表
        async function loadServerList() {
            try {
                const response = await fetch('/api/servers');
                const data = await response.json();
                const container = document.getElementById('serverList');

                if (data.servers.length === 0) {
                    container.innerHTML = '<div class="loading">暂无服务器</div>';
                    return;
                }

                container.innerHTML = data.servers.map(server => `
                    <div class="server-item">
                        <div class="server-info">
                            <div class="server-name-display">${server.name}</div>
                            <div class="server-details">${server.host}:${server.port} | ${server.username}</div>
                        </div>
                        <button class="btn btn-danger" onclick="deleteServer('${server.name}')">🗑️ 删除</button>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading server list:', error);
                document.getElementById('serverList').innerHTML = '<div class="loading">加载失败</div>';
            }
        }

        // 添加服务器
        async function addServer(event) {
            event.preventDefault();

            const name = document.getElementById('serverName').value;
            const host = document.getElementById('serverHost').value;
            const port = document.getElementById('serverPort').value || 22;
            const username = document.getElementById('serverUsername').value;
            const password = document.getElementById('serverPassword').value;

            try {
                const response = await fetch('/api/servers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, host, port: parseInt(port), username, password })
                });

                const result = await response.json();

                if (result.success) {
                    alert('✅ 服务器添加成功！');
                    document.getElementById('addServerForm').reset();
                    loadServerList();
                    manualRefresh();
                } else {
                    alert('❌ 添加失败: ' + result.error);
                }
            } catch (error) {
                console.error('Error adding server:', error);
                alert('❌ 添加失败: ' + error.message);
            }
        }

        // 删除服务器
        async function deleteServer(serverName) {
            if (!confirm('确定要删除服务器 "' + serverName + '" 吗？')) {
                return;
            }

            try {
                const response = await fetch('/api/servers/' + encodeURIComponent(serverName), {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (result.success) {
                    alert('✅ 服务器删除成功！');
                    loadServerList();
                    manualRefresh();
                } else {
                    alert('❌ 删除失败: ' + result.error);
                }
            } catch (error) {
                console.error('Error deleting server:', error);
                alert('❌ 删除失败: ' + error.message);
            }
        }

        // Initialize
        const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
        setTheme(savedTheme);
        fetchData();
        setInterval(fetchData, autoRefreshInterval * 1000);
    </script>
</body>
</html>
'''

def start_server(host='0.0.0.0', port=5000, config_path=None, refresh_interval=30):
    global _refresh_interval

    _refresh_interval = refresh_interval

    if config_path:
        load_config(config_path)
        fetch_all_server_data()
        thread = threading.Thread(target=background_refresh, args=(refresh_interval,))
        thread.daemon = True
        thread.start()

    print(f"""
🚀 服务器监控系统启动中...

📊 监控面板: http://localhost:{port}
🔄 自动刷新: 每 {refresh_interval} 秒

按 Ctrl+C 停止服务器
""")

    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    start_server()
