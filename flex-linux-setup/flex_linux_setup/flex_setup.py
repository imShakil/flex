#!/usr/bin/python3

import sys
import os
import zipfile
import argparse
import time
import glob
import code
import configparser
import subprocess
import shutil
import tempfile
import json
import uuid

from pathlib import Path
from urllib import request
from urllib.parse import urljoin
from xml.etree import ElementTree


argsp = None
cur_dir = os.path.dirname(__file__)
jans_installer_downloaded = bool(os.environ.get('JANS_INSTALLER'))
flex_installer_downloaded = False
install_py_path = os.path.join(cur_dir, 'jans_install.py')
installed_components = {'admin_ui': False, 'casa': False, 'ssa_decoded': {}}
ssa_json = {}
jans_config_properties = '/etc/jans/conf/jans.properties'

if '--remove-flex' in sys.argv and '--flex-non-interactive' not in sys.argv:

    print('\033[31m')
    print("This process is irreversible.")
    print("Gluu Flex Components will be removed")
    print('\033[0m')
    print()
    while True:
        print('\033[31m \033[1m')
        response = input("Are you sure to uninstall Gluu Flex? [yes/N] ")
        print('\033[0m')
        if response.strip().lower() in ('yes', 'n', 'no'):
            if response.lower() != 'yes':
                sys.exit()
            else:
                break
        else:
            print("Please type \033[1m yes \033[0m to uninstall")


def get_flex_setup_parser():
    parser = argparse.ArgumentParser(description="This script downloads Gluu Admin UI components and installs")
    parser.add_argument('--jans-setup-branch', help="Jannsen setup github branch", default='main')
    parser.add_argument('--flex-branch', help="Jannsen flex setup github branch", default='main')
    parser.add_argument('--jans-branch', help="Jannsen github branch", default='main')
    parser.add_argument('--node-modules-branch', help="Node modules branch. Default to flex setup github branch")
    parser.add_argument('--flex-non-interactive', help="Non interactive setup mode", action='store_true')
    parser.add_argument('--install-admin-ui', help="Installs Gluu Flex Admin UI", action='store_true')
    parser.add_argument('--update-admin-ui', help="Updates Gluu Flex Admin UI", action='store_true')
    parser.add_argument('-admin-ui-ssa', help="Admin-ui SSA file or jwt")
    parser.add_argument('--adminui_authentication_mode', help="Set authserver.acrValues", default='basic', choices=['basic', 'casa'])
    parser.add_argument('--install-casa', help="Installs casa", action='store_true')
    parser.add_argument('--remove-flex', help="Removes flex components", action='store_true')
    parser.add_argument('--no-restart-services', help="Do not restart services, useful when you are both uninstalling flex and Jans", action='store_true')
    parser.add_argument('--gluu-passwurd-cert', help="Creates Gluu Passwurd API keystore", action='store_true')
    parser.add_argument('-download-exit', help="Downloads files and exits", action='store_true')

    return parser

__STATIC_SETUP_DIR__ = '/opt/jans/jans-setup/'

profile = None
profile_fn = os.path.join(__STATIC_SETUP_DIR__, 'profile')
if os.path.exists(profile_fn):
    with open(profile_fn) as f:
        profile = f.read().strip()
    print("Profile was detected as \033[1m{}\033[0m.".format(profile))

if os.path.join(__STATIC_SETUP_DIR__, 'flex/flex-linux-setup') == cur_dir:
    jans_installer_downloaded = True
    flex_installer_downloaded = True

if not jans_installer_downloaded and os.path.exists(__STATIC_SETUP_DIR__):
    print("Backing up old Janssen setup directory")
    os.system('mv {} {}-{}'.format(__STATIC_SETUP_DIR__, __STATIC_SETUP_DIR__.rstrip('/'), time.ctime().replace(' ', '_')))
else:
    sys.path.append(__STATIC_SETUP_DIR__)

def download_jans_install_py(setup_branch):
    print("Downloading", os.path.basename(install_py_path))
    install_url = 'https://raw.githubusercontent.com/JanssenProject/jans/{}/jans-linux-setup/jans_setup/install.py'.format(setup_branch)
    request.urlretrieve(install_url, install_py_path)


if not (jans_installer_downloaded or os.path.exists(jans_config_properties)):
    argsp, nargs = get_flex_setup_parser().parse_known_args()
    print("Unable to locate jans-setup, installing ...")
    setup_branch = argsp.jans_setup_branch or 'main'
    download_jans_install_py(setup_branch)
    install_cmd = '{} {} --setup-branch={}'.format(sys.executable, install_py_path, setup_branch)

    if argsp.download_exit:
        nargs.append('--download-exit')
        argsp.flex_non_interactive = True

    if argsp.flex_non_interactive:
        nargs.append('-n')
        install_cmd += ' -yes'

    if nargs:
        install_cmd += ' --args="{}"'.format(subprocess.list2cmdline(nargs))

    print("Executing", install_cmd)
    os.system(install_cmd)
    jans_installer_downloaded = True

