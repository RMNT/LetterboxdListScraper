import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='LetterboxdListScraper',
    version='0.0.3',
    author='Raminta Urbonavičiūtė',
    author_email='urbonaviciuteraminta@gmail.com',
    description='For getting unions of various lists from Letterboxd',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/RMNT/LetterboxdListScraper',
    project_urls = {
        "Bug Tracker":"https://github.com/RMNT/LetterboxdListScraper/issues"
    },
    license='MIT',
    packages=['LetterboxdListScraper'],
    install_requires=['requests', 'bs4'],
)
