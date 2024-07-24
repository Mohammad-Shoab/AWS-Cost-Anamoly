import requests

def send_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Request to {url} successful")
        else:
            print(f"Request to {url} failed with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request to {url} failed: {e}")

def main():
    urls = [
        "https://aws-cost.internal.mum1.zetaapps.in/usage/clear_usage_cache",
        "https://aws-cost.internal.mum1.zetaapps.in/clear_cache",
        "https://aws-cost.internal.mum1.zetaapps.in/data",
        "https://aws-cost.internal.mum1.zetaapps.in/weekly",
        "https://aws-cost.internal.mum1.zetaapps.in/monthly",
        "https://aws-cost.internal.mum1.zetaapps.in/daily_service/",
        "https://aws-cost.internal.mum1.zetaapps.in/weekly_service/",
        "https://aws-cost.internal.mum1.zetaapps.in/monthly_service/",
        "https://aws-cost.internal.mum1.zetaapps.in/usage/weekly_monthly_index?data_type=weekly",
        "https://aws-cost.internal.mum1.zetaapps.in/usage/weekly_monthly_index?data_type=monthly"
    ]

    for url in urls:
        send_request(url)

if __name__ == "__main__":
    main()
