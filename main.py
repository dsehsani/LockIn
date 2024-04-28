import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
from bs4 import BeautifulSoup


def search(profName, uniName, driver, profURLArray):
    searchBar = f"site:https://www.ratemyprofessors.com/ {uniName} {profName}"
    driver.get(f"https://www.google.com/search?q={searchBar}")

    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "g")))
    except TimeoutException:
        print(f"No search results found for {profName} at {uniName}.")
        return None

    # Find the link to RateMyProfessors in the search results
    searchResult = driver.find_elements(By.CLASS_NAME, "g")
    profURL = None
    for result in searchResult:
        link = result.find_element(By.TAG_NAME, "a")
        href = link.get_attribute("href")
        if "ratemyprofessors.com" in href:
            profURL = href
            break

    profURLArray.append(profURL)
    return profURL


def run_script(searchInput):
    profURLArray = []
    try:
        chromeConfig = Options()
        chromeConfig.add_argument("--headless")
        driver = webdriver.Chrome(options=chromeConfig)

        for profName, uniName in searchInput.items():
            profURL = search(profName, uniName, driver, profURLArray)
            if profURL:
                print(f"RateMyProfessors URL for {profName} at {uniName}: {profURL}")
            else:
                print(f"RateMyProfessors URL for {profName} at {uniName} not found.")
        
        for url in profURLArray:
            if url:
                feedbackRMP = BeautifulSoup(requests.get(url).text,'html.parser').find_all('div', class_='FeedbackItem__FeedbackNumber-uof32n-1')
                takeAgain = feedbackRMP[0].text.strip()
                averageRating = feedbackRMP[1].text.strip()
                print(takeAgain,averageRating)
        
        # Close the WebDriver after all searches are done
        driver.quit()
        
        messagebox.showinfo("Success", "Script execution completed successfully!")
        
    except Exception as e:
        messagebox.showerror("Error", str(e))


def on_submit():
    names = name_entry.get().split(',')
    universities = university_entry.get().split(',')

    # Create a dictionary from input names and universities
    searchInput.update(dict(zip(names, universities)))

    run_script(searchInput)


# Create Tkinter window
root = tk.Tk()
root.title("Professor Search")

# Create labels and entry fields
tk.Label(root, text="Enter Professor Names (comma-separated):").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Label(root, text="Enter University Names (comma-separated):").pack()
university_entry = tk.Entry(root)
university_entry.pack()

# Create submit button
submit_button = tk.Button(root, text="Submit", command=on_submit)
submit_button.pack()

# Dictionary to store search input
searchInput = {}

# Run Tkinter event loop
root.mainloop()
