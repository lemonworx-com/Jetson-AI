from datetime import datetime

def generate_timestamp(TZ_LOCALE):
  return datetime.now(TZ_LOCALE).strftime("%Y-%m-%d-%H_%M_%S.%f")