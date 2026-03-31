# FastAPI Deployment on IaaS (Virtual Machines) Guide

## Overview
This guide provides step-by-step instructions for deploying a FastAPI application on an IaaS (Infrastructure as a Service) VM, such as Azure VMs, AWS EC2, or any Linux-based virtual machine. We'll cover installing dependencies, setting up the Python environment, cloning the code, and configuring Gunicorn with systemd for production deployment.

## Prerequisites
- A Linux VM (Ubuntu 20.04+ recommended)
- SSH access to the VM
- Administrator (sudo) privileges
- Git installed on your local machine

---

## Step 1: Update System & Install Dependencies

SSH into your VM and update the system packages:

```bash
sudo apt update
sudo apt upgrade -y
```

Install Python, pip, and venv:

```bash
sudo apt install -y python3 python3-pip python3-venv
```

Install other required packages:

```bash
sudo apt install -y git curl wget postgresql-client
```

Verify Python installation:

```bash
python3 --version
pip3 --version
```

---

## Step 2: Create a Non-Root User (Optional but Recommended)

For security, create a dedicated user (e.g., `student`) to run the application:

```bash
sudo useradd -m -s /bin/bash student
sudo usermod -aG sudo student  # Optional: add to sudo group
```

Switch to the new user:

```bash
su - student
```

---

## Step 3: Clone the Project Repository

Navigate to the home directory and clone your FastAPI project:

```bash
cd /home/student
git clone <your_repository_url> fastapi
cd fastapi/src/
```

Verify the project structure:

```bash
ls -la
# Should see: app/, requirements.txt, etc.
```

---

## Step 4: Create Python Virtual Environment

Create a virtual environment to isolate project dependencies:

```bash
cd /home/student/fastapi
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Your prompt should now show `(venv)`:

```
(venv) student@vm:~/fastapi$
```

---

## Step 5: Install Python Dependencies

Install the required Python packages from requirements.txt:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Common packages for FastAPI projects:

```bash
pip install fastapi uvicorn gunicorn sqlalchemy psycopg2-binary python-dotenv pydantic
```

---

## Step 6: Configure Environment Variables

Create a `.env` file in the user's home directory:

```bash
nano /home/student/.env
```

Add your environment variables:

```bash
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=your_password
DATABASE_NAME=fastapi
DATABASE_USERNAME=postgres
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_DRIVER=postgresql
```

Save with `Ctrl+O`, `Enter`, `Ctrl+X`.

Restrict permissions for security:

```bash
chmod 600 /home/student/.env
```

---

## Step 7: Test the Application Locally

Start the application manually to ensure it works:

```bash
cd /home/student/fastapi
source venv/bin/activate
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

Test it from another terminal:

```bash
curl http://localhost:8000/docs
```

If successful, you should get an HTTP 200 response. Press `Ctrl+C` to stop.

---

## Step 8: Install and Configure Gunicorn Service

Create the systemd service file:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Copy the following configuration:

```ini
[Unit]
Description=gunicorn instance to server api
After=network.target

[Service]
User=student
Group=student
WorkingDirectory=/home/student/fastapi/src/
Environment="PATH=/home/student/fastapi/venv/bin"
ExecStart=/home/student/fastapi/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
EnvironmentFile=/home/student/.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit.

---

## Step 9: Enable and Start the Service

Reload systemd daemon:

```bash
sudo systemctl daemon-reload
```

Enable the service to start at boot:

```bash
sudo systemctl enable gunicorn.service
```

Start the service:

```bash
sudo systemctl start gunicorn.service
```

Verify it's running:

```bash
sudo systemctl status gunicorn.service
```

View logs in real-time:

```bash
sudo journalctl -u gunicorn.service -f
```

---

## Step 10: Setup Reverse Proxy (Nginx)

Install Nginx:

```bash
sudo apt install -y nginx
```

Create an Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/fastapi
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
```

Test Nginx configuration:

```bash
sudo nginx -t
```

Start Nginx:

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

Your application is now accessible on port 80!

---

## Service File Structure & Configuration

### What is Systemd?
Systemd is the init system and service manager for modern Linux distributions. It manages system services, starting them at boot, restarting them if they crash, and logging their output.

### `[Unit]` Section
This section defines metadata and dependencies for the service.

```ini
[Unit]
Description=gunicorn instance to server api
After=network.target
```

| Option | Purpose |
|--------|---------|
| `Description` | A human-readable description of the service (shown in logs and status commands) |
| `After=network.target` | Ensures the network is available before starting the service (waits for network initialization) |

---

### `[Service]` Section
This section defines how the service should run.

```ini
[Service]
User=student
Group=student
WorkingDirectory=/home/student/fastapi/src/
Environment="PATH=/home/student/fastapi/venv/bin"
ExecStart=/home/student/fastapi/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
EnvironmentFile=/home/student/.env
```