if not argsp:
    argsp, nargs = get_flex_setup_parser().parse_known_args()

if not jans_installer_downloaded:
    jans_archieve_url = 'https://github.com/JanssenProject/jans/archive/refs/heads/{}.zip'.format(argsp.jans_branch)
    with tempfile.TemporaryDirectory() as tmp_dir:
        jans_zip_file = os.path.join(tmp_dir, os.path.basename(jans_archieve_url))
        print("Downloading {} as {}".format(jans_archieve_url, jans_zip_file))
        request.urlretrieve(jans_archieve_url, jans_zip_file)
        if argsp.download_exit:
            dist_dir = '/opt/dist/jans/'
            if not os.path.exists(dist_dir):
                os.makedirs(dist_dir)
            shutil.copyfile(jans_zip_file, os.path.join(dist_dir, 'jans.zip'))
        print("Extracting jans-setup package")
        jans_zip = zipfile.ZipFile(jans_zip_file)
        parent_dir = jans_zip.filelist[0].orig_filename
        unpack_dir = os.path.join(tmp_dir, 'unpacked')
        shutil.unpack_archive(jans_zip_file, unpack_dir)
        shutil.copytree(os.path.join(unpack_dir, parent_dir, 'jans-linux-setup/jans_setup'), __STATIC_SETUP_DIR__)
        jans_zip.close()

    if profile:
        print("Writing profile \033[1m{}\033[0m to file {}.".format(profile, profile_fn))
        with open(profile_fn, 'w') as w:
            w.write(profile)

    sys.path.append(__STATIC_SETUP_DIR__)
    from setup_app import downloads
    from setup_app.utils import base
    from setup_app.utils import arg_parser
    base.argsp = arg_parser.get_parser()
    downloads.base.current_app.app_info = base.readJsonFile(os.path.join(__STATIC_SETUP_DIR__, 'app_info.json'))
    downloads.download_sqlalchemy()
    downloads.download_cryptography()
    downloads.download_pyjwt()


install_components = {
        'admin_ui': argsp.install_admin_ui,
        'casa': argsp.install_casa
    }

logs_dir = os.path.join(__STATIC_SETUP_DIR__, 'logs')

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

if __STATIC_SETUP_DIR__ not in sys.path:
    sys.path.append(__STATIC_SETUP_DIR__)

from setup_app import paths
paths.LOG_FILE = os.path.join(logs_dir, 'flex-setup.log')
paths.LOG_ERROR_FILE = os.path.join(logs_dir, 'flex-setup-error.log')
print()
print("Log Files:")
print('\033[1m')
print(paths.LOG_FILE)
print(paths.LOG_ERROR_FILE)
print('\033[0m')


parser = get_flex_setup_parser()
from setup_app.utils import arg_parser
arg_parser.add_to_me(parser)
installed = False


if not (os.path.exists(jans_config_properties) or argsp.download_exit):
    installed = True
    try:
        from jans_setup import jans_setup
    except ImportError:
        import jans_setup
        jans_setup.main()

argsp = arg_parser.get_parser()
del_msg = "  - Deleting"

from setup_app import static
from setup_app.utils import base

profile_fn = os.path.join(base.par_dir, 'profile')
if os.path.exists(profile_fn):
    with open(profile_fn) as f:
        profile = f.read().strip()
else:
    profile = 'jans'

os.environ['JANS_PROFILE'] = profile
base.current_app.profile = profile
base.argsp = argsp

if 'SETUP_BRANCH' not in base.current_app.app_info:
    base.current_app.app_info['SETUP_BRANCH'] = argsp.jans_setup_branch

base.current_app.app_info['jans_version'] = base.current_app.app_info['JANS_APP_VERSION'] + base.current_app.app_info['JANS_BUILD']

sys.path.insert(0, base.pylib_dir)
sys.path.insert(0, os.path.join(base.pylib_dir, 'gcs'))

from setup_app.pylib.jproperties import Properties
from setup_app.pylib import jwt
from setup_app.pylib.ldif4.ldif import LDIFWriter
from setup_app.utils.package_utils import packageUtils
from setup_app.config import Config
from setup_app.utils.collect_properties import CollectProperties
from setup_app.installers.node import NodeInstaller
from setup_app.installers.httpd import HttpdInstaller
from setup_app.installers.config_api import ConfigApiInstaller
from setup_app.installers.jetty import JettyInstaller
from setup_app.installers.jans_auth import JansAuthInstaller
from setup_app.installers.jans import JansInstaller
from setup_app.installers.jans_cli import JansCliInstaller
from setup_app.installers.jans_casa import CasaInstaller
from setup_app.utils.properties_utils import propertiesUtils
from setup_app.utils.ldif_utils import myLdifParser


Config.outputFolder = os.path.join(__STATIC_SETUP_DIR__, 'output')
if not os.path.exists(Config.outputFolder):
    os.makedirs(Config.outputFolder)


