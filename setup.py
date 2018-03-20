from setuptools import setup
setup(
  name = 'sanic-aiopylimit',
  packages = ['sanic_aiopylimit'],
  description = 'A utlity package to help with distributed rate limiting with sanic and redis',
  author='David Markey',
  author_email='david@dmarkey.com',
  use_scm_version=True,
  setup_requires=['setuptools_scm'],
  url='https://github.com/dmarkey/sanic-aiopylimit',
  install_requires=[
      'aiopylimit<=0.2.2',
  ],
  keywords=['rate limiting', 'throttle', 'redis', 'asyncio', 'sanic'],
  classifiers=[],
)
