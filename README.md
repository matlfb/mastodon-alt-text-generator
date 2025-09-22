# Adding Alt Text to Your Mastodon Posts
*Do you want to add alt text to your Mastodon posts but find it frustrating? This tutorial is **for you!***

---

## Step 1: Retrieve Your Mastodon Account API

1. Go to your Mastodon preferences and click **"New Application"**.  

    ![Capture d’écran](https://github.com/user-attachments/assets/5a1bf3b2-d564-4439-895c-8e1b38d1554b)

2. Name your application and check the following permissions:  
    ```bash
    read:statuses
    profile
    write:media
    write:statuses
    ```

    ![Capture d’écran](https://github.com/user-attachments/assets/9eb8f438-7d4b-4536-a89f-457f6303fc0f)

3. At the bottom of the page, click **"Submit"**.
4. Click on your new application.
5. Copy the generated API credentials.

    ![Capture d’écran](https://github.com/user-attachments/assets/f900836f-fb54-4786-b83b-2af24e73e378)

---

## Step 2: Retrieve Your OpenAI API Key

1. Go to [**OpenAI API Keys**](https://platform.openai.com/account/api-keys).
2. Log in or create an account.
3. Click **"Create new secret key"**.
4. Copy the generated key — you will need it for the script.

<img width="1361" height="1034" alt="Capture d’écran 2025-09-03 à 17 15 12" src="https://github.com/user-attachments/assets/95157119-1a6b-45bd-8d30-b1ce97102dab" />

---

## Step 3: Create a `.env` File

1. In your project folder, create a file named `.env` (with a dot at the beginning).  
2. Add your keys like this:

    ```env
    MASTODON_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxx
    OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
    MASTODON_BASE_URL=https://xxxxxxxxxxxxxxxx
    ```

3. Save the file. The script will use these variables to connect to Mastodon and OpenAI.

> ⚠️ Never share this `.env` file publicly — it contains your secret keys.

---

## Step 4: Install Python and Required Libraries via Terminal

1. Open your terminal.

2. Check if Python is installed:
    ```bash
    python3 --version
    ```
    If it’s not installed, install Python using your package manager:
    - **Debian/Ubuntu:** `sudo apt update && sudo apt install python3 python3-pip -y`
    - **macOS (with Homebrew):** `brew install python`
    - **Windows (via terminal):** follow instructions on [python.org](https://www.python.org/downloads/)

3. Install the required Python libraries:
    ```bash
    python3 -m pip install --upgrade pip
    python3 -m pip install Mastodon.py openai beautifulsoup4 python-dotenv
    ```

> This way, everything is installed directly from the terminal, no GUI needed.

---

## Step 5: Edit the Script

1. Download the latest script (the one using GPT-4o and `.env`).
2. Replace `api_base_url='https://mastodon.instance'` with your Mastodon instance URL if different.
3. Save the script in the same folder as `.env`.

---

## Step 6: Run the Script

1. Open your terminal, navigate to the project folder, then run:

    ```bash
    python3 script.py
    ```

2. The script will fetch your last posts, analyze images without alt text using GPT-4o, and re-upload them with alt descriptions.

---

## Optional: Run Periodically with systemd on Linux

### Create a systemd service file

1. Create a service file in the systemd directory:
    ```bash
    sudo nano /etc/systemd/system/mastodon-alt-text.service
    ```

2. Add the following content to the service file:
    ```ini
    [Unit]
    Description=Mastodon Alt Text Generator
    After=network.target

    [Service]
    User=mastodon
    WorkingDirectory=/home/mastodon/live/scripts/alt_text_gen
    Environment="PATH=/home/mastodon/live/scripts/alt_text_gen/venv/bin"
    ExecStart=/home/mastodon/live/scripts/alt_text_gen/venv/bin/python script.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

3. Enable and start the service
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable mastodon-alt-text.service
    sudo systemctl start mastodon-alt-text.service
    ```

	•	enable makes the service start automatically at boot.
	•	start runs the service immediately.


4. Check the service status:
    ```bash
    sudo systemctl status mastodon-alt-text.service
    ```

---

## ✅ Done!

Your Mastodon alt-text generator is now fully configured with **GPT-4o** and `.env` support.

Follow me on Mastodon: [**@matlfb@social.lol**](https://social.lol/@matlfb)
