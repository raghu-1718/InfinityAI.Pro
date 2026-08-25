import subprocess

service_text = """[Unit]
Description=InfinityAI Engine-B ML Inference Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/infinityai/engine-b/src
Environment="PORT=8080"
Environment="GOOGLE_CLOUD_PROJECT=project-841b7f97-5ee3-4fbe-920"
Environment="GCS_MODELS_BUCKET=infinity-ai-models-vault"
Environment="ENVIRONMENT=production"
Environment="ENGINE_C_URL=https://engine-c-r2f5flt77q-el.a.run.app"
Environment="DEFAULT_USER_ID=raghu_primary"
Environment="PRIMARY_USER_ID=raghu_primary"
Environment="PYTHONPATH=/opt/infinityai/engine-b/src:/opt/infinityai/engine-b"
ExecStart=/opt/infinityai/engine-b/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

with open("/etc/systemd/system/engine-b.service", "w") as f:
    f.write(service_text)

subprocess.run(["systemctl", "daemon-reload"], check=True)
subprocess.run(["systemctl", "restart", "engine-b"], check=True)
print("SUCCESS_RESTARTED")
