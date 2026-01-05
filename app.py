import os
import re
import json
import time
import uuid
import base64
import shutil
import asyncio
import requests
import platform
import subprocess
import threading
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# Environment variables
UPLOAD_URL = os.environ.get('UPLOAD_URL', '')  # Node or subscription upload address, only filling this address will upload nodes, filling PROJECT_URL at the same time will upload subscriptions, for example: https://merge.serv00.net
PROJECT_URL = os.environ.get('PROJECT_URL', '')  # Project url, need to fill in for automatic keep-alive or automatic subscription upload, for example: https://www.google.com,
AUTO_ACCESS = os.environ.get('AUTO_ACCESS', 'false').lower() == 'true'  # false turns off automatic keep-alive, true turns on automatic keep-alive, default is off
FILE_PATH = os.environ.get('FILE_PATH', '.cache')  # Running path, sub.txt save path
SUB_PATH = os.environ.get('SUB_PATH', 'sub')  # Subscription token, default is sub, for example: https://www.google.com/sub
UUID = os.environ.get('UUID', '') or str(uuid.uuid4())  # UUID
ARGO_DOMAIN = os.environ.get('ARGO_DOMAIN', '')  # Argo fixed tunnel domain, leave empty to use temporary tunnel
ARGO_AUTH = os.environ.get('ARGO_AUTH', '')  # Argo fixed tunnel key, leave empty to use temporary tunnel
ARGO_PORT = int(os.environ.get('ARGO_PORT', '8001'))  # Argo port, when using fixed tunnel token, need to set the port in cloudflare backend to be consistent with here
CFIP = os.environ.get('CFIP', 'spring.io')  # Preferred ip or preferred domain
CFPORT = int(os.environ.get('CFPORT', '443'))  # Preferred ip or preferred domain corresponding port
NAME = os.environ.get('NAME', '')  # Node name
CHAT_ID = os.environ.get('CHAT_ID', '')  # Telegram chat_id, push nodes to tg, both variables need to be filled to push
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')  # Telegram bot_token
PORT = int(os.environ.get('SERVER_PORT') or os.environ.get('PORT') or 3000)  # Subscription port, if unable to subscribe, manually modify to the assigned port


# Create running folder
def create_directory():
    try:
        print('\033c', end='')
        if not os.path.exists(FILE_PATH):
            os.makedirs(FILE_PATH)
            print(f"{FILE_PATH} is created")
        else:
            print(f"{FILE_PATH} already exists")
    except Exception as e:
        print(f"Error creating directory {FILE_PATH}: {e}")
        # Don't stop the program, just log the error


# Global variables
npm_path = os.path.join(FILE_PATH, 'npm')
php_path = os.path.join(FILE_PATH, 'php')
web_path = os.path.join(FILE_PATH, 'web')
bot_path = os.path.join(FILE_PATH, 'bot')
sub_path = os.path.join(FILE_PATH, 'sub.txt')
list_path = os.path.join(FILE_PATH, 'list.txt')
boot_log_path = os.path.join(FILE_PATH, 'boot.log')
config_path = os.path.join(FILE_PATH, 'config.json')


# Delete nodes
def delete_nodes():
    try:
        if not UPLOAD_URL:
            return

        if not os.path.exists(sub_path):
            return

        try:
            with open(sub_path, 'r') as file:
                file_content = file.read()
        except:
            return None

        decoded = base64.b64decode(file_content).decode('utf-8')
        nodes = [line for line in decoded.split('\n') if
                 any(protocol in line for protocol in ['vless://', 'vmess://', 'trojan://', 'hysteria2://', 'tuic://'])]

        if not nodes:
            return

        try:
            requests.post(f"{UPLOAD_URL}/api/delete-nodes",
                          data=json.dumps({"nodes": nodes}),
                          headers={"Content-Type": "application/json"}).raise_for_status()
        except Exception as e:
            print(f"Error deleting nodes: {e}")
            # Don't stop the program, just log the error
    except Exception as e:
        print(f"Error in delete_nodes: {e}")
        # Don't stop the program, just log the error


