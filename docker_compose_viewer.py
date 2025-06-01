#!/usr/bin/env python3

import os
import yaml
import argparse
from flask import Flask, render_template_string

app = Flask(__name__)

SERVICE_IP = None

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Docker Compose Services</title>
  <style>
    html, body {
      height: 100%;
      margin: 0;
    }
    body {
      font-family: Arial, sans-serif;
      background: #f0f2f5;
      color: #333;
      display: flex;
      justify-content: center; /* горизонтальный центр */
      align-items: center;     /* вертикальный центр */
      padding: 2em;
      box-sizing: border-box;
      min-height: 100vh;
    }
    #container {
      width: 90vw;  /* 90% от ширины окна */
      /* max-width: 1200px; */
      overflow-y: auto;
      max-height: 90vh; /* чтобы не вылезать за высоту окна */
      background: white;
      padding: 1em 2em 2em 2em;
      box-shadow: 0 0 8px rgba(0,0,0,0.1);
      border-radius: 6px;
    }
    h1 {
      margin-top: 0;
      margin-bottom: 1em;
      color: #2a3f54;
      font-weight: 700;
    }
    h2 {
      margin-top: 2em;
      margin-bottom: 0.5em;
      font-weight: 700;
      border-bottom: 2px solid #666;
      padding-bottom: 0.2em;
      color: #2a3f54;
    }
    table {
      border-collapse: collapse;
      width: 100%; /* растянуть по ширине контейнера */
      min-width: 800px;
      table-layout: fixed; /* фиксированная ширина столбцов */
    }
    th, td {
      border: 1px solid #ccc;
      padding: 0.6em 1em;
      text-align: left;      /* ВСЕ колонки по левому краю */
      vertical-align: top;   /* выравнивание по верху */
      font-size: 0.95rem;
      word-break: break-word;
      overflow-wrap: break-word;
    }
    th {
      background-color: #e2e6ea;
      font-weight: 600;
    }
    /* Фиксированные ширины столбцов */
    th.service-col, td.service-col       { width: 7%; }
    th.container-col, td.container-col   { width: 7%; }
    th.restart-col, td.restart-col       { width: 7%; }
    th.links-col, td.links-col           { width: 10%; }
    th.ports-col, td.ports-col           { width: 10%; }
    th.volumes-col, td.volumes-col       { width: 40%; }
    th.env-col, td.env-col               { width: 20%; white-space: pre-wrap; font-family: monospace; }

    /* Чередование цвета строк */
    tbody tr:nth-child(odd) {
      background-color: #fafafa;
    }
    tbody tr:nth-child(even) {
      background-color: #f4f6f8;
    }
    a {
      color: #007bff;
      text-decoration: none;
      word-break: break-all;
    }
    a:hover {
      text-decoration: underline;
    }
    div.link-item {
      margin-bottom: 0.3em;
    }
    pre {
      margin: 0;
      font-family: monospace;
      font-size: 0.9rem;
      white-space: pre-wrap;
      word-break: break-word;
      text-align: left; /* чтобы в environment не было центрирования */
    }
  </style>
</head>
<body>
  <div id="container">
    <h1>Docker Compose Services</h1>
    {% for file_group in services_by_file %}
      <h2>{{ file_group.filename }}</h2>
      <table>
        <thead>
          <tr>
            <th class="service-col">Service</th>
            <th class="container-col">Container Name</th>
            <th class="restart-col">Restart Policy</th>
            <th class="links-col">Links (IP:Port)</th>
            <th class="ports-col">Ports</th>
            <th class="volumes-col">Volumes</th>
            <th class="env-col">Environment Variables</th>
          </tr>
        </thead>
        <tbody>
          {% for service in file_group.services %}
            <tr>
              <td class="service-col">{{ service.name }}</td>
              <td class="container-col">{{ service.container_name or "" }}</td>
              <td class="restart-col">{{ service.restart or "" }}</td>
              <td class="links-col">
                {% for link in service.links %}
                  <div class="link-item"><a href="{{ link }}" target="_blank" rel="noopener">{{ link }}</a></div>
                {% endfor %}
              </td>
              <td class="ports-col">
{%- if service.ports -%}
                <pre>
{%- for p in service.ports %}
{{ p.replace(":", " → ") }}
{%- endfor %}
                </pre>
{%- endif -%}
              </td>
              <td class="volumes-col">
{%- if service.volumes -%}
                <pre>
{%- for v in service.volumes %}
{{ v.replace(":", " → ") }}
{%- endfor %}
                </pre>
{%- endif -%}
              </td>
              <td class="env-col">
{%- if service.environment -%}
                <pre>
{%- for e in service.environment %}
{{ e }}
{%- endfor %}
                </pre>
{%- endif -%}
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% endfor %}
  </div>
</body>
</html>
"""

def parse_compose_file(filepath, service_ip):
    with open(filepath, "r") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError:
            return []

    services = []
    for name, config in (data.get("services") or {}).items():
        ports = config.get("ports", [])
        volumes = config.get("volumes", [])

        port_list = []
        link_list = []
        for port in ports:
            if isinstance(port, str):
                parts = port.split(":")
                if len(parts) == 2 and parts[0].isdigit():
                    host_port = parts[0]
                    port_list.append(port)
                    if service_ip:
                        link_list.append(f"http://{service_ip}:{host_port}")
                else:
                    port_list.append(port)

        volume_list = [v for v in volumes if isinstance(v, str)]

        # Обработка переменных окружения
        env = config.get("environment", [])
        env_list = []
        if isinstance(env, dict):
            for k, v in env.items():
                env_list.append(f"{k}={v}")
        elif isinstance(env, list):
            env_list = [str(e) for e in env]
        else:
            env_list = []

        services.append({
            "name": name,
            "container_name": config.get("container_name"),
            "restart": config.get("restart"),
            "ports": port_list,
            "links": link_list,
            "volumes": volume_list,
            "environment": env_list,
        })

    return services

def find_yaml_files(root_dir):
    yaml_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith((".yaml", ".yml")):
                yaml_files.append(os.path.join(dirpath, filename))
    return yaml_files

@app.route("/")
def index():
    services_by_file = []
    for filepath in find_yaml_files(app.config["SEARCH_DIR"]):
        services = parse_compose_file(filepath, SERVICE_IP)
        if services:
            services_by_file.append({
                "filename": os.path.relpath(filepath, start=app.config["SEARCH_DIR"]),
                "services": services
            })

    return render_template_string(TEMPLATE, services_by_file=services_by_file)

def main():
    global SERVICE_IP

    parser = argparse.ArgumentParser(description="Docker Compose HTML viewer")
    parser.add_argument("-d", "--dir", default=".", help="Directory to search for YAML files")
    parser.add_argument("-H", "--host", default="0.0.0.0", help="Host to run Flask server on")
    parser.add_argument("-p", "--port", type=int, default=8888, help="Port to run Flask server on")
    parser.add_argument("-s", "--service-ip", default=None,
                        help="IP address to use in service links (default: Flask server host)")
    args = parser.parse_args()

    SERVICE_IP = args.service_ip or args.host
    app.config["SEARCH_DIR"] = args.dir

    app.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()

