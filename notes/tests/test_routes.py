from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Великий автор')
        cls.reader = User.objects.create(username='Читатель Петя')
        
        # Создаем заметку 
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,)
  
    # Все страницы доступны неавторизованному пользователю
    def test_pages_availability(self):           
        urls = (
            ('notes:home', None),       # Главная страница
            ('users:login', None),      #  Страница входа в учётную запись 
            ('users:logout', None),     # Страница выхода
            ('users:signup', None),     # Страницы регистрации пользователей,
        )
        for name, args in urls:
            with self.subTest(name=name):
            # Передаём имя и позиционный аргумент в reverse()
            # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)    # неавторизованный пользователь
                self.assertEqual(response.status_code, HTTPStatus.OK) 


    # При попытке попасть на страницу создания заметки
    # неавторизованный пользователь перенаправляется на страницу логина
    def test_add_note(self):
        login_url = reverse('users:login')
        url = reverse('notes:add', None)  
        redirect_url = f'{login_url}?next={url}'  
        response = self.client.get(url)
        self.assertRedirects(response, redirect_url) 


    # Страницы отдельной заметки,  удаления и редактирования заметки доступны автору заметки.
    # но недоступны другим польzователям
    def test_availability_for_note_edit_and_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            for name in ('notes:detail',
                         'notes:edit',
                         'notes:delete',):
                with self.subTest(user=user, name=name):        
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
