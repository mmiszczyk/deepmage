from setuptools import setup

setup(
    name='deepmage',
    version='0.2',
    packages=['libdeepmage'],
    url='https://github.com/mmiszczyk/deepmage',
    license='GPL 3',
    author='Maciej Miszczyk',
    author_email='maciejmmiszczyk@gmail.com',
    description='Hex editor for bit-level occultism',
    install_requires=['hy', 'bitstring', 'asciimatics'],
    python_requires='>=3',
    package_data={'': '*.hy'},
    scripts=('deepmage', 'deepmage-hexdump', 'deepmage-hexparse'),
    classifiers=('Programming Language :: Python :: 3',
                 'Programming Language :: Lisp',
                 'Operating System :: OS Independent',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Information Technology',
                 'Intended Audience :: System Administrators',
                 'Intended Audience :: Telecommunications Industry',
                 'Topic :: Security',
                 'Topic :: Software Development :: Embedded Systems')
)
