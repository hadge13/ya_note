from http import HTTPStatus
from django.contrib.auth import get_user_model
from notes.models import Note

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

# Получаем модель пользователя.
User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Великий автор')
        cls.reader = User.objects.create(username='Читатель Петя')
        # Создаем заметку 
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='some_slug',
            author=cls.author,)
        # cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        # cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

       
    #Отдельная заметка передается на страницу со списком заметок в списке object_list
    # словаря context
    #в список заметок одного пользователя не попадают заметки другого

    def test_note_in_object_list_author(self):
        url = reverse('notes:list')
        self.client.force_login(self.author)
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_note_in_object_list_another_user(self):
        url = reverse('notes:list')
        self.client.force_login(self.reader)
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)
    
    #На страницы создания и редактирования заметки передаются формы
         
    def test_author_has_form(self):
        urls = (
            ('notes:add', None),      #  Страница добавления заметки
            ('notes:edit', (self.note.slug,)) # Страниц редактирования
        )
        for name, args in urls:
            self.client.force_login(self.author)
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)  
                self.assertIn('form', response.context) 