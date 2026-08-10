# SplitSplit Telegram Bot

A smart Telegram bot that seamlessly splits restaurant bills using AI! Simply drop a photo of a receipt into a group chat, and the bot will use Google Gemini Vision to extract the items, generate an interactive Telegram poll, and automatically calculate exactly how much everyone owes (including evenly distributed tax and service charges).

## Features
- **AI Receipt OCR**: Uses `gemini-3.5-flash` to read complex, blurry, or crinkled receipts with high accuracy.
- **Interactive Telegram Polls**: Automatically generates a poll in your group chat allowing friends to claim the items they ordered.
- **Auto-Calculation**: Once all items in the poll are claimed, it instantly auto-calculates the final bill.
- **Fair Tax Distribution**: Evenly divides tax and service charges among everyone who ordered food.
- **Highlight Support**: If you highlight items with colored markers, the bot will group them by color!

## Prerequisites
- Python 3.9+
- A Telegram Bot Token from [@BotFather](https://t.me/botfather)
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/SplitSplit.git
   cd SplitSplit
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Configure your API keys:
   Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` to include your `TG_BOT_TOKEN` and `GEMINI_API_KEY`.*

## Important Telegram Setup (Group Privacy)
For the bot to read receipt photos in a group chat without needing a command:
1. Go to **@BotFather** on Telegram.
2. Send `/setprivacy`.
3. Select your bot and click **Disable**.
4. **Important**: If the bot is already in your group chat, you must kick it and re-add it for this setting to take effect.

## Usage
Run the bot locally:
```bash
python main.py
```

- Add the bot to your Telegram group.
- Send a photo of a receipt into the group.
- Let your friends tap the items they ordered in the poll.
- The bot will auto-calculate the final amounts and post the results!