if not installed:

    # initialize config object
    Config.init(paths.INSTALL_DIR)

    if not argsp.download_exit:
        collectProperties = CollectProperties()
        collectProperties.collect()

    else:
        from setup_app.utils import arg_parser

    if not hasattr(base, 'argsp'):
        base.argsp = arg_parser.get_parser()

maven_base_url = 'https://jenkins.jans.io/maven/io/jans/'
app_versions = {
  "SETUP_BRANCH": argsp.jans_setup_branch,
  "FLEX_BRANCH": argsp.flex_branch,
  "JANS_BRANCH": argsp.jans_branch,
  "JANS_APP_VERSION": "1.0.22",
  "JANS_BUILD": "-SNAPSHOT",
  "NODE_VERSION": "v18.16.0",
  "NODE_MODULES_BRANCH": argsp.node_modules_branch or argsp.flex_branch
}

node_installer = NodeInstaller()
httpd_installer = HttpdInstaller()
jans_installer = JansInstaller()
config_api_installer = ConfigApiInstaller()
jansAuthInstaller = JansAuthInstaller()
jans_cli_installer = JansCliInstaller()
jans_casa_installer = CasaInstaller()

setup_properties = base.read_properties_file(argsp.f) if argsp.f else {}


class flex_installer(JettyInstaller):

    def __init__(self):

        self.jans_auth_dir = os.path.join(Config.jetty_base, jansAuthInstaller.service_name)
        self.jans_auth_custom_lib_dir = os.path.join(self.jans_auth_dir, 'custom/libs')
        self.admin_ui_log_dir = '/var/log/adminui'
        self.gluu_admin_ui_source_path = os.path.join(Config.dist_jans_dir, 'gluu-admin-ui.zip')
        self.log4j2_adminui_path = os.path.join(Config.dist_jans_dir, 'log4j2-adminui.xml')
        self.log4j2_path = os.path.join(Config.dist_jans_dir, 'log4j2.xml')
        self.admin_ui_plugin_source_path = os.path.join(Config.dist_jans_dir, 'gluu-flex-admin-ui-plugin.jar')
        self.flex_path = os.path.join(Config.dist_jans_dir, 'flex.zip')
        self.source_dir = os.path.join(Config.install_dir, 'flex')
        self.flex_setup_dir = os.path.join(self.source_dir, 'flex-linux-setup')
        self.templates_dir = os.path.join(self.flex_setup_dir, 'templates')
        self.scopes_ldif_fn = os.path.join(self.templates_dir, 'scopes.ldif')
        self.admin_ui_node_modules_url = 'https://jenkins.gluu.org/npm/admin_ui/{0}/node_modules/admin-ui-{0}-node_modules.tar.gz'.format(app_versions['NODE_MODULES_BRANCH'])
        self.config_api_node_modules_url = 'https://jenkins.gluu.org/npm/admin_ui/{0}/OpenApi/jans_config_api/admin-ui-{0}-jans_config_api.tar.gz'.format(app_versions['NODE_MODULES_BRANCH'])

        self.admin_ui_node_modules_path = os.path.join(Config.dist_jans_dir, os.path.basename(self.admin_ui_node_modules_url))
        self.config_api_node_modules_path = os.path.join(Config.dist_jans_dir, os.path.basename(self.config_api_node_modules_url))

        self.admin_ui_config_properties_path = os.path.join(self.templates_dir, 'auiConfiguration.json')

        if not argsp.download_exit:
            self.dbUtils.bind(force=True)

        self.admin_ui_dn = 'ou=admin-ui,ou=configuration,o=jans'
        Config.templateRenderingDict['admin_ui_apache_root'] = os.path.join(httpd_installer.server_root, 'admin')
        self.simple_auth_scr_inum = 'A51E-76DA'
        self.admin_ui_plugin_path = os.path.join(config_api_installer.libDir, os.path.basename(self.admin_ui_plugin_source_path))

        if not flex_installer_downloaded and os.path.exists(self.source_dir):
            os.rename(self.source_dir, self.source_dir + '-' + time.ctime().replace(' ', '_'))


    def download_files(self, force=False):
        print("Downloading Gluu Flex components")
        download_url, target = ('https://github.com/GluuFederation/flex/archive/refs/heads/{}.zip'.format(app_versions['FLEX_BRANCH']), self.flex_path)

        if not flex_installer_downloaded:
            base.download(download_url, target, verbose=True)

        print("Extracting", self.flex_path)
        base.extract_from_zip(self.flex_path, 'flex-linux-setup/flex_linux_setup', self.flex_setup_dir)

        download_files = []

        if install_components['admin_ui'] or argsp.download_exit or argsp.update_admin_ui:
            download_files += [
                    ('https://nodejs.org/dist/{0}/node-{0}-linux-x64.tar.xz'.format(app_versions['NODE_VERSION']), os.path.join(Config.dist_app_dir, 'node-{0}-linux-x64.tar.xz'.format(app_versions['NODE_VERSION']))),
                    (urljoin(maven_base_url, 'jans-config-api/plugins/admin-ui-plugin/{0}{1}/admin-ui-plugin-{0}{1}-distribution.jar'.format(app_versions['JANS_APP_VERSION'], app_versions['JANS_BUILD'])), self.admin_ui_plugin_source_path),
                    ('https://raw.githubusercontent.com/JanssenProject/jans/{}/jans-config-api/server/src/main/resources/log4j2.xml'.format(app_versions['JANS_BRANCH']), self.log4j2_path),
                    ('https://raw.githubusercontent.com/JanssenProject/jans/{}/jans-config-api/plugins/admin-ui-plugin/config/log4j2-adminui.xml'.format(app_versions['JANS_BRANCH']), self.log4j2_adminui_path),
                    (self.admin_ui_node_modules_url, self.admin_ui_node_modules_path),
                    (self.config_api_node_modules_url, self.config_api_node_modules_path),
                    ]

            if argsp.update_admin_ui:
                download_files.pop(0) 

        for download_url, target in download_files:
            if force or not os.path.exists(target):
                base.download(download_url, target, verbose=True)

        if argsp.download_exit:
            sys.exit()

    def add_apache_directive(self, check_str, template):
        print("Updating apache configuration")
        apache_directive_template_text = self.readFile(os.path.join(self.templates_dir, template))
        apache_directive_text = self.fomatWithDict(apache_directive_template_text, Config.templateRenderingDict)

        https_jans_text = self.readFile(httpd_installer.https_jans_fn)

        if check_str not in https_jans_text:

            https_jans_list = https_jans_text.splitlines()
            n = 0

            for i, l in enumerate(https_jans_list):
                if l.strip() == '</LocationMatch>':
                    n = i

            https_jans_list.insert(n+1, '\n' + apache_directive_text + '\n')
            self.writeFile(httpd_installer.https_jans_fn, '\n'.join(https_jans_list))

        self.enable_apache_mod_dir()

    def enable_apache_mod_dir(self):

        # Enable mod_dir for apache

        cmd_a2enmod = shutil.which('a2enmod')

        if base.clone_type == 'deb':
            httpd_installer.run([cmd_a2enmod, 'dir'])

        elif base.os_type == 'suse':
            httpd_installer.run([cmd_a2enmod, 'dir'])
            cmd_a2enflag = shutil.which('a2enflag')
            httpd_installer.run([cmd_a2enflag, 'SSL'])

        else:
            base_mod_path = Path('/etc/httpd/conf.modules.d/00-base.conf')
            mod_load_content = base_mod_path.read_text().splitlines()
            modified = False

            for i, l in enumerate(mod_load_content[:]):
                ls = l.strip()
                if ls.startswith('#') and ls.endswith('mod_dir.so'):
                    mod_load_content[i] = ls.lstrip('#')
                    modified = True

            if modified:
                base_mod_path.write_text('\n'.join(mod_load_content))


    def rewrite_cli_ini(self):
        print("  - Rewriting Jans CLI init file for plugins")
        cli_config = Path(jans_cli_installer.config_ini_fn)

        if cli_config.exists():
            config = configparser.ConfigParser()
            config.read_file(cli_config.open())
            plugins = config_api_installer.get_plugins()
            config['DEFAULT']['jca_plugins'] = ','.join(plugins)
            config.write(cli_config.open('w'))
            cli_config.chmod(0o600)


    def build_gluu_admin_ui(self):
        print("Extracting admin-ui from", self.flex_path)
        base.extract_from_zip(self.flex_path, 'admin-ui', self.source_dir)

        print("Stopping Jans Auth")
        config_api_installer.stop('jans-auth')

        print("Stopping Janssen Config Api")
        config_api_installer.stop()

        print("Building Gluu Admin UI Frontend")
        env_tmp = os.path.join(self.source_dir, '.env.tmp')
        config_api_installer.renderTemplateInOut(env_tmp, self.source_dir, self.source_dir)
        config_api_installer.copyFile(os.path.join(self.source_dir, '.env.tmp'), os.path.join(self.source_dir, '.env'))

        for module_pack in (self.admin_ui_node_modules_path, self.config_api_node_modules_path):
            print("Unpacking", module_pack)
            shutil.unpack_archive(module_pack, self.source_dir)

        config_api_installer.run([paths.cmd_chown, '-R', 'node:node', self.source_dir])
        cmd_path = 'PATH=$PATH:{}/bin:{}/bin'.format(Config.jre_home, Config.node_home)

        for cmd in ('npm run build:prod',):
            print("Executing `{}`".format(cmd))
            run_cmd = '{} {}'.format(cmd_path, cmd)
            config_api_installer.run(['/bin/su', 'node','-c', run_cmd], self.source_dir)


        print("Copying files to",  Config.templateRenderingDict['admin_ui_apache_root'])
        config_api_installer.copy_tree(os.path.join(self.source_dir, 'dist'),  Config.templateRenderingDict['admin_ui_apache_root'])


    def install_gluu_admin_ui(self):

        print("Installing Gluu Admin UI Frontend")
        self.build_gluu_admin_ui()


        def get_client_parser():

            cli_ldif_client_fn = os.path.join(jans_cli_installer.templates_folder, os.path.basename(jans_cli_installer.ldif_client))
            ldif_parser = myLdifParser(cli_ldif_client_fn)
            ldif_parser.parse()

            return ldif_parser

        print("Creating Gluu Flex Admin UI Web Client")

        client_check_result = config_api_installer.check_clients([('admin_ui_client_id', '2001.')])
        if client_check_result['2001.'] == -1:

            ldif_parser = get_client_parser()

            ldif_parser.entries[0][1]['inum'] = ['%(admin_ui_client_id)s']
            ldif_parser.entries[0][1]['jansClntSecret'] = ['%(admin_ui_client_encoded_pw)s']
            ldif_parser.entries[0][1]['displayName'] = ['Admin UI Web Client {}'.format(ssa_json.get('org_id', ''))]
            ldif_parser.entries[0][1]['jansTknEndpointAuthMethod'] = ['none']
            ldif_parser.entries[0][1]['jansAttrs'] = ['{"tlsClientAuthSubjectDn":"","runIntrospectionScriptBeforeJwtCreation":false,"keepClientAuthorizationAfterExpiration":false,"allowSpontaneousScopes":false,"spontaneousScopes":[],"spontaneousScopeScriptDns":[],"updateTokenScriptDns":[],"backchannelLogoutUri":[],"backchannelLogoutSessionRequired":false,"additionalAudience":[],"postAuthnScripts":[],"consentGatheringScripts":[],"introspectionScripts":[],"rptClaimsScripts":[],"parLifetime":600,"requirePar":false,"jansAuthSignedRespAlg":null,"jansAuthEncRespAlg":null,"jansAuthEncRespEnc":null}']

            client_tmp_fn = os.path.join(self.templates_dir, 'admin_ui_client.ldif')

            print("\033[1mAdmin UI Web Client ID:\033[0m", Config.admin_ui_client_id)
            print("\033[1mAdmin UI Web Client Secret:\033[0m", Config.admin_ui_client_pw)

            with open(client_tmp_fn, 'wb') as w:
                ldif_writer = LDIFWriter(w)
                ldif_writer.unparse('inum=%(admin_ui_client_id)s,ou=clients,o=jans', ldif_parser.entries[0][1])

            config_api_installer.renderTemplateInOut(client_tmp_fn, self.templates_dir, self.source_dir)
            self.dbUtils.import_ldif([self.scopes_ldif_fn, os.path.join(self.source_dir, os.path.basename(client_tmp_fn))])


        client_check_result = config_api_installer.check_clients([('admin_ui_web_client_id', '2002.')])
        if client_check_result['2002.'] == -1:

            ldif_parser = get_client_parser()

            ldif_parser.entries[0][1]['inum'] = ['%(admin_ui_web_client_id)s']
            ldif_parser.entries[0][1]['jansClntSecret'] = ['%(admin_ui_web_client_encoded_pw)s']
            ldif_parser.entries[0][1]['displayName'] = ['Admin UI Backend API Client {}'.format(ssa_json.get('org_id', ''))]
            ldif_parser.entries[0][1]['jansGrantTyp'] = ['client_credentials']
            ldif_parser.entries[0][1]['jansRespTyp'] = ['token']
            ldif_parser.entries[0][1]['jansScope'] = ['inum=F0C4,ou=scopes,o=jans', 'inum=2002.3534E1,ou=scopes,o=jans']
            ldif_parser.entries[0][1]['jansTknEndpointAuthMethod'] = ['client_secret_basic']
            ldif_parser.entries[0][1]['jansTrustedClnt'] = ['FALSE']
            for del_entry in ('jansLogoutURI', 'jansPostLogoutRedirectURI', 'jansRedirectURI', 'jansSignedRespAlg'):
                del ldif_parser.entries[0][1][del_entry]

            web_client_tmp_fn = os.path.join(self.templates_dir, 'admin_ui_web_client.ldif')

            print("\033[1mAdmin UI Backend API Client ID:\033[0m", Config.admin_ui_web_client_id)
            print("\033[1mAdmin UI Backend API Secret:\033[0m", Config.admin_ui_web_client_encoded_pw)

            with open(web_client_tmp_fn, 'wb') as w:
                ldif_writer = LDIFWriter(w)
                ldif_writer.unparse('inum=%(admin_ui_web_client_id)s,ou=clients,o=jans', ldif_parser.entries[0][1])

            config_api_installer.renderTemplateInOut(web_client_tmp_fn, self.templates_dir, self.source_dir)
            self.dbUtils.import_ldif([os.path.join(self.source_dir, os.path.basename(web_client_tmp_fn))])

        self.add_apache_directive(Config.templateRenderingDict['admin_ui_apache_root'], 'admin_ui_apache_directive')

        oidc_client = installed_components.get('oidc_client', {})
        Config.templateRenderingDict['ssa'] = installed_components['ssa']
        Config.templateRenderingDict['op_host'] = ssa_json.get('iss', '')
        Config.templateRenderingDict['oidc_client_id'] = oidc_client.get('client_id', '')
        Config.templateRenderingDict['oidc_client_secret'] = oidc_client.get('client_secret', '')
        Config.templateRenderingDict['license_hardware_key'] = ssa_json.get('org_id', str(uuid.uuid4()))
        Config.templateRenderingDict['scan_license_api_hostname'] =  Config.templateRenderingDict['op_host'].replace('account', 'cloud')
        Config.templateRenderingDict['adminui_authentication_mode'] = argsp.adminui_authentication_mode

        config_api_installer.renderTemplateInOut(self.admin_ui_config_properties_path, self.templates_dir, self.source_dir)
        admin_ui_jans_conf_app =  config_api_installer.readFile(os.path.join(self.source_dir, os.path.basename(self.admin_ui_config_properties_path)))
        config_api_installer.dbUtils.set_configuration('jansConfApp', admin_ui_jans_conf_app, self.admin_ui_dn)

        self.install_config_api_plugin()

        print("Removing DUO Script")
        config_api_installer.dbUtils.delete_dn('inum=5018-F9CF,ou=scripts,o=jans')

        self.rewrite_cli_ini()


    def install_config_api_plugin(self):

        old_plugin = os.path.join(config_api_installer.libDir, 'admin-ui-plugin.jar')
        if os.path.exists(old_plugin):
            print("Old plugin {} was detected. Removing...".format(old_plugin))
            os.remove(old_plugin)

        config_api_installer.copyFile(self.admin_ui_plugin_source_path, config_api_installer.libDir, backup=False)
        config_api_installer.add_extra_class(self.admin_ui_plugin_path)

        config_api_installer.copyFile(self.log4j2_path, config_api_installer.custom_config_dir)

        log4j2_adminui_path_target_path = os.path.join(
                                config_api_installer.custom_config_dir,
                                os.path.basename(self.log4j2_adminui_path)
                                )

        print("Reading XML", self.log4j2_adminui_path)
        tree = ElementTree.parse(self.log4j2_adminui_path)
        root = tree.getroot()

        for appenders in root.findall('Appenders'):
            for child in appenders:
                if child.tag=='RollingFile' and child.get('name') in ('ADMINUI-AUDIT', 'ADMINUI-LOG'):
                    for prop in ('fileName', 'filePattern'):
                        file_name = child.get(prop)
                        if file_name:
                            file_base_name = os.path.basename(file_name)
                            new_file_path = os.path.join(self.admin_ui_log_dir, file_base_name)
                            child.set(prop, new_file_path)
        print("Writing XML", log4j2_adminui_path_target_path)
        tree.write(log4j2_adminui_path_target_path, encoding='utf-8', xml_declaration=True)

        if not os.path.exists(self.admin_ui_log_dir):
            os.makedirs(self.admin_ui_log_dir)
        config_api_installer.chown(self.admin_ui_log_dir, Config.jetty_user, Config.jetty_group)

        config_api_installer.set_class_path(glob.glob(os.path.join(config_api_installer.libDir, '*.jar')))

        self.rewrite_cli_ini()

    def install_casa(self):
        Config.install_casa = True
        jans_casa_installer.calculate_selected_aplications_memory()
        jans_installer.order_services()
        jans_casa_installer.start_installation()
        jans_casa_installer.enable()

    def save_properties(self):
        fn = Config.savedProperties
        print("Saving properties", fn)
        if os.path.exists(fn):
            p = Properties()
            with open(fn, 'rb') as f:
                p.load(f, 'utf-8')
            for prop in ('admin_ui_client_id', 'admin_ui_client_pw'):
                if Config.get(prop):
                    p[prop] = Config.get(prop)
            with open(fn, 'wb') as f:
                p.store(f, encoding="utf-8")
        else:
            propertiesUtils.save_properties()


    def remove_apache_directive(self, directive):
        https_jans_current = self.readFile(httpd_installer.https_jans_fn)
        tmp_ = directive.lstrip('<').rstrip('>').strip()
        dir_name, dir_arg = tmp_.split()
        dir_fname = '/'+dir_name

        https_jans_list = []
        append_c = 2

        for l in https_jans_current.splitlines():
            if dir_name in l and dir_arg in l:
                append_c = 0
            elif append_c == 0 and dir_fname in l:
                append_c = 1

            if append_c > 1:
                https_jans_list.append(l)

            if append_c == 1:
                append_c = 2

        self.writeFile(httpd_installer.https_jans_fn, '\n'.join(https_jans_list))


    def uninstall_admin_ui(self):
        print("Uninstalling Gluu Admin-UI")

        client_check_result = config_api_installer.check_clients([('admin_ui_client_id', '2001.')])
        if client_check_result['2001.'] == 1:
            print("  - Deleting Gluu Flex Admin UI Web Client ", Config.admin_ui_client_id)
            self.dbUtils.delete_dn('inum={},ou=clients,o=jans'.format(Config.admin_ui_client_id))

        client_check_result = config_api_installer.check_clients([('admin_ui_web_client_id', '2002.')])
        if client_check_result['2002.'] == 1:
            print("  - Deleting Gluu Flex Admin UI Backend API Client ", Config.admin_ui_web_client_id)
            self.dbUtils.delete_dn('inum={},ou=clients,o=jans'.format(Config.admin_ui_web_client_id))


        self.dbUtils.set_configuration("jansConfApp", None, self.admin_ui_dn)

        print("  - Removing Admin UI directives from apache configuration")
        self.remove_apache_directive('<Directory "{}">'.format(Config.templateRenderingDict['admin_ui_apache_root']))

        if os.path.exists(self.admin_ui_plugin_path):
            print(del_msg, self.admin_ui_plugin_path)
            self.run(['rm', '-f', self.admin_ui_plugin_path])

        write_config_api_xml = False
        config_api_plugins = config_api_installer.get_plugins(paths=True)

        if self.admin_ui_plugin_path in config_api_plugins:
            print("  - Removing plugin {} from Jans Config API Configuration".format(self.admin_ui_plugin_path))
            config_api_plugins.remove(self.admin_ui_plugin_path)
            write_config_api_xml = True

        if write_config_api_xml:
            config_api_installer.set_class_path(config_api_plugins)

        for s_path in (self.log4j2_adminui_path, self.log4j2_path):
            f_path = os.path.join(
                        config_api_installer.custom_config_dir,
                        os.path.basename(s_path)
                        )
            if os.path.exists(f_path):
                print(del_msg, f_path)
                self.run(['rm', '-f', f_path])

        self.rewrite_cli_ini()

        if os.path.exists(Config.templateRenderingDict['admin_ui_apache_root']):
            print(del_msg, Config.templateRenderingDict['admin_ui_apache_root'])
            self.run(['rm', '-f', '-r', Config.templateRenderingDict['admin_ui_apache_root']])

    def generate_gluu_passwurd_api_keystore(self):
        print("Generating Gluu Passwurd API Keystore")
        suffix = 'passwurd_api'
        keystore_pw = jansAuthInstaller.getPW()
        keystore_pw_fn = os.path.join(Config.certFolder, 'passwurd_api.json')
        key_fn, csr_fn, crt_fn = jansAuthInstaller.gen_cert(suffix, 'changeit', user='jetty')
        passwurd_api_keystore_fn = os.path.join(Config.certFolder, 'passwurdAKeystore.pcks12')
        self.import_key_cert_into_keystore(
                        suffix=suffix,
                        keystore_fn=passwurd_api_keystore_fn,
                        keystore_pw=keystore_pw,
                        in_key=key_fn,
                        in_cert=crt_fn,
                        store_type='PKCS12'
                        )
        keystore_pw_data = {'keyStoreSecret': keystore_pw}
        jansAuthInstaller.writeFile(keystore_pw_fn, json.dumps(keystore_pw_data))
        jansAuthInstaller.chown(keystore_pw_fn, Config.jetty_user, Config.root_user)
        jansAuthInstaller.run([base.paths.cmd_chmod, '640', keystore_pw_fn])

