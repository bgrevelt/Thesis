from setuptools import setup

setup(name='gwf',
      version='0.1',
      description='Library for reading and writing data in the generic water column format',
      url='http://github.com/bgrevelt/gwf',
      author='Bouke Grevelt',
      author_email='b.grevelt@gmail.com',
      license='MIT',
      packages=['gwf'],
      install_required=['matplotlib'],
      zip_safe=False)
