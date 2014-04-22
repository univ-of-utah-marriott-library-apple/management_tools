from distutils.core import setup

setup(
    name='Helpful Tools',
    version='0.9',
    url='https://github.com/univ-of-utah-marriott-library-apple/helpful_tools',
    author='Pierce Darragh, Marriott Library IT Services',
    author_email='mlib-its-mac-github@lists.utah.edu',
    description=('A suite of helpful scripts and packages to assist in administrating '
                 'OS X computers in distributed environments.'),
    license='MIT',
    packages=['helpful_tools'],
    package_dir={'helpful_tools': 'src/helpful_tools'},
    scripts=['scripts/app_lookup.py',
             'scripts/management_logger.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
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