def read_or_get_ssa():
    if os.path.isfile(argsp.admin_ui_ssa):
        with open(argsp.admin_ui_ssa) as f:
            installed_components['ssa'] = f.read().strip()
    else:
        installed_components['ssa'] = argsp.admin_ui_ssa


def decode_ssa_jwt():

    print("Decoding SSA")

    ssa_decoded = jwt.decode(
        installed_components['ssa'],
        options={
                'verify_signature': False,
                'verify_exp': True,
                'verify_aud': False
                }
        )

    ssa_json.update(ssa_decoded)


def prompt_for_installation():

    if not os.path.exists(os.path.join(httpd_installer.server_root, 'admin')):
        prompt_admin_ui_install = input("Install Admin UI [Y/n]: ")
        if not prompt_admin_ui_install.strip().lower().startswith('n'):
            install_components['admin_ui'] = True
            if argsp.admin_ui_ssa:
                read_or_get_ssa()
                try:
                    decode_ssa_jwt()
                except Exception as e:
                    argsp.admin_ui_ssa = None
                    print("\033[31mSSA you provided via argument is not valid.\033[0m")
                    print(e)

            while not argsp.admin_ui_ssa:
                ssa_text = input("Please enter path of file containing SSA or paste SSA (q to exit): ")
                if ssa_text.strip().lower() == 'q':
                    print("Can't continue without SSA. Exiting...")
                    sys.exit()
                argsp.admin_ui_ssa = ssa_text
                read_or_get_ssa()
                try:
                    decode_ssa_jwt()
                except Exception as e:
                    argsp.admin_ui_ssa = None
                    print("Error decoding SSA")
                    print(e)

    else:
        print("Admin UI is allready installed on this system")
        install_components['admin_ui'] = False

    if not jans_casa_installer.installed():
        prompt_casa_install = input("Install Jans Casa [Y/n]: ")
        if not prompt_casa_install.strip().lower().startswith('n'):
            install_components['casa'] = True
    else:
        print("Jans Casa is allready installed on this system")
        install_components['casa'] = False

    if not (install_components['casa'] or install_components['admin_ui'] or argsp.gluu_passwurd_cert):
        print("Nothing to install. Exiting ...")
        sys.exit()


