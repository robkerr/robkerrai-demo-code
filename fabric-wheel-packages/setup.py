'''
  setup.py creates the wheel file to upload to Fabric  
  to build a .whl file into the dist/ folder, run this command:
    python setup.py bdist_wheel
  
'''

from setuptools import setup, find_packages

setup(
    name='shared_utils', #needs to build fabric
    version='1.0.0',
    description='A sample library of utilities to use in Fabric notebooks',
    packages=find_packages(),  
    install_requires=['pyarrow'],
)
