# Altitude Daily Summary Automation

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/altitude-summary)

An open-source serverless automation tool that processes Gmail messages from Altitude to generate daily summaries and send them via email at 4 PM daily.

## 🚀 Features

- **Automated Daily Summaries**: Processes updates at 4 PM daily
- **Comprehensive Tracking**: Toileting, diapers, naps, meals, and activities
- **Email Notifications**: Formatted summaries sent to parents
- **Serverless**: Runs on Vercel with zero infrastructure management
- **Open Source**: Free for all parents to use and customize

## 📋 Summary Format

Each daily summary includes:

1. **# of Toiletings** - Wet, Dry, BM counts
2. **# of Diapers** - Wet, Dry, BM counts  
3. **Length of Nap** - Duration in minutes/hours
4. **Meals Status** - AM Snack, Lunch, PM Snack (All/Some/None)
5. **Other Activities** - Learning activities, play, etc.

## 🛠️ Quick Setup

### 1. Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Download `credentials.json`

### 2. Deploy to Vercel
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/altitude-summary)

### 3. Set Environment Variables
```bash
GMAIL_CREDENTIALS_JSON={"web":{"client_id":"..."}}
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
RECIPIENT_EMAIL=parent@example.com
```

## 🧪 Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test the parser
python -c "from api.altitude_summary import process_daily_summary; print(process_daily_summary('2025-06-10', True))"
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Open Pull Request

## 📝 License

MIT License - Free for all parents to use!

---

Made with ❤️ for parents everywhere
# Deploy trigger Wed Jun 11 22:04:33 EDT 2025
