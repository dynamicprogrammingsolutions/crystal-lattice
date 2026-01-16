from setuptools import setup


setup(
    name="dev_plugins",
    version="0.0.1",
    packages=["dev_plugins"],
    include_package_data=True,
    package_data={"dev_plugins": ["agent_plugin.json"]},
)
