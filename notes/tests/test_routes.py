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
                url = reverse(name, args=args)
                response = self.client.get(url)    # неавторизованный пользователь
                self.assertEqual(response.status_code, HTTPStatus.OK) 


    # При попытке попасть на страницу списка заметок, страницу успешного создания заметки, 
    # страницу добавления заметки, редактирования или удаления
    # неавторизованный пользователь перенаправляется на страницу логина
    def test_list_add_done_edit_delete_note(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),       # Cтраница заметок
            ('notes:add', None),      #  Страница добавления заметки
            ('notes:success', None),     # Страница успеха
            ('notes:edit', (self.note.slug,)), # Страниц редактирования
            ('notes:delete', (self.note.slug,)), # Страниц редактирования
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)    # неавторизованный пользователь
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

    # Страницы списка заметок, добавления и успеха доступны 
    # аутентифицированному пользователю
    def test_list_add_done_note(self):
        urls = (
            ('notes:list', None),       # Cтраница заметок
            ('notes:add', None),      #  Страница добавления заметки
            ('notes:success', None),     # Страница успеха
        )
        for name, args in urls:
            self.client.force_login(self.author)
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)    
                self.assertEqual(response.status_code, HTTPStatus.OK)        
        