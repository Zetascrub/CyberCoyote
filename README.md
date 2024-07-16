<p align="center">
  <img src="./Logo.png" alt="CyberCoyote Logo" width="500" height="400">
</p>

# CyberCoyote

CyberCoyote is a Linux command-line tool designed to automate the process of running penetration testing commands and analyzing their output using a Language Model (LLM) hosted via Text Generation Web UI. The tool helps penetration testers to better understand the output of their commands and suggests the next steps based on the context provided.

## Warning

This tool is very much still in development.

## Pre-requesits
Have the following installed with APIs enabled: [https://github.com/oobabooga/text-generation-webui]


## Features

- Run a command and analyze its output using an LLM.
- Automatically suggest and run the next command based on the analysis.
- Interactive mode for manually entering commands.
- Review session logs.
- Error handling with retry mechanism and configurable error limit.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/CyberCoyote.git
    cd CyberCoyote
    ```

2. Ensure you have the necessary dependencies:
    - Python 3.x
    - `requests` library
    - `colorama` library
    - `markdown2` library

    You can install the required Python libraries using pip:
    ```bash
    pip install requests colorama markdown2
    ```

3. Update the `config.json` file with your LLM server URL and other configurations.

## Configuration

The `config.json` file contains the following configurations:

```json
{
    "LLM_SERVER_URL": "http://192.168.0.0:5000/v1/chat/completions",
    "HEADERS": {
        "Content-Type": "application/json"
    },
    "PROMPT_TEMPLATE": "Based on the following command output, please provide the next command to run in this penetration test. Format the response as follows:\n\nNext command:\n<command>\n\nExplanation:\n<explanation>\n\nCommand output:\n",
    "ERROR_COUNT_LIMIT": 3
}
```

Usage
Run a Command
```bash
./CyberCoyote.sh --session-id <session_id> "<command>"
```

Example:

```bash
./CyberCoyote.sh --session-id 12345 "nmap -p 1-100 192.168.0.1"
```
Review a Session Log
```bash
./CyberCoyote.sh --session-id <session_id> --review
```
Example:

```bash
./CyberCoyote.sh --session-id 12345 --review
```

Interactive Mode
```bash
./CyberCoyote.sh --session-id <session_id> --interactive
```
Example:

```bash
./CyberCoyote.sh --session-id 12345 --interactive
```
Auto Mode
```bash
./CyberCoyote.sh --session-id <session_id> --auto --ip <target_ip>
```
Example:

```bash
./CyberCoyote.sh --session-id 12345 --auto --ip 192.168.0.1
```
Execute Commands from a File with IP Replacement
```bash
./CyberCoyote.sh --session-id <session_id> --commands-file <file_path> --ip <target_ip>
```
Example:

```bash
./CyberCoyote.sh --session-id 12345 --commands-file commands.txt --ip 192.168.0.1
```
Contributing
Contributions are welcome! Please feel free to submit a Pull Request or open an issue.

License
This project is licensed under the MIT License.

Contact
For any questions or issues, please contact [Thomas.e.odonnell@gmail.com].

