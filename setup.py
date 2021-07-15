from setuptools import setup


setup(
    name='cldfbench_bowernpnygeo',
    py_modules=['cldfbench_bowernpnygeo'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'bowernpnygeo=cldfbench_bowernpnygeo:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
