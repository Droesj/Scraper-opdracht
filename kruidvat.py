#%%
from bs4 import  BeautifulSoup
import requests
import time
import random
import pandas as pd
import collections

#%%
def get_product_info(product_page_link):
    '''
    function to scrape needed info per product page from kruidvat.nl
    '''
    link = product_page_link
    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')
    #get name, brand and amount(if available)
    prod_name = soup.find('h1', attrs={"class":"h1"}).get_text()
    brand = prod_name.split(' ')[0]
    try:
        amount = soup.find('span', attrs={"class":"c-product-title__subtitle"}).get_text()
    except:
        amount = '-'
    #price
    price = soup.find('div', attrs={"class":"c-pricetext c-pricetext--pdp"}).get_text()
    price = ''.join(price.split('\n'))
    #product info & EAN codes
    prod_info = soup.find('p', attrs={"class":"c-product-information__text"}).get_text()
    EANs = soup.find('p', attrs={"class":"c-product-information__text c-product-information__ean"}).get_text().lstrip('EAN code: ')
    if ',' in EANs:
        EANs = EANs.split(', ')
    else:
        EANs = [EANs]
    tmp = soup.find_all('p',attrs={"class":"c-product-information__text m-bottom-small"})
    for lines in tmp:
        line = lines.get_text()
        if 'Ingrediënten' in line:
            ingredients = line
    try:
        ingredients
    except:
        ingredients = '-'
    return (prod_name, brand, amount, price, prod_info, EANs, ingredients)



def construct_data(item,main_category,sub_category,sub_sub_category, sub_sub_sub_category):
    '''
    wrapper function for page scraper
    data-dict constructor
    '''
    item_link = item.a.get('href')
    item_link = base_page+item_link
    prod_name, brand, amount, price, prod_info, EANs, ing = get_product_info(item_link)
    data_dict = collections.OrderedDict()
    data_dict['Merk'] = brand
    data_dict['Product naam'] = prod_name
    data_dict['Product info'] = prod_info
    data_dict['Prijs'] = price
    data_dict['Hoofd categorie'] = main_category
    data_dict['Sub categorie'] = sub_category
    data_dict['Sub-sub categorie'] = sub_sub_category
    data_dict['Product_category']  = sub_sub_sub_category
    data_dict['Inhoud of aantallen'] = amount
    data_dict['Ingrediënten'] = ing
    data_dict['Weblink'] = item_link
    data_dict['EAN code 1'] = EANs[0]
    if len(EANs) > 1:
        data_dict['EAN code 2'] = EANs[1]
    if len(EANs) > 2:
        data_dict['EAN code 3'] = EANs[2]
    return(data_dict)

