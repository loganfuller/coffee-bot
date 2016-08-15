from setuptools import setup

setup(
    name="coffee-bot",
    version="0.1.0",
    description="Keep tabs on your office coffee with Slack and RPi",
    author="Logan Fuller",
    author_email="fuller.logan@gmail.com",
    url="https://github.com/loganfuller/coffee-bot",
    license="MIT",
    packages=["coffee-bot"],
    install_requires=[
        "slackclient"
        "Adafruit_GPIO"
        "Adafruit_SSD1306"
        "RPi.GPIO"
        "PIL",
    ],
)
