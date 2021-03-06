import logging


def get_module_logger(mod_name):
  logger = logging.getLogger(mod_name)
  handler = logging.StreamHandler()
#   formatter = logging.Formatter(
#       '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
  formatter = logging.Formatter(
      '%(asctime)s %(levelname)-6s %(message)s')
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  # NOTSET does not mean "pass all messages through", it means "inherit the log level from the parent logger"
  logger.setLevel(logging.NOTSET)
  return logger
