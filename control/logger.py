"""This module contains Logger class for logging host applications.

  Typical usage example:

  logger = UbsLogger(loglevel="INFO")

  logger.info("This is an info")
  logger.warning("This is a warning")
  logger.error("This is an error")

  Notice:
  Set log level:
    use loglevel=[LEVEL] parameter while created UbsLogger() instance to
    set stream handler log level and keep file handler log level at DEBUG to
    log all messages. Don't use UbsLogger().SetLeve([LEVEL]), this will
    reset file handler's log level.
    e.g.:
    OK -
    logger = UbsLogger(loglevel="INFO")
    NG -
    logger = UbsLogger()
    logger.SetLevel(level='INFO')
  Save log to file:
    parameter savelog=['True'/'False'] can decide to log into file or not.
    e.g.:
    Only stream -
      logger = UbsLogger(loglevel='INFO', savelog='False')
    Both stream and file -
      logger = UbsLogger(loglevel='INFO', savelog='True')
"""
import logging
from logging import handlers
import os
import sys
#from json import JSONEncoder

_LOG_INST = False


class TestLogger():
  """Provides a common logging format for ubs host applications."""

  def __init__(self) -> None:
    self.ClassName = "TestLogger"
  
  def to_json(self):
    return {'ClassName': self.ClassName}

  def __new__(cls, **config):
    """Constructs this class.

    cls._loglevel use the INFO level be the default for user forgot to set it.
    If want to view root_logger record message under this method, suggest to
    modify to DEBUG.
    cls._savelog for user to set to decide to save into log or just shows on
    terminal.

    Args:
      **config: dict.

    Returns:
      logger object.

    Raises:
       OSError: occur while created the log folder error.
    """
    cls._loglevel = config.get('loglevel', 'INFO')
    cls._savelog = config.get('savelog', 'True')
    cls._showOnScreen = config.get('display', 'False')
    root_logger = logging.getLogger(__name__)
    # Don't use parent logging handlers (Add for log twice issue)
    root_logger.propagate = False

    global _LOG_INST

    if not _LOG_INST:
      f_time = '%(asctime)s'
      f_level = '[%(levelname)s]'
      f_fileline = '[%(filename)s:%(lineno)s]'
      f_msg = '%(message)s'
      fmt = f'{f_time} {f_fileline} {f_level} {f_msg}'
      formatter = logging.Formatter(fmt)

      # Set the default log level to debug.
      root_logger.setLevel(logging.DEBUG)
      # stream_handler = logging.StreamHandler()
      # stream_handler.setLevel(level=cls._loglevel)
      # stream_handler.setFormatter(formatter)
      # root_logger.addHandler(stream_handler)

      if (cls._savelog == 'True') or (cls._savelog == 'T'):
        # Create log folder.
        #init_path = os.path.expanduser('~')
        init_path = str(os.getcwd())
        logger_fd = os.path.join(init_path, 'log_data')
        root_logger.debug('ubs log folder=%s', logger_fd)

        if os.path.exists(logger_fd):
          root_logger.debug('The log folder already existed.')
        else:
          try:
            os.makedirs(logger_fd)
            root_logger.info('Creating log folder : %s', logger_fd)
          except OSError as err:
            root_logger.debug('exception while creating, err=%s', err)
            # pylint: disable=raise-missing-from
            raise OSError

        log_file_path = os.path.join(logger_fd, 'test_logger.log')

        file_handler = handlers.TimedRotatingFileHandler(
            filename=log_file_path, when='midnight')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        root_logger.addHandler((file_handler))
        #
        if cls._showOnScreen == 'True' or cls._showOnScreen == 'T':
          screen_handler = logging.StreamHandler(stream=sys.stdout) #stream=sys.stdout is similar to normal print
          screen_handler.setFormatter(formatter)
          root_logger.addHandler(screen_handler)
        #
      _LOG_INST = True

    return root_logger


if __name__ == '__main__':
  logger = TestLogger(loglevel='INFO', savelog='True')
  logger.info('This is an info')
  logger.warning('This is a warning')
  logger.error('This is an error')
  logger.critical('This is critical')
  logger.debug('This is debug')
