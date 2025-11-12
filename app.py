import os
import smtplib
import time
import re
import urllib.parse
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# -------------------------
# CHROME / SELENIUM SETUP
# -------------------------
chrome_options = Options()
chrome_options.add_argument("headless")
chrome_options.add_argument("no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
time.sleep(1)

# -------------------------
# EXCLUDE & INCLUDE FILTERS
# -------------------------
EXCLUDE_KEYWORDS = [
    "php","laravel","wordpress","drupal",".net","c#","java","spring","hibernate",
    "senior","lead","manager","architect","3 year","3 years","4 year","4 years",
    "5 year","5 years","5+","6 year","6 years","10 year"
]
EXCLUDE_LOWER = [e.lower() for e in EXCLUDE_KEYWORDS]

# Accept if these fresher terms appear (optional, not mandatory)
PREFER_TERMS = [
    "fresher","freshers","intern","internship","trainee","entry level",
    "0-1","0 - 1","0-2","0 - 2","0 to 2","1 year","below 2"
]
PREFER_LOWER = [p.lower() for p in PREFER_TERMS]

# Main inclusion list for relevant jobs
INCLUDE_TERMS = [
    "python","django","flask","fastapi","react","angular","vue","javascript",
    "typescript","full stack","backend","frontend","web developer",
    "machine learning","ml","ai","artificial intelligence",
    "data science","data scientist","data analyst","analytics","business intelligence",
    "power bi","tableau","excel","sql","dashboard","bi developer",
    "visualization","data engineer","deep learning","nlp","llm"
]

# -------------------------
# FILTER FUNCTION
# -------------------------
def looks_relevant(title, snippet=""):
    text = (title + " " + snippet).lower()

    if any(ex in text for ex in EXCLUDE_LOWER):
        return False

    if not any(term in text for term in INCLUDE_TERMS):
        return False

    # Exclude if mentions "senior"/"lead"/"manager"/"5 years+"
    if re.search(r"\b(senior|lead|manager|architect|5\s*\+?\s*years?)\b", text):
        return False

    # Prefer fresher jobs but not mandatory
    if any(t in text for t in PREFER_LOWER):
        return True

    # If no years mentioned, assume entry-level acceptable
    if not re.search(r"\b[3-9]\s*(year|years|yrs|yr)\b", text):
        return True

    return False


# -------------------------
# NORMALIZE / DEDUP
# -------------------------
def normalize_job(job):
    return {
        "title": job.get("title","").strip(),
        "company": job.get("company","").strip(),
        "link": job.get("link","").strip()
    }

def dedupe_jobs(jobs):
    seen, unique = set(), []
    for j in jobs:
        key = (j.get("title","").lower(), j.get("company","").lower())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique


# -------------------------
# SCRAPING FUNCTIONS
# -------------------------
def fetch_infopark_jobs(pages=3):
    jobs = []
    for page in range(1, pages+1):
        url = f"https://infopark.in/companies/job-search?page={page}"
        driver.get(url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("table tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            title = cols[1].text.strip()
            company = cols[2].text.strip()
            link_el = row.find("a", href=True)
            job_link = link_el["href"] if link_el else ""
            if not job_link.startswith("http"):
                job_link = "https://infopark.in" + job_link
            if looks_relevant(title):
                jobs.append({"title": title, "company": company, "link": job_link})
    return jobs

def fetch_technopark_jobs(pages=3):
    jobs = []
    for page in range(1, pages+1):
        url = f"https://technopark.in/job-search?page={page}"
        driver.get(url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("table tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            title = cols[1].text.strip()
            company = cols[2].text.strip()
            link_el = row.find("a", href=True)
            job_link = link_el["href"] if link_el else ""
            if not job_link.startswith("http"):
                job_link = "https://technopark.in" + job_link
            if looks_relevant(title):
                jobs.append({"title": title, "company": company, "link": job_link})
    return jobs

def fetch_cyberpark_jobs():
    jobs = []
    url = "https://cyberparks.in/careers"
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("a[href*='job'], a[href*='career'], .job-card, .career-item")
    for card in cards:
        title = card.text.strip()
        company = "Cyberpark"
        link = card["href"] if card.has_attr("href") else ""
        if not link.startswith("http"):
            link = "https://cyberparks.in" + link
        if looks_relevant(title):
            jobs.append({"title": title, "company": company, "link": link})
    return jobs

def fetch_smartcity_jobs():
    jobs = []
    url = "https://smartcitykochi.in/careers"
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    items = soup.select("a[href*='job'], a[href*='career'], .job-card, .career-listing")
    for i in items:
        title = i.text.strip()
        link = i["href"] if i.has_attr("href") else ""
        if not link.startswith("http"):
            link = "https://smartcitykochi.in" + link
        if looks_relevant(title):
            jobs.append({"title": title, "company": "SmartCity Kochi", "link": link})
    return jobs

def fetch_tidelpark_jobs():
    jobs = []
    url = "https://www.tidelpark.com/careers"
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for a in soup.select("a[href*='career'], a[href*='job']"):
        title = a.text.strip()
        if looks_relevant(title):
            jobs.append({"title": title, "company": "TIDEL Park Chennai", "link": a['href']})
    return jobs

def fetch_stpi_jobs():
    jobs = []
    url = "https://www.stpi.in/career"
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for a in soup.select("a[href*='job'], a[href*='career']"):
        title = a.text.strip()
        if looks_relevant(title):
            jobs.append({"title": title, "company": "STPI India", "link": a['href']})
    return jobs


def fetch_all_jobs():
    jobs = []
    jobs += fetch_infopark_jobs()
    jobs += fetch_technopark_jobs()
    jobs += fetch_cyberpark_jobs()
    jobs += fetch_smartcity_jobs()
    jobs += fetch_tidelpark_jobs()
    jobs += fetch_stpi_jobs()
    jobs = [normalize_job(j) for j in jobs]
    jobs = dedupe_jobs(jobs)
    return jobs


# -------------------------
# EMAIL SECTION (UNCHANGED)
# -------------------------
def send_email(jobs):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    recipients = [x.strip() for x in os.getenv("EMAIL_TO", "").split(",") if x.strip()]
    raw_names = os.getenv("STUDENT_NAMES", "")
    student_names = [
        x.strip() for x in raw_names.replace("\r", "").replace("\n", "").replace(" ,", ",").replace(", ", ",").split(",") if x.strip()
    ]
    tracker_url = os.getenv("TRACKER_URL")

    subject = f"Acadeno Technologies | Latest Python & Data Jobs – {datetime.now().strftime('%d %b %Y')}"
    logo_url = "https://drive.google.com/uc?export=view&id=1wLdjI3WqmmeZcCbsX8aADhP53mRXthtB"

    for index, student_email in enumerate(recipients):
        student_name = student_names[index] if index < len(student_names) else "Student"
        html = f"""
        <html>
        <body style="font-family:Arial, sans-serif; background:#f4f8f5; padding:25px;">
        <div style="background:linear-gradient(90deg,#5B00C2,#FF6B00);padding:25px;border-radius:15px;color:white;text-align:center;">
            <img src="{logo_url}" alt="Acadeno Logo" style="width:120px;height:auto;margin-bottom:12px;border-radius:10px;">
            <h2 style="margin:0;">Acadeno Technologies Private Limited</h2>
        </div>
        <div style="background:white;padding:25px;border-radius:12px;margin-top:25px;">
            <p>Dear <b style="color:#5B00C2;">{student_name}</b>,</p>
            <p>Here are the latest <b>Python / Data / AI / ML / Analytics</b> opportunities across India (fresher & below 2 years):</p>
        """

        for job in jobs:
            safe_link = urllib.parse.quote(job['link'], safe='')
            safe_title = urllib.parse.quote(job['title'], safe='')
            safe_email = urllib.parse.quote(student_email, safe='')
            tracking_link = f"{tracker_url}?email={safe_email}&job={safe_title}&link={safe_link}"
            html += f"""
            <div style="border:1px solid #ddd;border-radius:10px;padding:15px;margin-bottom:15px;">
                <h3 style="color:#5B00C2;margin:0;">{job['title']}</h3>
                <p>🏢 {job['company']}</p>
                <a href="{tracking_link}" style="background:linear-gradient(90deg,#FF6B00,#5B00C2);color:white;padding:10px 18px;text-decoration:none;border-radius:6px;font-weight:bold;">🔗 View & Apply</a>
            </div>
            """
        html += "</div></body></html>"

        msg = MIMEMultipart("alternative")
        msg["From"] = sender
        msg["To"] = student_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        print(f"✅ Email sent to {student_name} ({student_email})")


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    jobs = fetch_all_jobs()
    driver.quit()
    if jobs:
        df = pd.DataFrame(jobs)
        df.drop_duplicates(subset=["title", "company"], inplace=True)
        df.to_csv("jobs.csv", index=False)
        print(f"✅ Found {len(df)} matching jobs. Saved to jobs.csv.")
        send_email(jobs)
    else:
        print("⚠️ No matching jobs found.")