| Option | Purpose |
|--------|---------|
| `User=student` | The Linux user account that runs the service (prevents running as root for security) |
| `Group=student` | The Linux group that runs the service (controls file permissions) |
| `WorkingDirectory` | The directory where the service starts (sets the base path for relative imports and file operations) |
| `Environment="PATH=..."` | Sets the PATH environment variable to use the Python virtual environment's bin directory |
| `ExecStart` | The command executed when the service starts |
| `EnvironmentFile` | Path to a file containing environment variables (e.g., database credentials, secret keys) |

#### ExecStart Command Breakdown
```
/home/student/fastapi/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

| Component | Purpose |
|-----------|---------|
| `/home/student/fastapi/venv/bin/gunicorn` | Full path to the Gunicorn WSGI HTTP server executable |
| `-w 4` | Number of worker processes (4 concurrent requests, adjust based on CPU cores) |
| `-k uvicorn.workers.UvicornWorker` | Specifies Uvicorn as the worker class (needed for async FastAPI) |
| `app.main:app` | Module path and application object (`app/main.py` file, `app` variable) |
| `--bind 0.0.0.0:8000` | Listen on all network interfaces on port 8000 |

---

### `[Install]` Section
This section defines how to enable the service at boot time.

```ini
[Install]
WantedBy=multi-user.target
```

| Option | Purpose |
|--------|---------|
| `WantedBy=multi-user.target` | Service runs in multi-user mode (standard for servers); enables auto-start at boot |

---

## Systemd Service Management Commands

### View Service Status
```bash
# Check if service is running
sudo systemctl status gunicorn.service

# See detailed status
systemctl show gunicorn.service
```

### Start/Stop/Restart Commands
```bash
# Start the service
sudo systemctl start gunicorn.service

# Stop the service
sudo systemctl stop gunicorn.service

# Restart the service
sudo systemctl restart gunicorn.service

# Reload configuration (graceful restart)
sudo systemctl reload gunicorn.service
```

### View Logs
```bash
# View last 50 lines
sudo journalctl -u gunicorn.service -n 50

# Follow logs in real-time
sudo journalctl -u gunicorn.service -f

# View logs from last hour
sudo journalctl -u gunicorn.service --since "1 hour ago"

# View with more details
sudo journalctl -u gunicorn.service -o verbose
```

### Boot Configuration
```bash
# Enable service to start at boot
sudo systemctl enable gunicorn.service

# Disable auto-start at boot
sudo systemctl disable gunicorn.service

# Check if enabled
sudo systemctl is-enabled gunicorn.service
```

---

## How to Use This Service File

### Installation
```bash
# Copy the service file to systemd directory
sudo cp gunicorn.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload
```

### Enable at Boot
```bash
sudo systemctl enable gunicorn.service
```

### Start/Stop/Restart
```bash
# Start the service
sudo systemctl start gunicorn.service

# Stop the service
sudo systemctl stop gunicorn.service

# Restart the service
sudo systemctl restart gunicorn.service

# Check status
sudo systemctl status gunicorn.service

# View logs
sudo journalctl -u gunicorn.service -f  # Follow logs in real-time
```

---

## Common Configurations & Customization

### Increase Worker Count
For a 4-core CPU, use `4` workers (rule of thumb: 2-4 × CPU cores):
```ini
ExecStart=/home/student/fastapi/venv/bin/gunicorn -w 8 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Add Timeout
Prevent hanging requests from blocking workers:
```ini
ExecStart=/home/student/fastapi/venv/bin/gunicorn -w 4 --timeout 60 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Auto-restart on Failure
Add to `[Service]` section:
```ini
Restart=always
RestartSec=10
```

### Change Port
Modify the `--bind` option:
```ini
--bind 0.0.0.0:8001
```

---

## Environment Variables (.env file)

The `EnvironmentFile=/home/student/.env` loads environment variables from the .env file. These should include:

```bash
DATABASE_HOSTNAME=<DB_IP>
DATABASE_PORT=5432
DATABASE_PASSWORD=your_password
DATABASE_NAME=fastapi
DATABASE_USERNAME=postgres
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_DRIVER=postgresql
```

**Important**: Ensure the .env file is only readable by the `student` user for security:
```bash
chmod 600 /home/student/.env
```

---

## Deployment Checklist

Use this checklist to verify your deployment is complete:

- [ ] **System Setup**
  - [ ] VM is running and SSH accessible
  - [ ] System packages updated (`apt update && apt upgrade`)
  - [ ] Python 3, pip, and venv installed
  - [ ] Git installed

- [ ] **User & Directories**
  - [ ] Dedicated non-root user created (e.g., `student`)
  - [ ] Project cloned to `/home/student/fastapi`
  - [ ] Project ownership: `chown -R student:student /home/student/fastapi`

- [ ] **Python Environment**
  - [ ] Virtual environment created: `python3 -m venv venv`
  - [ ] Virtual environment activated
  - [ ] Dependencies installed: `pip install -r requirements.txt`
  - [ ] Gunicorn installed: `pip install gunicorn`

- [ ] **Configuration**
  - [ ] `.env` file created in `/home/student/.env`
  - [ ] All environment variables set (DATABASE_*, SECRET_KEY, etc.)
  - [ ] `.env` permissions restricted: `chmod 600 .env`

- [ ] **Application Test**
  - [ ] Application runs locally: `gunicorn ... --bind 0.0.0.0:8000`
  - [ ] Health check passes: `curl http://localhost:8000/docs`
  - [ ] Database connection works