# Clean up old files
def cleanup_old_files():
    paths_to_delete = ['web', 'bot', 'npm', 'php', 'boot.log', 'list.txt']
    for file in paths_to_delete:
        file_path = os.path.join(FILE_PATH, file)
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
            # Don't stop the program, just log the error


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Hello World')

        elif self.path == f'/{SUB_PATH}':
            try:
                with open(sub_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(content)
            except:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


# Determine system architecture
def get_system_architecture():
    try:
        architecture = platform.machine().lower()
        if 'arm' in architecture or 'aarch64' in architecture:
            return 'arm'
        else:
            return 'amd'
    except Exception as e:
        print(f"Error determining system architecture: {e}")
        # Default to amd if detection fails
        return 'amd'


# Download file based on architecture
def download_file(file_name, file_url):
    file_path = os.path.join(FILE_PATH, file_name)
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        # Handle zip files
        if file_url.endswith('.zip'):
            import zipfile
            import io
            
            # Download to memory first
            zip_content = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                zip_content.write(chunk)
            zip_content.seek(0)
            
            # Extract zip file
            with zipfile.ZipFile(zip_content, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(FILE_PATH)
                
                # Find the main executable file
                extracted_files = zip_ref.namelist()
                target_file = None
                
                for extracted_file in extracted_files:
                    if file_name == 'web' and 'xray' in extracted_file and not extracted_file.endswith(('.dat', '.md', '.txt', '.json')):
                        target_file = extracted_file
                        break
                    elif file_name == 'bot' and 'cloudflared' in extracted_file and extracted_file.endswith(('.linux', '.darwin', '.windows')):
                        target_file = extracted_file
                        break
                
                if target_file:
                    extracted_path = os.path.join(FILE_PATH, target_file)
                    # Rename to expected filename
                    os.rename(extracted_path, file_path)
                    print(f"Download and extract {file_name} successfully")
                else:
                    print(f"Could not find target file in {file_name} zip | path: {file_path}")
                    return False
                        
        else:
            # Handle regular files
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Download {file_name} successfully")

        return True
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"Download {file_name} failed: {e}")
        return False


# Get files for architecture
def get_files_for_architecture(architecture):
    try:
        base_files = []
        
        # Xray binary URLs
        if architecture == 'arm':
            base_files.append({"fileName": "web", "fileUrl": "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-arm64-v8a.zip"})
        else:
            base_files.append({"fileName": "web", "fileUrl": "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"})
        
        # Cloudflared binary URLs
        if architecture == 'arm':
            base_files.append({"fileName": "bot", "fileUrl": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"})
        else:
            base_files.append({"fileName": "bot", "fileUrl": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"})

        return base_files
    except Exception as e:
        print(f"Error getting files for architecture {architecture}: {e}")
        # Return empty list if error occurs
        return []


# Authorize files with execute permission
def authorize_files(file_paths):
    for relative_file_path in file_paths:
        absolute_file_path = os.path.join(FILE_PATH, relative_file_path)
        if os.path.exists(absolute_file_path):
            try:
                os.chmod(absolute_file_path, 0o755)
                print(f"Made {absolute_file_path} executable")
            except Exception as e:
                print(f"Failed to make {absolute_file_path} executable: {e}")
                # Don't stop the program, just log the error


# Configure Argo tunnel
def argo_type():
    try:
        if not ARGO_AUTH or not ARGO_DOMAIN:
            print("ARGO_DOMAIN or ARGO_AUTH variable is empty, use quick tunnels")
            return

        if "TunnelSecret" in ARGO_AUTH:
            with open(os.path.join(FILE_PATH, 'tunnel.json'), 'w') as f:
                f.write(ARGO_AUTH)

            tunnel_id = ARGO_AUTH.split('"')[11]
            tunnel_yml = f"""
tunnel: {tunnel_id}
credentials-file: {os.path.join(FILE_PATH, 'tunnel.json')}
protocol: http2

ingress:
  - hostname: {ARGO_DOMAIN}
    service: http://localhost:{ARGO_PORT}
    originRequest:
      noTLSVerify: true
  - service: http_status:404
"""
            with open(os.path.join(FILE_PATH, 'tunnel.yml'), 'w') as f:
                f.write(tunnel_yml)
        else:
            print("Use token connect to tunnel,please set the {ARGO_PORT} in cloudflare")
    except Exception as e:
        print(f"Error configuring Argo tunnel: {e}")
        # Don't stop the program, just log the error


# Execute shell command and return output
def exec_cmd(command):
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return stdout + stderr
    except Exception as e:
        print(f"Error executing command: {e}")
        return str(e)


# Download and run necessary files
async def download_files_and_run():
    global private_key, public_key

    architecture = get_system_architecture()
    files_to_download = get_files_for_architecture(architecture)

    if not files_to_download:
        print("Can't find a file for the current architecture")
        await asyncio.sleep(10)
        return await download_files_and_run()

    print(f"Downloading binaries for {architecture}64 architecture...")
    
    # Check if files already exist to avoid re-downloading
    all_files_exist = True
    for file_info in files_to_download:
        file_path = os.path.join(FILE_PATH, file_info["fileName"])
        if not os.path.exists(file_path):
            all_files_exist = False
            break
    
    if not all_files_exist:
        # Download all files
        download_success = True
        for file_info in files_to_download:
            print(f"Downloading {file_info['fileName']} ({file_info['fileUrl']}) ...")
            if not download_file(file_info["fileName"], file_info["fileUrl"]):
                download_success = False
                print(f"Failed to download {file_info['fileName']}")

        if not download_success:
            print("Error downloading files, retrying in 10 seconds...")
            await asyncio.sleep(10)
            return await download_files_and_run()
    else:
        print("All required files already exist, skipping download")
        
    # Verify all required files are downloaded
    required_files = ['web', 'bot']
    for required_file in required_files:
        required_path = os.path.join(FILE_PATH, required_file)
        if not os.path.exists(required_path):
            print(f"Required file {required_file} not found")
            await asyncio.sleep(10)
            return await download_files_and_run()

    # Authorize files
    files_to_authorize = ['web', 'bot']
    authorize_files(files_to_authorize)

    # Generate configuration file
    config = {"log": {"access": "/dev/null", "error": "/dev/null", "loglevel": "none", }, "inbounds": [
        {"port": ARGO_PORT, "protocol": "vless",
         "settings": {"clients": [{"id": UUID, "flow": "xtls-rprx-vision", }, ], "decryption": "none",
                      "fallbacks": [{"dest": 3001}, {"path": "/vless-argo", "dest": 3002},
                                    {"path": "/vmess-argo", "dest": 3003}, {"path": "/trojan-argo", "dest": 3004}, ], },
         "streamSettings": {"network": "tcp", }, }, {"port": 3001, "listen": "127.0.0.1", "protocol": "vless",
                                                     "settings": {"clients": [{"id": UUID}, ], "decryption": "none"},
                                                     "streamSettings": {"network": "ws", "security": "none"}},
        {"port": 3002, "listen": "127.0.0.1", "protocol": "vless",
         "settings": {"clients": [{"id": UUID, "level": 0}], "decryption": "none"},
         "streamSettings": {"network": "ws", "security": "none", "wsSettings": {"path": "/vless-argo"}},
         "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"], "metadataOnly": False}},
        {"port": 3003, "listen": "127.0.0.1", "protocol": "vmess",
         "settings": {"clients": [{"id": UUID, "alterId": 0}]},
         "streamSettings": {"network": "ws", "wsSettings": {"path": "/vmess-argo"}},
         "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"], "metadataOnly": False}},
        {"port": 3004, "listen": "127.0.0.1", "protocol": "trojan", "settings": {"clients": [{"password": UUID}, ]},
         "streamSettings": {"network": "ws", "security": "none", "wsSettings": {"path": "/trojan-argo"}},
         "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"], "metadataOnly": False}}, ],
              "outbounds": [{"protocol": "freedom", "tag": "direct"}, {"protocol": "blackhole", "tag": "block"}]}
    with open(os.path.join(FILE_PATH, 'config.json'), 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)


    # Run sbX
    web_path = os.path.join(FILE_PATH, 'web')
    if os.path.exists(web_path):
        # Make executable if needed
        os.chmod(web_path, 0o755)
        command = f"nohup {web_path} -c {os.path.join(FILE_PATH, 'config.json')} >/dev/null 2>&1 &"
        try:
            exec_cmd(command)
            print('web is running')
            time.sleep(1)
        except Exception as e:
            print(f"web running error: {e}")
    else:
        print("Web binary not found, skipping Xray server")

    # Run cloudflared
    bot_path = os.path.join(FILE_PATH, 'bot')
    if os.path.exists(bot_path):
        # Make executable if needed
        os.chmod(bot_path, 0o755)
        if re.match(r'^[A-Z0-9a-z=]{120,250}$', ARGO_AUTH):
            args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 run --token {ARGO_AUTH}"
        elif "TunnelSecret" in ARGO_AUTH:
            args = f"tunnel --edge-ip-version auto --config {os.path.join(FILE_PATH, 'tunnel.yml')} run"
        else:
            args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 --logfile {FILE_PATH}/boot.log --loglevel info --url http://localhost:{ARGO_PORT}"

        try:
            exec_cmd(f"nohup {bot_path} {args} >/dev/null 2>&1 &")
            print('bot is running')
            time.sleep(2)
        except Exception as e:
            print(f"Error executing command: {e}")
            # If cloudflared fails, wait and retry
            await asyncio.sleep(10)
            return await download_files_and_run()
    else:
        print("Bot binary not found, skipping cloudflared")
        await asyncio.sleep(10)
        return await download_files_and_run()

    time.sleep(5)

    # Extract domains and generate sub.txt
    await extract_domains()


