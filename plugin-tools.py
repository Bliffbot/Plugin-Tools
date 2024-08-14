import os
import time
import shutil
import datetime
import sys
import xml.etree.ElementTree as ET
import json5
import paramiko
import stat
from mcrcon import MCRcon


def logo():
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Plugin-Tools by Bliffbot")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Version 2.0.0")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] ")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] loading config...")


def help():
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] no args detected")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] USAGE")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] plugin-tools.py \"path/to/config.json\"")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] the config file will be set to a default if it is empty")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] the following pip packages are required: json5, mcrcon, paramiko")
	exit()


def newConfig():
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] config file not found or empty")

	defaults = '''// YOU MIGHT HAVE TO REMOVE ALL COMMENTS FROM THIS FILE
{
	// just the name of your plugin without anything else like version numbers
	"pluginName": "best plugin",

	// the folder in which intellij put the compiled jar files
	"sourceFolder": "C:/intellij/projects/best plugin/target",

	// the path to the pom.xml which has all of your maven config
	"pomXML": "C:/intellij/projects/best plugin/pom.xml",

	// true		- the script automatically sets the next version in the pom.xml
	// false	- the pom.xml remains untouched
	// supported version formats: 1.0.0 or 1.0.0.beta.0
	// the last number will be incremented by one: 1.0.1 or 1.0.0.beta.1
	// everything else is ignored so you could put \'the.BEST.plugin.EVER.0\' and it would still work
	"setNextVersion": "true",

	// put all the folders where you want the latest version of your plugin to be copied to in here
	"folders": {

		// put the path of your folder in here
		"C:/minecraft server/plugins": {

			// the folder might not be on the local machine and instead on an sftp server
			// set the following options if you this is the case
			"sftp": {
				"enabled": "false",
				"ip": "127.0.0.1",
				"port": "22",
				"username": "user",
				"password": "password"
			},

			// old		- the script looks for all .jar-files starting with the the name of your plugin and append them with .old
			// delete	- the script looks for all .jar-files starting with the the name of your plugin and delete them (even the old ones)
			// false	- the script will not search the folder for these .jar-files
			"tidy": "delete",

			// true		- the script will copy the latest version of your plugin to this folder (after tidy ran)
			// false	- the script will not copy the latest version of your plugin to this folder
			"copy": "true"
		}
	},

	// you can execute a command on a server using rcon if you want
	"servers": {

		// the name is only used for logging purposes
		"server name": {

			// set the rcon options to allow the script to connect to the server
			"enabled": "false",
			"ip": "127.0.0.1",
			"port": "25575",
			"password": "password",

			// it is possible to execute multiple commands
			"command": ["reload confirm", "say SERVER IS READY"]
		}
	}
}'''

	try:
		with open(sys.argv[1], "w") as configFile:
			configFile.write(defaults)
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] new config file generated at {sys.argv[1]}")
	except Exception as error:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] could not generate new config file - {error}")

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] finished :)")
	exit()


def getConfig():
	if not os.path.exists(sys.argv[1]):
		newConfig()

	with open(sys.argv[1], "r") as configFile:
		content = configFile.read()

	if content == "":
		newConfig()

	with open(sys.argv[1], "r") as configFile:
		config = json5.load(configFile)

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] config loaded")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Plugin Name: {config['pluginName']}")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Source Folder: {config['sourceFolder']}")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] POM Location: {config['pomXML']}")
	return config


def pom(config):
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] getting plugin version...")

	if not os.path.exists(config['pomXML']):
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] pom.xml not found - please check your config")
		exit()

	tree = ET.parse(f"{config['pomXML']}")

	if tree is None:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] pom.xml could not be parsed")
		exit()

	root = tree.getroot()
	namespace = root.tag[root.tag.find('{')+1:root.tag.find('}')]
	version_element = root.find(f'{{{namespace}}}version')

	if version_element is None:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] plugin version could not be found in the pom.xml")
		exit()

	pluginVersion = version_element.text

	if pluginVersion is None:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] plugin version seem to be not set in the pom.xml")
		exit()

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Plugin Version: {pluginVersion}")

	if config["setNextVersion"] == "false":
		return pluginVersion

	version = pluginVersion.split(".")

	try:
		versionInt = int(version[-1])
	except:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] weird version in pom.xml -> did not modify")
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] please use major.minor.patch.test.revision")
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] the parts need to be separated by dots")
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] and there must be a number after the last dot")
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] e.g. 1.2.3 or 1.2.3.beta.4")
		return pluginVersion

	version[-1] = str(versionInt + 1)
	newVersion = ".".join(version)

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Next Version: {newVersion}")
	version_element.text = newVersion

	try:
		tree.write("pom.xml", xml_declaration = True, encoding = "utf-8", method = "xml", default_namespace = namespace)
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] the next plugin version has been set in the pom.xml")

	except:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] could not update the plugin version in the pom.xml")

	return pluginVersion


