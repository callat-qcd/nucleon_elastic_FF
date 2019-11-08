"""Module which interfaces lattedb entries to figure out which form factors are present
and which dependencies are needed.
"""
from typing import List, Optional, Tuple

from abc import ABC

from lattedb.project.formfac import models as ffmodels

from espressodb.base.models import Base
import espressodb.base.utilities.blackmagicsorcery as re


class DepenencyError(Exception):
    """Custom error to signalize problems with dependency
    """

    def __init__(
        self,
        message: str,
        source: Base,
        dependencies: Optional[List[Base]] = None,
        **kwargs,
    ):
        self.source = source
        self.dependencies = dependencies
        self.parameters = kwargs
        msg = message
        msg += f"\n\tsource={source}"
        if dependencies is not None:
            msg += (
                f"\n\tdependencies=["
                + ",\n\t\t".join([str(dep) for dep in dependencies])
                + "]"
            )
        for key, val in kwargs.items():
            msg += f"\n\t{key}={val}"
        super().__init__(msg)


def get_missing_disk_tsliced_saveraged_ffs(
    **kwargs,
) -> List[ffmodels.DiskTSlicedSAveragedFormFactor4DFile]:
    """Returns all t-sliced source averaged Form Factor 4D files on disk which have
    `exists = False`

    Argument:
        kwargs:
            Other field query parameters like, e.g., `ensemble="a12m180L"`.
            Multiple kwargs are searched with and `and`.
    """
    kwargs.pop("exists", None)
    return ffmodels.DiskTSlicedSAveragedFormFactor4DFile.objects.filter(
        exists=False, **kwargs
    )


class DependencyTracker(ABC):  # pylint: disable=too-few-public-methods
    """Abstract class for tracking dependencies
    """

    dependency: Base = None

    @classmethod
    def get_missing_deps_for_instance(cls, instance: "source",) -> List["dependency"]:
        """Finds dependencies of 'source'.

        Arguments:
            ff: The instance to look up missing dependencies

        Returns:
            A queryset of missing dependencies which are not yet on disk (but in the db).

        Raise:
            ValueError: If source_set string of 'source' input file is weired.
            DepenencyError: If dependencies are not in dependency table.
        """
        match = re.match(r"([0-9]+)\-([0-9]+)", instance.file.source_set)
        if not match:
            raise ValueError(
                f"Was not able to parse soruce set string: {instance.file.source_set}"
            )
        n_srcs = int(match.groups()[1]) - int(match.groups()[0])
        if n_srcs <= 0:
            raise ValueError(
                f"Src set {instance.file.source_set} means expecting {n_srcs} sources."
                " Abort."
            )

        query = {
            "file__ensemble": instance.file.ensemble,
            "file__stream": instance.file.stream,
            "file__source_set": instance.file.source_set,
            "file__configuration": instance.file.configuration,
            "file__t_separation": instance.file.t_separation,
        }
        dependencies = cls.dependency.objects.filter(**query)

        if dependencies.count() != n_srcs:
            raise DepenencyError(
                "Found less dependencies then expected from soruce set.",
                source=instance,
                dependencies=dependencies,
                expected_srcs=n_srcs,
                found_srcs=dependencies.count(),
            )

        return dependencies.filter(exists=False)

    @classmethod
    def get_missing_deps_for_set(cls, instances: List["source"]) -> List["dependency"]:
        """Finds dependencies of 'source'.

        Arguments:
            ff: The queryset of instances to look up missing dependencies

        Returns:
            A list of missing dependencies which are not yet on disk (but in the db).

        Raise:
            ValueError: If source_set string of 'source' input file is weired.
            DepenencyError: If dependencies are not in dependency table.
        """
        return [cls.get_missing_deps_for_instance(isinstance) for instance in instances]


class TSlicedSAveredTracker(DependencyTracker):  # pylint: disable=R0903
    """Class for tracking dependencies of t-sliced source averaged form factors
    """

    dependency = ffmodels.DiskTSlicedFormFactor4DFile


class TSlicedTracker(DependencyTracker):  # pylint: disable=R0903
    """Class for tracking dependencies of t-sliced form factors
    """

    dependency = ffmodels.DiskFormFactor4DFile


def get_dependencies_ts_sa_ff(
    ts_sa_ff: ffmodels.DiskTSlicedSAveragedFormFactor4DFile,
) -> Tuple[
    List[ffmodels.DiskTSlicedFormFactor4DFile],
    List[List[ffmodels.DiskFormFactor4DFile]],
]:
    """Tracks recursively missing instances for DiskTSlicedSAveragedFormFactor4DFile

    Returns:
        A queryset of missing t-sliced dependencies
        and a list of querysets of their missing ff dependencies
    """
    sliced_ff_missing = TSlicedSAveredTracker.get_missing_deps_for_instance(ts_sa_ff)
    ff_missing = TSlicedTracker.get_missing_deps_for_set(sliced_ff_missing)
    return sliced_ff_missing, ff_missing


def main():
    """Tracks all missing dependencies fo DiskTSlicedSAveragedFormFactor4DFile.
    """
    print("Running deps locator script")

    all_missing_ts_sa_files = get_missing_disk_tsliced_saveraged_ffs()

    for ts_sa_ff in all_missing_ts_sa_files:
        print(f"Root: {ts_sa_ff}")
        try:
            sliced_ff_missing, ff_missing = get_dependencies_ts_sa_ff(ts_sa_ff)
            for ts_ff, ffs in zip(sliced_ff_missing, ff_missing):
                print(f"Missing tsliced: {ts_ff}")
                print(f"Missing ffs: {ffs}")
                break
        except DepenencyError as e:
            print("Failed with error:", e)


if __name__ == "__main__":
    main()
