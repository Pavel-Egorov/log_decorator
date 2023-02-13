import os

from setuptools import setup


def read(path: str) -> str:
    """Try to read file by path or return empty string."""
    try:
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), path)) as f:
            return f.read()
    except Exception:  # noqa
        return ''


if __name__ == '__main__':
    setup(
        name='verbose_log_decorator',
        description='decorators to log function calls in verbose manner',
        license='Apache',
        url='https://github.com/Pavel-Egorov/log_decorator',
        version='1.1.2',
        author='Pavel Egorov',
        author_email='paveg.sp@gmail.com',
        maintainer='Pavel Egorov',
        maintainer_email='paveg.sp@gmail.com',
        keywords=['logging'],
        long_description=read('README.md'),
        long_description_content_type='text/markdown',
        packages=['log_decorator'],
        zip_safe=False,
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Natural Language :: English',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        install_requires=[
            'wrapt',
            'ujson',
        ],
        tests_require=[
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'flake8',
            'wemake-python-styleguide',
        ],
    )