def install_post_setup():
    if install_components['casa']:
        print("Starting Casa")
        jans_casa_installer.start()

    print("Installation was completed.")

    if install_components['admin_ui']:
        print("Browse https://{}/admin".format(Config.hostname))

    if install_components['casa']:
        print("Browse https://{}/jans-casa".format(Config.hostname))

def prepare_for_installation():
    if not (argsp.flex_non_interactive or argsp.download_exit):
        prompt_for_installation()
    else:
        if argsp.install_admin_ui:
            if not argsp.admin_ui_ssa:
                print("Please provide Admin UI SSA")
                sys.exit()
            read_or_get_ssa()
            decode_ssa_jwt()

def get_components_from_setup_properties():
    if argsp.f:
        if not argsp.gluu_passwurd_cert:
            argsp.gluu_passwurd_cert = base.as_bool(setup_properties.get('gluu-passwurd-cert'))

        if not (argsp.install_admin_ui or install_components['admin_ui']):
            install_components['admin_ui'] = base.as_bool(setup_properties.get('install-admin-ui'))

        if not argsp.admin_ui_ssa and install_components['admin_ui']:
            argsp.admin_ui_ssa = setup_properties.get('admin-ui-ssa')
            read_or_get_ssa()
            decode_ssa_jwt()

        if not (argsp.install_casa or install_components['casa']):
            install_components['casa'] = base.as_bool(setup_properties.get('install-casa'))

        if 'adminui-authentication-mode' in setup_properties:
            argsp.adminui_authentication_mode = setup_properties['adminui-authentication-mode']


