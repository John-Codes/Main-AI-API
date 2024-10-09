import os
import sys

try:
    from dotenv import load_dotenv
    import requests
except ImportError as e:
    print(f"Error: {e}")
    print("This script requires the 'python-dotenv' and 'requests' libraries.")
    print("Please install them using pip:")
    print("pip install python-dotenv requests")
    sys.exit(1)

# Load environment variables
load_dotenv()

def bing_search(query, count=10):
    api_key = os.getenv('BING_API_KEY')
    if not api_key:
        raise ValueError("BING_API_KEY not found in .env file")
    
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "count": count,
        "textFormat": "HTML"
    }
    
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error making request to Bing API: {e}")
        sys.exit(1)

def process_results(results):
    processed = []
    for result in results.get('webPages', {}).get('value', []):
        processed.append({
            'name': result.get('name', 'No title'),
            'url': result.get('url', 'No URL'),
            'snippet': result.get('snippet', 'No snippet available')
        })
    return processed

def main():
    query = input("Enter your search query: ")
    results = bing_search(query)
    processed_results = process_results(results)
    
    if not processed_results:
        print("No results found.")
        return

    print(f"\nSearch results for '{query}':\n")
    for i, result in enumerate(processed_results, 1):
        print(f"{i}. {result['name']}")
        print(f"   URL: {result['url']}")
        print(f"   Snippet: {result['snippet']}\n")

if __name__ == "__main__":
    main()