from pathlib import Path
import configparser


file_config = Path(__file__).parent.parent.joinpath("config.ini")


from mongoengine import connect


config = configparser.ConfigParser()
config.read(file_config)


mongodb_user_name = config.get("DEV_DB", "USER_NAME")
mongodb_password = config.get("DEV_DB", "MONGODB_PASSWORD")
mongodb_name = config.get("DEV_DB", "DB_NAME")
domain = config.get("DEV_DB", "DOMAIN")


connect(
    host=f"""mongodb+srv://{mongodb_user_name}:{mongodb_password}@{domain}/{mongodb_name}?retryWrites=true&w=majority""",
    ssl=True,
)
