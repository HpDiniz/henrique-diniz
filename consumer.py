
import re
import logging
from RPA.HTTP import HTTP
from datetime import datetime
from robocorp import workitems
from robocorp.tasks import task
from typing import Tuple, List, Any

from utils import Utils
from file_utils import FileUtils
from browser_utils import BrowserUtils
from business_exception import BusinessException

http = HTTP()
files = FileUtils()
browser = BrowserUtils()

logging.basicConfig(format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TEMP_PATH = 'temp'
OUTPUT_PATH = 'output'
files.create_folder(TEMP_PATH)
files.create_folder(OUTPUT_PATH)


@task
def consume_news_workitems():
    """Consumes news work items, executes news extraction for each item, marks them as done or failed."""

    for item in workitems.inputs:
        try:
            execute_news_extraction(item)
            item.done()
        except BusinessException as e:
            handle_exception(item, "BUSINESS", e)
        except Exception as e:
            handle_exception(item, "APPLICATION", e)

    files.delete_files_from_folder(TEMP_PATH)


def execute_news_extraction(item: workitems.Input):
    """Executes the process of extracting news based on the provided work item."""

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
    create_images_zip_file(worksheet_data, search_phrase)
    close_website()


def read_payload(item: workitems.Input) -> Tuple[str, str, int]:
    """Reads the payload of a work item and returns search phrase, news cate    gory, and number of months."""

    logger.info('Reading payload...')

    news_data = item.payload["news_data"]

    logger.info(news_data)

    search_phrase = str(news_data["search_phrase"])
    news_category = str(news_data["news_category"])
    number_of_months = int(news_data["number_of_months"])

    return search_phrase, news_category, number_of_months


def open_website():
    """Opens the browser and navigates to the specified website."""

    logger.info('Opening browser...')

    browser.open_available_browser(f'https://www.latimes.com', maximized=True)


def search_for_phrase(search_phrase):
    """Enters the search phrase into the search bar of the website."""

    logger.info(f'Searching for phrase "{search_phrase}"...')

    browser.click_button_when_visible(
        "css=button[data-element='search-button']")

    browser.input_text_when_visible(
        "css=input[data-element='search-form-input']", search_phrase)

    browser.click_button_when_visible(
        "css=button[data-element='search-submit-button']")


def change_news_category(news_category):
    """Changes the news category on the website if provided."""

    if not news_category:
        logger.warn(f'No news category was inputed.')
        return

    logger.info(f'Searching for news category "{news_category}"...')

    browser.click_element_if_possible("css=span[class='see-all-text']")

    category_selected = browser.click_element_if_possible(
        f"//span[text()='{news_category}']/ancestor::label[input]")

    if not category_selected:
        logger.warn(f'News category "{news_category}" not found.')
    else:

        browser.wait_until_page_contains_element(
            'css=div[class="search-results-module-filters-selected"][data-showing="true"]')

        browser.wait_for_loading('css=div[class="loading-icon"]', 5)


def sort_by_most_recent_news():
    """Navigates to the given URL"""

    logger.info(f'Sorting the latest news...')

    browser.select_from_list_by_label(
        "css=select[class='select-input']", "Newest")

    browser.wait_for_loading('css=div[class="loading-icon"]', 5)


def get_number_of_pages():
    """Sorts the news by most recent on the website."""

    logger.info(f'Getting the total number of pages...')

    pattern = r'(?<=of\s)[\d.,]+'

    match = browser.find_pattern_match_in_element(
        'css=div[class="search-results-module-page-counts"]', pattern, when_visible=False, continue_on_error=True)

    total_pages = int(match.group().replace(",", "")) if match else 1

    logger.info(f'A total of {total_pages} pages were found.')

    return total_pages


def extract_valid_news(worksheet_data: List, search_phrase: str, total_pages: int, number_of_months: int):
    """Retrieves the total number of pages of news articles."""

    limit_date = Utils.get_inferior_date_interval_from_months(number_of_months)

    logger.info(f'Extracting news until {limit_date}...')

    for current_page in range(0, total_pages):

        logger.info(f'Current page: {current_page+1}')

        if not extract_news_from_current_page(worksheet_data, search_phrase, limit_date):
            logger.info(
                f'Date limit of interest reached, ending extraction...')
            break

        if not go_to_next_page():
            logger.info(f'Next page button is disabled, ending extraction...')
            break


def extract_news_from_current_page(worksheet_data: List, search_phrase: str, limit_date: datetime) -> bool:
    """Extracts valid news articles within the specified timeframe."""

    img_pattern = r'(?:<img.*?src=\"(.*?)\".*?)?'
    title_pattern = r'class="promo-title">\s+<a.*?>(.*?)<\/a>.*?'
    description_pattern = r'class="promo-description".*?>(.*?)<\/p>.*?'
    timestamp_pattern = r'class=\"promo-timestamp\".*?data-timestamp=\"(.*?)\"'

    pattern = img_pattern + title_pattern + description_pattern + timestamp_pattern

    logger.info(f'Getting news information from page...')

    matches = browser.find_pattern_matches_in_element(
        "css=ul[class='search-results-module-results-menu']", pattern, when_visible=True, flags=re.DOTALL)

    for match in matches:

        image_url = match.group(1)
        title = match.group(2)
        description = match.group(3)
        news_date = Utils.get_date_from_timestamp(match.group(4))

        if any(news_item['title'] == title and news_item['description'] == description for news_item in worksheet_data):
            continue

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
    """Extracts news articles from the current page of the website."""

    logger.info(f'Going to next page...')

    next_page_locator = "css=div[class='search-results-module-next-page']"

    if browser.element_exists(next_page_locator, 10) is False:
        return False

    is_inactive = browser.find_pattern_match_in_element(
        next_page_locator, r'data-inactive')

    if is_inactive:
        return False

    browser.scroll_element_into_view(
        next_page_locator)

    browser.remove_element_if_possible(
        "css=modality-custom-element[name='metering-bottompanel']", timeout=10)

    browser.click_element(next_page_locator)

    return True


def close_website():
    """Closes the website."""

    logger.info(f'Closing website...')

    browser.close_browser()


def create_excel_file(worksheet_data: Any, search_phrase: str):
    """Creates an Excel file containing the extracted news data."""

    logger.info(f'Creating Excel file...')

    excel_path = f'{TEMP_PATH}/{search_phrase}.xlsx'

    files.create_excel_file_from_json(worksheet_data, excel_path)


def create_images_zip_file(worksheet_data: Any, search_phrase: str):
    """Creates a zip file containing images and Excel file of the extracted news data."""

    logger.info(f'Creating Zip file...')

    zip_path = f'{OUTPUT_PATH}/{search_phrase}.zip'

    files_to_zip = [
        f"{TEMP_PATH}/{data['picture file']}" for data in worksheet_data if data['picture file'] != '-']
    files_to_zip.append(f'{TEMP_PATH}/{search_phrase}.xlsx')

    files.create_zip_from_files(zip_path, files_to_zip)

    if files.count_files_in_directory(OUTPUT_PATH) > 50:
        files.delete_file(zip_path)
        raise BusinessException(
            f'The total number of files exceeds the maximum allowed limit.')

    if files.get_megabytes_size_of_directory(OUTPUT_PATH) > 20:
        files.delete_file(zip_path)
        raise BusinessException(
            f'The size of {search_phrase}.zip exceeds the maximum allowed limit in megabytes.')


def download_file_from_url(url: str | None, file_name: str):
    """Downloads a file from a given URL and saves it with the specified name."""

    if url is None:
        return '-'

    http.download(
        url=url,
        target_file=f'{TEMP_PATH}/{file_name}',
        overwrite=True)

    return file_name


def handle_exception(item: workitems.Input, exception_type: str, exception: Exception):
    """Handles exceptions occurring during news extraction process."""
    item.fail(exception_type=exception_type, message=str(exception))
    logger.error(exception)
    close_website()
