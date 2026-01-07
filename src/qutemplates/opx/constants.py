from enum import StrEnum, auto


class ExportConstants(StrEnum):

    PARAMETERS = auto()
    DATA = auto()
    DEBUG = auto()


class Status(StrEnum):

    RUNNING = auto()
    STOPPED = auto()


