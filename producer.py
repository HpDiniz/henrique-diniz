import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from robocorp.tasks import task

from RPA.Browser.Selenium import Selenium
from RPA.HTTP import HTTP
from RPA.Excel.Files import Files

http = HTTP()
files = Files()
browser = Selenium()


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
    number_of_months = 500

    open_website()
    search_for_phrase(search_phrase)
    change_category_and_sort(target_category)
    total_pages = get_number_of_pages()
    limit_date = get_news_limit_date(number_of_months)
    worksheet_data = extract_valid_news(search_phrase, total_pages, limit_date)
    create_excel_file(worksheet_data)


def open_website():
    browser.open_available_browser(f'https://www.latimes.com', maximized=True)


def search_for_phrase(search_phrase):

    browser.click_button_when_visible(
        "css=button[data-element='search-button']")

    browser.wait_until_element_is_visible(
        "css=input[data-element='search-form-input']")

    browser.input_text(
        "css=input[data-element='search-form-input']", search_phrase)

    browser.click_button_when_visible(
        "css=button[data-element='search-submit-button']")


def change_category_and_sort(target_category):

    category_selected = click_element_if_possible(
        f"//span[text()='{target_category}']/ancestor::label[input]")

    if not category_selected:
        print(f'Target category "{target_category}" not found.')
    else:
        browser.wait_until_page_contains_element(
            'css=div[class="search-results-module-filters-selected"][data-showing="true"]')

        wait_for_loading('css=div[class="loading-icon"]', 10)

    browser.select_from_list_by_label(
        "css=select[class='select-input']", "Newest")

    wait_for_loading('css=div[class="loading-icon"]', 10)


def get_number_of_pages():

    browser.wait_until_element_is_visible(
        'css=div[class="search-results-module-page-counts"]')

    results_count = browser.find_element(
        'css=div[class="search-results-module-page-counts"]')

    total_pages_pattern = r'(?<=of\s)[\d.,]+'

    match = re.search(total_pages_pattern, results_count.text)

    total_pages = int(match.group().replace(",", "")) if match else 0

    return total_pages


def extract_valid_news(search_phrase, total_pages, limit_date):

    worksheet_data = []

    print(f'Extracting news until {limit_date}...')

    for current_page in range(0, total_pages):

        print(f'Current page: {current_page+1}')

        if not extract_news_from_current_page(worksheet_data, search_phrase, limit_date):
            print("Invalid date reached")
            break

        if not go_to_next_page():
            print("Next page doesn't exist")
            break

    return worksheet_data


def extract_news_from_current_page(worksheet_data, search_phrase, limit_date):

    browser.wait_until_element_is_visible(
        "css=ul[class='search-results-module-results-menu']")

    search_results = browser.find_element(
        "css=ul[class='search-results-module-results-menu']")

    pattern = r'(?:<img.*?src=\"(.*?)\".*?)?class="promo-title">\s+<a.*?>(.*?)<\/a>.*?class="promo-description".*?>(.*?)<\/p>.*?class=\"promo-timestamp\".*?data-timestamp=\"(.*?)\"'

    matches = re.finditer(
        pattern, search_results.get_attribute('innerHTML'), flags=re.DOTALL)

    for match in matches:

        image_url = match.group(1)
        title = match.group(2)
        description = match.group(3)
        news_date = get_date_from_timestamp(match.group(4))

        if news_date < limit_date:
            return False

        worksheet_data.append({
            'title': title,
            'date': news_date.strftime('%Y-%m-%d'),
            'description': description,
            'picture file': download_image(image_url, len(worksheet_data)),
            'counter': count_search_phrases(title, description, search_phrase),
            'contains monetary': contains_monetary(title, description)
        })

    return True


def go_to_next_page():
    next_page_elem = browser.find_element(
        "css=div[class='search-results-module-next-page']")

    if 'data-inactive' in next_page_elem.get_attribute('innerHTML'):
        return False

    browser.scroll_element_into_view(next_page_elem)

    browser.click_element(next_page_elem)

    return True


def create_excel_file(content):
    files.create_workbook(path="./output/result.xlsx")
    files.create_worksheet(name="Result",
                           content=content, header=True)
    files.save_workbook(path="./output/result.xlsx")


def click_element_if_possible(locator):
    try:
        span_element = browser.find_element(locator)
        browser.click_element(span_element)
    except:
        return False

    return True


def wait_for_loading(locator, timeout):
    try:
        browser.wait_until_element_is_visible(locator, timeout=timeout)
        browser.wait_until_element_is_not_visible(locator, timeout=timeout)
    except:
        pass


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


def get_date_from_timestamp(timestamp):
    return datetime.fromtimestamp(int(timestamp) / 1000)


def get_previous_months_first_days(num_months):
    current_date = datetime.today().replace(hour=0, minute=0, second=0)
    first_days = []

    if num_months > 0:
        num_months = num_months - 1

    for i in range(num_months + 1):
        target_date = current_date.replace(day=1) - timedelta(days=i*30)
        first_day = target_date.replace(day=1)
        first_days.append(first_day)

    return min(first_days)


def is_allowed_timestamp(timestamp, number_of_months):

    inferior_limit_date = datetime.now() - relativedelta(months=number_of_months)

    timestamp_date = datetime.fromtimestamp(int(timestamp) / 1000)

    return timestamp_date >= inferior_limit_date


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


def get_news_limit_date(number_of_months):
    current_date = datetime.today().replace(day=1, hour=0, minute=0, second=0)
    target_date = current_date.replace(day=1)

    if number_of_months > 0:
        number_of_months = number_of_months - 1

    for _ in range(number_of_months):
        target_date -= timedelta(days=target_date.day)
        target_date -= timedelta(days=1)
        target_date -= timedelta(days=target_date.day - 1)

    return target_date