#%%
data_list = []
base_page = "https://www.kruidvat.nl"
page = requests.get(base_page)
soup = BeautifulSoup(page.content, 'html.parser')
bf = soup.find_all('div',attrs={"class":"c-categories-carousel__item"})
#get main_categories
for car_item in bf:
    main_category  = car_item.get_text('href')
    main_cat_link = car_item.a.get('href')
    print(main_cat_link)
    if 'foto' in main_cat_link:
        continue
    cat_link = base_page + main_cat_link
    print(cat_link)
    try:
        cat_page = requests.get(cat_link)
    except:
        continue
    cat_soup = BeautifulSoup(cat_page.content, 'html.parser')
    cat_bf = cat_soup.find_all('div',attrs={"class":"c-categories-carousel__item"})
    if cat_bf:
        #get sub-categories
        for sub in cat_bf:
            sub_cat = sub.a.get('href')
            sub_category  = sub.get_text('href')
            if 'https' in sub_cat:
                sub_cat_link = sub_cat
            else:
                sub_cat_link = base_page + sub_cat
            print(sub_cat_link)
            try:
                sub_cat_page = requests.get(sub_cat_link)
            except:
                continue
            sub_cat_soup = BeautifulSoup(sub_cat_page.content, 'html.parser')
            #check for sub_sub
            sub_sub_cat_list = sub_cat_soup.find_all('div',attrs={"class":"c-categories-carousel__item"})
            if sub_sub_cat_list:
                for sub_sub in sub_sub_cat_list:
                    sub_sub_cat = sub_sub.a.get('href')
                    sub_sub_category = sub_sub.get_text('href')
                    if '?' in sub_sub_cat:
                        sub_sub_cat_link = base_page + sub_sub_cat +'&size=100'
                    else:
                        sub_sub_cat_link = base_page + sub_sub_cat +'?size=100'
                    print(sub_sub_cat_link)
                    try:
                        sub_sub_cat_page = requests.get(sub_sub_cat_link)
                    except:
                        continue
                    sub_sub_cat_soup = BeautifulSoup(sub_sub_cat_page.content, 'html.parser')
                    #check for 3rd layer sub cat
                    sub_sub_sub_cat_list =  sub_sub_cat_soup.find_all('div',attrs={"class":"c-categories-carousel__item"})
                    if sub_sub_sub_cat_list:
                        for sub_sub_sub in sub_sub_sub_cat_list:
                            sub_sub_sub_cat = sub_sub_sub.a.get('href')
                            sub_sub_sub_category = sub_sub_sub.get_text('href')
                            sub_sub_sub_cat_link = base_page + sub_sub_sub_cat +'&size=100'
                            print(sub_sub_sub_cat_link)
                            try:
                                sub_sub_sub_cat_page = requests.get(sub_sub_sub_cat_link)
                            except:
                                continue
                            sub_sub_sub_cat_soup = BeautifulSoup(sub_sub_sub_cat_page.content, 'html.parser')
                            #extraction sub-sub-sub
                            try:
                                n_items = int(sub_sub_sub_cat_soup.find('span',attrs={"class":"c-pagination__results"}).get_text().split(' ')[0])
                            except:
                                continue
                            item_links = sub_sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                            print('extracting items from sub-sub-sub-category %s with %i items' %(sub_sub_sub_category, n_items))
                            for item in item_links:
                                data_list.append(construct_data(item,main_category, sub_category, sub_sub_category, sub_sub_sub_category))
                            if n_items > 100:
                                if '&page=' in sub_sub_sub_cat_link:
                                    sub_sub_sub_cat_link = sub_sub_sub_cat_link.replace('&page=0','&page=1')
                                else:
                                    sub_sub_sub_cat_link = sub_sub_sub_cat_link + '&page=1'
                                sub_sub_sub_cat_page = requests.get(sub_sub_sub_cat_link)
                                sub_sub_sub_cat_soup = BeautifulSoup(sub_sub_sub_cat_page.content, 'html.parser')
                                item_links = sub_sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                                for item in item_links:
                                    data_list.append(construct_data(item,main_category, sub_category, sub_sub_category, sub_sub_sub_category))
                            if n_items > 200: 
                                sub_sub_sub_cat_link = sub_sub_sub_cat_link.replace('&page=1','&page=2')
                                sub_sub_sub_cat_page = requests.get(sub_sub_sub_cat_link)
                                sub_sub_sub_cat_soup = BeautifulSoup(sub_sub_sub_cat_page.content, 'html.parser')
                                item_links = sub_sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                                for item in item_links:
                                    data_list.append(construct_data(item,main_category, sub_category, sub_sub_category, sub_sub_sub_category))
                            if n_items > 300: 
                                sub_sub_sub_cat_link = sub_sub_sub_cat_link.replace('&page=2','&page=3')
                                sub_sub_sub_cat_page = requests.get(sub_sub_sub_cat_link)
                                sub_sub_sub_cat_soup = BeautifulSoup(sub_sub_sub_cat_page.content, 'html.parser')
                                item_links = sub_sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                                for item in item_links:
                                    data_list.append(construct_data(item,main_category, sub_category, sub_sub_category, sub_sub_sub_category))
                            if n_items > 400: 
                                sub_sub_sub_cat_link = sub_sub_sub_cat_link.replace('&page=3','&page=4')
                                sub_sub_sub_cat_page = requests.get(sub_sub_sub_cat_link)
                                sub_sub_sub_cat_soup = BeautifulSoup(sub_sub_sub_cat_page.content, 'html.parser')
                                item_links = sub_sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                                for item in item_links:
                                    data_list.append(construct_data(item,main_category, sub_category, sub_sub_category, sub_sub_sub_category))
                    else:
                    #extraction sub-sub
                        try:
                            n_items = int(sub_sub_cat_soup.find('span',attrs={"class":"c-pagination__results"}).get_text().split(' ')[0])
                        except:
                            continue
                        item_links = sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                        print('extracting items from sub-sub-category %s with %i items' %(sub_sub_category, n_items))
                        for item in item_links:
                            data_list.append(construct_data(item,main_category, sub_category, '-', sub_sub_category))
                        if n_items > 100:
                            if '&page=' in sub_sub_cat_link:
                                sub_sub_cat_link = sub_sub_cat_link.replace('&page=0','&page=1')
                            else:
                                sub_sub_cat_link = sub_sub_cat_link + '&page=1'
                            sub_sub_cat_page = requests.get(sub_sub_cat_link)
                            sub_sub_cat_soup = BeautifulSoup(sub_sub_cat_page.content, 'html.parser')
                            item_links = sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                            for item in item_links:
                                data_list.append(construct_data(item,main_category, sub_category, '-', sub_sub_category))
                        if n_items > 200: 
                            sub_sub_cat_link = sub_sub_cat_link.replace('&page=1','&page=2')
                            sub_sub_cat_page = requests.get(sub_sub_cat_link)
                            sub_sub_cat_soup = BeautifulSoup(sub_sub_cat_page.content, 'html.parser')
                            item_links = sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                            for item in item_links:
                                data_list.append(construct_data(item,main_category, sub_category, '-', sub_sub_category))
                        if n_items > 300: 
                            sub_sub_cat_link = sub_sub_cat_link.replace('&page=2','&page=3')
                            sub_sub_cat_page = requests.get(sub_sub_cat_link)
                            sub_sub_cat_soup = BeautifulSoup(sub_sub_cat_page.content, 'html.parser')
                            item_links = sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                            for item in item_links:
                                data_list.append(construct_data(item,main_category, sub_category, '-', sub_sub_category))
                        if n_items > 400: 
                            sub_sub_cat_link = sub_sub_cat_link.replace('&page=3','&page=4')
                            sub_sub_cat_page = requests.get(sub_sub_cat_link)
                            sub_sub_cat_soup = BeautifulSoup(sub_sub_cat_page.content, 'html.parser')
                            item_links = sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                            for item in item_links:
                                data_list.append(construct_data(item,main_category, sub_category, '-', sub_sub_category))
                        if n_items > 500: 
                            sub_sub_cat_link = sub_sub_cat_link.replace('&page=4','&page=5')
                            sub_sub_cat_page = requests.get(sub_sub_cat_link)
                            sub_sub_cat_soup = BeautifulSoup(sub_sub_cat_page.content, 'html.parser')
                            item_links = sub_sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                            for item in item_links:
                                data_list.append(construct_data(item,main_category, sub_category, '-', sub_sub_category))
            else:
            #extract sub-cat items
                sub_cat_link = sub_cat_link + '?size=100'
                try:
                    sub_cat_page = requests.get(sub_cat_link)
                except:
                    continue
                sub_cat_soup = BeautifulSoup(sub_cat_page.content, 'html.parser')
                try:
                    n_items = int(sub_cat_soup.find_all('span',attrs={"class":"c-pagination__results"}).get_text().split(' ')[0])
                except:
                    continue
                item_links = sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                print('extracting items from sub-category %s with %i items' %(sub_category, n_items))
                for item in item_links:
                    data_list.append(construct_data(item,main_category, '-', '-', sub_category))
                if n_items > 100:
                    if '&page=' in sub_cat_link:
                        sub_cat_link = sub_cat_link.replace('&page=0','&page=1')
                    else:
                        sub_cat_link = sub_cat_link + '&page=1'
                    sub_cat_page = requests.get(sub_cat_link)
                    sub_cat_soup = BeautifulSoup(sub_cat_page.content, 'html.parser')
                    item_links = sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                    for item in item_links:
                        data_list.append(construct_data(item,main_category, '-', '-', sub_category))
                if n_items > 200: 
                    sub_cat_link = sub_cat_link.replace('&page=1','&page=2')
                    sub_cat_page = requests.get(sub_cat_link)
                    sub_cat_soup = BeautifulSoup(sub_cat_page.content, 'html.parser')
                    item_links = sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                    for item in item_links:
                        data_list.append(construct_data(item,main_category, '-', '-', sub_category))
                if n_items > 300: 
                    sub_cat_link = sub_cat_link.replace('&page=2','&page=3')
                    sub_cat_page = requests.get(sub_cat_link)
                    sub_cat_soup = BeautifulSoup(sub_cat_page.content, 'html.parser')
                    item_links = sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                    for item in item_links:
                        data_list.append(construct_data(item,main_category, '-', '-', sub_category))
                if n_items > 400: 
                    sub_cat_link = sub_cat_link.replace('&page=3','&page=4')
                    sub_cat_page = requests.get(sub_cat_link)
                    sub_cat_soup = BeautifulSoup(sub_cat_page.content, 'html.parser')
                    item_links = sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                    for item in item_links:
                        data_list.append(construct_data(item,main_category, '-', '-', sub_category))
                if n_items > 500: 
                    sub_cat_link = sub_cat_link.replace('&page=4','&page=5')
                    sub_cat_page = requests.get(sub_cat_link)
                    sub_cat_soup = BeautifulSoup(sub_cat_page.content, 'html.parser')
                    item_links = sub_cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
                    for item in item_links:
                        data_list.append(construct_data(item,main_category, '-', '-', sub_category))
    else:
        cat_link = cat_link + '?size=100'
        try:
            cat_page = requests.get(cat_link)
        except:
            continue
        cat_soup = BeautifulSoup(cat_page.content, 'html.parser')
        try:
            n_items = int(cat_soup.find_all('span',attrs={"class":"c-pagination__results"}).get_text().split(' ')[0])
        except:
            continue
        item_links = cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
        print('extracting items from main category %s with %i items' %(main_category, n_items))
        for item in item_links:
            data_list.append(construct_data(item,main_category, '-', '-', main_category))
        if n_items > 100:
            if '&page=' in cat_link:
                cat_link = cat_link.replace('&page=0','&page=1')
            else:
                cat_link = cat_link + '&page=1'
            cat_page = requests.get(cat_link)
            cat_soup = BeautifulSoup(cat_page.content, 'html.parser')
            item_links = cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
            for item in item_links:
                data_list.append(construct_data(item,main_category, '-', '-', main_category))
        if n_items > 200: 
            cat_link = cat_link.replace('&page=1','&page=2')
            cat_page = requests.get(cat_link)
            cat_soup = BeautifulSoup(cat_page.content, 'html.parser')
            item_links = cat_soup.find_all('div', attrs = {'class':'c-product-tile__image'})
            for item in item_links:
                data_list.append(construct_data(item,main_category, '-', '-', main_category))
#store and save
#%%
print('saving dataframe with %i items' %(len(data_list)))
data_df = pd.DataFrame(data_list)
data_df = data_df.drop_duplicates(subset = ['Merk','Product naam','Product info','Prijs', 'Inhoud of aantallen'])
data_df.to_excel('kruidvat_dataset.xlsx')



#%%
