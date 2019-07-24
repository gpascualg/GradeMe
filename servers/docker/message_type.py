from enum import Enum


class MessageType(Enum):
    IMPORT_ERROR    = 0
    TEST_RESULT     = 1
    TESTS_DONE      = 2
    JOB_QUEUED      = 3
    JOB_STARTED     = 4
    JOB_ENDED       = 5
