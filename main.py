
import json
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def main():
    with open("requirements.txt", "r") as file:
        lines = file.readlines()

    checked = len(lines)
    not_found = 0
    incompatible = 0

    highest_minimum = None
    highest_package = None

    for line in lines:
        line = line.strip()

        # Get package name and pinned version
        if "==" not in line:
            not_found += 1
            continue

        name, version = line.split("==", 1)
        name = name.strip()
        version = version.strip()

        if not name or not version:
            not_found += 1
            continue

        # 1. Check whether the package exists
        package_url = (
            f"https://pypi.org/pypi/{quote(name, safe='')}/json"
        )

        try:
            with urlopen(package_url, timeout=10) as response:
                json.load(response)

        except HTTPError as error:
            if error.code == 404:
                not_found += 1
                continue
            raise

        # 2. Check whether the exact version exists
        release_url = (
            f"https://pypi.org/pypi/"
            f"{quote(name, safe='')}/{quote(version, safe='')}/json"
        )

        try:
            with urlopen(release_url, timeout=10) as response:
                data = json.load(response)

        except HTTPError as error:
            if error.code == 404:
                not_found += 1
                continue
            raise

        # 3. Read Python version requirements
        requires_python = data["info"].get("requires_python")

        # No requirement means compatible
        if not requires_python:
            continue

        specifiers = SpecifierSet(requires_python)

        # Check Python 3.11 compatibility
        if not specifiers.contains("3.11"):
            incompatible += 1

        # 4. Find the highest minimum requirement
        for spec in specifiers:
            if spec.operator in (">=", ">", "~=", "=="):
                minimum = Version(spec.version)

                if highest_minimum is None or minimum > highest_minimum:
                    highest_minimum = minimum
                    highest_package = f"{name}=={version}"

    print("Dependencies checked:", checked)
    print("Not found on PyPI:", not_found)
    print("Incompatible with Python 3.11:", incompatible)

    if highest_package:
        print(
            f"Highest requirement: {highest_package} "
            f"(>={highest_minimum})"
        )
    else:
        print("Highest requirement: None")


if __name__ == "__main__":
    main()
