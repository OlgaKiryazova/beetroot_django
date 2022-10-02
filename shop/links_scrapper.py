from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from queue import Queue

import requests
from bs4 import BeautifulSoup


TIME_OUT = 10

LOCK = Lock()


def links_worker(queue: Queue):
    while True:
        url = queue.get()
        print('[WORKING ON]', url)
        try:
            with requests.Session() as session:
                response = session.get(
                    url,
                    allow_redirects=True,
                    timeout=TIME_OUT
                )
                print(response.status_code)

                if response.status_code == 404:
                    print('Page not found', url)
                    break

                assert response.status_code in (200, 301, 302), 'Bad response'

            soup = BeautifulSoup(response.text, 'html.parser')
            # Getting product links
            links = soup.select('.grid-product__content a')
            links = '\n'.join([
                f"https://www.habausa.com{link.get('href')}" for link in links
            ])
            with LOCK:
                with open('./links.txt', 'a') as file:
                    file.write(links)
                    print('WRITE TO FILE')

        except (
            requests.Timeout,
            requests.TooManyRedirects,
            requests.ConnectionError,
            requests.RequestException,
            requests.ConnectTimeout,
            AssertionError
        ) as error:
            print('An error happen', error)
            queue.put(url)

        if queue.qsize() == 0:
            break


def main():
    category_urls = ['https://www.habausa.com/collections/best-sellers',
                     'https://www.habausa.com/collections/puzzles',
                     'https://www.habausa.com/collections/musical-toys',
                     'https://www.habausa.com/collections/magnetic-games',
                     'https://www.habausa.com/collections/threading-games-motor-skills',
                     'https://www.habausa.com/collections/puppets',
                     'https://www.habausa.com/collections/strategy-games',
                     'https://www.habausa.com/collections/travel-tin-games',
                     'https://www.habausa.com/collections/bath-toys',

    ]

    queue = Queue()

    for url in category_urls:
        queue.put(url)

    worker_number = 5

    with ThreadPoolExecutor(max_workers=worker_number) as executor:
        for _ in range(worker_number):
            executor.submit(links_worker, queue)


if __name__ == '__main__':
    main()