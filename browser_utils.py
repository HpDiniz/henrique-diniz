import re
from RPA.Browser.Selenium import Selenium
from typing import Match, Iterator, Any


class BrowserUtils(Selenium):
    """
    Extends Selenium functionality with additional browser automation utilities.

    This class provides a set of utility methods for automating web browser interactions using Selenium.
    """

    def __init__(self):
        """
        Initializes BrowserUtils by invoking the constructor of the base class Selenium.
        """
        super().__init__()

    def click_element_if_possible(self, locator: str) -> bool:
        """
        Clicks on an element if it is present on the page.

        Attempts to locate the element specified by the provided locator and clicks on it if found.

        Args:
            locator (str): Locator for the element.

        Returns:
            bool: True if the element was found and clicked successfully, False otherwise.
        """
        try:
            span_element = self.find_element(locator)
            self.click_element(span_element)
        except:
            return False

        return True

    def wait_for_loading(self, locator: str, timeout: int):
        """
        Wait for loading spinner to disappear after an element becomes visible.

        This method waits until the loading spinner disappears after an element 
        located by the provided locator becomes visible, within the specified timeout.

        Args:
            locator (str): Locator for the element.
            timeout (int): Maximum time (in seconds) to wait for the loading spinner appear for the first time.

        Returns:
            None
        """
        try:
            self.wait_until_element_is_visible(
                locator, timeout=timeout)
            self.wait_until_element_is_not_visible(locator)
        except:
            pass

    def input_text_when_visible(self, locator: str, text: str):
        """
        Input text into the specified element when it becomes visible.

        Waits until the element located by the provided locator is visible, then inputs the given text into it.

        Args:
            locator (str): Locator for the element.
            text (str): Text to input into the element.

        Returns:
            None
        """
        self.wait_until_element_is_visible(locator)
        self.input_text(locator, text)

    def find_pattern_match_in_element(self, locator: str, pattern: Any, flags=0, when_visible=False, continue_on_error=False) -> (Match[str] | None):
        """
        Find a match for the given pattern in the text of the element located by the provided locator.

        Args:
            locator (str): Locator for the element.
            pattern (Any): Regular expression pattern to search for in the element's text.
            when_visible (bool): If True, waits until the element is visible before searching for the text match.
            flags (int): Optional flags to modify regex behavior (default is 0).
            continue_on_error (bool): If True, continues execution even if an error occurs.

        Returns:
            (Match[str] | None): The first match found in the element's text, or None if no match is found.
        """
        try:
            if when_visible:
                self.wait_until_element_is_visible(locator)

            element = self.find_element(locator)
            if element:
                return re.search(pattern, element.get_attribute('innerHTML'), flags=flags)
        except Exception as e:
            if not continue_on_error:
                raise Exception(e)

        return None

    def find_pattern_matches_in_element(self, locator: str, pattern: Any, flags=0, when_visible=False, continue_on_error=False) -> (Iterator[Match[str]] | None):
        """
        Find matches for the given pattern in the text of the element located by the provided locator.

        Args:
            locator (str): Locator for the element.
            pattern (Any): Regular expression pattern to search for in the element's text.
            when_visible (bool): If True, waits until the element is visible before searching for the text match.
            flags (int): Optional flags to modify regex behavior (default is 0).
            continue_on_error (bool): If True, continues execution even if an error occurs.

        Returns:
            (Iterator[Match[str]] | None): An iterator containing matches found in the element's text, or None if no match is found.
        """
        try:
            if when_visible:
                self.wait_until_element_is_visible(locator)

            element = self.find_element(locator)
            if element:
                return re.finditer(pattern, element.get_attribute('innerHTML'), flags=flags)

        except Exception as e:
            if not continue_on_error:
                raise Exception(e)

        return None

    def scroll_into_view_and_click_element(self, locator: str):
        """
        Scrolls the element into view and clicks it.

        This method scrolls the element located by the provided locator into view
        and then clicks it.

        Args:
            locator (str): Locator for the element to be scrolled into view and clicked.

        Returns:
            None
        """

        self.scroll_element_into_view(locator)
        self.click_element(locator)

    def remove_element_if_possible(self, locator: str, timeout: int = None):
        """
        Removes an element from the webpage if it is present.

        This method attempts to remove the element specified by the provided locator from the webpage.
        If a timeout is provided, it waits until the element is enabled before attempting removal.

        Args:
            locator (str): Locator for the element to be removed.
            timeout (int, optional): Maximum time (in seconds) to wait for the element to be enabled before removal. Defaults to None.

        Returns:
            None
        """

        try:
            if timeout:
                self.wait_until_element_is_enabled(locator, timeout=timeout)
        except:
            pass

        try:
            element = self.find_element(locator)
            element.parent.execute_script(
                "arguments[0].hidden = true;", element)
        except:
            pass

    def element_exists(self, locator: str, timeout: int = None) -> bool:
        """
        Check if an element exists within a specified timeout period.

        Args:
            locator (str): Locator for the element.
            timeout (int, optional): Maximum time to wait for the element to appear (in seconds). If None, uses default timeout.

        Returns:
            bool: True if the element exists within the specified timeout, False otherwise.
        """
        try:
            self.wait_until_element_is_enabled(locator, timeout=timeout)
            return True
        except:
            return False
