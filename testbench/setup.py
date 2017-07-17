from setuptools import setup

setup(name='wcd_testbench',
      version='0.1',
      description='testbench',
      url='github.com/bgrevelt/Thesis',
      author='Bouke Grevelt',
      author_email='b.grevelt@gmail.com',
      license='MIT',
      #install_requires=['matplotlib', 'numpy'],
      dependency_links=['https://github.com/bgrevelt/Thesis/raw/master/gwf/dist/gwf-0.1-py3.5.egg#egg=gwf-0.1'],
      zip_safe=False)
