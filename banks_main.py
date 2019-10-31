import os
import csv
import json
import re
import requests
from bs4 import BeautifulSoup
import csv
import tldextract
from time import sleep
import html2text
import browser_cookie3
import random
import signal
from contextlib import contextmanager
import io
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage


def extract_pdf_text(file_path):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(file_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()

    if text:
        return text
    else:
        return ''


def convert_pdf_to_text(content):
    with open('temp.pdf', 'wb') as fout:
        fout.write(content)

    pdf_text = extract_pdf_text('temp.pdf')
    os.remove('temp.pdf')

    return pdf_text


@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError


def load_banks_data():
    file_name = 'shadow_only.csv'
    banks_data = {}
    with open(file_name, 'r') as fin:
        reader = csv.reader(fin)
        for i, line in enumerate(reader):
            if i == 0:
                pass
            else:
                bank_name = line[2].replace(' ', '_')
                bank_name = re.sub(r'\W+', '', bank_name)
                banks_data[bank_name] = line[4]

    return banks_data


def create_bank_folders(banks_data):
    root_folder = os.getcwd()
    bank_folders_name = 'directory'
    bank_folders_path = os.path.join(root_folder, bank_folders_name)
    try:
        os.mkdir(bank_folders_path)
    except:
        # folder already exists
        pass

    for key, value in banks_data.items():
        folder_name = key.replace(' ', '_')
        folder_path = os.path.join(bank_folders_path, folder_name)
        try:
            os.mkdir(folder_path)
        except:
            # folder already exists
            pass

        banks_data[key] = [value, folder_path]


# function to extract the text content from a page.
#  page_body -> text object
def get_page_text(page_body):
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = True
    text_maker.ignore_images = True
    text_maker.ignore_anchors = True
    text_maker.body_width = 0


    text = text_maker.handle(page_body).lower().replace('#', '').replace('*', '').replace('_', '').replace(' - ', ' ').replace('|', '').replace('(icon)', '').strip()

    return text


def init_session():
    session = requests.Session()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36',
    }
    cookie = browser_cookie3.chrome()
    session.cookies.update(cookie)

    return session


def get_page(current_session):
    url = 'https://start.loandepot.com/assets/img/aflac/Aflac_loanDepot_CustomerFlyer.pdf'
    response = current_session.get(url)
    content_type = response.headers['content-type']
    if 'pdf' in content_type:
        pdf_text = convert_pdf_to_text(response.content)
    if 'text/html' in content_type:
        pass


def current_urls(urls_list, session):
    bad_contents = ['/media/', '/images/', '.css', '.png', '.jpeg', 'jpg', '.gif',
                    '.ashx', '=', '.ico', '%20', '/css/', '/ajax', '.mp4', '.wav', 'facebook', 'twitter',
                    'instagram', 'pinterest', '.mp3', '.mov', 'trustpilot', 'mailto', '.zip', '.tar', '.gz', 'webmaxstaging', '#', '.docx', '.doc', '.xlsx', '.csv' ]

    while len(urls_list[0]) > 0:
        try:
            for url in urls_list[0]:
                if url in urls_list[1]:
                    pass
                else:
                    print(url)
                    urls_list[1].append(url)
                    with timeout(15):
                        try:
                            r = session.get(url, timeout=5)
                        except Exception as e:
                            pass
                    if not r.status_code == 200:
                        print(r.status_code)
                        urls_list[0].remove(url)
                    else:
                        urls_list[0].remove(url)

                        content_type = r.headers['content-type']

                        if 'pdf' in content_type:
                            out_text = convert_pdf_to_text(response.content)

                        if 'text/html' in content_type:
                            r_text = r.text
                            out_text = get_page_text(r_text)


                        page_name = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('www.', '').replace('.', '-') + '.txt'
                        out_dir = urls_list[3][0]
                        try:
                            os.mkdir(out_dir)
                        except Exception:
                            pass
                        out_path = os.path.join(out_dir, page_name)
                        with open(out_path, 'w') as fout:
                            fout.write(out_text)

                        soup = BeautifulSoup(r_text, 'html.parser')
                        for anchor in soup.find_all('a', href=True):
                            link = anchor['href']

                            if link.startswith('#'):
                                pass
                            if link.endswith('/'):
                                link = link[:-1]
                            if link.startswith('/'):
                                link = 'https://www.' + urls_list[2][0] + link

                            if not urls_list[2][0] in link:
                                pass
                            else:
                                if any(substring in link for substring in bad_contents):
                                    pass
                                else:
                                    link = link.replace('https://', 'http://')
                                    urls_list[0].append(link)
                                    for url in urls_list[0]:
                                        if url in urls_list[1]:
                                            urls_list[0].remove(url)
                                            urls_list[0] = list(set(urls_list[0]))



        except Exception as e:
            print(e)


def main():
    if os.path.exists('already_scraped.txt'):
        pass
    else:
        with open('already_scraped.txt', 'w') as fout:
            fout.write('')

    banks = load_banks_data()
    create_bank_folders(banks)
    session = init_session()

    already_scraped = []
    with open('already_scraped.txt', 'r') as fin:
        for line in fin:
            if line == '':
                pass
            else:
                already_scraped.append(line.strip())

    for key, value in banks.items():
        bank_name = key
        bank_root_url = value[0]
        bank_dir = value[1]

        if bank_name.strip() in already_scraped:
            pass
        else:
            with open('already_scraped.txt', 'a') as fout:
                fout.write(bank_name.strip() + '\n')
            urls_list = [[bank_root_url], [], [], [bank_dir]] #[ [current_urls_list], [seen_urls], [current domain], [live folder] ]
            domain = tldextract.extract(bank_root_url)
            root = '{}.{}'.format(domain[1], domain[2])
            urls_list[2].append(root)
            current_urls(urls_list, session)








main()
