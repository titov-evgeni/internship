<h1 align="center">Scraper</h1>

## Description

**Script for getting data from the site www.reddit.com on posts
in the 'Top' -> 'This Month' category.**

## How to run

**1. Install Chrome browser if necessary** 

**2. Install MongoDB Community Server for your Platform if necessary**  
(use site https://www.mongodb.com/try/download/community)

**3. Download ChromeDriver for your Chrome browser version  
(use site https://chromedriver.chromium.org/downloads or other)**  

**4. Unpack zip file and move file chromedriver.exe to:**
- **/usr/bin** for Linux:

        sudo mv chromedriver /usr/bin  

- **project folder** for Windows:

        move chromedriver.exe PATH\project

**5. Run MongoDB Server**

**6. Open new terminal window and move to the project folder**

**7. Install venv if necessary:**
- for Linux:

        sudo apt install -y python3-venv

- for Windows:

        pip install venv

**8. Create virtual environment:**
- for Linux:

        python3 -m venv my_env

- for Windows:

        python -m venv my_env

**9. Activate virtual environment:**
- for Linux:

        source my_env/bin/activate

- for Windows:

        my_env\Scripts\activate.bat

**10. Install requirements:**

        pip install -r requirements.txt

**11. Run RESTful server:**

        python task3/server.py

**12. Repeat the steps 6, 9**

**13. Run script:**

        python task3/main_multiprocessing.py

**14. Stop RESTful server (Ctrl+C) in appropriate terminal window**

**15. Stop MongoDB Server in appropriate terminal window**

**16. Deactivate virtual environment:**
- for Linux:

        deactivate

- for Windows:

        deactivate.bat
