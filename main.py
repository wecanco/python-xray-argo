# main.py
import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Xray Argo Configuration Manager')
    parser.add_argument('command', nargs='?', choices=['run', 'send_config'], default='run',
                       help='Command to execute: run (default) or send_config')
    
    args = parser.parse_args()
    
    if args.command == 'send_config':
        os.system("python app.py send_config")
    else:
        os.system("python app.py")

if __name__ == "__main__":
    main()