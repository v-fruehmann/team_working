# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 13:19:43 2021

@author: fadee
"""

# import neccessary libraries
import requests
from pprint import pprint
from bs4 import BeautifulSoup  
import re
import json
import pandas as pd
import numpy as np
import pandas_profiling
import time
import datetime
from datetime import datetime, timedelta

url = 'https://auto.ru/moskva/cars/' # url for cars in moscow region


# перечень брендов авто, которые будут парситься
brands = [
    'audi', 'BMW', 'chery', 'Chevrolet', 'Citroen', 'Daewoo', 'Ford', 'Geely',
    'Honda', 'Hyundai', 'Kia', 'vaz', 'land_rover', 'Lexus', 'Mazda',
    'Mercedes', 'Mitsubishi', 'Nissan', 'Opel', 'Peugeot', 'Renault', 'Skoda',
    'Subaru', 'Suzuki', 'Toyota', 'Volkswagen', 'Volvo', 'alfa_romeo',
    'aston_martin', 'Auburn', 'AURUS', 'Austin', 'Bentley', 'Chrysler',
    'Ferrari', 'Fiat', 'GMC', 'Hummer', 'Infiniti', 'SEAT', 'Tesla', 'zaz',
    'uaz', 'gaz', 'moscvich'
]

# функция получения информации с главной страницы авто
def car_info(page):
    cars = []
    for text in page.find_all('span', class_='CardInfoRow__cell'):
        cars.append(text.text)
    cars = np.asarray(cars).reshape(int(len(cars)/2), 2)
    return cars

# создание датасета в который будет записываться информация по авто
df_car = pd.DataFrame()

# начало парсинга

for car_brand in brands:
    brand_url = url + car_brand + '/used/?page='  # url на конкретную марку
    for number in range(1, 100):  # цикл по 99 страницам сайта
        response = requests.get(brand_url + str(number),
                                headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:  # проверка отклика с сайта
            page = BeautifulSoup(response.content.decode('utf-8'),
                                 'html.parser')
            link_list = page.find_all(
                'a', class_='Link ListingItemTitle-module__link'
            )  # список ссылок на авто
            if len(link_list) != 0:
                for link in link_list:
                    time.sleep(1)  # делаем задержку парсинга
                    print(link['href'])
                    try:
                        response = requests.get(link['href'])

                        if response.status_code == 200:
                            page = BeautifulSoup(
                                response.content.decode('utf-8'),
                                'html.parser')  # получение страницы
                            car_info = page.find('script',
                                                 type='application/ld+json')
                            # не работал метод text, ментор подсказал такое решение
                            # обрезаем начало и конец текста со страницы и отправляем текст в json
                            start, end = '<script type="application/ld+json">', '</script>'
                            result_dict = json.loads(
                                str(car_info)[len(start):-len(end)])
                            # получаем дату и цену авто. если дата старше 2004 года и имеется цена
                            # то продолжаем парсить
                            production_year = result_dict['productionDate']
                            price = result_dict['offers']['price']

                            if (production_year >= 2005) and (price > 0):
                                # получаем необходимые поля, как в тестовом датасете
                                body_type = result_dict['bodyType']
                                brand = result_dict['brand']
                                car_url = link
                                color = result_dict['color']
                                description = result_dict['description']
                                fuelType = result_dict['fuelType']
                                image = result_dict['image']
                                modelDate = result_dict['modelDate']
                                priceCurrency = result_dict['offers'][
                                    'priceCurrency']
                                numberOfDoors = result_dict['numberOfDoors']
                                car_gear = result_dict['vehicleTransmission']
                                vehicleConfiguration = result_dict[
                                    'vehicleConfiguration']
                                engineDisplacement = result_dict[
                                    'vehicleEngine']['engineDisplacement']
                                engine_power = result_dict['vehicleEngine'][
                                    'enginePower']
                                engine_name = result_dict['vehicleEngine'][
                                    'name']

                                # некоторую информацию, аналогичную тестовому датасету, собирали таким образом
                                page_t = page.find('script',
                                                   id="initial-state")
                                start, end = '<script id="initial-state" nonce="mB1ltaadK7jA+Dz5wF8hOA==" type="application/json">', '</script>'
                                result_dict = json.loads(
                                    str(page_t)[len(start):-len(end)])

                                sell_id = result_dict['card']['id']
                                super_gen = result_dict['card'][
                                    'vehicle_info']['super_gen']
                                steering_wheel = result_dict['card'][
                                    'vehicle_info']['steering_wheel']
                                ut = result_dict['card']['additional_info'][
                                    'creation_date']
                                vendor = result_dict['card']['vehicle_info'][
                                    'vendor']
                                complectation_dict = result_dict['card'][
                                    'vehicle_info']['complectation']
                                equipment_dict = result_dict['card'][
                                    'vehicle_info']['equipment']
                                model_info = result_dict['card'][
                                    'vehicle_info']['model_info']
                                model_name = result_dict['card'][
                                    'vehicle_info']['model_info']['name']

                                try:  # в процессе парсинга заметил что не все авто имеют информацию о пробеге
                                    mileage = result_dict['card']['state'][
                                        'mileage']
                                except:
                                    mileage = 0
                                # получение последней информации с помощью функции car_info
                                for item, value in car_info(page):
                                    if item == 'Привод': car_lead = value
                                    if item == 'Руль': car_side = value
                                    if item == 'Состояние':
                                        car_condition = value
                                    if item == 'Владельцы': car_owners = value
                                    if item == 'ПТС': PTS = value
                                    if item == 'Владение': ownership = value
                                    if item == 'Таможня': customer = value
                                print(customer)
                                # создаем список со значениями для датасета
                                row = {
                                    'bodyType': body_type,
                                    'brand': brand,
                                    'car_url': link['href'],
                                    'color': color,
                                    'complectation_dict': complectation_dict,
                                    'description': description,
                                    'engineDisplacement': engineDisplacement,
                                    'enginePower': engine_power,
                                    'equipment_dict': equipment_dict,
                                    'fuelType': fuelType,
                                    'image': image,
                                    'mileage': mileage,
                                    'modelDate': modelDate,
                                    'model_info': model_info,
                                    'model_name': model_name,
                                    'name': engine_name,
                                    'numberOfDoors': numberOfDoors,
                                    'parsing_unixtime': ut,
                                    'productionDate': production_year,
                                    'sell_id': sell_id,
                                    'super_gen': super_gen,
                                    'vehicleConfiguration':
                                    vehicleConfiguration,
                                    'vehicleTransmission': car_gear,
                                    'vendor': vendor,
                                    'Владельцы': car_owners,
                                    'Владение': ownership,
                                    'ПТС': PTS,
                                    'Привод': car_lead,
                                    'Руль': car_side,
                                    'Состояние': car_condition,
                                    'Таможня': customer,
                                    'price': price,
                                    'priceCurrency': priceCurrency
                                }
                                # записываем все в датасет
                                df_car = pd.concat(
                                    [df_car, pd.DataFrame([row])])
                    except:
                        pass
                        
df_car.to_csv(r'C:\Users\fadee\mySkillFactory\df_car_17_04.csv', index=False)                        