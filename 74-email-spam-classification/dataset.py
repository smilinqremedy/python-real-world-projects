"""
Dataset Generator & Pre-curated Corpus for Email Spam Classification.
Generates realistic labeled spam and legitimate (ham) email communications.
"""
import random
import pandas as pd


SPAM_TEMPLATES = [
    "URGENT: Your account access has been suspended! Click {link} to verify your credentials immediately.",
    "Congratulations! You have been selected as the lucky winner of a ${amount} Walmart gift card! Claim now at {link}",
    "Exclusive Investment Opportunity: Double your Bitcoin in 24 hours guaranteed. Deposit crypto now: {link}",
    "FINAL NOTICE: You have an unpaid tax bill of ${amount}. Immediate wire transfer required to avoid warrant.",
    "Get rich quick with automated forex trading robots! Zero risk, 100% daily returns guaranteed. Sign up: {link}",
    "Cheap medications online! Viagra, Cialis, no prescription required, discreet overnight shipping. Order {link}",
    "Dear Friend, I am Barrister {name}, representing the late estate of ${amount}M USD. Reply to claim inheritance.",
    "Work from home and earn ${amount} daily with just your phone! No experience necessary. Apply here: {link}",
    "Your package delivery failed due to missing customs fees. Pay ${amount} tracking fee at {link} within 2 hours.",
    "ACT NOW: Free trial expires in 15 minutes! Get unlimited adult access and prizes. Click here {link}",
    "Security Alert: Unauthorized login attempt from Nigeria. Confirm your online banking password now: {link}",
    "Cash loan approved! Instant wire transfer of ${amount} into your checking account. No credit check required {link}"
]

HAM_TEMPLATES = [
    "Hi team, please find the quarterly financial budget attached for our review meeting tomorrow at 10 AM.",
    "Thank you for your recent order #{order_id}. Your receipt and tracking information are attached.",
    "Reminder: Sprint planning is scheduled for this Wednesday at 2:00 PM in Conference Room B.",
    "Hi {name}, could you please push your branch updates for the authentication module before the code freeze?",
    "Dear customer, your monthly subscription invoice #{order_id} has been processed successfully. Thank you.",
    "Meeting notes: We agreed on the database schema migration timeline and assigned tasks to backend engineers.",
    "Hi everyone, the office will be closed on Monday in observance of the public holiday. Have a wonderful weekend.",
    "Your appointment with Dr. {name} has been confirmed for Friday at 3:30 PM. Please arrive 10 minutes early.",
    "Hello team, please remember to submit your weekly timesheets and expense reports by 5:00 PM today.",
    "The pull request #{order_id} has been approved by the tech lead and merged into the main development branch.",
    "Hi {name}, great job on yesterday's client presentation! The customer was very impressed with our progress.",
    "Please find attached the updated project roadmap and architecture diagram for the upcoming release."
]


def generate_spam_dataset(n_samples: int = 1000, seed: int = 42, output_csv: str = "spam_dataset.csv") -> pd.DataFrame:
    random.seed(seed)
    names = ["Johnson", "Williams", "Smith", "Adeyemi", "Brown", "Okafor", "Davis", "Miller"]
    links = ["http://bit.ly/claim-99", "http://secure-verify-login.xyz", "http://fast-cash-wire.info", "http://update-wallet.cc"]

    emails = []
    labels = []

    # 40% Spam, 60% Ham
    n_spam = int(n_samples * 0.40)
    n_ham = n_samples - n_spam

    for _ in range(n_spam):
        tpl = random.choice(SPAM_TEMPLATES)
        text = tpl.format(
            amount=random.choice([500, 1000, 5000, 15000, 25000]),
            link=random.choice(links),
            name=random.choice(names)
        )
        emails.append(text)
        labels.append(1)

    for _ in range(n_ham):
        tpl = random.choice(HAM_TEMPLATES)
        text = tpl.format(
            order_id=random.randint(10000, 99999),
            name=random.choice(names)
        )
        emails.append(text)
        labels.append(0)

    # Shuffle
    combined = list(zip(emails, labels))
    random.shuffle(combined)
    emails, labels = zip(*combined)

    df = pd.DataFrame({
        "message": emails,
        "is_spam": labels
    })

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df
