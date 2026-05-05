from datetime import datetime, timedelta
import os, sys
import base64


def add_months(date, months):
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1

    days_in_month = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    ]

    day = min(date.day, days_in_month[month - 1])
    return date.replace(year=year, month=month, day=day)


def create_expiration(option):
    now = datetime.now()
    options = {
        "1": timedelta(hours=1),
        "2": timedelta(days=1),
        "3": timedelta(days=7),
        "4": timedelta(days=15)
    }
    month_options = {
        "5": 1,
        "6": 2,
        "7": 3,
        "8": 12,
    }

    if option in options:
        expire = now + options[option]

    elif option in month_options:
        expire = add_months(now, month_options[option])

    else:
        return None

    return expire.strftime("%M-%H-%d-%m-%Y")

def Line():
    print(f"-\033[1;00m"*os.get_terminal_size()[0])

def menu():
    os.system('clear')
    Line()
    print("[1] 1 Hour")
    print("[2] 1 Day")
    print("[3] 7 Days")
    print("[4] 15 Days")
    print("[5] 1 Month")
    print("[6] 2 Months")
    print("[7] 3 Months")
    print("[8] 1 Year")
    Line()
    choice = input("\033[1;32m[+] Enter Option: ").strip()
    if not choice in ['1','2','3','4','5','6','7','8']:
        Line()
        print("\033[1;31m[x] Invalid Option")
        sys.exit(0)
    Line()
    appID = input("\033[1;32m[+] Enter the client app ID: ")
    try:
        uid = base64.b16decode(appID[2:-3]).decode()
    except:
        Line()
        print("\033[1;31m[x] Invalid Key")
        sys.exit(0)
    if len(uid) <= 8:
        Line()
        print("\033[1;31m[x] Invalid Key")
        sys.exit(0)
    result = create_expiration(choice)
    Line()
    print(f"\033[1;32m[+] Generated Key: {uid+'@'+result}")
    
if __name__ == "__main__":
    menu()