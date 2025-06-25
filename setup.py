from setuptools import setup, find_packages

setup(
    name='medpharm-bot',
    version='1.0.0',
    description='AI-powered Telegram expense tracking bot with reports',
    author='Jasur',
    packages=find_packages(),
    install_requires=[
        'aiogram==3.4.1',
        'reportlab',
        'aiohttp>=3.9.0',
        'python-dotenv',
        'matplotlib',
    ],
    include_package_data=True,
    python_requires='>=3.8',
)