def obtain_oidc_client_credidentials():

    data = {
        "software_statement": installed_components['ssa'],
        "response_types": ["token"],
        "redirect_uris": ["{}".format(ssa_json['iss'])],
        "client_name": "test-ui-client"
    }

    registration_url = urljoin(ssa_json['iss'], 'jans-auth/restv1/register')

    req = request.Request(registration_url)
    req.add_header('Content-Type', 'application/json')
    jsondata = json.dumps(data)
    jsondataasbytes = jsondata.encode('utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))

    print("Requesting OIDC Client from", registration_url)

    try:
        response = request.urlopen(req, jsondataasbytes)
        result = response.read()
        installed_components['oidc_client'] = json.loads(result.decode())
        print("OIDC Client ID is", installed_components['oidc_client']['client_id'])
    except Exception as e:
        print("Error sending request to {}".format(registration_url))
        print(e)
        sys.exit()


def restart_services():
    print("Restarting Apache")
    httpd_installer.restart()

    print("Restarting Jans Auth")
    config_api_installer.restart('jans-auth')

    print("Restarting Janssen Config Api")
    config_api_installer.restart()

def main(uninstall):

    get_components_from_setup_properties()

    installer_obj = flex_installer()

    if argsp.update_admin_ui:
        if os.path.exists(os.path.join(httpd_installer.server_root, 'admin')):
            installer_obj.download_files(force=True)
            installer_obj.build_gluu_admin_ui()
            installer_obj.install_config_api_plugin()
            restart_services()
        else:
            print("Gluu Flex Admin UI was not installed on this system. Update not possible.")
        sys.exit()

    elif not uninstall:
        prepare_for_installation()

    if uninstall:
        installer_obj.uninstall_admin_ui()
        print("Disabling script", installer_obj.simple_auth_scr_inum)
        installer_obj.dbUtils.enable_script(installer_obj.simple_auth_scr_inum, enable=False)

    else:
        if install_components['admin_ui'] and argsp.admin_ui_ssa:
            obtain_oidc_client_credidentials()

        if not flex_installer_downloaded or argsp.download_exit:
            installer_obj.download_files(argsp.download_exit)

        print("Enabling script", installer_obj.simple_auth_scr_inum)
        installer_obj.dbUtils.enable_script(installer_obj.simple_auth_scr_inum)

        if install_components['admin_ui']:
            if not node_installer.installed():
                print("Installing node")
                node_installer.install()
            installer_obj.install_gluu_admin_ui()
        if install_components['casa']:
            installer_obj.install_casa()
            installer_obj.save_properties()
        if argsp.gluu_passwurd_cert:
            installer_obj.generate_gluu_passwurd_api_keystore()

    if not argsp.no_restart_services:
        restart_services()


    if not uninstall:
        install_post_setup()

if __name__ == "__main__":
    if argsp.shell:
        code.interact(local=locals())
        sys.exit()
    else:
       main(uninstall=argsp.remove_flex)

