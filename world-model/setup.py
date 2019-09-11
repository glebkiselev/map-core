from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='swm',
    version='1.0.0',
    packages=['swm', 'swm.components'],
    package_dir={'swm': 'src'},
    url='https://github.com/glebkiselev/map-core.git',
    license='',
    author='KiselevGA',
    author_email='kiselev@isa.ru',
    long_description=open('README.md').read(),
    install_requires=required,
    include_package_data=True
)