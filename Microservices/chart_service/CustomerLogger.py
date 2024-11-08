import logging
import os
class CustomLogger:
    def __init__(self, service_name, user_id):
        self.service_name = service_name
        self.user_id = user_id
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.DEBUG)
        #  Ensure the log directory exists
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Absolute path to the script's directory
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, f'{service_name}.log'))
        file_handler.setLevel(logging.DEBUG)
        # Create formatter
        
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)


        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)
