# Description

This project is built in a Python environment to deploy **Argo-Xray** nodes, integrating **Nezha probe v0/v1** (free choice).  
It includes three protocol combinations: **vless-ws-tls / vmess-ws-tls / trojan-ws-tls**.

# Deployment

### Method 1: Regular Python environment
For example, on a gaming or toy platform, simply upload two files:  
`app.py` and `requirements.txt`.  
Authorize `app.py` with `chmod 777`.  
Fill in the variables between lines 17 to 30 in `app.py`.

### Method 2: File + Command combination
Authorize `app.py`, upload both `app.py` and `requirements.txt`,  
then run the following commands:

```bash
chmod +x app.py
pip install -r requirements.txt
screen python app.py
```

If you see the message `screen not found`, it means `screen` is not installed.  
Install it with:
- Debian/Ubuntu: `apt install -y screen`
- CentOS: `yum install -y screen`

### Method 3: Docker Deployment
A prebuilt image is available under **packages** on the right side.  
Image address: `ghcr.io/eooce/python:latest`  
Platforms supporting image deployment are recommended to use this method first.

# Environment Variables

| Variable Name | Required | Default | Description |
| -------------- | -------- | -------- | ----------- |
| UPLOAD_URL   | No | Fill in the homepage of the deployed Merge-sub project | Subscription upload address, e.g., https://merge.serv00.net |
| PROJECT_URL  | No | https://www.google.com | Domain name assigned to the project |
| AUTO_ACCESS  | No | false | Whether to enable auto access keep-alive. Set to `true` to enable (requires `PROJECT_URL`) |
| PORT         | No | 3000 | HTTP service listening port, also used for subscriptions |
| ARGO_PORT    | No | 8001 | Argo tunnel port, must match the fixed tunnel token in Cloudflare |
| UUID         | No | 89c13786-25aa-4520-b2e7-12cd60fb5202 | UUID, must be modified when deploying Nezha v1 on different platforms |
| NEZHA_SERVER | No | — | Nezha panel domain, e.g., v1: nz.aaa.com:8008 or v0: nz.aaa.com |
| NEZHA_PORT   | No | — | Not used in v1. For v0, if the port is one of {443, 8443, 2096, 2087, 2083, 2053}, TLS will be enabled |
| NEZHA_KEY    | No | — | Nezha v1 or v0 key |
| ARGO_DOMAIN  | No | — | Fixed Argo tunnel domain |
| ARGO_AUTH    | No | — | Argo fixed tunnel JSON or token |
| CFIP         | No | time.is | Preferred node domain or IP |
| CFPORT       | No | 443 | Node port |
| NAME         | No | Vls | Node name prefix, e.g., Koyeb Fly |
| FILE_PATH    | No | .cache | Working directory, node storage path |
| SUB_PATH     | No | sub | Node subscription path |

# Node Output

- Output file: `sub.txt` (default location: `.cache`)  
- Subscription link: `assigned-domain/${SUB_PATH}`  
  Example: `https://www.google.com/${SUB_PATH}`  
- Non-standard port subscription (for gaming):  
  `assigned-domain:port/${SUB_PATH}`  
  Example: `http://www.google.com:1234/${SUB_PATH}` (use `http`, not `https`)

# Others

- This is the **Argo version**. For the **Direct connection version**, visit:  
  [https://github.com/eoovve/python-xray-direct](https://github.com/eoovve/python-xray-direct)
- If deploying via GitHub, **fork** the repo first and delete this `README.md` before deployment.  
  If your platform supports Docker deployment and requires GitHub linking,  
  simply create a new project and add a `Dockerfile` containing:
  ```
  FROM ghcr.io/eooce/python:latest
  ```

# Disclaimer

This program is for **learning and research purposes only**.  
It must not be used for any **commercial purposes**.  
Please delete it within **24 hours** of downloading.  
All text, data, and images belong to their respective copyright owners.  
When redistributing, please credit the source.  

By using this program, you agree to comply with all relevant laws and regulations of the **server location**, **host country**, and **user’s country**.  
The author is **not responsible** for any misuse or illegal activity by users.
