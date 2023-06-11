from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify
from notes.models import Note
from notes.forms import WARNING

# Получаем модель пользователя.
User = get_user_model()

class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        # одного логием в клиенте
        cls.author = User.objects.create(username='Великий автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # другого тоже логиним, он не автор
        cls.reader = User.objects.create(username='Читатель Петя')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
         # Создаем заметку 
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='some_slug',
            author=cls.author,)
        # Урлы
        cls.url = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        # Данные Post  запроса при создании заметки
        cls.form_data_note = {'title': 'Новый заголовок',
                              'text': 'Новый текст',
                              'slug': 'New_slug',
                              'author': cls.author}


    # Анонимный пользователь не может создать заметку
    # Одна заметка уже есть в базе, поэтому сравнение с 1
    def test_add_note_anonim(self):
        self.client.post(self.url, data=self.form_data_note)   
        count_notes = Note.objects.count()
        self.assertEqual(count_notes, 1)
    
    # залогиненый может
    def test_add_note_author(self):
        response = self.author_client.post(self.url, data=self.form_data_note)   
        count_notes = Note.objects.count()
        self.assertRedirects(response, self.url_success)
        self.assertEqual(count_notes, 2)
        new_note = Note.objects.get(id=2)
        self.assertEqual(new_note.title, self.form_data_note['title'])
        self.assertEqual(new_note.text, self.form_data_note['text'])
        self.assertEqual(new_note.slug, self.form_data_note['slug'])
        self.assertEqual(new_note.author, self.author)

    # Возможность создания 2 заметок с одинаковым slug
    def test_not_unique_slug(self):
        self.form_data_note['slug'] = self.note.slug
        # Пытаемся создать новую заметку:
        response = self.author_client.post(self.url, data=self.form_data_note)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        self.assertFormError(response, 'form', 'slug', errors=(self.note.slug + WARNING))
        # Убеждаемся, что количество заметок в базе осталось равным 1:
        assert Note.objects.count() == 1 

    # Пустое поле слаг формируется из поля title
    def test_empty_slug(self):
        # Убираем поле slug из словаря:
        self.form_data_note.pop('slug')
        response = self.author_client.post(self.url, data=self.form_data_note)
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, self.url_success)
        self.assertEqual(Note.objects.count(), 2) 
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get(id=2)
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data_note['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)

    # Автор может редактировать свои заметки, 
    def test_author_can_edit_note(self):
        # Получаем адрес страницы редактирования заметки:
        # В POST-запросе на адрес редактирования заметки
        # отправляем form_data - новые значения для полей заметки:
        response = self.author_client.post(self.edit_url, data=self.form_data_note)
        # Проверяем редирект:
        self.assertRedirects(response, self.url_success)
        # Обновляем объект заметки note: получаем обновлённые данные из БД:
        self.note.refresh_from_db()
        # Проверяем, что атрибуты заметки соответствуют обновлённым:
        self.assertEqual(self.note.title, self.form_data_note['title'])
        self.assertEqual(self.note.text, self.form_data_note['text'])
        self.assertEqual(self.note.slug, self.form_data_note['slug'])

    # Читатель не может редактировать заметки автора
    def test_reader_can_not_edit_note(self):
        # Получаем адрес страницы редактирования заметки:
        # В POST-запросе на адрес редактирования заметки
        # отправляем form_data - новые значения для полей заметки:
        response = self.reader_client.post(self.edit_url, data=self.form_data_note)
        # Проверяем редирект:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)  
        # Обновляем объект заметки note: получаем обновлённые данные из БД:
        note_from_db = Note.objects.get(id=self.note.id)
        # Проверяем, что атрибуты заметки соответствуют атрибутам до запроса
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    # Автор может удалять свои заметки, 
    def test_author_can_delete_note(self):
        response = self.author_client.post(self.delete_url)
        # Проверяем редирект:
        self.assertRedirects(response, self.url_success)
        assert Note.objects.count() == 0

    # Читатель не  может удалять заметки автора, 
    def test_reader_can_not_delete_note(self):
        response = self.reader_client.post(self.delete_url)
        # Проверяем редирект:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND) 
        assert Note.objects.count() == 1







       
        