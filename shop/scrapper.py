import sys
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.db.transaction import atomic
from django.utils.text import slugify

from shop.models import Age, Category,  Product, Image


TIME_OUT = 10


def upload_image_to_local_media(
        img_url: str,
        image_name: str,
        product: Product
):
    with requests.Session() as session:
        img_response = session.get(img_url, timeout=TIME_OUT)

    with open(f'media/images/{image_name}', 'wb') as file:
        file.write(img_response.content)

    Image.objects.create(
        product=product,
        image=f'images/{image_name}',
        base_url=img_url
    )

    del img_response


@atomic
def process(html_string: str, url: str):
    soup = BeautifulSoup(html_string, 'html.parser')
    try:
        title = soup.select('.grid-product__title')
        price = soup.select('.grid-product__price')
        price_ = price[0].text.strip('$')[:-1]

        availability = soup.select('span[data-default-text="Add to cart"]')
        description = soup.select('.collapsible-content__inner p')

        # age = soup.select('.product-block')
        # age = age[2].text.strip().lower().replace('age: ', '')
        # print(age)
        # age, _ = Age.objects.get_or_create(name=age)
        # print(age)
        # print('#'*80)

        product, _ = Product.objects.get_or_create(
            slug=slugify(title := title[0].text.strip()),
            defaults={
                'base_url': url,
                'title': title,
                'price': (price_) if not price_.startswith('R') else
            price_.splitlines()[2].replace('Sale price', '').replace('$', ''),
                'availability': True if availability[0].text.strip().lower() == 'add to cart' else False,
                'description': '\n'.join([f'<p>{item.text}</p>' for item in description]),


            }
        )

        categories = soup.select('.breadcrumb a')
        categories = [categories[1].get('href').split('/')[-1]]

        for category in categories:
            print(category)
            cat, _ = Category.objects.get_or_create(name=category, slug=category)
            product.categories.add(cat)
            print(cat)

        images = soup.select('.grid-product__image-mask img')

        images = [f"https:{img.get('data-src')}".format(width=360) for img in images]
        image_names = [name.split('/')[-1].split('?')[0] for name in images]
        print('Uploading images')
        for image, name in zip(images, image_names):
            print(name)
            upload_image_to_local_media(
                image,
                name.lower(),
                product
            )

        print('Done')

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Parsing Error', error, exc_tb.tb_lineno, url)


def worker(queue: Queue):
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

            process(response.text, url)

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
    with open(f'{settings.BASE_DIR}/links.txt') as file:
        links = file.readlines()

    queue = Queue()

    for url in links:
        queue.put(url)

    worker_number = 20

    with ThreadPoolExecutor(max_workers=worker_number) as executor:
        for _ in range(worker_number):
            executor.submit(worker, queue)


if __name__ == '__main__':
    main()