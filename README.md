# ExpenseBot
Telegram bot for tracking expenses with weekly, daily, and monthly reports, budget management, reminders, currency conversion, and Google Sheets integration.

## Features
- **Expense Tracking**: Add expenses with format `Category: Amount: Date` (e.g., `Food: 50000: 2025-06-04`).
- **Reports**: Generate daily, weekly, or monthly reports in PDF format with pie charts.
- **Budget Management**: Set daily, weekly, or monthly budgets with alerts at 80% usage.
- **Reminders**: Daily reminders for expense entry (e.g., `/eslatma 20:00`).
- **Currency Conversion**: Convert expenses to USD or other currencies (`/valyuta USD`).
- **Google Sheets Integration**: Automatically sync expenses to Google Sheets.

## Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
