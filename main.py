import asyncio
from decorator_handler import error_handler
from validator import VideoProcessorInput
from video_processor import VideoProcessor


@error_handler
async def main():
    input_data = VideoProcessorInput(
        input_directory="files", source_language="en-US",
        target_language="ru", output_directory="translated_files", workers=32
    )
    video_processor = VideoProcessor(**input_data.model_dump())
    await video_processor.main()


if __name__ == "__main__":
    asyncio.run(main())
