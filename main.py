import os
import asyncio
from gtts import gTTS
import speech_recognition as sr
from googletrans import Translator
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from pydantic import BaseModel


class VideoProcessor:
    def __init__(self, input_directory: str, source_language: str, target_language: str, output_directory: str):
        """
        Конструктор класса VideoProcessor.

        :param input_directory: Путь к директории с видеофайлами.
        :param source_language: Исходный язык аудио в видеофайлах.
        :param target_language: Целевой язык для перевода.
        :param output_directory: Путь к директории, в которой будут сохранены обработанные видеофайлы.
        """
        self.input_directory = input_directory
        self.source_language = source_language
        self.target_language = target_language
        self.output_directory = output_directory

    @staticmethod
    async def generate_audio_path(video_path: str, suffix: str) -> str:
        """
        Генерация пути к аудиофайлу на основе пути к видеофайлу и суффикса.

        :param video_path: Путь к исходному видеофайлу.
        :param suffix: Суффикс для нового аудиофайла.
        :return: Путь к новому аудиофайлу.
        """
        return video_path.replace(".mp4", suffix)

    @staticmethod
    async def remove_temp_files(file: str) -> None:
        """
        Удаление временных файлов.

        :param file: Путь к файлу для удаления.
        """
        if os.path.exists(file):
            os.remove(file)

    async def convert_video_to_audio(self, video_path: str) -> str:
        """
        Конвертация видео в аудио и возврат пути к аудиофайлу.

        :param video_path: Путь к исходному видеофайлу.
        :return: Путь к новому аудиофайлу.
        """
        audioclip_path = await self.generate_audio_path(video_path, "_audio.wav")
        videoclip = VideoFileClip(video_path)
        audioclip = videoclip.audio
        audioclip.write_audiofile(audioclip_path, codec='pcm_s16le')
        return audioclip_path

    async def recognize_speech(self, audio_path: str) -> str:
        """
        Распознавание речи в аудиофайле и возврат распознанного текста.

        :param audio_path: Путь к аудиофайлу с речью.
        :return: Распознанный текст.
        """
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language=self.source_language)
        return text

    async def translate_text(self, text: str) -> str:
        """
        Перевод текста с исходного языка на целевой и возврат переведенного текста.

        :param text: Текст для перевода.
        :return: Переведенный текст.
        """
        translator = Translator()
        translation = translator.translate(text, dest=self.target_language)
        return translation.text

    async def synthesize_and_save_audio(self, text: str, audio_path: str) -> None:
        """
        Синтез речи из текста и сохранение аудиофайла.

        :param text: Текст для синтеза.
        :param audio_path: Путь для сохранения аудиофайла.
        """
        myobj = gTTS(text=text, lang=self.target_language, slow=False)
        myobj.save(audio_path)

    async def generate_output_video_path(self, video_path: str) -> str:
        """
        Генерация пути к выходному видеофайлу с переведенным аудио.

        :param video_path: Путь к исходному видеофайлу.
        :return: Путь к выходному видеофайлу.
        """
        return os.path.join(
            self.output_directory,
            f"{os.path.basename(video_path).replace('.mp4', f'_translated_{self.target_language}.mp4')}"
        )

    @staticmethod
    async def add_translated_audio_to_video(video_path: str, audio_path: str, output_path: str) -> None:
        """
        Добавление переведенного аудио к видео и сохранение нового видеофайла.

        :param video_path: Путь к исходному видеофайлу.
        :param audio_path: Путь к аудиофайлу с переведенной речью.
        :param output_path: Путь для сохранения нового видеофайла.
        """
        videoclip = VideoFileClip(video_path)
        audioclip = AudioFileClip(audio_path)
        new_audioclip = CompositeAudioClip([audioclip])
        videoclip.audio = new_audioclip
        videoclip.write_videofile(output_path)

    async def process_video(self, video_path: str) -> None:
        """
        Обработка видеофайла: конвертация в аудио, распознавание речи, перевод текста, создание нового аудио и видео.

        :param video_path: Путь к исходному видеофайлу.
        """
        audio_path = await self.convert_video_to_audio(video_path)
        recognized_text = await self.recognize_speech(audio_path)
        translated_text = await self.translate_text(recognized_text)
        audio_translated_path = await self.generate_audio_path(video_path, "_translated_audio.wav")
        await self.synthesize_and_save_audio(translated_text, audio_translated_path)
        output_video_path = await self.generate_output_video_path(video_path)
        await self.add_translated_audio_to_video(video_path, audio_translated_path, output_video_path)
        await self.remove_temp_files(audio_path)
        await self.remove_temp_files(audio_translated_path)

    async def main(self) -> None:
        """
        Основной метод, который выполняет обработку всех видеофайлов в директории и сохраняет результаты.
        """
        if not os.path.exists(self.output_directory):
            os.mkdir(self.output_directory)

        input_files = [f for f in os.listdir(self.input_directory) if f.endswith('.mp4')]
        tasks = []
        for video_file in input_files:
            video_path = os.path.join(self.input_directory, video_file)
            task = self.process_video(video_path)
            tasks.append(task)
        await asyncio.gather(*tasks)


class VideoProcessorInput(BaseModel):
    input_directory: str
    source_language: str
    target_language: str
    output_directory: str


if __name__ == "__main__":
    input_data = VideoProcessorInput(
        input_directory="f",
        source_language="en-US",
        target_language="ru",
        output_directory="translated_files"
    )

    video_processor = VideoProcessor(
        input_directory=input_data.input_directory,
        source_language=input_data.source_language,
        target_language=input_data.target_language,
        output_directory=input_data.output_directory
    )

    asyncio.run(video_processor.main())
