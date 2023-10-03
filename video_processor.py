import os
import asyncio
from validator import target_language_annotated, source_language_annotated
from concurrent.futures import ThreadPoolExecutor
from gtts import gTTS
import speech_recognition as sr
from googletrans import Translator
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.editor import VideoFileClip, CompositeAudioClip


class VideoProcessor:
    def __init__(self, input_directory: str, source_language: source_language_annotated,
                 target_language: target_language_annotated, output_directory: str,
                 workers: int):
        """
        Конструктор класса VideoProcessor.

        :param input_directory: Путь к директории с видеофайлами.
        :param source_language: Исходный язык аудио в видеофайлах.
        :param target_language: Целевой язык для перевода.
        :param output_directory: Путь к директории, в которой будут сохранены обработанные видеофайлы.
        :param workers: Количество потоков.
        """
        self.input_directory = input_directory
        self.source_language = source_language
        self.target_language = target_language
        self.output_directory = output_directory
        self.workers = workers
        self.unrecognized_audio_files = []

    @staticmethod
    def generate_audio_path(video_path: str, suffix: str) -> str:
        """
        Генерация пути к аудиофайлу на основе пути к видеофайлу и суффикса.

        :param video_path: Путь к исходному видеофайлу.
        :param suffix: Суффикс для нового аудиофайла.
        :return: Путь к новому аудиофайлу.
        """
        return video_path.replace(".mp4", suffix)

    @staticmethod
    def remove_temp_files(file: str) -> None:
        """
        Удаление временных файлов.

        :param file: Путь к файлу для удаления.
        """
        if os.path.exists(file):
            os.remove(file)

    def convert_video_to_audio(self, video_path: str) -> str:
        """
        Конвертация видео в аудио и возврат пути к аудиофайлу.

        :param video_path: Путь к исходному видеофайлу.
        :return: Путь к новому аудиофайлу.
        """
        audioclip_path = self.generate_audio_path(video_path, "_audio.wav")
        videoclip = VideoFileClip(video_path)
        audioclip = videoclip.audio
        audioclip.write_audiofile(audioclip_path, codec='pcm_s16le')
        return audioclip_path

    def recognize_speech(self, audio_path: str, source_language: str) -> str:
        """
        Распознавание речи в аудиофайле и возврат распознанного текста.

        :param audio_path: Путь к аудиофайлу с речью.
        :param source_language: Язык аудио (например, 'en-US' для английского).
        :return: Распознанный текст.
        """
        r = sr.Recognizer()

        for _ in range(3):
            try:
                with sr.AudioFile(audio_path) as source:
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data, language=source_language)
                return text
            except sr.RequestError as e:
                print(f"Ошибка запроса к Google API: {e}")
                print("Повторная попытка...")
            except sr.UnknownValueError:
                print("Google API не смог распознать аудио.")
                self.unrecognized_audio_files.append(audio_path)

        return "Не удалось распознать аудио после нескольких попыток."

    def translate_text(self, text: str) -> str:
        """
        Перевод текста с исходного языка на целевой и возврат переведенного текста.

        :param text: Текст для перевода.
        :return: Переведенный текст.
        """
        translator = Translator()
        translation = translator.translate(text, dest=self.target_language)
        return translation.text

    def synthesize_and_save_audio(self, text: str, audio_path: str) -> None:
        """
        Синтез речи из текста и сохранение аудиофайла.

        :param text: Текст для синтеза.
        :param audio_path: Путь для сохранения аудиофайла.
        """
        myobj = gTTS(text=text, lang=self.target_language, slow=False)
        myobj.save(audio_path)

    def generate_output_video_path(self, video_path: str) -> str:
        """
        Генерация пути к выходному видеофайлу с переведенным аудио.

        :param video_path: Путь к исходному видеофайлу.
        :return: Путь к выходному видеофайлу.
        """
        return os.path.join(
            self.output_directory,
            f"{os.path.basename(video_path).replace('.mp4', f'_translated_{self.target_language}.mp4')}"
        )

    def add_translated_audio_to_video(self, video_path: str, audio_path: str, output_path: str) -> None:
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

    def process_video(self, video_path: str) -> None:
        """
        Обработка видеофайлов в параллельных потоках.

        :param video_path: Список путей к исходным видеофайлам.
        """
        audio_path = self.convert_video_to_audio(video_path)
        recognized_text = self.recognize_speech(audio_path, self.source_language)
        translated_text = self.translate_text(recognized_text)
        audio_translated_path = self.generate_audio_path(video_path, "_translated_audio.wav")
        self.synthesize_and_save_audio(translated_text, audio_translated_path)
        output_video_path = self.generate_output_video_path(video_path)
        self.add_translated_audio_to_video(video_path, audio_translated_path, output_video_path)
        self.remove_temp_files(audio_path)
        self.remove_temp_files(audio_translated_path)

    async def process_videos_concurrently(self, input_files):
        """
        Обработка видеофайла: конвертация в аудио, распознавание речи, перевод текста, создание нового аудио и видео.

        :param input_files: Путь к исходному видеофайлу.
        """
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = []

            for video_file in input_files:
                video_path = os.path.join(self.input_directory, video_file)
                task = loop.run_in_executor(executor, self.process_video, video_path)
                tasks.append(task)

            await asyncio.gather(*tasks)

    async def main(self) -> None:
        """
        Основной метод, который выполняет обработку всех видеофайлов в директории и сохраняет результаты.
        """
        if not os.path.exists(self.output_directory):
            os.mkdir(self.output_directory)

        try:
            input_files = [f for f in os.listdir(self.input_directory) if f.endswith('.mp4')]
            if not input_files:
                raise FileNotFoundError("Во входном каталоге не найдено файлов формата .mp4.")

            await self.process_videos_concurrently(input_files)
        except FileNotFoundError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        finally:
            if self.unrecognized_audio_files:
                await self.process_videos_concurrently(self.unrecognized_audio_files)
            exit()
