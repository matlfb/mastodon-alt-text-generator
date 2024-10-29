# Adding Alt Text to Your Mastodon Posts

*Do you want to add alt text to your Mastodon posts but find it frustrating? This tutorial is **for you!***

---

## Step 1: Retrieve Your Mastodon Account API

1. Click on "New Application"

    <img width="1360" alt="Capture d’écran 2024-10-29 à 18 46 32" src="https://github.com/user-attachments/assets/5a1bf3b2-d564-4439-895c-8e1b38d1554b">

3. Name your application and check the following:
    
    ```bash
    read:statuses
    profile
    write:media
    write:statuses
    ```
    
    <img width="1360" alt="Capture d’écran 2024-10-29 à 18 47 06" src="https://github.com/user-attachments/assets/9eb8f438-7d4b-4536-a89f-457f6303fc0f">


4. At the bottom of the page, click **"Submit"**.
5. Click on your new application.
6. Copy the generated API credentials.

   <img width="1360" alt="Capture d’écran 2024-10-29 à 18 47 24" src="https://github.com/user-attachments/assets/f900836f-fb54-4786-b83b-2af24e73e378">


## Step 2: Retrieve Your OpenAI API

1. Go to [**OpenAI Platform**](https://platform.openai.com/settings/organization/billing/overview).
2. Fund your OpenAI account with at least $5 by clicking on "Add to credit balance".
    
    <img width="1360" alt="Capture%20d%E2%80%99e%CC%81cran%202024-10-28%20a%CC%80%2012 49 06" src="https://github.com/user-attachments/assets/a1a25684-e85f-4901-84d4-31cee29a2d30">


3. Go to [**your profile**](https://platform.openai.com/settings/profile).
4. Click on **"User API keys"** and then on **"Create new secret key"**.
5. Name your key and copy the obtained API key.
    
    <img width="1360" alt="Capture%20d%E2%80%99e%CC%81cran%202024-10-28%20a%CC%80%2012 51 57" src="https://github.com/user-attachments/assets/c6fe4c67-ea56-4b86-8801-51ec37b4fdfd">


## Step 3: Retrieve Your Microsoft Azure API Key

### **1. Create an Azure Subscription**

1. Visit the Azure site: [**Azure Free Account**](https://azure.microsoft.com/en-us/free/).
2. Follow the instructions to create a free account. You can receive free credits to try Azure services.

### **2. Create a Computer Vision Resource**

1. Access the Azure Portal: [**Azure Portal**](https://portal.azure.com/).
2. Log in with the account you just created.
3. Create a new resource:
    - Click on **“Create a resource”** at the top left.
    - Search for **“Computer Vision”**.
    - Click on **“Create”**.

4. **Configure the resource**:

- Choose a **Name** for the resource.
- Select a **Region** (ensure it supports the desired functionality).
- Choose the pricing tier **“F0”** (**Free**).
- Click on **“Review + create”**, then **“Create”**.

5. **Access the resource**:

- Once the resource is created, click on **“Go to resource”**.

### **3. Retrieve the Key and Endpoint**

1. Find the credentials:
    - On your resource page, in the left menu, click on **“Keys and Endpoint”**.
    - Note down **Key1** (or Key2) and the **Endpoint**.

## Step 4: Install Python and the Required Libraries for the Script

1. Install Python [**here**](https://www.python.org/downloads/).
2. Open your computer's terminal and enter the following commands:
    
    ```bash
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    ```
    
3. Install the libraries related to the script:
    
    ```bash
    pip3 install Mastodon.py
    pip3 install azure-cognitiveservices-vision-computervision
    pip3 install openai
    pip3 install beautifulsoup4
    ```
    
## Step 5: Edit the Script.py File

1. Open a text editor.
2. Download the python script above, opening and replacing the “XXXXXXXXXX” with the new keys generated.
3. Once done, run the script

**Don’t forget to change “api_base_url” to your account's instance

## And there you have it! Your script should be up and running 🥳

*It is also possible to run the script on a server and complete these steps in a terminal.*

*Note that the script can be executed periodically on Linux with the following command:*

```bash
crontab -e
```

If you enjoyed this tutorial, you can follow me on Mastodon at: [**@matlfb@mastodon.design**](https://mastodon.design/@matlfb)
