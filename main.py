import logging
import os

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType, File, Message
from aiogram.utils import executor
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

load_dotenv()
TOKEN_BOT = os.getenv('TOKEN_BOT')
TOKEN_OPENAI = os.getenv('TOKEN_OPENAI')
PATH_SAVE_VOICE = 'data/voice/'
PATH_SAVE_VIDEO_NOTE = 'data/video_note/'

logging.basicConfig(level=logging.INFO)

openai.api_key = TOKEN_OPENAI
bot = Bot(token=TOKEN_BOT)
dp = Dispatcher(bot)


async def convert_voice_to_text(path: str):
    """Конвертирует mp3 в текст с помощью openai."""
    return openai.Audio.transcribe("whisper-1", open(path, "rb"))['text']


async def get_text_voice(file: File, file_name: str, path: str):
    path_ogg = f'{path}/{file_name}.ogg'
    path_mp3 = f'{path}/{file_name}.mp3'
    await bot.download_file(file_path=file.file_path, destination=path_ogg)
    sound = AudioSegment.from_ogg(path_ogg)
    os.remove(path_ogg)
    sound.export(path_mp3, format='mp3')
    text = await convert_voice_to_text(path_mp3)
    os.remove(path_mp3)
    return text


async def get_text_video_note(file: File, file_name: str, path: str):
    path_mp4 = f'{path}/{file_name}.mp4'
    path_mp3 = f'{path}/{file_name}.mp3'
    await bot.download_file(file_path=file.file_path, destination=path_mp4)
    video = VideoFileClip(path_mp4)
    audio = video.audio
    audio.write_audiofile(path_mp3)
    video.close()
    audio.close()
    os.remove(path_mp4)
    text = await convert_voice_to_text(path_mp3)
    os.remove(path_mp3)
    return text


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """Обработка команды /start."""
    await message.reply('Привет! Я умею переводить голосовые сообщения в '
                        'текст.\nДля этого отправь мне голосовое сообщение или'
                        ' запиши кружочек. Ты также можешь переслать сообщения'
                        ' от других пользователей.')


@dp.message_handler(is_forwarded=False)
async def handle_forwarded_message(message: types.Message):
    """Обработка текстовых сообщений."""
    await message.reply('Обрабатываю только голосовые сообщения и кружочки!')


@dp.message_handler(content_types=[ContentType.VOICE])
async def voice_message_handler(message: Message):
    """Обработка голосовых сообщений."""
    voice = await message.voice.get_file()
    text = await get_text_voice(
        file=voice,
        file_name=voice.file_id,
        path=PATH_SAVE_VOICE
    )
    await message.reply(text)


@dp.message_handler(content_types=[ContentType.VIDEO_NOTE])
async def video_note_message_handler(message: Message):
    """Обработка видео-кружочков."""
    video_note = await message.video_note.get_file()
    text = await get_text_video_note(
        file=video_note,
        file_name=video_note.file_id,
        path=PATH_SAVE_VIDEO_NOTE
    )
    await message.reply(text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
