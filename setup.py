from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="altitude-summary",
    version="1.0.0",
    author="Karan Bhatia",
    author_email="karanbir88@gmail.com",
    description="Automated daily summaries for Altitude Gmail updates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/altitude-summary",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop", 
        "Topic :: Communications :: Email",
        "Topic :: Home and Family",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-auth>=2.23.0",
        "google-auth-oauthlib>=1.1.0", 
        "google-auth-httplib2>=0.1.0",
        "google-api-python-client>=2.100.0",
        "python-dateutil>=2.8.0",
    ],
)
