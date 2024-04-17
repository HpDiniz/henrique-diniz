import re
from typing import Tuple, List
from utils import Utils
from browser_utils import BrowserUtils
from file_utils import FileUtils
from datetime import datetime
from dateutil.relativedelta import relativedelta
from robocorp.tasks import task
from robocorp import workitems
from robocorp.tasks import task
from RPA.HTTP import HTTP

http = HTTP()
files = FileUtils()
browser = BrowserUtils()


@task
def consume_news_workitems():
    """
    Inhuman Insurance, Inc. Artificial Intelligence System automation.
    Consumes news data work items.
    """
    for item in workitems.inputs:
        try:
            execute_news_extraction(item)
            item.done()
        except Exception as e:
            item.fail(message=e)
            close_website()
            print(e)

    browser._quit_all_drivers()


"""
item.done()
item.fail(
    exception_type="APPLICATION",
    code="TRAFFIC_DATA_POST_FAILED",
    message=return_json["message"],
)
item.fail(
    exception_type="BUSINESS",
    code="INVALID_TRAFFIC_DATA",
    message=item.payload,
)
"""


def execute_news_extraction(item: workitems.Input):

    worksheet_data = []
    search_phrase, news_category, number_of_months = read_payload(item)

    open_website()
    search_for_phrase(search_phrase)
    change_news_category(news_category)
    sort_by_most_recent_news()
    total_pages = get_number_of_pages()
    extract_valid_news(worksheet_data, search_phrase,
                       total_pages, number_of_months)
    create_excel_file(worksheet_data, search_phrase)
    close_website()


def read_payload(item: workitems.Input) -> Tuple[str, str, int]:

    news_data = item.payload["news_data"]
    search_phrase = str(news_data["search_phrase"])
    news_category = str(news_data["news_category"])
    number_of_months = int(news_data["number_of_months"])

    return search_phrase, news_category, number_of_months


def open_website():

    print("abrindo browser")
    print(datetime.now())
    browser.open_available_browser(f'https://www.latimes.com', maximized=True)

    print("abriu browser")
    print(datetime.now())


def search_for_phrase(search_phrase):

    browser.click_button_when_visible(
        "css=button[data-element='search-button']")

    browser.input_text_when_visible(
        "css=input[data-element='search-form-input']", search_phrase)

    browser.click_button_when_visible(
        "css=button[data-element='search-submit-button']")


def change_news_category(news_category):

    if not news_category:
        return

    browser.click_element_if_possible("css=span[class='see-all-text']")

    category_selected = browser.click_element_if_possible(
        f"//span[text()='{news_category}']/ancestor::label[input]")

    if not category_selected:
        print(f'Target category "{news_category}" not found.')
    else:
        browser.wait_until_page_contains_element(
            'css=div[class="search-results-module-filters-selected"][data-showing="true"]')

        browser.wait_for_loading('css=div[class="loading-icon"]', 5)


def sort_by_most_recent_news():

    browser.select_from_list_by_label(
        "css=select[class='select-input']", "Newest")

    browser.wait_for_loading('css=div[class="loading-icon"]', 5)


def get_number_of_pages():

    pattern = r'(?<=of\s)[\d.,]+'

    match = browser.find_pattern_match_in_element(
        'css=div[class="search-results-module-page-counts"]', pattern, when_visible=True)

    return int(match.group().replace(",", "")) if match else 0


def extract_valid_news(worksheet_data: List, search_phrase: str, total_pages: int, number_of_months: int):

    limit_date = Utils.get_inferior_date_interval_from_months(number_of_months)

    print(f'Extracting news until {limit_date}...')

    for current_page in range(0, total_pages):

        print(f'Current page: {current_page+1}')

        if not extract_news_from_current_page(worksheet_data, search_phrase, limit_date):
            print("Invalid date reached")
            break

        if not go_to_next_page():
            print("Next page doesn't exist")
            break


def extract_news_from_current_page(worksheet_data: List, search_phrase: str, limit_date: datetime) -> bool:

    img_pattern = r'(?:<img.*?src=\"(.*?)\".*?)?'
    title_pattern = r'class="promo-title">\s+<a.*?>(.*?)<\/a>.*?'
    description_pattern = r'class="promo-description".*?>(.*?)<\/p>.*?'
    timestamp_pattern = r'class=\"promo-timestamp\".*?data-timestamp=\"(.*?)\"'

    pattern = img_pattern + title_pattern + description_pattern + timestamp_pattern

    matches = browser.find_pattern_matches_in_element(
        "css=ul[class='search-results-module-results-menu']", pattern, when_visible=True, flags=re.DOTALL)

    for match in matches:

        image_url = match.group(1)
        title = match.group(2)
        description = match.group(3)
        news_date = Utils.get_date_from_timestamp(match.group(4))

        if news_date < limit_date:
            return False

        file_name = f'{search_phrase}_{len(worksheet_data)}.jpeg'

        title_counter = Utils.count_pattern_matches_in_text(
            search_phrase, title, re.IGNORECASE)

        description_counter = Utils.count_pattern_matches_in_text(
            search_phrase, description, re.IGNORECASE)

        contains_monetary = re.search(
            r'\$[\d,]+(?:\.\d+)?|\d+\s*(?:dollars?|USD)', f'{title}|{description}', re.IGNORECASE)

        worksheet_data.append({
            'title': title,
            'date': news_date.strftime('%Y-%m-%d'),
            'description': description,
            'picture file': download_file_from_url(image_url, file_name),
            'counter': title_counter + description_counter,
            'contains monetary': bool(contains_monetary)
        })

    return True


def go_to_next_page() -> bool:

    is_inactive = browser.find_pattern_match_in_element(
        "css=div[class='search-results-module-next-page']", r'data-inactive')

    if is_inactive:
        return False

    browser.scroll_element_into_view(
        "css=div[class='search-results-module-next-page']")

    browser.remove_element_if_possible(
        "css=modality-custom-element[name='metering-bottompanel']", timeout=10)

    browser.click_element("css=div[class='search-results-module-next-page']")

    return True


def create_excel_file(content, search_phrase):

    file_path = f'./output/{search_phrase}.xlsx'

    files.create_excel_file_from_json(content, file_path)


def download_file_from_url(url: str | None, file_name: str):

    if url is None:
        return '-'

    http.download(
        url=url,
        target_file=f'output/{file_name}',
        overwrite=True)

    return file_name


def close_website():
    browser.close_browser()


"""
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
"""
