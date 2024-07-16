#!/usr/bin/env python3
import subprocess
import requests
import argparse
import os
import json
import logging
from datetime import datetime
from colorama import Fore, Style, init
import markdown2
from time import sleep

# Initialize colorama
init()

SESSION_LOG_DIR = 'session_logs'
DEFAULT_CONFIG_FILE = 'config.json'
IP_PLACEHOLDER = "<IP>"

# Setup logging
if not os.path.exists(SESSION_LOG_DIR):
    os.makedirs(SESSION_LOG_DIR)

logging.basicConfig(filename=os.path.join(SESSION_LOG_DIR, 'cybercoyote.log'),
                    level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

def generate_session_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def run_command(command):
    print(f"Running command: {command}")
    logging.info(f"Running command: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        result.check_returncode()
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{command}' failed with error: {e}")
        print(f"Error: Command '{command}' failed with error: {e}")
        return f"Error: Command '{command}' failed with error: {e}"

def analyze_output(output, history, prompt_template, llm_server_url, headers, retry_attempts=3):
    print("Analyzing output with LLM...")
    logging.info("Analyzing output with LLM...")
    prompt = f"{prompt_template}\n{output}"
    history.append({"role": "user", "content": prompt})
    data = {
        "mode": "chat",
        "character": "Example",
        "messages": history
    }
    for attempt in range(retry_attempts):
        try:
            response = requests.post(llm_server_url, headers=headers, json=data, verify=False)
            response.raise_for_status()  # Check if the request was successful
            response_json = response.json()
            if 'choices' in response_json and response_json['choices']:
                assistant_message = response_json['choices'][0]['message']['content']
                history.append({"role": "assistant", "content": assistant_message})
                return assistant_message
            else:
                logging.error(f"Unexpected response structure: {response_json}")
                print(f"Error: Unexpected response structure: {response_json}")
                return f"Error: Unexpected response structure: {response_json}"
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e} (attempt {attempt + 1} of {retry_attempts})")
            print(f"Error: Request failed: {e} (attempt {attempt + 1} of {retry_attempts})")
            if attempt + 1 < retry_attempts:
                sleep(2)  # Wait before retrying
            else:
                return f"Error: Request failed after {retry_attempts} attempts: {e}"
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON response: {response.text}")
            print(f"Error: Failed to parse JSON response: {response.text}")
            return f"Error: Failed to parse JSON response: {response.text}"

def extract_next_command(response_text):
    print("Extracting next command from LLM response...")
    logging.info("Extracting next command from LLM response...")
    next_command_marker = "Next command:"
    start_idx = response_text.find(next_command_marker)
    if start_idx != -1:
        start_idx += len(next_command_marker)
        next_command_lines = response_text[start_idx:].split('\n')
        next_command = next_command_lines[1].strip() if len(next_command_lines) > 1 else ""
        logging.info(f"Next command extracted: {next_command}")
        print(f"Next command extracted: {next_command}")
        return next_command
    logging.error("No next command found in LLM response.")
    print("No next command found in LLM response.")
    return None

def log_history(session_id, command, output, analysis):
    log_file = os.path.join(SESSION_LOG_DIR, f"{session_id}.log")
    with open(log_file, 'a') as log:
        log.write(f"Timestamp: {datetime.now()}\n")
        log.write(f"Command: {command}\n")
        log.write(f"Output:\n{output}\n")
        log.write(f"Analysis:\n{analysis}\n")
        log.write("="*80 + "\n")
    logging.info(f"Logged history for session {session_id}")

def print_output(output, analysis):
    print(f"{Fore.CYAN}Command Output:{Style.RESET_ALL}\n{output}")
    print(f"{Fore.GREEN}Analysis:{Style.RESET_ALL}\n{analysis}")

def save_analysis_as_markdown(session_id, command_output, analysis):
    markdown_content = f"# Command Output\n\n```\n{command_output}\n```\n\n# Analysis\n\n{analysis}"
    markdown_file = os.path.join(SESSION_LOG_DIR, f"{session_id}.md")
    with open(markdown_file, 'w') as file:
        file.write(markdown2.markdown(markdown_content))

def interactive_mode(session_id, prompt_template, llm_server_url, headers):
    history_file = os.path.join(SESSION_LOG_DIR, f"{session_id}_history.json")
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            history = json.load(file)
    else:
        history = []

    while True:
        command_str = input("Enter command (or 'exit' to quit): ")
        if command_str.lower() == 'exit':
            break

        command_output = run_command(command_str)
        analysis = analyze_output(command_output, history, prompt_template, llm_server_url, headers)

        # Save history
        with open(history_file, 'w') as file:
            json.dump(history, file)

        print_output(command_output, analysis)
        log_history(session_id, command_str, command_output, analysis)
        save_analysis_as_markdown(session_id, command_output, analysis)

def auto_mode(session_id, ip, prompt_template, llm_server_url, headers, error_count_limit):
    history_file = os.path.join(SESSION_LOG_DIR, f"{session_id}_history.json")
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            history = json.load(file)
    else:
        history = []

    command_str = f"nmap -p 1-100 {ip}"
    error_count = 0

    while command_str:
        command_output = run_command(command_str)
        if "Error" in command_output:
            error_count += 1
            if error_count >= error_count_limit:
                print(f"{Fore.RED}Error limit reached. Exiting auto mode.{Style.RESET_ALL}")
                logging.error("Error limit reached. Exiting auto mode.")
                break

        analysis = analyze_output(command_output, history, prompt_template, llm_server_url, headers)
        if "Error" in analysis:
            error_count += 1
            if error_count >= error_count_limit:
                print(f"{Fore.RED}Error limit reached. Exiting auto mode.{Style.RESET_ALL}")
                logging.error("Error limit reached. Exiting auto mode.")
                break

        # Save history
        with open(history_file, 'w') as file:
            json.dump(history, file)

        print_output(command_output, analysis)
        log_history(session_id, command_str, command_output, analysis)
        save_analysis_as_markdown(session_id, command_output, analysis)

        command_str = extract_next_command(analysis)
        if command_str:
            print(f"{Fore.YELLOW}Next command suggested by LLM:{Style.RESET_ALL} {command_str}")
        else:
            print(f"{Fore.RED}No further command suggested by LLM. Exiting auto mode.{Style.RESET_ALL}")
            break

def main():
    parser = argparse.ArgumentParser(description='Run a command and analyze the output with an LLM.')
    parser.add_argument('command', help='Command to run', nargs='*')
    parser.add_argument('--session-id', help='Session ID for logging')
    parser.add_argument('--review', help='Review session log', action='store_true')
    parser.add_argument('--interactive', help='Start interactive mode', action='store_true')
    parser.add_argument('--auto', help='Start auto mode', action='store_true')
    parser.add_argument('--config', help='Path to configuration file', default=DEFAULT_CONFIG_FILE)
    parser.add_argument('--commands-file', help='Path to a file with a list of commands to execute sequentially')
    parser.add_argument('--ip', help='IP address to replace in commands file or for auto mode')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    llm_server_url = config['LLM_SERVER_URL']
    headers = config['HEADERS']
    prompt_template = config['PROMPT_TEMPLATE']
    error_count_limit = config.get('ERROR_COUNT_LIMIT', 3)

    # Generate session ID if not provided
    if not args.session_id:
        session_id = generate_session_id()
    else:
        session_id = args.session_id

    if args.review:
        log_file = os.path.join(SESSION_LOG_DIR, f"{session_id}.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as log:
                print(log.read())
        else:
            print(f"No log found for session ID: {session_id}")
            logging.warning(f"No log found for session ID: {session_id}")
    elif args.command:
        command_str = ' '.join(args.command)
        command_output = run_command(command_str)
        
        # Ensure the session log directory exists
        if not os.path.exists(SESSION_LOG_DIR):
            os.makedirs(SESSION_LOG_DIR)
        
        # Initialize or load history
        history_file = os.path.join(SESSION_LOG_DIR, f"{session_id}_history.json")
        if os.path.exists(history_file):
            with open(history_file, 'r') as file:
                history = json.load(file)
        else:
            history = []

        analysis = analyze_output(command_output, history, prompt_template, llm_server_url, headers)

        # Save history
        with open(history_file, 'w') as file:
            json.dump(history, file)

        print_output(command_output, analysis)
        log_history(session_id, command_str, command_output, analysis)
        save_analysis_as_markdown(session_id, command_output, analysis)
    elif args.interactive:
        interactive_mode(session_id, prompt_template, llm_server_url, headers)
    elif args.auto:
        if args.ip:
            auto_mode(session_id, args.ip, prompt_template, llm_server_url, headers, error_count_limit)
        else:
            print("IP address must be provided for auto mode.")
            logging.error("IP address must be provided for auto mode.")
    elif args.commands_file:
        if args.ip:
            if os.path.exists(args.commands_file):
                with open(args.commands_file, 'r') as file:
                    commands = file.readlines()
                for command in commands:
                    command_str = command.strip().replace(IP_PLACEHOLDER, args.ip)
                    if command_str:
                        command_output = run_command(command_str)
                        
                        # Ensure the session log directory exists
                        if not os.path.exists(SESSION_LOG_DIR):
                            os.makedirs(SESSION_LOG_DIR)
                        
                        # Initialize or load history
                        history_file = os.path.join(SESSION_LOG_DIR, f"{session_id}_history.json")
                        if os.path.exists(history_file):
                            with open(history_file, 'r') as file:
                                history = json.load(file)
                        else:
                            history = []

                        analysis = analyze_output(command_output, history, prompt_template, llm_server_url, headers)

                        # Save history
                        with open(history_file, 'w') as file:
                            json.dump(history, file)

                        print_output(command_output, analysis)
                        log_history(session_id, command_str, command_output, analysis)
                        save_analysis_as_markdown(session_id, command_output, analysis)
            else:
                print(f"Commands file not found: {args.commands_file}")
                logging.error(f"Commands file not found: {args.commands_file}")
        else:
            print("IP address must be provided with the commands file.")
            logging.error("IP address must be provided with the commands file.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