def sftpTidy(config, folder, sftp):
	if config["folders"][folder]["tidy"] != "old" and config["folders"][folder]["tidy"] != "delete":
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] not tidying sftp folder")
		return

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] tidying sftp folder...")

	folderPath = config["folders"][folder]["path"]

	if not folderPath.endswith("/"):
		folderPath = folderPath + "/"

	for file in sftp.listdir(folderPath):
		path = folderPath + file
		if file.startswith(config['pluginName']) and stat.S_ISREG(sftp.stat(path).st_mode) and file.endswith(".jar"):
			if config["folders"][folder]["tidy"] == "old":
				try:
					sftp.rename(path, path + ".old")
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} renamed")
				except Exception as error:
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} not renamed - {error}")

			if config["folders"][folder]["tidy"] == "delete":
				try:
					sftp.remove(path)
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} deleted")
				except Exception as error:
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} not deleted - {error}")

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] tidied sftp folder")


def sftpCopy(config, folder, jarPath, fileName, sftp):
	if config["folders"][folder]["copy"] == "false":
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] not copying to sftp folder")
		return

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] copying to sftp folder...")

	folderPath = config["folders"][folder]["path"]

	if not folderPath.endswith("/"):
		folderPath = folderPath + "/"

	try:
		sftp.put(jarPath, folderPath + fileName)
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] copied to sftp folder")

	except Exception as error:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {error}")


def sftp(config, folder, jarPath, fileName):
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] sftp connecting...")
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(config["folders"][folder]["sftp"]["ip"], int(config["folders"][folder]["sftp"]["port"]), config["folders"][folder]["sftp"]["username"], config["folders"][folder]["sftp"]["password"])
	sftp = ssh.open_sftp()
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] sftp connected")
	sftpTidy(config, folder, sftp)
	sftpCopy(config, folder, jarPath, fileName, sftp)
	sftp.close()


def tidy(config, folder):
	if config["folders"][folder]["tidy"] != "old" and config["folders"][folder]["tidy"] != "delete":
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] not tidying local folder")
		return

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] tidying local folder...")

	folderPath = config["folders"][folder]["path"]

	if not folderPath.endswith("/"):
		folderPath = folderPath + "/"

	for file in os.listdir(folderPath):
		path = folderPath + file
		if file.startswith(config['pluginName']) and os.path.isfile(path) and file.endswith(".jar"):
			if config["folders"][folder]["tidy"] == "old":
				try:
					shutil.move(path, path + ".old")
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} renamed")
				except Exception as error:
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} not renamed - {error}")

			if config["folders"][folder]["tidy"] == "delete":
				try:
					os.remove(path)
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} deleted")
				except Exception as error:
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {file} not deleted - {error}")

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] tidied local folder")


def copy(config, folder, jarPath):
	if config["folders"][folder]["copy"] == "false":
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] not copying to local folder")
		return

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] copying to local folder...")

	folderPath = config["folders"][folder]["path"]

	if not folderPath.endswith("/"):
		folderPath = folderPath + "/"

	try:
		shutil.copy(jarPath, folderPath)
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] copied to local folder")

	except Exception as error:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {error}")


def folders(config, pluginVersion):
	fileName = f"{config['pluginName']}-{pluginVersion}.jar"
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] File Name: {fileName}")

	sourceFolder = config['sourceFolder']

	if not sourceFolder.endswith("/"):
		sourceFolder = sourceFolder + "/"

	jarPath = f"{sourceFolder}{fileName}"

	if not os.path.exists(jarPath):
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] jar not found")
		return

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] jar found")
	time.sleep(2)
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] modifying the folders...")

	for folder in config["folders"]:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {folder} - {config["folders"][folder]["path"]}")
		if config["folders"][folder]["sftp"]["enabled"] == "true":
			sftp(config, folder, jarPath, fileName)

		else:
			tidy(config, folder)
			copy(config, folder, jarPath)


def command(options, server):
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {server}")

	for command in options["command"]:
		with MCRcon(options["ip"], options["password"], port = int(options["port"])) as mcr:
			response = mcr.command(command)
			print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {command}")
			print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {response}")


def servers(config):
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] sending server commands...")

	for server in config["servers"]:
		command(config["servers"][server], server)

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] all commands sent")


def main():
	os.system("cls")

	logo()

	if len(sys.argv) < 2:
		help()

	elif len(sys.argv) > 1:
		config = getConfig()

	pluginVersion = pom(config)
	folders(config, pluginVersion)
	servers(config)

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] finished :)")


main()