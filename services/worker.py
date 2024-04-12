import os, pytz, logging, mechanicalsoup, datetime, time, schedule, base64
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from services.database import get_db_connection

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
fernet = Fernet(os.getenv("FERNET_KEY"))


def reissue_books(username, password):
    browser = mechanicalsoup.StatefulBrowser()
    url = "http://14.139.108.229/W27/login.aspx"

    browser.open(url)
    browser.get_current_page()
    browser.select_form()
    browser.get_current_form()

    browser["txtUserName"] = username
    browser["Password1"] = password

    browser.submit_selected()

    new_url = "http://14.139.108.229/W27/MyInfo/w27MyInfo.aspx"
    browser.open(new_url)

    page = browser.get_current_page()
    table = page.find_all(
        "table", attrs={"id": "ctl00_ContentPlaceHolder1_CtlMyLoans1_grdLoans"}
    )

    if table:
        tds = table[0].find_all("td")
        book_data = []
        for td in tds:
            book_data.append(td.text.replace("\n", ""))

        no_of_book_issued = int(len(book_data) / 9)
        print(no_of_book_issued)
    else:
        return

    num_columns = 9
    data_rows = [
        book_data[i : i + num_columns] for i in range(0, len(book_data), num_columns)
    ]
    print(data_rows)
    reissue_btns = table[0].find_all("input")
    issue_book_btn = []
    for btn in reissue_btns:
        issue_book_btn.append(btn.attrs["name"])

    indian_current_date = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).date()

    for data_row, reissue_btn in zip(data_rows, issue_book_btn):
        due_date_str = data_row[4]
        due_date = datetime.datetime.strptime(due_date_str.strip(), "%d-%b-%Y").date()

        if due_date <= indian_current_date:
            # browser.select_form('form[action="./w27MyInfo.aspx"]')
            # browser.submit_selected(btnName=reissue_btn)
            print("Book Reissued: ", data_row[1])

    current_utc_datetime = datetime.datetime.now(datetime.timezone.utc)
    ist_timezone = pytz.timezone("Asia/Kolkata")
    current_date = current_utc_datetime.astimezone(ist_timezone).strftime("%Y-%m-%d")
    with open("status.txt", "w") as file:
        file.write(current_date)

    with open("log.txt", "a") as file:
        file.write(str(datetime.datetime.now()) + "\n")


def fetch_data_from_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return users
    except Exception as e:
        print(e)
        logger.error(f"Error fetching data from database: {e}")
        return None


def worker():
    user_data = fetch_data_from_database()
    for user in user_data:
        print(user[3], user[4])
        reissue_books(user[3], user[4])


schedule.every().day.at("03:00").do(worker)  # Adjust the time as needed

while True:
    schedule.run_pending()
    time.sleep(1)