# Extract domains from cloudflared logs
async def extract_domains():
    argo_domain = None

    if ARGO_AUTH and ARGO_DOMAIN:
        argo_domain = ARGO_DOMAIN
        print(f'ARGO_DOMAIN: {argo_domain}')
        print(f'UUID: {UUID}')
        await generate_links(argo_domain)
    else:
        try:
            with open(boot_log_path, 'r') as f:
                file_content = f.read()

            lines = file_content.split('\n')
            argo_domains = []

            for line in lines:
                domain_match = re.search(r'https?://([^ ]*trycloudflare\.com)/?', line)
                if domain_match:
                    domain = domain_match.group(1)
                    argo_domains.append(domain)

            if argo_domains:
                argo_domain = argo_domains[0]
                print(f'ArgoDomain: {argo_domain}')
                await generate_links(argo_domain)
            else:
                print('ArgoDomain not found, re-running bot to obtain ArgoDomain')
                # Remove boot.log and restart bot
                if os.path.exists(boot_log_path):
                    os.remove(boot_log_path)

                try:
                    exec_cmd('pkill -f "[b]ot" > /dev/null 2>&1')
                except:
                    pass

                time.sleep(1)
                args = f'tunnel --edge-ip-version auto --no-autoupdate --protocol http2 --logfile {FILE_PATH}/boot.log --loglevel info --url http://localhost:{ARGO_PORT}'
                exec_cmd(f'nohup {os.path.join(FILE_PATH, "bot")} {args} >/dev/null 2>&1 &')
                print('bot is running.')
                time.sleep(6)  # Wait 6 seconds
                await extract_domains()  # Try again
        except Exception as e:
            print(f'Error reading boot.log: {e}')
            # Wait and retry
            await asyncio.sleep(10)
            await extract_domains()


