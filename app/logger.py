import logging

# Create a logger object
logger = logging.getLogger('app_logger')

# Set the log level (you can change this to logging.DEBUG, logging.ERROR, etc.)
logger.setLevel(logging.DEBUG)

# Create a formatter to include useful details like time and log level
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a console handler (prints to stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Create a file handler (logs to a file)
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Optionally, prevent the logger from propagating to the root logger
logger.propagate = False

