from pydantic import ValidationError


def error_handler(func):
    """
    Декоратор для обработки ошибок в асинхронных функциях.

    :param func: Асинхронная функция, которая будет обернута декоратором.
    """

    async def wrapper():
        try:
            await func()
        except ValidationError as e:
            print("Ошибка проверки:")
            for error in e.errors():
                print(f"- {error['loc'][0]}: {error['msg']}")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        finally:
            exit()

    return wrapper
