{{!-- Modern Dashboard Template with Light/Dark Theme Support --}}
<!DOCTYPE html>
<html data-theme="light">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>{{coalesce meta.title 'Server Monitoring Dashboard'}}</title>

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
			--accent-hover: #2563eb;
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
			--accent-hover: #3b82f6;
			--success-color: #34d399;
			--warning-color: #fbbf24;
			--danger-color: #f87171;
			--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
			--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4);
			--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5);
		}

		* {
			margin: 0;
			padding: 0;
			box-sizing: border-box;
		}

		body {
			font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
			background-color: var(--bg-primary);
			color: var(--text-primary);
			line-height: 1.6;
			transition: background-color 0.3s ease, color 0.3s ease;
		}

		.dashboard-container {
			min-height: 100vh;
		}

		.header {
			background: linear-gradient(135deg, var(--accent-color) 0%, #8b5cf6 100%);
			color: white;
			padding: 2rem 0;
			margin-bottom: 2rem;
			box-shadow: var(--shadow-lg);
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
			font-size: 1.875rem;
			font-weight: 700;
			display: flex;
			align-items: center;
			gap: 0.75rem;
		}

		.theme-toggle {
			display: flex;
			gap: 0.5rem;
			background: rgba(255, 255, 255, 0.2);
			padding: 0.25rem;
			border-radius: 9999px;
			backdrop-filter: blur(10px);
		}

		.theme-btn {
			padding: 0.5rem 1rem;
			border: none;
			background: transparent;
			color: rgba(255, 255, 255, 0.7);
			cursor: pointer;
			border-radius: 9999px;
			font-size: 0.875rem;
			font-weight: 500;
			transition: all 0.2s;
		}

		.theme-btn.active {
			background: white;
			color: #1e293b;
		}

		.theme-btn:hover {
			background: rgba(255, 255, 255, 0.3);
		}

		.main-content {
			max-width: 1400px;
			margin: 0 auto;
			padding: 0 2rem 2rem;
		}

		.server-section {
			margin-bottom: 3rem;
		}

		.server-header {
			display: flex;
			align-items: center;
			gap: 1rem;
			margin-bottom: 1.5rem;
			padding-bottom: 1rem;
			border-bottom: 2px solid var(--border-color);
		}

		.server-icon {
			width: 48px;
			height: 48px;
			background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
			border-radius: 12px;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 1.5rem;
		}

		.server-name {
			font-size: 1.5rem;
			font-weight: 600;
		}

		.server-status {
			display: flex;
			gap: 0.5rem;
			margin-left: auto;
		}

		.status-badge {
			padding: 0.25rem 0.75rem;
			border-radius: 9999px;
			font-size: 0.75rem;
			font-weight: 600;
		}

		.status-ok {
			background: rgba(16, 185, 129, 0.1);
			color: var(--success-color);
		}

		.status-warning {
			background: rgba(245, 158, 11, 0.1);
			color: var(--warning-color);
		}

		.status-danger {
			background: rgba(239, 68, 68, 0.1);
			color: var(--danger-color);
		}

		.grid-container {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
			gap: 1.5rem;
		}

		.card {
			background: var(--bg-card);
			border-radius: 16px;
			padding: 1.5rem;
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
			justify-content: space-between;
			margin-bottom: 1rem;
			padding-bottom: 1rem;
			border-bottom: 1px solid var(--border-color);
		}

		.card-title {
			font-size: 1rem;
			font-weight: 600;
			display: flex;
			align-items: center;
			gap: 0.5rem;
		}

		.card-title .icon {
			width: 32px;
			height: 32px;
			border-radius: 8px;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 1rem;
		}

		.icon-memory {
			background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
		}

		.icon-disk {
			background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
		}

		.icon-cpu {
			background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
		}

		.icon-network {
			background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
		}

		.icon-port {
			background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
		}

		.icon-system {
			background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
		}

		.metric-grid {
			display: grid;
			grid-template-columns: repeat(2, 1fr);
			gap: 1rem;
		}

		.metric-item {
			text-align: center;
			padding: 1rem;
			background: var(--bg-secondary);
			border-radius: 12px;
		}

		.metric-value {
			font-size: 1.5rem;
			font-weight: 700;
			color: var(--text-primary);
			margin-bottom: 0.25rem;
		}

		.metric-label {
			font-size: 0.75rem;
			color: var(--text-secondary);
			text-transform: uppercase;
			letter-spacing: 0.05em;
		}

		.progress-bar-container {
			margin-top: 1rem;
		}

		.progress-header {
			display: flex;
			justify-content: space-between;
			margin-bottom: 0.5rem;
			font-size: 0.875rem;
		}

		.progress-bar {
			height: 8px;
			background: var(--bg-secondary);
			border-radius: 4px;
			overflow: hidden;
		}

		.progress-fill {
			height: 100%;
			border-radius: 4px;
			transition: width 0.5s ease;
		}

		.progress-success {
			background: linear-gradient(90deg, var(--success-color), #34d399);
		}

		.progress-warning {
			background: linear-gradient(90deg, var(--warning-color), #fbbf24);
		}

		.progress-danger {
			background: linear-gradient(90deg, var(--danger-color), #f87171);
		}

		.chart-container {
			position: relative;
			height: 200px;
			margin-top: 1rem;
		}

		.alarm-list {
			display: flex;
			flex-direction: column;
			gap: 0.75rem;
		}

		.alarm-item {
			display: flex;
			align-items: center;
			justify-content: space-between;
			padding: 0.75rem;
			background: var(--bg-secondary);
			border-radius: 8px;
			border-left: 4px solid;
		}

		.alarm-item.ok {
			border-left-color: var(--success-color);
		}

		.alarm-item.warning {
			border-left-color: var(--warning-color);
		}

		.alarm-item.danger {
			border-left-color: var(--danger-color);
		}

		.alarm-name {
			font-weight: 500;
			font-size: 0.875rem;
		}

		.alarm-status {
			display: flex;
			align-items: center;
			gap: 0.5rem;
		}

		.alarm-badge {
			width: 24px;
			height: 24px;
			border-radius: 50%;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 0.75rem;
		}

		.alarm-badge.ok {
			background: rgba(16, 185, 129, 0.1);
			color: var(--success-color);
		}

		.alarm-badge.danger {
			background: rgba(239, 68, 68, 0.1);
			color: var(--danger-color);
		}

		.port-grid {
			display: grid;
			grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
			gap: 0.75rem;
		}

		.port-item {
			padding: 0.75rem;
			background: var(--bg-secondary);
			border-radius: 8px;
			text-align: center;
		}

		.port-number {
			font-weight: 700;
			font-size: 1.25rem;
			margin-bottom: 0.25rem;
		}

		.port-status {
			font-size: 0.75rem;
			padding: 0.25rem 0.5rem;
			border-radius: 9999px;
		}

		.port-open {
			background: rgba(16, 185, 129, 0.1);
			color: var(--success-color);
		}

		.port-closed {
			background: rgba(239, 68, 68, 0.1);
			color: var(--danger-color);
		}

		.network-list {
			display: flex;
			flex-direction: column;
			gap: 0.75rem;
		}

		.network-item {
			padding: 0.75rem;
			background: var(--bg-secondary);
			border-radius: 8px;
		}

		.network-header {
			font-weight: 600;
			margin-bottom: 0.5rem;
			display: flex;
			align-items: center;
			gap: 0.5rem;
		}

		.network-stats {
			display: grid;
			grid-template-columns: repeat(2, 1fr);
			gap: 0.5rem;
			font-size: 0.875rem;
		}

		.network-stat {
			display: flex;
			justify-content: space-between;
			color: var(--text-secondary);
		}

		.network-stat span:last-child {
			font-weight: 600;
			color: var(--text-primary);
		}

		.footer {
			text-align: center;
			padding: 2rem;
			color: var(--text-secondary);
			font-size: 0.875rem;
			border-top: 1px solid var(--border-color);
			margin-top: 3rem;
		}

		@media (max-width: 768px) {
			.header-content {
				flex-direction: column;
				gap: 1rem;
				text-align: center;
			}

			.server-header {
				flex-direction: column;
				text-align: center;
			}

			.server-status {
				margin-left: 0;
				margin-top: 1rem;
			}

			.grid-container {
				grid-template-columns: 1fr;
			}
		}
	</style>
</head>
<body>
	<div class="dashboard-container">
		<header class="header">
			<div class="header-content">
				<h1>
					<span>📊</span>
					{{coalesce meta.title 'Server Monitoring Dashboard'}}
				</h1>
				<div class="theme-toggle">
					<button class="theme-btn active" onclick="setTheme('light')" id="light-btn">
						☀️ 亮色
					</button>
					<button class="theme-btn" onclick="setTheme('dark')" id="dark-btn">
						🌙 暗色
					</button>
				</div>
			</div>
		</header>

		<main class="main-content">
			{{#servers}}
			<section class="server-section">
				<div class="server-header">
					<div class="server-icon">🖥️</div>
					<div>
						<h2 class="server-name">{{name}}</h2>
					</div>
					<div class="server-status">
						<span class="status-badge status-ok">✅ 正常</span>
					</div>
				</div>

				<div class="grid-container">
					{{#inspectors}}
					{{#ifEq type 'memory'}}
					<div class="card">
						<div class="card-header">
							<span class="card-title">
								<span class="icon icon-memory">💾</span>
								内存使用
							</span>
						</div>
						<div class="metric-grid">
							<div class="metric-item">
								<div class="metric-value">{{metrics.mem_total}}</div>
								<div class="metric-label">总内存</div>
							</div>
							<div class="metric-item">
								<div class="metric-value">{{metrics.mem_free}}</div>
								<div class="metric-label">空闲</div>
							</div>
							<div class="metric-item">
								<div class="metric-value">{{metrics.cached}}</div>
								<div class="metric-label">缓存</div>
							</div>
							<div class="metric-item">
								<div class="metric-value">{{metrics.swap_free}}</div>
								<div class="metric-label">Swap空闲</div>
							</div>
						</div>
					</div>
					{{/ifEq}}

					{{#ifEq type 'disk'}}
					<div class="card">
						<div class="card-header">
							<span class="card-title">
								<span class="icon icon-disk">💿</span>
								磁盘空间
							</span>
						</div>
						<div class="metric-grid">
							<div class="metric-item">
								<div class="metric-value">{{metrics.size}}</div>
								<div class="metric-label">总容量</div>
							</div>
							<div class="metric-item">
								<div class="metric-value">{{metrics.available}}</div>
								<div class="metric-label">可用</div>
							</div>
						</div>
						<div class="progress-bar-container">
							<div class="progress-header">
								<span>使用率</span>
								<span>{{metrics.percent_full}}%</span>
							</div>
							<div class="progress-bar">
								<div class="progress-fill progress-success" style="width: {{metrics.percent_full}}%"></div>
							</div>
						</div>
					</div>
					{{/ifEq}}

					{{#ifEq type 'loadavg'}}
					<div class="card">
						<div class="card-header">
							<span class="card-title">
								<span class="icon icon-cpu">⚡</span>
								CPU负载
							</span>
						</div>
						<div class="metric-grid">
							<div class="metric-item">
								<div class="metric-value">{{metrics.load_1m}}</div>
								<div class="metric-label">1分钟</div>
							</div>
							<div class="metric-item">
								<div class="metric-value">{{metrics.load_5m}}</div>
								<div class="metric-label">5分钟</div>
							</div>
							<div class="metric-item">
								<div class="metric-value">{{metrics.load_15m}}</div>
								<div class="metric-label">15分钟</div>
							</div>
						</div>
					</div>
					{{/ifEq}}

					{{#ifEq type 'system'}}
					<div class="card">
						<div class="card-header">
							<span class="card-title">
								<span class="icon icon-system">🖴</span>
								系统信息
							</span>
						</div>
						<div class="metric-grid">
							<div class="metric-item">
								<div class="metric-value">{{metrics.uptime}}</div>
								<div class="metric-label">运行时间</div>
							</div>
						</div>
					</div>
					{{/ifEq}}
					{{/inspectors}}

					{{#inspectors}}
					{{#alarms}}
					<div class="card" style="grid-column: span 1;">
						<div class="card-header">
							<span class="card-title">🔔 告警</span>
						</div>
						<div class="alarm-list">
							<div class="alarm-item {{#if fired}}danger{{else}}ok{{/if}}">
								<span class="alarm-name">{{name}}</span>
								<span class="alarm-status">
									<span class="alarm-badge {{#if fired}}danger{{else}}ok{{/if}}">
										{{#if fired}}✗{{else}}✓{{/if}}
									</span>
								</span>
							</div>
						</div>
					</div>
					{{/alarms}}
					{{/inspectors}}
				</div>
			</section>
			{{/servers}}
		</main>

		<footer class="footer">
			<p>由 <strong>SshSysMon</strong> 生成 | {{ctime}}</p>
		</footer>
	</div>

	<script>
		function setTheme(theme) {
			document.documentElement.setAttribute('data-theme', theme);
			localStorage.setItem('dashboard-theme', theme);

			if (theme === 'dark') {
				document.getElementById('dark-btn').classList.add('active');
				document.getElementById('light-btn').classList.remove('active');
			} else {
				document.getElementById('light-btn').classList.add('active');
				document.getElementById('dark-btn').classList.remove('active');
			}
		}

		const savedTheme = localStorage.getItem('dashboard-theme');
		if (savedTheme) {
			setTheme(savedTheme);
		}
	</script>
</body>
</html>
