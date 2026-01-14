import requests
import concurrent.futures
import time

URL = "http://127.0.0.1:8000/buy_ticket"
WORKERS = 50
TOTAL_REQUESTS = 200

CLIENT_RETRIES = 2
RETRY_DELAY = 0.05  # seconds


def attempt_purchase(i):
    """
    Attempt a purchase with client-side retry on 503.
    """
    for attempt in range(CLIENT_RETRIES + 1):
        try:
            response = requests.post(URL, timeout=3)

            # Success or sold out are final states
            if response.status_code in (200, 410):
                return response.status_code

            # Retry on transient contention
            if response.status_code == 503 and attempt < CLIENT_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** attempt))
                continue

            return response.status_code

        except requests.RequestException as e:
            return f"Error: {e}"


def main():
    print(f"Starting {TOTAL_REQUESTS} requests with {WORKERS} concurrent workers...")
    start_time = time.time()

    status_codes = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(attempt_purchase, i) for i in range(TOTAL_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            status_codes.append(future.result())

    duration = time.time() - start_time
    print(f"Finished in {duration:.2f} seconds.")

    success_count = status_codes.count(200)
    sold_out_count = status_codes.count(410)
    busy_count = status_codes.count(503)
    errors = [s for s in status_codes if s not in (200, 410, 503)]

    print("-" * 40)
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Successful Buys (200 OK): {success_count}")
    print(f"Sold Out Responses (410 GONE): {sold_out_count}")
    print(f"Busy / Timeout Responses (503): {busy_count}")
    print(f"Errors: {len(errors)} {errors if errors else ''}")
    print("-" * 40)

    # Correctness checks
    if success_count == 100:
        print("✅ SUCCESS: Exactly 100 items sold.")
    elif success_count > 100:
        print("❌ FAILURE: Oversold! (Stock was 100)")
    else:
        print(f"❌ FAILURE: Undersold? Only {success_count} sold.")

    if errors:
        print("⚠️ Warnings: Unexpected errors occurred.")


if __name__ == "__main__":
    time.sleep(2)
    main()
