import sys
import string

def supports_24bit_color():
    """Determine if the terminal supports 24-bit color."""
    if sys.platform != "win32":
        return os.getenv("COLORTERM") == "truecolor"
    return False


class colours:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CBLACK  = '\33[30m'
    CGREENBG  = '\33[42m'
    CREDBG    = '\33[41m'
    CVIOLETBG2 = '\33[105m'
    SPOTIFYGREEN = '\033[38;2;30;215;96m' if supports_24bit_color() else '\033[92m'


BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
LEGAL_PATH_CHARACTERS = string.ascii_letters + string.digits+ " ()[]" + "_-.,&'!@#$%^&+=~`"

DEFAULT_MIN_VIEWS_FOR_DOWNLOAD = 10000
DEFAULT_MAX_LENGTH_FOR_DOWNLOAD = 60*30

