from pathlib import Path
from typing import List
from typing import Optional

from poetry.core.masonry.utils.include import Include


class PackageInclude(Include):
    def __init__(
        self,
        base: Path,
        include: str,
        formats: Optional[List[str]] = None,
        source: Optional[str] = None,
    ) -> None:
        self._package: Optional[str] = None
        self._is_package = False
        self._is_module = False
        self._source = source

        if source is not None:
            base = base / source

        super().__init__(base, include, formats=formats)
        self.check_elements()

    @property
    def package(self) -> Optional[str]:
        return self._package

    @property
    def source(self) -> Optional[str]:
        return self._source

    def is_package(self) -> bool:
        return self._is_package

    def is_module(self) -> bool:
        return self._is_module

    def refresh(self) -> "PackageInclude":
        super().refresh()

        return self.check_elements()

    def is_stub_only(self) -> bool:
        # returns `True` if this a PEP 561 stub-only package,
        # see [PEP 561](https://www.python.org/dev/peps/pep-0561/#stub-only-packages)
        return (self.package or "").endswith("-stubs") and all(
            el.suffix == ".pyi"
            or (el.parent.name == self.package and el.name == "py.typed")
            for el in self.elements
            if el.is_file()
        )

    def has_modules(self) -> bool:
        # Packages no longer need an __init__.py in python3, but there must
        # at least be one .py file for it to be considered a package
        return any(element.suffix == ".py" for element in self.elements)

    def check_elements(self) -> "PackageInclude":
        if not self._elements:
            raise ValueError(
                f"{self._base / self._include} does not contain any element"
            )

        root = self._elements[0]
        if len(self._elements) > 1:
            # Probably glob
            self._is_package = True
            self._package = root.parent.name

            if not self.is_stub_only() and not self.has_modules():
                raise ValueError(f"{root.name} is not a package.")

        else:
            if root.is_dir():
                # If it's a directory, we include everything inside it
                self._package = root.name
                self._elements: List[Path] = sorted(root.glob("**/*"))

                if not self.is_stub_only() and not self.has_modules():
                    raise ValueError(f"{root.name} is not a package.")

                self._is_package = True
            else:
                self._package = root.stem
                self._is_module = True

        return self
