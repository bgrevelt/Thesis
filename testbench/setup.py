from setuptools import setup

setup(name='gwf',
      version='0.1',
      description='testbench',
      url='github.com/bgrevelt/Thesis',
      author='Bouke Grevelt',
      author_email='b.grevelt@gmail.com',
      license='MIT',
      install_required=['matplotlib', 'numpy'],
      dependency_links=['git+https://github.com/bgrevelt/Thesis/tree/master/gwf'],
      zip_safe=False)
