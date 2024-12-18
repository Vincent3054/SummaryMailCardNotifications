import imaplib
import email
from email.header import decode_header
import re

# 信箱設置
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "xxx@gmail.com"  # 你的信箱
PASSWORD = "xxxx"      # 你的應用程式專用密碼

# 信用卡郵件過濾條件
SEARCH_KEYWORDS = "2309"  # 假設郵件標題含有這些字
DATE_SINCE = "12-Dec-2024"  # 開始日期 (含該日)
DATE_BEFORE = "18-Dec-2024" # 結束日期 (不含該日)

def clean_text(text):
    """處理郵件主體，轉換為可讀文字"""
    if isinstance(text, bytes):
        return text.decode('utf-8', errors='ignore')
    return text

def extract_amount_and_time(body):
    """從郵件內容中提取金額與時間"""
    amounts = re.findall(r'[\d,]+\.\d{2}', body)  # 提取金額格式如 1,234.56
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', body)  # 提取日期格式如 2024-01-01
    return amounts, dates

def encode_utf7(string):
    """將字串轉換為 IMAP 支援的 UTF-7 編碼"""
    return string.encode("utf-7").decode()

def fetch_credit_card_emails():
    """連接信箱並提取信用卡通知信中的金額與時間"""
    total_amount = 0.0
    transactions = []

    # 連接到 IMAP 伺服器
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select("inbox")

    # 搜尋符合條件的郵件：標題包含特定字詞且日期範圍內
    search_subject = f'SUBJECT "{SEARCH_KEYWORDS}"'
    search_criteria = f'({search_subject} SINCE "{DATE_SINCE}" BEFORE "{DATE_BEFORE}")'
    search_criteria_utf7 = encode_utf7(search_criteria)  # 編碼為 UTF-7
    status, messages = mail.search(None, search_criteria_utf7)
    if status != "OK":
        print("No messages found!")
        return

    email_ids = messages[0].split()

    # 處理每封郵件
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                print(f"Processing email: {subject}")

                # 讀取郵件內容
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body = clean_text(part.get_payload(decode=True))
                            amounts, dates = extract_amount_and_time(body)
                            for amount, date in zip(amounts, dates):
                                amount_value = float(amount.replace(",", ""))
                                transactions.append({"date": date, "amount": amount_value})
                                total_amount += amount_value
                else:
                    body = clean_text(msg.get_payload(decode=True))
                    amounts, dates = extract_amount_and_time(body)
                    for amount, date in zip(amounts, dates):
                        amount_value = float(amount.replace(",", ""))
                        transactions.append({"date": date, "amount": amount_value})
                        total_amount += amount_value

    # 關閉連接
    mail.close()
    mail.logout()

    # 輸出結果
    print("\n--- 信用卡消費明細 ---")
    for transaction in transactions:
        print(f"時間: {transaction['date']}, 金額: {transaction['amount']}")
    print(f"\n總金額: {total_amount:.2f}")

if __name__ == "__main__":
    fetch_credit_card_emails()
