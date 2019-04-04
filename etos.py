#%%
from bs4 import  BeautifulSoup
import requests
import time
import random
import pandas as pd
import collections
from urllib.parse import urljoin
from time import sleep
#%%
def scrape_item(item_link, main_cattegory, sub_category, sub_sub_category, sub_sub_sub_category):
    try:
        item_page = requests.get(item_link)
    except:
        print('connection error, waiting 15 seconds')
        sleep(15)
        item_page = requests.get(item_link)
    item_soup = BeautifulSoup(item_page.content, 'html.parser')
    prod_name = item_soup.find('h1', attrs={'class' : "product-hero__title"}).get_text()
    brand = prod_name.split(' ')[0]
    try:
        amount = item_soup.find('span', attrs = {'class' : "product-meta__property"}).get_text().strip('\n')
    except:
        amount = '-'
    price = item_soup.find('span', attrs = {'class' : "price__value", 'property' : "price"})['content']
    try:
        prod_info = item_soup.find('div', attrs= {'class' : "s-rich-text", 'property' : "description"}).get_text().strip('\n')
    except:
        prod_info = '-'
    try:
        ing = item_soup.find('div', attrs = {'id' : "id-2"}).get_text().strip('\n').split(': ')[-1]
    except:
        ing = '-'
    EAN = item_soup.find('div', attrs = {'id' : "id-4"}).get_text().strip('\n').split(': ')[-1]

    data_dict = collections.OrderedDict()
    data_dict['Merk'] = brand
    data_dict['Product naam'] = prod_name
    data_dict['Product info'] = prod_info
    data_dict['Prijs'] = price
    data_dict['Hoofd categorie'] = main_category
    data_dict['Sub categorie'] = sub_category
    data_dict['Sub-sub categorie'] = sub_sub_category
    data_dict['Product_categorie']  = sub_sub_sub_category
    data_dict['Inhoud of aantallen'] = amount
    data_dict['Ingrediënten'] = ing
    data_dict['Weblink'] = item_link
    data_dict['EAN code'] = EAN

    return data_dict
#%%
data_list = []
base_page = "https://www.etos.nl"
page = requests.get(base_page)
soup = BeautifulSoup(page.content, 'html.parser')
bfs = soup.find_all('a', attrs={'class' : "menu__nav-link menu__nav-link--dropdown"})
#get main categories
for item in bfs:
    main_cat = item.get('href')
    main_category = item.get_text('span').split('\n')[2]
    main_link = base_page + main_cat
    cat_page = requests.get(main_link)
    cat_soup = BeautifulSoup(cat_page.content, 'html.parser')
    cat_bfs = cat_soup.find_all(class_ = "c-button")
    #get sub categories
    for cat_item in cat_bfs:
        sub_cat = cat_item['href']
        sub_category = sub_cat.strip('/')
        sub_link = urljoin(base_page, sub_cat) 
        sub_page = requests.get(sub_link)
        sub_soup = BeautifulSoup(sub_page.content, 'html.parser')
        sub_bfs = sub_soup.find_all('li', attrs = {'class' : "category-list__list-item"})
        #check sub_sub categories (else extract sub cat)
        if sub_bfs:
            for sub_item in sub_bfs:
                sub_sub = sub_item.a.get('href')
                sub_sub_category = sub_item.a['title']
                sub_sub_link = urljoin(base_page, sub_sub) + '?sz=300'
                try:
                    sub_sub_page = requests.get(sub_sub_link)
                except:
                    print('connection error, waiting 10 seconds')
                    sleep(10)
                    sub_sub_page = requests.get(sub_sub_link)
                sub_sub_soup = BeautifulSoup(sub_sub_page.content, 'html.parser')
                #check for sub_sub_sub, else skip to extraction sub_sub
                sub_sub_bfs = sub_sub_soup.find_all('li', attrs = {'class' : "category-list__list-item"})
                if sub_sub_bfs:
                    for sub_sub_item in sub_sub_bfs:
                        sub_sub_sub = sub_sub_item.a.get('href')
                        sub_sub_sub_category = sub_sub_item.a['title']
                        sub_sub_sub_link = urljoin(base_page, sub_sub_sub) + '?sz=300'
                        try:
                            sub_sub_sub_page = requests.get(sub_sub_sub_link)
                        except:
                            print('connection error, waiting 10 seconds')
                            sleep(10)
                            sub_sub_sub_page = requests.get(sub_sub_sub_link)
                        sub_sub_sub_soup = BeautifulSoup(sub_sub_sub_page.content, 'html.parser')
                        n_items = int(sub_sub_sub_soup.find('span', attrs={'class' : "search-results__result-count"}).get_text().split(' ')[0])
                        sub_sub_sub_bfs  = sub_sub_sub_soup.find_all('div', attrs={'class' : "image-container"})
                        print('extracting items from sub_sub_sub category %s with %i items' %(sub_sub_sub_category, n_items))
                        for links in sub_sub_sub_bfs:
                            item_link = links.a.get('href')
                            item_link = urljoin(base_page, item_link)
                            data_list.append(scrape_item(item_link, main_category, sub_category, sub_sub_category, sub_sub_sub_category))
                else:
                    #extract sub_sub_cat:
                    n_items = int(sub_sub_soup.find('span', attrs={'class' : "search-results__result-count"}).get_text().split(' ')[0])
                    sub_sub_bfs  = sub_sub_soup.find_all('div', attrs={'class' : "image-container"})
                    print('extracting items from sub_sub category %s with %i items' %(sub_sub_category, n_items))
                    for links in sub_sub_bfs:
                        item_link = links.a.get('href')
                        item_link = urljoin(base_page, item_link)
                        data_list.append(scrape_item(item_link, main_category, sub_category, '-', sub_sub_category))
                    
        else:
            #extract sub_cat
            n_items = int(sub_soup.find('span', attrs={'class' : "search-results__result-count"}).get_text().split(' ')[0])
            sub_bfs  = sub_soup.find_all('div', attrs={'class' : "image-container"})
            print('extracting items from sub category %s with %i items' %(sub_category, n_items))
            for links in sub_bfs:
                item_link = links.a.get('href')
                item_link = urljoin(base_page, item_link)
                data_list.append(scrape_item(item_link, main_category, '-', '-', sub_category))

data_df = pd.DataFrame(data_list)
data_df = data_df.drop_duplicates(subset = ['Merk','Product naam','Product info','Prijs', 'Inhoud of aantallen', 'EAN'])
data_df.to_excel('etos_dataset.xlsx')
print('saved dataset "etos_dataset.xlsx" with %i datapoints' %(len(data_df)))

