import logging
from utils import Utils
from RPA.HTTP import HTTP
from robocorp import workitems
from file_utils import FileUtils
from re import search, DOTALL, IGNORECASE
from browser_utils import BrowserUtils
from business_exception import BusinessException

TEMP_PATH = 'temp'
OUTPUT_PATH = 'output'

logging.basicConfig(format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NewsAutomation:

    def __init__(self):
        self.http = HTTP()
        self.files = FileUtils()
        self.browser = BrowserUtils()
        self.files.create_folder(TEMP_PATH)
        self.files.create_folder(OUTPUT_PATH)

    def setup_extraction(self, item: workitems.Input):
        """Sets up parameters for news extraction."""

        news_data = item.payload["news_data"]
        self.search_phrase = news_data["search_phrase"]
        self.news_category = news_data["news_category"]
        self.limit_date = Utils.get_inferior_date_interval_from_months(
            news_data["number_of_months"])

        self.total_pages = 1
        self.extracted_news = []

        logger.info(f'Target search phrase: "{self.search_phrase}"')
        logger.info(f'Target news category: "{self.news_category}"')
        logger.info(f'Target limit date: "{self.limit_date}"')

    def execute_news_extraction(self):
        """Executes the news extraction process."""

        self.open_website()
        self.search_for_phrase()
        self.change_news_category()
        self.sort_by_most_recent_news()
        self.get_number_of_pages()
        self.extract_valid_news()

    def create_output_files(self):
        """Creates output files."""

        self.create_excel_file()
        self.create_images_zip_file()

    def open_website(self):
        """Opens the target website."""

        self.browser.open_available_browser(
            f'https://www.latimes.com', maximized=True)

    def search_for_phrase(self):
        """Performs a search for a specific phrase."""

        self.browser.click_button_when_visible(
            "css=button[data-element='search-button']")

        self.browser.input_text_when_visible(
            "css=input[data-element='search-form-input']", self.search_phrase)

        self.browser.click_button_when_visible(
            "css=button[data-element='search-submit-button']")

    def change_news_category(self):
        """Changes the news category if specified."""

        if not self.news_category:
            logger.warn(f'No news category was inputed.')
            return

        self.browser.click_element_if_possible(
            "css=span[class='see-all-text']")

        category_selected = self.browser.click_element_if_possible(
            f"//span[text()='{self.news_category}']/ancestor::label[input]")

        if not category_selected:
            logger.warn(f'News category "{self.news_category}" not found.')
        else:
            self.browser.wait_until_page_contains_element(
                'css=div[class="search-results-module-filters-selected"][data-showing="true"]')

            self.browser.wait_for_loading('css=div[class="loading-icon"]', 5)

    def sort_by_most_recent_news(self):
        """Sorts news by most recent."""

        self.browser.select_from_list_by_label(
            "css=select[class='select-input']", "Newest")

        self.browser.wait_for_loading('css=div[class="loading-icon"]', 5)

    def get_number_of_pages(self):
        """Gets the total number of pages containing news."""

        pattern = r'(?<=of\s)[\d.,]+'

        match = self.browser.find_pattern_match_in_element(
            'css=div[class="search-results-module-page-counts"]', pattern, when_visible=False, continue_on_error=True)

        if match:
            self.total_pages = int(match.group().replace(",", ""))

        logger.info(f'A total of {self.total_pages} pages were found.')

    def extract_valid_news(self):
        """Extracts valid news from the current page."""

        for current_page in range(0, self.total_pages):

            logger.info(f'Current page: {current_page+1}')

            if not self.extract_news_from_current_page():
                logger.info(
                    f'Date limit of interest reached, ending extraction...')
                break

            if not self.go_to_next_page():
                logger.info(
                    f'Next page button is disabled, ending extraction...')
                break

    def extract_news_from_current_page(self):
        """Extracts news from the current page."""

        img_pattern = r'(?:<img.*?src=\"(.*?)\".*?)?'
        title_pattern = r'class="promo-title">\s+<a.*?>(.*?)<\/a>.*?'
        description_pattern = r'class="promo-description".*?>(.*?)<\/p>.*?'
        timestamp_pattern = r'class=\"promo-timestamp\".*?data-timestamp=\"(.*?)\"'

        pattern = img_pattern + title_pattern + description_pattern + timestamp_pattern

        matches = self.browser.find_pattern_matches_in_element(
            "css=ul[class='search-results-module-results-menu']", pattern, when_visible=True, flags=DOTALL)

        for match in matches:
            image_url = match.group(1)
            title = match.group(2)
            description = match.group(3)
            news_date = Utils.get_date_from_timestamp(match.group(4))

            if any(news_item['title'] == title and news_item['description'] == description for news_item in self.extracted_news):
                continue

            if news_date < self.limit_date:
                return False

            file_name = f'{self.search_phrase}_{len(self.extracted_news)}.jpeg'

            title_counter = Utils.count_pattern_matches_in_text(
                self.search_phrase, title, IGNORECASE)

            description_counter = Utils.count_pattern_matches_in_text(
                self.search_phrase, description, IGNORECASE)

            contains_monetary = search(
                r'\$[\d,]+(?:\.\d+)?|\d+\s*(?:dollars?|USD)', f'{title}|{description}', IGNORECASE)

            self.extracted_news.append({
                'title': title,
                'date': news_date.strftime('%Y-%m-%d'),
                'description': description,
                'picture file': self.download_file_from_url(image_url, file_name),
                'counter': title_counter + description_counter,
                'contains monetary': bool(contains_monetary)
            })

        return True

    def go_to_next_page(self):
        """Navigates to the next page of news."""

        logger.info(f'Going to next page...')

        next_page_locator = "css=div[class='search-results-module-next-page']"

        if self.browser.element_exists(next_page_locator, 10) is False:
            return False

        is_inactive = self.browser.find_pattern_match_in_element(
            next_page_locator, r'data-inactive')

        if is_inactive:
            return False

        self.browser.scroll_element_into_view(
            next_page_locator)

        self.browser.remove_element_if_possible(
            "css=modality-custom-element[name='metering-bottompanel']", timeout=10)

        self.browser.click_element(next_page_locator)

        return True

    def create_excel_file(self):
        """Creates an Excel file with extracted news."""

        logger.info(f'Creating Excel file...')

        excel_path = f'{TEMP_PATH}/{self.search_phrase}.xlsx'

        self.files.create_excel_file_from_json(self.extracted_news, excel_path)

    def create_images_zip_file(self):
        """Creates a ZIP file containing news images."""

        logger.info(f'Creating Zip file...')

        zip_path = f'{OUTPUT_PATH}/{self.search_phrase}.zip'

        files_to_zip = [
            f"{TEMP_PATH}/{data['picture file']}" for data in self.extracted_news if data['picture file'] != '-']

        files_to_zip.append(f'{TEMP_PATH}/{self.search_phrase}.xlsx')

        self.files.create_zip_from_files(zip_path, files_to_zip)

        if self.files.count_files_in_directory(OUTPUT_PATH) > 50:

            self.files.delete_file(zip_path)

            raise BusinessException(
                f'The total number of files exceeds the maximum allowed limit.')

        if self.files.get_megabytes_size_of_directory(OUTPUT_PATH) > 20:

            self.files.delete_file(zip_path)

            raise BusinessException(
                f'The size of {self.search_phrase}.zip exceeds the maximum allowed limit in megabytes.')

    def download_file_from_url(self, url: str | None, file_name: str):
        """Downloads a file from a URL."""

        if url is None:
            return '-'

        self.http.download(
            url=url,
            target_file=f'{TEMP_PATH}/{file_name}',
            overwrite=True)

        return file_name

    def close_resources(self):
        """Closes resources after extraction."""

        logger.info(f'Closing website...')

        self.total_pages = 1

        self.extracted_news = []

        self.browser.close_browser()

        self.files.delete_files_from_folder(TEMP_PATH)
