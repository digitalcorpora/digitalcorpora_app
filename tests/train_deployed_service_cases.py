import requests
import json
import os

CASES_PATH = os.path.join(os.path.dirname(__file__), 'deployed_service_cases.json')

def load_cases():
    if os.path.exists(CASES_PATH):
        with open(CASES_PATH, 'r') as f:
            return json.load(f)
    return []

def save_cases(cases):
    with open(CASES_PATH, 'w') as f:
        json.dump(cases, f, indent=4)

def main():
    print("Training program for deployed service test cases.")
    cases = load_cases()
    while True:
        url = input("Enter a URL to test (or 'q' to quit): ").strip()
        if url.lower() == 'q':
            break
        try:
            response = requests.get(url, allow_redirects=False, timeout=10, verify=True)
            print(f"Status code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            is_redirect = response.is_redirect or response.is_permanent_redirect
            print(f"Redirect: {is_redirect}")
            if is_redirect:
                location = response.headers.get('Location')
                print(f"Redirect Location: {location}")
                # Optionally, follow the redirect
                follow = input("Follow redirect and show final response? (y/n): ").strip().lower()
                if follow == 'y' and location:
                    response2 = requests.get(location, allow_redirects=True, timeout=10, verify=True)
                    print(f"Final Status code: {response2.status_code}")
                    print(f"Final Headers: {dict(response2.headers)}")
                    response = response2
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue
        add = input("Add this as a test case? (y/n): ").strip().lower()
        if add != 'y':
            continue
        # Extract Content-Length and Content-Type
        content_length = response.headers.get('Content-Length')
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        print(f"Detected Content-Length: {content_length}")
        print(f"Detected MIME type: {content_type}")
        # Allow user to override or accept
        length_input = input(f"Expected Content-Length [{content_length}]: ").strip()
        if length_input:
            try:
                length = int(length_input)
            except ValueError:
                print("Invalid length. Skipping.")
                continue
        else:
            try:
                length = int(content_length)
            except (TypeError, ValueError):
                print("No valid Content-Length detected. Skipping.")
                continue
        mime_input = input(f"Expected MIME type [{content_type}]: ").strip()
        mime = mime_input if mime_input else content_type
        direct = input(f"Served directly (not a redirect)? (y/n) [{'y' if not is_redirect else 'n'}]: ").strip().lower()
        if direct == '':
            direct = not is_redirect
        else:
            direct = (direct == 'y')
        case = {
            "url": url,
            "expect": {
                "type": "file",
                "length": length,
                "mime": mime,
                "direct": direct
            }
        }
        cases.append(case)
        save_cases(cases)
        print("Test case added!\n")

if __name__ == '__main__':
    main() 