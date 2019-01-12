import io
from html import unescape
import requests
from genshi.input import HTML
from lxml import html
import ez_epub
from requests.compat import urljoin

session = requests.session()
ILLEGAL_FILENAME_CHARACTERS = str.maketrans(r'.<>:"/\|?*^', '-----------')

session.headers[
    'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3021.0 Safari/537.36'
session.headers['origin'] = 'https://www.blinkist.com'
session.headers['upgrade-insecure-requests'] = "1"
session.headers['content-type'] = "application/x-www-form-urlencoded"
session.headers['accept-encoding'] = "gzip, deflate, br"
session.headers['authority'] = "www.blinkist.com"

book_titles = []
username = "?"
password = "?"


def get_csrf_token():
    url_start = "https://www.blinkist.com/en/nc/books.html"
    response = session.get(url=url_start)
    html_content = response.content.decode("utf-8")
    tree = html.fromstring(html=html_content)
    csrf_token = tree.xpath("//meta[@name='csrf-token']/@content")[0]
    return csrf_token


def login(user: str, pwd: str):
    csrf_token = get_csrf_token()

    url_login = "https://www.blinkist.com/en/nc/login/"
    session.post(url=url_login, data={
        "login[email]": user,
        "login[password]": pwd,
        "login[facebook_access_token]": None,
        "utf8": unescape("%E2%9C%93"),
        "authenticity_token": csrf_token
    }, allow_redirects=True)


def analytic_info_html(book: ez_epub.Book, url):
    print('Getting info of ' + url)

    response = session.get(url=url)
    tree = html.fromstring(response.content)
    title = tree.xpath("//h1[@class='book__header__title']/text()")[0].strip()
    subtitle = tree.xpath("//h2[@class='book__header__subtitle']/text()")[0].strip()
    tree_author = [author.strip() for author in tree.xpath("//div[@class='book__header__author']/text()")]
    # tree_info__category = "; ".join(tree.xpath("//div[@class='book__header__info__category']//a/text()"))
    tree_image = tree.xpath("//div[@class='book__header__image']/img/@src")[0]
    tree_synopsis = tree.xpath("//div[@ref='synopsis']")[0]
    # tree_book_faq = tree.xpath("//div[@class='book__faq']")[0]
    html_synopsis = html.tostring(tree_synopsis)
    book.impl.description = HTML(html_synopsis, encoding='utf-8')
    book.impl.addMeta('publisher', 'Blinkist')
    # book.impl.addMeta('tag', tree_info__category)
    # book.impl.addMeta('faq', tree_book_faq)
    book.impl.addMeta('subtitle', subtitle)

    # section = ez_epub.Section()
    # faq_html = html.tostring(tree_book_faq)
    # section.html = HTML(faq_html, encoding="utf-8")
    # section.title = "Frequently Asked Questions"
    # book.sections.append(section)

    # TODO: who is it for? about the author

    story_cover = io.BytesIO(session.get(tree_image).content)
    book.impl.addCover(fileobj=story_cover)
    book.title = title
    book.authors = tree_author
    book.impl.url = url

    return book


def analytic_content_html(book: ez_epub.Book, url: str):
    print('Getting content of ' + url)

    response = session.get(url=url)
    tree = html.fromstring(response.content)
    tree_main = tree.xpath("//main[@role='main']")[0]
    tree_main = remove_tag(tree_main, ".//script")
    tree_main = remove_tag(tree_main, ".//form")
    tree_chapters = tree_main.xpath(".//div[@class='chapter chapter']")
    for tree_chapter in tree_chapters:
        section = ez_epub.Section()
        title = tree_chapter.xpath(".//h1")[0].text
        tree_chapter_content = tree_chapter.xpath(".//div[@class='chapter__content']")[0]
        chapter_html = html.tostring(tree_chapter_content)
        section.html = HTML(chapter_html, encoding="utf-8")
        section.title = title
        book.sections.append(section)
    return book


def remove_tag(tree, xpath):
    for script in tree.xpath(xpath):
        script.getparent().remove(script)
    return tree


def extract_title_from_book_url(book_url: str):
    title = book_url.split("/")[-1].split(".")[0]
    return title


def get_recently_added_blinks(url: str):
    local_book_urls = []
    next_url = url
    while next_url is not None:
        print(next_url)
        json_content = requests.get(url=urljoin(url, next_url)).json()
        status = json_content.get("status", None)
        if status == "ok":
            html_content = json_content.get("template", None)
            if html_content:
                next_book_urls = extract_book_urls(html_content=html_content)
                local_book_urls += next_book_urls
            next_url = json_content.get("next_url", None)
        else:
            break
    return local_book_urls


def extract_book_urls(html_content):
    tree = html.fromstring(html_content)
    tree_book_urls = tree.xpath("//a[@class='blinkV2__link']/@data-product-url")
    local_book_urls = []
    for book_url in tree_book_urls:
        local_book_urls.append(book_url)
    return local_book_urls


def main():
    login(user=username, pwd=password)

    for index, title in enumerate(book_titles):
        # title = extract_title_from_book_url(book_url)
        print("{}/{} - {}".format(index + 1, len(book_titles), title))
        book = ez_epub.Book()
        book.sections = []
        book = analytic_info_html(book=book, url="https://www.blinkist.com/en/books/{title}/".format(title=title))

        book = analytic_content_html(book=book, url="https://www.blinkist.com/en/nc/reader/{title}/".format(title=title))
        print('Saving epub')
        book.make('./{title}'.format(title=book.title.translate(ILLEGAL_FILENAME_CHARACTERS)))


if __name__ == '__main__':
    book_titles = ['15-secrets-successful-people-know-about-time-management-en-kevin-kruse']

    # if sys.argv[1:]:
    #     book_titles = sys.argv[1:]
    # else:
    #     book_titles = sys.stdin
    main()
