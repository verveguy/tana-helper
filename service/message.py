import platform

os_platform = platform.system()

if os_platform == "Darwin":
  import syslog
  # Define identifier
  syslog.openlog("TanaHelper")

  def message(s):
    syslog.syslog(syslog.LOG_ALERT, s)
    print(s)
else:
  def message(s):
    # print(s)
    pass
