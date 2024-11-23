#!/bin/bash

# Variables (change these to match your setup, or pass as arguments)
DOMAIN=${1:-"api.fminatorul.xyz"}
YOUR_USER=${2:-"your_user"}
APP_DIR=${3:-$(pwd)}

echo "Setting up Flask app on $FULL_DOMAIN with NGINX and Gunicorn"
echo "Setting up Flask app with NGINX and Gunicorn"
echo "Domain/IP: $YOUR_DOMAIN_OR_IP"
echo "User: $YOUR_USER"
echo "App Directory: $APP_DIR"

# Step 1 — Install Components
echo "Updating package list and installing required packages..."
sudo apt update
sudo apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv nginx

# Connect to the venv
echo "Running now from the virtual environment"
source venv/bin/activate

# Step 2 — Install Flask and Gunicorn
echo "Installing Flask, Gunicorn, and other dependencies..."
pip install wheel flask gunicorn


# Creating WSGI entry point
echo "Creating WSGI entry point..."
cat > $APP_DIR/wsgi.py <<EOL
from flaskapp import app

if __name__ == "__main__":
    app.run()
EOL

# Step 3 — Configure Gunicorn Service
echo "Configuring Gunicorn systemd service..."
sudo tee /etc/systemd/system/flask_gunicorn.service > /dev/null <<EOL
[Unit]
Description=Gunicorn instance to serve Flask app
After=network.target

[Service]
User=$YOUR_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="GOOGLE_CLOUD_PROJECT=unchiipecos"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 2 --bind unix:$APP_DIR/app.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOL

# Start and enable the Gunicorn service
echo "Starting and enabling Gunicorn service..."
sudo systemctl daemon-reload
sudo systemctl start flask_gunicorn
sudo systemctl enable flask_gunicorn

# Step 5 — Configure NGINX
echo "Configuring NGINX..."
sudo tee /etc/nginx/sites-available/flask_nginx > /dev/null <<EOL
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/app.sock;
    }
}
EOL

# Enable the new NGINX configuration
sudo ln -s /etc/nginx/sites-available/flask_nginx /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Step 6 — Firewall and SSL (optional)
echo "Configuring firewall for NGINX..."
sudo ufw allow 'Nginx Full'
sudo ufw delete allow 5000

# Optional SSL setup with Let's Encrypt
read -p "Would you like to set up SSL with Let's Encrypt? (y/n): " ssl_choice
if [ "$ssl_choice" == "y" ]; then
    sudo apt install -y python3-certbot-nginx
    sudo certbot --nginx -d $DOMAIN
fi

echo "Setup complete! Your Flask app should be running with NGINX and Gunicorn."