# Upload nodes to subscription service
def upload_nodes():
    if UPLOAD_URL and PROJECT_URL:
        subscription_url = f"{PROJECT_URL}/{SUB_PATH}"
        json_data = {
            "subscription": [subscription_url]
        }

        try:
            response = requests.post(
                f"{UPLOAD_URL}/api/add-subscriptions",
                json=json_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print('Subscription uploaded successfully')
        except Exception as e:
            print(f'Failed to upload subscription: {e}')
            # Don't stop the program, just log the error

    elif UPLOAD_URL:
        if not os.path.exists(list_path):
            return

        with open(list_path, 'r') as f:
            content = f.read()

        nodes = [line for line in content.split('\n') if
                 any(protocol in line for protocol in ['vless://', 'vmess://', 'trojan://', 'hysteria2://', 'tuic://'])]

        if not nodes:
            return

        json_data = json.dumps({"nodes": nodes})

        try:
            response = requests.post(
                f"{UPLOAD_URL}/api/add-nodes",
                data=json_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print('Nodes uploaded successfully')
        except Exception as e:
            print(f'Failed to upload nodes: {e}')
            # Don't stop the program, just log the error
    else:
        return

# Send error notification to Telegram
def send_telegram_error(error_message, function_name="Unknown"):
    if not BOT_TOKEN or not CHAT_ID:
        print('TG variables is empty, Skipping push error to TG')
        return

    try:
        error_text = f"""
🚨 **Error Alert** - {NAME}

<b>Function</b>: <code>{function_name}</code>
<b>Time</b>: <code>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</code>
<b>Error</b>: <code>{error_message}</code>

Please check the logs for more details.
"""

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {
            "chat_id": CHAT_ID,
            "text": error_text,
            "parse_mode": "HTML"
        }

        resp = requests.post(url, json=params)
        resp.raise_for_status()
        print('Telegram error message sent successfully')
    except Exception as e:
        print(f'Failed to send Telegram error message: {e}')
        if 'resp' in locals():
            print(resp.json())

# Send configuration information to Telegram
def send_telegram_config(argo_domain="Generated-Config"):
    if not BOT_TOKEN or not CHAT_ID:
        print('TG variables is empty, Skipping push config to TG')
        return

    try:
        with open(sub_path, 'r') as f:
            message = f.read()

        node_count = len(message.split()) if message else 0

        config_info = f"""
✅ <b>Configuration Complete</b> - {NAME}

<b>Argo Domain</b>: <code>{argo_domain}</code>
<b>UUID</b>: <code>{UUID}</code>
<b>Subscription URL</b>: <code>{PROJECT_URL}/{SUB_PATH}</code>
<b>Node Count</b>: <code>{node_count}</code>
<b>Time</b>: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}

All services are running successfully! 🎉
"""

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {
            "chat_id": CHAT_ID,
            "text": config_info,
            "parse_mode": "HTML"
        }

        resp = requests.post(url, json=params)
        resp.raise_for_status()
        print('Telegram configuration message sent successfully')
    except Exception as e:
        print(f'Failed to send Telegram configuration message: {e}')
        send_telegram_error(str(e), "send_telegram_config")
        if 'resp' in locals():
            print(resp.json())

# Generate links and subscription content
async def generate_links(argo_domain):
    try:
        # Get ISP information with error handling
        try:
            # meta_info = subprocess.run(['curl', '-s', 'https://speed.cloudflare.com/meta'],
            #                          capture_output=True, text=True, timeout=10)
            # meta_info = meta_info.stdout.split('"')
            # ISP = f"{meta_info[25]}-{meta_info[17]}".replace(' ', '_').strip()

            meta_info = subprocess.run(['curl', '-sm', '5', '-H', 'User-Agent: Mozilla/5.0', 'https://api.ip.sb/geoip'], capture_output=True, text=True)
            geo_data = json.loads(meta_info.stdout)
            country_code = geo_data.get('country_code', 'Unknown')
            isp = geo_data.get('isp', 'Unknown').replace(' ', '_').strip()

            if NAME and NAME.strip():
                ISP = f"{NAME.strip()}-{country_code}_{isp}"
            else:
                ISP = f"{country_code}_{isp}"
        except Exception as e:
            print(f"Error getting ISP info: {e}")
            ISP = "Unknown-ISP"
            # Use default ISP if curl fails

        time.sleep(2)
        
        # Generate VMESS configuration
        VMESS = {
            "v": "2", 
            "ps": f"{ISP}", 
            "add": CFIP, 
            "port": CFPORT, 
            "id": UUID, 
            "aid": "0", 
            "scy": "none", 
            "net": "ws", 
            "type": "none", 
            "host": argo_domain, 
            "path": "/vmess-argo?ed=2560", 
            "tls": "tls", 
            "sni": argo_domain, 
            "alpn": "", 
            "fp": "chrome"
        }

        # Generate subscription content
        list_txt = f"""vless://{UUID}@{CFIP}:{CFPORT}?encryption=none&security=tls&sni={argo_domain}&fp=chrome&type=ws&host={argo_domain}&path=%2Fvless-argo%3Fed%3D2560#{ISP}

vmess://{base64.b64encode(json.dumps(VMESS).encode('utf-8')).decode('utf-8')}

trojan://{UUID}@{CFIP}:{CFPORT}?security=tls&sni={argo_domain}&fp=chrome&type=ws&host={argo_domain}&path=%2Ftrojan-argo%3Fed%3D2560#{ISP}"""

        # Save files with error handling
        try:
            with open(os.path.join(FILE_PATH, 'list.txt'), 'w', encoding='utf-8') as list_file:
                list_file.write(list_txt)
        except Exception as e:
            print(f"Error writing list.txt: {e}")
            return None

        sub_txt = base64.b64encode(list_txt.encode('utf-8')).decode('utf-8')
        try:
            with open(os.path.join(FILE_PATH, 'sub.txt'), 'w', encoding='utf-8') as sub_file:
                sub_file.write(sub_txt)
        except Exception as e:
            print(f"Error writing sub.txt: {e}")
            return None

        print(f"Generated {len(list_txt.split())} nodes")
        print(f"{FILE_PATH}/sub.txt saved successfully")

        try:
            upload_nodes()
        except Exception as e:
            print(f"Error uploading nodes: {e}")

        try:
            send_telegram_config(argo_domain)
        except Exception as e:
            print(f"Error sending config to Telegram: {e}")
            send_telegram_error(str(e), "generate_links")

        return sub_txt
    except Exception as e:
        print(f"Error generating links: {e}")
        send_telegram_error(str(e), "generate_links")
        # Wait and retry
        await asyncio.sleep(30)
        # Try to extract domains again
        await extract_domains()


# Clean up files after 90 seconds
def clean_files():
    def _cleanup():
        try:
            time.sleep(90)  # Wait 90 seconds
            files_to_delete = [boot_log_path, config_path, list_path, web_path, bot_path, php_path, npm_path]

            for file in files_to_delete:
                try:
                    if os.path.exists(file):
                        if os.path.isdir(file):
                            shutil.rmtree(file)
                        else:
                            os.remove(file)
                except Exception as e:
                    print(f"Error removing {file}: {e}")

            print('\033c', end='')
            print('App is running')
            print('Thank you for using this script, enjoy!')
        except Exception as e:
            print(f"Error in cleanup: {e}")

    threading.Thread(target=_cleanup, daemon=True).start()


# Main function to start the server
async def start_server():
    try:
        delete_nodes()
        cleanup_old_files()
        create_directory()
        argo_type()
        await download_files_and_run()

        server_thread = Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

        # clean_files()
    except Exception as e:
        print(f"Error in start_server: {e}")
        print("Retrying in 10 seconds...")
        await asyncio.sleep(10)
        # Retry the entire process
        await start_server()


def run_server():
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    print(f"Server is running on port {PORT}")
    print(f"Running done！")
    # print(f"\nLogs will be delete in 90 seconds")
    server.serve_forever()


def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(start_server())
        
        # Keep the event loop running
        while True:
            try:
                time.sleep(3600)
            except KeyboardInterrupt:
                print("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Continuing...")
                time.sleep(30)
    except Exception as e:
        print(f"Fatal error in run_async: {e}")
        # Wait before restarting
        time.sleep(10)


if __name__ == "__main__":
    import sys
    
    # Check if send_config command is provided
    if len(sys.argv) > 1 and sys.argv[1] == 'send_config':
        if not BOT_TOKEN or not CHAT_ID:
            print('Error: BOT_TOKEN and CHAT_ID environment variables must be set for send_config command')
            sys.exit(1)
        
        # Check if sub.txt exists
        if not os.path.exists(sub_path):
            print('Error: Configuration file not found. Please run the application first to generate configuration.')
            sys.exit(1)
        
        try:
            with open(sub_path, 'r') as f:
                config_content = f.read()
            
            # Send configuration to Telegram
            send_telegram_config("Generated-Config")
            print('Configuration sent to Telegram successfully!')
            
        except Exception as e:
            print(f'Error sending configuration: {e}')
            sys.exit(1)
    else:
        while True:
            try:
                run_async()
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Restarting in 10 seconds...")
                time.sleep(10)
