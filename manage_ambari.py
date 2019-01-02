import subprocess
import logging
import shlex

## __name__ : the name of the module
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def os_run_os_command(cmd, env=None, shell=False, cwd=None):
    logger.info('about to run command: ' + str(cmd))
    if type(cmd) == str:
        cmd = shlex.split(cmd)
    #https://stackoverflow.com/questions/19961052/what-is-the-difference-if-i-dont-use-stdout-subprocess-pipe-in-subprocess-popen
    process = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env,
                                cwd=cwd,
                                shell=shell
    )
    logger.info("\nprocess_pid=" + str(process.pid))
    (stdoutdata, stderrdata) = process.communicate()
    return process.returncode, stdoutdata, stderrdata



print os_run_os_command("ls *")
print os_run_os_command("ambari-agent status ")
