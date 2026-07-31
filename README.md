# 🛡️ ReturnGuard — AI-Powered Return Window Tracker & Auto-Alert System

[![AWS Serverless](https://img.shields.io/badge/AWS-Serverless-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Amazon Bedrock](https://img.shields.io/badge/AI-Amazon%20Bedrock-8B5CF6?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**ReturnGuard** is an automated, forward-looking productivity assistant built for the **AWS Builder Center Weekend Challenge**. It solves a universal financial annoyance: **passive money loss from missed online purchase return windows**. 

Instead of manually reading fine print and tracking return deadlines on a calendar, simply paste your order confirmation email text into ReturnGuard. Amazon Bedrock (*Nova Lite*) extracts the item, retailer, price, and deadline. An automated daily AWS EventBridge Scheduler checks your active return windows and emails you a pre-drafted return request 3 days before your window closes.

---

## ✨ Features

- 🧠 **AI-Powered Extraction**: Uses **Amazon Bedrock (Nova Lite)** to parse unstructured confirmation emails and receipts into structured purchase data.
- 🛡️ **Resilient Fallback Engine**: Built-in Python regex & policy rules engine automatically activates if AWS Bedrock model access is restricted on new Free Tier accounts—guaranteeing 100% uptime.
- ⏱️ **Visual Countdown Dashboard**: Responsive single-page web UI built with HTML5/JS and hosted on **AWS Amplify Hosting**, featuring color-coded urgency badges (`Safe`, `Warning`, `Urgent < 3 Days`).
- 🔔 **Automated Daily Audits**: **Amazon EventBridge Scheduler** triggers a daily check at 09:00 UTC to scan for expiring return windows.
- ✉️ **Ready-to-Send Return Drafts**: **Amazon SES** emails you an urgent alert with a pre-formatted customer support return request tailored to that retailer.

---

## 🏗️ Serverless Architecture


```

[User / Order Email]
│
▼
[AWS Amplify Hosting] ──► [Amazon API Gateway (HTTP API)]
│
▼
[SubmitItem Lambda Function]
│                       │
▼                       ▼
[Amazon Bedrock (Nova Lite)]  [Fallback Rules Engine]
│                       │
└───────────┬───────────┘
│
▼
[Amazon DynamoDB Table]
▲
│
[CheckDeadlines Lambda Function]
▲
│ (Daily 09:00 UTC Cron)
[Amazon EventBridge Scheduler]
│
▼
[Amazon SES Email Alert] ──► [User Inbox]

```

### **AWS Tech Stack**
* **AWS Amplify Hosting**: Global HTTPS static hosting for the web dashboard.
* **Amazon API Gateway (HTTP API)**: Fast, lightweight REST endpoint (`/items`).
* **AWS Lambda (Python 3.12)**: Serverless compute for item submission, AI parsing, and deadline auditing.
* **Amazon Bedrock (`amazon.nova-lite-v1:0`)**: Foundation model for natural language date and retailer extraction.
* **Amazon DynamoDB (On-Demand)**: NoSQL database storing tracked items and calculated deadlines.
* **Amazon EventBridge Scheduler**: Serverless cron trigger (`cron(0 9 * * ? *)`).
* **Amazon SES**: Email notification service for automated return warnings.

---

## 📂 Project Folder Structure

```text
ReturnGuard/
│
├── README.md                     # Project documentation
├── index.html                    # Frontend Web Dashboard (AWS Amplify)
├── template.yaml                 # AWS SAM Infrastructure Template
│
├── submit_item/                  # Lambda: API Handler & AI Parsing
│   ├── app.py
│   └── requirements.txt
│
└── check_deadlines/              # Lambda: Daily EventBridge Cron Audit & SES Alerts
    ├── app.py
    └── requirements.txt

```

---

## 🚀 Step-by-Step Deployment Guide

### 1. Prerequisites

* **AWS CLI** configured with an IAM user (`aws configure`).
* **AWS SAM CLI** installed.
* **Python 3.12+**.
* An email address verified in **Amazon SES** (under *Verified identities* in your AWS Console) to receive alerts.

### 2. Deploy the Serverless Backend

Clone the repository and run the guided SAM deployment:

```bash
git clone [https://github.com/NarenMK-25/ReturnGuard.git](https://github.com/NarenMK-25/ReturnGuard.git)
cd ReturnGuard

# Build Python Lambda packages
sam build

# Deploy infrastructure to AWS Cloud
sam deploy --guided

```

When prompted by the wizard:

* **Stack Name**: `returnguard-stack`
* **AWS Region**: `us-east-1` (or your preferred region)
* **Parameter AlertEmail**: Enter your verified Amazon SES email address
* **Confirm changes before deploy**: `y`
* **Allow SAM CLI IAM role creation**: `y`
* **SubmitItemFunction has no authentication**: `y` *(allows public access from your HTML frontend)*

When deployment completes, copy the **`ApiEndpoint`** URL shown in the terminal output.

### 3. Configure & Deploy the Frontend

1. Open `index.html` in your text editor.
2. Replace line **95** with your deployed API Gateway endpoint:
```javascript
const API_URL = "https://YOUR_API_ID.execute-api.YOUR_[REGION.amazonaws.com/items](https://REGION.amazonaws.com/items)";

```


3. Zip `index.html` into `index.zip`.
4. Open **AWS Amplify Console** $\rightarrow$ **Deploy an app** $\rightarrow$ **Deploy without Git**.
5. Name your app `ReturnGuard` and drag-and-drop `index.zip`.
6. Within seconds, Amplify will generate your live HTTPS domain URL!

---

## 🧪 Testing the Application

1. Open your live AWS Amplify URL in any browser.
2. Paste the following test order confirmation text into the text area:
```text
Thank you for your order from Target! Your order for Sony Noise Cancelling Headphones ($129.99) placed today has been confirmed.

```


3. Click **Extract & Track Window**.
4. The card will appear in your dashboard showing the extracted price, retailer badge, extraction method (`Amazon-Bedrock` or `Fallback-Rules`), and calculated countdown.
5. **Test Alerts**: Open the AWS Lambda console, manually invoke `CheckDeadlinesFunction` with `{}` payload, and check your email inbox for the pre-drafted return warning!

---

## 🛠️ Challenges Overcome

During development, I encountered an AWS account-level restriction (`ValidationException: Operation not allowed`) when attempting to invoke Amazon Bedrock on a new Free Tier account. Rather than letting this block deployment, I engineered a **resilient Fallback Rules Engine** directly in Python using regex and standard retailer return policies (30 days for Amazon, 90 days for Target, 14 days for Apple). This dual-parser architecture ensures the application remains 100% functional and fault-tolerant even if AI endpoints are restricted.

---

## 📝 License

This project is open-source and licensed under the **MIT License**.

```
