import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # logging.FileHandler("simp_daemon.log"),
        logging.StreamHandler() 
    ]
)

logger = logging.getLogger("SIMPDaemon")