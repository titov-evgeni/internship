<h1 align="center">Scraper</h1>

## Description

**Script for getting data from the site www.reddit.com on posts
in the 'Top' -> 'This Month' category.**

## How to run

**1. Install Chrome browser if necessary**  

**2. Download ChromeDriver for your Chrome browser version  
(use site https://chromedriver.chromium.org/downloads or other)**  

**3. Unpack zip file and move file chromedriver.exe to:**
- **/usr/bin** for Linux:

        sudo mv chromedriver /usr/bin  

- **project folder** for Windows:

		  move chromedriver.exe PATH\project

**4. Move to the project folder**  

**5. Install venv if necessary:**
- for Linux:

        sudo apt install -y python3-venv

- for Windows:

		  pip install venv
**6. Create virtual environment:**
- for Linux:

        python3 -m venv my_env

- for Windows:

		  python -m venv my_env
**6. Activate virtual environment:**
- for Linux:

        source my_env/bin/activate

- for Windows:

        my_env\Scripts\activate.bat
**6. Install requirements:**

        pip install -r requirements.txt

**6. Run script:**

        python main.py
**6. Deactivate virtual environment:**
- for Linux:

        deactivate

- for Windows:

        deactivate.bat
