import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from robocorp.tasks import task

from RPA.Browser.Selenium import Selenium
from RPA.HTTP import HTTP
from RPA.Excel.Files import Files

http = HTTP()
files = Files()
browser = Selenium(timeout=timedelta(seconds=15),
                   implicit_wait=timedelta(seconds=15))


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    search_phrase = 'Carnaval'
    target_category = 'World & Nation'
    number_of_months = 100

    open_website(search_phrase)
    worksheet_data = extract_news(search_phrase, number_of_months)

    # category_elem = get_target_category_elem(target_category)

    # if category_elem is not None:
    #    category_elem.click()

    files.create_workbook(path="./output/result.xlsx")
    files.create_worksheet(name="Result",
                           content=worksheet_data, header=True)
    files.save_workbook(path="./output/result.xlsx")


def open_website(search_phrase):

    browser.open_available_browser(
        f'https://www.latimes.com/search?q={search_phrase}&s=1&p=1', maximized=True)

    """
    browser.click_element("css=button[data-element='search-button']")

    browser.input_text(
        "css=input[data-element='search-form-input']", search_phrase)

    browser.click_element("css=button[data-element='search-submit-button']")

    browser.select_from_list_by_label(
        "css=select[class='select-input']", "Newest")

    browser.driver.refresh()
    """


def extract_news(search_phrase, number_of_months):

    worksheet_data = []

    results_count = browser.find_element(
        'css=div[class="search-results-module-page-counts"]')

    match = re.search(r'(?<=of\s)[\d.,]+', results_count.text)

    total_pages = int(match.group().replace(".", "")) if match else 0

    for current_page in range(0, total_pages):

        browser.wait_until_element_is_visible(
            "css=ul[class='search-results-module-results-menu']")
        search_results = browser.find_element(
            "css=ul[class='search-results-module-results-menu']")

        print(f'Current page: {current_page+1}')

        pattern = r'(?:<img.*?src=\"(.*?)\".*?)?class="promo-title">\s+<a.*?>(.*?)<\/a>.*?class="promo-description".*?>(.*?)<\/p>.*?class=\"promo-timestamp\".*?data-timestamp=\"(.*?)\"'

        matches = re.finditer(
            pattern, search_results.get_attribute('innerHTML'), flags=re.DOTALL)

        for match in matches:

            image_url = match.group(1)
            title = match.group(2)
            description = match.group(3)
            timestamp = match.group(4)

            if is_allowed_timestamp(timestamp, number_of_months):
                print("invalid date")
                return worksheet_data

            worksheet_data.append({
                'title': title,
                'date': get_date_from_timestamp(timestamp),
                'description': description,
                'picture file': download_image(image_url, len(worksheet_data)),
                'counter': count_search_phrases(title, description, search_phrase),
                'contains monetary': contains_monetary(title, description)
            })

        next_page_elem = browser.find_element(
            "css=div[class='search-results-module-next-page']")

        if 'data-inactive' in next_page_elem.get_attribute('innerHTML'):
            return worksheet_data

        browser.scroll_element_into_view(next_page_elem)

        browser.click_element(next_page_elem)

    return worksheet_data


"""
def get_target_category_elem(target_category):

    checkboxes = browser.find_elements(
        "css=label[class='checkbox-input-label']")

    for elem in checkboxes:

        elem.find
        # Access last child directly using find_element
        last_child = elem.find_element(By.XPATH, ".//last-child()")
        inner_text = last_child.get_attribute("innerText")

        if inner_text == target_category:
            return elem

    return None
    

def extract_news(search_phrase, number_of_months):

    worksheet_data = []

    results_count = browser.find_element(
        'css=div[class="search-results-module-page-counts"]')

    match = re.search(r'(?<=of\s)[\d.,]+', results_count.text)

    total_pages = int(match.group().replace(".", "")) if match else 0

    for current_page in range(0, total_pages):


        browser.driver.page_source


        print(current_page)

        # browser.go_to(f'https://www.latimes.com/search?q={search_phrase}&s=1&p={str(page)}')

        # class:search-results-module-main')
        emergency = browser.find_element(
            "css=ul[class='search-results-module-results-menu']")

        if emergency is not None:
            print(emergency)

        browser.wait_until_element_is_visible('css=div[class="promo-wrapper"]')
        elements = browser.find_elements('css=div[class="promo-wrapper"]')

        if elements is not None:
            print(elements)

        for element in elements:
            content = element.get_attribute('innerHTML')

            pattern = r'(?:<img.*?src=\"(.*?)\".*?)?class="promo-title">\s+<a.*?>(.*?)<\/a>.*?class="promo-description".*?>(.*?)<\/p>.*?class=\"promo-timestamp\".*?data-timestamp=\"(.*?)\"'

            match = re.search(pattern, content, flags=re.DOTALL)

            if match:

                image_url = match.group(1)
                title = match.group(2)
                description = match.group(3)
                timestamp = match.group(4)

                # if is_allowed_timestamp(timestamp, number_of_months):
                #    print("invalid date")
                #    return worksheet_data

                worksheet_data.append({
                    'title': title,
                    'date': get_date_from_timestamp(timestamp),
                    'description': description,
                    'picture file': download_image(image_url, title),
                    'counter': count_search_phrases(title, description, search_phrase),
                    'contains monetary': contains_monetary(title, description)
                })

        browser.scroll_element_into_view(
            "css=div[class='search-results-module-next-page']")

        remove_element_if_possible(
            'css=modality-custom-element[name="metering-bottompanel"]')

        browser.click_element(
            "css=div[class='search-results-module-next-page']")

    return worksheet_data

"""


def download_image(image_url, index):
    """Downloads excel file from the given URL"""

    if image_url is None:
        return '-'

    file_name = f'image_{index}.jpeg'

    # file_name = convert_to_valid_filename(file_name, file_extension)
    http.download(
        url=image_url,
        target_file=f'output/{file_name}',
        overwrite=True)

    return file_name


# def convert_to_valid_filename(file_name, file_extension):
#    file_name = re.sub(r'[^\w\s]', '', file_name)
#    return f'{file_name}.{file_extension}'


def get_date_from_timestamp(timestamp):
    formatted_date = datetime.fromtimestamp(
        int(timestamp) / 1000).strftime('%Y-%m-%d')
    return formatted_date


def is_allowed_timestamp(timestamp, number_of_months):

    inferior_limit_date = datetime.now() - relativedelta(months=number_of_months)

    timestamp_date = datetime.fromtimestamp(int(timestamp) / 1000)

    return timestamp_date < inferior_limit_date


def count_search_phrases(title, description, search_phrase):
    title_counter = len(re.findall(search_phrase, title, flags=re.IGNORECASE))
    description_counter = len(re.findall(
        search_phrase, description, flags=re.IGNORECASE))
    return title_counter + description_counter


def contains_monetary(title, description):
    money_pattern = r'\$[\d,]+(?:\.\d+)?|\d+\s*(?:dollars?|USD)'
    monetary_title = re.search(money_pattern, title, flags=re.IGNORECASE)
    monetary_description = re.search(
        money_pattern, description, flags=re.IGNORECASE)
    return bool(monetary_title) or bool(monetary_description)


def remove_element_if_possible(locator: str):
    try:
        modal = browser.find_element(locator)
        modal.parent.execute_script("arguments[0].hidden = true;", modal)
    except:
        print("Unable to remove element")
