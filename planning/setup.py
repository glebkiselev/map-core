from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='planning',
    version='1.0.0',
    packages=['planning', 'planning.grounding', 'planning.parsers', 'planning.search', 'planning.agent'],
    package_dir={'planning': 'src'},
    url='https://github.com/glebkiselev/map-core.git',
    license='',
    author='KiselevGA',
    author_email='kiselev@isa.ru',
    long_description=open('README.md').read(),
    install_requires=required,
    include_package_data=True
)