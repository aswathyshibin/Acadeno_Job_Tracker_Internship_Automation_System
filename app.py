import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os

# ======================================
# CONFIGURATION (from GitHub Secrets)
# ======================================

SENDER_EMAIL = os.getenv("EMAIL_USER")                     # Gmail sender
SENDER_PASS = os.getenv("EMAIL_PASS")                      # Gmail App Password
TRACKER_URL = os.getenv("TRACKER_URL",
    "https://script.google.com/macros/s/AKfycbydHHAX5zK8dMNcn_kurn5zdTIymCg17tvRhydnE1X9YPPmNsr2CWWk-ygZqls_Tikj/exec")
EMAIL_TO = os.getenv("EMAIL_TO", "")
STUDENTS = [x.strip() for x in EMAIL_TO.split(",") if x.strip()]

# ======================================
# SCRAPE JOBS FROM INFOPARK
# ======================================

def fetch_infopark_jobs():
    print("🔍 Fetching latest jobs from Infopark...")

    chrome_options = Options()
    chrome_options.add_argument("headless")
    chrome_options.add_argument("disable-gpu")
    chrome_options.add_argument("no-sandbox")
    chrome_options.add_argument("disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    jobs = []

    TECHNICAL_ROLES = [
        "data scientist", "data science", "data analyst", "machine learning", "ml", "ai",
        "python", "django", "flask", "full stack", "react", "angular", "vue", "javascript",
        "typescript", "intern", "trainee", "developer", "engineer"
    ]
    EXCLUDE_ROLES = ["php", "laravel", "wordpress", "drupal", ".net", "c#", "java", "spring", "hibernate"]

    for page in range(1, 4):
        url = f"https://infopark.in/companies/job-search?page={page}"
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            table = soup.find("table")
            if not table:
                break

            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                date = cols[0].text.strip()
                title = cols[1].text.strip()
                company = cols[2].text.strip()

                link_tag = row.find("a", href=True)
                if not link_tag:
                    continue
                job_link = link_tag["href"]
                if not job_link.startswith("http"):
                    job_link = f"https://infopark.in{job_link}"

                title_lower = title.lower()
                if any(ex in title_lower for ex in EXCLUDE_ROLES):
                    continue
                if any(role in title_lower for role in TECHNICAL_ROLES):
                    jobs.append({
                        "title": title,
                        "company": company,
                        "date": date,
                        "link": job_link
                    })
        except Exception as e:
            print(f"⚠️ Error loading {url}: {e}")

    driver.quit()
    print(f"✅ Found {len(jobs)} technical jobs.")
    return jobs

# ======================================
# SEND JOB EMAILS (HTML + TRACKING)
# ======================================

def send_job_emails(jobs):
    if not jobs:
        print("⚠️ No jobs found to send.")
        return

    print(f"📧 Sending job updates to {len(STUDENTS)} students...")

    for student in STUDENTS:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Maitexa Technologies <{SENDER_EMAIL}>"
        msg["To"] = student
        msg["Subject"] = f"🌿 Kerala IT Park Jobs – {datetime.now().strftime('%d %b %Y')}"

        html = f"""
        <html>
        <body style="font-family:'Segoe UI',Arial,sans-serif;background-color:#f5fff8;padding:25px;">
        <div style="background-color:#007A33;color:white;padding:18px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;">🌟 Kerala IT Park Job Updates</h2>
        </div>
        <div style="background:white;border:1px solid #007A33;border-top:none;padding:20px;border-radius:0 0 8px 8px;">
            <p>Dear Team,</p>
            <p>We’re delighted to bring you today’s <strong>curated job updates</strong> from Infopark, Technopark, and Cyberpark!</p>
            <p>Every opportunity is a stepping stone toward your dream career — explore, apply, and grow with confidence. 🚀</p>
            <hr style="border:0;height:1px;background:#007A33;">
        """

        for job in jobs:
            tracked_link = (
                f"{TRACKER_URL}?email={student}"
                f"&job={job['title'].replace(' ', '%20')}"
                f"&link={job['link']}"
            )
            html += f"""
            <div style="margin:15px 0;padding:15px;border:1px solid #ccc;border-radius:8px;">
                <h3 style="color:#007A33;margin-bottom:5px;">{job['title']}</h3>
                <p style="margin:2px 0;">🏢 <b>{job['company']}</b></p>
                <p style="margin:2px 0;">📅 {job['date']}</p>
                <a href="{tracked_link}" 
                   style="display:inline-block;margin-top:6px;background:#007A33;color:white;
                          text-decoration:none;padding:8px 14px;border-radius:5px;font-weight:bold;">
                   🔗 View & Apply
                </a>
            </div>
            """

        html += """
            <hr style="border:0;height:1px;background:#007A33;margin-top:20px;">
            <p>Keep learning, keep applying — the right opportunity is just a click away!</p>
            <p style="color:#007A33;font-weight:bold;">Warm regards,<br>
            Maitexa Technologies Pvt Ltd<br>
            Kadannamanna, Malappuram, Kerala<br>
            <a href='mailto:contact@maitexa.com'>contact@maitexa.com</a> |
            <a href='https://www.maitexa.com'>www.maitexa.com</a></p>
            <p style="font-size:12px;color:#777;">— Generated automatically by Maitexa Job Tracker © 2025</p>
        </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASS)
                server.send_message(msg)
                print(f"✅ Email sent to {student}")
        except Exception as e:
            print(f"❌ Failed to send email to {student}: {e}")

# ======================================
# MAIN
# ======================================

def main():
    print("\n🚀 Maitexa Job Scraper Automation Started...")
    jobs = fetch_infopark_jobs()
    send_job_emails(jobs)
    print("✅ All tasks completed successfully!\n")

if __name__ == "__main__":
    main()
