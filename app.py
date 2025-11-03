import os
import time
import re
import smtplib
import urllib.parse
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------
# Chrome setup for scraping
# -----------------------------
chrome_options = Options()
chrome_options.add_argument("headless")
chrome_options.add_argument("disable-gpu")
chrome_options.add_argument("no-sandbox")
chrome_options.add_argument("disable-dev-shm-usage")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
time.sleep(1)

# -----------------------------
# Job Filters
# -----------------------------
TECHNICAL_ROLES = [
    "data scientist", "data science", "data analyst", "machine learning", "ml", "ai",
    "python", "django", "flask", "full stack", "react", "angular", "vue", "javascript",
    "typescript", "intern", "trainee", "developer", "engineer"
]
EXCLUDE_ROLES = ["php", "laravel", "wordpress", "drupal", ".net", "c#", "java", "spring", "hibernate"]

# -----------------------------
# Fetch Jobs from Infopark
# -----------------------------
def fetch_infopark_jobs():
    print("Fetching jobs from Infopark...")
    jobs = []
    page = 1

    while page <= 5:
        url = f"https://infopark.in/companies/job-search?page={page}"
        try:
            driver.get(url)
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Failed to load {url}: {e}")
            page += 1
            continue

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

            link_element = row.find("a", href=True)
            job_link = ""
            if link_element:
                job_link = link_element["href"]
                if not job_link.startswith("http"):
                    job_link = f"https://infopark.in{job_link}"

            title_lower = title.lower()
            if any(ex in title_lower for ex in EXCLUDE_ROLES):
                continue
            if any(role in title_lower for role in TECHNICAL_ROLES):
                experience = "0–2 years" if "intern" not in title_lower else "Intern"
                jobs.append({
                    "park": "Infopark",
                    "title": title,
                    "company": company,
                    "experience": experience,
                    "date": date,
                    "location": "Infopark, Kochi",
                    "link": job_link
                })

        page += 1

    print(f"✅ Found {len(jobs)} filtered technical jobs from Infopark.")
    return jobs


# -----------------------------
# Send HTML Email with tracking
# -----------------------------
def send_email_with_jobs(jobs):
    if not jobs:
        print("⚠️ No jobs to email.")
        return

    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    recipients = [x.strip() for x in os.getenv("EMAIL_TO", "").split(",") if x.strip()]
    TRACKER_URL = os.getenv("TRACKER_URL")

    for student in recipients:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Maitexa Technologies <{sender}>"
        msg["To"] = student
        msg["Subject"] = "🌟 Exciting Career Opportunities from Maitexa – Kerala IT Parks"

        # Build email body dynamically
        job_html = ""
        for job in jobs[:20]:  # Limit to 20 jobs for email readability
            email_encoded = urllib.parse.quote(student)
            job_encoded = urllib.parse.quote(job['title'])
            link_encoded = urllib.parse.quote(job['link'])

            tracked_link = f"{TRACKER_URL}?email={email_encoded}&job={job_encoded}&link={link_encoded}"

            job_html += f"""
            <div style="border:1px solid #e0e0e0; padding:15px; border-radius:10px; margin-bottom:12px; background:#f9fff9;">
                <h3 style="color:#007A33; margin-bottom:5px;">{job['title']}</h3>
                <p style="margin:0; color:#333;"><b>🏢 {job['company']}</b></p>
                <p style="margin:2px 0;">📍 {job['location']} | 💼 {job['experience']} | 📅 {job['date']}</p>
                <a href="{tracked_link}" style="display:inline-block; margin-top:5px; background-color:#007A33; color:white; padding:8px 14px; text-decoration:none; border-radius:5px;">👉 View & Apply</a>
            </div>
            """

        html_content = f"""
        <html>
        <body style="font-family:Arial, sans-serif; background-color:#f4fdf5; padding:20px;">
            <div style="background:#ffffff; border-radius:12px; padding:25px; max-width:700px; margin:auto; box-shadow:0 4px 8px rgba(0,0,0,0.1);">
                <h2 style="color:#007A33;">Dear {student.split('@')[0].title()},</h2>
                <p>We are thrilled to inform you that <b>new and exciting career opportunities</b> are now open for talented individuals like you!</p>
                <p>At <b>Maitexa Technologies</b>, we believe that dreams are the starting point of every great success story. This is your chance to chase your dreams and build a rewarding career with us.</p>
                <h3 style="color:#004d26;">✨ Latest Openings (Infopark Kochi)</h3>
                {job_html}
                <p style="margin-top:20px;">Keep learning, keep growing — and take your next big step today!</p>
                <p style="color:#007A33; font-weight:bold;">Warm regards,<br>Maitexa Technologies Pvt Ltd</p>
                <p style="font-size:12px; color:#555;">Kadannamanna, Malappuram, Kerala – 679324<br>
                <a href='mailto:contact@maitexa.com'>contact@maitexa.com</a> | <a href='https://www.maitexa.com'>www.maitexa.com</a></p>
                <p style="font-size:11px; color:gray;">— Generated automatically by Maitexa Job Tracker © 2025</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            print(f"📧 Email sent to {student}")
        except Exception as e:
            print(f"❌ Failed to send email to {student}: {e}")


# -----------------------------
# Main Function
# -----------------------------
def main():
    print("\n🚀 Scanning Kerala IT Parks for Technical Jobs (Excluding Java)...")
    infopark_jobs = fetch_infopark_jobs()
    driver.quit()
    if infopark_jobs:
        send_email_with_jobs(infopark_jobs)
        print("✅ Emails sent successfully!")
    else:
        print("⚠️ No matching jobs found.")


if __name__ == "__main__":
    main()
