import os

def get_var(var_name : str):
  env_var = os.getenv(var_name)
  if env_var == None:
    raise ValueError(f"{var_name} not set.")
  return env_var

def get_int_var(var_name : str):
  return int(get_var(var_name))

def get_bool_var(var_name : str):
  return bool(get_int_var(var_name))

