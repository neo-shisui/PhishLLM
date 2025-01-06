import requests
import urllib3
import json

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read the API key from a file (OpenAI.txt in the same directory)
with open("OpenAI.txt", "r") as file:
    api_key = file.read().strip()

# Define the headers for the request
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Define the data payload for the request
data = {
    "model": "gpt-4o-mini",  # Change to the appropriate model you want to use
    "messages": [
        {
            "role": "system",
            "content": "You are an expert in webpage design. Given the webpage content, your task is to decide the status of the webpage."
        },
        {
            "role": "user",
            "content": (
                "A credential-requiring page is where the users are asked to fill in their sensitive information, including usernames, passwords; "
                "contact details such as addresses, phone numbers, emails, and financial information such as credit card numbers, social security numbers, etc.\n\n"
                "Given the webpage text: 'MAX BOUNTY Affiliate Login: Email address Password Sign in'. "
                "Question: A. This is a credential-requiring page. B. This is not a credential-requiring page. "
                "Answer: 'First we filter the keywords that are related to sensitive information: Email address, Password. "
                "After that we find the keywords that are related to login: Sign in, Login. Therefore the answer would be A'.\n\n"
                "Given the webpage content: 'M indiamart Shopping Sign In v Search for products find verified sellers near you 9 All India X Q Search Sign In Email ID Enter your Email ID', "
                "Question: A. This is a credential-requiring page. B. This is not a credential-requiring page. Answer:"
            )
        }
    ]
}

print("[*] GPT 4o-mini:")
print("  [+] Given the webpage content: ")
print("      'M indiamart Shopping Sign In v Search for products find verified sellers near you 9 All India X Q Search Sign In Email ID Enter your Email ID', ")
print("  [+] Question: A. This is a credential-requiring page. B. This is not a credential-requiring page. Answer:")

char = input("")  # Takes only the first character

# Send the POST request
response = requests.post(
    url="https://api.openai.com/v1/chat/completions",
    headers=headers,
    json=data,
    verify=False  # Disable SSL verification (use with caution in production)
)

# Parse and print the response
if response.status_code == 200:
    print("[*] Original answer:")
    print("    ", response.json()["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code}, {response.text}")

# Intercept the POST request
char = input("")
print("")
response = requests.post(
    url="https://api.openai.com/v1/chat/completions",
    headers=headers,
    json=data,
    verify=False  # Disable SSL verification (use with caution in production)
)

# Parse and print the response
if response.status_code == 200:
    print("[*] Output integrity attack:")
    print("    ", response.json()["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code}, {response.text}")
