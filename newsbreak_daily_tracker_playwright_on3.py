from playwright.sync_api import sync_playwright
import pandas as pd
import json
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread


def initialize_browser(headless=True):
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return playwright, browser, context, page

def perform_login(page: object, email: str, password: str):
    response = page.goto("https://mp.newsbreak.com/login")
    assert response.ok
    page.get_by_placeholder("Your email address").fill(email)
    page.get_by_placeholder("Your password").fill(password)
    page.locator('button.ant-btn.ant-btn-primary.Button.button-continue').click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)

def get_yesterday_metrics(page):
    page.locator("a[href='/home/analytics']").click()
    page.wait_for_timeout(3000)

    local_storage = page.evaluate('() => Object.entries(localStorage)')
    root_state_json = None
    for key, value in local_storage:
        if key == "rootState":
            root_state_json = value
            break

    if root_state_json:
        print("Data are loaded")
        root_state_dict = json.loads(root_state_json)
    else:
        raise ValueError("rootState not found in localStorage.")

    user_info = root_state_dict.get("app", {}).get("userInfo", {})
    account = user_info.get("account")

    daily_trending_metrics = root_state_dict.get("analytics", {}).get("accountStats", {}).get("dailyTrending", [])
    yesterday = "2025-12-09"#(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_metrics = {}

    for metrics in daily_trending_metrics:
        if metrics.get("date") == yesterday:
            print(metrics)
            yesterday_metrics = metrics
            break

    try:
        #custom_date = "2025-05-18"#datetime.strptime(yesterday_metrics.get("date"), "%Y-%m-%d").strftime("%d/%m/%y")1
        #formatted_date = datetime.strptime(custom_date, "%Y-%m-%d").date()
        formatted_date = datetime.strptime(yesterday, "%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception as e:
        formatted_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")

    print(account)
    if account != "--":
        df = pd.DataFrame(
            [[
                account,
                formatted_date,
                yesterday_metrics.get("impression", 0),
                yesterday_metrics.get("page_view", 0),
                yesterday_metrics.get("like", 0),
                yesterday_metrics.get("follower", 0),
                yesterday_metrics.get("comment", 0),
                yesterday_metrics.get("in_app_page_view", 0),
                yesterday_metrics.get("share", 0),
                yesterday_metrics.get("register_follower", 0)
            ]],
            columns=[
                "Publisher name",
                "Date",
                "Impressions",
                "Pageviews",
                "Likes",
                "Followers",
                "Comments",
                "In app pageviews",
                "Shares",
                "Register followers"
            ]
        )
        return df
    else:
        return None

def iterate_publishers_and_get_metrics(page, sheet_id, worksheet_name):
    page.goto("https://mp.newsbreak.com/home/account_setting", wait_until='networkidle')
    page.wait_for_timeout(5000)

    # get last publisher
    publisher_names = page.locator(".profile_name .profile_val")
    publisher_names.nth(-1).click()
    page.wait_for_timeout(8000)

    page.goto("https://mp.newsbreak.com/home/account_setting", wait_until='networkidle')
    page.wait_for_timeout(5000)

    yesterday_metrics_df = get_yesterday_metrics(page)
    print(f"Yesterday metrics for publisher last publisher: {yesterday_metrics_df}")

    if yesterday_metrics_df is not None:
        append_data_to_google_sheet(yesterday_metrics_df, sheet_id, worksheet_name)

    page.goto("https://mp.newsbreak.com/home/account_setting", wait_until='networkidle')
    page.wait_for_timeout(5000)

    publisher_names = page.locator(".profile_name .profile_val")
    publisher_names.nth(0).click()
    page.wait_for_timeout(8000)

    page.goto("https://mp.newsbreak.com/home/account_setting", wait_until='networkidle')
    page.wait_for_timeout(5000)

    publisher_names = page.locator(".profile_name .profile_val")

    page.wait_for_timeout(5000)
    publisher_names.nth(0).click()
    page.wait_for_timeout(5000)
    yesterday_metrics_df = get_yesterday_metrics(page)
    print(f"Yesterday metrics for first publisher: {yesterday_metrics_df}")

    if yesterday_metrics_df is not None:
        append_data_to_google_sheet(yesterday_metrics_df, sheet_id, worksheet_name)

    '''page.goto("https://mp.newsbreak.com/home/account_setting", wait_until='networkidle')
    page.wait_for_timeout(5000)

    publisher_names = page.locator(".profile_name .profile_val")
    count = publisher_names.count()
    print(count)

    for i in range(count):
        #breakpoint()
        publisher_names.nth(i).click()
        page.wait_for_timeout(3000)

        yesterday_metrics_df = get_yesterday_metrics(page)
        print(f"Yesterday metrics for publisher {i + 1}: {yesterday_metrics_df}")

        if yesterday_metrics_df is not None:
            append_data_to_google_sheet(yesterday_metrics_df, sheet_id, worksheet_name)

        page.goto("https://mp.newsbreak.com/home/account_setting", wait_until='networkidle')
        page.wait_for_timeout(5000)'''

def load_data_from_google_sheet(sheet_id: str, worksheet_name: str) -> pd.DataFrame:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('sage-buttress-313618-6feaaa015949.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame([data])
    return df

def append_data_to_google_sheet(df: pd.DataFrame, sheet_id: str, worksheet_name: str):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('sage-buttress-313618-6feaaa015949.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    #if "Date" in df.columns:
    #    df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.date  # ISO date format

    for _, row in df.iterrows():
        row_list = row.values.tolist()

        if "Date" in df.columns:
            date_index = df.columns.get_loc("Date")
            date_value = row_list[date_index]

            try:
                date_obj = datetime.strptime(date_value, "%Y-%m-%d")
                row_list[date_index] = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                pass

        sheet.append_row(row_list, value_input_option="USER_ENTERED")
        #sheet.append_row(row.values.tolist())

def main():
    email = 'team@nordot.io'#os.getenv("MSN_EMAIL")
    password = 'Nordot@123$'#os.getenv("MSN_PASSWORD")

    if not email or not password:
        print("Email and password must be set in the environment variables.")
        return

    sheet_id = "16zk_PpT3LBWaQDYKFPdF3BZZgrOjHqnj6pUiC5stR5k"
    worksheet_name = "Newsbreak"

    playwright, browser, context, page = initialize_browser(headless=False)
    try:
        perform_login(page, email, password)
        iterate_publishers_and_get_metrics(page, sheet_id, worksheet_name)

    finally:
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    main()
