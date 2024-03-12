from typing import List, Dict, Union
import json
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from custom_logger import logger


from bs4 import BeautifulSoup
import requests


class Scrapping:
    """
    Class for retrieving and storing data from a website using web scraping.
    """

    def __init__(self, url: str):
        """Initialize the Scrapping object with the starting URL.

        Parameters:
            url (str): The starting URL of the website.
        """
        self.main_url = url

    def get_page(self, url: str) -> BeautifulSoup:
        """Returns a BeautifulSoup object for the given URL.

        Parameters:
            url (str): The URL of the page.

        Returns:
            BeautifulSoup: A BeautifulSoup object representing the page content.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            text = BeautifulSoup(response.text, "html.parser")
            return text
        except requests.RequestException as e:
            logger.log(f"Error retrieving page: {e}", level=40)
            return None

    def get_quotes(
        self, content: BeautifulSoup
    ) -> List[Dict[str, Union[str, List[str]]]]:
        """Gets quotes from the content of a page.

        Parameters:
            content (BeautifulSoup): A BeautifulSoup object representing the content of the page.

        Returns:
            List[Dict[str, Union[str, List[str]]]]: A list of dictionaries, each containing information about a quote.
        """
        result = []
        quotes = content.find_all("div", class_="quote")

        for quote in quotes:
            one_quote: Dict[str, Union[str, List[str]]] = {}

            one_quote["quote"] = quote.find("span", class_="text").get_text()
            one_quote["author"] = quote.find("small", class_="author").get_text()
            one_quote["tags"] = (
                quote.find("div", class_="tags")
                .find("meta", class_="keywords")
                .get("content")
                .split(",")
            )

            result.append(one_quote)

        return result

    def get_authors(self, content: BeautifulSoup) -> List[Dict[str, str]]:
        """Gets authors from the content of a page.

        Parameters:
            content (BeautifulSoup): A BeautifulSoup object representing the content of the page.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing information about an author.
        """

        result = []
        author_links = content.find_all(
            "a", href=lambda value: value and "/author/" in value
        )
        for link in author_links:
            one_authors: Dict[str, str] = {}
            page_text = self.get_page(self.main_url + link.get("href"))
            autors = page_text.find_all("div", class_="author-details")
            for author in autors:
                one_authors["fullname"] = author.find(
                    "h3", class_="author-title"
                ).get_text()
                one_authors["born_date"] = author.find(
                    "span", class_="author-born-date"
                ).get_text()
                one_authors["born_location"] = author.find(
                    "span", class_="author-born-location"
                ).get_text()
                one_authors["description"] = (
                    author.find("div", class_="author-description").get_text().strip()
                )

                result.append(one_authors)

        return result

    def save_to_json(
        self, data: List[Dict[str, Union[str, List[str]]]], filename: str
    ) -> None:
        """Saves data in JSON format to the specified file.

        Parameters:
            data (List[Dict[str, Union[str, List[str]]]]): The data to be saved.
            filename (str): The name of the file to save to.
        """
        try:
            with open(filename, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=4, ensure_ascii=False)
            logger.log(f"Data saved to {filename} successfully.")
        except IOError as e:
            logger.log(f"Error saving data to {filename}: {e}", level=40)


def main() -> None:
    """
    Main function for performing scraping and saving data.
    """
    quotes: List[Dict[str, Union[str, List[str]]]] = []
    authors: List[Dict[str, str]] = []

    clear_double: List[Dict[str, str]] = []

    url = "http://quotes.toscrape.com"
    scrapping = Scrapping(url)
    page = scrapping.get_page(url)

    if page:
        try:
            while True:
                clear_double.extend(author for author in scrapping.get_authors(page))
                authors.extend(
                    author
                    for author in clear_double
                    if author.get("fullname")
                    not in [
                        existing_author.get("fullname") for existing_author in authors
                    ]
                )

                quotes.extend(quote for quote in scrapping.get_quotes(page))

                next_page_link = page.find("li", class_="next")
                if next_page_link is None:
                    break

                next_page_url = url + next_page_link.find("a")["href"]
                page = scrapping.get_page(next_page_url)
        except Exception as e:
            logger.log(f"An error occurred: {e}")
    scrapping.save_to_json(quotes, "quotes.json")
    scrapping.save_to_json(authors, "authors.json")


if __name__ == "__main__":
    main()
