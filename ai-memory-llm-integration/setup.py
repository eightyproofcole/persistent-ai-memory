from setuptools import setup, find_packages

setup(
    name='ai-memory-llm-integration',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='Integration of Persistent AI Memory System with LLMs',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'watchdog',
        'sqlite3',  # Add any other dependencies required for your project
        # Include any additional libraries needed for LLM integration
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)