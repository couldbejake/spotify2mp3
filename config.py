### SETTINGS
global BEARER_TOKEN
global MIN_VIEW_COUNT
global MAX_LENGTH
global DEBUG
global PATH_TO_JELLYFIN

MIN_VIEW_COUNT = 0 # 5, 000 views
MAX_LENGTH = 60 * 20   # 20 minutes
FAILURE_THRESHOLD = 100 # The number of songs that need to fail before prompting to re-run
DEBUG = False

MULTITHREAD = False

PATH_TO_JELLYFIN = ''