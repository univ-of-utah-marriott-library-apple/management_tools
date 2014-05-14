from distutils.core import setup

setup(
    name='Management Tools',
    version='1.3.1',
    url='https://github.com/univ-of-utah-marriott-library-apple/management_tools',
    author='Pierce Darragh, Marriott Library IT Services',
    author_email='mlib-its-mac-github@lists.utah.edu',
    description=('A suite of helpful scripts and packages to assist in administrating '
                 'OS X computers in distributed environments.'),
    license='MIT',
    packages=['management_tools'],
    package_dir={'management_tools': 'src/management_tools'},
    scripts=['scripts/app_lookup.py',
             'scripts/management_logger.py',
             'scripts/executable_bundler.py'],
    classifiers=[
        'Development Status :: 5 - Stable',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
)
