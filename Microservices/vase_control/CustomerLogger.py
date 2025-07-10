import logging
import os 
class CustomLogger:
    def __init__(self, service_name, user_id=None):
        self.service_name = service_name
        self.user_id = user_id
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.DEBUG)
        # Ensure the log directory exists
        # Use local logs directory if /app is not writable (running locally)
        default_log_dir = '/app/logs' if os.path.exists('/app') and os.access('/app', os.W_OK) else './logs'
        log_dir = os.getenv('LOG_DIR', default_log_dir)
        os.makedirs(log_dir, exist_ok=True)
        
        if not self.logger.hasHandlers():
            # Create file handler
            file_handler = logging.FileHandler(f'{log_dir}/{service_name}.log')
            file_handler.setLevel(logging.DEBUG)

            # Create formatter
            formatter = logging.Formatter('[%(levelname)s] %(message)s - %(user_id)s')

            # Set formatter to handler
            file_handler.setFormatter(formatter)

            # Add the file handler to the logger
            self.logger.addHandler(file_handler)


    def info(self, message):
        self.logger.info(message, extra={'user_id': self.user_id or 'N/A'})

    def error(self, message):
        self.logger.error(message, extra={'user_id': self.user_id or 'N/A'})
