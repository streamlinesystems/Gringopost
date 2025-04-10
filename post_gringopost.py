name: GringoPost Bot

on:
  schedule:
    # Runs at 9:00 AM on Mondays and Wednesdays (GMT-5 → 14:00 UTC)
    - cron: '0 14 * * 1,3'
  workflow_dispatch:  # allow manual runs

jobs:
  post:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repo
      uses: actions/checkout@v3

    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        playwright install chromium

    - name: Run GringoPost Bot
      env:
        GRINGO_EMAIL: ${{ secrets.GRINGO_EMAIL }}
        GRINGO_PASSWORD: ${{ secrets.GRINGO_PASSWORD }}
      run: |
        echo "📥 Starting GringoPost bot..."
        python3 post_gringopost.py
        echo "✅ Bot finished execution. Check for 'Post submitted successfully!' message in logs."

    - name: Upload screenshots if they exist
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: screenshots
        path: |
          screenshot_*.png
          error_*.png
          *.png
        if-no-files-found: ignore