- [ ] **Systemd Service**
  - [ ] Service file created: `/etc/systemd/system/gunicorn.service`
  - [ ] Service file has correct paths and username
  - [ ] systemd daemon reloaded: `sudo systemctl daemon-reload`
  - [ ] Service enabled: `sudo systemctl enable gunicorn.service`
  - [ ] Service started: `sudo systemctl start gunicorn.service`
  - [ ] Service status verified: `sudo systemctl status gunicorn.service`

- [ ] **Reverse Proxy (Nginx)**
  - [ ] Nginx installed: `sudo apt install nginx`
  - [ ] Nginx config created: `/etc/nginx/sites-available/fastapi`
  - [ ] Nginx config verified: `sudo nginx -t`
  - [ ] Nginx enabled: `sudo systemctl enable nginx`
  - [ ] Nginx restarted: `sudo systemctl restart nginx`
  - [ ] Application accessible via port 80

- [ ] **Security**
  - [ ] `.env` file permissions: `600` (only owner readable)
  - [ ] Service runs as non-root user
  - [ ] Gunicorn bound to localhost:8000, proxy only
  - [ ] Nginx handles external requests (port 80)
  - [ ] Firewall rules configured (if needed)

- [ ] **Monitoring**
  - [ ] Logs accessible: `sudo journalctl -u gunicorn.service`
  - [ ] Service auto-restart configured: `Restart=always`
  - [ ] Monitoring/alerting setup (optional)

---

## Quick Reference: Common Tasks

### Restart the Application After Code Changes
```bash
cd /home/student/fastapi
git pull origin main
sudo systemctl restart gunicorn.service
```

### Update Dependencies
```bash
source /home/student/fastapi/venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart gunicorn.service
```

### Check Application Logs
```bash
sudo journalctl -u gunicorn.service -f
```

### Verify Ports Are Open
```bash
# Check port 8000 (Gunicorn)
sudo lsof -i :8000

# Check port 80 (Nginx)
sudo lsof -i :80
```

### Check Worker Processes
```bash
ps aux | grep gunicorn
# Should show 4 worker processes + 1 master process
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Service won't start | Check logs: `sudo journalctl -u gunicorn.service -n 50` |
| Permission denied | Ensure user has access to `/home/student/fastapi/src/` and `.env` |
| Port 8000 already in use | Kill process: `sudo kill -9 $(lsof -t -i:8000)` |
| Module not found | Verify venv is activated and dependencies installed |
| Env variables not loaded | Check `.env` file path and format |
| Nginx 502 Bad Gateway | Gunicorn not running or not bound to localhost:8000 |
| Connection refused | Check firewall rules, ensure port 80 is open |
| Slow/hanging requests | Increase worker count: `-w 8` in ExecStart |
| High CPU usage | Check app logs for infinite loops, adjust worker count |

---

## Performance Tuning

### Increase Worker Count
For a 4-core CPU, use 4-8 workers (2-4 × CPU cores):

```bash
# Check available cores
nproc

# Update service file ExecStart
ExecStart=/home/student/fastapi/venv/bin/gunicorn -w 8 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000
```

### Add Request Timeout
Prevent hanging requests from blocking workers:

```bash
ExecStart=/home/student/fastapi/venv/bin/gunicorn -w 4 --timeout 60 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000
```

### Enable Gzip Compression (in Nginx)
```nginx
gzip on;
gzip_types text/plain application/json;
gzip_min_length 1000;
```

---

## Security Best Practices

1. **Run as non-root user** ✓ (Uses `User=student`)
2. **Use environment file for secrets** ✓ (Uses `EnvironmentFile`)
3. **Restrict .env file permissions**: `chmod 600 .env`
4. **Bind Gunicorn to localhost only**: `--bind 127.0.0.1:8000`
5. **Use Nginx as reverse proxy** ✓ (Nginx handles external requests)
6. **Enable HTTPS**: Use Let's Encrypt with Certbot in Nginx
7. **Keep system updated**: `apt update && apt upgrade`
8. **Monitor logs regularly**: Set up log rotation and alerts
9. **Use strong SECRET_KEY**: Generate with `openssl rand -hex 32`
10. **Implement rate limiting**: Configure in Nginx or FastAPI

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Gunicorn Documentation](https://gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Systemd Documentation](https://systemd.io/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
