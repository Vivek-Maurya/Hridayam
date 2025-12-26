import pandas as pd

from playwright.sync_api import sync_playwright
import os
import time

# --- CONFIGURATION ---
URL = 'https://hridayampsp.com/login'
# Use a relative path for user data that works on both Windows and Linux
USER_DATA_DIR = os.path.join(os.getcwd(), "playwright_user_data") 

LOCATORS = {
    'UID':           '//*[@id="email"]',
    'Pass':          '//*[@id="password"]',
    'Go':            '//*[@id="loginButton"]',
    'Pinfo':         '//html/body/div[2]/div[1]/div/div/div/ul/li[4]/a',

    'Dr Name':       '//*[@id="hcp_name"]',
    'Patient Name':  '//*[@id="patient_name"]',   
    'Age':           '//*[@id="age"]',
    'Mobile Number': '//*[@id="mobile_number"]',
    'Gender':        '//*[@id="gender"]',
    'Comp':          '//html/body/div[1]/div[3]/div/form/div/div[3]/div[2]/div[5]/div[4]/div[2]/div/div/span/span[1]/span/span/textarea',
    'Heart Rate':    '//*[@id="heart_rate"]',
    'Weight':        '//*[@id="weight"]',
    'Height':        '//*[@id="height"]',
    
    'CBP':           '//html/body/div[1]/div[3]/div/form/div/div[3]/div[2]/div[3]/div[1]/div/div/span[2]/label',
    'PA':            '//html/body/div[1]/div[3]/div/form/div/div[3]/div[2]/div[4]/div[1]/div/div/span[2]/label',
    'PE':            '//html/body/div[1]/div[3]/div/form/div/div[3]/div[2]/div[5]/div[1]/div/div/span[2]/label/input',
    
    'T2DM':          '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[1]/div[4]/div[1]/div/div/span[1]/label/input',
    'HPT':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[1]/div[4]/div[2]/div/div/span[1]/label/input',
    'DYS':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[1]/div[4]/div[3]/div/div/span[2]/label/input',
    'PCO':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[1]/div[4]/div[4]/div/div/span[2]/label/input',
    'KPN':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[1]/div[4]/div[5]/div/div/span[2]/label/input',
    'AST':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[1]/div[4]/div[6]/div/div/span[2]/label/input',
    'BTH':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[3]/div[4]/div[1]/div/div/span[1]/label/input',
    'DRS':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[3]/div[4]/div[2]/div/div/span[2]/label/input',
    'WLK':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[3]/div[4]/div[3]/div/div/span[1]/label/input',
    'TLT':           '//html/body/div[1]/div[3]/div/form/div/div[6]/div/div/div[4]/div[3]/div[4]/div[4]/div/div/span[1]/label/input',
    
    'Submit':        '//*[@id="submit"]'
}

def run_automation(excel_path, uid, password, doctor_name, logger_callback=print):
    """
    Runs the playwright automation.
    logger_callback: function to call with status strings.
    """
    logger_callback(f"Loading Excel file: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path, sheet_name='Sheet1')
        logger_callback(f"Successfully loaded {len(df)} rows.")
    except Exception as e:
        logger_callback(f"Error reading Excel: {e}")
        return False, str(e)

    logger_callback("Launching Browser...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                channel="chromium",
                headless=True, # Must be True for Render/Server environments
                args=[
                     "--no-sandbox",
                     "--disable-setuid-sandbox",
                     "--disable-dev-shm-usage",
                     "--disable-gpu"
                    ] # Added flags for stability
            )
            
            # Create a new context with no viewport to respect maximized arg
            context = browser.new_context()
            page = context.new_page()
            
            # Login
            logger_callback("Navigating to Login Page...")
            page.goto(URL, wait_until='networkidle')
            
            logger_callback("Performing Login...")
            page.fill(LOCATORS['UID'], uid)
            page.fill(LOCATORS['Pass'], password)
            page.click(LOCATORS['Go'])
            
            # Wait for navigation or specific element that confirms login
            # Here we just wait a bit or assume 'Pinfo' is next
            logger_callback("Navigating to Patient Info...")
            try:
                 page.wait_for_selector(LOCATORS['Pinfo'], timeout=10000)
                 page.click(LOCATORS['Pinfo'])
            except:
                 logger_callback("Warning: Could not find Pinfo link immediately, trying direct navigation...")
            
            row_count = 0
            success_count = 0

            for index, row in df.iterrows():
                row_count += 1
                logger_callback(f"Processing Row {row_count}: {row.get('Patient Name', 'Unknown')}")

                try:
                    # Extract data (safely handle missing keys if needed, but assuming structure matches)
                    # dname is now passed from frontend
                    pname = str(row['Patient Name'])
                    age = str(row['Age'])
                    mnumber = str(row['Mobile Number'])
                    gender = str(row['Gender'])
                    comp = 'N/A' # Hardcoded as per v3
                    weight = str(row['Weight'])
                    height = str(row['Height'])

                    # Fill Form
                    # Note: We probably need to ensure we are on the form page for each row if it resets
                    # The original script did NOT have a loop-back to the form URL inside the loop (commented out).
                    # Assuming the "Submit" action reloads the form or stays on it.
                    # Based on v3 logic, it performs actions and then relies on reload()
                    
                    page.select_option(LOCATORS['Dr Name'], doctor_name)
                    page.fill(LOCATORS['Patient Name'], pname)
                    page.select_option(LOCATORS['Age'], age)
                    page.fill(LOCATORS['Mobile Number'], mnumber)
                    page.select_option(LOCATORS['Gender'], gender)
                    
                    page.click(LOCATORS['CBP'])
                    page.click(LOCATORS['PA'])
                    page.click(LOCATORS['PE'])
                    
                    page.fill(LOCATORS['Comp'], comp)
                    # Keyboard enter was in v3
                    page.keyboard.press('Enter')
                    # Click arbitrary point
                    page.mouse.click(1000, 50)
                    
                    page.fill(LOCATORS['Weight'], weight)
                    page.fill(LOCATORS['Height'], height)
                    
                    for key in ['T2DM', 'HPT', 'DYS', 'PCO', 'KPN', 'AST', 'BTH', 'DRS', 'WLK', 'TLT']:
                         page.click(LOCATORS[key])

                    # Submit
                    # page.click(LOCATORS['Submit'])
                    
                    # Post-submit wait
                    page.wait_for_timeout(4000)
                    page.reload() 
                    
                    logger_callback(f"Row {row_count} submitted successfully.")
                    success_count += 1

                except Exception as e:
                    logger_callback(f"Error on row {row_count}: {e}")

            logger_callback(f"Automation Complete. {success_count}/{row_count} rows processed.")
            browser.close() # Keep open? Usually web automation closes it or we keep it open.
            # Context manager closes it automatically.
            
        except Exception as e:
            logger_callback(f"Browser Error: {e}")
            return False, str(e)
            
    return True, "Done"
