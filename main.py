import logging
import json
import requests
from datetime import date
from TOKEN import VK_TOKEN


logging.basicConfig(level=logging.INFO, filename="logging.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


class VK:
    url_base = 'https://api.vk.com/method/'

    def __init__(self, token, owner_id):
        self.method = 'photos.get?'
        self.owner_id = owner_id
        self.params = {
            'owner_id': owner_id,
            'album_id': 'profile',
            'rev': False,
            'extended': True,
            'photo_sizes': True,
            'access_token': token,
            'v': '5.199'
        }

    def photos(self):
        logging.info(f'Запрос фотографий с профиля {self.owner_id} VK.')
        response = requests.get(self.url_base+self.method, params=self.params)
        return response.json()


class YandexDisk:
    def __init__(self, token):
        self.default_dict = 'VK'
        self.token = {'Authorization': token}
        self.url_base = 'https://cloud-api.yandex.net/v1/disk'
        self.url_create_folder = self.url_base + '/resources'
        self.create_dict = {'path': self.default_dict}
        self.get_link = self.url_create_folder + '/upload'

    def authorization(self):
        while True:
            try:
                logging.info(f'Авторизация Яндекс.Диска.')
                response = requests.get(self.url_base, headers=self.token)
                if response.status_code == 401:
                    logging.error(response.json().get('message') + ' Повторный запрос токена.')
                    new_token = input('Токен с Полигона Яндекс.Диска введен неверно. '
                                      'Введите токен с Полигона Яндекс.Диска:\n')
                    self.token = {'Authorization': new_token}
                if response.status_code == 200:
                    logging.info(f'Авторицаия Яндекс.Диска прошла успешно.')
                    break
            except UnicodeEncodeError:
                logging.error('Введены русские символы в токене с Полигона Яндекс.Диска. Повторный запрос токена.')
                new_token = input('Токен с Полигона Яндекс.Диска введен неверно. '
                                  'Введите токен с Полигона Яндекс.Диска:\n')
                self.token = {'Authorization': new_token}

    def create_folder(self):
        while True:
            response = requests.put(self.url_create_folder, params=self.create_dict, headers=self.token)
            logging.info(f'Создание папки по указанному пути "{self.default_dict}".')
            if response.status_code == 201:
                logging.info(f'Создана папка по указанному пути "{self.default_dict}".')
                break
            if response.status_code == 409:
                logging.warning(response.json().get('message'))
                logging.info(f'Замена пути "{self.default_dict}" на "{self.default_dict + str(date.today())}".')
                self.default_dict = self.default_dict + f'-{str(date.today())}'
                self.create_dict = {'path': self.default_dict}

    def upload_photo(self, url_photo, name_photo):
        while True:
            logging.info(f'Создание ресурса "{self.default_dict}/{name_photo}".')
            params_dict = {'path': f'{self.default_dict}/{name_photo}'}
            response = requests.get(self.get_link, params=params_dict, headers=self.token)
            if response.status_code == 409:
                logging.warning(response.json().get('message'))
                logging.info(f'Замена имени "{name_photo}" на "{name_photo+str(date.today())}".')
                name_photo += f'-{str(date.today())}'
                continue
            url_for_upload = response.json().get('href')
            data = requests.get(url_photo)
            response = requests.put(url=url_for_upload, data=data)
            if response.status_code == 201:
                logging.info(f'Ресурс "{self.default_dict}/{name_photo}" создан.')
                break
        return name_photo


if __name__ == "__main__":
    logging.info(f'Запрос токена с Полигона Яндекс.Диска.')
    input_token = input('Введите токен с Полигона Яндекс.Диска:\n')
    ya = YandexDisk(token=input_token)

    logging.info(f'Запрос id пользователя vk.')
    input_owner_id = input('Введите id пользователя vk:\n')
    vk = VK(VK_TOKEN, input_owner_id)

    vk_j = vk.photos()
    count = 5
    vk_count = vk_j.get('response').get('count')
    logging.info(f'Профиль имеет {vk_count} фотографий.')
    if count > vk_count:
        count = vk_count

    vk_base_photo = []
    for i in vk_j.get('response').get('items'):
        n_photo = str(i.get('likes').get('count')) + '.jpg'
        for u in i.get('sizes'):
            if u.get('type') == 'z':
                u_photo = u.get('url')
                vk_base_photo.append([u_photo, n_photo])

    ya.authorization()
    ya.create_folder()
    len_photo = 0
    logging.info(f'Загрузка {count} файлов на Яндекс.Диск.')
    while count != len_photo:
        ya.upload_photo(vk_base_photo[len_photo][0], vk_base_photo[len_photo][1])
        info_json = {'file_name': vk_base_photo[len_photo][1],
                     'size': 'z'}
        save_json = json.dumps(info_json)
        logging.info(f'Сохранение информации о файле в папку json.')
        with open(f"json/{vk_base_photo[len_photo][1].replace('.jpg','')}.json", "w") as my_file:
            my_file.write(save_json)
        len_photo += 1

    print(f'Ссылка на Яндекс.Диск: https://disk.yandex.ru/client/disk/{ya.default_dict}')

