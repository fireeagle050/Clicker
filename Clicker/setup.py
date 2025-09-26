from setuptools import setup, find_packages

setup(
    name="Clicker",
    version="0.1.0",
    author="Fire Eagle",
    description="An advanced automation tool for automating mouse and keyboard actions.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/Clicker",  # Replace with your actual URL
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pynput",
        "Pillow",
    ],
    entry_points={
        "console_scripts": [
            "clicker=Clicker.Clicker:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)